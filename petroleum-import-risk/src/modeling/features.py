"""As-of feature store: one row per (origin, series, task) built only from data public at the origin.

Tasks are months 1, 3 and 6 after the origin month ("m1", "m3", "m6") and the mean of months 1-3
("sum3", the window the shortfall rule uses). Targets are log mass minus the series level, where
the level is the mean log mass of the last `level_window` visible months. Model outputs are turned
back into tonnes with the same level, so one global model can serve series of any size.

Leakage rules (spec section 3, rule 6):
- an observation is visible at origin M only if its first release is on or before the end of M;
- external indicators are shifted by their release delay (settings modeling.external_lag_months);
- a shock event counts only from its announcement, and only while it is known to be active;
- the published uv_relative uses a centred median (future months), so it is never a feature; an
  as-of unit-value signal is rebuilt from visible months only.
"""
import logging

import numpy as np
import pandas as pd

from src.modeling import panel as pn

log = logging.getLogger(__name__)
TASKS = ["m1", "m3", "m6", "sum3"]
TASK_H = {"m1": 1, "m3": 3, "m6": 6, "sum3": 3}
SUPPLIER = ["hhi_12m", "largest_supplier_share", "russia_share"]
EXTERNAL = ["brent_log", "brent_chg3", "brent_chg12", "gpr_global", "gpr_rus", "fx_chg12", "cpi_chg12"]
SHOCK = ["shock_supply_active", "shock_supply_recent", "shock_demand_active"]
UV = ["uv_asof"]


def own_columns(n_lags):
    return ([f"lag{j}" for j in range(n_lags)] + ["last1", "last3", "seas12", "seas24", "since_last", "n_vis24", "vol12",
                                                   "moy_sin", "moy_cos", "h", "is_sum3", "is_distillate"])


def months_index(monthly):
    return pd.date_range(monthly.month.min(), monthly.month.max(), freq="MS")


def _window_mean(values, end, length=3):
    """Mean of `length` months ending at index `end`; NaN if any is missing or out of range."""
    if end - length + 1 < 0 or end >= len(values):
        return np.nan
    w = values[end - length + 1:end + 1]
    return np.nan if np.isnan(w).any() else float(w.mean())


def _baseline(values, end, years):
    """Mean of the 3-month mean at the same window in each of the previous `years` years (missing years skipped)."""
    vals = [_window_mean(values, end - 12 * k) for k in range(1, years + 1)]
    vals = [v for v in vals if not np.isnan(v)]
    return float(np.mean(vals)) if vals else np.nan


def _seasonal_scale(values):
    """In-sample mean absolute seasonal difference (lag 12) of the visible months: the MASE denominator."""
    d = np.abs(values[12:] - values[:-12])
    d = d[~np.isnan(d)]
    return float(d.mean()) if len(d) >= 6 else np.nan


def _sum3_scale(values):
    q = pd.Series(values).rolling(3, min_periods=3).mean().to_numpy()
    return _seasonal_scale(q)


def persistence_ratio(mass, avail, months, origin, years):
    """As-of persistence score: the last complete visible 3-month ratio Q/B at `origin` (exploratory H4 benchmark, R1).

    Q is the mean mass of the latest three consecutive months that were all public by the end of the origin month;
    B is the baseline of that window (`_baseline`, same rule as `baseline_asof`) built from visible months only. Final or
    later-released values are never used. NaN if no such window exists or B is not positive. Lower ratio = higher risk.
    """
    oi = months.get_loc(origin)
    end_of = np.datetime64(pn.origin_end(origin))
    vm = np.where(~np.isnan(mass[:oi + 1]) & (avail[:oi + 1] <= end_of), mass[:oi + 1], np.nan)
    for e in range(oi, 1, -1):
        q = _window_mean(vm, e)
        if not np.isnan(q):
            b = _baseline(vm, e, years)
            return q / b if b > 0 else np.nan
    return np.nan


def _external_frame(settings, months):
    wide = pn.external_panel(settings)
    glob = wide[wide.key == "GLOBAL"].set_index("month").reindex(months)
    brent = np.log(glob["brent_usd_bbl"])
    g = pd.DataFrame({"brent_log": brent, "brent_chg3": brent - brent.shift(3), "brent_chg12": brent - brent.shift(12),
                      "gpr_global": glob["GPR"], "gpr_rus": glob["GPRC_RUS"]}, index=months)
    country = {}
    for key, part in wide[wide.key != "GLOBAL"].groupby("key"):
        p = part.set_index("month").reindex(months)
        country[key] = pd.DataFrame({"fx_chg12": np.log(p["fx_lcu_per_usd_avg"]).diff(12),
                                     "cpi_chg12": np.log(p["cpi_index"]).diff(12)}, index=months)
    return g, country


