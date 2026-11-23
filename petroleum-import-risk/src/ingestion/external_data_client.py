"""External indicators. Each source keeps its raw file and its original frequency.

Annual World Bank values stay annual: they are never spread over months here.
"""
import io
import json
import logging
from datetime import datetime, timezone

import pandas as pd
import requests
import xlrd

from src.ingestion import oil_price_client
from src.utils.config import PROCESSED, RAW, load_countries

log = logging.getLogger(__name__)
UA = {"User-Agent": "research-pipeline"}
GPR_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"
BIS_URL = "https://stats.bis.org/api/v1/data/WS_XRU/M..../?format=csv&startPeriod=2010-01"
IMF_URL = "https://api.imf.org/external/sdmx/2.1/data/IMF.STA,CPI/{}.CPI._T.IX.M?startPeriod=2010-01"
WB_URL = "https://api.worldbank.org/v2/country/{}/indicator/{}?format=json&per_page=20000&date=2010:2026"
WB_INDICATORS = {
    "NY.GDP.MKTP.CD": "gdp_current_usd", "NY.GDP.PCAP.CD": "gdp_per_capita_usd", "SP.POP.TOTL": "population",
    "FP.CPI.TOTL.ZG": "cpi_inflation_pct", "NV.IND.TOTL.ZS": "industry_share_gdp", "PA.NUS.FCRF": "fx_official_lcu_per_usd",
    "IS.VEH.NVEH.P3": "vehicles_per_1000",
}
# Balance rows extracted by Russian label; sheet numbers are from the 2024 edition
BALANCE_SHEETS = {"8": "diesel", "9": "gasoline", "10": "fuel_oil"}
BALANCE_ROWS = {"Добыча": "production", "импорту": "imports", "экспорт": "exports", "Остатки на начало": "stock_start",
                "Остатки на конец": "stock_end", "Потреблено внутри": "domestic_use"}


def _fetch(url, out, headers=UA, timeout=180):
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    out.write_bytes(r.content)
    return out


def collect_gpr():
    path = _fetch(GPR_URL, RAW / "gpr" / "data_gpr_export.xls")
    book = xlrd.open_workbook(str(path))
    sheet = book.sheet_by_index(0)
    header = sheet.row_values(0)
    keep = {h: i for i, h in enumerate(header) if h in ("GPR", "GPRT", "GPRA") or str(h).startswith("GPRC_")}
    rows = []
    for i in range(1, sheet.nrows):
        serial = sheet.cell_value(i, 0)
        if serial < 40179:  # before Jan 2010; the file starts in 1900, where Excel serials are ambiguous
            continue
        y, m, *_ = xlrd.xldate_as_tuple(serial, book.datemode)
        for name, col in keep.items():
            v = sheet.cell_value(i, col)
            if v != "":
                rows.append({"period": y * 100 + m, "series": name, "value": float(v), "unit": "index", "frequency": "M",
                             "source": "Caldara-Iacoviello GPR"})
    return pd.DataFrame(rows)


def collect_fx():
    path = _fetch(BIS_URL, RAW / "fx" / "bis_ws_xru_monthly.csv")
    bis = pd.read_csv(path, dtype=str)
    bis = bis[bis.COLLECTION == "A"]  # A = period average, E = end of period
    bis = bis.assign(period=bis.TIME_PERIOD.str.replace("-", "").astype(int), value=pd.to_numeric(bis.OBS_VALUE, errors="coerce"))
    return bis[["period", "REF_AREA", "CURRENCY", "value", "OBS_STATUS"]].rename(columns={"REF_AREA": "iso2", "CURRENCY": "currency"}).dropna(subset=["value"])


def collect_cpi(iso3_list):
    """IMF CPI, all items, index. One request per country so a gap stays visible."""
    rows, misses = [], []
    for iso3 in iso3_list:
        out = RAW / "macroeconomic" / f"imf_cpi_{iso3}.csv"
        r = requests.get(IMF_URL.format(iso3), headers={"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"}, timeout=120)
        if r.status_code != 200 or len(r.content) < 50:
            misses.append(iso3)
            continue
        out.write_bytes(r.content)
        d = pd.read_csv(io.BytesIO(r.content), usecols=["COUNTRY", "TIME_PERIOD", "OBS_VALUE"], dtype=str).dropna(subset=["TIME_PERIOD"])
        if d.empty:
            misses.append(iso3)
            continue
        d["period"] = d.TIME_PERIOD.str.replace("-M", "").str.replace("-", "").astype(int)
        d["value"] = pd.to_numeric(d.OBS_VALUE, errors="coerce")
        rows.append(d[["COUNTRY", "period", "value"]].rename(columns={"COUNTRY": "iso3"}))
    log.info("IMF CPI: %d countries, none for %s", len(rows), misses)
    return pd.concat(rows, ignore_index=True).dropna(subset=["value"])


def collect_world_bank(iso3_list):
    rows = []
    for code, name in WB_INDICATORS.items():
        path = RAW / "macroeconomic" / f"wb_{code}.json"
        _fetch(WB_URL.format(";".join(iso3_list), code), path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        for rec in payload[1] or []:
            if rec["value"] is not None:
                rows.append({"iso3": rec["countryiso3code"], "year": int(rec["date"]), "indicator": name, "value": float(rec["value"]),
                             "frequency": "A", "source": f"World Bank WDI {code}"})
    return pd.DataFrame(rows)


def collect_energy_balance():
    """Tables 5-7 of the Kyrgyz Fuel and Energy Balance (2024 edition), thousand tonnes."""
    import openpyxl
    # Manually downloaded from the NSC website and kept in Git: there is no stable download URL
    path = RAW / "energy_balance" / "teb2024.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing. Download the 2024 Fuel and Energy Balance "
                                "from the National Statistical Committee (stat.gov.kg) and save it there.")
    book = openpyxl.load_workbook(path, data_only=True, read_only=True)
    rows = []
    for sheet, fuel in BALANCE_SHEETS.items():
        table = [[c for c in r if c is not None] for r in book[sheet].iter_rows(values_only=True)]
        years = next(r for r in table if r and r[0] == 1999)
        for r in table:
            if len(r) != len(years) + 1 or not isinstance(r[0], str):
                continue
            item = next((v for k, v in BALANCE_ROWS.items() if k.lower() in r[0].lower()), None)
            if item:
                rows += [{"fuel": fuel, "year": int(y), "item": item, "label": r[0].strip(), "kt": float(v)}
                         for y, v in zip(years, r[1:]) if isinstance(v, (int, float))]
    return pd.DataFrame(rows)


def collect_all(settings):
    iso3 = [c for c in load_countries().iso3 if c != "LIE"]
    results = {}
    steps = {
        "ext_oil_prices": oil_price_client.collect,
        "ext_gpr": collect_gpr,
        "ext_fx_bis": collect_fx,
        "ext_cpi_imf": lambda: collect_cpi(iso3),
        "ext_world_bank_annual": lambda: collect_world_bank(iso3),
        "ext_energy_balance": collect_energy_balance,
    }
    for name, step in steps.items():
        try:
            df = step()
            df.to_parquet(PROCESSED / f"{name}.parquet", index=False)
            results[name] = {"rows": len(df), "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "status": "ok"}
            log.info("%s: %d rows", name, len(df))
        except Exception as e:  # one source failing must be reported, not fatal to the others
            results[name] = {"status": "failed", "error": f"{type(e).__name__}: {str(e)[:200]}"}
            log.error("%s FAILED: %s", name, results[name]["error"])
    (PROCESSED / "external_manifest.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
