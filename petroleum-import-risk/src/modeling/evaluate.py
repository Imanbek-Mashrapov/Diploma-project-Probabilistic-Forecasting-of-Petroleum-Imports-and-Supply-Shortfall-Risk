"""Phase 3 evaluation: accuracy tables, hypothesis tests H1-H4, ablations and the results report.

Reads data/modeling/forecasts_raw.parquet and features.parquet; writes
data/modeling/forecasts.parquet (conformal quantiles in tonnes + shortfall probabilities, the
monitor's input) and reports/phase3/ (results.md, tables/, figures/).
"""
import json
import logging

import matplotlib
import numpy as np
import pandas as pd

from src.modeling import calibrate, features as ft, metrics as mt, panel as pn
from src.research import events as ev
from src.utils.config import REPORTS

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

log = logging.getLogger(__name__)
OUT = REPORTS / "phase3"
TABLES = OUT / "tables"
FIGS = OUT / "figures"
QC = calibrate.QCOLS
LOCAL = ["naive", "snaive", "mean12", "ets", "sarima", "lgbm_local"]
GLOBAL = ["lgbm_global", "mlp_global", "gru_global"]
MAIN = LOCAL + GLOBAL
NEURAL = ["mlp_global", "gru_global"]
LABELS = {"naive": "Naive", "snaive": "Seasonal naive", "mean12": "12-month mean", "ets": "ETS", "sarima": "SARIMA",
          "lgbm_local": "LightGBM (local)", "lgbm_global": "LightGBM (global)", "mlp_global": "MLP (global)", "gru_global": "GRU (global)"}


# ------------------------------------------------------------------ scoring
def shock_cells(settings, monthly):
    """(series_id, month) pairs inside a documented supply-shortfall window (end + response lag)."""
    events = pn.event_table(settings, monthly)
    events = events[events.role == "supply_shortfall"]
    last = monthly.month.max()
    cells = set()
    for e in events.itertuples():
        start, end = ev.event_window(e, last)
        for mth in pd.date_range(start, end, freq="MS"):
            cells.add((f"{e.iso3}:{e.product_group}", mth))
    return cells


def realised_labels(monthly, series):
    """Shortfall labels from the final data (descriptive rule in src/research/events.py)."""
    rows = []
    for s in series.itertuples():
        lab = ev.label_series(monthly, s.iso3, s.product_group)
        for t in (0.70, 0.80):
            lab[f"flag_{int(t * 100)}"] = (lab.ratio < t) & lab.ratio.notna()
        lab = lab.reset_index().rename(columns={"index": "month"})
        lab["series_id"] = s.series_id
        rows.append(lab)
    out = pd.concat(rows, ignore_index=True)
    return out.rename(columns={"month": "target_month", "flag": "flag_75"})


def score(settings, forecasts, feats, cells):
    keep = ["origin", "series_id", "task", "iso3", "product_group", "evaluation", "level", "target", "actual_t", "scale_month",
            "scale_sum3", "target_month", "hhi_12m", "largest_supplier_share"]
    d = forecasts.merge(feats[keep], on=["origin", "series_id", "task"], how="left")
    d["scale"] = np.where(d.task == "sum3", d.scale_sum3, d.scale_month)
    for suffix, cols in (("", [c + "_c" for c in QC]), ("_raw", QC)):
        tonnes = np.expm1(d[cols].to_numpy() + d.level.to_numpy()[:, None]).clip(min=0)
        a = d.actual_t.to_numpy()
        d["ase" + suffix] = np.abs(a - tonnes[:, 2]) / d.scale
        d["pinball" + suffix] = mt.scaled_pinball(a, tonnes, d.scale.to_numpy())
        d["cover80" + suffix] = (a >= tonnes[:, 1]) & (a <= tonnes[:, 3])
        d["cover95" + suffix] = (a >= tonnes[:, 0]) & (a <= tonnes[:, 4])
        d["width80" + suffix] = (tonnes[:, 3] - tonnes[:, 1]) / d.scale
        d["crps" + suffix] = mt.crps_from_quantiles(a, tonnes, mt.LEVELS) / d.scale
        for k, v in mt.point_errors(a, tonnes[:, 2], d.scale.to_numpy()).items():
            d[k + suffix] = v
        d["hit" + suffix] = list((a[:, None] <= tonnes))  # outcome at or below each stored quantile
    months_in = lambda r: [r.target_month - pd.DateOffset(months=k) for k in ((0, 1, 2) if r.task == "sum3" else (0,))]  # noqa: E731
    d["shock"] = [any((r.series_id, m) in cells for m in months_in(r)) for r in d[["series_id", "target_month", "task"]].itertuples()]
    return d


