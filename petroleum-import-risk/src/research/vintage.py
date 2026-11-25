"""Second Comtrade vintage: raw pull and revision measurement (decision log 2026-11-25, R3).

`pull` downloads a new raw snapshot (settings `vintage`) for the modelling panel's reporters and the four target
HS lines, imports only, into `data/raw/un_comtrade/<vintage.snapshot_id>/`. It never touches `snapshot_id`, the
processed/analytical/research data or any model output: the v1.0 analysis stays frozen on the reference snapshot.

`compare` measures what changed between the two raw snapshots for the target series. Totals are rebuilt from
partner rows with the project's own row-level mass rule (`cleaning.resolve_mass`: net weight, or kg quantity that
passes the density test). The unit-value cleaning of Phase 2 is NOT applied (it needs the full panel and Brent),
so these are "reported" masses before that step. Absent stays absent: nothing is filled.
"""
import logging

import numpy as np
import pandas as pd

from src.ingestion.comtrade_client import ComtradeClient, QuotaExhausted
from src.ingestion import plans
from src.preprocessing import cleaning
from src.utils.config import REPORTS, load_countries, months_between

log = logging.getLogger(__name__)
OUT = REPORTS / "phase3"
GROUPS = {"gasoline": ["gasoline"], "middle_incl_blends": ["middle_heavy", "biodiesel_blend"]}
WORLD = 0
REL_TOL = 1e-9


# ------------------------------------------------------------------ pull
def target_reporters(settings):
    """Comtrade codes of the modelling panel's reporters (Tier 1 + Tier 2 target series)."""
    from src.modeling import panel as pn
    iso = sorted(pn.series_table(settings).iso3.unique())
    codes = load_countries().set_index("iso3").comtrade_code
    return iso, [int(codes[i]) for i in iso]


def tasks(settings):
    v = settings["vintage"]
    _, reporters = target_reporters(settings)
    periods = months_between(v["window"]["start"], v["window"]["end"])
    return plans.bilateral_tasks(reporters, periods, [str(c) for c in v["hs_codes"]], v["flows"], settings["comtrade"]["keyed"]["periods_per_call"])


def pull(settings):
    """Download the new raw snapshot. Resumes from its manifest; a quota stop is logged and the stage is rerun."""
    v = settings["vintage"]
    client = ComtradeClient({**settings, "snapshot_id": v["snapshot_id"]})
    if client.mode != "keyed":
        raise SystemExit("vintage_pull needs UN_COMTRADE_PRIMARY_KEY in .env (keyless preview would need ~10x the calls)")
    todo = tasks(settings)
    log.info("vintage pull: snapshot %s, %d tasks", v["snapshot_id"], len(todo))
    counts = {}
    for i, params in enumerate(todo, 1):
        try:
            status = client.fetch("bilateral", params)
        except QuotaExhausted as e:
            log.error("stopped on quota after %d/%d tasks: %s. Rerun to resume.", i - 1, len(todo), str(e)[:160])
            counts["stopped_on_quota"] = len(todo) - (i - 1)
            break
        counts[status] = counts.get(status, 0) + 1
        if i % 20 == 0 or i == len(todo):
            log.info("vintage %d/%d %s calls=%d", i, len(todo), counts, client.calls)
    log.info("vintage pull finished: %s", counts)
    return counts


# ------------------------------------------------------------------ measurement
def monthly_totals(snapshot, settings, iso_by_code):
    """Partner-sum mass (t) and value (USD) per (series_id, month), imports, target product groups. NaN mass stays NaN."""
    raw = cleaning.load_snapshot(snapshot, "bilateral")
    raw = raw[(raw.flowCode == "M") & (raw.partnerCode != WORLD) & raw.reporterCode.isin(iso_by_code)]
    raw, _ = cleaning.drop_exact_duplicates(raw)
    df = cleaning.resolve_mass(cleaning.add_product_group(raw))
    out = []
    for group, parts in GROUPS.items():
        g = df[df.product_group.isin(parts) & df.cmdCode.isin([str(c) for c in settings["vintage"]["hs_codes"]])]
        if group == "gasoline":
            g = g[g.cmdCode.isin(["271011", "271012"])]
        else:
            g = g[g.cmdCode.isin(["271019", "271020"])]
        agg = g.groupby(["reporterCode", "period"]).agg(mass_t=("mass_t", lambda s: s.sum(min_count=1)), value_usd=("value_usd", lambda s: s.sum(min_count=1)),
                                                        n_rows=("partnerCode", "size")).reset_index()
        out.append(agg.assign(product_group=group))
    t = pd.concat(out, ignore_index=True)
    t["series_id"] = t.reporterCode.map(iso_by_code) + ":" + t.product_group
    t["month"] = pd.to_datetime(t.period.astype(str), format="%Y%m")
    return t.drop(columns=["reporterCode", "period", "product_group"])


