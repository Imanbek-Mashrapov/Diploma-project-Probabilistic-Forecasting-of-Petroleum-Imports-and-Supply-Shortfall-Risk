"""Local benchmark models: naive, seasonal naive, 12-month mean, ETS and SARIMA.

All forecasts are quantiles of the task target (log mass minus series level), so they share one
format with the learned models. Naive-family quantiles come from the same rule's past errors on
the same series, using only errors whose target had been released by the origin.
"""
import logging
import warnings

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from src.modeling import panel as pn
from src.modeling.features import TASKS, TASK_H, months_index

log = logging.getLogger(__name__)
QCOLS = ["q025", "q100", "q500", "q900", "q975"]
LEVELS = np.array([0.025, 0.1, 0.5, 0.9, 0.975])
MIN_RESID = 8


def rule_points(table):
    """Point forecasts of the naive rules in target units."""
    return pd.DataFrame({"naive": table.last1, "snaive": table.seas12.fillna(table.last1), "mean12": 0.0}, index=table.index)


def empirical_quantiles(table, points, origins):
    """For each origin, quantiles = point + quantiles of past residuals of the same rule (series first, task pool fallback)."""
    out = []
    resid_all = table.target - points
    for o in origins:
        now = table[table.origin == o]
        if now.empty:
            continue
        known = table[(table.origin < o) & (table.target_available_on <= pn.origin_end(o))]
        r = resid_all.loc[known.index]
        for idx, row in now.iterrows():
            same = r[(known.series_id == row.series_id) & (known.task == row.task)].dropna()
            if len(same) < MIN_RESID:
                same = r[known.task == row.task].dropna()
            if len(same) < MIN_RESID or np.isnan(points.loc[idx]):
                continue
            q = points.loc[idx] + np.quantile(same.to_numpy(), LEVELS)
            out.append([o, row.series_id, row.task, *q])
    return pd.DataFrame(out, columns=["origin", "series_id", "task", *QCOLS])


def naive_family(table, origins):
    pts = rule_points(table)
    frames = []
    for name in pts.columns:
        f = empirical_quantiles(table, pts[name], origins)
        f["model"] = name
        frames.append(f)
    return pd.concat(frames, ignore_index=True)


def _simulate_paths(kind, logs, last_idx, steps, reps, seed):
    """Simulated log1p paths for `steps` months after index `last_idx`, or None if the model cannot be fitted."""
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if kind == "sarima":
            first = np.flatnonzero(~np.isnan(logs))[0]
            y = logs[first:last_idx + 1]
            if np.sum(~np.isnan(y)) < 36:
                return None
            res = SARIMAX(y, order=(0, 1, 1), seasonal_order=(0, 1, 1, 12)).fit(disp=False)
            np.random.seed(seed)  # this statsmodels/pandas pairing rejects random_state in MLEResults.simulate
            return res.simulate(steps, repetitions=reps, anchor="end").reshape(steps, reps).T
        # ETS needs an unbroken run; use the latest run ending at the last visible month
        y = logs[:last_idx + 1]
        gaps = np.flatnonzero(np.isnan(y))
        start = gaps[-1] + 1 if len(gaps) else 0
        run = y[start:]
        if len(run) < 36:
            return None
        res = ExponentialSmoothing(run, trend=None, seasonal="add", seasonal_periods=12).fit()
        return res.simulate(steps, repetitions=reps, anchor="end", random_state=seed).reshape(steps, reps).T


def _series_statistical(kind, series_rows, months, mass, avail, reps=400):
    out, failures = [], []
    logm = np.log1p(mass)
    for o, rows in series_rows.groupby("origin"):
        oi = (o.to_period("M") - months[0].to_period("M")).n
        visible = ~np.isnan(mass) & (avail <= np.datetime64(pn.origin_end(o)))
        visible[oi + 1:] = False
        idx = np.flatnonzero(visible)
        if len(idx) == 0:
            continue
        last = idx[-1]
        logs = np.where(visible, logm, np.nan)
        steps = oi + 6 - last
        try:
            paths = _simulate_paths(kind, logs, last, steps, reps, seed=int(oi))
        except Exception as e:  # a failed fit is recorded as a missing forecast and counted, never replaced
            failures.append(f"{type(e).__name__}: {e}")
            paths = None
        if paths is None:
            continue
        mass_paths = np.expm1(paths)
        for r in rows.itertuples():
            off = oi - last  # months between last visible month and the origin month
            if r.task == "sum3":
                sim = np.log1p(np.clip(mass_paths[:, off:off + 3], 0, None).mean(axis=1))
            else:
                sim = paths[:, off + TASK_H[r.task] - 1]
            out.append([o, r.series_id, r.task, *(np.quantile(sim, LEVELS) - r.level)])
    return out, failures


def statistical(table, monthly, origins, kind, n_jobs=-1):
    months = months_index(monthly)
    rows = table[table.origin.isin(origins)]
    jobs = []
    for sid, part in rows.groupby("series_id"):
        g = monthly[monthly.series_id == sid].set_index("month").reindex(months)
        jobs.append(delayed(_series_statistical)(kind, part, months, g.import_mass_t.to_numpy(float),
                                                 g.available_on.to_numpy("datetime64[ns]")))
    res = Parallel(n_jobs=n_jobs)(jobs)
    out = pd.DataFrame([r for part, _ in res for r in part], columns=["origin", "series_id", "task", *QCOLS])
    out["model"] = kind
    failures = [f for _, part in res for f in part]
    log.info("%s: %d forecasts, %d failed fits", kind, len(out), len(failures))
    if failures:
        log.warning("%s first failure: %s", kind, failures[0][:300])
    return out
