"""Stage 6a (fallback): Boolean gap checks applied locally, because the OpenAlex Boolean queries in
gapcheck.py returned HTTP 429 (rate limit) on 2026-11-07.

For each gap, (1) Crossref is queried with the plain keywords (top 200 by relevance) and (2) the same Boolean
condition is applied as a regular expression to the titles and abstracts of the whole deduplicated pool
(metadata/raw/candidates.csv) plus those Crossref results. Matches are written for manual reading.
This is weaker than a database-side Boolean count: it can only find what the pool or Crossref's top results contain.
Outputs: metadata/raw/gapcheck_crossref.jsonl, metadata/raw/search_log_gapcheck_local.csv, metadata/raw/gap_matches.json
"""
import csv
import json
import re
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "metadata" / "raw"
UA = {"User-Agent": "academic-literature-review-script"}

FUEL = r"(oil|petroleum|fuel|gasoline|diesel|refined product)"
GAPS = {
    "A_global_landlocked": ("landlocked oil petroleum fuel import forecasting",
                            [r"landlocked", FUEL, r"(forecast|predict)"]),
    "A2_cross_country_fuel_import_forecast": ("cross-country panel petroleum fuel import forecasting",
                            [r"(petroleum|oil product|refined|gasoline|diesel|fuel)", r"import", r"(forecast|predict)",
                             r"(panel|cross-country|countries|global model|pooled)"]),
    "B_dl_vs_gbm": ("gradient boosting LightGBM XGBoost LSTM deep learning trade import oil forecasting",
                    [r"(lightgbm|xgboost|gradient boost|catboost)", r"(lstm|gru|n-beats|deep learning|neural)",
                     r"(import|trade|oil|petroleum|fuel)", r"(forecast|predict)"]),
    "C_probabilistic_fuel": ("probabilistic quantile prediction interval oil fuel import demand forecasting",
                             [r"(probabilistic|quantile|prediction interval|conformal|density forecast)", FUEL,
                              r"(import|demand|consumption)", r"(forecast|predict)"]),
    "D_publication_lag": ("real-time data vintages publication lag trade import forecasting",
                          [r"(publication lag|release lag|real-time data|real time data|vintage|data revision|ragged edge|release calendar)",
                           r"(trade|import|export|oil|petroleum)", r"(forecast|nowcast)"]),
    "E_supplier_gpr_features": ("geopolitical risk supplier concentration oil imports forecasting",
                                [r"(geopolitical risk|herfindahl|hhi|supplier concentration|concentration of supply|diversification)",
                                 r"import", r"(forecast|predict)"]),
    "F_early_warning": ("early warning fuel oil supply shortage disruption",
                        [r"(early warning|alarm|alert)", r"(fuel|oil|petroleum|energy|import)", r"(supply|shortage|disruption|security)"]),
    "G_landlocked_energy": ("landlocked countries energy security fuel imports",
                            [r"landlocked", r"(energy|fuel|oil|petroleum)", r"(import|security|dependen)"]),
}


def crossref(q, rows=100, pages=2):
    items = []
    for p in range(pages):
        for _ in range(4):
            try:
                r = requests.get("https://api.crossref.org/works", headers=UA, timeout=60,
                                 params={"query.bibliographic": q, "rows": rows, "offset": p * rows,
                                         "select": "DOI,title,abstract,issued,container-title,type"})
                if r.status_code == 200:
                    items += r.json()["message"]["items"]
                    break
            except requests.RequestException:
                pass
            time.sleep(5)
    return items


def main():
    pool = [{"title": r["title"], "abstract": r["abstract"], "doi": r["doi"], "year": r["year"], "venue": r["venue"], "src": "pool"}
            for r in csv.DictReader(open(RAW / "candidates.csv", encoding="utf-8"))]
    matches = {}
    with open(RAW / "gapcheck_crossref.jsonl", "w", encoding="utf-8") as out, \
         open(RAW / "search_log_gapcheck_local.csv", "w", newline="", encoding="utf-8") as logf:
        w = csv.DictWriter(logf, ["database", "theme", "query", "search_date", "total_hits", "retrieved", "status"])
        w.writeheader()
        for gap, (q, pats) in GAPS.items():
            cr = crossref(q)
            recs = []
            for it in cr:
                out.write(json.dumps({"query": q, "theme": f"gapcheck_{gap}", "rank": 0, "item": it}, ensure_ascii=False) + "\n")
                recs.append({"title": (it.get("title") or [""])[0], "abstract": re.sub(r"<[^>]+>", " ", it.get("abstract") or ""),
                             "doi": it.get("DOI", "").lower(), "year": (it.get("issued", {}).get("date-parts") or [[None]])[0][0],
                             "venue": (it.get("container-title") or [""])[0], "src": "crossref"})
            w.writerow({"database": "crossref_gapcheck", "theme": gap, "query": q, "search_date": date.today().isoformat(),
                        "total_hits": None, "retrieved": len(cr), "status": "ok" if cr else "failed"})
            seen, hits = set(), []
            for r in pool + recs:
                text = f"{r['title']} {r['abstract']}".lower()
                if all(re.search(p, text) for p in pats):
                    k = r["doi"] or r["title"].lower()
                    if k not in seen:
                        seen.add(k)
                        hits.append({k2: r[k2] for k2 in ("title", "year", "venue", "doi", "src")})
            matches[gap] = {"crossref_query": q, "boolean": " AND ".join(pats), "n_matches": len(hits), "matches": hits}
            print(gap, len(cr), len(hits), flush=True)
    json.dump(matches, open(RAW / "gap_matches.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
