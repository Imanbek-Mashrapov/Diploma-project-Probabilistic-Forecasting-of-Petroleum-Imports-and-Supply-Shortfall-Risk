"""Stage 2b: verify the proposal's seed references and run backward/forward citation searching (OpenAlex).

Writes metadata/raw/seeds.jsonl (one verification record per seed id),
metadata/raw/snowball.jsonl (candidate records) and metadata/raw/search_log_snowball.csv.
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
TODAY = date.today().isoformat()

# Anchor papers for citation chasing, with the topical filter applied to their citing works
ANCHORS = {
    "10.1016/j.ijforecast.2021.03.004": "forecasting",                 # Montero-Manso & Hyndman, locality and globality
    "10.1016/j.ijforecast.2020.11.009": "forecasting",                 # Semenoglou et al., cross-learning
    "10.1016/j.patcog.2021.108441": "forecasting",                     # Hewamalage et al., global models simulation
    "10.1257/aer.20191823": "oil OR petroleum OR energy import",       # Caldara & Iacoviello, GPR
    "10.1016/j.enpol.2011.06.034": "oil OR petroleum OR import",       # Cohen et al., diversification of supplies
    "10.1016/j.enpol.2009.05.069": "oil OR petroleum OR import",       # Le Coq & Paltseva
    "10.1016/j.rser.2014.10.064": "oil OR petroleum OR import",        # Ang et al., energy security indexes
    "10.1016/j.knosys.2022.108687": "import OR oil",                   # Yang et al., oil import dependence forecasting
    "10.1016/j.physa.2024.129977": "trade OR import",                  # Silva et al., trade networks and ML
    "10.1016/j.ijforecast.2021.11.013": "gradient boosting OR LightGBM OR probabilistic",  # M5 accuracy
    "10.1016/j.ijforecast.2019.07.001": "energy OR trade OR demand",   # DeepAR
    "10.3390/en15217822": "energy OR fuel",                            # Kosowska & Kosowski, Tajikistan/Kyrgyzstan
}


def get(url, params=None, tries=6):
    wait = 2
    for _ in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=40)
        except requests.RequestException:
            time.sleep(wait); wait *= 2; continue
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(wait); wait = min(wait * 2, 60); continue
        return r
    return None


def verify_seed(sid):
    rec = {"seed_id": sid}
    if sid.lower().startswith("arxiv.org/abs/"):
        aid = sid.split("/abs/")[1]
        r = get("https://export.arxiv.org/api/query", {"id_list": aid})
        rec["arxiv_ok"] = bool(r is not None and r.status_code == 200 and "<entry>" in r.text and "<title>Error" not in r.text)
        oa = get(f"https://api.openalex.org/works/doi:10.48550/arxiv.{aid}")
    else:
        cr = get(f"https://api.crossref.org/works/{sid}")
        rec["crossref_ok"] = bool(cr is not None and cr.status_code == 200)
        if rec["crossref_ok"]:
            m = cr.json()["message"]
            rec["crossref_title"] = (m.get("title") or [""])[0]
            rec["crossref_year"] = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
            rec["crossref_venue"] = (m.get("container-title") or [""])[0]
        oa = get(f"https://api.openalex.org/works/doi:{sid}")
    rec["openalex"] = oa.json() if oa is not None and oa.status_code == 200 else None
    return rec


def main():
    seeds = [l.strip() for l in open(RAW / "proposal_seed_ids.txt", encoding="utf-8") if l.strip()]
    with open(RAW / "seeds.jsonl", "w", encoding="utf-8") as f:
        for s in seeds:
            f.write(json.dumps(verify_seed(s), ensure_ascii=False) + "\n")
            print("seed", s, flush=True)

    with open(RAW / "snowball.jsonl", "w", encoding="utf-8") as out, \
         open(RAW / "search_log_snowball.csv", "w", newline="", encoding="utf-8") as logf:
        w = csv.DictWriter(logf, ["database", "theme", "query", "search_date", "total_hits", "retrieved", "status"])
        w.writeheader()
        for doi, topic in ANCHORS.items():
            r = get(f"https://api.openalex.org/works/doi:{doi}")
            if r is None or r.status_code != 200:
                w.writerow({"database": "openalex_citations", "theme": "snowball", "query": f"anchor {doi}", "search_date": TODAY,
                            "total_hits": None, "retrieved": 0, "status": "anchor_not_found"})
                continue
            work = r.json()
            wid = work["id"].rsplit("/", 1)[1]
            # forward: newer works citing the anchor, restricted to the topic
            fr = get("https://api.openalex.org/works", {"filter": f"cites:{wid}", "search": topic, "per-page": 25, "sort": "cited_by_count:desc"})
            items = fr.json().get("results", []) if fr is not None and fr.status_code == 200 else []
            total = fr.json().get("meta", {}).get("count") if items else 0
            for rank, it in enumerate(items, 1):
                out.write(json.dumps({"query": f"cites {doi} | {topic}", "theme": "snowball_forward", "rank": rank, "item": it}, ensure_ascii=False) + "\n")
            w.writerow({"database": "openalex_citations", "theme": "snowball_forward", "query": f"cites {doi} | {topic}",
                        "search_date": TODAY, "total_hits": total, "retrieved": len(items), "status": "ok"})
            # backward: the anchor's reference list
            refs = [u.rsplit("/", 1)[1] for u in work.get("referenced_works", [])]
            got = []
            for i in range(0, len(refs), 50):
                br = get("https://api.openalex.org/works", {"filter": "openalex_id:" + "|".join(refs[i:i + 50]), "per-page": 50})
                if br is not None and br.status_code == 200:
                    got += br.json().get("results", [])
            for rank, it in enumerate(got, 1):
                out.write(json.dumps({"query": f"references of {doi}", "theme": "snowball_backward", "rank": rank, "item": it}, ensure_ascii=False) + "\n")
            w.writerow({"database": "openalex_citations", "theme": "snowball_backward", "query": f"references of {doi}",
                        "search_date": TODAY, "total_hits": len(refs), "retrieved": len(got), "status": "ok"})
            print("anchor", doi, len(items), len(got), flush=True)


if __name__ == "__main__":
    main()
