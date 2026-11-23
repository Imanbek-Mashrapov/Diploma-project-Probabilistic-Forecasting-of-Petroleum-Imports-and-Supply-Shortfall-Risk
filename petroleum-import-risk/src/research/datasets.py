"""Phase 2 research datasets, built only from Phase 1 outputs. Raw responses are read, never written.

Aggregation rules:
- A country total is the sum of partner rows. World rows are a check, and a fallback
  only where partner rows do not exist (total_source = world_row). The two are never added.
- The 2710 heading is never summed with its six-digit lines.
- 271011 (HS2007) and 271012 (HS2012 on) both feed gasoline. 271019 keeps its own group,
  and 271019 + 271020 is a separate labelled group.
"""
import logging

import numpy as np
import pandas as pd

from src.preprocessing.harmonization import load_availability
from src.utils.config import ANALYTICAL, DATA, PROCESSED, REPORTS, load_countries, months_between

log = logging.getLogger(__name__)
RESEARCH = DATA / "research"
RESEARCH_PRODUCTS = ["gasoline", "middle_heavy", "middle_incl_blends", "biodiesel_blend", "lpg", "crude", "total_2710"]
PRODUCT_LABELS = {"gasoline": "Gasoline proxy (HS 271011/271012)", "middle_heavy": "Middle and heavy distillates (HS 271019)",
                  "middle_incl_blends": "Distillates with blends (HS 271019 + 271020)", "biodiesel_blend": "Biodiesel blends (HS 271020)",
                  "lpg": "LPG (HS 271112/13/19)", "crude": "Crude (HS 2709)", "total_2710": "HS 2710 heading total"}
RUSSIA = 643
SELF_OR_NON_SUPPLIER = {837: "bunkers", 839: "special_categories"}
NES_PARTNERS = {490: "other_asia_nes", 568: "other_europe_nes", 899: "areas_nes"}


def partner_type(frame):
    kinds = np.where(frame.partner_code == frame.reporter_code, "self", "country")
    out = pd.Series(kinds, index=frame.index)
    out[frame.partner_code.isin(NES_PARTNERS)] = "unallocated_nes"
    out[frame.partner_code.isin(SELF_OR_NON_SUPPLIER)] = "non_supplier"
    return out


def bilateral_imports(a):
    """Country x product x partner x month, imports only. Heading rows are dropped to avoid double counting."""
    b = a[(a.flow == "M") & (a.product_group != "total_2710")].copy()
    b["partner_type"] = partner_type(b)
    keys = ["iso3", "reporter_code", "product_group", "partner_code", "partner_iso", "partner_name", "partner_type", "period"]
    out = b.groupby(keys, as_index=False, dropna=False).agg(
        import_mass_t=("mass_t", lambda s: s.sum(min_count=1)), import_value_usd=("value_usd", "sum"), hs_codes=("hs_code", lambda s: "|".join(sorted(set(s)))),
        classification=("classification", "first"), mass_source=("mass_source", lambda s: "|".join(sorted(set(s)))),
        any_mass_estimated=("mass_estimated", "any"), original_net_weight_kg=("net_weight_kg_original", "sum"), original_qty=("qty_original", "sum"),
        qty_unit=("qty_unit", "first"), mass_t_volume_estimate=("mass_t_volume_estimate", "sum"))
    out["month"] = pd.to_datetime(out.period.astype(str), format="%Y%m")
    return out.sort_values(["iso3", "product_group", "period", "partner_code"])


def _trailing_hhi(s, window=12, min_months=6):
    """Pooled 12-month HHI: shares of summed mass, so one thin month cannot dominate."""
    wide = s.pivot_table(index="period", columns="partner_code", values="import_mass_t", aggfunc="sum")
    periods = months_between(int(wide.index.min()), int(wide.index.max()))
    wide = wide.reindex(periods)
    observed = wide.notna().any(axis=1).rolling(window, min_periods=1).sum()
    pooled = wide.fillna(0).rolling(window, min_periods=1).sum()
    shares = pooled.div(pooled.sum(axis=1), axis=0)
    return (shares ** 2).sum(axis=1).where(observed >= min_months).rename("hhi_12m")