def common(d, models):
    """Rows where every model in `models` has a forecast for the same case."""
    key = ["origin", "series_id", "task"]
    sub = d[d.model.isin(models)]
    n = sub.groupby(key).model.nunique()
    full = n[n == len(models)].index
    return sub.set_index(key).loc[full].reset_index()


def accuracy_table(d, models, by=("task",)):
    c = common(d, models)
    g = c.groupby(list(by) + ["model"]).agg(MASE=("ase", "mean"), pinball=("pinball", "mean"), cover80=("cover80", "mean"),
                                            cover95=("cover95", "mean"), width80=("width80", "mean"), n=("ase", "size"))
    return g.reset_index()


def extended_accuracy(d, models):
    """Point and distribution scores beyond MASE, by task and model, on cases every model forecast.

    MAE, RMSE (tonnes) and WAPE are pooled over series, so large importers dominate them; MASE and RMSSE are
    scaled per series and are the comparable scores across series. CRPS is the quantile approximation (scaled like MASE).
    """
    c = common(d, models)
    g = c.groupby(["task", "model"])
    out = g.agg(MAE_t=("abs_err", "mean"), sq=("sq_err", "mean"), abs_sum=("abs_err", "sum"), actual_sum=("actual_t", "sum"),
                RMSSE=("sq_scaled", "mean"), CRPS=("crps", "mean"), CRPS_raw=("crps_raw", "mean"), MASE=("ase", "mean"), n=("ase", "size"))
    out["RMSE_t"] = np.sqrt(out.pop("sq"))
    out["WAPE"] = out.pop("abs_sum") / out.pop("actual_sum")
    out["RMSSE"] = np.sqrt(out.RMSSE)
    return out.reset_index()


def coverage_by_horizon(d, models):
    """Empirical 80% and 95% coverage by task (horizon) and model, raw and conformal, with the case count."""
    c = common(d, models)
    return c.groupby(["task", "model"]).agg(cover80_raw=("cover80_raw", "mean"), cover80=("cover80", "mean"), cover95_raw=("cover95_raw", "mean"),
                                            cover95=("cover95", "mean"), n=("cover80", "size")).reset_index()


def quantile_calibration(d, models):
    """Share of outcomes at or below each stored quantile (conformal), by task and model. Level = perfectly calibrated."""
    c = common(d, models)
    rows = []
    for (task, model), g in c.groupby(["task", "model"]):
        h = np.vstack(g.hit.to_numpy()).mean(axis=0)
        rows.append({"task": task, "model": model, **{f"hit_{c}": v for c, v in zip(QC, h)}})
    return pd.DataFrame(rows)


def pit_table(d, models, bins=10):
    """PIT histogram of the conformal forecast distribution (piecewise-linear CDF through the stored quantiles, normal tails).

    With five stored quantiles the PIT inside the central 80% is interpolated, so this is a coarse check: read the tails and
    the overall shape (U = too narrow, hump = too wide, slope = bias), not the finer bins.
    """
    rows = []
    cols = [c + "_c" for c in QC]
    for (task, model), g in common(d, models).groupby(["task", "model"]):
        pit = calibrate.cdf(g[cols].to_numpy(), g.target.to_numpy())
        share = mt.pit_counts(pit, bins)
        rows.append({"task": task, "model": model, "n": int(len(g)), **{f"bin{i + 1}": v for i, v in enumerate(share)},
                     "tails": float(share[0] + share[-1]), "tails_ideal": 2.0 / bins})
    return pd.DataFrame(rows)


