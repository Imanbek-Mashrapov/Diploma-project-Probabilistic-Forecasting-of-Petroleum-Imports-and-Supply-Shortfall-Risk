"""UN Comtrade client.

Uses the keyed data endpoint when UN_COMTRADE_PRIMARY_KEY is set, otherwise the
keyless preview endpoint. Every response is stored byte-for-byte, and a JSONL
manifest records one line per task outcome, which also serves as the checkpoint.

The secondary key is only tried after the primary is rejected as invalid (401).
Comtrade does not document it as extra quota, so quota errors never trigger it.
"""
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timezone

import requests

from src.utils.config import RAW
from src.utils.retry import backoff_delay

log = logging.getLogger(__name__)
DONE_STATES = {"ok", "empty", "split"}


class QuotaExhausted(RuntimeError):
    pass


class ComtradeError(RuntimeError):
    pass


def task_id(dataset, params):
    canon = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha1(canon.encode()).hexdigest()[:10]
    reporter = str(params.get("reporterCode", "all")).split(",")[0]
    period = str(params.get("period", "")).split(",")[0]
    return f"{dataset}_{reporter}_{period}_{digest}"


class ComtradeClient:
    def __init__(self, settings):
        self.cfg = settings["comtrade"]
        self.snapshot = settings["snapshot_id"]
        self.keys = [k for k in (os.getenv("UN_COMTRADE_PRIMARY_KEY"), os.getenv("UN_COMTRADE_SECONDARY_KEY")) if k]
        self.mode = "keyed" if self.keys else "preview"
        self.limits = self.cfg[self.mode]
        self.key_index = 0
        self.root = RAW / "un_comtrade" / self.snapshot
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.jsonl"
        self.done = self._load_manifest()
        self.session = requests.Session()
        self.last_call = 0.0
        self.calls = 0
        log.info("Comtrade mode=%s snapshot=%s completed_tasks=%d", self.mode, self.snapshot, len(self.done))

    def _load_manifest(self):
        done = set()
        if self.manifest_path.exists():
            for line in self.manifest_path.open(encoding="utf-8"):
                rec = json.loads(line)
                if rec["status"] in DONE_STATES:
                    done.add(rec["task"])
        return done

    def _record(self, **rec):
        rec["recorded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self.manifest_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")

    def _throttle(self):
        wait = self.limits["min_interval_s"] - (time.monotonic() - self.last_call)
        if wait > 0:
            time.sleep(wait)
        self.last_call = time.monotonic()

    def _headers(self):
        return {self.cfg["auth_header"]: self.keys[self.key_index]} if self.mode == "keyed" else {}

    def _get(self, path, params):
        """One logical request with retries. Returns the successful Response."""
        url = self.cfg["base_url"] + path
        waited = 0.0
        for attempt in range(self.cfg["max_retries"] + 1):
            self._throttle()
            try:
                r = self.session.get(url, params=params, headers=self._headers(), timeout=self.cfg["timeout_s"])
                self.calls += 1
            except requests.RequestException as e:
                delay = backoff_delay(attempt, self.cfg["backoff_base_s"], self.cfg["backoff_max_s"])
                log.warning("network error %s; retry in %.0fs", type(e).__name__, delay)
                time.sleep(delay)
                continue
            if r.status_code == 200:
                return r
            body = r.text[:200]
            if r.status_code == 401:
                if self.mode == "keyed" and self.key_index + 1 < len(self.keys):
                    log.warning("primary key rejected; switching to the secondary key")
                    self.key_index += 1
                    continue
                raise ComtradeError(f"401 unauthorized: {body}")
            if r.status_code in (403, 429):
                delay = self._quota_delay(r, attempt)
                waited += delay
                if waited > self.cfg["quota_wait_max_s"]:
                    raise QuotaExhausted(body)
                log.warning("HTTP %s quota/rate response; waiting %.0fs: %s", r.status_code, delay, body)
                time.sleep(delay)
                continue
            if r.status_code >= 500:
                delay = backoff_delay(attempt, self.cfg["backoff_base_s"], self.cfg["backoff_max_s"])
                log.warning("HTTP %s; retry in %.0fs", r.status_code, delay)
                time.sleep(delay)
                continue
            raise ComtradeError(f"HTTP {r.status_code}: {body}")
        raise ComtradeError(f"retries exhausted for {params}")

    def _quota_delay(self, response, attempt):
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            return float(retry_after) + 2
        m = re.search(r"replenished in (\d+):(\d+):(\d+)", response.text)
        if m:
            h, mi, s = map(int, m.groups())
            return h * 3600 + mi * 60 + s + 5
        return backoff_delay(attempt + 3, self.cfg["backoff_base_s"], self.cfg["backoff_max_s"])

    @staticmethod
    def validate(payload):
        """Return (rows, problem). A problem means the body cannot be trusted."""
        if not isinstance(payload, dict) or "data" not in payload:
            return [], "response has no data field"
        if payload.get("error"):
            return [], f"api error: {payload['error']}"
        rows = payload["data"] or []
        if not isinstance(rows, list):
            return [], "data is not a list"
        count = payload.get("count")
        if count is not None and count != len(rows):
            return rows, f"count {count} != rows {len(rows)}"
        return rows, None

    def fetch(self, dataset, params, path=None):
        """Download one task. Truncated responses are split, never accepted."""
        tid = task_id(dataset, params)
        if tid in self.done:
            return "cached"
        path = path or (self.cfg["data_path"] if self.mode == "keyed" else self.cfg["preview_path"])
        query = {**params, "includeDesc": "true"}
        retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            r = self._get(path, query)
            payload = r.json()
        except (ComtradeError, ValueError) as e:
            self._record(task=tid, dataset=dataset, params=params, status="failed", error=str(e)[:300], mode=self.mode)
            log.error("FAILED %s: %s", tid, str(e)[:200])
            return "failed"
        rows, problem = self.validate(payload)
        if problem:
            self._record(task=tid, dataset=dataset, params=params, status="failed", error=problem, mode=self.mode)
            log.error("INVALID %s: %s", tid, problem)
            return "failed"
        if len(rows) >= self.limits["record_cap"]:
            children = self._split(params)
            if not children:
                self._record(task=tid, dataset=dataset, params=params, status="truncated", rows=len(rows), mode=self.mode)
                log.error("TRUNCATED and unsplittable: %s", tid)
                return "truncated"
            log.info("%s hit the %d record cap; splitting", tid, self.limits["record_cap"])
            statuses = [self.fetch(dataset, c, path) for c in children]
            if all(s in ("ok", "empty", "cached") for s in statuses):
                self._record(task=tid, dataset=dataset, params=params, status="split", mode=self.mode)
                self.done.add(tid)
                return "ok"
            return "failed"
        out = self.root / dataset / f"{tid}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(r.content)
        status = "ok" if rows else "empty"
        self._record(task=tid, dataset=dataset, params=params, status=status, rows=len(rows), mode=self.mode,
                     endpoint=path, retrieved_at=retrieved, sha256=hashlib.sha256(r.content).hexdigest(),
                     file=out.relative_to(self.root).as_posix())
        self.done.add(tid)
        return status

    @staticmethod
    def _split(params):
        """Halve the first list-valued dimension; None when nothing is left to split."""
        for field in ("period", "cmdCode", "flowCode", "reporterCode"):
            parts = str(params.get(field, "")).split(",")
            if len(parts) > 1:
                mid = len(parts) // 2
                return [{**params, field: ",".join(parts[:mid])}, {**params, field: ",".join(parts[mid:])}]
        return None

    def availability(self, reporter=None):
        """Monthly dataset listing, including firstReleased dates. Keyless."""
        params = {"reporterCode": reporter} if reporter is not None else {}
        return self._get(self.cfg["availability_path"], params).json()

    def reference(self, name):
        """Download a reference file (reporters, partners, HS editions) into data/raw/reference."""
        out = RAW / "reference" / f"{name}.json"
        if not out.exists():
            r = self.session.get(f"{self.cfg['base_url']}{self.cfg['reference_path']}/{name}.json", timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)
        return json.loads(out.read_text(encoding="utf-8-sig"))
