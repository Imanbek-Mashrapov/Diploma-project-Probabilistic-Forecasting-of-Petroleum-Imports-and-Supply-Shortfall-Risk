"""Build the coverage audit and Datasets A, B and C from stored raw responses.

Dataset A: bilateral, country x product x partner x month x flow
Dataset B: monthly, country x product x month x flow
Dataset C: external indicators, country x month and global x month
"""
import json
import logging

import numpy as np
import pandas as pd

from src.preprocessing import cleaning
from src.utils.config import ANALYTICAL, PROCESSED, RAW, REPORTS, load_countries, load_settings, months_between

log = logging.getLogger(__name__)
WORLD = 0
RUSSIA = 643


def _longest_gap(periods, start, end):
    present, gap, best = set(periods), 0, 0
    for p in months_between(start, end):
        gap = 0 if p in present else gap + 1
        best = max(best, gap)
    return best


def load_availability(snapshot):
    """Per reporter-month publication listing; empty months mean nothing was published at all."""
    rows = []
    for path in (RAW / "un_comtrade" / snapshot / "availability").glob("*.json"):
        for r in json.loads(path.read_text(encoding="utf-8")).get("data") or []:
            rows.append({"iso3": path.stem, "period": int(r["period"]), "classification": r["classificationCode"],
                         "first_released": r["firstReleased"], "last_released": r["lastReleased"], "total_records": r["totalRecords"]})
    df = pd.DataFrame(rows)
    df["first_released"] = pd.to_datetime(df.first_released, format="ISO8601")
    return df.sort_values("first_released").drop_duplicates(["iso3", "period"], keep="first")


def country_coverage(settings):
    """Tier each candidate from world-level records actually returned by the API."""
    snapshot, scr = settings["snapshot_id"], settings["screening"]
    start, end = scr["window"]["start"], scr["window"]["end"]
    avail = load_availability(snapshot)
    world = cleaning.resolve_mass(cleaning.add_product_group(cleaning.load_snapshot(snapshot, "world_audit")))
    world.to_parquet(PROCESSED / "world_audit_records.parquet", index=False)
    target = world[world.product_group.isin(["gasoline", "middle_heavy"]) & world.period.between(start, end)]
    monthly = target.groupby(["reporterISO", "product_group", "period"], as_index=False).agg(mass_t=("mass_t", lambda s: s.sum(min_count=1)), value_usd=("value_usd", "sum"))
    rows = []
    for c in load_countries().itertuples():
        a = avail[(avail.iso3 == c.iso3)]
        a_win = a[a.period.between(start, end)]
        rec = {"country": c.name, "iso3": c.iso3, "landlocked_lldc": c.lldc, "group": c.group, "importer_type_provisional": c.importer_type_provisional,
               "any_monthly_first": a.period.min() if len(a) else None, "any_monthly_last": a.period.max() if len(a) else None,
               "published_months_in_window": a_win.period.nunique()}
        best = (0, None)
        for product in ("gasoline", "middle_heavy"):
            s = monthly[(monthly.reporterISO == c.iso3) & (monthly.product_group == product)]
            usable = s[s.mass_t > 0]
            months = usable.period.nunique()
            rec[f"{product}_months"] = months
            rec[f"{product}_first"] = usable.period.min() if months else None
            rec[f"{product}_last"] = usable.period.max() if months else None
            rec[f"{product}_mass_share"] = round(months / s.period.nunique(), 3) if len(s) else 0.0
            rec[f"{product}_median_t"] = round(usable.mass_t.median(), 1) if months else 0.0
            rec[f"{product}_max_gap"] = _longest_gap(usable.period, usable.period.min(), usable.period.max()) if months else None
            passes = months >= scr["tier1"]["min_months"] and rec[f"{product}_mass_share"] >= scr["tier1"]["min_mass_share"] \
                and rec[f"{product}_max_gap"] <= scr["tier1"]["max_gap_months"] and rec[f"{product}_median_t"] >= scr["min_series_tonnes_per_month"]
            mid = months >= scr["tier2"]["min_months"] and rec[f"{product}_mass_share"] >= scr["tier2"]["min_mass_share"] \
                and rec[f"{product}_median_t"] >= scr["min_series_tonnes_per_month"]
            score = 2 if passes else 1 if mid else 0
            if score > best[0]:
                best = (score, product)
        low, high = sorted([rec["gasoline_median_t"], rec["middle_heavy_median_t"]])
        # One line below 5% of the other means fuels are filed under a different HS line (e.g. SACU reporters)
        rec["product_split_suspect"] = bool(high > 0 and low / high < 0.05)
        rec["tier"] = {2: "Tier 1", 1: "Tier 2", 0: "Tier 3"}[best[0]]
        rec["tier_basis_product"] = best[1]
        rec["exclusion_reason"] = _exclusion_reason(rec, scr) if best[0] == 0 else ""
        rows.append(rec)
    out = pd.DataFrame(rows).sort_values(["tier", "iso3"])
    REPORTS.mkdir(exist_ok=True)
    out.to_csv(REPORTS / "country_coverage_report.csv", index=False)
    log.info("tiers: %s", out.tier.value_counts().to_dict())
    return out