def crossing_table(scored_all):
    """How often quantiles crossed before sorting: learner output (if the archive recorded it) and after the conformal shift."""
    rows = []
    for model, g in scored_all.groupby("model"):
        raw = g.crossed_raw.dropna() if "crossed_raw" in g else pd.Series(dtype=float)
        rows.append({"model": model, "rows": int(len(g)),
                     "crossed_learner": float(raw.mean()) if len(raw) else np.nan,
                     "crossed_conformal": float(g.crossed_c.mean()) if "crossed_c" in g else np.nan})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ hypotheses
def _diff_series(d, a, b, task, col, mask=None):
    c = common(d[d.task == task], [a, b])
    if mask is not None:
        c = c[mask(c)]
    p = c.pivot_table(index=["origin", "series_id"], columns="model", values=col)
    per_origin = (p[a] - p[b]).groupby(level="origin").mean().sort_index()
    return c, per_origin


def _relative(c, a, b, col):
    m = c.groupby("model")[col].mean()
    return 1 - m[a] / m[b], m[a], m[b]


def _bootstrap_rel(c, a, b, col):
    groups = [g for _, g in c.groupby("origin")]
    stat = lambda f: (lambda m: 1 - m.get(a, np.nan) / m.get(b, np.nan))(f.groupby("model")[col].mean())  # noqa: E731
    return mt.block_bootstrap(groups, stat)


def h1(d, m):
    kgz = d[(d.iso3 == "KGZ") & (d.task == "m3")]
    loc = accuracy_table(kgz, LOCAL)
    best = loc.sort_values("MASE").iloc[0].model
    c, diff = _diff_series(kgz, "lgbm_global", best, "m3", "ase")
    rel, ma, mb = _relative(c, "lgbm_global", best, "ase")
    test = mt.hln_test(diff.to_numpy(), 3)
    _, diff_sn = _diff_series(kgz, "lgbm_global", "snaive", "m3", "ase")
    return {"hypothesis": "H1", "comparison": f"lgbm_global vs best local ({best}), Kyrgyz series, h=3",
            "metric": "MASE", "model": float(ma), "reference": float(mb), "relative_improvement": float(rel),
            "ci95": [float(x) for x in _bootstrap_rel(c, "lgbm_global", best, "ase")], "target": 0.05, **test,
            "vs_seasonal_naive_p": mt.hln_test(diff_sn.to_numpy(), 3)["p_one_sided"], "best_local": best}


def pick_neural(d, settings):
    """Choose the neural candidate on the calibration origins only, so the test block is not used for selection."""
    cal = d[(d.origin < pd.Timestamp(str(settings["modeling"]["evaluation_start"]) + "01")) & d.evaluation & (d.task == "m3")]
    t = accuracy_table(cal, NEURAL)
    return t.sort_values("MASE").iloc[0].model if len(t) else "mlp_global"


def h2(d, neural):
    ev_ = d[d.evaluation]
    out = []
    for name, mask in (("all", None), ("shock", lambda c: c.shock), ("normal", lambda c: ~c.shock)):
        for col in ("ase", "pinball"):
            c, diff = _diff_series(ev_, neural, "lgbm_global", "m3", col, mask)
            if c.empty:
                continue
            rel, ma, mb = _relative(c, neural, "lgbm_global", col)
            out.append({"window": name, "metric": "MASE" if col == "ase" else "pinball", "neural": neural, "model": float(ma),
                        "reference": float(mb), "relative_improvement": float(rel), "cases": int(len(c) / 2), **mt.hln_test(diff.to_numpy(), 3)})
    return out


