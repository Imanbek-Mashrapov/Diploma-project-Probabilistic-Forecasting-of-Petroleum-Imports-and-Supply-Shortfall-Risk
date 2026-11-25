"""Load the modelling panel from data/research.

Every observation carries the date it became public (`available_on`). An origin is the last
day of a month: at origin month M a value is visible only if `available_on` falls on or before
the end of M. Nothing here fills missing months.
"""
import numpy as np
import pandas as pd

from src.research import events as ev
from src.utils.config import DATA, REPORTS

RESEARCH = DATA / "research"
MODELING = DATA / "modeling"


def origin_end(month):
    """Last moment of an origin month."""
    return pd.Timestamp(month) + pd.offsets.MonthBegin(1) - pd.Timedelta(microseconds=1)


def series_table(settings):
    """Target series with tier, importer type and dependence. One row per (iso3, product_group)."""
    m = settings["modeling"]
    cov = pd.read_csv(RESEARCH / "country_product_coverage.csv")
    cov = cov[cov.product_group.isin(m["products"].values()) & cov.quality_tier.isin(m["tiers"]["training"])]
    elig = pd.read_csv(REPORTS / "series_eligibility.csv").drop_duplicates(["iso3", "product_group"])
    out = cov[["iso3", "country", "product_group", "quality_tier", "median_lag_days_2021_on"]].merge(
        elig[["iso3", "product_group", "importer_type_provisional"]], on=["iso3", "product_group"], how="left")
    out["evaluation"] = out.quality_tier.isin(m["tiers"]["evaluation"])
    out["series_id"] = out.iso3 + ":" + out.product_group
    return out.sort_values(["product_group", "iso3"]).reset_index(drop=True)


def monthly_panel(settings, series=None):
    """Monthly rows for the target series: mass, release date, supplier structure, unit value."""
    series = series if series is not None else series_table(settings)
    cols = ["iso3", "product_group", "month", "import_mass_t", "first_released", "uv_relative", "hhi_12m",
            "largest_supplier_share", "russia_share", "data_status"]
    m = pd.read_parquet(RESEARCH / "petroleum_imports_monthly.parquet", columns=cols)
    m = m.merge(series[["iso3", "product_group", "series_id"]], on=["iso3", "product_group"])
    m["month"] = pd.to_datetime(m.month).astype("datetime64[ns]")
    m["available_on"] = pd.to_datetime(m.first_released).astype("datetime64[ns]")
    m.loc[m.import_mass_t.isna(), "available_on"] = pd.NaT
    return m.sort_values(["series_id", "month"]).reset_index(drop=True)


def external_panel(settings):
    """Monthly external indicators, wide by (iso3 or global) and month, lagged by their release delay.

    The value stored at month t is what was public at the end of month t.
    """
    lags = settings["modeling"]["external_lag_months"]
    e = pd.read_parquet(RESEARCH / "external_indicators_monthly.parquet")
    e = e[e.indicator.isin(lags)]
    e["month"] = pd.to_datetime(e.month).astype("datetime64[ns]")
    shifted = e.month.dt.to_period("M") + e.indicator.map(lags).astype(int)
    e["month"] = shifted.dt.to_timestamp().astype("datetime64[ns]")
    e["key"] = np.where(e.scope == "global", "GLOBAL", e.iso3)
    return e.pivot_table(index=["key", "month"], columns="indicator", values="value").reset_index()


def event_table(settings, monthly):
    """Shock events touching each modelled series, with the date each became public."""
    events = ev.load_events()
    panel = monthly[["iso3", "product_group"]].drop_duplicates()
    touched = ev.expand(events, monthly.rename(columns={"import_mass_t": "import_mass_t"}), panel)
    cols = ["event_id", "start_date", "end_date", "announced_date", "role", "end_basis"]
    out = touched.merge(events[cols], on=["event_id", "role"])
    out["public_on"] = out.announced_date.fillna(out.start_date)
    return out
