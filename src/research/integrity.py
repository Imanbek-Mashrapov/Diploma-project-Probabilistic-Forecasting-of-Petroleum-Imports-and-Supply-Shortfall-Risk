"""Systematic integrity audit. Every count below is computed from stored data at run time."""
import numpy as np
import pandas as pd

from src.preprocessing import cleaning
from src.utils.config import PROCESSED, load_countries

TARGETS = ["gasoline", "middle_heavy", "middle_incl_blends"]
HS_EDITION_START = {"H3": 2007, "H4": 2012, "H5": 2017, "H6": 2022}


class Issues:
    def __init__(self):
        self.rows = []

    def add(self, code, issue, dataset, records, impact, treatment, auto, severity):
        self.rows.append({"issue_id": code, "issue": issue, "affected_dataset": dataset, "affected_records": records, "research_impact": impact,
                          "recommended_treatment": treatment, "automatically_correctable": auto, "severity": severity})

    def frame(self):
        return pd.DataFrame(self.rows).sort_values("severity", key=lambda s: s.map({"high": 0, "medium": 1, "low": 2, "info": 3}), kind="stable")


def annual_vs_monthly(snapshot, monthly_raw):
    """Annual Comtrade submissions against the sum of the same reporter's monthly World rows."""
    annual = cleaning.load_snapshot(snapshot, "annual_world")
    annual = annual[annual.cmdCode.isin(["271011", "271012", "271019"])].assign(group=lambda d: np.where(d.cmdCode == "271019", "middle_heavy", "gasoline"))
    a = annual.groupby(["reporterISO", "group", "period"], as_index=False).agg(annual_usd=("primaryValue", "sum"))
    world = monthly_raw[(monthly_raw.partnerCode == 0) & (monthly_raw.flowCode == "M") & monthly_raw.cmdCode.isin(["271011", "271012", "271019"])]
    world = world.assign(group=np.where(world.cmdCode == "271019", "middle_heavy", "gasoline"), year=world.period // 100)
    m = world.groupby(["reporterISO", "group", "year"], as_index=False).agg(monthly_usd=("primaryValue", "sum"), months=("period", "nunique"))
    out = a.merge(m, left_on=["reporterISO", "group", "period"], right_on=["reporterISO", "group", "year"])
    out = out[out.months == 12]
    out["ratio"] = out.monthly_usd / out.annual_usd.where(out.annual_usd > 0)
    return out.drop(columns="period")


def run(data, snapshot, reconciliation, all_goods, mirror):
    all_rows = pd.read_parquet(PROCESSED / "raw_bilateral_records.parquet")
    raw = all_rows.sort_values("retrieved_at").drop_duplicates(cleaning.KEY, keep="last")  # overlapping pulls must not inflate any check
    monthly, bil, conc, eligibility, cov = data["monthly"], data["bilateral"], data["concentration"], data["eligibility"], data["coverage"]
    target = monthly[monthly.product_group.isin(TARGETS)]
    panel = eligibility[eligibility.eligible].iso3.unique()
    p = raw[raw.partnerCode != 0]
    issues = Issues()

    net, qty = pd.to_numeric(raw.netWgt, errors="coerce"), pd.to_numeric(raw.qty, errors="coerce")
    value = pd.to_numeric(raw.primaryValue, errors="coerce")
    is_kg = raw.qtyUnitAbbr.astype(str).str.lower() == "kg"
    both = raw[(net > 0) & (qty > 0) & is_kg]
    differ = both[(both.netWgt - both.qty).abs() / both.netWgt > 0.01]
    non_kg_qty = raw[raw.qtyUnitAbbr.notna() & ~is_kg & ~raw.qtyUnitAbbr.astype(str).isin(["N/A"]) & (qty > 0)]

    # Reporter versus partner, and vintage problems first: they can bias the target itself
    kg_gas = reconciliation[reconciliation.year == 2025].iloc[0]
    late = all_goods[(all_goods.period >= 202501) & all_goods.comtrade_total_usd_m.notna() & (all_goods.vintages >= 2)]
    issues.add("V01", f"Comtrade holds first-release Kyrgyz figures: {int(((late.comtrade_to_first - 1).abs() < .01).sum())} of {len(late)} months from 2025 match the first national release within 1%, none matches the latest; latest runs {(1 / late.comtrade_to_latest - 1).median():.0%} higher at the median",
               "Kyrgyz records 2025-2026", len(late), "Recent months are provisional and may understate imports. The 2025 shortfall may partly be under-recording", "Keep as observed, flag as provisional, take new snapshots, and evaluate on first-release data", "No", "high")
    issues.add("V02", f"2025 Comtrade gasoline value is {kg_gas.gas_value_ratio:.2f} of the official value, against 0.95-1.00 in 2022-2024", "petroleum_imports_monthly", 12,
               "Late-2025 shock depth is uncertain", "Recheck when the 2025 energy balance appears", "No", "high")
    ru_kg = mirror[(mirror.exporter == "RUS") & (mirror.iso3 == "KGZ") & (mirror.product_group == "gasoline")]
    issues.add("V03", f"Russia reports far more gasoline to Kyrgyzstan than Kyrgyzstan reports importing in 2016-2017 (import/export mass {ru_kg[ru_kg.year.isin([2016, 2017])].mass_ratio_imports_to_exports.min():.2f}-{ru_kg[ru_kg.year.isin([2016, 2017])].mass_ratio_imports_to_exports.max():.2f}); ratio is 0.93-1.02 in 2018 and 2021", "mirror_russia vs bilateral", len(ru_kg),
               "Early target level is unreliable", "Report results with and without 2015-2017", "No", "high")
    extreme_mirror = mirror[(mirror.mass_ratio_imports_to_exports > 3) | (mirror.mass_ratio_imports_to_exports < 1 / 3)]
    issues.add("V04", "Annual exporter-importer pairs differing by more than 3 times", "mirror comparison", len(extreme_mirror), "Bilateral flows are less reliable than country totals", "Use supplier shares as indicators, not exact flows", "No", "medium")
    issues.add("V05", "No Russian mirror data exists after December 2021", "mirror_russia", int(data["monthly"].query("iso3 == 'KGZ' and product_group == 'gasoline' and period >= 202201").shape[0]), "Main supplier cannot be cross-checked in the shock period", "Treat as a permanent limit", "No", "medium")
    ag = data["annual_check"]
    kg_ag = ag[(ag.reporterISO == "KGZ") & (ag.group == "gasoline") & (ag.year == 2021)].ratio.iloc[0]
    issues.add("V06", "Sum of monthly World values differs from the annual submission by more than 5%", "annual_world vs monthly", int(((ag.ratio - 1).abs() > .05).sum()), f"Of {len(ag)} reporter-product-years. Annual data seem revised while monthly data are not (Kyrgyz gasoline 2021: monthly {kg_ag:.2f} of annual)", "Note in the coverage matrix; do not rescale monthly data", "No", "medium")

    # Identifiers and classification
    issues.add("I01", "Exact duplicates on the natural key in raw records", "raw_bilateral_records", int(all_rows.duplicated(cleaning.KEY).sum()), f"Would double count; all belong to {', '.join(sorted(all_rows[all_rows.duplicated(cleaning.KEY, keep=False)].reporterISO.unique()))}", "Removed in Phase 1, keeping latest retrieval; they arise from keyless and keyed pulls overlapping", "Yes", "low")
    issues.add("I02", "Duplicates left in the research datasets", "petroleum_imports_bilateral, monthly", int(bil.duplicated(["iso3", "product_group", "partner_code", "period"]).sum() + monthly.duplicated(["iso3", "product_group", "period"]).sum()), "None if zero", "Assertion only", "Yes", "info")
    issues.add("I03", "Comtrade reporter identifiers that disagree with config/countries.csv", "raw_bilateral_records", int((~raw.reporterISO.isin(load_countries().iso3)).sum()), "None if zero", "Assertion only", "Yes", "info")
    issues.add("I04", "Partners without a country identity (Other Asia nes, Other Europe nes, Areas nes)", "petroleum_imports_bilateral", int((bil.partner_type == "unallocated_nes").sum()), f"{bil[bil.partner_type == 'unallocated_nes'].import_mass_t.sum() / bil.import_mass_t.sum():.2%} of mass; hides true suppliers", "Keep as one partner; nes_share is reported per month", "Partly", "low")
    issues.add("I05", "Reporter listed as its own partner", "petroleum_imports_bilateral", int((bil.partner_type == "self").sum()), "Would overstate suppliers", "Excluded from concentration, kept in the dataset", "Yes", "low")
    issues.add("I06", "Bunkers and special categories as partners", "petroleum_imports_bilateral", int((bil.partner_type == "non_supplier").sum()), "Not suppliers", "Excluded from concentration, kept in the dataset", "Yes", "low")
    issues.add("I07", "Periods that disagree with refYear and refMonth", "raw_bilateral_records", int(((raw.refYear * 100 + raw.refMonth) != raw.period).sum()), "None if zero", "Assertion only", "Yes", "info")
    invalid = raw[((raw.cmdCode == "271011") & (raw.classificationCode != "H3")) | ((raw.cmdCode.isin(["271012", "271020"])) & (raw.classificationCode == "H3"))]
    issues.add("I08", "HS codes that do not exist in the stated edition", "raw_bilateral_records", len(invalid), "None if zero", "Assertion only", "Yes", "info")
    lag = raw[raw.period // 100 >= raw.classificationCode.map(HS_EDITION_START) + 6]
    issues.add("I09", "Rows filed under an HS edition at least six years old", "raw_bilateral_records", len(lag), "Lines may be defined differently from newer editions", "Mapping 271011 to 271012 is safe at this level; 271020 cannot be split out under H3", "Partly", "low")
    issues.add("I10", "Breakdown between 271011 (HS2007) and 271012 (HS2012 on)", "gasoline series", int((raw.cmdCode == "271011").sum()), "Biodiesel-containing oils left this line in HS2012, so the merged series is not perfectly continuous; negligible for Kyrgyz data from 2015", "Merge, documented", "Yes", "low")
    blends = eligibility[(eligibility.product_group == "middle_heavy") & (eligibility.blend_share >= .2)]
    issues.add("I11", f"HS 271019 misses blended diesel in {', '.join(sorted(blends.iso3))}", "middle_heavy series", int(blends.usable_months.sum()), "Distillates are not comparable across countries", "Use middle_incl_blends for these reporters or exclude them", "Yes", "high")
    issues.add("I12", f"Fuels seem filed under the wrong HS line in {', '.join(sorted(cov[cov.product_split_suspect].iso3))}", "gasoline and distillate series", int(target[target.classification_flag == "fuel_lines_suspect"].import_mass_t.notna().sum()), "Series would not mean gasoline or distillates", "Exclude from the main experiment; use the 2710 total if needed", "No", "high")
    heading = raw[(raw.partnerCode == 0) & (raw.flowCode == "M") & raw.cmdCode.str.startswith("2710")]
    h = heading[heading.cmdCode == "2710"].groupby(["reporterISO", "period"]).primaryValue.sum()
    l = heading[heading.cmdCode != "2710"].groupby(["reporterISO", "period"]).primaryValue.sum()
    gap = ((l / h.where(h > 0)) - 1).abs() > .01
    issues.add("I13", "Six-digit lines differ from the 2710 heading by more than 1%", "raw World rows", int(gap.sum()), f"Mostly {gap.groupby('reporterISO').sum().idxmax()}; cause not found", "Use lines as reported, keep a flag", "No", "medium")

    # Units and mass
    issues.add("U01", "Rows with no quantity unit (N/A)", "raw_bilateral_records", int((raw.qtyUnitAbbr.astype(str) == "N/A").sum() + raw.qtyUnitAbbr.isna().sum()), "Quantity cannot be used; net weight still can", "Use net weight", "Yes", "low")
    issues.add("U02", "Positive quantities in a unit other than kg", "raw_bilateral_records", len(non_kg_qty), "Must not be mixed with mass", "Never converted into mass", "Yes", "info")
    issues.add("U03", "Net weight and kg quantity differ by more than 1%", "raw_bilateral_records", len(differ), f"Of {len(both)} rows holding both; concentrated in {differ.reporterISO.value_counts().head(3).index.tolist()}", "Net weight wins", "Yes", "medium")
    issues.add("U04", "Net weight null or zero next to positive value", "raw_bilateral_records", int(((net.fillna(0) == 0) & (value > 0)).sum()), "Would read as zero imports", "Treated as missing; kg quantity used if plausible", "Yes", "medium")
    issues.add("U05", "Mass from kg quantity because net weight is empty", "petroleum_imports_bilateral", int(bil.mass_source.str.contains("qty_kg|altQty_kg").sum()), "Less certain source", "Kept, recorded in mass_source", "Yes", "low")
    issues.add("U06", "Physically impossible kg quantity against reported litres", "dataset_a_bilateral", int(bil.mass_source.str.contains("qty_rejected_density").sum()), "Would inject false mass", "Rejected; volume estimate stored apart", "Yes", "medium")
    issues.add("U07", "Rows with no usable mass", "petroleum_imports_bilateral", int(bil.import_mass_t.isna().sum()), "Small; lowers supplier coverage", "Stay missing; value_share_with_mass reports the effect", "No", "low")
    issues.add("U08", "Weight flagged as estimated by the reporter", "raw_bilateral_records", int(raw.isNetWgtEstimated.fillna(False).astype(bool).sum()), "Mass is partly modelled, by Comtrade or the reporter", "Keep, carry share_estimated", "No", "medium")

    # Value and magnitude
    issues.add("M01", "Negative quantities or values", "raw_bilateral_records", int((net < 0).sum() + (value < 0).sum() + (qty < 0).sum()), "None if zero", "Assertion only", "Yes", "info")
    issues.add("M02", "Missing trade value", "raw_bilateral_records", int(value.isna().sum()), "None if zero", "Assertion only", "Yes", "info")
    issues.add("M03", "Explicit zero-trade rows", "raw_bilateral_records", int((value == 0).sum()), "Comtrade does not report zero flows, so a genuine zero cannot be proved", "Absent records stay missing", "No", "medium")
    usable = target[target.iso3.isin(panel) & target.import_mass_t.notna()].sort_values(["iso3", "product_group", "period"])
    change = np.log(usable.import_mass_t).groupby([usable.iso3, usable.product_group]).diff().abs()
    issues.add("M04", "Month-on-month mass change above 5 times", "petroleum_imports_monthly, eligible series", int((change > np.log(5)).sum()), "Mixes real lumpy deliveries and recording errors", "Keep; test robust losses; never smooth the target", "No", "medium")
    issues.add("M05", "Robust outliers in log mass (|z| > 4)", "petroleum_imports_monthly, eligible series", int(usable.flag_mass_outlier.fillna(False).astype(bool).sum()), "May be shocks, the object of study", "Keep and flag", "No", "low")
    issues.add("M06", "Mass removed: unit value far too low", "petroleum_imports_monthly", int((target.data_status == "mass_rejected_by_check").sum()), "Series gets gaps", "Original kept; treated as missing", "Yes", "medium")
    issues.add("M07", "Unit value far too high, mass kept", "petroleum_imports_monthly", int(target.flag_uv_high.fillna(False).astype(bool).sum()), "Value suspect; lagged unit-value features affected", "Flag; exclude flagged months from unit-value features", "Partly", "medium")

    # Coverage and missingness
    status = target[target.iso3.isin(panel)].data_status.value_counts()
    issues.add("C01", "Reporting interruptions inside a reporter's span", "petroleum_imports_monthly, eligible series", int(status.get("reporting_interruption", 0)), "Series have gaps, some of 10-13 months", "Mask; no interpolation of targets", "No", "medium")
    issues.add("C02", "Series ending before the window ends", "petroleum_imports_monthly, eligible series", int((eligibility[eligibility.eligible]["last"] < 202606).sum()), "2026 shock window is thin", "Report the countries covering each test period", "No", "high")
    issues.add("C03", "Published reporter-month with no product record", "petroleum_imports_monthly, eligible series", int(status.get("no_record_in_published_month", 0)), "Could be zero or unreported", "Treat as missing", "No", "low")
    issues.add("C04", "Value reported with no mass", "petroleum_imports_monthly, eligible series", int(status.get("value_reported_mass_missing", 0)), "Mostly Hungary 2015-2016 distillates", "Keep missing; never derive mass from value", "No", "low")
    w = monthly[monthly.total_source == "world_row"]
    issues.add("C05", "Months resting on World rows, without partner detail", "petroleum_imports_monthly", len(w[w.product_group.isin(TARGETS)]), "Partner composition unknown", "Marked in total_source", "No", "low")
    issues.add("C06", "Countries with no monthly reporting at all", "country coverage", int((cov.published_months_in_window == 0).sum()), "Afghanistan, Tajikistan, Turkmenistan and others cannot enter", "List in the coverage matrix", "No", "medium")
    world_zero = target[(target.total_source == "partner_sum") & (target.partner_to_world_mass.isna())]
    issues.add("C07", "World row lacks mass although partners carry it", "petroleum_imports_monthly", len(world_zero), "World rows understate mass", "Totals are rebuilt from partners", "Yes", "medium")
    double = target[target.partner_to_world_value.notna() & ((target.partner_to_world_value - 1).abs() > .05)]
    issues.add("C08", "Partner sum and World value differ by more than 5%", "petroleum_imports_monthly", len(double), "Would signal double counting or lost partners", "Review listed months", "No", "low")
    issues.add("C09", "Mislabelled official figure: 2025 diesel in NSC table 4.03.00.12 reads USD 48.1 billion", "nsc_dynamic_1233", 1, "An official source can also be wrong", "Excluded from ratios, kept in raw", "No", "low")
    return issues.frame()
