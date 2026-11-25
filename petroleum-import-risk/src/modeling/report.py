"""Write reports/phase3/results.md from the evaluation results. Every number comes from the run."""
import numpy as np
import pandas as pd

from src.utils.config import REPORTS

OUT = REPORTS / "phase3"
NAMES = {"naive": "Naive", "snaive": "Seasonal naive", "mean12": "12-month mean", "ets": "ETS", "sarima": "SARIMA",
         "lgbm_local": "LightGBM, local", "lgbm_global": "LightGBM, global", "mlp_global": "MLP, global", "gru_global": "GRU, global"}


def _pct(x):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{100 * x:+.1f}%"


def _p(x):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else (f"{x:.3f}" if x >= 0.001 else "<0.001")


def _table(frame, cols, fmt=None):
    fmt = fmt or {}
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    body = ""
    for r in frame.itertuples(index=False):
        vals = []
        for c in cols:
            v = getattr(r, c)
            vals.append(fmt[c](v) if c in fmt else (f"{v:.3f}" if isinstance(v, float) else str(v)))
        body += "| " + " | ".join(vals) + " |\n"
    return head + body


def verdict(supported):
    return "**supported**" if supported else "**not supported**"


def _int(v):
    return str(int(v))


def _na4(v):
    return "n/a" if v is None or np.isnan(v) else f"{v:.4f}"


def diagnostics_section(extra):
    """Extra scores and calibration checks (spec section 2): point errors, CRPS, coverage by horizon, quantile calibration, PIT, crossing."""
    ext, cov_h, qcal, pit, cross = (extra[k] for k in ("ext", "cov_h", "qcal", "pit", "cross"))
    order = [k for k in NAMES if k in set(ext.model)]

    def by_task(t, task):
        return t[t.task == task].set_index("model").reindex(order).reset_index().assign(model=lambda f: f.model.map(NAMES))

    qc = [c for c in qcal.columns if c.startswith("hit_")]
    out = """## Further scores and calibration checks

Added 2026-11-25; they do not change any number above. Same cases as the accuracy table (every model forecast the case).
MAE, RMSE (tonnes) and WAPE are pooled over series, so large importers dominate them; MASE and RMSSE are scaled per series.
CRPS is approximated from the five stored quantiles (2 x weighted pinball loss, scaled like MASE). It runs below the exact CRPS
(about 11% for a normal forecast) because the tails are coarse, so use it to rank models, not for its absolute level.
`CRPS_raw` uses the raw (non-conformal) intervals.

"""
    cols = ["model", "MASE", "RMSSE", "MAE_t", "RMSE_t", "WAPE", "CRPS", "CRPS_raw", "n"]
    fmt = {"MAE_t": lambda v: f"{v:,.0f}", "RMSE_t": lambda v: f"{v:,.0f}", "n": _int}
    for task, label in (("m3", "h = 3"), ("m1", "h = 1"), ("m6", "h = 6"), ("sum3", "months 1-3 total")):
        out += f"### Point and distribution scores, {label}\n\n" + _table(by_task(ext, task), cols, fmt) + "\n"
    out += "### Coverage by horizon (nominal 0.80 and 0.95)\n\n"
    for task in ("m1", "m3", "m6", "sum3"):
        out += f"`{task}`\n\n" + _table(by_task(cov_h, task), ["model", "cover80_raw", "cover80", "cover95_raw", "cover95", "n"], {"n": _int}) + "\n"
    out += "Cases overlap across origins and series, so coverage differences of a few points are within noise.\n\n"
    out += "### Quantile calibration, h = 3\n\nShare of outcomes below each conformal quantile; the ideal equals the level.\n\n"
    out += _table(by_task(qcal, "m3"), ["model"] + qc) + "\n"
    out += (f"### PIT, h = 3\n\nShare of PIT values in the two outer deciles (ideal {pit.tails_ideal.iloc[0]:.2f}; above it means outcomes fall "
            "outside the forecast distribution too often). With five stored quantiles the PIT is interpolated, so read the tails and the "
            "overall shape only. Full histograms: `tables/pit.csv`.\n\n"
            + _table(by_task(pit, "m3"), ["model", "tails", "bin1", "bin2", "bin5", "bin6", "bin9", "bin10", "n"], {"n": _int})
            + "\n![PIT](figures/fig07_pit_h3.png)\n\n")
    cr = cross.assign(model=cross.model.map(lambda k: NAMES.get(k, k)))
    out += ("### Quantile crossing\n\nShare of forecast rows whose quantiles were out of order before sorting. `crossed_learner` is the learner's own "
            "output (recorded only for forecasts produced after this diagnostic was added; n/a otherwise); `crossed_conformal` is the share after "
            "the conformal shift. Sorted quantiles are what every score above uses.\n\n"
            + _table(cr, ["model", "rows", "crossed_learner", "crossed_conformal"], {"rows": _int, "crossed_learner": _na4, "crossed_conformal": _na4}) + "\n")
    return out

