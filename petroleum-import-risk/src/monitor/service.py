"""Data access for the Fuel Import Risk Monitor. Read-only; every number comes from stored model output.

Inputs: data/modeling/forecasts.parquet (written by `run.py evaluate`), data/research/*.parquet,
config/shock_events.csv and reports/phase3/tables/accuracy.csv.
"""
from functools import lru_cache

import numpy as np
import pandas as pd

from src.modeling import panel as pn
from src.research import events as ev
from src.utils.config import REPORTS, load_settings

PRODUCTS = {"gasoline": "gasoline", "distillates": "middle_incl_blends"}
BILATERAL_GROUPS = {"gasoline": ["gasoline"], "middle_incl_blends": ["middle_heavy", "biodiesel_blend"]}
TASK_LABEL = {"m1": "month +1", "m3": "month +3", "m6": "month +6", "sum3": "next 3 months (mean)"}


class NotFound(KeyError):
    pass


@lru_cache(maxsize=1)
def settings():
    return load_settings()


@lru_cache(maxsize=1)
def forecasts():
    f = pd.read_parquet(pn.MODELING / "forecasts.parquet")
    return f[f.model == settings()["monitor"]["model"]]


@lru_cache(maxsize=1)
def series():
    return pn.series_table(settings())


@lru_cache(maxsize=1)
def monthly():
    return pn.monthly_panel(settings(), series())


def product_group(product):
    if product not in PRODUCTS:
        raise NotFound(f"unknown product '{product}', use one of {sorted(PRODUCTS)}")
    return PRODUCTS[product]


def latest_origin():
    return forecasts().origin.max()


def _origin(origin):
    if origin in (None, "latest"):
        return latest_origin()
    o = pd.Timestamp(origin).to_period("M").to_timestamp()
    if o not in set(forecasts().origin):
        raise NotFound(f"no forecasts for origin {o:%Y-%m}")
    return o


def band(p):
    b = settings()["monitor"]["risk_bands"]
    if p is None or np.isnan(p):
        return "unknown"
    return "red" if p >= b["red"] else "amber" if p >= b["amber"] else "green"


def series_list():
    s = series()
    return [{"iso3": r.iso3, "country": r.country, "product": next(k for k, v in PRODUCTS.items() if v == r.product_group),
             "tier": r.quality_tier, "evaluated": bool(r.evaluation), "importer_type": r.importer_type_provisional}
            for r in s.itertuples()]


def _risk(row, t=75):
    """Recalibrated probability when one exists (rolling as-of Platt map), else the raw forecast probability."""
    rc = getattr(row, f"p_short_{t}_rc", np.nan)
    return _num(rc) if _num(rc) is not None else _num(getattr(row, f"p_short_{t}"))


def risk_table(origin=None):
    o = _origin(origin)
    f = forecasts()
    s = f[(f.origin == o) & (f.task == "sum3")]
    feats = _origin_features(o)
    out = []
    for r in s.itertuples():
        x = feats.get(r.series_id, {})
        out.append({"iso3": r.series_id.split(":")[0], "product": next(k for k, v in PRODUCTS.items() if r.series_id.endswith(v)),
                    "p_shortfall": _risk(r), "status": band(_risk(r) if _risk(r) is not None else np.nan),
                    "p_shortfall_raw": _num(r.p_short_75), "recalibrated": _num(getattr(r, "p_short_75_rc", np.nan)) is not None,
                    "p_shortfall_70": _risk(r, 70), "p_shortfall_80": _risk(r, 80),
                    "median_t": _num(r.q500_t), "low80_t": _num(r.q100_t), "high80_t": _num(r.q900_t),
                    "baseline_t": _num(x.get("baseline_asof")), "hhi_12m": _num(x.get("hhi_12m")),
                    "largest_supplier_share": _num(x.get("largest_supplier_share")), "months_since_data": _int(x.get("since_last")),
                    "conformal": bool(r.conformal_ok)})
    out.sort(key=lambda d: -(d["p_shortfall"] if d["p_shortfall"] is not None else -1))
    return {"origin": f"{o:%Y-%m}", "model": settings()["monitor"]["model"], "rows": out}


