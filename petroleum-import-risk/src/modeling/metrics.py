"""Forecast metrics and comparison tests (proposal Table 7)."""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import average_precision_score

LEVELS = np.array([0.025, 0.1, 0.5, 0.9, 0.975])


def scaled_pinball(actual, quantiles, scale):
    """Mean pinball loss over the stored quantile levels, divided by the MASE scale. quantiles: (n, 5) in tonnes."""
    diff = actual[:, None] - quantiles
    loss = np.maximum(LEVELS * diff, (LEVELS - 1) * diff).mean(axis=1)
    return loss / scale


def recall_at_budget(y, score, budget):
    """Share of true shortfalls among the top `budget` share of cases ranked by score."""
    y, score = np.asarray(y, bool), np.asarray(score, float)
    ok = ~np.isnan(score)
    y, score = y[ok], score[ok]
    if y.sum() == 0:
        return np.nan
    k = max(1, int(round(budget * len(score))))
    top = np.argsort(-score, kind="stable")[:k]
    return float(y[top].sum() / y.sum())


def pr_auc(y, score):
    y, score = np.asarray(y, bool), np.asarray(score, float)
    ok = ~np.isnan(score)
    return float(average_precision_score(y[ok], score[ok])) if y[ok].any() else np.nan


def brier(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    ok = ~np.isnan(p)
    return float(np.mean((p[ok] - y[ok]) ** 2))


def hln_test(d, h):
    """Diebold-Mariano test with the Harvey-Leybourne-Newbold correction.

    d: loss differential series ordered in time (loss of A minus loss of B). A one-sided p-value
    for 'A has lower expected loss' is returned with the statistic and the mean differential.
    """
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    n = len(d)
    if n < 8:
        return {"n": n, "mean_diff": np.nan, "stat": np.nan, "p_one_sided": np.nan}
    dbar = d.mean()
    gamma = [np.mean((d[k:] - dbar) * (d[:n - k] - dbar)) for k in range(h)]
    var = (gamma[0] + 2 * sum(gamma[1:])) / n
    if var <= 0:
        var = gamma[0] / n
    dm = dbar / np.sqrt(var)
    corr = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    stat = dm * corr
    return {"n": n, "mean_diff": float(dbar), "stat": float(stat), "p_one_sided": float(stats.t.cdf(stat, df=n - 1))}


def holm(pvalues):
    """Holm-adjusted p-values, same order as the input."""
    p = np.asarray(pvalues, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    m = len(p)
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    return adj


def block_bootstrap(groups, statistic, n_boot=2000, block=6, seed=0):
    """Moving-block bootstrap over time. groups: list of per-origin DataFrames in time order; statistic(frame) -> float."""
    rng = np.random.default_rng(seed)
    n = len(groups)
    block = min(block, n)
    out = []
    for _ in range(n_boot):
        picks = []
        while len(picks) < n:
            s = rng.integers(0, n - block + 1)
            picks.extend(range(s, s + block))
        frame = pd.concat([groups[i] for i in picks[:n]], ignore_index=True)
        out.append(statistic(frame))
    return np.nanpercentile(out, [2.5, 97.5])
