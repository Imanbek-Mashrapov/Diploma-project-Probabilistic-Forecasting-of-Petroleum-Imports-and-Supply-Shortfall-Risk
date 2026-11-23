"""Project paths and configuration loading."""
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
ANALYTICAL = DATA / "analytical"
REPORTS = ROOT / "reports"


def load_settings():
    load_dotenv(ROOT / ".env")
    with open(ROOT / "config" / "settings.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_countries():
    return pd.read_csv(ROOT / "config" / "countries.csv", dtype={"comtrade_code": int})


def load_hs_codes():
    return pd.read_csv(ROOT / "config" / "hs_codes.csv", dtype={"hs_code": str})


def months_between(start, end):
    """YYYYMM integers from start to end inclusive."""
    out, y, m = [], start // 100, start % 100
    while y * 100 + m <= end:
        out.append(y * 100 + m)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out
