"""Tests for the exploratory additions (R1-R3): the as-of persistence score, the paired bootstrap, episodes and the vintage revisions."""
import numpy as np
import pandas as pd
import pytest

from src.modeling import features as ft, h4_extra
from src.research import vintage as vg


def _series(n=60, value=100.0, release_lag_months=1):
    months = pd.date_range("2019-01-01", periods=n, freq="MS")
    mass = np.full(n, value)
    avail = (months + pd.offsets.MonthEnd(0) + pd.Timedelta(days=30 * release_lag_months)).to_numpy(dtype="datetime64[ns]")
    return months, mass, avail


def test_persistence_ratio_flat_series_is_one():
    months, mass, avail = _series()
    assert ft.persistence_ratio(mass, avail, months, months[-1], 3) == pytest.approx(1.0)


def test_persistence_ratio_uses_last_visible_window_not_unreleased_months():
    months, mass, avail = _series()
    mass = mass.copy()
    mass[-3:] = 10.0  # a collapse in the last three months ...
    origin = months[-1]
    # ... released only after the origin: invisible at the origin
    avail = avail.copy()
    avail[-3:] = np.datetime64(origin + pd.DateOffset(months=3))
    r = ft.persistence_ratio(mass, avail, months, origin, 3)
    assert r == pytest.approx(1.0)  # last visible window (earlier months) is still flat
    # once released by the end of the origin month the collapse is the score
    avail[-3:] = np.datetime64(pn_end(origin))
    assert ft.persistence_ratio(mass, avail, months, origin, 3) == pytest.approx(0.1)


def pn_end(month):
    return pd.Timestamp(month) + pd.offsets.MonthBegin(1) - pd.Timedelta(seconds=1)


def test_persistence_ratio_ignores_later_revisions_of_future_values():
    months, mass, avail = _series()
    origin = months[40]
    base = ft.persistence_ratio(mass, avail, months, origin, 3)
    changed = mass.copy()
    changed[41:] = 1e6  # values after the origin must not matter
    assert ft.persistence_ratio(changed, avail, months, origin, 3) == base


def test_persistence_ratio_nan_without_complete_window_and_gap_skipped():
    months, mass, avail = _series(n=10)
    assert np.isnan(ft.persistence_ratio(mass, avail, months, months[-1], 3))  # no baseline yet
    months, mass, avail = _series()
    mass = mass.copy()
    mass[-1] = np.nan  # absent month is not filled: the window ends one month earlier
    mass[-2] = 50.0
    r = ft.persistence_ratio(mass, avail, months, months[-1], 3)
    assert r == pytest.approx(np.mean([100.0, 100.0, 50.0]) / 100.0)


def test_episodes_counts_runs_of_consecutive_origins():
    f = pd.DataFrame({"series_id": ["A"] * 5 + ["B"] * 2,
                      "origin": pd.to_datetime(["2023-01-01", "2023-02-01", "2023-03-01", "2023-06-01", "2023-07-01", "2023-01-01", "2023-05-01"]),
                      "flag_75": True})
    n_series, n_ep = h4_extra.episodes(f)
    assert (n_series, n_ep) == (2, 4)  # A: Jan-Mar and Jun-Jul; B: two single months


def test_paired_bootstrap_perfect_vs_random_score_favours_perfect():
    rng = np.random.default_rng(1)
    n = 240
    y = rng.random(n) < 0.2
    good, bad = y + rng.normal(0, 0.1, n), rng.random(n)
    groups = [np.arange(i, i + 10) for i in range(0, n, 10)]
    ci, p, k = h4_extra.paired_bootstrap(y, good, bad, groups, n_boot=300)
    assert ci[0] > 0 and p < 0.05 and k > 0


def _vt(rows):
    return pd.DataFrame(rows, columns=["series_id", "month", "mass_t", "value_usd", "n_rows"]).assign(month=lambda f: pd.to_datetime(f.month))


def test_compare_measures_added_dropped_and_revisions():
    old = _vt([("KGZ:gasoline", "2025-01-01", 100.0, 1000.0, 3), ("KGZ:gasoline", "2025-02-01", 200.0, 2000.0, 3),
               ("KGZ:gasoline", "2025-03-01", 300.0, 3000.0, 3), ("KGZ:gasoline", "2025-04-01", np.nan, 50.0, 1)])
    new = _vt([("KGZ:gasoline", "2025-01-01", 100.0, 1000.0, 3), ("KGZ:gasoline", "2025-02-01", 220.0, 2000.0, 3),
               ("KGZ:gasoline", "2025-04-01", 80.0, 900.0, 3), ("KGZ:gasoline", "2025-05-01", 90.0, 950.0, 3)])
    c = vg.compare(old, new, {"KGZ:gasoline"}).set_index("month")
    st = c.status.to_dict()
    assert st[pd.Timestamp("2025-01-01")] == "common" and st[pd.Timestamp("2025-03-01")] == "dropped"
    assert st[pd.Timestamp("2025-04-01")] == "added"  # old had value but no mass: absent, not zero
    assert st[pd.Timestamp("2025-05-01")] == "added"
    assert c.loc["2025-02-01", "rel_mass_rev"] == pytest.approx(0.10)
    assert not c.loc["2025-01-01", "mass_changed"] and c.loc["2025-02-01", "mass_changed"]
    assert not c.loc["2025-02-01", "value_changed"]
    s = vg.summarise(c.reset_index(), "x")
    assert (s["months_added"], s["months_dropped"], s["months_common"], s["mass_changed"]) == (2, 1, 2, 1)
    assert s["mass_abs_rev_median_changed"] == pytest.approx(0.10)


def test_compare_never_fills_missing_months():
    old = _vt([("A:gasoline", "2025-01-01", 10.0, 1.0, 1)])
    new = _vt([("A:gasoline", "2025-03-01", 10.0, 1.0, 1)])
    c = vg.compare(old, new, {"A:gasoline"})
    assert sorted(c.month.dt.month) == [1, 3]  # no February row invented
