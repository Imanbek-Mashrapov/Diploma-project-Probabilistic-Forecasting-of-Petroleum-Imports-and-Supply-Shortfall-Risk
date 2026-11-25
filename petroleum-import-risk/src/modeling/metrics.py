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


def quantile_weights(levels=LEVELS):
    """Integration weights for the stored quantile levels: each level gets the share of (0, 1) closer to it than to any other."""
    lv = np.asarray(levels, float)
    edges = np.concatenate([[0.0], (lv[1:] + lv[:-1]) / 2, [1.0]])
    return np.diff(edges)


def crps_from_quantiles(actual, quantiles, levels=LEVELS):
    """CRPS approximated from stored quantiles: 2 * sum_i w_i * pinball_i (CRPS = 2 * integral of the pinball loss over the level).

    The weights are nearest-level shares of (0, 1), so the tails beyond the outermost levels are
    carried by those levels. This is an approximation, not an exact CRPS. quantiles: (n, len(levels)).
    """
    lv = np.asarray(levels, float)
    diff = np.asarray(actual, float)[:, None] - np.asarray(quantiles, float)
    loss = np.maximum(lv * diff, (lv - 1) * diff)
    return 2 * (loss * quantile_weights(lv)).sum(axis=1)


def crossing_rate(quantiles):
    """Share of rows whose quantiles are not non-decreasing in the level (before any sorting)."""
    q = np.asarray(quantiles, float)
    ok = ~np.isnan(q).any(axis=1)
    return float((np.diff(q[ok], axis=1) < 0).any(axis=1).mean()) if ok.any() else np.nan


def quantile_hit_rates(actual, quantiles):
    """Share of outcomes at or below each stored quantile; should equal the level when calibrated."""
    a = np.asarray(actual, float)[:, None]
    q = np.asarray(quantiles, float)
    ok = ~(np.isnan(a) | np.isnan(q)).any(axis=1)
    return (a[ok] <= q[ok]).mean(axis=0)


def pit_counts(pit, bins=10):
    """Share of PIT values in `bins` equal-width bins (uniform = 1/bins each)."""
    p = np.asarray(pit, float)
    p = p[~np.isnan(p)]
    return np.histogram(p, bins=bins, range=(0, 1))[0] / max(len(p), 1)


def point_errors(actual, point, scale):
    """Absolute, squared and scaled errors of a point forecast (tonnes), for MAE, RMSE, WAPE and RMSSE."""
    e = np.asarray(actual, float) - np.asarray(point, float)
    return {"abs_err": np.abs(e), "sq_err": e ** 2, "sq_scaled": (e / np.asarray(scale, float)) ** 2}


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
