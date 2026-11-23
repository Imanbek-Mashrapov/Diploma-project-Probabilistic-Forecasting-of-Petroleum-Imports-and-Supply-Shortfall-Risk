"""Stage 6a: targeted Boolean searches that test each candidate research gap (OpenAlex title+abstract search).

The hit count of each query is evidence in itself: a small count with no on-target paper supports a gap,
a large count means the area is covered. Writes metadata/raw/gapcheck.jsonl and search_log_gapcheck.csv.
"""
import csv
import json
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "metadata" / "raw"
UA = {"User-Agent": "academic-literature-review-script"}
FIELDS = ("id,doi,title,publication_year,authorships,primary_location,type,cited_by_count,"
          "abstract_inverted_index,open_access,best_oa_location")

GAP_QUERIES = {
    "A_global_landlocked": [
        'landlocked AND (oil OR petroleum OR fuel) AND (forecast OR forecasting OR prediction)',
        '(petroleum OR "oil products" OR "refined products" OR gasoline OR diesel OR fuel) AND (import OR imports) AND (forecast OR forecasting) AND ("cross-country" OR panel OR "global model" OR "multiple countries")',
        '(Comtrade) AND (forecast OR forecasting OR prediction)',
    ],
    "B_dl_vs_gbm": [
        '(LightGBM OR XGBoost OR "gradient boosting") AND (LSTM OR GRU OR "N-BEATS" OR "deep learning") AND (import OR imports OR "international trade") AND (forecast OR forecasting)',
        '(LightGBM OR XGBoost OR "gradient boosting") AND (LSTM OR GRU OR "deep learning") AND (oil OR petroleum OR fuel OR gasoline) AND (demand OR consumption OR import) AND forecasting',
    ],
    "C_probabilistic_imports": [
        '(probabilistic OR quantile OR "prediction interval" OR "prediction intervals" OR conformal OR "density forecast") AND (oil OR petroleum OR fuel OR gasoline OR diesel) AND (import OR imports OR demand OR consumption) AND forecasting',
        '(probabilistic OR quantile OR "prediction interval" OR conformal) AND (import OR imports OR "trade flows") AND forecasting',
    ],
    "D_publication_lag": [
        '("publication lag" OR "publication delay" OR "release lag" OR "real-time data" OR "data vintages" OR "data revisions" OR "ragged edge") AND (trade OR imports OR exports) AND (forecast OR forecasting OR nowcasting)',
        '("publication lag" OR "release lag" OR "real-time" OR vintage) AND (oil OR petroleum OR energy) AND (forecast OR forecasting OR nowcasting)',
    ],
    "E_supplier_gpr_features": [
        '"geopolitical risk" AND (import OR imports OR trade) AND (forecast OR forecasting OR prediction)',
        '("supplier concentration" OR Herfindahl OR HHI OR "supplier diversification") AND (oil OR petroleum OR fuel OR energy) AND (import OR imports)',
        '"geopolitical risk" AND (oil OR petroleum) AND (import OR imports)',
    ],
    "F_early_warning": [
        '"early warning" AND (fuel OR oil OR petroleum OR energy) AND (supply OR shortage OR disruption OR security)',
        '(shortage OR shortfall OR "supply disruption") AND (fuel OR petroleum OR "oil products") AND (prediction OR forecasting OR "early warning")',
    ],
    "G_landlocked_group": [
        'landlocked AND ("energy security" OR "oil import" OR "fuel import" OR "petroleum import" OR "energy import")',
        '(Kyrgyzstan OR Kyrgyz OR "Central Asia") AND (fuel OR petroleum OR "oil products" OR gasoline) AND (import OR imports OR supply)',
    ],
}


def get(params, tries=3):
    wait = 2
    for _ in range(tries):
        try:
            r = requests.get("https://api.openalex.org/works", params=params, headers=UA, timeout=120)
            if r.status_code == 200:
                r.json()
                return r
        except (requests.RequestException, ValueError):
            pass
        time.sleep(wait); wait *= 2
    return None


def main():
    log_path = RAW / "search_log_gapcheck.csv"
    done = set()
    if log_path.exists():
        done = {r["query"] for r in csv.DictReader(open(log_path, encoding="utf-8")) if r["status"] == "ok"}
    mode = "a" if done else "w"
    with open(RAW / "gapcheck.jsonl", mode, encoding="utf-8") as out, open(log_path, mode, newline="", encoding="utf-8") as logf:
        w = csv.DictWriter(logf, ["database", "theme", "query", "search_date", "total_hits", "retrieved", "status"])
        if not done:
            w.writeheader()
        for theme, qs in GAP_QUERIES.items():
            for q in qs:
                if q in done:
                    continue
                r = get({"filter": f"title_and_abstract.search:{q}", "per-page": 25, "sort": "relevance_score:desc", "select": FIELDS})
                items = r.json().get("results", []) if r else []
                total = r.json().get("meta", {}).get("count") if r else None
                for rank, it in enumerate(items, 1):
                    out.write(json.dumps({"query": q, "theme": f"gapcheck_{theme}", "rank": rank, "item": it}, ensure_ascii=False) + "\n")
                w.writerow({"database": "openalex_gapcheck", "theme": theme, "query": q, "search_date": date.today().isoformat(),
                            "total_hits": total, "retrieved": len(items), "status": "ok" if r else "failed"})
                logf.flush()
                out.flush()
                print(theme, total, len(items), flush=True)


if __name__ == "__main__":
    main()