def _exclusion_reason(rec, scr):
    if rec["iso3"] == "LIE":
        return "Not a Comtrade reporter; reported within Switzerland"
    if rec["published_months_in_window"] == 0:
        return "No monthly Comtrade data published"
    best = max(rec["gasoline_months"], rec["middle_heavy_months"])
    if best < scr["tier2"]["min_months"]:
        return f"Only {best} usable months in the window"
    return "Series too small or mass too incomplete"


def panel_reporters():
    """Tier 1 first, so a partial run still holds the best countries. Kyrgyzstan comes from the pilot.

    Tier 3 reporters that publish most months also get pulled: World rows can lack
    mass that partner rows carry, so their tier is only final after this stage."""
    cov = pd.read_csv(REPORTS / "country_coverage_report.csv")
    codes = load_countries().set_index("iso3").comtrade_code
    cov["recheck"] = (cov.tier == "Tier 3") & (cov.published_months_in_window >= 120)
    picked = cov[cov.tier.isin(["Tier 1", "Tier 2"]) | cov.recheck].sort_values(["tier", "iso3"])
    return [int(codes[i]) for i in picked.iso3 if i != "KGZ"]


def bilateral_records(snapshot):
    """Partner records, plus World rows from the audit for reporters not pulled at partner level yet.
    Audit rows only ever feed Dataset B, flagged through total_source = world_row."""
    raw = cleaning.load_snapshot(snapshot, "bilateral")
    raw.to_parquet(PROCESSED / "raw_bilateral_records.parquet", index=False)
    audit = cleaning.load_snapshot(snapshot, "world_audit")
    audit = audit.assign(retrieved_at="0000-" + audit.retrieved_at.astype(str))  # sorts first, so partner pulls win
    deduped, dropped = cleaning.drop_exact_duplicates(pd.concat([raw, audit], ignore_index=True))
    df = cleaning.resolve_mass(cleaning.add_product_group(deduped))
    df["mass_t_volume_estimate"], df["empirical_density"] = cleaning.volume_estimate_t(df)
    df["retrieved_at"] = df.retrieved_at.str.replace("0000-", "", regex=False)
    return df, {"raw_rows": len(raw), "audit_rows": len(audit), "overlap_rows_dropped": dropped}