def compare(old, new, series_ids, rel_tol=REL_TOL):
    """Month-level comparison of two vintages. A month counts as present when its mass is not NaN."""
    o = old[old.series_id.isin(series_ids)].set_index(["series_id", "month"]).add_suffix("_old")
    n = new[new.series_id.isin(series_ids)].set_index(["series_id", "month"]).add_suffix("_new")
    c = o.join(n, how="outer").reset_index()
    has_o, has_n = c.mass_t_old.notna(), c.mass_t_new.notna()
    c["status"] = np.select([has_o & has_n, ~has_o & has_n, has_o & ~has_n], ["common", "added", "dropped"], "absent_both")
    c = c[c.status != "absent_both"].copy()
    both = c.status == "common"
    c["rel_mass_rev"] = np.where(both, (c.mass_t_new - c.mass_t_old) / c.mass_t_old.where(c.mass_t_old > 0), np.nan)
    vboth = both & c.value_usd_old.notna() & c.value_usd_new.notna()
    c["rel_value_rev"] = np.where(vboth, (c.value_usd_new - c.value_usd_old) / c.value_usd_old.where(c.value_usd_old > 0), np.nan)
    c["mass_changed"] = both & (c.rel_mass_rev.abs() > rel_tol)
    c["value_changed"] = vboth & (c.rel_value_rev.abs() > rel_tol)
    return c.sort_values(["series_id", "month"]).reset_index(drop=True)


def _q(x, q):
    x = pd.Series(x).dropna()
    return float(np.quantile(x, q)) if len(x) else np.nan


def summarise(c, label):
    """One summary row: counts and the size of relative revisions (absolute), over all common months and over changed ones."""
    common = c[c.status == "common"]
    ch_m, ch_v = c[c.mass_changed], c[c.value_changed]
    return {"scope": label, "series": int(c.series_id.nunique()), "months_old": int((c.status.isin(["common", "dropped"])).sum()),
            "months_new": int((c.status.isin(["common", "added"])).sum()), "months_added": int((c.status == "added").sum()),
            "months_dropped": int((c.status == "dropped").sum()), "months_common": int(len(common)),
            "mass_changed": int(c.mass_changed.sum()), "value_changed": int(c.value_changed.sum()),
            "share_mass_changed": float(c.mass_changed.sum() / len(common)) if len(common) else np.nan,
            "mass_abs_rev_median_changed": _q(ch_m.rel_mass_rev.abs(), 0.5), "mass_abs_rev_p90_changed": _q(ch_m.rel_mass_rev.abs(), 0.9),
            "mass_abs_rev_p90_all_common": _q(common.rel_mass_rev.abs(), 0.9),
            "mass_signed_rev_median_changed": _q(ch_m.rel_mass_rev, 0.5),
            "value_abs_rev_median_changed": _q(ch_v.rel_value_rev.abs(), 0.5), "value_abs_rev_p90_changed": _q(ch_v.rel_value_rev.abs(), 0.9),
            "value_abs_rev_p90_all_common": _q(common.rel_value_rev.abs(), 0.9)}


def summary_table(c):
    rows = [summarise(c, "all target series"), summarise(c[c.series_id.str.startswith("KGZ:")], "Kyrgyzstan (both products)"),
            summarise(c[~c.series_id.str.startswith("KGZ:")], "other reporters")]
    for sid, g in c.groupby("series_id"):
        rows.append(summarise(g, sid))
    return pd.DataFrame(rows)


def _pct(x):
    return "n/a" if x is None or pd.isna(x) else f"{100 * x:.2f}%"