def high_dependence(d, settings):
    m = settings["modeling"]
    pre = d[(d.origin < pd.Timestamp(str(m["evaluation_start"]) + "01")) & (d.model == "lgbm_global") & (d.task == "m3")]
    share = pre.groupby("series_id").largest_supplier_share.median()
    return sorted(share[share >= m["high_dependence_share"]].index)


def h3(d, series):
    sub = d[d.evaluation & d.series_id.isin(series)]
    c, diff = _diff_series(sub, "lgbm_global", "abl_own_history", "m3", "pinball")
    rel, ma, mb = _relative(c, "lgbm_global", "abl_own_history", "pinball")
    return {"hypothesis": "H3", "comparison": "lgbm_global vs own-history LightGBM, high-dependence series, h=3",
            "metric": "pinball (scaled)", "series": series, "model": float(ma), "reference": float(mb), "relative_improvement": float(rel),
            "ci95": [float(x) for x in _bootstrap_rel(c, "lgbm_global", "abl_own_history", "pinball")], "target": 0.03,
            **mt.hln_test(diff.to_numpy(), 3)}


def h4_frame(d, probs, labels, model="lgbm_global"):
    s = probs[probs.model == model].merge(d[(d.model == model) & (d.task == "sum3")][
        ["origin", "series_id", "evaluation", "target_month", "hhi_12m", "largest_supplier_share", "shock"]], on=["origin", "series_id"])
    s = s.merge(labels[["series_id", "target_month", "flag_75", "flag_70", "flag_80", "supply_side", "ratio"]], on=["series_id", "target_month"], how="left")
    return s[s.evaluation & s.ratio.notna()]


def h4(s, budget, seed=0):
    out = {}
    for label, pcol in (("flag_75", "p_short_75"), ("flag_70", "p_short_70"), ("flag_80", "p_short_80"), ("supply_side", "p_short_75"), ("shock", "p_short_75")):
        y = s[label].astype(bool).to_numpy()
        res = {"positives": int(y.sum()), "cases": int(len(y)),
               "pr_auc_model": mt.pr_auc(y, s[pcol]), "pr_auc_hhi": mt.pr_auc(y, s.hhi_12m), "pr_auc_top_share": mt.pr_auc(y, s.largest_supplier_share),
               "base_rate": float(y.mean()), "brier_model": mt.brier(y, s[pcol]),
               "recall_model": mt.recall_at_budget(y, s[pcol], budget), "recall_hhi": mt.recall_at_budget(y, s.hhi_12m, budget)}
        groups = [g for _, g in s.groupby("origin")]
        diffs = []
        rng = np.random.default_rng(seed)
        n, block = len(groups), min(6, len(groups))
        for _ in range(2000):
            picks = []
            while len(picks) < n:
                st = rng.integers(0, n - block + 1)
                picks.extend(range(st, st + block))
            f = pd.concat([groups[i] for i in picks[:n]])
            yy = f[label].astype(bool).to_numpy()
            if yy.any():
                diffs.append(mt.pr_auc(yy, f[pcol]) - mt.pr_auc(yy, f.hhi_12m))
        diffs = np.array(diffs)
        res["diff_ci95"] = [float(x) for x in np.nanpercentile(diffs, [2.5, 97.5])]
        res["p_one_sided"] = float(np.mean(diffs <= 0))
        out[label] = res
    return out


def calibration_table(s, col="p_short_75"):
    bins = np.array([0, 0.1, 0.2, 0.4, 0.6, 1.0])
    s = s[s[col].notna()].assign(bin=lambda f: pd.cut(f[col], bins, include_lowest=True))
    return s.groupby("bin", observed=True).agg(mean_p=(col, "mean"), observed=("flag_75", "mean"), n=("flag_75", "size")).reset_index()