def build_monthly(df, settings, avail):
    """Rebuild totals from partner rows; World rows remain as a separate check column."""
    flagged = df.assign(has_mass=df.mass_t.notna(),
                        value_with_mass=df.value_usd.where(df.mass_t.notna(), 0.0),
                        estimated_t=df.mass_t.where(df.mass_estimated, 0.0),
                        recovered_t=df.mass_t.where(df.mass_source.isin(["qty_kg", "altQty_kg"]), 0.0))
    keys = ["reporterISO", "product_group", "flowCode", "period"]
    partners = flagged[flagged.partnerCode != WORLD].groupby(keys).agg(
        mass_t_partner_sum=("mass_t", lambda s: s.sum(min_count=1)), value_usd_partner_sum=("value_usd", "sum"),
        value_with_mass=("value_with_mass", "sum"), estimated_t=("estimated_t", "sum"), recovered_t=("recovered_t", "sum"),
        volume_estimate_t=("mass_t_volume_estimate", "sum"),
        n_partners=("partnerCode", "nunique"), classification=("classificationCode", "first"))
    world = flagged[flagged.partnerCode == WORLD].groupby(keys).agg(
        mass_t_world=("mass_t", lambda s: s.sum(min_count=1)), value_usd_world=("value_usd", "sum"))
    m = partners.join(world, how="outer").reset_index()
    m["mass_t_reported"] = m.mass_t_partner_sum.where(m.mass_t_partner_sum.notna(), m.mass_t_world)
    m["value_usd"] = m.value_usd_partner_sum.where(m.value_usd_partner_sum.notna(), m.value_usd_world)
    m["total_source"] = np.where(m.mass_t_partner_sum.notna(), "partner_sum", "world_row")
    m["value_share_with_mass"] = (m.value_with_mass / m.value_usd_partner_sum).clip(upper=1)
    m["share_estimated"] = m.estimated_t / m.mass_t_reported
    m["share_mass_recovered_from_qty"] = m.recovered_t / m.mass_t_reported
    m["partner_to_world_mass"] = m.mass_t_partner_sum / m.mass_t_world
    m["partner_to_world_value"] = m.value_usd_partner_sum / m.value_usd_world.where(m.value_usd_world > 0)
    m["unit_value_usd_t"] = m.value_usd / m.mass_t_reported
    bands = settings["quality"]["unit_value_usd_per_t"]
    low = m.product_group.map(lambda g: bands[g][0])
    high = m.product_group.map(lambda g: bands[g][1])
    rel_cfg = settings["quality"]["uv_relative"]
    brent = pd.read_parquet(PROCESSED / "ext_oil_prices.parquet").query("series == 'brent'").set_index("period").value
    m = m.sort_values(["reporterISO", "product_group", "flowCode", "period"])
    m["uv_relative"] = m.groupby(["reporterISO", "product_group", "flowCode"], group_keys=False).apply(
        lambda s: cleaning.relative_unit_value(s.unit_value_usd_t, s.period.map(brent)), include_groups=False)
    # Too cheap means mass is overstated, so the mass goes. Too dear more often means a bad value, so it is flagged only.
    m["flag_uv_low"] = (m.unit_value_usd_t < low) | (m.uv_relative < rel_cfg["low"])
    m["flag_uv_high"] = (m.unit_value_usd_t > high) | (m.uv_relative > rel_cfg["high"])
    m["flag_unit_value"] = m.flag_uv_low | m.flag_uv_high
    # A month is rejected when its leading supplier's weight was thrown out by the density test
    m["share_value_mass_rejected"] = (m.volume_estimate_t.fillna(0) > 0) & (m.value_share_with_mass < rel_cfg["min_value_share_with_mass"])
    m["mass_t"] = m.mass_t_reported.where(~m.flag_uv_low & ~m.share_value_mass_rejected)
    m["mass_t_incl_volume_estimate"] = m.mass_t_reported.fillna(0) + m.volume_estimate_t.fillna(0)
    m.loc[m.volume_estimate_t.fillna(0) == 0, "mass_t_incl_volume_estimate"] = np.nan
    m["flag_mass_outlier"] = m.groupby(["reporterISO", "product_group", "flowCode"]).mass_t.transform(cleaning.robust_z).abs() > settings["quality"]["robust_z_threshold"]
    m = m.rename(columns={"reporterISO": "iso3", "flowCode": "flow"})
    # Absent is not zero: expand each series over its span and label why a month has no row
    frames = []
    for (iso3, group, flow), s in m.groupby(["iso3", "product_group", "flow"]):
        span = months_between(int(s.period.min()), int(s.period.max()))
        grid = pd.DataFrame({"period": span}).merge(s, on="period", how="left")
        grid[["iso3", "product_group", "flow"]] = iso3, group, flow
        frames.append(grid)
    out = pd.concat(frames, ignore_index=True)
    a = avail[["iso3", "period", "first_released"]].assign(published=True)
    out = out.merge(a, on=["iso3", "period"], how="left")
    out["month_status"] = np.select([out.mass_t.notna(), out.mass_t_reported.notna(), out.value_usd.notna(), out.published.eq(True)],
                                    ["usable", "unit_value_rejected", "value_without_mass", "published_product_absent"], "not_published")
    out["month"] = pd.to_datetime(out.period.astype(str), format="%Y%m")
    out["publication_lag_days"] = (out.first_released - (out.month + pd.offsets.MonthEnd(0))).dt.days
    return out.drop(columns=["value_with_mass", "estimated_t", "recovered_t", "published", "share_value_mass_rejected"]).sort_values(["iso3", "product_group", "flow", "period"])


def with_blend_aggregate(df):
    """Add 271019 + 271020 as its own group. Where road diesel contains biodiesel, as across
    the EU, it is filed under 271020, so 271019 alone is not comparable between reporters."""
    parts = df[df.product_group.isin(["middle_heavy", "biodiesel_blend"])].assign(product_group="middle_incl_blends")
    return pd.concat([df, parts], ignore_index=True)


