"""Stage 5a: verify every included record against Crossref (DOI registry) and enrich it.

For each included work: resolve the DOI at Crossref and compare titles; fetch abstract, open-access PDF
location and TLDR from the Semantic Scholar batch endpoint; fall back to OpenAlex for records without a DOI.
Writes metadata/raw/verified.json.
"""
import difflib
import json
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "metadata" / "raw"
UA = {"User-Agent": "academic-literature-review-script"}


def get(url, params=None, tries=6):
    wait = 2
    for _ in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=40)
            if r.status_code == 200:
                r.json()
                return r
            if r.status_code == 404:
                return r
        except (requests.RequestException, ValueError):
            pass
        time.sleep(wait); wait = min(wait * 2, 60)
    return None


def norm(t):
    return re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower()).split()


def s2_batch(dois):
    out = {}
    for i in range(0, len(dois), 400):
        ids = [f"DOI:{d}" if not d.startswith("10.48550/arxiv.") else f"ARXIV:{d.split('arxiv.')[1]}" for d in dois[i:i + 400]]
        wait = 5
        for _ in range(10):
            r = requests.post("https://api.semanticscholar.org/graph/v1/paper/batch",
                              params={"fields": "title,abstract,openAccessPdf,tldr,venue,year,externalIds"},
                              json={"ids": ids}, headers=UA, timeout=60)
            if r.status_code == 200:
                for d, p in zip(dois[i:i + 400], r.json()):
                    out[d] = p
                break
            time.sleep(wait); wait = min(wait * 2, 90)
    return out


def main():
    inc = json.load(open(RAW / "included.json", encoding="utf-8"))
    # incremental: keep verification already done for a key
    prev = {}
    if (RAW / "verified.json").exists():
        prev = {p["key"]: p["verification"] for p in json.load(open(RAW / "verified.json", encoding="utf-8"))}
    todo = [i for i in inc if i["key"] not in prev]
    s2 = s2_batch([i["doi"] for i in todo if i["doi"]])
    for it in inc:
        if it["key"] in prev:
            it["verification"] = prev[it["key"]]
            continue
        v = {"crossref_status": "no_doi", "title_similarity": None}
        if it["doi"]:
            r = get(f"https://api.crossref.org/works/{it['doi']}")
            if r is not None and r.status_code == 200:
                m = r.json()["message"]
                ct = (m.get("title") or [""])[0]
                v.update({
                    "crossref_status": "resolved", "crossref_title": ct,
                    "crossref_year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0],
                    "crossref_venue": (m.get("container-title") or [""])[0], "crossref_type": m.get("type"),
                    "crossref_publisher": m.get("publisher"), "crossref_url": m.get("URL"),
                    "crossref_volume": m.get("volume"), "crossref_issue": m.get("issue"), "crossref_page": m.get("page"),
                    "crossref_article_number": m.get("article-number"),
                    "crossref_authors": [{"given": a.get("given", ""), "family": a.get("family", a.get("name", ""))} for a in m.get("author", [])],
                    "crossref_license": [l.get("URL") for l in m.get("license", [])],
                    "crossref_abstract": " ".join(re.sub(r"<[^>]+>", " ", m.get("abstract") or "").split()),
                    "crossref_relation": m.get("relation", {}),
                    "crossref_update_to": m.get("update-to"),
                })
                v["title_similarity"] = round(difflib.SequenceMatcher(None, norm(ct), norm(it["title"])).ratio(), 2)
            elif r is not None and r.status_code == 404:
                v["crossref_status"] = "doi_not_in_crossref"   # e.g. DataCite DOIs (arXiv, Zenodo, SSRN via DataCite)
            else:
                v["crossref_status"] = "lookup_failed"
        p = s2.get(it["doi"]) or {}
        v.update({"s2_abstract": p.get("abstract") or "", "s2_tldr": (p.get("tldr") or {}).get("text", ""),
                  "s2_oa_pdf": (p.get("openAccessPdf") or {}).get("url", ""), "s2_found": bool(p)})
        if not it["doi"]:
            q = get("https://api.openalex.org/works", {"filter": f"title.search:{it['title'][:150]}", "per-page": 1})
            res = q.json().get("results", []) if q is not None and q.status_code == 200 else []
            if res:
                v["openalex_check_title"] = res[0].get("title")
                v["openalex_check_venue"] = ((res[0].get("primary_location") or {}).get("source") or {}).get("display_name")
        it["verification"] = v
        print(v["crossref_status"], v["title_similarity"], it["title"][:60], flush=True)
    json.dump(inc, open(RAW / "verified.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