def recalibration_summary(s, budget):
    """Raw vs recalibrated probabilities on the same cases (those with a recalibrated value)."""
    out = {}
    for t in (75, 70, 80):
        y_col, raw, rc, fix = f"flag_{t}", f"p_short_{t}", f"p_short_{t}_rc", f"p_short_{t}_rcfix"
        c = s[s[rc].notna() & s[fix].notna()]
        y = c[y_col].astype(bool).to_numpy()
        base = float(y.mean())
        out[y_col] = {"cases": int(len(c)), "positives": int(y.sum()), "base_rate": base, "brier_climatology": base * (1 - base),
                      "brier_raw": mt.brier(y, c[raw]), "brier_rc": mt.brier(y, c[rc]),
                      "mean_p_raw": float(c[raw].mean()), "mean_p_rc": float(c[rc].mean()),
                      "pr_auc_raw": mt.pr_auc(y, c[raw]), "pr_auc_rc": mt.pr_auc(y, c[rc]), "pr_auc_hhi": mt.pr_auc(y, c.hhi_12m),
                      "recall_raw": mt.recall_at_budget(y, c[raw], budget), "recall_rc": mt.recall_at_budget(y, c[rc], budget),
                      "brier_fix": mt.brier(y, c[fix]), "mean_p_fix": float(c[fix].mean()), "pr_auc_fix": mt.pr_auc(y, c[fix]),
                      "recall_fix": mt.recall_at_budget(y, c[fix], budget)}
    return out


# ------------------------------------------------------------------ figures
def fig_models(acc):
    t = acc[acc.model.isin(MAIN)].pivot(index="model", columns="task", values="MASE").reindex(MAIN)
    ax = t[["m1", "m3", "m6", "sum3"]].plot.bar(figsize=(8, 4), width=0.8)
    ax.axhline(1, color="grey", lw=0.8, ls="--")
    ax.set_xticklabels([LABELS[m] for m in t.index], rotation=30, ha="right")
    ax.set_ylabel("MASE (lower is better)")
    ax.set_title("Point accuracy on Tier 1 series, origins 2023 onward")
    plt.tight_layout()
    plt.savefig(FIGS / "fig01_mase_by_model.png", dpi=150)
    plt.close()


def fig_coverage(acc_raw, acc):
    m = [x for x in MAIN if x in set(acc.model)]
    a = acc[acc.task == "m3"].set_index("model").reindex(m)
    r = acc_raw[acc_raw.task == "m3"].set_index("model").reindex(m)
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(m))
    ax.bar(x - 0.2, r.cover80, 0.4, label="raw")
    ax.bar(x + 0.2, a.cover80, 0.4, label="conformal")
    ax.axhline(0.8, color="black", lw=0.8, ls="--")
    ax.set_xticks(x, [LABELS[i] for i in m], rotation=30, ha="right")
    ax.set_ylabel("Empirical coverage of 80% interval")
    ax.set_title("Interval calibration, h = 3")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGS / "fig02_coverage.png", dpi=150)
    plt.close()


def fig_pr(s):
    from sklearn.metrics import precision_recall_curve
    y = s.flag_75.astype(bool)
    fig, ax = plt.subplots(figsize=(5, 4))
    for col, name in (("p_short_75", "Forecast probability (LightGBM)"), ("hhi_12m", "HHI ranking")):
        ok = s[col].notna()
        p, r, _ = precision_recall_curve(y[ok], s.loc[ok, col])
        ax.plot(r, p, label=name)
    ax.axhline(y.mean(), color="grey", ls="--", lw=0.8, label="base rate")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Shortfall warnings, next three months")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIGS / "fig03_shortfall_pr.png", dpi=150)
    plt.close()


