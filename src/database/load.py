"""Load the analytical parquet files into PostgreSQL. Expects sql/schema.sql applied to an empty database."""
import json
import logging

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine
from src.utils.config import ANALYTICAL, PROCESSED, REPORTS, ROOT, load_countries, load_hs_codes

log = logging.getLogger(__name__)
RAW_KEEP = ["source_task", "retrieved_at", "reporterCode", "flowCode", "cmdCode", "partnerCode", "period"]
MONTHLY_COLS = ["iso3", "product_group", "flow", "period", "month", "mass_t", "mass_t_reported", "mass_t_partner_sum", "mass_t_world", "value_usd",
                "unit_value_usd_t", "total_source", "n_partners", "value_share_with_mass", "share_estimated", "share_mass_recovered_from_qty",
                "flag_uv_low", "flag_uv_high", "flag_mass_outlier", "mass_t_incl_volume_estimate", "month_status", "first_released", "publication_lag_days"]


def _append(frame, schema, table, conn):
    frame.to_sql(table, conn, schema=schema, if_exists="append", index=False, method="multi", chunksize=2000)
    log.info("%s.%s: %d rows", schema, table, len(frame))


def _melt(frame, ids):
    return frame.melt(id_vars=ids, var_name="series", value_name="value").dropna(subset=["value"])


def apply_schema(engine):
    sql = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)


def load_all(engine=None):
    engine = engine or get_engine()
    cov = pd.read_csv(REPORTS / "country_coverage_report.csv")[["iso3", "tier_final"]]
    countries = load_countries().merge(cov, on="iso3", how="left").rename(columns={"group": "country_group", "tier_final": "tier"})
    countries["lldc"] = countries.lldc.astype(bool)
    products = load_hs_codes().assign(in_target=lambda d: d.in_target.astype(bool))
    bilateral = pd.read_parquet(ANALYTICAL / "dataset_a_bilateral.parquet")
    monthly = pd.read_parquet(ANALYTICAL / "dataset_b_monthly.parquet")
    conc = pd.read_parquet(ANALYTICAL / "supplier_concentration.parquet")
    glob = pd.read_parquet(ANALYTICAL / "dataset_c_global_monthly.parquet")
    country = pd.read_parquet(ANALYTICAL / "dataset_c_country_monthly.parquet")
    annual = pd.read_parquet(ANALYTICAL / "dataset_c_country_annual.parquet")
    raw = pd.read_parquet(PROCESSED / "raw_bilateral_records.parquet")
    raw_rows = raw[RAW_KEEP].rename(columns={"reporterCode": "reporter_code", "flowCode": "flow", "cmdCode": "hs_code", "partnerCode": "partner_code"})
    records = raw.drop(columns=["source_task", "api_mode"]).astype(object)
    raw_rows["record"] = [json.loads(json.dumps(r, default=str)) for r in records.where(records.notna(), None).to_dict("records")]
    raw_rows = raw_rows.drop_duplicates(["source_task", "reporter_code", "flow", "hs_code", "partner_code", "period"])
    staging_cols = ["iso3", "flow", "period", "hs_code", "product_group", "classification", "partner_code", "partner_iso", "partner_name", "mass_t",
                    "mass_source", "mass_estimated", "value_usd", "net_weight_kg_original", "qty_original", "qty_unit", "is_reported", "is_aggregate", "retrieved_at"]
    ext_global = _melt(glob, ["period"]).assign(scope="global", iso3="WLD")
    ext_country = _melt(country, ["iso3", "period"]).assign(scope="country")
    with engine.begin() as conn:
        _append(countries, "metadata", "country", conn)
        _append(products, "metadata", "product", conn)
        from sqlalchemy.dialects.postgresql import JSONB
        raw_rows.to_sql("un_comtrade_imports", conn, schema="raw", if_exists="append", index=False, method="multi", chunksize=1000, dtype={"record": JSONB})
        log.info("raw.un_comtrade_imports: %d rows", len(raw_rows))
        _append(bilateral[staging_cols], "staging", "petroleum_imports", conn)
        _append(monthly[MONTHLY_COLS], "analytics", "monthly_petroleum_imports", conn)
        _append(conc, "analytics", "supplier_concentration", conn)
        _append(pd.concat([ext_global, ext_country]), "analytics", "monthly_external_indicators", conn)
        _append(_melt(annual, ["iso3", "year"]), "analytics", "annual_external_indicators", conn)
        counts = {t: conn.execute(text(f"select count(*) from {t}")).scalar() for t in
                  ["raw.un_comtrade_imports", "staging.petroleum_imports", "analytics.monthly_petroleum_imports", "analytics.supplier_concentration"]}
    log.info("loaded: %s", counts)
    return counts