def supplier_concentration(b):
    """Shares use mass. Self-trade and non-supplier categories are excluded. Unallocated nes partners
    remain as one partner, and their share is reported, because dropping them would overstate HHI."""
    use = b[b.product_group.isin(["gasoline", "middle_heavy", "biodiesel_blend", "lpg"]) & ~b.partner_type.isin(["self", "non_supplier"])]
    blends = use[use.product_group.isin(["middle_heavy", "biodiesel_blend"])].assign(product_group="middle_incl_blends")
    use = pd.concat([use[use.product_group != "biodiesel_blend"], blends])
    by = use.groupby(["iso3", "product_group", "period", "partner_code", "partner_iso", "partner_type"], as_index=False, dropna=False).agg(
        import_mass_t=("import_mass_t", lambda s: s.sum(min_count=1)), value=("import_value_usd", "sum"))
    rows = []
    for (iso3, group), series in by.groupby(["iso3", "product_group"]):
        trailing = _trailing_hhi(series[series.import_mass_t > 0])
        for period, g in series.groupby("period"):
            priced = g[g.import_mass_t > 0].sort_values("import_mass_t", ascending=False)
            total = priced.import_mass_t.sum()
            if not total:
                continue
            share = priced.import_mass_t / total
            rows.append({"iso3": iso3, "product_group": group, "period": period, "supplier_total_mass_t": total, "active_suppliers": len(priced),
                         "largest_supplier_share": share.iloc[0], "top3_supplier_share": share.iloc[:3].sum(), "hhi": (share ** 2).sum(),
                         "hhi_12m": trailing.get(period), "largest_supplier_iso": priced.partner_iso.iloc[0], "russia_share": share[priced.partner_code == RUSSIA].sum(),
                         "nes_share": share[priced.partner_type == "unallocated_nes"].sum(),
                         "value_share_with_mass": priced.value.sum() / g.value.sum() if g.value.sum() else np.nan})
    c = pd.DataFrame(rows).sort_values(["iso3", "product_group", "period"])
    c["month"] = pd.to_datetime(c.period.astype(str), format="%Y%m")
    return c


def missing_class(frame):
    """Five-way classification. A genuine zero is never asserted: Comtrade holds no explicit
    zero-trade rows here, so a published month with no record stays ambiguous."""
    return np.select(
        [frame.import_mass_t.notna(), frame.import_mass_t_original.notna(), frame.import_value_usd.notna(),
         frame.published.eq(True), frame.inside_reporting_span.eq(True)],
        ["observed", "mass_rejected_by_check", "value_reported_mass_missing", "no_record_in_published_month", "reporting_interruption"],
        "outside_reporting_span")


def monthly_imports(b_monthly, conc, eligibility, cov, avail, window):
    months = months_between(window["start"], window["end"])
    countries = load_countries()
    grid = pd.MultiIndex.from_product([countries.iso3, RESEARCH_PRODUCTS, months], names=["iso3", "product_group", "period"]).to_frame(index=False)
    imp = b_monthly[b_monthly.flow == "M"].rename(columns={"mass_t": "import_mass_t", "mass_t_reported": "import_mass_t_original", "value_usd": "import_value_usd"})
    keep = ["iso3", "product_group", "period", "import_mass_t", "import_mass_t_original", "mass_t_incl_volume_estimate", "import_value_usd", "unit_value_usd_t", "uv_relative",
            "total_source", "n_partners", "partner_to_world_mass", "partner_to_world_value", "share_estimated", "share_mass_recovered_from_qty", "flag_uv_low", "flag_uv_high", "flag_mass_outlier", "classification"]
    m = grid.merge(imp[keep], how="left", on=["iso3", "product_group", "period"])
    exp = b_monthly[(b_monthly.flow == "X")].rename(columns={"mass_t": "export_mass_t"})[["iso3", "product_group", "period", "export_mass_t"]]
    m = m.merge(exp, how="left", on=["iso3", "product_group", "period"])
    pub = avail.assign(published=True)[["iso3", "period", "published", "first_released"]]
    m = m.merge(pub, how="left", on=["iso3", "period"])
    span = avail.groupby("iso3").period.agg(["min", "max"])
    m["inside_reporting_span"] = m.period.between(m.iso3.map(span["min"]), m.iso3.map(span["max"]))
    m["data_status"] = missing_class(m)
    m["month"] = pd.to_datetime(m.period.astype(str), format="%Y%m")
    m["publication_lag_days"] = (m.first_released - (m.month + pd.offsets.MonthEnd(0))).dt.days
    cols = ["iso3", "product_group", "period", "active_suppliers", "largest_supplier_share", "top3_supplier_share", "hhi", "hhi_12m", "largest_supplier_iso", "russia_share", "nes_share"]
    m = m.merge(conc[cols], how="left", on=["iso3", "product_group", "period"])
    m["country"] = m.iso3.map(countries.set_index("iso3").name)
    m["product_label"] = m.product_group.map(PRODUCT_LABELS)
    m["classification_flag"] = np.where(m.iso3.isin(cov[cov.product_split_suspect].iso3), "fuel_lines_suspect", "")
    blend = eligibility[eligibility.product_group == "middle_heavy"].set_index("iso3").blend_share
    high_blend = (m.product_group == "middle_heavy") & (m.iso3.map(blend).fillna(0) >= 0.2)
    m.loc[high_blend & (m.classification_flag == ""), "classification_flag"] = "271019_misses_blended_diesel"
    return m.drop(columns=["published", "inside_reporting_span"]).sort_values(["iso3", "product_group", "period"])