def fig_kgz(d, feats):
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for ax, prod, name in zip(axes, ["gasoline", "middle_incl_blends"], ["Gasoline proxy", "Distillates"]):
        sid = f"KGZ:{prod}"
        f = d[(d.series_id == sid) & (d.model == "lgbm_global") & (d.task == "m3")].sort_values("target_month")
        q = np.expm1(f[[c + "_c" for c in QC]].to_numpy() + f.level.to_numpy()[:, None]) / 1000
        ax.fill_between(f.target_month, q[:, 0], q[:, 4], alpha=0.15, color="tab:blue", label="95% interval")
        ax.fill_between(f.target_month, q[:, 1], q[:, 3], alpha=0.3, color="tab:blue", label="80% interval")
        ax.plot(f.target_month, q[:, 2], color="tab:blue", label="median forecast, 3 months ahead")
        ax.plot(f.target_month, f.actual_t / 1000, "k.-", lw=0.8, label="actual")
        ax.set_ylabel("thousand t")
        ax.set_title(f"Kyrgyzstan, {name}")
    axes[0].legend(fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(FIGS / "fig04_kgz_forecasts.png", dpi=150)
    plt.close()


def fig_ablation(abl):
    t = abl.set_index("variant").pinball_change.sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(t.index, t.values * 100, color=["tab:red" if v > 0 else "tab:green" for v in t.values])
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("Change in pinball loss vs full LightGBM, % (positive = worse)")
    ax.set_title("Ablation, Tier 1 series, h = 3")
    plt.tight_layout()
    plt.savefig(FIGS / "fig05_ablation.png", dpi=150)
    plt.close()


def fig_pit(pit):
    """PIT histograms at h = 3 for the main models."""
    t = pit[pit.task == "m3"].set_index("model").reindex([x for x in MAIN if x in set(pit.model)])
    bins = [c for c in pit.columns if c.startswith("bin")]
    fig, axes = plt.subplots(3, 3, figsize=(9, 7), sharey=True)
    for ax, (model, r) in zip(axes.ravel(), t.iterrows()):
        ax.bar(range(len(bins)), r[bins].to_numpy(float), color="tab:blue")
        ax.axhline(1 / len(bins), color="black", lw=0.8, ls="--")
        ax.set_title(LABELS[model], fontsize=8)
        ax.set_xticks([])
    for ax in axes.ravel()[len(t):]:
        ax.axis("off")
    fig.suptitle("PIT histograms, h = 3, conformal intervals (dashed = uniform)", fontsize=10)
    plt.tight_layout()
    plt.savefig(FIGS / "fig07_pit_h3.png", dpi=150)
    plt.close()


def fig_reliability(cal, base_rate, cal_rc=None, cal_fix=None):
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.plot([0, 0.8], [0, 0.8], color="grey", ls="--", lw=0.8, label="perfect calibration")
    ax.plot(cal.mean_p, cal.observed, "o-", color="tab:blue", label="raw probability")
    for r in cal.itertuples():
        ax.annotate(f"n={r.n}", (r.mean_p, r.observed), textcoords="offset points", xytext=(4, -10), fontsize=7)
    # bins with fewer than 10 cases are left out of the recalibrated curves (the table keeps them)
    if cal_rc is not None:
        c = cal_rc[cal_rc.n >= 10]
        ax.plot(c.mean_p, c.observed, "s-", color="tab:green", label="recalibrated, rolling (as-of Platt)")
    if cal_fix is not None:
        c = cal_fix[cal_fix.n >= 10]
        ax.plot(c.mean_p, c.observed, "^-", color="tab:purple", label="recalibrated, fixed map (Jan 2023)")
    ax.axhline(base_rate, color="tab:orange", lw=0.8, label="base rate")
    ax.set_xlabel("Mean forecast probability")
    ax.set_ylabel("Observed shortfall frequency")
    ax.set_title("Reliability of shortfall probabilities")
    ax.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(FIGS / "fig06_shortfall_reliability.png", dpi=150)
    plt.close()


# ------------------------------------------------------------------ driver
def run(settings):
    m = settings["modeling"]
    for p in (TABLES, FIGS):
        p.mkdir(parents=True, exist_ok=True)
    feats = ft.load()
    series = pn.series_table(settings)
    monthly = pn.monthly_panel(settings, series)
    raw = pd.read_parquet(pn.MODELING / "forecasts_raw.parquet")
    conf = calibrate.conformalise(raw, feats, m["conformal"]["window"], m["conformal"]["min_scores"])
    probs = calibrate.shortfall_probability(conf, feats)
    labels = realised_labels(monthly, series)
    rc = m["recalibration"]
    probs = calibrate.recalibrate(probs, feats, labels, rc["window"], rc["min_events"],
                                  freeze_at=pd.Timestamp(str(m["evaluation_start"]) + "01"))
    archive = conf.merge(feats[["origin", "series_id", "task", "level", "target_month"]], on=["origin", "series_id", "task"])
    tonnes = np.expm1(archive[[c + "_c" for c in QC]].to_numpy() + archive.level.to_numpy()[:, None]).clip(min=0)
    archive[[c + "_t" for c in QC]] = tonnes
    archive = archive.merge(probs[["model", "origin", "series_id", "task", "p_short_75", "p_short_70", "p_short_80",
                                   "p_short_75_rc", "p_short_70_rc", "p_short_80_rc"]], how="left",
                            on=["model", "origin", "series_id", "task"])
    archive["rules_version"] = m["rules_version"]
    archive.to_parquet(pn.MODELING / "forecasts.parquet", index=False)

    cells = shock_cells(settings, monthly)
    scored = score(settings, conf, feats, cells)
    cal_start = pd.Timestamp(str(m["evaluation_start"]) + "01")
    neural = pick_neural(scored[scored.target.notna()], settings)
    d = scored[(scored.origin >= cal_start) & scored.target.notna()]
    ev_ = d[d.evaluation]

    acc = accuracy_table(ev_, [x for x in MAIN if x in set(d.model)])
    acc_raw = accuracy_table(ev_.assign(ase=ev_.ase_raw, pinball=ev_.pinball_raw, cover80=ev_.cover80_raw, cover95=ev_.cover95_raw,
                                         width80=ev_.width80_raw), [x for x in MAIN if x in set(d.model)])
    acc_shock = accuracy_table(ev_[ev_.task == "m3"], [x for x in MAIN if x in set(d.model)], by=("shock",))
    acc.to_csv(TABLES / "accuracy.csv", index=False)
    acc_raw.to_csv(TABLES / "accuracy_raw_intervals.csv", index=False)
    acc_shock.to_csv(TABLES / "accuracy_by_shock_window.csv", index=False)
    mains = [x for x in MAIN if x in set(d.model)]
    ext = extended_accuracy(ev_, mains)
    cov_h = coverage_by_horizon(ev_, mains)
    qcal = quantile_calibration(ev_, mains)
    pit = pit_table(ev_, mains, m.get("diagnostics", {}).get("pit_bins", 10))
    cross = crossing_table(d)
    for name, tab in (("accuracy_extended", ext), ("coverage_by_horizon", cov_h), ("quantile_calibration", qcal), ("pit", pit), ("quantile_crossing", cross)):
        tab.to_csv(TABLES / f"{name}.csv", index=False)
    fig_pit(pit)
    accuracy_table(d[d.iso3 == "KGZ"], [x for x in MAIN if x in set(d.model)], by=("product_group", "task")).to_csv(TABLES / "accuracy_kyrgyzstan.csv", index=False)

    abl_models = [x for x in sorted(set(d.model)) if x.startswith("abl_")]
    rows = []
    for a in abl_models:
        sub = ev_
        if a == "abl_without_kgz":
            sub = d[d.iso3 == "KGZ"]
        elif a == "abl_strict_importers":  # a strict-importer panel is evaluated on strict importers only
            sub = ev_[ev_.series_id.isin(series[series.importer_type_provisional == "strict_importer"].series_id)]
        c = common(sub[sub.task == "m3"], ["lgbm_global", a])
        g = c.groupby("model")[["ase", "pinball", "cover80"]].mean()
        rows.append({"variant": a, "cases": int(len(c) / 2), "mase_change": g.ase[a] / g.ase["lgbm_global"] - 1,
                     "pinball_change": g.pinball[a] / g.pinball["lgbm_global"] - 1, "cover80": g.cover80[a]})
    c = ev_[(ev_.model == "lgbm_global") & (ev_.task == "m3")]
    rows.append({"variant": "abl_no_conformal", "cases": len(c), "mase_change": c.ase_raw.mean() / c.ase.mean() - 1,
                 "pinball_change": c.pinball_raw.mean() / c.pinball.mean() - 1, "cover80": c.cover80_raw.mean()})
    c = common(ev_[ev_.task == "m3"], ["lgbm_global", "lgbm_local"]).groupby("model")[["ase", "pinball", "cover80"]].mean()
    rows.append({"variant": "abl_local_training", "cases": None, "mase_change": c.ase["lgbm_local"] / c.ase["lgbm_global"] - 1,
                 "pinball_change": c.pinball["lgbm_local"] / c.pinball["lgbm_global"] - 1, "cover80": c.cover80["lgbm_local"]})
    abl = pd.DataFrame(rows)
    abl.to_csv(TABLES / "ablation.csv", index=False)

    s = h4_frame(d, probs, labels)
    res = {"H1": h1(d, m), "H2": h2(d, neural), "H3": h3(d, high_dependence(scored, settings)), "H4": h4(s, m["alert_budget"])}
    primary = [res["H1"]["p_one_sided"], next((r["p_one_sided"] for r in res["H2"] if r["window"] == "shock" and r["metric"] == "MASE"), np.nan),
               res["H3"]["p_one_sided"], res["H4"]["flag_75"]["p_one_sided"]]
    res["holm"] = dict(zip(["H1", "H2_shock", "H3", "H4"], [float(x) for x in mt.holm(np.nan_to_num(primary, nan=1.0))]))
    res["meta"] = {"rules_version": m["rules_version"], "evaluation_start": str(cal_start.date()), "last_origin": str(d.origin.max().date()),
                   "origins": int(d.origin.nunique()), "neural_selected": neural}
    res["recalibration"] = recalibration_summary(s, m["alert_budget"])
    cal, cal_rc, cal_fix = calibration_table(s), calibration_table(s, "p_short_75_rc"), calibration_table(s, "p_short_75_rcfix")
    pd.concat([cal.assign(probability="raw"), cal_rc.assign(probability="rolling"), cal_fix.assign(probability="fixed")]).to_csv(
        TABLES / "shortfall_calibration.csv", index=False)
    fig_reliability(cal, float(s.flag_75.mean()), cal_rc, cal_fix)
    s.to_csv(TABLES / "shortfall_cases.csv", index=False)
    (OUT / "results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")

    from src.modeling import h4_extra  # exploratory R1/R2 additions; they do not touch results.json
    expl, strata, _ = h4_extra.run_all(d, probs, labels, monthly, series, settings)
    expl.to_csv(TABLES / "h4_exploratory_benchmarks.csv", index=False)
    strata.to_csv(TABLES / "h4_exploratory_strata.csv", index=False)

    fig_models(acc)
    fig_coverage(acc_raw, acc)
    fig_pr(s)
    fig_kgz(scored[scored.origin >= cal_start], feats)
    fig_ablation(abl)
    from src.modeling.report import write
    write(res, acc, acc_raw, acc_shock, abl, settings, extra={"ext": ext, "cov_h": cov_h, "qcal": qcal, "pit": pit, "cross": cross}, expl=(expl, strata))
    log.info("evaluation written to %s", OUT)
    return res