def series_eligibility(monthly, conc, cov, settings):
    """Final, per-series verdict from partner-level data. Tier rules match the screening stage."""
    scr = settings["screening"]
    start, end = scr["window"]["start"], scr["window"]["end"]
    m = monthly[monthly.period.between(start, end)]
    imp = m[m.flow == "M"]
    exp = m[(m.flow == "X") & (m.month_status == "usable")]
    rows = []
    for (iso3, product), s in imp[imp.product_group.isin(["gasoline", "middle_heavy", "middle_incl_blends"])].groupby(["iso3", "product_group"]):
        usable = s[s.month_status == "usable"]
        n = len(usable)
        traded = s[s.value_usd.notna()]
        imported = usable.mass_t.sum()
        exported = exp[(exp.iso3 == iso3) & (exp.product_group == product)].mass_t.sum()
        supplier = conc[(conc.iso3 == iso3) & (conc.product_group == product) & conc.period.between(start, end)] if product != "middle_incl_blends" else conc.iloc[0:0]
        rows.append({"iso3": iso3, "product_group": product, "usable_months": n, "first": usable.period.min() if n else None, "last": usable.period.max() if n else None,
                     "max_gap": _longest_gap(usable.period, usable.period.min(), usable.period.max()) if n else None,
                     "mass_share": n / len(traded) if len(traded) else 0.0, "median_t": usable.mass_t.median() if n else 0.0,
                     "partner_months": int((usable.total_source == "partner_sum").sum()),
                     "supplier_months_cov90": int((supplier.value_share_covered >= 0.9).sum()),
                     "exports_to_imports": exported / imported if imported else np.nan})
    e = pd.DataFrame(rows)
    blend = imp[imp.month_status == "usable"].pivot_table(index="iso3", columns="product_group", values="mass_t", aggfunc="sum")
    e["blend_share"] = e.iso3.map(blend.biodiesel_blend.fillna(0) / blend.middle_incl_blends)
    t1, t2 = scr["tier1"], scr["tier2"]
    floor = scr["min_series_tonnes_per_month"]
    e["series_tier"] = np.select(
        [(e.usable_months >= t1["min_months"]) & (e.mass_share >= t1["min_mass_share"]) & (e.max_gap <= t1["max_gap_months"]) & (e.median_t >= floor),
         (e.usable_months >= t2["min_months"]) & (e.mass_share >= t2["min_mass_share"]) & (e.median_t >= floor)], [1, 2], 3)
    e["split_suspect"] = e.iso3.map(cov.set_index("iso3").product_split_suspect)
    e["importer_type_provisional"] = e.iso3.map(cov.set_index("iso3").importer_type_provisional)
    e["eligible"] = (e.series_tier < 3) & (e.usable_months >= scr["min_panel_months"]) & ~e.split_suspect & (e.partner_months >= scr["min_panel_months"])
    e["import_dependent"] = e.exports_to_imports < scr["max_exports_to_imports"]
    e["comparable_distillate"] = (e.product_group != "middle_heavy") | (e.blend_share < scr["max_blend_share"])
    e["core"] = e.eligible & e.import_dependent & e.comparable_distillate & (e.product_group != "middle_incl_blends")
    return e.sort_values(["iso3", "product_group"])


def final_tiers(cov, eligibility):
    """Tier each country on its better fuel series, now using partner-level mass."""
    fuels = eligibility[eligibility.product_group.isin(["gasoline", "middle_heavy"])]
    best = fuels.groupby("iso3").series_tier.min()
    out = cov.copy()
    out["tier_final"] = out.iso3.map(best).map({1: "Tier 1", 2: "Tier 2", 3: "Tier 3"}).fillna("Tier 3")
    out["tier_changed"] = out.tier != out.tier_final
    return out


