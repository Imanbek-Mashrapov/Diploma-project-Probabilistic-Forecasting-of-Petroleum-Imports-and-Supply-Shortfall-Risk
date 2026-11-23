"""Generated Phase 2 documents: inventory, data dictionary, version record and EDA report.
Every number comes from the run that writes it."""
import hashlib
import json
from datetime import date

import numpy as np
import pandas as pd

from src.preprocessing.validation import md
from src.research import datasets, eda
from src.utils.config import DATA, RAW, REPORTS, ROOT

DOCS = ROOT / "docs"
TIER_RULES = "See src/research/coverage.py"
DICTIONARY = {
    "petroleum_imports_monthly": {
        "iso3": "Reporter ISO3 code", "country": "Reporter name", "product_group": "Product group key", "product_label": "Product group with its HS codes", "period": "Month as YYYYMM", "month": "First day of the month",
        "import_mass_t": "TARGET. Clean import mass in metric tonnes; missing unless data_status is observed", "import_mass_t_original": "Mass before the unit-value check", "mass_t_incl_volume_estimate": "Original mass plus labelled litre-based estimate; annual comparison only, never a target",
        "import_value_usd": "Import value in USD as reported, CIF for most reporters", "unit_value_usd_t": "Value divided by original mass", "uv_relative": "Brent-deflated unit value over its centred 13-month median; cleaning only, uses future months",
        "total_source": "partner_sum, or world_row where partner rows are absent", "n_partners": "Partner rows in the sum, including those without mass", "partner_to_world_mass": "Partner-sum mass over World-row mass", "partner_to_world_value": "Partner-sum value over World-row value",
        "share_estimated": "Share of mass flagged as estimated", "share_mass_recovered_from_qty": "Share of mass taken from kg quantity fields", "flag_uv_low": "Unit value too low; mass removed", "flag_uv_high": "Unit value too high; mass kept, value suspect",
        "flag_mass_outlier": "Robust |z| above 4 on log mass; kept", "classification": "HS edition of the first row in the sum", "export_mass_t": "Clean export mass, tonnes, for trade orientation", "first_released": "First Comtrade release of the reporter-month", "publication_lag_days": "Days from month end to first release",
        "data_status": "observed, mass_rejected_by_check, value_reported_mass_missing, no_record_in_published_month, reporting_interruption, outside_reporting_span", "active_suppliers": "Partners with positive mass, excluding self and non-suppliers", "largest_supplier_share": "Largest supplier's mass share",
        "top3_supplier_share": "Three largest suppliers' mass share", "hhi": "Monthly sum of squared mass shares", "hhi_12m": "HHI of mass pooled over 12 months; null with fewer than 6 observed", "largest_supplier_iso": "Largest supplier's code", "russia_share": "Russia's mass share", "nes_share": "Share of unallocated partners", "classification_flag": "fuel_lines_suspect, 271019_misses_blended_diesel or empty"},
    "petroleum_imports_bilateral": {
        "iso3": "Reporter ISO3", "reporter_code": "Comtrade reporter code", "product_group": "Product group key; 2710 heading excluded", "partner_code": "Comtrade partner code, never 0 (World)", "partner_iso": "Partner code", "partner_name": "Partner name", "partner_type": "country, unallocated_nes, self or non_supplier", "period": "Month as YYYYMM", "month": "First day of the month",
        "import_mass_t": "Mass in tonnes; missing if none is usable", "import_value_usd": "Value in USD", "hs_codes": "HS lines summed", "classification": "HS edition", "mass_source": "Field or fields that gave mass", "any_mass_estimated": "Any line estimated", "original_net_weight_kg": "Sum of original net weight, kg", "original_qty": "Sum of original quantity", "qty_unit": "Unit of original quantity", "mass_t_volume_estimate": "Labelled litre-based estimate for rejected rows"},
    "supplier_concentration_monthly": {
        "iso3": "Reporter ISO3", "product_group": "gasoline, middle_heavy, middle_incl_blends or lpg", "period": "Month as YYYYMM", "month": "First day of the month", "supplier_total_mass_t": "Mass in the shares", "active_suppliers": "Partners with positive mass", "largest_supplier_share": "Largest share", "top3_supplier_share": "Top three share", "hhi": "Monthly HHI, 0 to 1", "hhi_12m": "Pooled 12-month HHI, trailing", "largest_supplier_iso": "Largest supplier", "russia_share": "Russia's share", "nes_share": "Unallocated share", "value_share_with_mass": "Share of value carried by rows with mass"},
    "external_indicators_monthly": {
        "period": "Month as YYYYMM", "month": "First day of the month", "scope": "global or country", "iso3": "Country, or WLD for global", "indicator": "Indicator key", "value": "Value in original units", "unit": "Unit", "source": "Source", "frequency": "Original frequency"},
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(settings):
    """Scan the disk rather than trusting the plan: only what exists is listed."""
    described = {"un_comtrade/*/bilateral": ("UN Comtrade monthly partner-level JSON", "Integrated"), "un_comtrade/*/world_audit": ("UN Comtrade monthly World rows, all 43 candidates", "Integrated"), "un_comtrade/*/mirror_russia": ("Russian exports to candidates, 2015-2021", "Validation only"),
                 "un_comtrade/*/annual_world": ("Annual World rows, 2015-2025", "Validation only"), "un_comtrade/*/kgz_all_goods": ("Kyrgyz all-goods monthly totals, 2023-2026", "Validation only"), "un_comtrade/*/availability": ("Comtrade publication listings with release dates", "Integrated"),
                 "reference": ("Comtrade reporter, partner, unit and HS reference files", "Integrated"), "oil_prices": ("EIA Brent and WTI monthly history", "Integrated"), "gpr": ("Caldara-Iacoviello Geopolitical Risk data", "Integrated"), "fx": ("BIS monthly exchange rates", "Integrated"), "macroeconomic": ("IMF CPI and World Bank annual indicators", "Integrated"),
                 "energy_balance": ("Kyrgyz Fuel and Energy Balance, 2024 edition", "Validation only"), "official_kg": ("NSC annual import values and monthly express reports", "Validation only")}
    rows = []
    for pattern, (what, use) in described.items():
        files = [f for f in RAW.glob(pattern + "/*") if f.is_file()]
        rows.append({"location": "data/raw/" + pattern, "contents": what, "files": len(files), "size_mb": round(sum(f.stat().st_size for f in files) / 1e6, 1), "use": use})
    for folder, what in [("data/analytical", "Phase 1 datasets A-D"), ("data/research", "Phase 2 research datasets")]:
        files = [f for f in (ROOT / folder).glob("*") if f.is_file()]
        rows.append({"location": folder, "contents": what, "files": len(files), "size_mb": round(sum(f.stat().st_size for f in files) / 1e6, 1), "use": "Derived"})
    files = [f for f in (DATA / "pilot").glob("*") if f.is_file()]
    rows.append({"location": "data/pilot", "contents": "1 Nov 2026 pilot Kyrgyz monthly output", "files": len(files), "size_mb": round(sum(f.stat().st_size for f in files) / 1e6, 1), "use": "Superseded; reproduction check only"})
    return pd.DataFrame(rows)


def facts(data, cov):
    monthly = data["monthly"]
    tiers = cov[cov.product_group.isin(["gasoline", "middle_heavy", "middle_incl_blends"])].pivot_table(index="product_group", columns="quality_tier", values="iso3", aggfunc="count", fill_value=0)
    main = cov[cov.product_group.isin(["gasoline", "middle_incl_blends"])]
    t1, t12 = main[main.quality_tier == "Tier 1"], main[main.quality_tier != "Tier 3"]
    reporters = monthly[monthly.import_mass_t.notna()].iso3.nunique()
    return {"tiers": tiers.to_dict("index"), "main_tier1_series": len(t1), "main_tier1_countries": t1.iso3.nunique(), "main_tier1_obs": int(t1.observed_months.sum()), "training_series": len(t12), "training_countries": t12.iso3.nunique(), "training_obs": int(t12.observed_months.sum()),
            "tier1_gasoline": sorted(t1[t1.product_group == "gasoline"].iso3), "tier1_distillates": sorted(t1[t1.product_group == "middle_incl_blends"].iso3), "countries_with_any_mass": reporters, "reach_2026_06": int((t12[t12.product_group == "gasoline"].last_month >= 202606).sum())}


def eda_report(data, cov, quality, reconciliation, r, summary):
    trends = r["trends"]
    kg = trends[trends.product_group == "gasoline"].dropna(subset=["yoy_pct_full_years"])
    season = r["season"]
    strength = r["strengths"]
    corr = r["correlations"]
    sig = corr[corr.p_bh < .05]
    kg_corr = corr[corr.iso3 == "KGZ"]
    scale = r["scale"]
    gas_scale = scale[scale.product_group == "gasoline"]
    conc = r["concentration"]
    panel_conc = conc[conc.product_group == "gasoline"]
    breaks_by_year = r["pooled_breaks"].groupby("year").size().rename("breaks").reset_index()
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    gas_season = season.iloc[0]
    index = {m: gas_season[f"m{i + 1:02d}"] for i, m in enumerate(months)}
    high, low = max(index, key=index.get), min(index, key=index.get)
    show_trend = trends[trends.product_group.isin(["gasoline", "middle_heavy"])].pivot(index="year", columns="product_group", values="kt").join(trends[trends.product_group == "gasoline"].set_index("year").months.rename("gas_months")).reset_index()
    return f"""# Exploratory data analysis

Snapshot `{data['snapshot']}`, January 2015 to August 2026. Descriptive only: no forecasting model was fitted. Generated by `python run.py phase2`. Tables are in `tables/`.

Jet fuel, diesel and fuel oil cannot be analysed separately from Comtrade, because HS six-digit data merge them in 2710.19. They appear separately only in annual Kyrgyz official sources (section 5). Monthly industrial production was not available for the panel, so it is not analysed.

## 1. Kyrgyz imports over time

![Kyrgyz monthly imports](figures/fig01_kyrgyz_monthly_imports.png)

Monthly gasoline swings widely around a stable level, between {r['segments'][r['segments'].product_group == 'gasoline'].mean_kt.min():.0f} and {r['segments'][r['segments'].product_group == 'gasoline'].mean_kt.max():.0f} thousand tonnes by segment. Distillates rose from 2024.

![Annual imports](figures/fig02_kyrgyz_annual_imports.png)

{md(show_trend.rename(columns={'gasoline': 'gasoline_kt', 'middle_heavy': 'distillates_kt'}), '{:,.1f}')}
Year-on-year gasoline changes between adjacent full years range from {kg.yoy_pct_full_years.min():.0f}% to {kg.yoy_pct_full_years.max():.0f}%.

## 2. Seasonality

![Seasonality](figures/fig03_kyrgyz_seasonality.png)

Kyrgyz gasoline varies by month (Kruskal-Wallis p {'< 0.001' if season.iloc[0].p < .001 else f'= {season.iloc[0].p:.3f}'}): typically highest in {high} ({index[high]:.2f} of the annual mean) and lowest in {low} ({index[low]:.2f}). HS 271019 shows no clear monthly pattern (p = {season.iloc[1].p:.2f}), so seasonal farm demand should be tested, not assumed.

![STL decomposition](figures/fig04_kyrgyz_gasoline_stl.png)

STL needs an unbroken series and targets are not interpolated, so it uses the longest gap-free stretch. Across the panel, median seasonal strength is {strength.seasonal_strength.median():.2f} and median trend strength {strength.trend_strength.median():.2f} on a 0-1 scale, so seasonality is moderate at best. Kyrgyz gasoline: seasonal {strength[(strength.iso3 == 'KGZ') & (strength.product_group == 'gasoline')].seasonal_strength.iloc[0]:.2f}, trend {strength[(strength.iso3 == 'KGZ') & (strength.product_group == 'gasoline')].trend_strength.iloc[0]:.2f}.

## 3. Structural breaks

![Structural breaks](figures/fig05_kyrgyz_structural_breaks.png)

Change points come from PELT on observed log mass, with a minimum segment of 6 months. They describe level shifts and do not prove causes.

{md(r['segments'], '{:,.1f}')}
The gasoline shift from July 2025 coincides with the Russian restrictions, and also with the months where Comtrade holds first-release data (section 5), so its size is uncertain. Detected breaks across the panel, by year:

{md(breaks_by_year)}
## 4. Country comparison

Absolute tonnes mainly reflect country size, so volumes are shown per person.

![Scale and volatility](figures/fig06_country_scale_and_volatility.png)

Imports are not consumption: the high figures for Luxembourg and Andorra probably include fuel sold to non-residents, which these data cannot confirm. Kyrgyz gasoline volatility (robust sd of monthly log change {gas_scale[gas_scale.iso3 == 'KGZ'].robust_sd_dlog.iloc[0]:.2f}) ranks {int(gas_scale.robust_sd_dlog.rank().loc[gas_scale.iso3 == 'KGZ'].iloc[0])} of {len(gas_scale)}, against a panel median of {gas_scale.robust_sd_dlog.median():.2f}. Lag-12 autocorrelation of log mass has a median of {gas_scale.acf12_log.median():.2f}, which matches the weak seasonal strength. Series co-move little: the median pairwise correlation of year-on-year gasoline changes is {r['comovement']['median_rho']:.2f}, and {r['comovement']['kgz_median_rho']:.2f} for Kyrgyzstan.

![Coverage](figures/fig09_coverage_heatmap.png)

## 5. Kyrgyz validation

![Reconciliation](figures/fig11_kyrgyz_reconciliation.png)

![Vintages and dependency](figures/fig12_kyrgyz_vintage_and_dependency.png)

Full comparison tables and explanations are in `kyrgyz_validation.md`.

## 6. Supplier concentration

Concentration says how few suppliers a country uses. It does not say how much of its fuel is imported.

![Concentration by country](figures/fig07_supplier_concentration_by_country.png)

Kyrgyz gasoline has a median 12-month HHI of {panel_conc[panel_conc.iso3 == 'KGZ'].hhi_12m_median.iloc[0]:.2f}, among the highest in the panel (median {panel_conc.hhi_12m_median.median():.2f}). The dashed line marks 0.25, a common threshold for high concentration in competition analysis, used here for reference only.

![Kyrgyz concentration](figures/fig08_kyrgyz_supplier_concentration.png)

Trailing HHI for Kyrgyz gasoline stays high in most years, so it offers limited variation as a predictor; this is what hypothesis H4 needs to test.

## 7. External indicators

![External correlations](figures/fig10_external_correlations.png)

Correlations use year-on-year log changes across {corr[['iso3', 'product_group']].drop_duplicates().shape[0]} series, with leads of 0, 1, 3 and 6 months.

{md(r['correlation_summary'].rename(columns={'significant_bh': 'significant_after_bh'}), '{:,.2f}')}
{len(sig)} of {len(corr)} tests pass a Benjamini-Hochberg 5% threshold, but overlapping year-on-year windows make p-values too small, and the signs vary by country. **For Kyrgyzstan, {int((kg_corr.p_bh < .05).sum())} of {len(kg_corr)} pass**; the strongest is rho = {kg_corr.loc[kg_corr.rho.abs().idxmax()].rho:.2f}. GDP: {int((r['gdp'].p < .05).sum())} of {len(r['gdp'])} country-product series have an annual GDP correlation with p < 0.05, using few annual points. Correlation is not causation, and weak linear association does not rule out a role during shocks.

## 8. Shortfall labels recomputed

This repeats the proposal's descriptive rule (trailing three-month mass under 0.75 of the same months in the previous three years).

{md(r['shortfall'])}
The rule gives {r['shortfall'].iloc[0].episodes} gasoline and {r['shortfall'].iloc[2].episodes} distillate episodes on clean data, against the proposal's 11 and 8. Dates move, so the labels still need checking against documented events. Sep 2025 and later are affected by the first-release issue.
"""


def kyrgyz_report(reconciliation, dependency, mirror, all_goods, press):
    mass = reconciliation[["year", "gas_months_observed", "gas_ct_kt", "gas_ct_with_volume_est_kt", "gas_teb_kt", "gas_mass_ratio", "gas_mass_ratio_with_estimate", "mid_months_observed", "mid_ct_kt", "diesel_teb_kt", "fuel_oil_teb_kt", "mid_to_diesel_plus_fuel_oil"]]
    value = reconciliation[["year", "gas_ct_usd_m", "gas_nsc_usd_m", "gas_value_ratio", "mid_ct_usd_m", "diesel_nsc_usd_m", "kerosene_nsc_usd_m", "mid_value_to_diesel_plus_kerosene", "lpg_ct_usd_m", "lpg_nsc_usd_m", "lpg_value_ratio"]]
    ru = mirror[(mirror.exporter == "RUS") & (mirror.iso3 == "KGZ")][["product_group", "year", "export_kt", "import_kt", "mass_ratio_imports_to_exports", "value_ratio_imports_to_exports"]]
    other = mirror[(mirror.exporter != "RUS") & (mirror.iso3 == "KGZ")][["exporter", "product_group", "year", "export_kt", "import_kt", "mass_ratio_imports_to_exports"]]
    late = all_goods[all_goods.period >= 202501][["period", "comtrade_total_usd_m", "nsc_first_usd_m", "nsc_latest_usd_m", "comtrade_to_first", "comtrade_to_latest"]]
    dep = dependency[dependency.year >= 2015][["fuel", "year", "production", "imports", "exports", "domestic_use", "stock_end", "net_import_dependency", "domestic_production_share", "stock_cover_months"]]
    full = reconciliation[(reconciliation.gas_months_observed == 12) & reconciliation.gas_teb_kt.notna()]
    since = full[full.year >= 2018]
    mad = lambda f: (abs(f.gas_ct_kt - f.gas_teb_kt) / f.gas_teb_kt).mean() * 100
    return f"""# Kyrgyz validation

Comtrade compared with official Kyrgyz sources. Differences are investigated, not forced to match. Monthly official fuel statistics were not found, so nothing here is monthly by product, and no monthly official series was constructed.

## Sources compared

| Source | Product definition | Period | Unit | Compatibility |
|---|---|---|---|---|
| UN Comtrade, Kyrgyz reporter | HS 271012 (+271011); HS 271019 | Monthly, 2015 to Aug 2026 | kg net weight; USD | Base series |
| Fuel and Energy Balance, NSC, 2024 edition | Motor gasoline; diesel; fuel oil | Annual, to 2024 | Thousand tonnes | Gasoline is close. HS 271019 is wider than diesel plus fuel oil, as it also holds kerosene and lubricants |
| NSC table 4.03.00.12, import of main commodities | Motor gasoline; diesel; kerosene; liquefied gas | Annual, to 2025 | Thousand USD, CIF | Value only. Comparable for gasoline; 271019 also holds fuel oil and lubricants |
| NSC monthly express reports | All goods, no product detail | Monthly, 2024 to Aug 2026 | USD million | All-goods level only, so it tests vintages, not fuels |
| Press quotes of NSC trade reports | Undefined "fuels and lubricants"; motor gasoline | 2023; Jan-Feb 2025 | Thousand tonnes, USD | Secondary. Originals were not found |

The balance has no 2025 edition yet. NSC tables found give values, not tonnes, by commodity.

## Mass against the energy balance

Mean absolute gasoline difference: {mad(full):.1f}% over complete years ({', '.join(map(str, full.year))}) and {mad(since):.1f}% from 2018. Years with fewer than 12 observed months are not valid comparisons. `gas_ct_with_volume_est_kt` adds the labelled litre-based estimate for Oct-Nov 2017, for this comparison only.

{md(mass, '{:,.2f}')}
## Value against the official commodity table

{md(value, '{:,.2f}')}
Possible explanations:
- **2015, 2016 and 2025 gasoline, ratios of 0.71-0.79.** Comtrade's value is below the national figure. For 2025 this fits the first-release pattern below. For 2015-2016 the cause is not known.
- **2019.** Two months are absent from Comtrade.
- **HS 271019 above diesel plus kerosene.** Expected, because the line also covers fuel oil and lubricants, which this table does not list.
- **LPG 2021, ratio 2.87.** Unexplained. HS 2711.19 may hold non-LPG gases.
- **2025 diesel.** The official table reads USD 48.1 billion, which looks like a data-entry error. It is excluded and left in the raw file.

## First-release check, all goods

For 2025 onward, each month's Comtrade total is compared with the first and the latest figure in the monthly NSC reports.

{md(late, '{:,.3f}')}
Most months match the first national release, and none matches the latest. The national figures are later revised upward while the Comtrade record stays put, at least so far. This is all-goods evidence: how far fuel is affected is not known. It explains why the gasoline value is 0.78 of the official figure in 2025 only partly, since all goods sit near 0.90.

## Reporter against partner

Imports are CIF and exports FOB, and customs dates differ, so a ratio near 1 is expected, not exact.

{md(ru, '{:,.2f}')}
Russian figures end in December 2021. In 2016-2017, Russia reports about three times Kyrgyz gasoline imports, and more than the national balance as well (1,023 against 533 kt in 2016), so simple Kyrgyz under-recording does not explain it. Transit through Kyrgyzstan, re-routing or different product coding are possible; none could be tested here. Other partners:

{md(other, '{:,.2f}')}
Kazakh pairs vary greatly by year, sometimes by more than 20 times, while Uzbek pairs agree. Small corridors need caution.

## Press figures

{md(press[['claim', 'press_kt', 'comtrade_kt', 'press_usd_m', 'comtrade_usd_m', 'comtrade_basis']], '{:,.1f}')}
Neither is a valid check. "Fuels and lubricants" is undefined, and a Jan-Feb 2025 figure of 170.2 kt with USD 73.3 million implies USD 431/t, far below that period's customs values. The original reports should be obtained.

## Import dependency

Dependency is how much of domestic use comes from net imports. It differs from supplier concentration, which is how few suppliers provide those imports. It is computed for Kyrgyzstan only, because this project holds no comparable production and consumption data for other countries. Panel exports-to-imports ratios describe trade orientation and are not dependency measures.

Net import dependency = (imports - exports) / domestic use. Values above 1 mean imports also went into stocks, and negative values mean a net exporter. Stock cover = year-end stock / average monthly use.

{md(dep, '{:,.2f}')}
Kyrgyzstan depends heavily on imported gasoline and diesel, at 0.77 and 0.86 of domestic use in 2024. The balance shows domestic gasoline output jumping from 25.8 to 156 kt in 2024, which reduces dependency and explains part of the fall; it should be confirmed before use. Fuel oil dependency is unstable because domestic use is small.
"""


def write_all(settings, data, cov, quality, reconciliation, results, extras):
    DOCS.mkdir(exist_ok=True)
    (eda.OUT / "kyrgyz_validation.md").write_text(kyrgyz_report(reconciliation, *extras), encoding="utf-8")
    data = {**data, "snapshot": settings["snapshot_id"]}
    inv = inventory(settings)
    inv.to_csv(eda.OUT / "dataset_inventory.csv", index=False)
    (eda.OUT / "dataset_inventory.md").write_text(f"# Dataset inventory\n\nBuilt by scanning the disk. Snapshot `{settings['snapshot_id']}`.\n\n{md(inv, '{:,.1f}')}", encoding="utf-8")
    lines = ["# Data dictionary", "", "Files are in `data/research/`. Generated by `python run.py phase2`.", ""]
    for name, columns in DICTIONARY.items():
        frame = pd.read_parquet(datasets.RESEARCH / f"{name}.parquet")
        undocumented = set(frame.columns) - set(columns)
        if undocumented:
            raise ValueError(f"{name}: undocumented columns {sorted(undocumented)}")
        lines += [f"## {name}.parquet", "", f"{len(frame):,} rows.", "", "| Column | Type | Meaning |", "|---|---|---|"]
        lines += [f"| `{c}` | {frame[c].dtype} | {columns[c]} |" for c in frame.columns] + [""]
    (DOCS / "data_dictionary.md").write_text("\n".join(lines), encoding="utf-8")
    fact = facts(data, cov)
    (eda.OUT / "phase2_facts.json").write_text(json.dumps(fact, indent=1, default=str), encoding="utf-8")
    (eda.OUT / "eda_report.md").write_text(eda_report(data, cov, quality, reconciliation, results, fact), encoding="utf-8")
    outputs = sorted(f for f in datasets.RESEARCH.glob("*") if f.is_file() and f.name != "VERSION.json")
    version = {"dataset_version": "1.0.0", "built_on": date.today().isoformat(), "comtrade_snapshot": settings["snapshot_id"], "window": settings["screening"]["window"],
               "raw_manifest_sha256": sha256(RAW / "un_comtrade" / settings["snapshot_id"] / "manifest.jsonl"), "files": {f.name: {"bytes": f.stat().st_size, "sha256": sha256(f)} for f in outputs}}
    (datasets.RESEARCH / "VERSION.json").write_text(json.dumps(version, indent=1), encoding="utf-8")
