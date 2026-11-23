"""Country-product coverage matrix with transparent series tiers. Every candidate country and
product appears, including those with nothing usable, so nothing is dropped silently.

Tier 1, main experiment: target product, at least 120 observed months, at least 85% temporal coverage,
no gap over 6 months, reaches June 2025 or later, at least 84 months of supplier data, median of at least
100 t, exports under half of imports, and no classification flag.
Tier 2, usable with documented limits: at least 84 observed months, at least 84 months of supplier data, median of
at least 100 t, no suspected fuel mislabelling. Non-target LPG can reach Tier 2 at most.
Tier 3, unsuitable for the main experiment: everything else.
"""
import numpy as np
import pandas as pd

from src.preprocessing.harmonization import _longest_gap
from src.utils.config import load_countries, months_between

TARGET = {"gasoline", "middle_heavy", "middle_incl_blends"}
CONTEXT_ONLY = {"crude", "total_2710", "biodiesel_blend"}
RULES = {"t1_months": 120, "t1_coverage": 85.0, "t1_gap": 6, "t1_last": 202506, "min_supplier_months": 84, "t2_months": 84, "min_t": 100.0, "max_x_m": 0.5}


def reason_for(r):
    if r.iso3 == "LIE":
        return "Not a Comtrade reporter; reported within Switzerland"
    if r.observed_months == 0:
        return "No monthly data for this product" if r.published_months else "Country publishes no monthly data"
    if r.product_group in CONTEXT_ONLY:
        return "Context series, not a forecasting target"
    if r.classification_flag == "fuel_lines_suspect":
        return "Fuels seem filed under another HS line"
    if r.observed_months < RULES["t2_months"]:
        return f"Only {int(r.observed_months)} observed months"
    if r.supplier_months < RULES["min_supplier_months"]:
        return f"Only {int(r.supplier_months)} months of supplier data"
    if r.median_t < RULES["min_t"]:
        return "Trivial volume"
    return ""


def limits_for(r):
    notes = []
    if r.exports_to_imports >= RULES["max_x_m"]:
        notes.append(f"exports {r.exports_to_imports:.2f} of imports")
    if r.classification_flag == "271019_misses_blended_diesel":
        notes.append("misses blended diesel")
    if r.observed_months < RULES["t1_months"]:
        notes.append(f"{int(r.observed_months)} months")
    if pd.notna(r.last_month) and r.last_month < RULES["t1_last"]:
        notes.append(f"ends {int(r.last_month)}")
    if r.coverage_pct < RULES["t1_coverage"]:
        notes.append(f"coverage {r.coverage_pct:.0f}%")
    if pd.notna(r.longest_gap) and r.longest_gap > RULES["t1_gap"]:
        notes.append(f"gap of {int(r.longest_gap)} months")
    if r.annual_mismatch_years:
        notes.append(f"monthly sum off from annual data by over 25% in {r.annual_mismatch_years}")
    return "; ".join(notes)


def annual_mismatches(annual_check):
    """Years where monthly and annual submissions differ by over 25%. A noted limit, not a demotion."""
    big = annual_check[(annual_check.ratio - 1).abs() > .25]
    out = {}
    for r in big.itertuples():
        for product in ([r.group] if r.group == "gasoline" else ["middle_heavy", "middle_incl_blends"]):
            out.setdefault((r.reporterISO, product), []).append(str(r.year))
    return {k: ",".join(v) for k, v in out.items()}


def matrix(monthly, external, avail, window, annual_check):
    mismatch = annual_mismatches(annual_check)
    months = months_between(window["start"], window["end"])
    fx = external[external.indicator == "fx_lcu_per_usd_avg"].groupby("iso3").period.nunique()
    cpi = external[external.indicator == "cpi_index"].groupby("iso3").period.nunique()
    published = avail[avail.period.between(window["start"], window["end"])].groupby("iso3").period.nunique()
    rows = []
    for (iso3, country, product), s in monthly.groupby(["iso3", "country", "product_group"]):
        observed = s[s.data_status == "observed"]
        n = len(observed)
        exports, imports = s.export_mass_t.sum(), observed.import_mass_t.sum()
        status = s.data_status.value_counts()
        rows.append({"iso3": iso3, "country": country, "product_group": product, "first_month": observed.period.min() if n else None, "last_month": observed.period.max() if n else None,
                     "observed_months": n, "missing_months": len(months) - n, "coverage_pct": 100 * n / len(months), "longest_gap": _longest_gap(observed.period, observed.period.min(), observed.period.max()) if n else None,
                     "reporting_interruptions": int(status.get("reporting_interruption", 0)), "rejected_months": int(status.get("mass_rejected_by_check", 0)), "value_no_mass_months": int(status.get("value_reported_mass_missing", 0)),
                     "no_record_months": int(status.get("no_record_in_published_month", 0)), "outside_span_months": int(status.get("outside_reporting_span", 0)),
                     "median_t": observed.import_mass_t.median() if n else 0.0, "exports_to_imports": exports / imports if imports else np.nan,
                     "supplier_months": int(s.active_suppliers.notna().sum()), "bilateral_available": bool(s.active_suppliers.notna().any()), "partner_vs_world_only": "partner" if (s.total_source == "partner_sum").any() else ("world only" if n else "none"),
                     "fx_months": int(fx.get(iso3, 0)), "cpi_months": int(cpi.get(iso3, 0)), "published_months": int(published.get(iso3, 0)),
                     "classification_flag": s.classification_flag.iloc[0], "annual_mismatch_years": mismatch.get((iso3, product), ""), "median_lag_days_2021_on": s[s.period >= 202101].publication_lag_days.median()})
    m = pd.DataFrame(rows)
    t2 = (m.observed_months >= RULES["t2_months"]) & (m.supplier_months >= RULES["min_supplier_months"]) & (m.median_t >= RULES["min_t"]) & (m.classification_flag != "fuel_lines_suspect") & ~m.product_group.isin(CONTEXT_ONLY)
    gap_ok = m.longest_gap.fillna(99) <= RULES["t1_gap"]
    t1 = t2 & m.product_group.isin(TARGET) & (m.observed_months >= RULES["t1_months"]) & (m.coverage_pct >= RULES["t1_coverage"]) & gap_ok & (m.last_month >= RULES["t1_last"]) \
        & (m.exports_to_imports.fillna(0) < RULES["max_x_m"]) & (m.classification_flag == "")
    m["quality_tier"] = np.select([t1, t2], ["Tier 1", "Tier 2"], "Tier 3")
    m["reason_or_limits"] = [reason_for(r) if r.quality_tier == "Tier 3" else limits_for(r) for r in m.itertuples()]
    return m.sort_values(["product_group", "quality_tier", "iso3"])


def main_panel(cov):
    """Main experiment: Tier 1 gasoline and 271019, swapping in blends for reporters flagged on 271019."""
    return cov[cov.product_group.isin(["gasoline", "middle_heavy", "middle_incl_blends"])].query("quality_tier == 'Tier 1'")