def build_bilateral(df):
    b = df[df.partnerCode != WORLD]
    cols = {"reporterISO": "iso3", "reporterCode": "reporter_code", "flowCode": "flow", "period": "period", "cmdCode": "hs_code", "product_group": "product_group",
            "classificationCode": "classification", "partnerCode": "partner_code", "partnerISO": "partner_iso", "partnerDesc": "partner_name",
            "mass_t": "mass_t", "mass_source": "mass_source", "mass_estimated": "mass_estimated", "value_usd": "value_usd",
            "volume_kl": "volume_kl", "implied_density": "implied_density", "mass_t_volume_estimate": "mass_t_volume_estimate", "empirical_density": "empirical_density",
            "cifvalue": "cif_value", "fobvalue": "fob_value", "netWgt": "net_weight_kg_original", "grossWgt": "gross_weight_kg_original", "qty": "qty_original", "qtyUnitAbbr": "qty_unit",
            "altQty": "alt_qty_original", "altQtyUnitAbbr": "alt_qty_unit", "isReported": "is_reported", "isAggregate": "is_aggregate",
            "legacyEstimationFlag": "legacy_estimation_flag", "retrieved_at": "retrieved_at", "source_task": "source_task"}
    return b[list(cols)].rename(columns=cols)


def concentration(bilateral):
    """Supplier structure on imports, by mass. Partners without mass cannot enter the shares,
    so value_share_covered travels with every row and limits how far a month can be trusted."""
    b = bilateral[(bilateral.flow == "M") & bilateral.product_group.isin(["gasoline", "middle_heavy", "lpg"])]
    by_partner = b.groupby(["iso3", "product_group", "period", "partner_code", "partner_iso"], as_index=False).agg(mass_t=("mass_t", "sum"), value_usd=("value_usd", "sum"))
    rows = []
    for (iso3, group, period), g in by_partner.groupby(["iso3", "product_group", "period"]):
        priced = g[g.mass_t > 0].sort_values("mass_t", ascending=False)
        total = priced.mass_t.sum()
        if not total:
            continue
        share = priced.mass_t / total
        rows.append({"iso3": iso3, "product_group": group, "period": period, "total_mass_t": total, "active_suppliers": len(priced),
                     "top1_share": share.iloc[0], "top3_share": share.iloc[:3].sum(), "hhi": (share ** 2).sum(),
                     "top_supplier_iso": priced.partner_iso.iloc[0], "russia_share": share[priced.partner_code == RUSSIA].sum(),
                     "value_share_covered": priced.value_usd.sum() / g.value_usd.sum() if g.value_usd.sum() else np.nan})
    c = pd.DataFrame(rows).sort_values(["iso3", "product_group", "period"])
    prev = by_partner[by_partner.mass_t > 0].groupby(["iso3", "product_group", "period"]).partner_code.agg(set)
    c["new_suppliers"] = [len(prev.loc[(i, g, p)] - prev.loc[(i, g, q)]) if (i, g, q) in prev.index else np.nan
                          for i, g, p, q in zip(c.iso3, c.product_group, c.period, c.groupby(["iso3", "product_group"]).period.shift(1).fillna(-1).astype(int))]
    return c


def external_panel(settings, iso3_list):
    """Dataset C keeps global and country series apart; annual covariates stay in their own table."""
    d = PROCESSED
    oil = pd.read_parquet(d / "ext_oil_prices.parquet")
    gpr = pd.read_parquet(d / "ext_gpr.parquet")
    global_m = pd.concat([oil.assign(series=oil.series + "_usd_bbl"), gpr[gpr.series.isin(["GPR", "GPRT", "GPRA", "GPRC_RUS", "GPRC_UKR", "GPRC_TUR", "GPRC_CHN"])]])
    global_wide = global_m[global_m.period >= 201001].pivot_table(index="period", columns="series", values="value").reset_index()
    fx = pd.read_parquet(d / "ext_fx_bis.parquet")
    iso2 = _iso2_map()
    fx = fx.assign(iso3=fx.iso2.map(iso2)).dropna(subset=["iso3"]).rename(columns={"value": "fx_lcu_per_usd_avg"})[["iso3", "period", "fx_lcu_per_usd_avg"]]
    cpi = pd.read_parquet(d / "ext_cpi_imf.parquet").rename(columns={"value": "cpi_index"})
    own_gpr = gpr[gpr.series.isin([f"GPRC_{i}" for i in iso3_list])].assign(iso3=lambda x: x.series.str[-3:]).rename(columns={"value": "gpr_country"})[["iso3", "period", "gpr_country"]]
    grid = pd.MultiIndex.from_product([iso3_list, months_between(201001, settings["window"]["end"])], names=["iso3", "period"]).to_frame(index=False)
    panel = grid.merge(fx, how="left", on=["iso3", "period"]).merge(cpi, how="left", on=["iso3", "period"]).merge(own_gpr, how="left", on=["iso3", "period"])
    panel = panel.dropna(subset=["fx_lcu_per_usd_avg", "cpi_index", "gpr_country"], how="all")
    annual = pd.read_parquet(d / "ext_world_bank_annual.parquet")
    annual = annual[annual.indicator != "vehicles_per_1000"].pivot_table(index=["iso3", "year"], columns="indicator", values="value").reset_index()
    return global_wide, panel, annual


