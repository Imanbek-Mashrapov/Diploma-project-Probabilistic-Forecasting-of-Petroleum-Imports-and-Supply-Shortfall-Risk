"""Stage 3: normalise raw search records, deduplicate and score topical relevance.

Input: metadata/raw/*.jsonl. Output: metadata/raw/candidates.csv (one row per unique work)
and metadata/raw/dedup_stats.json. Relevance scores only order the screening queue;
every inclusion decision is made by reading the title and abstract.
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "metadata" / "raw"


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())[:150]


def norm_doi(d):
    if not d:
        return ""
    d = d.lower().strip()
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", d)


def oa_abstract(inv):
    if not inv:
        return ""
    pos = sorted((p, w) for w, ps in inv.items() for p in ps)
    return " ".join(w for _, w in pos)


def from_openalex(it):
    loc = it.get("primary_location") or {}
    src = loc.get("source") or {}
    best = it.get("best_oa_location") or {}
    return {
        "title": it.get("title") or it.get("display_name") or "", "year": it.get("publication_year"),
        "authors": "; ".join(a["author"]["display_name"] for a in it.get("authorships", [])[:20] if a.get("author")),
        "venue": src.get("display_name") or "", "doi": norm_doi(it.get("doi")), "type": it.get("type") or "",
        "abstract": oa_abstract(it.get("abstract_inverted_index")), "cited_by": it.get("cited_by_count"),
        "oa_pdf": best.get("pdf_url") or "", "oa_license": best.get("license") or "", "url": loc.get("landing_page_url") or "",
        "openalex_id": (it.get("id") or "").rsplit("/", 1)[-1], "publisher_host": src.get("host_organization_name") or "",
    }


def from_crossref(it):
    issued = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
    abstract = re.sub(r"<[^>]+>", " ", it.get("abstract") or "")
    return {
        "title": (it.get("title") or [""])[0], "year": issued,
        "authors": "; ".join(" ".join(filter(None, [a.get("given"), a.get("family")])) for a in it.get("author", [])[:20]),
        "venue": (it.get("container-title") or [""])[0], "doi": norm_doi(it.get("DOI")), "type": it.get("type") or "",
        "abstract": " ".join(abstract.split()), "cited_by": it.get("is-referenced-by-count"), "oa_pdf": "", "oa_license": "",
        "url": it.get("URL") or "", "openalex_id": "", "publisher_host": it.get("publisher") or "",
    }


def from_s2(it):
    ext = it.get("externalIds") or {}
    pdf = (it.get("openAccessPdf") or {}).get("url") or ""
    doi = norm_doi(ext.get("DOI")) or (f"10.48550/arxiv.{ext['ArXiv'].lower()}" if ext.get("ArXiv") else "")
    return {
        "title": it.get("title") or "", "year": it.get("year"), "authors": "; ".join(a.get("name", "") for a in (it.get("authors") or [])[:20]),
        "venue": it.get("venue") or "", "doi": doi, "type": ",".join(it.get("publicationTypes") or []),
        "abstract": it.get("abstract") or "", "cited_by": it.get("citationCount"), "oa_pdf": pdf, "oa_license": "",
        "url": it.get("url") or "", "openalex_id": "", "publisher_host": "",
    }


def from_arxiv(it):
    aid = re.sub(r"v\d+$", "", (it.get("id") or "").rsplit("/abs/", 1)[-1])
    return {
        "title": it.get("title") or "", "year": int(it["published"][:4]) if it.get("published") else None,
        "authors": "; ".join(it.get("authors") or []), "venue": it.get("journal_ref") or "arXiv",
        "doi": norm_doi(it.get("doi")) or f"10.48550/arxiv.{aid.lower()}", "type": "preprint",
        "abstract": it.get("abstract") or "", "cited_by": None, "oa_pdf": f"https://arxiv.org/pdf/{aid}", "oa_license": "arxiv",
        "url": f"https://arxiv.org/abs/{aid}", "openalex_id": "", "publisher_host": "arXiv",
    }


PARSERS = {"openalex": from_openalex, "crossref": from_crossref, "semanticscholar": from_s2, "arxiv": from_arxiv, "snowball": from_openalex, "gapcheck": from_openalex, "seedrecords": from_openalex, "gapcheck_crossref": from_crossref}

WEIGHTS = [
    (r"petroleum|oil product|refined (oil|product)|gasoline|diesel|motor fuel|\bfuel", 3),
    (r"\boil\b|crude|energy", 1.5),
    (r"import|export|trade flow|international trade|\btrade\b", 2.5),
    (r"forecast|predict|nowcast", 2.5),
    (r"probabilist|quantile|prediction interval|conformal|uncertainty|calibrat|crps|pinball|density forecast", 2),
    (r"global model|cross-learning|cross learning|local and global|locality|panel of|multiple time series|groups of time series", 2.5),
    (r"landlocked|kyrgyz|central asia|tajik|kazakh|uzbek|mongolia|caucasus|armenia|nepal|bolivia|paraguay|zambia", 3),
    (r"geopolitic|sanction|embargo|supplier concentration|herfindahl|hhi|diversif|energy security|security of supply", 2.5),
    (r"disruption|shortage|shortfall|early warning|resilien|vulnerab|supply risk|shock", 2),
    (r"lightgbm|xgboost|gradient boost|random forest|lstm|gru|temporal convolution|n-beats|transformer|deepar|neural", 1),
    (r"publication lag|data revision|real-time data|vintage|ragged edge", 2.5),
]


def score(r):
    text = f"{r['title']} {r['title']} {r['abstract']}".lower()
    return round(sum(w for pat, w in WEIGHTS if re.search(pat, text)), 1)


def main():
    raw_count = defaultdict(int)
    groups = {}
    title_to_key = {}
    for name, parse in PARSERS.items():
        path = RAW / f"{name}.jsonl"
        if not path.exists():
            continue
        for line in open(path, encoding="utf-8"):
            row = json.loads(line)
            rec = parse(row["item"])
            if not rec["title"]:
                continue
            raw_count[name] += 1
            nt = norm_title(rec["title"])
            key = rec["doi"] or nt
            # same title under another DOI = preprint/journal versions or duplicate deposits: merge, keep history
            key = title_to_key.get(nt, key)
            title_to_key.setdefault(nt, key)
            g = groups.setdefault(key, {"records": [], "sources": set(), "queries": set(), "themes": set(), "dois": set()})
            g["records"].append((name, rec))
            g["sources"].add(name)
            g["queries"].add(row["query"])
            g["themes"].add(row["theme"])
            if rec["doi"]:
                g["dois"].add(rec["doi"])
    seeds = set()
    if (RAW / "seeds.jsonl").exists():
        for line in open(RAW / "seeds.jsonl", encoding="utf-8"):
            s = json.loads(line)
            sid = s["seed_id"].lower()
            seeds.add(f"10.48550/arxiv.{sid.split('/abs/')[1]}" if "/abs/" in sid else sid)

    pref = ["crossref", "openalex", "seedrecords", "snowball", "gapcheck", "gapcheck_crossref", "semanticscholar", "arxiv"]
    out = []
    for key, g in groups.items():
        recs = sorted(g["records"], key=lambda x: pref.index(x[0]))
        merged = {}
        for field in recs[0][1]:
            merged[field] = next((r[field] for _, r in recs if r[field] not in (None, "")), "")
        # Prefer a journal DOI over an arXiv DOI when both versions were found
        journal = [d for d in g["dois"] if not d.startswith("10.48550")]
        if journal:
            merged["doi"] = sorted(journal)[0]
        merged["abstract"] = max((r["abstract"] for _, r in recs), key=len)
        merged["oa_pdf"] = next((r["oa_pdf"] for _, r in recs if r["oa_pdf"]), "")
        merged.update({
            "key": key, "all_dois": "|".join(sorted(g["dois"])), "n_versions": len(g["dois"]),
            "found_in": "|".join(sorted(g["sources"])), "n_hits": len(recs), "themes": "|".join(sorted(g["themes"])),
            "queries": " || ".join(sorted(g["queries"]))[:1500], "is_seed": bool(seeds & g["dois"]),
        })
        merged["relevance"] = score(merged)
        out.append(merged)
    out.sort(key=lambda r: (-r["relevance"], -(r["n_hits"])))
    fields = ["key", "relevance", "is_seed", "title", "year", "authors", "venue", "type", "doi", "all_dois", "n_versions",
              "openalex_id", "cited_by", "oa_pdf", "oa_license", "url", "publisher_host", "found_in", "n_hits", "themes", "queries", "abstract"]
    with open(RAW / "candidates.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        for r in out:
            w.writerow({k: r.get(k, "") for k in fields})
    stats = {"raw_records_by_source": dict(raw_count), "raw_records_total": sum(raw_count.values()), "unique_works": len(out),
             "multi_version_groups": sum(1 for r in out if r["n_versions"] > 1)}
    json.dump(stats, open(RAW / "dedup_stats.json", "w"), indent=2)
    print(stats)


if __name__ == "__main__":
    main()
