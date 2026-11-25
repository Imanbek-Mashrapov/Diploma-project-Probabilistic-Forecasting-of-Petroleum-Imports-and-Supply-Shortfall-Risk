"""Rolling-origin backtest: every model forecasts at every monthly origin with only data public then.

Origins run from modeling.calibration_start to the live origin. Origins before
modeling.evaluation_start only feed the conformal step. Learned models are refitted every
`refit_every` origins on examples whose target had been released by the refit origin; between
refits the last model is reused, which never uses newer information.

Output: data/modeling/forecasts_raw.parquet, one row per (model, origin, series, task) with
quantiles in target units (log mass minus series level).
"""
import logging
import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from src.modeling import baselines, features as ft, panel as pn
from src.modeling.learners import LightGBMQuantile, NeuralQuantile

log = logging.getLogger(__name__)
QCOLS = baselines.QCOLS
ALL = ("own", "supplier", "external", "shock", "uv")


def variants(settings):
    """Learned-model configurations: main models and the ablation arms of proposal section 3.11."""
    m = settings["modeling"]
    lgbm = lambda: LightGBMQuantile(m["lightgbm"])  # noqa: E731
    return {
        "lgbm_global": dict(make=lgbm, groups=ALL),
        "lgbm_local": dict(make=lambda: LightGBMQuantile(m["lightgbm"] | {"min_child_samples": 10}, with_id=False), groups=ALL, local=True),
        "mlp_global": dict(make=lambda: NeuralQuantile(m["neural"], "mlp", m["seeds"], m["n_lags"]), groups=ALL),
        "gru_global": dict(make=lambda: NeuralQuantile(m["neural"], "gru", m["seeds"], m["n_lags"]), groups=ALL),
        "abl_own_history": dict(make=lgbm, groups=("own",)),
        "abl_no_supplier": dict(make=lgbm, groups=("own", "external", "shock", "uv")),
        "abl_no_shock": dict(make=lgbm, groups=("own", "supplier", "external", "uv")),
        "abl_no_external": dict(make=lgbm, groups=("own", "supplier", "shock", "uv")),
        "abl_no_uv": dict(make=lgbm, groups=("own", "supplier", "external", "shock")),
        "abl_strict_importers": dict(make=lgbm, groups=ALL, train_filter="strict"),
        "abl_train_to_2021": dict(make=lgbm, groups=ALL, freeze="2021-12-01"),
        "abl_from_2018": dict(make=lgbm, groups=ALL, train_filter="from2018"),
        "abl_without_kgz": dict(make=lgbm, groups=ALL, train_filter="no_kgz"),
    }


def origins(settings, live_origin):
    start = pd.Timestamp(str(settings["modeling"]["calibration_start"]) + "01")
    return pd.date_range(start, pd.Timestamp(live_origin), freq="MS")


def training_rows(feats, refit_origin, series, train_filter=None):
    known = (feats.origin < refit_origin) & (feats.target_available_on <= pn.origin_end(refit_origin)) & feats.target.notna()
    train = feats[known]
    if train_filter == "strict":
        strict = series[series.importer_type_provisional == "strict_importer"].series_id
        train = train[train.series_id.isin(strict)]
    elif train_filter == "from2018":
        train = train[train.target_month >= "2018-01-01"]
    elif train_filter == "no_kgz":
        train = train[train.iso3 != "KGZ"]
    return train


def _block(spec, cols, feats, series, refit, block):
    """Fit once at `refit`, predict every origin in `block`."""
    train = training_rows(feats, refit, series, spec.get("train_filter"))
    test = feats[feats.origin.isin(block)]
    out = []
    if spec.get("local"):
        for sid, part in test.groupby("series_id"):
            tr = train[train.series_id == sid]
            if len(tr) < 40:
                continue
            model = spec["make"]().fit(tr, cols)
            out.append(_frame(part, model.predict(part), model.crossed))
    else:
        if len(train) < 200:
            return None
        model = spec["make"]().fit(train, cols)
        out.append(_frame(test, model.predict(test), model.crossed))
    return pd.concat(out, ignore_index=True) if out else None


def _frame(rows, q, crossed=None):
    """Forecast rows; `crossed` records whether the learner's raw quantiles crossed before sorting (diagnostic)."""
    f = rows[["origin", "series_id", "task"]].reset_index(drop=True)
    f[QCOLS] = q
    if crossed is not None:
        f["crossed_raw"] = np.asarray(crossed, bool)
    return f


def run_learned(settings, feats, series, name, spec, all_origins):
    every = settings["modeling"]["refit_every"]
    cols = ft.feature_columns(settings, spec["groups"])
    if spec.get("freeze"):
        refit = pd.Timestamp(spec["freeze"])
        blocks = [(refit, list(all_origins[all_origins >= refit]))]
    else:
        blocks = [(all_origins[i], list(all_origins[i:i + every])) for i in range(0, len(all_origins), every)]
    t0 = time.time()
    parts = Parallel(n_jobs=-1)(delayed(_block)(spec, cols, feats, series, r, b) for r, b in blocks)
    out = pd.concat([p for p in parts if p is not None], ignore_index=True)
    out["model"] = name
    log.info("%s: %d forecasts in %.0fs", name, len(out), time.time() - t0)
    return out


def run(settings, live_origin, only=None):
    """Run all models (or those named in `only`) and append to the raw forecast archive."""
    feats = ft.load()
    series = pn.series_table(settings)
    monthly = pn.monthly_panel(settings, series)
    all_origins = origins(settings, live_origin)
    feats = feats[feats.origin <= all_origins[-1]]
    frames = []
    wanted = lambda n: only is None or n in only  # noqa: E731
    if any(wanted(n) for n in ("naive", "snaive", "mean12")):
        f = baselines.naive_family(feats, all_origins)
        frames.append(f[f.model.map(wanted)])
    for kind in ("ets", "sarima"):
        if wanted(kind):
            frames.append(baselines.statistical(feats, monthly, all_origins, kind))
    for name, spec in variants(settings).items():
        if wanted(name):
            frames.append(run_learned(settings, feats, series, name, spec, all_origins))
    new = pd.concat(frames, ignore_index=True)
    path = pn.MODELING / "forecasts_raw.parquet"
    if path.exists():
        old = pd.read_parquet(path)
        new = pd.concat([old[~old.model.isin(new.model.unique())], new], ignore_index=True)
    new.to_parquet(path, index=False)
    log.info("forecast archive: %d rows, models %s", len(new), sorted(new.model.unique()))
    return new
