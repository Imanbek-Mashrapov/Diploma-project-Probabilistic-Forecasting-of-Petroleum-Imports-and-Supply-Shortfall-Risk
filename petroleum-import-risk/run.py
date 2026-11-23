"""Pipeline entry point: python run.py <stage>

Stages, in order: refs, availability, pilot, audit, panel, external, process, reports, load
Phase 2: validation_pull, phase2, events
"""
import argparse
import json
import logging

import pandas as pd

from src.ingestion import plans
from src.ingestion.comtrade_client import ComtradeClient, QuotaExhausted
from src.utils.config import PROCESSED, load_countries, load_hs_codes, load_settings
from src.utils.logging_config import setup_logging

log = logging.getLogger("run")


def run_tasks(client, dataset, tasks, label):
    """Run a task list. Failures are counted and reported, never skipped silently."""
    counts = {}
    total = len(tasks)
    i = 0
    try:
        for i, params in enumerate(tasks, 1):
            status = client.fetch(dataset, params)
            counts[status] = counts.get(status, 0) + 1
            if i % 50 == 0 or i == total:
                log.info("%s %d/%d %s calls=%d", label, i, total, counts, client.calls)
    except QuotaExhausted as e:
        log.error("%s stopped on quota after %d/%d tasks: %s. Rerun to resume.", label, i - 1, total, str(e)[:160])
        counts["stopped_on_quota"] = total - (i - 1)
    log.info("%s finished: %s", label, counts)
    return counts


def stage_refs(settings):
    client = ComtradeClient(settings)
    for name in ["Reporters", "partnerAreas", "QuantityUnits", "H3", "H4", "H5", "H6"]:
        client.reference(name)
    reporters = {r["reporterCode"]: r for r in client.reference("Reporters")["results"]}
    rows = []
    for c in load_countries().itertuples():
        ref = reporters.get(c.comtrade_code)
        rows.append({"iso3": c.iso3, "comtrade_code": c.comtrade_code, "in_reporter_list": ref is not None,
                     "ref_iso": ref and ref.get("reporterCodeIsoAlpha3"), "ref_desc": ref and ref.get("reporterDesc"),
                     "ref_note": ref and ref.get("reporterNote")})
    check = pd.DataFrame(rows)
    PROCESSED.mkdir(exist_ok=True)
    check.to_csv(PROCESSED / "reporter_code_check.csv", index=False)
    log.info("reporter check: %d of %d found; iso mismatches: %s", check.in_reporter_list.sum(), len(check),
             check[check.iso3 != check.ref_iso][["iso3", "ref_iso", "ref_desc"]].values.tolist())
    hs_rows = []
    for ed in ["H3", "H4", "H5", "H6"]:
        ids = {str(r["id"]): r["text"] for r in client.reference(ed)["results"]}
        for code in load_hs_codes().hs_code:
            hs_rows.append({"edition": ed, "hs_code": code, "exists": code in ids, "text": ids.get(code)})
    hs = pd.DataFrame(hs_rows)
    hs.to_csv(PROCESSED / "hs_edition_check.csv", index=False)
    log.info("hs existence by edition:\n%s", hs.pivot(index="hs_code", columns="edition", values="exists").to_string())


def stage_availability(settings):
    client = ComtradeClient(settings)
    out = client.root / "availability"
    out.mkdir(exist_ok=True)
    for c in load_countries().itertuples():
        f = out / f"{c.iso3}.json"
        if not f.exists():
            f.write_text(json.dumps(client.availability(c.comtrade_code)), encoding="utf-8")
    log.info("availability saved for %d reporters", len(list(out.glob("*.json"))))


def stage_pilot(settings):
    client = ComtradeClient(settings)
    tasks = plans.bilateral_tasks([417], plans.window(settings["pilot_window"]), load_hs_codes().hs_code.tolist(),
                                  settings["flows"]["pilot"], client.limits["periods_per_call"])
    run_tasks(client, "bilateral", tasks, "pilot")


def stage_audit(settings):
    client = ComtradeClient(settings)
    codes = load_hs_codes().query("in_target == 1 or hs_code == '2710'").hs_code.tolist()
    reporters = load_countries().comtrade_code.tolist()
    run_tasks(client, "world_audit", plans.world_tasks(reporters, plans.window(settings["window"]), codes), "audit")


def stage_panel(settings):
    from src.preprocessing.harmonization import panel_reporters
    client = ComtradeClient(settings)
    reporters = panel_reporters()
    flows = settings["flows"]["panel_keyed" if client.mode == "keyed" else "panel_preview"]
    tasks = plans.bilateral_tasks(reporters, plans.window(settings["screening"]["window"]), load_hs_codes().hs_code.tolist(),
                                  flows, client.limits["periods_per_call"])
    log.info("panel: %d reporters, %d tasks, mode=%s", len(reporters), len(tasks), client.mode)
    run_tasks(client, "bilateral", tasks, "panel")


def stage_validation_pull(settings):
    """Extra Comtrade data for validation: Russian mirror exports and annual totals. Needs a key."""
    client = ComtradeClient(settings)
    if client.mode != "keyed":
        raise SystemExit("validation_pull needs UN_COMTRADE_PRIMARY_KEY in .env")
    fuels = "271011,271012,271019,271020,271112,271113,271119"
    filters = plans.TOTAL_FILTERS
    partners = ",".join(str(c) for c in load_countries().comtrade_code)
    mirror = [{"reporterCode": 643, "period": ",".join(str(y * 100 + m) for m in range(1, 13)), "cmdCode": fuels, "flowCode": "X", "partnerCode": partners, **filters}
              for y in range(2015, 2023)]
    run_tasks(client, "mirror_russia", mirror, "mirror")
    reporters = ",".join(str(c) for c in load_countries().comtrade_code)
    annual = [{"reporterCode": reporters, "period": str(y), "cmdCode": "2710," + fuels, "flowCode": "M", "partnerCode": 0, **filters} for y in range(2015, 2026)]
    counts = {}
    for params in annual:
        status = client.fetch("annual_world", params, settings["comtrade"]["annual_path"])
        counts[status] = counts.get(status, 0) + 1
    log.info("annual finished: %s", counts)
    totals = [{"reporterCode": 417, "period": ",".join(str(y * 100 + m) for m in range(1, 13)), "cmdCode": "TOTAL", "flowCode": "M", "partnerCode": 0, **filters} for y in (2023, 2024, 2025, 2026)]
    run_tasks(client, "kgz_all_goods", totals, "kgz_all_goods")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage")
    stage = parser.parse_args().stage
    settings = load_settings()  # loads .env first, so the log filter knows the keys to mask
    setup_logging(stage)
    stages = {"refs": stage_refs, "availability": stage_availability, "pilot": stage_pilot, "audit": stage_audit, "panel": stage_panel, "validation_pull": stage_validation_pull}
    if stage == "external":
        from src.ingestion.external_data_client import collect_all
        collect_all(settings)
    elif stage == "process":
        from src.preprocessing.harmonization import build_all
        build_all(settings)
    elif stage == "reports":
        from src.preprocessing.validation import build_reports
        build_reports(settings)
    elif stage == "phase2":
        from src.research.pipeline import run
        run(settings)
    elif stage == "events":
        from src.research.events import run as run_events
        from src.utils.config import DATA, REPORTS
        run_events(pd.read_parquet(DATA / "research" / "petroleum_imports_monthly.parquet"), pd.read_csv(REPORTS / "series_eligibility.csv"))
    elif stage == "load":
        from src.database.load import load_all
        load_all()
    else:
        stages[stage](settings)


if __name__ == "__main__":
    main()
