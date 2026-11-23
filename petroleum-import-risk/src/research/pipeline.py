"""Phase 2 driver: python run.py phase2. Reads Phase 1 outputs and raw files, writes only to
data/research and reports/phase2."""
import json
import logging

from src.preprocessing import cleaning
from src.research import coverage, datasets, docs, eda, integrity, kyrgyz
from src.utils.config import load_settings

log = logging.getLogger(__name__)


def run(settings=None):
    settings = settings or load_settings()
    snapshot = settings["snapshot_id"]
    eda.OUT.mkdir(parents=True, exist_ok=True)
    eda.TABLES.mkdir(parents=True, exist_ok=True)
    data = datasets.build_all(settings)
    monthly = data["monthly"]
    reconciliation = kyrgyz.annual_reconciliation(monthly)
    dependency = kyrgyz.import_dependency()
    mirror = kyrgyz.supplier_mirror(snapshot, data["bilateral"], settings)
    all_goods = kyrgyz.all_goods_check(snapshot)
    press = kyrgyz.press_checks(monthly)
    annual_check = integrity.annual_vs_monthly(snapshot, cleaning.load_deduped_bilateral())
    data["annual_check"] = annual_check
    quality = integrity.run(data, snapshot, reconciliation, all_goods, mirror)
    cov = coverage.matrix(monthly, data["external"], data["availability"], settings["screening"]["window"], annual_check)
    results = eda.run_all(data, reconciliation, dependency, mirror, all_goods, cov)
    quality.to_csv(datasets.RESEARCH / "data_quality_report.csv", index=False)
    cov.to_csv(datasets.RESEARCH / "country_product_coverage.csv", index=False)
    for name, table in [("kyrgyz_reconciliation", reconciliation), ("kyrgyz_import_dependency", dependency), ("mirror_comparison", mirror), ("kyrgyz_vintage_check", all_goods),
                        ("press_checks", press), ("annual_vs_monthly", annual_check)]:
        table.to_csv(eda.TABLES / f"{name}.csv", index=False)
    docs.write_all(settings, data, cov, quality, reconciliation, results, (dependency, mirror, all_goods, press))
    log.info("phase 2 complete")
    return {"data": data, "coverage": cov, "quality": quality, "results": results}
