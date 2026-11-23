"""Kyrgyz validation against official sources, and import dependency from the energy balance."""
import hashlib
import json
import logging
import re

import openpyxl
import pandas as pd
import requests

from src.preprocessing import cleaning
from src.utils.config import PROCESSED, RAW

log = logging.getLogger(__name__)
NSC_TABLE = RAW / "official_kg" / "nsc_dynamic_1233.xlsx"
NSC_URL = "https://stat.gov.kg/ru/statistics/download/dynamic/1233/"
NSC_PAGE = "https://stat.gov.kg/ru/statistics/vneshneekonomicheskaya-deyatelnost/"
MONTHS_RU = {"Январь": 1, "Февраль": 2, "Март": 3, "Апрель": 4, "Май": 5, "Июнь": 6, "Июль": 7, "Август": 8, "Сентябрь": 9, "Октябрь": 10, "Ноябрь": 11, "Декабрь": 12}
NSC_ROWS = {"Бензин автомобильный": "gasoline", "Топливо дизельное": "diesel", "Керосин": "kerosene", "Газ сжиженный": "lpg"}
NSC_IMPLAUSIBLE = {("diesel", 2025): "Table shows USD 48.1 billion, about 100 times the other years; excluded from ratios, kept in the raw file"}
# Quoted by the press from National Statistical Committee reports; the originals were not found
PRESS_CHECKS = [
    {"claim": "Fuels and lubricants, all of 2023", "press_kt": 630.0, "press_usd_m": 277.0, "url": "https://economist.kg/ekonomika/2024/02/16/v-2023-ghodu-kyrghyzstan-importiroval-630-tysiach-tonn-gsm/"},
    {"claim": "Motor gasoline, first two months of 2025", "press_kt": 170.2, "press_usd_m": 73.3, "url": "https://economist.kg/transport/2025/04/16/kyrghyzstan-narastil-import-bienzina-osnovnym-postavshchikom-ostaietsia-rossiia/"},
]