@lru_cache(maxsize=64)
def _origin_features(o):
    from src.modeling import features as ft
    x = ft.load()
    x = x[(x.origin == o) & (x.task == "sum3")]
    return {r.series_id: r._asdict() for r in x.itertuples()}


def forecast(iso3, product, origin=None):
    pg = product_group(product)
    sid = f"{iso3.upper()}:{pg}"
    if sid not in set(series().series_id):
        raise NotFound(f"series {sid} is not in the modelling panel")
    o = _origin(origin)
    f = forecasts()
    rows = f[(f.series_id == sid) & (f.origin == o)]
    end = pn.origin_end(o)
    m = monthly()
    h = m[(m.series_id == sid)].sort_values("month")
    h = h[h.month >= o - pd.DateOffset(months=settings()["monitor"]["history_months"])]
    history = [{"month": f"{r.month:%Y-%m}", "mass_t": _num(r.import_mass_t),
                "public_at_origin": bool(pd.notna(r.available_on) and r.available_on <= end)} for r in h.itertuples()]
    fc = [{"task": r.task, "label": TASK_LABEL[r.task], "target_month": f"{r.target_month:%Y-%m}",
           "q025_t": _num(r.q025_t), "q100_t": _num(r.q100_t), "q500_t": _num(r.q500_t), "q900_t": _num(r.q900_t), "q975_t": _num(r.q975_t),
           "p_shortfall": _risk(r) if r.task == "sum3" else None} for r in rows.sort_values("target_month").itertuples()]
    return {"series_id": sid, "origin": f"{o:%Y-%m}", "model": settings()["monitor"]["model"], "history": history, "forecasts": fc}


def suppliers(iso3, product, months=12):
    pg = product_group(product)
    b = _bilateral()
    b = b[(b.iso3 == iso3.upper()) & b.product_group.isin(BILATERAL_GROUPS[pg])]
    if b.empty:
        raise NotFound(f"no supplier data for {iso3}/{product}")
    last = b.month.max()
    b = b[b.month > last - pd.DateOffset(months=months)]
    g = b.groupby(["partner_iso", "partner_name"]).import_mass_t.sum().sort_values(ascending=False)
    total = g.sum()
    return {"iso3": iso3.upper(), "product": product, "window": f"{b.month.min():%Y-%m} to {last:%Y-%m}",
            "suppliers": [{"iso3": k[0], "name": k[1], "mass_t": float(v), "share": float(v / total)} for k, v in g.items() if v > 0]}


@lru_cache(maxsize=1)
def _bilateral():
    b = pd.read_parquet(pn.RESEARCH / "petroleum_imports_bilateral.parquet",
                        columns=["iso3", "product_group", "partner_iso", "partner_name", "import_mass_t", "month"])
    b["month"] = pd.to_datetime(b.month)
    return b


def events(iso3):
    e = ev.load_events()
    iso3 = iso3.upper()
    hit = e[e.affected_iso3.fillna("").str.split(";").apply(lambda c: iso3 in c or "ALL" in c or "EXPOSED" in c)]
    hit = hit[~hit.exempt_iso3.fillna("").str.split(";").apply(lambda c: iso3 in c)]
    return [{"event_id": r.event_id, "title": r.title, "role": r.role, "type": r.event_type,
             "start": _date(r.start_date), "end": _date(r.end_date), "announced": _date(r.announced_date),
             "scope": r.affected_iso3, "confidence": r.confidence, "source": r.source1_url}
            for r in hit.sort_values("start_date").itertuples()]


def performance():
    p = REPORTS / "phase3" / "tables" / "accuracy.csv"
    if not p.exists():
        raise NotFound("run `python run.py evaluate` first")
    t = pd.read_csv(p)
    return t.replace({np.nan: None}).to_dict(orient="records")


def _num(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else float(x)


def _int(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else int(x)


def _date(x):
    return None if pd.isna(x) else f"{x:%Y-%m-%d}"