def external_monthly():
    """Long form so every value keeps its own source and original frequency."""
    oil = pd.read_parquet(PROCESSED / "ext_oil_prices.parquet")
    gpr = pd.read_parquet(PROCESSED / "ext_gpr.parquet")
    fx = pd.read_parquet(ANALYTICAL / "dataset_c_country_monthly.parquet")
    parts = [oil.assign(scope="global", iso3="WLD", indicator=oil.series + "_usd_bbl")[["period", "scope", "iso3", "indicator", "value", "unit", "source"]]]
    parts[0] = parts[0][parts[0].period >= 201001]
    g = gpr[~gpr.series.str.startswith("GPRC_") | gpr.series.isin(["GPRC_RUS", "GPRC_UKR", "GPRC_TUR", "GPRC_CHN"])]
    parts.append(g.assign(scope="global", iso3="WLD", indicator=g.series)[["period", "scope", "iso3", "indicator", "value", "unit", "source"]])
    specs = {"fx_lcu_per_usd_avg": ("LCU per USD, period average", "BIS WS_XRU"), "cpi_index": ("index", "IMF CPI, all items"), "gpr_country": ("index", "Caldara-Iacoviello country GPR")}
    for col, (unit, source) in specs.items():
        d = fx[["iso3", "period", col]].dropna().rename(columns={col: "value"})
        parts.append(d.assign(scope="country", indicator=col, unit=unit, source=source))
    out = pd.concat(parts, ignore_index=True)
    out["frequency"] = "M"
    out["month"] = pd.to_datetime(out.period.astype(str), format="%Y%m")
    return out.sort_values(["scope", "iso3", "indicator", "period"])


def transformation_log(monthly, b):
    target = monthly[monthly.product_group.isin(["gasoline", "middle_heavy", "middle_incl_blends"])]
    rows = [
        ("Sum partner rows to country total", "partner rows", int(b.import_mass_t.notna().sum()), "Original rows kept in petroleum_imports_bilateral"),
        ("Fall back to World row where no partner rows exist", "target series-months", int((target.total_source == "world_row").sum()), "Marked total_source = world_row"),
        ("Remove mass failing the low unit-value check", "target series-months", int((target.data_status == "mass_rejected_by_check").sum()), "import_mass_t_original keeps the value"),
        ("Use kg quantity where net weight is empty", "bilateral rows", int(b.mass_source.str.contains("qty_kg|altQty_kg").sum()), "mass_source records it; original fields kept"),
        ("Reject kg quantity that fails the density test", "bilateral rows", int(b.mass_source.str.contains("qty_rejected_density").sum()), "Labelled volume estimate kept apart from mass"),
        ("Convert kg to tonnes (kg / 1000)", "partner rows", int(b.import_mass_t.notna().sum()), "Original kg kept in original_net_weight_kg"),
        ("Interpolate or impute target values", "any", 0, "Not done"),
        ("Replace missing with zero", "any", 0, "Not done"),
    ]
    return pd.DataFrame(rows, columns=["operation", "unit", "records", "how_original_is_preserved"])


def build_all(settings):
    RESEARCH.mkdir(exist_ok=True)
    window = settings["screening"]["window"]
    a = pd.read_parquet(ANALYTICAL / "dataset_a_bilateral.parquet")
    b_monthly = pd.read_parquet(ANALYTICAL / "dataset_b_monthly.parquet")
    eligibility = pd.read_csv(REPORTS / "series_eligibility.csv")
    cov = pd.read_csv(REPORTS / "country_coverage_report.csv")
    avail = load_availability(settings["snapshot_id"])
    b = bilateral_imports(a)
    conc = supplier_concentration(b)
    monthly = monthly_imports(b_monthly, conc, eligibility, cov, avail, window)
    ext = external_monthly()
    annual = pd.read_parquet(ANALYTICAL / "dataset_c_country_annual.parquet")
    b.to_parquet(RESEARCH / "petroleum_imports_bilateral.parquet", index=False)
    monthly.to_parquet(RESEARCH / "petroleum_imports_monthly.parquet", index=False)
    conc.to_parquet(RESEARCH / "supplier_concentration_monthly.parquet", index=False)
    ext.to_parquet(RESEARCH / "external_indicators_monthly.parquet", index=False)
    annual.to_parquet(RESEARCH / "external_indicators_annual.parquet", index=False)
    transformation_log(monthly, b).to_csv(RESEARCH / "transformation_log.csv", index=False)
    log.info("research datasets: monthly %d, bilateral %d, concentration %d, external %d", len(monthly), len(b), len(conc), len(ext))
    return {"monthly": monthly, "bilateral": b, "concentration": conc, "external": ext, "annual": annual, "eligibility": eligibility, "coverage": cov, "availability": avail}