def nsc_import_values():
    """Official annual import value by fuel, thousand USD (table 4.03.00.12)."""
    if not NSC_TABLE.exists():
        NSC_TABLE.parent.mkdir(exist_ok=True)
        r = requests.get(NSC_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        r.raise_for_status()
        NSC_TABLE.write_bytes(r.content)
    rows = list(openpyxl.load_workbook(NSC_TABLE, data_only=True, read_only=True)["RUS"].iter_rows(values_only=True))
    header = next(r for r in rows if r and "Наименование показателей" in [str(c).strip() for c in r])
    years = {i: int(str(c).strip()[:4]) for i, c in enumerate(header) if str(c).strip()[:4].isdigit()}
    out = []
    for row in rows:
        label = next((str(c).strip() for c in row[:3] if isinstance(c, str) and str(c).strip() in NSC_ROWS), None)
        if label:
            out += [{"fuel": NSC_ROWS[label], "year": y, "usd_thousand": row[i]} for i, y in years.items() if isinstance(row[i], (int, float))]
    frame = pd.DataFrame(out)
    bad = [(f, y) in NSC_IMPLAUSIBLE for f, y in zip(frame.fuel, frame.year)]
    return frame.assign(usd_thousand=frame.usd_thousand.mask(bad))


def fetch_operational_reports():
    """Monthly NSC express reports. Titles come from each file's own download name."""
    out = RAW / "official_kg"
    page = requests.get(NSC_PAGE, headers={"User-Agent": "Mozilla/5.0"}, timeout=60).text
    records = []
    for report in dict.fromkeys(re.findall(r"/ru/statistics/download/operational/(\d+)/", page)):
        path = out / f"nsc_operational_{report}.xlsx"
        r = requests.get(f"https://stat.gov.kg/ru/statistics/download/operational/{report}/", headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        r.raise_for_status()
        path.write_bytes(r.content)
        name = re.search(r'filename="(.+?)"', r.headers.get("content-disposition", ""))
        title = name.group(1).encode("latin1").decode("utf8") if name else ""
        records.append({"id": report, "title": title, "file": path.name, "sha256": hashlib.sha256(r.content).hexdigest()})
    (out / "manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    return records


def nsc_monthly_total_imports():
    """All-goods monthly imports in USD million. Later reports supersede earlier ones. Column H is imports."""
    records = json.loads((RAW / "official_kg" / "manifest.json").read_text(encoding="utf-8"))
    vintages = []
    for rec in sorted(records, key=lambda r: int(r["id"])):
        year = None
        for row in openpyxl.load_workbook(RAW / "official_kg" / rec["file"], data_only=True).worksheets[0].iter_rows(values_only=True):
            first = str(row[0]).strip() if row[0] is not None else ""
            if re.fullmatch(r"20\d\d(\s*\d)?", first):
                year = int(first[:4])
            elif year and first in MONTHS_RU and isinstance(row[7], (int, float)):
                vintages.append({"period": year * 100 + MONTHS_RU[first], "report": int(rec["id"]), "usd_m": float(row[7])})
    v = pd.DataFrame(vintages).sort_values(["period", "report"])
    return v.groupby("period").agg(nsc_first_usd_m=("usd_m", "first"), nsc_latest_usd_m=("usd_m", "last"), vintages=("usd_m", "size")).reset_index()


def all_goods_check(snapshot):
    """Do Comtrade's Kyrgyz records equal the first or the latest national figure?"""
    c = cleaning.load_snapshot(snapshot, "kgz_all_goods")
    ct = c[c.cmdCode == "TOTAL"].groupby("period").primaryValue.sum().div(1e6).rename("comtrade_total_usd_m").reset_index()
    out = nsc_monthly_total_imports().merge(ct, how="outer", on="period").sort_values("period")
    out["comtrade_to_first"] = out.comtrade_total_usd_m / out.nsc_first_usd_m
    out["comtrade_to_latest"] = out.comtrade_total_usd_m / out.nsc_latest_usd_m
    return out


def annual_reconciliation(monthly):
    """Annual comparison by mass and by value. A year is compared only where all 12 months are observed."""
    teb = pd.read_parquet(PROCESSED / "ext_energy_balance.parquet")
    imports = teb[teb["item"] == "imports"].pivot(index="year", columns="fuel", values="kt")
    values = nsc_import_values().pivot(index="year", columns="fuel", values="usd_thousand") / 1000
    kg = monthly[monthly.iso3 == "KGZ"].assign(year=lambda d: d.period // 100)
    rows = []
    for year in range(2015, 2026):
        y = kg[kg.year == year]
        gas, mid = y[y.product_group == "gasoline"], y[y.product_group == "middle_heavy"]
        gas_m, mid_m = int(gas.import_mass_t.notna().sum()), int(mid.import_mass_t.notna().sum())
        rec = {"year": year, "gas_months_observed": gas_m, "mid_months_observed": mid_m, "gas_ct_kt": gas.import_mass_t.sum() / 1000,
               "gas_ct_with_volume_est_kt": gas.import_mass_t.fillna(gas.mass_t_incl_volume_estimate).sum() / 1000,
               "gas_teb_kt": imports.gasoline.get(year), "mid_ct_kt": mid.import_mass_t.sum() / 1000, "diesel_teb_kt": imports.diesel.get(year), "fuel_oil_teb_kt": imports.fuel_oil.get(year),
               "gas_ct_usd_m": gas.import_value_usd.sum() / 1e6, "gas_nsc_usd_m": values.gasoline.get(year), "mid_ct_usd_m": mid.import_value_usd.sum() / 1e6,
               "diesel_nsc_usd_m": values.diesel.get(year), "kerosene_nsc_usd_m": values.kerosene.get(year),
               "lpg_ct_usd_m": y[y.product_group == "lpg"].import_value_usd.sum() / 1e6, "lpg_nsc_usd_m": values.lpg.get(year),
               "value_months": int(gas.import_value_usd.notna().sum())}
        rows.append(rec)
    r = pd.DataFrame(rows)
    r["gas_mass_ratio"] = r.gas_ct_kt / r.gas_teb_kt
    r["gas_mass_ratio_with_estimate"] = r.gas_ct_with_volume_est_kt / r.gas_teb_kt
    r["mid_to_diesel_plus_fuel_oil"] = r.mid_ct_kt / (r.diesel_teb_kt + r.fuel_oil_teb_kt)
    r["gas_value_ratio"] = r.gas_ct_usd_m / r.gas_nsc_usd_m
    r["mid_value_to_diesel_plus_kerosene"] = r.mid_ct_usd_m / (r.diesel_nsc_usd_m + r.kerosene_nsc_usd_m)
    r["lpg_value_ratio"] = r.lpg_ct_usd_m / r.lpg_nsc_usd_m
    r["gas_ct_uv"] = r.gas_ct_usd_m * 1e6 / (r.gas_ct_with_volume_est_kt * 1000)
    r["gas_official_uv"] = r.gas_nsc_usd_m * 1e6 / (r.gas_teb_kt * 1000)
    return r


def press_checks(monthly):
    kg = monthly[monthly.iso3 == "KGZ"]
    def total(products, periods):
        s = kg[kg.product_group.isin(products) & kg.period.isin(periods)]
        return s.import_mass_t.sum() / 1000, s.import_value_usd.sum() / 1e6
    gas23 = total(["gasoline"], range(202301, 202313))
    mid23 = total(["middle_heavy"], range(202301, 202313))
    gas25 = total(["gasoline"], [202501, 202502])
    rows = [{**PRESS_CHECKS[0], "comtrade_kt": gas23[0] + mid23[0], "comtrade_usd_m": gas23[1] + mid23[1], "comtrade_basis": "gasoline + HS 271019"},
            {**PRESS_CHECKS[1], "comtrade_kt": gas25[0], "comtrade_usd_m": gas25[1], "comtrade_basis": "gasoline, Jan-Feb 2025"}]
    return pd.DataFrame(rows)


def import_dependency():
    """Annual dependency from the balance. Only for Kyrgyzstan: other countries lack matching
    production and consumption data here, so no dependency figure is given for them."""
    teb = pd.read_parquet(PROCESSED / "ext_energy_balance.parquet").pivot_table(index=["fuel", "year"], columns="item", values="kt").reset_index()
    teb["exports"] = teb.exports.fillna(0)
    teb["net_imports_kt"] = teb.imports - teb.exports
    teb["net_import_dependency"] = teb.net_imports_kt / teb.domestic_use
    teb["domestic_production_share"] = teb.production / (teb.production + teb.imports)
    teb["stock_cover_months"] = teb.stock_end / (teb.domestic_use / 12)
    return teb


def supplier_mirror(snapshot, bilateral, settings):
    """Partner-reported against reporter-reported mass, annually. Imports are CIF and exports FOB, and
    timing differs, so ratios near 1 are expected rather than exact."""
    bounds = settings["quality"]["unit_value_usd_per_t"]
    fuels = {"271011": "gasoline", "271012": "gasoline", "271019": "middle_heavy"}
    ru = cleaning.load_snapshot(snapshot, "mirror_russia")
    ru = ru.assign(product_group=ru.cmdCode.map(fuels), iso3=ru.partnerISO, year=ru.period // 100, exporter="RUS")
    ru["export_kt"] = ru.netWgt / 1e6
    ru = ru.dropna(subset=["product_group"])
    a = pd.read_parquet(PROCESSED.parent / "analytical" / "dataset_a_bilateral.parquet")
    x = a[(a.flow == "X") & a.product_group.isin(["gasoline", "middle_heavy"])]
    panel_x = x.assign(exporter=x.iso3, iso3=x.partner_iso, year=x.period // 100, export_kt=x.mass_t / 1000)
    exports = pd.concat([ru[["exporter", "iso3", "product_group", "year", "export_kt", "primaryValue"]].rename(columns={"primaryValue": "value_usd"}),
                         panel_x[["exporter", "iso3", "product_group", "year", "export_kt", "value_usd"]]])
    months_x = pd.concat([ru[["exporter", "iso3", "product_group", "period"]], panel_x.assign(period=x.period)[["exporter", "iso3", "product_group", "period"]]])
    e = exports.groupby(["exporter", "iso3", "product_group", "year"], as_index=False).agg(export_kt=("export_kt", "sum"), export_usd_m=("value_usd", lambda s: s.sum() / 1e6))
    imp = bilateral[bilateral.product_group.isin(["gasoline", "middle_heavy"])]
    imp = imp.assign(exporter=imp.partner_iso, year=imp.period // 100)
    i = imp.groupby(["exporter", "iso3", "product_group", "year"], as_index=False).agg(import_kt=("import_mass_t", lambda s: s.sum() / 1000), import_usd_m=("import_value_usd", lambda s: s.sum() / 1e6), import_months=("period", "nunique"))
    m = e.merge(i, on=["exporter", "iso3", "product_group", "year"])
    m = m[(m.import_kt >= 1) & (m.export_kt >= 1) & (m.import_months == 12)]
    m["mass_ratio_imports_to_exports"] = m.import_kt / m.export_kt.where(m.export_kt > 0)
    m["value_ratio_imports_to_exports"] = m.import_usd_m / m.export_usd_m.where(m.export_usd_m > 0)
    return m.sort_values(["iso3", "exporter", "product_group", "year"])
