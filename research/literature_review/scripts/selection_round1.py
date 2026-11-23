"""Stage 4b: manual title/abstract screening decisions, round 1.

Row numbers refer to metadata/raw/prescreen.csv as built on 2026-11-07 before seeds were merged;
running this script converts them to stable keys (DOI or normalised title) in
metadata/raw/selection_round1.json, so later rebuilds of the candidate table do not shift decisions.
Tier: core = detailed extraction; support = method/background source cited for a specific point.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "metadata" / "raw"

PF, ES, PR, GT, DL, GR, LL = ("petroleum_forecasting", "energy_security", "probabilistic_forecasting", "global_time_series",
                              "deep_learning", "geopolitical_risk", "landlocked_economies")
SEL = {
    # petroleum / energy import and demand forecasting
    926: (PF, "core"), 941: (PF, "core"), 28: (PF, "core"), 214: (PF, "core"), 608: (PF, "core"), 212: (PF, "core"),
    224: (PF, "core"), 607: (PF, "core"), 2456: (PF, "core"), 2459: (PF, "core"), 1327: (PF, "core"), 189: (PF, "core"),
    119: (PF, "core"), 10: (PF, "core"), 953: (PF, "core"), 3: (PF, "support"), 1300: (PF, "core"), 1297: (PF, "support"),
    340: (PF, "support"), 497: (PF, "support"), 2791: (PF, "core"), 213: (PF, "support"), 9: (PF, "core"), 1418: (PF, "support"),
    1296: (PF, "support"), 930: (PF, "support"), 2461: (PF, "support"), 925: (PF, "support"),
    # trade-flow forecasting and trade data quality (filed under petroleum_forecasting: forecasting of trade flows)
    534: (PF, "core"), 138: (PF, "core"), 1557: (PF, "support"), 1079: (PF, "core"), 319: (PF, "core"), 1552: (PF, "core"),
    1085: (PF, "support"), 300: (PF, "support"), 1567: (PF, "support"), 1265: (PF, "support"), 1565: (PF, "core"),
    1326: (PF, "core"), 366: (PF, "support"), 1325: (LL, "support"), 1413: (LL, "support"), 152: (GR, "core"),
    # energy security, supply disruption, early warning
    6: (ES, "core"), 20: (ES, "core"), 70: (ES, "core"), 512: (ES, "core"), 613: (ES, "core"), 1597: (ES, "support"),
    928: (ES, "core"), 3687: (ES, "core"), 2467: (ES, "core"), 409: (ES, "core"), 1063: (ES, "core"), 2195: (ES, "support"),
    2449: (ES, "support"), 2216: (ES, "support"), 2538: (ES, "support"), 2540: (ES, "support"), 2483: (ES, "support"),
    111: (ES, "support"), 1512: (ES, "core"), 588: (ES, "support"), 491: (ES, "core"), 3691: (ES, "support"),
    2280: (ES, "core"), 1015: (ES, "support"), 449: (ES, "support"), 95: (ES, "support"), 390: (ES, "support"),
    56: (ES, "support"), 181: (ES, "support"), 769: (ES, "core"),
    # geopolitical risk and sanctions
    2925: (GR, "core"), 460: (GR, "core"), 161: (GR, "core"), 975: (GR, "core"), 978: (GR, "support"), 2214: (GR, "support"),
    2409: (GR, "support"), 436: (GR, "support"), 1019: (GR, "support"), 23: (GR, "core"), 1468: (GR, "core"), 504: (GR, "core"),
    1016: (GR, "support"), 1674: (GR, "support"), 715: (GR, "core"), 1001: (GR, "core"),
    # global / local forecasting and forecast evaluation
    582: (GT, "core"), 1517: (GT, "core"), 1059: (GT, "core"), 2342: (GT, "core"), 1730: (GT, "support"), 2915: (GT, "support"),
    1245: (GT, "support"), 500: (GT, "support"), 3238: (GT, "support"), 131: (GT, "support"), 1101: (GT, "support"),
    1579: (GT, "support"), 1314: (GT, "support"), 2974: (GT, "core"), 1851: (GT, "core"), 2893: (GT, "core"),
    2892: (GT, "support"), 3366: (GT, "support"), 3151: (GT, "support"), 2905: (GT, "support"), 2909: (GT, "support"),
    2979: (GT, "support"), 3362: (GT, "support"), 3536: (GT, "core"),
    # real-time data / publication lag (forecast-evaluation design, filed under global_time_series)
    584: (GT, "core"), 2929: (GT, "support"), 476: (GT, "core"), 1523: (GT, "support"), 3499: (GT, "support"),
    659: (GT, "support"), 1575: (GT, "support"),
    # deep learning versus gradient boosting
    2509: (DL, "core"), 2760: (DL, "core"), 2761: (DL, "core"), 2476: (DL, "core"), 1283: (DL, "core"), 2492: (DL, "support"),
    630: (DL, "core"), 1550: (DL, "support"), 1342: (DL, "support"), 2495: (DL, "support"), 1444: (DL, "support"),
    # probabilistic forecasting and calibration
    1075: (PR, "core"), 1068: (PR, "core"), 1934: (PR, "core"), 1946: (PR, "support"), 1850: (PR, "support"),
    1432: (PR, "support"), 1959: (PR, "support"), 1287: (PR, "support"), 1337: (PR, "support"), 522: (PR, "support"),
    2021: (PR, "support"), 1866: (PR, "support"), 1849: (PR, "core"), 1149: (PR, "support"),
    # landlocked economies, Central Asia, Kyrgyzstan
    209: (LL, "core"), 13: (LL, "core"), 285: (LL, "support"), 1402: (LL, "core"), 39: (LL, "support"), 185: (LL, "support"),
    598: (LL, "support"), 640: (LL, "support"), 337: (LL, "support"), 713: (LL, "support"), 1284: (LL, "support"),
    320: (LL, "support"), 277: (LL, "support"), 289: (LL, "support"), 1083: (LL, "support"),
}


def main():
    rows = list(csv.DictReader(open(RAW / "prescreen.csv", encoding="utf-8")))
    out = []
    for i, (theme, tier) in SEL.items():
        r = rows[i]
        out.append({"key": r["key"], "title": r["title"], "doi": r["doi"], "theme": theme, "tier": tier, "row_round1": i})
    json.dump(out, open(RAW / "selection_round1.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(len(out), "selected;", sum(o["tier"] == "core" for o in out), "core")


if __name__ == "__main__":
    main()
