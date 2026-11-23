"""Stage 5b: download open-access PDFs whose licence permits keeping a local copy.

Allowed: Creative Commons licences, public domain, and arXiv preprints (arXiv distributes them openly under a
licence that permits download). Anything else, including 'publisher-specific-oa' and unlicensed repository copies,
is recorded as a link only. Files are checked for the %PDF signature; HTML landing pages are discarded.
Writes metadata/raw/downloads.json.
"""
import json
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "metadata" / "raw"
PAPERS = ROOT / "papers"
UA = {"User-Agent": "academic-literature-review-script"}


def licence_ok(lic, url):
    lic = (lic or "").lower()
    if "arxiv.org" in (url or ""):
        return True, "arXiv"
    if lic.startswith("cc") or "creativecommons" in lic or lic in ("public-domain", "pd"):
        return True, lic
    return False, lic or "unknown"


def fname(it):
    first = (it["authors"].split(";")[0].strip().split() or ["Unknown"])[-1]
    first = re.sub(r"[^A-Za-z]", "", first) or "Unknown"
    words = [w for w in re.sub(r"[^A-Za-z0-9 ]", " ", it["title"]).split() if len(w) > 2][:7]
    return f"{it['year'] or 'nd'}_{first}_{'_'.join(words)}.pdf"[:150]


def main():
    inc = json.load(open(RAW / "verified.json", encoding="utf-8"))
    log = []
    for it in inc:
        v = it["verification"]
        cands = []
        if it["oa_pdf"]:
            cands.append((it["oa_pdf"], it["oa_license"]))
        if v.get("s2_oa_pdf"):
            cr_lic = " ".join(v.get("crossref_license") or [])
            cands.append((v["s2_oa_pdf"], it["oa_license"] or cr_lic))
        if it["doi"].startswith("10.48550/arxiv."):
            cands.append((f"https://arxiv.org/pdf/{it['doi'].split('arxiv.')[1]}", "arXiv"))
        rec = {"key": it["key"], "title": it["title"], "theme": it["theme"], "status": "no_open_copy", "file": "", "licence": "", "source_url": ""}
        for url, lic in cands:
            ok, lic_name = licence_ok(lic, url)
            rec.update({"licence": lic_name, "source_url": url})
            if not ok:
                rec["status"] = "link_only_licence_not_open"
                continue
            try:
                r = requests.get(url, headers=UA, timeout=60)
            except requests.RequestException:
                rec["status"] = "download_failed"
                continue
            if r.status_code == 200 and r.content[:4] == b"%PDF":
                out = PAPERS / it["theme"] / fname(it)
                out.write_bytes(r.content)
                rec.update({"status": "downloaded", "file": str(out.relative_to(ROOT)).replace("\\", "/"), "bytes": len(r.content)})
                break
            rec["status"] = "not_a_pdf_or_blocked"
            time.sleep(1)
        log.append(rec)
        print(rec["status"], it["title"][:60], flush=True)
    json.dump(log, open(RAW / "downloads.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