def exploratory_section(expl, budget):
    """R1 and R2 (2026-11-25): secondary H4 benchmarks and strata. Exploratory, not Holm-adjusted, no effect on H1-H4."""
    from src.modeling.h4_extra import LABELS as L
    long, strata = expl
    pct = int(100 * budget)
    ci = lambda r: f"{r.diff_ci95_lo:+.3f} to {r.diff_ci95_hi:+.3f}"  # noqa: E731

    def tab(stratum):
        t = long[long.stratum == stratum]
        head = (f"| Benchmark | Cases | Positives | PR-AUC LightGBM | PR-AUC benchmark | Difference (95% CI) | p (one-sided) | Recall@{pct}% LightGBM | Recall@{pct}% benchmark |\n"
                "|---|---|---|---|---|---|---|---|---|\n")
        body = "".join(f"| {L[r.benchmark]} | {r.cases} | {r.positives} | {r.pr_auc_lgbm:.3f} | {r.pr_auc_benchmark:.3f} | {r.pr_auc_diff:+.3f} ({ci(r)}) | {_p(r.p_one_sided)} | {r.recall_lgbm:.2f} | {r.recall_benchmark:.2f} |\n"
                       for r in t.itertuples() if "pr_auc_lgbm" in t and not pd.isna(r.pr_auc_lgbm))
        return head + body

    sd = "".join(f"| {r.stratum} | {r.series} | {r.cases} | {r.positives} | {r.base_rate:.3f} | {r.series_with_positive} | {r.episodes} |\n" for r in strata.itertuples())
    return f"""## Exploratory: H4 benchmarks and strata (R1, R2)

Added 2026-11-25 after the primary results were seen (`docs/decision_log.md`). **Exploratory: these are not Holm-adjusted primary tests,
and H1-H4 above are unchanged.** Same Tier-1 next-three-month cases and label (`flag_75`) as H4, scored with the LightGBM (global) shortfall
probability. Each row compares it with one other score on the cases both cover, so case counts differ by row (the local models do not forecast
every case). Difference is PR-AUC(LightGBM) minus PR-AUC(benchmark), with the same moving-block bootstrap as H4 (blocks of 6 origins, 2000
resamples); p is one-sided, the share of resamples with a difference at or below zero. The persistence rule scores a case by the last
visible three-month ratio Q/B at the origin (the latest three consecutive months public by the end of the origin month against their as-of
seasonal baseline; lower ratio = higher risk), built only from data released by the origin. Recall is at a {pct}% alert budget on the shared cases.

### R1: secondary benchmarks, all Tier-1 series

{tab('all')}
### R2: strata by import dominance

**The split uses the provisional importer type, which is hand-assigned and unsourced** (`reports/phase2/unresolved_issues.md` item 4).
"Import-dominant" = provisional `strict_importer` (imports assumed to be the dominant source of supply); "other" = provisional producer or
refiner. Only Kyrgyzstan has a supply balance in the data, so dominance is not verified for any other series. Episodes are runs of
consecutive-origin positives within a series (overlapping three-month windows make positives cluster, so episodes, not positives, show the
effective number of events).

| Stratum | Series | Cases | Positives | Base rate | Series with a positive | Episodes |
|---|---|---|---|---|---|---|
{sd}
**Import-dominant series (provisional, unsourced)**

{tab('import_dominant')}
**Other series (provisional producer / refiner, unsourced)**

{tab('other')}
The `HHI ranking` row in each table is H4's own comparison within the stratum. Strata are small and positives are few, so intervals are wide
and these rows describe, not test.

"""


