"""Row-level cleaning of Comtrade records. Original fields are kept untouched;
everything derived goes into new columns, and each mass value records its source.
"""
import json

import numpy as np
import pandas as pd

from src.utils.config import PROCESSED, RAW, load_hs_codes

KEY = ["reporterCode", "flowCode", "cmdCode", "partnerCode", "partner2Code", "motCode", "customsCode", "period"]
KG_ABBR = {"kg"}
VOLUME_ABBR = "1000 l"
# Physical range in kg/L at customs conditions, wide enough for blends and winter grades
DENSITY_BOUNDS = {"gasoline": (0.68, 0.80), "lpg": (0.48, 0.62)}
DEFAULT_DENSITY = (0.60, 1.05)


def load_snapshot(snapshot, dataset):
    """Flatten every stored response of a dataset, with provenance columns."""
    root = RAW / "un_comtrade" / snapshot
    frames = []
    for line in (root / "manifest.jsonl").open(encoding="utf-8"):
        rec = json.loads(line)
        if rec.get("dataset") != dataset or rec["status"] != "ok":
            continue
        payload = json.loads((root / rec["file"]).read_text(encoding="utf-8"))
        frame = pd.DataFrame(payload["data"])
        frame["retrieved_at"] = rec["retrieved_at"]
        frame["source_task"] = rec["task"]
        frame["api_mode"] = rec["mode"]
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True)
    df["period"] = df["period"].astype(int)
    df["cmdCode"] = df["cmdCode"].astype(str)
    return df


def drop_exact_duplicates(df):
    """Overlapping tasks may return the same record; keep the latest retrieval and report the count."""
    before = len(df)
    df = df.sort_values("retrieved_at").drop_duplicates(KEY, keep="last")
    return df, before - len(df)


def load_deduped_bilateral():
    raw = pd.read_parquet(PROCESSED / "raw_bilateral_records.parquet")
    return drop_exact_duplicates(raw)[0]


def resolve_mass(df):
    """Mass in kg from netWgt, else qty or altQty only when their unit is literally kg.

    Litres and other units are never converted into mass_kg. A zero mass next to a
    positive value is missing, not zero. A kg quantity standing in for netWgt must
    also be physically possible against any volume on the same row: Russia, 271012,
    Oct 2017 has qty 107,037,530 kg and 75,576 thousand litres, i.e. 1.42 kg/L.
    Such rows are rejected and keep their volume for the labelled estimate.
    """
    out = df.copy()
    net = pd.to_numeric(out["netWgt"], errors="coerce")
    qty = pd.to_numeric(out["qty"], errors="coerce")
    alt = pd.to_numeric(out["altQty"], errors="coerce")
    value = pd.to_numeric(out["primaryValue"], errors="coerce")
    qty_unit = out["qtyUnitAbbr"].astype(str).str.lower()
    alt_unit = out["altQtyUnitAbbr"].astype(str).str.lower()
    qty_is_kg, alt_is_kg = qty_unit.isin(KG_ABBR), alt_unit.isin(KG_ABBR)
    conditions = [net > 0, qty_is_kg & (qty > 0), alt_is_kg & (alt > 0)]
    out["mass_kg"] = np.select(conditions, [net, qty, alt], default=np.nan)
    out["mass_source"] = np.select(conditions, ["netWgt", "qty_kg", "altQty_kg"], default="none")
    out["volume_kl"] = alt.where((alt_unit == VOLUME_ABBR) & (alt > 0), qty.where((qty_unit == VOLUME_ABBR) & (qty > 0)))
    out["implied_density"] = out["mass_kg"] / (out["volume_kl"] * 1000)
    low = out["product_group"].map(lambda g: DENSITY_BOUNDS.get(g, DEFAULT_DENSITY)[0]) if "product_group" in out else DEFAULT_DENSITY[0]
    high = out["product_group"].map(lambda g: DENSITY_BOUNDS.get(g, DEFAULT_DENSITY)[1]) if "product_group" in out else DEFAULT_DENSITY[1]
    impossible = out["implied_density"].notna() & ((out["implied_density"] < low) | (out["implied_density"] > high))
    rejected = impossible & out["mass_source"].isin(["qty_kg", "altQty_kg"])
    out.loc[rejected, "mass_kg"] = np.nan
    out.loc[rejected, "mass_source"] = "qty_rejected_density"
    no_trade = (net.fillna(0) == 0) & (qty.fillna(0) == 0) & (value.fillna(0) == 0)
    out.loc[no_trade, "mass_source"] = "no_trade_row"
    out["mass_t"] = out["mass_kg"] / 1000
    estimated = out["isNetWgtEstimated"].fillna(False).astype(bool).where(out["mass_source"] == "netWgt",
                                                                         out["isQtyEstimated"].fillna(False).astype(bool))
    out["mass_estimated"] = estimated & out["mass_kg"].notna()
    out["value_usd"] = value
    return out


def add_product_group(df):
    groups = load_hs_codes().set_index("hs_code").product_group
    out = df.copy()
    out["product_group"] = out["cmdCode"].map(groups)
    return out


def volume_estimate_t(df):
    """Mass estimate for rejected rows: their volume times the median density the same
    reporter and HS code show on rows with a real net weight. Never merged into mass_t."""
    valid = df[(df.mass_source == "netWgt") & df.implied_density.notna()]
    valid = valid[valid.apply(lambda r: DENSITY_BOUNDS.get(r.product_group, DEFAULT_DENSITY)[0] <= r.implied_density <= DENSITY_BOUNDS.get(r.product_group, DEFAULT_DENSITY)[1], axis=1)]
    density = valid.groupby(["reporterCode", "cmdCode"]).implied_density.median().rename("empirical_density")
    out = df.join(density, on=["reporterCode", "cmdCode"])
    rejected = out.mass_source == "qty_rejected_density"
    return (out.volume_kl * out.empirical_density).where(rejected), out.empirical_density.where(rejected)


def relative_unit_value(uv, brent):
    """Unit value relative to its centred 13-month median, after deflating by Brent so
    that real oil-price moves such as 2020 are not mistaken for recording errors."""
    deflated = uv / brent
    return deflated / deflated.rolling(13, center=True, min_periods=6).median()


def robust_z(series):
    """Modified z-score on logs, computed per series."""
    logged = np.log(series.where(series > 0))
    med = logged.median()
    mad = (logged - med).abs().median()
    return 0.6745 * (logged - med) / mad if mad and mad > 0 else pd.Series(np.nan, index=series.index)
