"""Data quality audit. Every number in the reports is computed here from stored data."""
import json
import logging

import numpy as np
import pandas as pd

from src.preprocessing import cleaning
from src.preprocessing.harmonization import load_availability
from src.utils.config import ANALYTICAL, DATA, PROCESSED, RAW, REPORTS, load_settings, months_between

log = logging.getLogger(__name__)
TABLES = REPORTS / "tables"


def md(frame, floatfmt="{:,.2f}"):
    """Small markdown table writer, so reports need no extra dependency."""
    f = frame.copy()
    for c in f.columns:
        if pd.api.types.is_float_dtype(f[c]):
            f[c] = f[c].map(lambda v: "" if pd.isna(v) else floatfmt.format(v))
    f = f.astype(object).where(f.notna(), "")
    head = "| " + " | ".join(map(str, f.columns)) + " |\n|" + "---|" * len(f.columns) + "\n"
    return head + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in f.values) + "\n"


def imports(monthly, iso3=None):
    m = monthly[monthly.flow == "M"]
    return m[m.iso3 == iso3] if iso3 else m


def reconciliation(monthly, bilateral):
    """Annual Comtrade imports against the Kyrgyz balance, with and without the mass recovery."""
    balance = pd.read_parquet(PROCESSED / "ext_energy_balance.parquet")
    teb = balance[balance["item"] == "imports"].pivot(index="year", columns="fuel", values="kt")
    teb_x = balance[balance["item"] == "exports"].pivot(index="year", columns="fuel", values="kt").add_suffix("_x")
    kg = imports(monthly, "KGZ").assign(year=lambda d: d.period // 100)
    x = monthly[(monthly.iso3 == "KGZ") & (monthly.flow == "X")].assign(year=lambda d: d.period // 100)
    rows = []
    for year in range(2015, 2025):
        gas = kg[(kg.product_group == "gasoline") & (kg.year == year)]
        mid = kg[(kg.product_group == "middle_heavy") & (kg.year == year)]
        gas_x = x[(x.product_group == "gasoline") & (x.year == year)]
        # Rejected months count at their volume estimate here, so the annual total stays comparable
        gas_with_est = gas.mass_t.fillna(gas.mass_t_incl_volume_estimate).sum() / 1000
        rows.append({"year": year, "gas_usable_months": gas.mass_t.notna().sum(), "mid_usable_months": mid.mass_t.notna().sum(),
                     "gas_ct_kt": gas.mass_t.sum() / 1000, "gas_incl_volume_est_kt": gas_with_est,
                     "gas_teb_kt": teb.gasoline.get(year), "mid_ct_kt": mid.mass_t.sum() / 1000, "diesel_teb_kt": teb.diesel.get(year),
                     "fuel_oil_teb_kt": teb.fuel_oil.get(year), "gas_exports_ct_kt": gas_x.mass_t.sum() / 1000, "gas_exports_teb_kt": teb_x.gasoline_x.get(year)})
    r = pd.DataFrame(rows)
    r["months"] = r.gas_usable_months
    r["gas_ratio"] = r.gas_ct_kt / r.gas_teb_kt
    r["gas_ratio_incl_volume_est"] = r.gas_incl_volume_est_kt / r.gas_teb_kt
    r["mid_to_diesel"] = r.mid_ct_kt / r.diesel_teb_kt
    r["mid_to_diesel_plus_fueloil"] = r.mid_ct_kt / (r.diesel_teb_kt + r.fuel_oil_teb_kt)
    return r


def reproduce_pilot(monthly):
    """Compare the fresh pull against the 1 Nov pilot output without forcing agreement."""
    # Copy of ../pilot_evidence/outputs/kg_monthly.csv, kept in the repo so a fresh clone can run the check
    old = pd.read_csv(DATA / "pilot" / "kg_monthly.csv", index_col=0, parse_dates=True)
    kg = imports(monthly, "KGZ")
    rows = {}
    for group, col in (("gasoline", "gas_t"), ("middle_heavy", "mid_t")):
        s = kg[kg.product_group == group].set_index("month")
        new_w = s.mass_t_world.reindex(old.index)
        new_p = s.mass_t_reported.reindex(old.index)
        was_zero = (old[col].fillna(0) == 0) & old[col].notna()
        rows[group] = {"pilot_months_listed": int(old[col].notna().sum()), "pilot_true_positive_months": int((old[col] > 0).sum()), "pilot_zero_mass_months": int(was_zero.sum()),
                       "fresh_positive_months": int((new_p > 0).sum()), "months_recovered": int(((new_p > 0) & ~(old[col] > 0)).sum()),
                       "fresh_usable_after_checks": int(s.mass_t.reindex(old.index).notna().sum()),
                       "median_abs_diff_world_pct": float(((new_w - old[col]).abs() / old[col].where(old[col] > 0)).median() * 100)}
    return pd.DataFrame(rows).T.reset_index(names="product_group")


def completeness(monthly, window):
    rows = []
    start, end = window["start"], window["end"]
    expected = len(months_between(start, end))
    for (iso3, group), s in imports(monthly).groupby(["iso3", "product_group"]):
        s = s[s.period.between(start, end)]
        status = s.month_status.value_counts()
        usable = s[s.month_status == "usable"]
        rows.append({"iso3": iso3, "product_group": group, "expected_months": expected, "usable": int(status.get("usable", 0)),
                     "first": usable.period.min() if len(usable) else None, "last": usable.period.max() if len(usable) else None,
                     "not_published": expected - len(s) + int(status.get("not_published", 0)), "product_absent": int(status.get("published_product_absent", 0)),
                     "value_no_mass": int(status.get("value_without_mass", 0)), "uv_rejected": int(status.get("unit_value_rejected", 0)),
                     "pct_usable": 100 * status.get("usable", 0) / expected, "median_partners": s.n_partners.median(),
                     "median_value_share_with_mass": s.value_share_with_mass.median(), "share_months_estimated_gt_50pct": float((s.share_estimated > .5).mean())})
    return pd.DataFrame(rows)


def consistency(raw, bilateral, monthly):
    pos = raw[(pd.to_numeric(raw.netWgt, errors="coerce") > 0) & (raw.qtyUnitAbbr.astype(str).str.lower() == "kg") & (pd.to_numeric(raw.qty, errors="coerce") > 0)]
    agree = ((pos.netWgt - pos.qty).abs() / pos.netWgt <= 0.01).mean() if len(pos) else np.nan
    world = raw[raw.partnerCode == 0]
    checks = {
        "raw rows": len(raw),
        "duplicates on natural key": int(raw.duplicated(cleaning.KEY).sum()),
        "negative trade value rows": int((pd.to_numeric(raw.primaryValue, errors="coerce") < 0).sum()),
        "negative net weight rows": int((pd.to_numeric(raw.netWgt, errors="coerce") < 0).sum()),
        "rows with zero value": int((pd.to_numeric(raw.primaryValue, errors="coerce") == 0).sum()),
        "rows with netWgt null or zero": int((pd.to_numeric(raw.netWgt, errors="coerce").fillna(0) == 0).sum()),
        "share netWgt and kg qty agree within 1%": None if pd.isna(agree) else round(float(agree), 4),
        "rows with partner2/transport/customs not total": int(((raw.partner2Code != 0) | (raw.motCode != 0) | (raw.customsCode != "C00")).sum()),
        "World rows": len(world),
        "isAggregate true among partner rows": int(raw[raw.partnerCode != 0].isAggregate.fillna(False).astype(bool).sum()),
    }
    units = raw.groupby(raw.qtyUnitAbbr.astype(str)).size().rename("rows").reset_index()
    source = bilateral.groupby(["product_group", "mass_source"]).agg(rows=("mass_source", "size"), mass_kt=("mass_t", lambda s: s.sum() / 1000)).reset_index()
    estimation = raw.groupby(["isReported", "legacyEstimationFlag"], dropna=False).size().rename("rows").reset_index()
    classification = raw.groupby(["reporterISO", "classificationCode"]).period.agg(["min", "max", "nunique"]).reset_index()
    return checks, units, source, estimation, classification


def heading_check(raw):
    """HS 2710 heading against the sum of its six-digit lines, World rows, by value."""
    w = raw[(raw.partnerCode == 0) & (raw.flowCode == "M") & raw.cmdCode.str.startswith("2710")]
    head = w[w.cmdCode == "2710"].groupby(["reporterISO", "period"]).primaryValue.sum()
    lines = w[w.cmdCode != "2710"].groupby(["reporterISO", "period"]).primaryValue.sum()
    ratio = (lines / head.where(head > 0)).dropna()
    return ratio.groupby("reporterISO").agg(months="size", median_ratio="median", months_off_by_1pct=lambda s: int(((s - 1).abs() > .01).sum())).reset_index()


def partner_world(monthly, tol):
    m = imports(monthly)
    m = m[m.product_group.isin(["gasoline", "middle_heavy"]) & m.partner_to_world_value.notna()]
    return m.groupby(["iso3", "product_group"]).agg(months=("period", "size"), value_ratio_median=("partner_to_world_value", "median"),
                                                    months_value_off=("partner_to_world_value", lambda s: int(((s - 1).abs() > tol).sum())),
                                                    months_world_mass_missing_or_zero=("mass_t_world", lambda s: int((s.fillna(0) == 0).sum()))).reset_index()


def publication_lag(monthly):
    m = imports(monthly)
    m = m[(m.product_group == "gasoline") & (m.period >= 202101)]  # earlier years are mostly backfilled releases
    return m.groupby("iso3").publication_lag_days.describe()[["count", "min", "50%", "max"]].rename(columns={"50%": "median"}).reset_index()


def external_match(window):
    g = pd.read_parquet(ANALYTICAL / "dataset_c_global_monthly.parquet").set_index("period")
    c = pd.read_parquet(ANALYTICAL / "dataset_c_country_monthly.parquet")
    a = pd.read_parquet(ANALYTICAL / "dataset_c_country_annual.parquet")
    months = months_between(window["start"], window["end"])
    tier = pd.read_csv(REPORTS / "country_coverage_report.csv")
    panel = tier[tier.tier_final.isin(["Tier 1", "Tier 2"])].iso3.tolist()
    rows = [{"series": s, "scope": "global", "frequency": "M", "countries": "all", "first": int(g[s].first_valid_index()), "last": int(g[s].last_valid_index()),
             "pct_window_covered": 100 * g[s].reindex(months).notna().mean()} for s in g.columns]
    for s in ["fx_lcu_per_usd_avg", "cpi_index", "gpr_country"]:
        d = c[c.iso3.isin(panel) & c[s].notna()]
        win = d[d.period.isin(months)]
        rows.append({"series": s, "scope": "country", "frequency": "M", "countries": f"{d.iso3.nunique()} of {len(panel)}", "first": d.period.min(), "last": d.period.max(),
                     "pct_window_covered": 100 * len(win) / (len(months) * len(panel))})
    for s in a.columns.drop(["iso3", "year"]):
        d = a[a.iso3.isin(panel) & a[s].notna()]
        rows.append({"series": s, "scope": "country", "frequency": "A", "countries": f"{d.iso3.nunique()} of {len(panel)}", "first": d.year.min(), "last": d.year.max(),
                     "pct_window_covered": 100 * len(d) / ((window["end"] // 100 - window["start"] // 100 + 1) * len(panel))})
    return pd.DataFrame(rows)


def kyrgyz_product_coverage(monthly, bilateral):
    m = imports(monthly, "KGZ")
    rows = []
    for group, s in m.groupby("product_group"):
        u = s[s.month_status == "usable"]
        rows.append({"product_group": group, "first": u.period.min(), "last": u.period.max(), "usable_months": len(u), "usable_from_2015": int((u.period >= 201501).sum()),
                     "median_t": u.mass_t.median(), "partner_months": int(s.n_partners.notna().sum()), "median_partners": s.n_partners.median()})
    return pd.DataFrame(rows)


def inventory(settings):
    d = ANALYTICAL
    b = pd.read_parquet(d / "dataset_a_bilateral.parquet")
    m = pd.read_parquet(d / "dataset_b_monthly.parquet")
    rows = [
        ("Dataset A bilateral", "UN Comtrade", "HS6 x partner x month x flow", f"{b.period.min()}-{b.period.max()}", f"{b.iso3.nunique()} reporters", len(b), "Public preview; key for full panel"),
        ("Dataset B monthly", "UN Comtrade", "country x product x month x flow", f"{m.period.min()}-{m.period.max()}", f"{m.iso3.nunique()} reporters", len(m), "Derived"),
    ]
    for name, src, grain, access in [("dataset_c_global_monthly", "EIA, Caldara-Iacoviello", "global x month", "Public files"), ("dataset_c_country_monthly", "BIS, IMF, Caldara-Iacoviello", "country x month", "Public API/files"),
                                     ("dataset_c_country_annual", "World Bank WDI", "country x year (annual, not interpolated)", "Public API")]:
        f = pd.read_parquet(d / f"{name}.parquet")
        col = "year" if "year" in f else "period"
        rows.append((name, src, grain, f"{f[col].min()}-{f[col].max()}", f"{f.iso3.nunique()} countries" if "iso3" in f else "global", len(f), access))
    i = pd.read_parquet(d / "dataset_d_integrated.parquet")
    rows.append(("dataset_d_integrated", "Datasets B and C, supplier metrics", "eligible series x month, same-month values", f"{i.period.min()}-{i.period.max()}", f"{i.iso3.nunique()} countries", len(i), "Derived"))
    e = pd.read_parquet(PROCESSED / "ext_energy_balance.parquet")
    rows.append(("Kyrgyz Fuel and Energy Balance", "National Statistical Committee", "fuel x year (annual, kt)", f"{e.year.min()}-{e.year.max()}", "Kyrgyzstan", len(e), "Public XLSX, 2024 edition"))
    return pd.DataFrame(rows, columns=["dataset", "source", "granularity", "period", "coverage", "rows", "access"])


def build_reports(settings=None):
    settings = settings or load_settings()
    TABLES.mkdir(parents=True, exist_ok=True)
    window = settings["screening"]["window"]
    snapshot = settings["snapshot_id"]
    monthly = pd.read_parquet(ANALYTICAL / "dataset_b_monthly.parquet")
    bilateral = pd.read_parquet(ANALYTICAL / "dataset_a_bilateral.parquet")
    conc = pd.read_parquet(ANALYTICAL / "supplier_concentration.parquet")
    raw = pd.read_parquet(PROCESSED / "raw_bilateral_records.parquet")
    cov = pd.read_csv(REPORTS / "country_coverage_report.csv")
    stats = json.loads((PROCESSED / "build_stats.json").read_text(encoding="utf-8"))

    rec = reconciliation(monthly, bilateral)
    pilot = reproduce_pilot(monthly)
    comp = completeness(monthly, window)
    checks, units, source, estimation, classification = consistency(raw, bilateral, monthly)
    heading = heading_check(raw)
    pw = partner_world(monthly, settings["quality"]["partner_vs_world_tolerance"])
    lag = publication_lag(monthly)
    ext = external_match(window)
    kg_cov = kyrgyz_product_coverage(monthly, bilateral)
    inv = inventory(settings)
    tables = {"reconciliation_kgz": rec, "pilot_reproduction": pilot, "completeness": comp, "unit_counts": units, "mass_source": source, "estimation_flags": estimation,
              "classification_periods": classification, "heading_vs_lines": heading, "partner_vs_world": pw, "publication_lag": lag, "external_match": ext, "kyrgyz_product_coverage": kg_cov, "data_inventory": inv}
    for name, t in tables.items():
        t.to_csv(TABLES / f"{name}.csv", index=False)

    full = rec[(rec.months == 12) & rec.gas_teb_kt.notna()]
    gas_mape = lambda f: float((abs(f.gas_ct_kt - f.gas_teb_kt) / f.gas_teb_kt).mean() * 100)
    summary = {
        "gas_mape_all_full_years_pct": gas_mape(full), "gas_mape_2018_on_pct": gas_mape(full[full.year >= 2018]),
        "kgz_flagged_outlier_months": monthly[(monthly.iso3 == "KGZ") & (monthly.flow == "M") & monthly.flag_mass_outlier].groupby("product_group").period.apply(list).to_dict(),
        "kgz_uv_rejected": monthly[(monthly.iso3 == "KGZ") & monthly.flag_unit_value.fillna(False).astype(bool)][["product_group", "flow", "period", "unit_value_usd_t"]].to_dict("records"),
        "usable_obs_by_product": imports(monthly).query("month_status == 'usable'").groupby("product_group").size().to_dict(),
        "reporters_bilateral": int(bilateral.iso3.nunique()), "concentration_rows": len(conc), **stats, "checks": checks,
    }
    (REPORTS / "summary_metrics.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")

    kg_comp = comp[comp.iso3 == "KGZ"]
    tier_cols = ["country", "iso3", "tier_final", "tier", "product_split_suspect", "gasoline_first", "gasoline_last", "gasoline_months", "gasoline_mass_share", "middle_heavy_months", "middle_heavy_mass_share", "exclusion_reason"]
    report = f"""# Data quality report

Snapshot `{snapshot}`. Screening window {window['start']}-{window['end']}. Generated by `python run.py reports`; every figure comes from stored data.
Detail tables are in `reports/tables/`.

## 1. Kyrgyz pilot reproduction

{md(pilot)}
`pilot_zero_mass_months` were counted as observed in the proposal's 136, although the World row held no usable mass.

## 2. Kyrgyz coverage by product

{md(kg_cov)}
## 3. Reconciliation with the Kyrgyz Fuel and Energy Balance

Imports in kt. `gas_ct_kt` is the clean series. `gas_incl_volume_est_kt` adds rejected months at their labelled volume estimate, for this annual comparison only.

{md(rec)}
Gasoline mean absolute difference over full years: {summary['gas_mape_all_full_years_pct']:.1f}% (all), {summary['gas_mape_2018_on_pct']:.1f}% (2018 onward).
`mid_to_diesel_plus_fueloil` is the fairer comparison, because HS 2710.19 holds both fuels, yet it still includes kerosene, jet fuel and lubricants the balance tables do not cover here.

## 4. Completeness, Kyrgyzstan

{md(kg_comp)}
## 5. Consistency checks

{md(pd.DataFrame(list(checks.items()), columns=['check', 'result']))}
### Quantity units

{md(units)}
### Where mass came from

{md(source)}
### Estimation flags

{md(estimation)}
## 6. Partner records against World rows

{md(pw)}
## 7. HS 2710 heading against its six-digit lines (value, World)

{md(heading)}
## 8. Publication lag, days from month end to first release

{md(lag, '{:,.0f}')}
## 9. External indicators, matched over the screening window and panel

{md(ext, '{:,.1f}')}
## 10. Country tiers

{md(cov[tier_cols])}
"""
    (REPORTS / "data_quality_report.md").write_text(report, encoding="utf-8")
    (REPORTS / "data_inventory.md").write_text(f"# Data inventory\n\nSnapshot `{snapshot}`.\n\n{md(inv)}\n", encoding="utf-8")
    log.info("reports written")