def write_report(c, summ, settings, meta):
    v = settings["vintage"]
    head = summ.iloc[:3]
    rows = "".join(f"| {r.scope} | {r.series} | {r.months_common} | {r.months_added} | {r.months_dropped} | {r.mass_changed} ({_pct(r.share_mass_changed)}) | "
                   f"{r.value_changed} | {_pct(r.mass_abs_rev_median_changed)} | {_pct(r.mass_abs_rev_p90_changed)} | {_pct(r.mass_abs_rev_p90_all_common)} | "
                   f"{_pct(r.value_abs_rev_median_changed)} | {_pct(r.value_abs_rev_p90_changed)} |\n" for r in head.itertuples())
    kgz = c[c.series_id.str.startswith("KGZ:")]
    late = kgz[(kgz.month >= "2025-01-01") & (kgz.status == "common")]
    kg_rows = "".join(f"| {sid} | {int((g.status == 'added').sum())} | {int(g.mass_changed.sum())} | {_pct(g.rel_mass_rev.abs().median())} | {_pct(g.rel_mass_rev.max())} | {_pct(g.rel_mass_rev.min())} |\n"
                      for sid, g in late.groupby("series_id"))
    added = c[c.status == "added"]
    last_old = c[c.status.isin(["common", "dropped"])].month.max()
    last_new = c[c.status.isin(["common", "added"])].month.max()
    text = f"""# Vintage comparison: {v['reference_snapshot']} vs {v['snapshot_id']}

Generated by `python run.py vintage` (exploratory, R3; `docs/decision_log.md` 2026-11-25). Rules version unchanged.
Both vintages are raw Comtrade pulls for the modelling panel's {meta['n_series']} target series ({meta['n_reporters']} reporters), imports only,
HS 271011 + 271012 (gasoline proxy) and 271019 + 271020 (distillates). The v1.0 analysis stays on {v['reference_snapshot']}; nothing
was rebuilt, retrained or re-evaluated on the new data.

**What is compared.** Partner-row totals of mass (t) and value (USD), rebuilt from the raw responses with the project's row-level
mass rule (net weight, or kg quantity passing the density test; no unit-value cleaning, which needs the full panel). These are
"reported" masses before Phase 2's unit-value step, so absolute levels differ from `data/research/` but a revision of the same
month between vintages is measured on the same basis. A month is *present* when its mass is not missing. Absent months are never
filled. Window {v['window']['start']}-{v['window']['end']}; the vintages differ in the time the data had to be revised and in
newly released months (latest month: {last_old.strftime('%Y-%m')} old, {last_new.strftime('%Y-%m')} new).
A month "changed" if its relative revision exceeds {REL_TOL:g}. Revision size = |new - old| / old.

| Scope | Series | Months in both | Added | Dropped | Mass changed | Value changed | Mass |rev| median (changed) | Mass |rev| P90 (changed) | Mass |rev| P90 (all common) | Value |rev| median (changed) | Value |rev| P90 (changed) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
{rows}
Kyrgyzstan, months from 2025-01 present in both vintages (signed revision = new vs old; positive = revised up):

| Series | Months added | Mass changed | Median abs rev | Max up | Max down |
|---|---|---|---|---|---|
{kg_rows}
Per-series rows: `tables/vintage_comparison_summary.csv`; every month: `tables/vintage_comparison_months.csv`.
Months added: {len(added)} (all series); of these {int(added.mass_t_new.notna().sum())} carry mass.

**Reading.** The revision statistics describe how much a first-seen value moved between two pulls {(pd.Timestamp(v['snapshot_id']) - pd.Timestamp(v['reference_snapshot'])).days}
days apart, so they are a lower bound on lifetime revisions of first-release data (the project's national-statistics check found later
Kyrgyz figures about 9% above Comtrade first releases). One extra vintage cannot identify first-release values: v1.0 and every model in it
use the {v['reference_snapshot']} values, with release dates from the Comtrade availability record, which is a pseudo-real-time design.
"""
    (OUT / "vintage_comparison.md").write_text(text, encoding="utf-8")


def run(settings):
    """Compare the two raw snapshots. Writes only reports/phase3/vintage_comparison.* and tables/vintage_comparison_*.csv."""
    v = settings["vintage"]
    iso, codes = target_reporters(settings)
    iso_by_code = dict(zip(codes, iso))
    from src.modeling import panel as pn
    series_ids = set(pn.series_table(settings).series_id)
    old = monthly_totals(v["reference_snapshot"], settings, iso_by_code)
    new = monthly_totals(v["snapshot_id"], settings, iso_by_code)
    start = pd.Timestamp(f"{v['window']['start'] // 100}-{v['window']['start'] % 100:02d}-01")
    old, new = old[old.month >= start], new[new.month >= start]
    c = compare(old, new, series_ids)
    summ = summary_table(c)
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    c.to_csv(OUT / "tables" / "vintage_comparison_months.csv", index=False)
    summ.to_csv(OUT / "tables" / "vintage_comparison_summary.csv", index=False)
    write_report(c, summ, settings, {"n_series": c.series_id.nunique(), "n_reporters": len(iso)})
    log.info("vintage comparison written to %s", OUT)
    return summ