def _brent_by_month(settings, months):
    """Monthly Brent as recorded for the month itself (used only to deflate visible unit values)."""
    e = pd.read_parquet(pn.RESEARCH / "external_indicators_monthly.parquet")
    b = e[e.indicator == "brent_usd_bbl"].copy()
    b["month"] = pd.to_datetime(b.month).astype("datetime64[ns]")
    return b.set_index("month").value.reindex(months)


def _shock_counts(events, series_id, origin):
    if events is None or events.empty:
        return 0, 0, 0
    e = events[events.series_id == series_id]
    end_of = pn.origin_end(origin)
    public = e[e.public_on <= end_of]
    active = public[(public.start_date <= end_of) & (public.end_date.isna() | (public.end_date >= origin))]
    supply = active.role == "supply_shortfall"
    recent = public[(public.role == "supply_shortfall") & (public.public_on > origin - pd.DateOffset(months=2))]
    return int(supply.sum()), int(len(recent)), int((active.role == "demand_shock").sum())


def build(settings, series=None, monthly=None, last_origin=None):
    """Return the full example table. Rows whose target is not yet observed keep target NaN (live forecasts)."""
    m = settings["modeling"]
    series = series if series is not None else pn.series_table(settings)
    monthly = monthly if monthly is not None else pn.monthly_panel(settings, series)
    months = months_index(monthly)
    first = pd.Timestamp(str(m["first_origin"]) + "01")
    last = pd.Timestamp(last_origin) if last_origin is not None else months[-1]
    origins = pd.date_range(first, last, freq="MS")
    glob, country = _external_frame(settings, pd.date_range(months[0], max(last, months[-1]), freq="MS"))
    brent = _brent_by_month(settings, months)
    events = pn.event_table(settings, monthly)
    events["series_id"] = events.iso3 + ":" + events.product_group
    n_lags, lw, min_obs, years = m["n_lags"], m["level_window"], m["min_level_obs"], m["shortfall"]["baseline_years"]
    rows = []
    for s in series.itertuples():
        g = monthly[monthly.series_id == s.series_id].set_index("month").reindex(months)
        mass = g.import_mass_t.to_numpy(dtype=float)
        logm = np.log1p(mass)
        avail = g.available_on.to_numpy(dtype="datetime64[ns]")
        uv_defl = np.log(_unit_values(s.iso3, s.product_group, months)) - np.log(brent.to_numpy())
        sup = g[SUPPLIER].to_numpy(dtype=float)
        ext_c = country.get(s.iso3)
        for o in origins:
            oi = months.get_loc(o) if o in months else len(months) - 1 + (o.to_period("M") - months[-1].to_period("M")).n
            end_of = np.datetime64(pn.origin_end(o))
            visible = ~np.isnan(mass[:min(oi + 1, len(months))]) & (avail[:min(oi + 1, len(months))] <= end_of)
            v = np.where(visible, logm[:len(visible)], np.nan)
            vis_idx = np.flatnonzero(visible)
            if len(vis_idx) < min_obs:
                continue
            tail = vis_idx[-lw:]
            if len(tail) < min_obs or oi - tail[-1] > 36:
                continue
            level = float(v[tail].mean())
            vm = np.where(visible, mass[:len(visible)], np.nan)
            base = {"origin": o, "series_id": s.series_id, "iso3": s.iso3, "product_group": s.product_group,
                    "evaluation": s.evaluation, "level": level, "since_last": oi - vis_idx[-1],
                    "n_vis24": int(visible[max(0, oi - 23):].sum()), "vol12": float(np.nanstd(v[tail])),
                    "last1": v[vis_idx[-1]] - level, "last3": float(v[vis_idx[-3:]].mean()) - level,
                    "scale_month": _seasonal_scale(vm), "scale_sum3": _sum3_scale(vm),
                    "is_distillate": int(s.product_group != "gasoline")}
            for j in range(n_lags):
                k = oi - j
                base[f"lag{j}"] = v[k] - level if 0 <= k < len(v) else np.nan
            last_sup = sup[vis_idx[-1]]
            base.update(dict(zip(SUPPLIER, last_sup)))
            uv_vis = np.where(visible, uv_defl[:len(visible)], np.nan)
            recent = uv_vis[vis_idx[-12:]]
            recent = recent[~np.isnan(recent)]
            base["uv_asof"] = float(uv_vis[vis_idx[-1]] - np.median(recent)) if len(recent) >= 6 and not np.isnan(uv_vis[vis_idx[-1]]) else np.nan
            for col in ["brent_log", "brent_chg3", "brent_chg12", "gpr_global", "gpr_rus"]:
                base[col] = glob.at[o, col] if o in glob.index else np.nan
            for col in ["fx_chg12", "cpi_chg12"]:
                base[col] = ext_c.at[o, col] if ext_c is not None and o in ext_c.index else np.nan
            base["shock_supply_active"], base["shock_supply_recent"], base["shock_demand_active"] = _shock_counts(events, s.series_id, o)
            for task in TASKS:
                h = TASK_H[task]
                ti = oi + h
                target_month = o + pd.DateOffset(months=h)
                r = dict(base, task=task, h=h, is_sum3=int(task == "sum3"), target_month=target_month,
                         moy_sin=np.sin(2 * np.pi * target_month.month / 12), moy_cos=np.cos(2 * np.pi * target_month.month / 12))
                if task == "sum3":
                    r["seas12"] = np.log1p(_window_mean(vm, ti - 12)) - level
                    r["seas24"] = np.log1p(_window_mean(vm, ti - 24)) - level
                    actual = _window_mean(mass, ti)
                    ok = ti < len(months) and not np.isnan(actual)
                    r["target_available_on"] = pd.Timestamp(avail[ti - 2:ti + 1].max()) if ok else pd.NaT
                    r["baseline_asof"] = _baseline(vm, ti, years)
                    r["baseline_final"] = _baseline(mass, ti, years) if ti < len(months) else np.nan
                else:
                    r["seas12"] = v[ti - 12] - level if 0 <= ti - 12 < len(v) else np.nan
                    r["seas24"] = v[ti - 24] - level if 0 <= ti - 24 < len(v) else np.nan
                    actual = mass[ti] if ti < len(months) else np.nan
                    r["target_available_on"] = pd.Timestamp(avail[ti]) if not np.isnan(actual) else pd.NaT
                r["actual_t"] = actual
                r["target"] = np.log1p(actual) - level if not np.isnan(actual) else np.nan
                rows.append(r)
    out = pd.DataFrame(rows)
    log.info("feature store: %d rows, %d origins, %d series", len(out), out.origin.nunique(), out.series_id.nunique())
    return out