def _iso2_map():
    refs = json.loads((RAW / "reference" / "Reporters.json").read_text(encoding="utf-8-sig"))["results"]
    return {r.get("reporterCodeIsoAlpha2"): r.get("reporterCodeIsoAlpha3") for r in refs if r.get("reporterCodeIsoAlpha2")}


def build_integrated():
    """Dataset D: eligible import series joined to supplier and external data on one
    calendar month. Values are same-month, so lag them to first_released before modelling."""
    eligibility = pd.read_csv(REPORTS / "series_eligibility.csv")
    keep = eligibility[eligibility.eligible & (eligibility.product_group != "middle_incl_blends")][["iso3", "product_group", "core"]]
    cols = ["iso3", "product_group", "period", "month", "first_released", "publication_lag_days", "month_status", "mass_t", "value_usd",
            "unit_value_usd_t", "total_source", "n_partners", "share_estimated", "flag_uv_low", "flag_uv_high", "flag_mass_outlier"]
    monthly = pd.read_parquet(ANALYTICAL / "dataset_b_monthly.parquet").query("flow == 'M'")[cols]
    conc = pd.read_parquet(ANALYTICAL / "supplier_concentration.parquet").drop(columns=["total_mass_t"])
    global_m = pd.read_parquet(ANALYTICAL / "dataset_c_global_monthly.parquet")
    country_m = pd.read_parquet(ANALYTICAL / "dataset_c_country_monthly.parquet")
    d = monthly.merge(keep, on=["iso3", "product_group"]).merge(conc, how="left", on=["iso3", "product_group", "period"])
    d = d.merge(global_m, how="left", on="period").merge(country_m, how="left", on=["iso3", "period"])
    if d.duplicated(["iso3", "product_group", "period"]).any():
        raise ValueError("Dataset D must hold one row per country, product and month")
    d = d[d.period >= 201501].sort_values(["iso3", "product_group", "period"])
    d.to_parquet(ANALYTICAL / "dataset_d_integrated.parquet", index=False)
    d.to_csv(PROCESSED / "dataset_d_integrated.csv", index=False)
    log.info("dataset_d_integrated: %d rows, %d usable", len(d), (d.month_status == "usable").sum())
    return d


def build_all(settings=None):
    settings = settings or load_settings()
    snapshot = settings["snapshot_id"]
    ANALYTICAL.mkdir(exist_ok=True)
    cov = country_coverage(settings)
    avail = load_availability(snapshot)
    df, stats = bilateral_records(snapshot)
    monthly = build_monthly(with_blend_aggregate(df), settings, avail)
    bilateral = build_bilateral(df)
    conc = concentration(bilateral)
    eligibility = series_eligibility(monthly, conc, cov, settings)
    eligibility.to_csv(REPORTS / "series_eligibility.csv", index=False)
    cov = final_tiers(cov, eligibility)
    cov.to_csv(REPORTS / "country_coverage_report.csv", index=False)
    log.info("final tiers: %s; eligible series: %d; core series: %d", cov.tier_final.value_counts().to_dict(), eligibility.eligible.sum(), eligibility.core.sum())
    global_m, country_m, annual = external_panel(settings, sorted(load_countries().query("iso3 != 'LIE'").iso3))
    outputs = {"dataset_a_bilateral": bilateral, "dataset_b_monthly": monthly, "supplier_concentration": conc,
               "dataset_c_global_monthly": global_m, "dataset_c_country_monthly": country_m, "dataset_c_country_annual": annual}
    for name, frame in outputs.items():
        frame.to_parquet(ANALYTICAL / f"{name}.parquet", index=False)
        frame.to_csv(PROCESSED / f"{name}.csv", index=False)
        log.info("%s: %d rows", name, len(frame))
    build_integrated()
    (PROCESSED / "build_stats.json").write_text(json.dumps({**stats, "reporters_in_bilateral": int(bilateral.iso3.nunique()), "tiers": cov.tier_final.value_counts().to_dict()}, indent=1), encoding="utf-8")
