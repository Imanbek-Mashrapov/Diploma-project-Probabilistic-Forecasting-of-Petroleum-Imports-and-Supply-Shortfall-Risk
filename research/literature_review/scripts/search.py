"""Stage 2: run the search strategy against scholarly APIs and log every query.

Sources: OpenAlex, Crossref, Semantic Scholar Academic Graph, arXiv.
Raw responses go to metadata/raw/<source>.jsonl; one row per (source, query) goes to
metadata/raw/search_log_<source>.csv. Re-running skips (source, query) pairs already logged.
"""
import csv
import json
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "metadata" / "raw"
UA = {"User-Agent": "academic-literature-review-script"}
TODAY = date.today().isoformat()

QUERIES = {
    "A_petroleum_import": [
        "petroleum import forecasting", "refined petroleum products import prediction", "oil product demand forecasting",
        "energy imports forecasting", "international petroleum trade prediction", "fuel import dependency",
        "petroleum trade flows forecasting", "energy trade forecasting machine learning", "oil import demand forecasting",
        "gasoline demand forecasting", "diesel consumption forecasting",
    ],
    "B_supply_disruption": [
        "energy supply disruption prediction", "petroleum supply chain resilience", "oil supply disruption risk",
        "energy security forecasting", "fuel shortage early warning system", "supply shortfall prediction",
        "energy supply vulnerability", "petroleum supply chain risk assessment", "oil supply shock early warning indicators",
    ],
    "C_probabilistic": [
        "probabilistic energy forecasting", "probabilistic time series forecasting", "uncertainty quantification energy forecasting",
        "quantile regression energy forecasting", "conformal prediction time series", "probabilistic demand forecasting",
        "prediction intervals forecasting evaluation", "proper scoring rules probabilistic forecasts calibration",
    ],
    "D_global_dl": [
        "global time series forecasting", "local versus global forecasting models", "deep learning time series forecasting",
        "cross-learning time series forecasting", "GRU energy forecasting", "temporal convolutional network energy forecasting",
        "N-BEATS forecasting", "temporal fusion transformer energy", "transfer learning time series forecasting",
        "forecasting competition M4 M5 results", "DeepAR probabilistic forecasting",
    ],
    "E_boosting_ml": [
        "XGBoost energy forecasting", "LightGBM forecasting time series", "gradient boosting international trade forecasting",
        "machine learning energy imports", "random forest energy demand forecasting",
        "machine learning supply chain disruption prediction", "tree-based models versus deep learning",
    ],
    "F_geopolitical_trade": [
        "geopolitical risk petroleum imports", "geopolitical uncertainty energy trade", "sanctions petroleum trade flows",
        "geopolitical risk energy supply disruption", "international trade disruption prediction",
        "supplier concentration energy security", "Herfindahl Hirschman index energy imports",
        "trade dependency supply chain resilience", "geopolitical risk index oil", "oil trade network resilience shocks",
        "forecasting trade flows machine learning", "nowcasting international trade",
    ],
    "G_landlocked_kyrgyz": [
        "energy security landlocked developing countries", "petroleum import dependency Central Asia", "energy security Kyrgyzstan",
        "oil product imports Kyrgyz Republic", "fuel supply vulnerability Central Asia", "landlocked countries trade costs energy",
        "energy trade dependence developing countries", "Central Asia Russia energy trade dependence", "Kyrgyzstan fuel",
    ],
    "H_related": [
        "real-time data vintages forecasting evaluation", "data revisions trade statistics", "publication lag forecasting nowcasting ragged edge",
        "mirror trade statistics discrepancies", "UN Comtrade data quality", "petroleum import demand elasticity",
        "comparing predictive accuracy test forecasts", "rolling origin evaluation time series", "energy security index diversification",
        "fuel export ban impact neighbouring countries", "oil price shock import volumes", "anomaly detection trade flows",
    ],
}

OA_FIELDS = ("id,doi,title,publication_year,authorships,primary_location,type,cited_by_count,"
             "abstract_inverted_index,open_access,best_oa_location,locations")
# The unauthenticated Semantic Scholar pool returns HTTP 429 most of the time, so it gets a core subset, slowly
S2_CORE = {
    "petroleum import forecasting", "energy imports forecasting", "fuel import dependency", "energy supply disruption prediction",
    "oil supply disruption risk", "probabilistic energy forecasting", "local versus global forecasting models",
    "cross-learning time series forecasting", "gradient boosting international trade forecasting", "geopolitical risk petroleum imports",
    "supplier concentration energy security", "forecasting trade flows machine learning", "energy security landlocked developing countries",
    "petroleum import dependency Central Asia", "energy security Kyrgyzstan", "publication lag forecasting nowcasting ragged edge",
}
LIMITS = {"openalex": 25, "crossref": 20, "semanticscholar": 20, "arxiv": 10}