_UV_CACHE = {}


def _unit_values(iso3, product, months):
    """Monthly customs unit value (USD per tonne) for one series, NaN where mass is missing."""
    if "frame" not in _UV_CACHE:
        cols = ["iso3", "product_group", "month", "unit_value_usd_t", "import_mass_t"]
        f = pd.read_parquet(pn.RESEARCH / "petroleum_imports_monthly.parquet", columns=cols)
        f["month"] = pd.to_datetime(f.month).astype("datetime64[ns]")
        _UV_CACHE["frame"] = f
    f = _UV_CACHE["frame"]
    s = f[(f.iso3 == iso3) & (f.product_group == product)].set_index("month")
    return s.unit_value_usd_t.where(s.import_mass_t.notna() & (s.unit_value_usd_t > 0)).reindex(months).to_numpy(dtype=float)


def feature_columns(settings, groups=("own", "supplier", "external", "shock", "uv")):
    cols = []
    if "own" in groups:
        cols += own_columns(settings["modeling"]["n_lags"])
    if "supplier" in groups:
        cols += SUPPLIER
    if "external" in groups:
        cols += EXTERNAL
    if "shock" in groups:
        cols += SHOCK
    if "uv" in groups:
        cols += UV
    return cols


def store(settings, last_origin=None):
    pn.MODELING.mkdir(parents=True, exist_ok=True)
    table = build(settings, last_origin=last_origin)
    table.to_parquet(pn.MODELING / "features.parquet", index=False)
    return table


def load():
    return pd.read_parquet(pn.MODELING / "features.parquet")
