"""Monthly-average crude benchmarks from the EIA history files, which need no key."""
import pandas as pd
import requests
import xlrd

from src.utils.config import RAW

SERIES = {"brent": "RBRTEm", "wti": "RWTCm"}
URL = "https://www.eia.gov/dnav/pet/hist_xls/{}.xls"


def download(name):
    out = RAW / "oil_prices" / f"{SERIES[name]}.xls"
    r = requests.get(URL.format(SERIES[name]), headers={"User-Agent": "research-pipeline"}, timeout=60)
    r.raise_for_status()
    out.write_bytes(r.content)
    return out


def parse(path, name):
    book = xlrd.open_workbook(str(path))
    sheet = book.sheet_by_name("Data 1")
    rows = []
    for i in range(3, sheet.nrows):
        date, price = sheet.row_values(i)[:2]
        if price == "":
            continue
        y, m, *_ = xlrd.xldate_as_tuple(date, book.datemode)
        rows.append({"period": y * 100 + m, "series": name, "value": float(price), "unit": "USD/barrel", "currency": "USD",
                     "frequency": "M", "source": f"EIA {SERIES[name]}, monthly average of daily spot"})
    return pd.DataFrame(rows)


def collect():
    return pd.concat([parse(download(n), n) for n in SERIES], ignore_index=True)