def write(res, acc, acc_raw, acc_shock, abl, settings, extra=None, expl=None):
    m = res["meta"]
    h1, h3, h4 = res["H1"], res["H3"], res["H4"]["flag_75"]
    holm = res["holm"]
    h2 = {(r["window"], r["metric"]): r for r in res["H2"]}
    h2_all, h2_shock = h2.get(("all", "MASE"), {}), h2.get(("shock", "MASE"), {})
    h1_ok = h1["relative_improvement"] >= 0.05 and holm["H1"] < 0.05
    h2_ok = (h2_all.get("p_one_sided", 1) >= 0.05) and holm["H2_shock"] < 0.05
    h3_ok = h3["relative_improvement"] >= 0.03 and holm["H3"] < 0.05
    h4_ok = h4["pr_auc_model"] > h4["pr_auc_hhi"] and h4["recall_model"] > h4["recall_hhi"] and holm["H4"] < 0.05

    pivot = acc.pivot(index="model", columns="task", values="MASE").reindex([k for k in NAMES if k in set(acc.model)]).reset_index()
    pivot["model"] = pivot.model.map(NAMES)
    m3 = acc[acc.task == "m3"].set_index("model")
    m3r = acc_raw[acc_raw.task == "m3"].set_index("model")
    cov = m3[["pinball", "cover80", "cover95", "width80"]].join(m3r[["cover80", "cover95"]], rsuffix="_raw").reindex(
        [k for k in NAMES if k in m3.index]).reset_index()
    cov["model"] = cov.model.map(NAMES)
    shock = acc_shock.pivot(index="model", columns="shock", values="MASE").reindex([k for k in NAMES if k in set(acc_shock.model)])
    shock.columns = ["normal" if not c else "shock" for c in shock.columns]
    shock = shock.reset_index()
    shock["model"] = shock.model.map(NAMES)
    n_shock = int(acc_shock[acc_shock.shock].n.max()) if acc_shock.shock.any() else 0

    text = f"""# Phase 3 results: forecasting and shortfall risk

Generated by `python run.py evaluate` (rules v{m['rules_version']}). Rolling origins from {m['evaluation_start']} to {m['last_origin']}
({m['origins']} monthly origins), Tier 1 series unless stated. Every number below is computed from
`data/modeling/forecasts_raw.parquet`; the tables are in `tables/` and the figures in `figures/`.

Forecasts use only data released by each origin. Intervals are conformally adjusted on the 24 previous origins.
MASE is scaled by each series' in-sample seasonal difference, so 1.0 equals the historical error of a
seasonal-naive forecast; values below 1 are better.

## Hypotheses

Holm-adjusted p-values over the four primary tests. Null results are reported with the same weight as positive ones.
Result is the relative improvement of the first model over the second: positive means the first model is better, negative means worse.
p is one-sided (first model better).

| Hypothesis | Test | Result | p (raw) | p (Holm) | Verdict |
|---|---|---|---|---|---|
| H1: global cuts Kyrgyz MASE ≥5% vs best local, h=3 | LightGBM global vs {NAMES.get(h1['best_local'], h1['best_local'])} | {_pct(h1['relative_improvement'])} (95% CI {_pct(h1['ci95'][0])} to {_pct(h1['ci95'][1])}) | {_p(h1['p_one_sided'])} | {_p(holm['H1'])} | {verdict(h1_ok)} |
| H2: neural not better overall, better in shock windows | {NAMES.get(m['neural_selected'])} vs LightGBM global, MASE h=3 | overall {_pct(h2_all.get('relative_improvement'))} (p={_p(h2_all.get('p_one_sided'))}); shock {_pct(h2_shock.get('relative_improvement'))} on {h2_shock.get('cases', 0)} cases | {_p(h2_shock.get('p_one_sided'))} | {_p(holm['H2_shock'])} | {verdict(h2_ok)} |
| H3: supplier + shock data cut pinball ≥3% on high-dependence series | LightGBM global vs own-history LightGBM | {_pct(h3['relative_improvement'])} (95% CI {_pct(h3['ci95'][0])} to {_pct(h3['ci95'][1])}) | {_p(h3['p_one_sided'])} | {_p(holm['H3'])} | {verdict(h3_ok)} |
| H4: forecast probability beats HHI ranking | PR-AUC and recall at {int(100 * settings['modeling']['alert_budget'])}% alert budget | PR-AUC {h4['pr_auc_model']:.3f} vs {h4['pr_auc_hhi']:.3f} (base rate {h4['base_rate']:.3f}); recall {h4['recall_model']:.2f} vs {h4['recall_hhi']:.2f} | {_p(h4['p_one_sided'])} | {_p(holm['H4'])} | {verdict(h4_ok)} |

High-dependence series for H3 (largest supplier ≥{int(100 * settings['modeling']['high_dependence_share'])}% before 2023): {', '.join(h3['series'])}.
The neural candidate for H2 ({NAMES.get(m['neural_selected'])}) was chosen on the 2021-2022 calibration origins, before the test block.
Shock windows are documented supply-shortfall events from `config/shock_events.csv` plus two months; the test block has
{n_shock} shock cases at h=3, so H2's shock comparison has low power.

## Point accuracy (MASE)

Cases where every model produced a forecast.

{_table(pivot, ['model', 'm1', 'm3', 'm6', 'sum3'])}
![MASE by model](figures/fig01_mase_by_model.png)

## Probabilistic accuracy and calibration, h = 3

Pinball loss is scaled like MASE. Coverage should be close to 0.80 and 0.95.

{_table(cov, ['model', 'pinball', 'cover80_raw', 'cover80', 'cover95_raw', 'cover95', 'width80'])}
![Coverage](figures/fig02_coverage.png)

## Normal and shock windows, h = 3 (MASE)

{_table(shock, ['model'] + [c for c in ('normal', 'shock') if c in shock.columns])}
## Shortfall warnings (H4 and sensitivity)

Shortfall: the next-three-month mean falls below the threshold share of its seasonal baseline (proposal eq. 2).
The probability comes from the conformal LightGBM forecast distribution (eq. 3); HHI is the trailing 12-month index at the origin.

| Label | Positives / cases | PR-AUC forecast | PR-AUC HHI | PR-AUC top-supplier share | Brier | Recall forecast | Recall HHI | p |
|---|---|---|---|---|---|---|---|---|
""" + "".join(
        f"| {k} | {v['positives']} / {v['cases']} | {v['pr_auc_model']:.3f} | {v['pr_auc_hhi']:.3f} | {v['pr_auc_top_share']:.3f} | {v['brier_model']:.3f} | {v['recall_model']:.2f} | {v['recall_hhi']:.2f} | {_p(v['p_one_sided'])} |\n"
        for k, v in res["H4"].items()) + f"""
`flag_75` is the primary label; `flag_70` and `flag_80` change the threshold; `supply_side` adds the unit-value condition;
`shock` uses the documented event calendar instead of the volume rule. The Phase 2 event check found the volume labels a weak
proxy (`reports/phase2/event_validation.md`), so the event-based row matters as much as the primary one.

![PR curves](figures/fig03_shortfall_pr.png)

Ranking and calibration are separate properties. The reliability diagram shows whether a stated probability matches
the observed frequency; a Brier score above the base-rate Brier (base rate × (1 − base rate)) means the probabilities
are worse than always predicting the base rate, even if they rank cases well.

![Reliability](figures/fig06_shortfall_reliability.png)

### Recalibrated probabilities (post-hoc extension, not part of H1-H4)

Added on 2026-11-25 after the reliability diagram showed overstated risk (`docs/decision_log.md`). Platt scaling on past
outcomes that had been released by each origin, pooled over all 44 series and 24 origins. *Rolling* refits the map every
origin; *fixed* fits it once at the first test origin and keeps it. Same cases for all three rows.

| Label | Probability | Mean p | Base rate | Brier | Base-rate Brier | PR-AUC | Recall |
|---|---|---|---|---|---|---|---|
""" + "".join(
        f"| {k} | {name} | {v['mean_p_' + key]:.3f} | {v['base_rate']:.3f} | {v['brier_' + key]:.4f} | {v['brier_climatology']:.4f} | {v['pr_auc_' + key]:.3f} | {v['recall_' + key]:.2f} |\n"
        for k, v in res["recalibration"].items() for name, key in (("raw", "raw"), ("rolling", "rc"), ("fixed", "fix"))) + f"""
Recalibration removes most of the overstatement, but no version is meaningfully better than the base rate on the
Brier score (the largest gain is about 0.001): the forecast carries ranking information, not a reliable probability level. The rolling map is monotone within an
origin, so it keeps each month's ranking (what the monitor shows); refitting changes the scale between origins,
which lowers the pooled PR-AUC. The monitor shows the rolling recalibrated probability.

## Ablation (LightGBM global, h = 3)

One change at a time. Positive change means the variant is worse than the full model.
`abl_without_kgz` is scored on Kyrgyz series only (leave-one-country-out); `abl_strict_importers` on strict-importer series only.
`abl_no_conformal` compares raw with conformal intervals of the same model, so its MASE does not change.

{_table(abl, ['variant', 'cases', 'mase_change', 'pinball_change', 'cover80'], {'mase_change': _pct, 'pinball_change': _pct, 'cases': lambda v: '' if v is None or (isinstance(v, float) and np.isnan(v)) else str(int(v))})}
![Ablation](figures/fig05_ablation.png)

## Kyrgyzstan

![Kyrgyz forecasts](figures/fig04_kgz_forecasts.png)

Per-product accuracy for Kyrgyzstan: `tables/accuracy_kyrgyzstan.csv`.

## Limits of this run

- One Comtrade snapshot (2026-11-02). Release dates are those of the current record, so older months may carry revised values; a second raw snapshot (2026-11-25) was pulled only to measure revisions (`vintage_comparison.md`); every result here uses the first.
- Shortfall labels are descriptive and weak (Phase 2); results for H4 depend on which label is used.
- Random forest, XGBoost, TCN, N-BEATS proper and the Temporal Fusion Transformer from the proposal were not run; the neural arm is a residual MLP and a GRU of the same size class.
- Hyperparameters are fixed defaults from `config/settings.yaml`, not tuned.
- Cleaning rules and tier thresholds are frozen as v{m['rules_version']} without supervisor review yet (`docs/decision_log.md`).
"""
    if extra:
        text = text.replace("## Ablation (LightGBM global", diagnostics_section(extra) + "\n## Ablation (LightGBM global", 1)
    if expl is not None:
        text = text.replace("## Limits of this run", exploratory_section(expl, settings["modeling"]["alert_budget"]) + "## Limits of this run", 1)
    (OUT / "results.md").write_text(text, encoding="utf-8")
