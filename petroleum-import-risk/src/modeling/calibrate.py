"""Conformal adjustment of forecast intervals and shortfall probabilities.

Conformalised quantile regression (Romano et al., 2019), applied per model and task and pooled
across series: at origin t the scores come from that model's forecasts at the previous `window`
origins whose targets had been released by t. With fewer than `min_scores` scores the
interval is left as it is and the row is flagged.

Shortfall probability (proposal eq. 3): Pr(Q / B < threshold), where Q is the next-three-month
mean (task sum3) and B the as-of seasonal baseline. The predictive CDF is linear between the
stored quantiles, with normal tails fitted to the outer quantiles.
"""
import numpy as np
import pandas as pd
from scipy.stats import norm

from src.modeling import panel as pn

QCOLS = ["q025", "q100", "q500", "q900", "q975"]
LEVELS = np.array([0.025, 0.1, 0.5, 0.9, 0.975])
PAIRS = {0.8: ("q100", "q900"), 0.95: ("q025", "q975")}


def _conformal_quantile(scores, coverage):
    n = len(scores)
    k = min(1.0, np.ceil((n + 1) * coverage) / n)
    return float(np.quantile(scores, k, method="higher"))


def conformalise(forecasts, feats, window=24, min_scores=30):
    """Return forecasts with conformal quantile columns (suffix _c) and a `conformal_ok` flag."""
    f = forecasts.merge(feats[["origin", "series_id", "task", "target", "target_available_on"]], on=["origin", "series_id", "task"], how="left")
    f = f.sort_values("origin").reset_index(drop=True)
    for c in QCOLS:
        f[c + "_c"] = f[c]
    f["conformal_ok"] = False
    for (_, _), g in f.groupby(["model", "task"]):
        for o in g.origin.unique():
            past = g[(g.origin < o) & (g.origin >= o - pd.DateOffset(months=window)) & g.target.notna()
                     & (g.target_available_on <= pn.origin_end(o))]
            if len(past) < min_scores:
                continue
            now = g.index[g.origin == o]
            for cov, (lo, hi) in PAIRS.items():
                s = np.maximum(past[lo] - past.target, past.target - past[hi]).to_numpy()
                q = _conformal_quantile(s, cov)
                f.loc[now, lo + "_c"] = f.loc[now, lo] - q
                f.loc[now, hi + "_c"] = f.loc[now, hi] + q
            f.loc[now, "conformal_ok"] = True
    cc = [c + "_c" for c in QCOLS]
    f["crossed_c"] = (np.diff(f[cc].to_numpy(), axis=1) < 0).any(axis=1)  # diagnostic: conformal shifts before sorting
    f[cc] = np.sort(f[cc].to_numpy(), axis=1)
    return f.drop(columns=["target", "target_available_on"])


def cdf(q, x):
    """P(target <= x) for rows of quantiles q (n, 5) at points x (n,)."""
    q = np.asarray(q, float)
    x = np.asarray(x, float)
    p = np.empty(len(x))
    for i in range(len(x)):
        qi, xi = q[i], x[i]
        if np.isnan(xi) or np.isnan(qi).any():
            p[i] = np.nan
        elif xi <= qi[0]:
            sd = max((qi[2] - qi[0]) / 1.96, 1e-6)
            p[i] = norm.cdf(norm.ppf(LEVELS[0]) + (xi - qi[0]) / sd)
        elif xi >= qi[-1]:
            sd = max((qi[-1] - qi[2]) / 1.96, 1e-6)
            p[i] = norm.cdf(norm.ppf(LEVELS[-1]) + (xi - qi[-1]) / sd)
        else:
            qs, idx = np.unique(qi, return_index=True)
            p[i] = np.interp(xi, qs, LEVELS[idx])
    return p


def shortfall_probability(forecasts, feats, thresholds=(0.75, 0.70, 0.80), conformal=True):
    """Probability of a shortfall in the next three months for every sum3 forecast."""
    cols = [c + "_c" for c in QCOLS] if conformal else QCOLS
    s = forecasts[forecasts.task == "sum3"].merge(feats[feats.task == "sum3"][["origin", "series_id", "level", "baseline_asof"]],
                                                   on=["origin", "series_id"], how="left")
    for t in thresholds:
        cut = np.log1p(t * s.baseline_asof) - s.level
        s[f"p_short_{int(round(t * 100))}"] = cdf(s[cols].to_numpy(), cut.to_numpy())
    return s.drop(columns=["level", "baseline_asof"])


def _logit(p):
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def recalibrate(probs, feats, labels, window=24, min_events=10, freeze_at=None):
    """As-of Platt recalibration of shortfall probabilities (post-hoc extension, docs/decision_log.md 2026-11-25).

    At origin t, for each model and threshold, fit Pr(shortfall) = sigmoid(a + b * logit(p)) on that model's
    forecasts from the previous `window` origins whose outcome had been released by t, pooled over all series.
    Fewer than `min_events` shortfalls or non-shortfalls -> no recalibrated value (NaN), never a guess.
    Adds p_short_<t>_rc columns. With `freeze_at`, also adds p_short_<t>_rcfix: one map fitted at that origin and
    applied unchanged to it and every later origin. A single monotone map keeps the ranking across origins.
    """
    from sklearn.linear_model import LogisticRegression
    s3 = feats[feats.task == "sum3"][["origin", "series_id", "target_month", "target_available_on"]]
    d = probs.merge(s3, on=["origin", "series_id"], how="left")
    lab = labels[labels.ratio.notna()][["series_id", "target_month", "flag_75", "flag_70", "flag_80"]]
    d = d.merge(lab, on=["series_id", "target_month"], how="left")
    for t in (75, 70, 80):
        p, y = f"p_short_{t}", f"flag_{t}"
        d[p + "_rc"] = np.nan
        d[p + "_rcfix"] = np.nan
        for _, g in d.groupby("model"):
            for o in np.sort(g.origin.unique()):
                o = pd.Timestamp(o)
                past = g[(g.origin < o) & (g.origin >= o - pd.DateOffset(months=window))
                         & (g.target_available_on <= pn.origin_end(o)) & g[y].notna() & g[p].notna()]
                yy = past[y].astype(bool).to_numpy()
                if yy.sum() < min_events or (~yy).sum() < min_events:
                    continue
                fit = LogisticRegression(C=1e6).fit(_logit(past[p])[:, None], yy)
                now = g.index[(g.origin == o) & g[p].notna()]
                d.loc[now, p + "_rc"] = fit.predict_proba(_logit(d.loc[now, p])[:, None])[:, 1]
                if freeze_at is not None and o == freeze_at:
                    later = g.index[(g.origin >= o) & g[p].notna()]
                    d.loc[later, p + "_rcfix"] = fit.predict_proba(_logit(d.loc[later, p])[:, None])[:, 1]
    return d.drop(columns=["target_month", "target_available_on", "flag_75", "flag_70", "flag_80"])
