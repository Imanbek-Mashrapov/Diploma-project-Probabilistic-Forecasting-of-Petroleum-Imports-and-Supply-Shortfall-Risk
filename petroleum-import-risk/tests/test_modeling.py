"""Tests for the Phase 3 modelling code: leakage rules, calibration and metrics. No built data needed."""
import numpy as np
import pandas as pd
import pytest

from src.modeling import backtest, calibrate, metrics as mt, panel as pn
from src.modeling.features import _baseline, _seasonal_scale, _window_mean


def test_origin_end_is_last_moment_of_month():
    end = pn.origin_end(pd.Timestamp("2024-02-01"))
    assert end < pd.Timestamp("2024-03-01") and end > pd.Timestamp("2024-02-29 23:59:59")


def test_training_rows_never_include_unreleased_targets():
    feats = pd.DataFrame({
        "origin": pd.to_datetime(["2023-01-01", "2023-02-01", "2023-03-01", "2023-01-01"]),
        "series_id": ["A:g"] * 4, "iso3": ["A"] * 4, "target_month": pd.to_datetime(["2023-04-01"] * 4),
        "target_available_on": pd.to_datetime(["2023-03-15", "2023-06-01", "2023-02-01", pd.NaT]),
        "target": [0.1, 0.2, 0.3, np.nan]})
    rows = backtest.training_rows(feats, pd.Timestamp("2023-03-01"), pd.DataFrame())
    # origin 2023-03 is not before the refit origin; the 2023-02 row is released only in June; NaN targets drop
    assert list(rows.target) == [0.1]


def test_window_mean_and_baseline_skip_missing_years():
    v = np.arange(48, dtype=float)
    v[47 - 12] = np.nan  # break the window one year back
    assert np.isnan(_window_mean(v, 35))
    assert _baseline(v, 47, 3) == pytest.approx(np.mean([_window_mean(v, 23), _window_mean(v, 11)]))


def test_seasonal_scale_needs_enough_pairs():
    assert np.isnan(_seasonal_scale(np.arange(15, dtype=float)))
    assert _seasonal_scale(np.arange(30, dtype=float)) == 12


def test_cdf_is_monotone_and_matches_quantiles():
    q = np.array([[-2, -1, 0, 1, 2]] * 5, dtype=float)
    x = np.array([-3, -1, 0, 1, 3], dtype=float)
    p = calibrate.cdf(q, x)
    assert np.all(np.diff(p) > 0)
    assert p[1] == pytest.approx(0.1) and p[2] == pytest.approx(0.5) and p[3] == pytest.approx(0.9)


def test_conformal_widens_intervals_that_undercover():
    origins = pd.date_range("2021-01-01", periods=30, freq="MS")
    rows = []
    for o in origins:
        for k in range(3):
            rows.append({"model": "m", "task": "m1", "origin": o, "series_id": f"S{k}",
                         "q025": -0.2, "q100": -0.1, "q500": 0.0, "q900": 0.1, "q975": 0.2})
    f = pd.DataFrame(rows)
    feats = f[["origin", "series_id", "task"]].assign(target=np.tile([0.5, -0.5, 0.0], 30), target_available_on=f.origin)
    out = calibrate.conformalise(f, feats, window=24, min_scores=30)
    last = out[out.origin == origins[-1]].iloc[0]
    assert last.conformal_ok and last.q900_c >= 0.5 and last.q100_c <= -0.5
    first = out[out.origin == origins[0]].iloc[0]
    assert not first.conformal_ok and first.q900_c == 0.1


def test_hln_detects_a_clear_improvement():
    rng = np.random.default_rng(0)
    d = -0.5 + rng.normal(0, 0.3, 60)
    assert mt.hln_test(d, 3)["p_one_sided"] < 0.01
    assert mt.hln_test(-d, 3)["p_one_sided"] > 0.99


def test_holm_adjusts_in_order():
    adj = mt.holm([0.01, 0.04, 0.03, 0.5])
    assert adj[0] == pytest.approx(0.04) and adj[2] == pytest.approx(0.09) and adj[1] == pytest.approx(0.09) and adj[3] == 0.5


def test_recall_at_budget_and_pinball():
    y = np.array([1, 0, 0, 1, 0, 0, 0, 0, 0, 0])
    s = np.array([0.9, 0.8, 0.1, 0.2, 0, 0, 0, 0, 0, 0])
    assert mt.recall_at_budget(y, s, 0.2) == 0.5
    loss = mt.scaled_pinball(np.array([10.0]), np.array([[10.0] * 5]), np.array([2.0]))
    assert loss[0] == 0


def test_recalibration_uses_only_released_outcomes_and_keeps_order():
    origins = pd.date_range("2021-01-01", periods=30, freq="MS")
    rng = np.random.default_rng(0)
    rows, labels, feats = [], [], []
    for o in origins:
        for k in range(20):
            p = float(rng.uniform(0.05, 0.9))
            sid, tm = f"S{k}", o + pd.DateOffset(months=3)
            rows.append({"model": "m", "origin": o, "series_id": sid, "task": "sum3", "p_short_75": p, "p_short_70": p, "p_short_80": p})
            y = bool(rng.uniform() < p / 3)  # true risk is a third of the stated probability
            labels.append({"series_id": sid, "target_month": tm, "ratio": 0.5 if y else 1.0, "flag_75": y, "flag_70": y, "flag_80": y})
            # outcomes of the last 6 origins are released only far in the future
            avail = tm + pd.DateOffset(months=1) if o < origins[-6] else pd.Timestamp("2030-01-01")
            feats.append({"origin": o, "series_id": sid, "task": "sum3", "target_month": tm, "target_available_on": avail})
    out = calibrate.recalibrate(pd.DataFrame(rows), pd.DataFrame(feats), pd.DataFrame(labels), window=24, min_events=10,
                                freeze_at=origins[12])
    last = out[out.origin == origins[-1]].sort_values("p_short_75")
    assert last.p_short_75_rc.notna().all() and last.p_short_75_rc.is_monotonic_increasing
    assert last.p_short_75_rc.mean() < last.p_short_75.mean()  # overstated risk is pulled down
    assert out[out.origin < origins[12]].p_short_75_rcfix.isna().all()
    first = out[out.origin == origins[0]]
    assert first.p_short_75_rc.isna().all()  # no released outcomes yet -> no recalibrated value