def get(url, params=None, tries=6, as_json=True):
    wait = 3
    for _ in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=40)
            if r.status_code == 200 and as_json:
                r.json()  # truncated bodies happen; treat them as a retryable failure
        except (requests.RequestException, ValueError):
            time.sleep(wait); wait *= 2; continue
        if r.status_code == 200:
            return r
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(wait); wait = min(wait * 2, 60); continue
        return r
    return None


def openalex(q):
    r = get("https://api.openalex.org/works", {"search": q, "per-page": LIMITS["openalex"], "select": OA_FIELDS})
    if r is None or r.status_code != 200:
        return None, None
    js = r.json()
    return js.get("meta", {}).get("count"), js.get("results", [])


def crossref(q):
    r = get("https://api.crossref.org/works", {"query.bibliographic": q, "rows": LIMITS["crossref"],
                                               "select": "DOI,title,author,issued,container-title,type,publisher,abstract,is-referenced-by-count,URL,link,license"})
    if r is None or r.status_code != 200:
        return None, None
    js = r.json()["message"]
    return js.get("total-results"), js.get("items", [])


def semanticscholar(q):
    r = get("https://api.semanticscholar.org/graph/v1/paper/search",
            {"query": q, "limit": LIMITS["semanticscholar"],
             "fields": "title,year,authors,venue,externalIds,abstract,openAccessPdf,publicationTypes,citationCount,url"}, tries=10)
    time.sleep(15)
    if r is None or r.status_code != 200:
        return None, None
    js = r.json()
    return js.get("total"), js.get("data", [])


def arxiv(q):
    terms = " AND ".join(f"all:{w}" for w in q.split() if len(w) > 2)
    r = get("https://export.arxiv.org/api/query", {"search_query": terms, "max_results": LIMITS["arxiv"]}, as_json=False)
    time.sleep(3)
    if r is None or r.status_code != 200:
        return None, None
    ns = {"a": "http://www.w3.org/2005/Atom", "os": "http://a9.com/-/spec/opensearch/1.1/", "ax": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(r.content)
    total = root.findtext("os:totalResults", namespaces=ns)
    items = []
    for e in root.findall("a:entry", ns):
        items.append({
            "id": e.findtext("a:id", namespaces=ns), "title": " ".join((e.findtext("a:title", namespaces=ns) or "").split()),
            "abstract": " ".join((e.findtext("a:summary", namespaces=ns) or "").split()),
            "published": e.findtext("a:published", namespaces=ns), "authors": [a.findtext("a:name", namespaces=ns) for a in e.findall("a:author", ns)],
            "doi": e.findtext("ax:doi", namespaces=ns), "journal_ref": e.findtext("ax:journal_ref", namespaces=ns),
            "categories": [c.get("term") for c in e.findall("a:category", ns)],
        })
    return int(total) if total else None, items


SOURCES = {"openalex": openalex, "crossref": crossref, "semanticscholar": semanticscholar, "arxiv": arxiv}


def main(only=None):
    for src in (only or SOURCES):
        run_source(src)


def run_source(src):
    fn = SOURCES[src]
    log_path = RAW / f"search_log_{src}.csv"
    done = set()
    if log_path.exists():
        with open(log_path, encoding="utf-8") as f:
            done = {r["query"] for r in csv.DictReader(f) if r["status"] == "ok"}
    new_log = not log_path.exists()
    with open(log_path, "a", newline="", encoding="utf-8") as logf, open(RAW / f"{src}.jsonl", "a", encoding="utf-8") as out:
        w = csv.DictWriter(logf, ["database", "theme", "query", "search_date", "total_hits", "retrieved", "status"])
        if new_log:
            w.writeheader()
        for theme, qs in QUERIES.items():
            for q in qs:
                if q in done or (src == "semanticscholar" and q not in S2_CORE):
                    continue
                total, items = fn(q)
                status = "ok" if items is not None else "failed"
                for rank, it in enumerate(items or [], 1):
                    out.write(json.dumps({"query": q, "theme": theme, "rank": rank, "item": it}, ensure_ascii=False) + "\n")
                w.writerow({"database": src, "theme": theme, "query": q, "search_date": TODAY, "total_hits": total,
                            "retrieved": len(items or []), "status": status})
                logf.flush()
                print(src, status, len(items or []), q, flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
