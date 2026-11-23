"""Stage 8a: assemble the deliverable tables from the raw search, screening, verification and extraction files.

Outputs
  metadata/papers_master.csv        included works (+ institutional reports), verified bibliographic data
  metadata/search_log.csv           every search with retrieved / screened / included counts
  metadata/excluded_papers.csv      every unique record not included, with stage and reason
  analysis/literature_matrix.csv    27-field extraction for every included work
  analysis/methodology_comparison.csv  coded design of forecasting and early-warning studies
  analysis/research_gaps.csv        gap assessment with scores and rank
  metadata/raw/stats.json           counts used by the report and figures
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import extraction_core_a, extraction_core_b, extraction_core_c, extraction_core_d  # noqa: E402
from extraction_support import ROLES  # noqa: E402
from fulltext_notes import FT  # noqa: E402
from gaps import CONTRIBUTIONS, GAPS  # noqa: E402
from merge import PARSERS, norm_title  # noqa: E402
from methods_coding import CODES, COLS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW, META, ANA = ROOT / "metadata" / "raw", ROOT / "metadata", ROOT / "analysis"

EXTRACT = {**extraction_core_a.E, **extraction_core_b.E, **extraction_core_c.E}
for k, v in extraction_core_d.E.items():
    EXTRACT[k] = v

THEME_LABEL = {"petroleum_forecasting": "Petroleum and trade-flow forecasting", "energy_security": "Energy security and early warning",
               "probabilistic_forecasting": "Probabilistic forecasting", "global_time_series": "Global forecasting and forecast evaluation",
               "deep_learning": "Deep learning versus gradient boosting", "geopolitical_risk": "Geopolitical risk and sanctions",
               "landlocked_economies": "Landlocked economies and Central Asia"}

INSTITUTIONAL_EXTRA = [
    dict(key="iea_kyrgyzstan_2022", title="Kyrgyzstan 2022: Energy Policy Review", authors="International Energy Agency", year="2022",
         venue="IEA", url="https://www.iea.org/reports/kyrgyzstan-2022", role="Kyrgyz energy-sector review; dependence on imported oil products"),
    dict(key="iea_kyrgyzstan_profile", title="Kyrgyzstan energy profile", authors="International Energy Agency", year="2020",
         venue="IEA", url="https://www.iea.org/reports/kyrgyzstan-energy-profile", role="States that over 90% of oil products are imported, mainly from Russia and Kazakhstan"),
    dict(key="unctad_2026_hormuz", title="Strait of Hormuz disruptions: The burden of oil price shocks on vulnerable economies", authors="UNCTAD",
         year="2026", venue="UNCTAD", url="https://unctad.org/news/new-unctad-monitor-warns-vulnerable-economies-face-heaviest-burden-oil-shocks",
         role="Refined products are 97.8% of net oil imports of vulnerable economies; price-shock burden on import bills"),
    dict(key="imf_wp_06_171", title="Weathering the storm so far: The impact of the 2003-05 oil shock on low-income countries", authors="International Monetary Fund (Working Paper 06/171)",
         year="2006", venue="IMF Working Paper", url="https://www.imf.org/en/Publications/WP/Issues/2016/12/31/Weathering-the-Storm-So-Far-The-Impact-of-the-200305-Oil-Shock-on-Low-Income-Countries-19368",
         role="Oil import volumes contracted with price pass-through in low-income importers"),
    dict(key="imf_wp_11_194", title="Oil shocks in a global perspective: Are they really that bad?", authors="Rasmussen, T. N.; Roitman, A. (IMF Working Paper 11/194)",
         year="2011", venue="IMF Working Paper", url="https://www.imf.org/en/Publications/WP/Issues/2016/12/31/Oil-Shocks-in-a-Global-Perspective-Are-they-Really-That-Bad-25164",
         role="Macroeconomic effects of oil price shocks on importers are usually small"),
    dict(key="un_ohrlls_lldc", title="List of Landlocked Developing Countries", authors="UN-OHRLLS", year="n.d.", venue="United Nations",
         url="https://www.un.org/ohrlls/content/list-lldcs", role="Official LLDC list used to define the landlocked panel"),
]


def peer_status(it):
    v = it["verification"]
    doi = it["doi"]
    ctype = v.get("crossref_type") or ""
    if doi.startswith("10.48550"):
        return "Preprint (arXiv)"
    if doi.startswith("10.2139"):
        return "Preprint / working paper (SSRN)"
    if doi.startswith("10.21203"):
        return "Preprint (Research Square)"
    if doi.startswith("10.71889"):
        return "Thesis (DataCite: dissertation)"
    if doi.startswith("10.5040"):
        return "Book / chapter"
    if doi == "10.26740/ijss.v4n2.p40-48":
        return "Journal article (DOI not registered)"
    if doi.startswith("10.34382"):
        return "Repository paper (JaLC DOI)"
    if doi.startswith("10.5281") or doi.startswith("10.62432"):
        return "Repository deposit (not verified as peer reviewed)"
    if doi.startswith("10.34989") or doi.startswith("10.17016"):
        return "Working paper (central bank)"
    if doi.startswith("10.1596") or doi.startswith("10.1787") or doi.startswith("10.30875"):
        return "Institutional report"
    if doi.startswith("10.32614"):
        return "Software package"
    if doi.startswith("10.59425"):
        return "Commentary (not peer reviewed)"
    if ctype == "journal-article":
        return "Peer-reviewed journal article"
    if ctype == "proceedings-article":
        return "Conference paper"
    if ctype in ("book-chapter", "book", "monograph", "edited-book"):
        return "Book / chapter"
    if ctype == "posted-content":
        return "Preprint"
    if it["key"].startswith("lightgbm"):
        return "Conference paper (NeurIPS 2017)"
    if not doi:
        return "Journal article (no DOI found)"
    return ctype or "Not determined"


def analysis_basis(doi, it, manual):
    if doi in FT:
        return "Full text"
    if len(it["abstract"]) >= 100 or doi in manual and "NOT extracted" not in manual[doi]["summary"]:
        return "Abstract only"
    return "Metadata only"


def parse_names(raw):
    """Return [(family, given)] from 'A B; C D', 'Family, Given; ...' or 'A B, C D' author strings."""
    parts = [x.strip() for x in (raw.split(";") if ";" in raw else raw.split(",") if raw.count(",") > 1 else [raw]) if x.strip()]
    out = []
    for n in parts:
        if "," in n:
            fam, giv = [x.strip() for x in n.split(",", 1)]
        else:
            toks = n.split()
            fam, giv = (toks[-1], " ".join(toks[:-1])) if toks else ("", "")
        out.append((fam, giv))
    return out


DATACITE = {}


def year_of(it):
    v = it.get("verification", {})
    return v.get("crossref_year") or DATACITE.get(it["key"], {}).get("datacite_year") or it["year"] or "n.d."


PROPER = ["Kyrgyzstan", "Kyrgyz", "Republic", "Russia", "Russian", "Kazakhstan", "Central Asian", "Central Asia", "Eurasian",
          "Indonesia", "India", "People's Republic", "Herfindahl-Hirschman", "Herfindahl", "China", "Iran", "Nigeria", "Serbian", "Serbia", "Pakistan", "Turkey"]
ORG = re.compile(r"universit|institut|named after|academy|ministry|college", re.I)


def person_authors(v):
    """Crossref sometimes lists an affiliation as an author (e.g. some Russian journals); drop such entries."""
    return [a for a in (v.get("crossref_authors") or []) if a["family"] and not ORG.search(a["family"] + " " + a["given"])]


def apa_authors(it):
    v = it["verification"]
    auth = person_authors(v)
    names = []
    if auth:
        for a in auth:
            fam, giv = a["family"], a["given"]
            ini = " ".join(f"{p[0]}." for p in re.split(r"[\s-]+", giv) if p)
            names.append(f"{fam}, {ini}".strip(", "))
    else:
        for fam, giv in parse_names(it["authors"]):
            ini = " ".join(f"{p[0]}." for p in re.split(r"[\s-]+", giv) if p)
            names.append(f"{fam}, {ini}".strip(", "))
    if not names:
        return "Anonymous"
    if len(names) > 20:
        names = names[:19] + ["... " + names[-1]]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + ", & " + names[-1]


def apa(it):
    v = it["verification"]
    year = year_of(it)
    title = v.get("crossref_title") or it["title"]
    if title.isupper():  # APA sentence case for titles registered in capitals, keeping proper nouns
        title = title.capitalize()
        for pn in PROPER:
            title = re.sub(r"\b" + re.escape(pn.lower()) + r"\b", pn, title)
    venue = v.get("crossref_venue") or it["venue"]
    vol, iss = v.get("crossref_volume"), v.get("crossref_issue")
    pages = v.get("crossref_page") or v.get("crossref_article_number")
    ref = f"{apa_authors(it)} ({year}). {title}."
    if venue:
        ref += f" {venue}"
        if vol:
            ref += f", {vol}"
            if iss:
                ref += f"({iss})"
        if pages:
            ref += f", {pages}"
        ref += "."
    if it["doi"]:
        ref += f" https://doi.org/{it['doi']}"
    elif it["url"]:
        ref += f" {it['url']}"
    return re.sub(r"\s+", " ", ref)


def main():
    inc = json.load(open(RAW / "verified.json", encoding="utf-8"))
    manual = {k: v for k, v in json.load(open(RAW / "manual_abstracts.json", encoding="utf-8")).items() if not k.startswith("_")}
    dc = json.load(open(RAW / "datacite_verification.json", encoding="utf-8"))
    DATACITE.update(dc)
    downloads = {d["key"]: d for d in json.load(open(RAW / "downloads.json", encoding="utf-8"))}
    s2 = json.load(open(RAW / "s2_abstracts.json", encoding="utf-8")) if (RAW / "s2_abstracts.json").exists() else {}
    for it in inc:  # fold in abstracts recovered after verification
        if len(it["abstract"]) < 100:
            if it["doi"] in manual:
                it["abstract"] = manual[it["doi"]]["summary"]
                it["abstract_source"] = manual[it["doi"]]["source"]
            elif len((s2.get(it["doi"]) or {}).get("abstract", "")) >= 100:
                it["abstract"] = s2[it["doi"]]["abstract"]
                it["abstract_source"] = "Semantic Scholar API"

    # ---------------- papers_master.csv
    master = []
    for i, it in enumerate(sorted(inc, key=lambda x: (x["theme"], x["tier"], -(int(x["year"] or 0)))), 1):
        v = it["verification"]
        ver = ("Crossref DOI resolved, title match %.2f" % v["title_similarity"]) if v["crossref_status"] == "resolved" else \
              ("DataCite DOI resolved" if dc.get(it["key"], {}).get("datacite_status") == "resolved" else
               ("DOI resolves via doi.org (JaLC)" if it["doi"] == "10.34382/00004671" else
                ("DOI not registered; verified from journal PDF" if it["doi"] == "10.26740/ijss.v4n2.p40-48" else
                 ("NeurIPS proceedings (no DOI)" if it["key"].startswith("lightgbm") else "Metadata from OpenAlex; no DOI"))))
        d = downloads.get(it["key"], {})
        it["id"] = f"P{i:03d}"
        master.append({
            "id": it["id"], "tier": it["tier"], "theme": THEME_LABEL[it["theme"]], "title": v.get("crossref_title") or it["title"],
            "authors": "; ".join(f"{a['given']} {a['family']}".strip() for a in person_authors(v)) or it["authors"],
            "year": year_of(it), "venue": v.get("crossref_venue") or it["venue"],
            "publication_type": peer_status(it), "doi": it["doi"], "doi_url": f"https://doi.org/{it['doi']}" if it["doi"] else "",
            "official_url": v.get("crossref_url") or it["url"], "open_access_pdf_url": d.get("source_url", "") if d.get("status") == "downloaded" else (it["oa_pdf"] or ""),
            "local_pdf": d.get("file", ""), "pdf_licence": d.get("licence", ""), "pdf_status": d.get("status", ""),
            "analysis_basis": analysis_basis(it["doi"], it, manual), "verification": ver,
            "all_version_dois": it["all_dois"], "found_in": it["found_in"], "is_proposal_seed": it["is_seed"],
            "apa7": apa(it),
        })
    for ex in INSTITUTIONAL_EXTRA:
        master.append({"id": ex["key"], "tier": "support", "theme": "Institutional report", "title": ex["title"], "authors": ex["authors"],
                       "year": ex["year"], "venue": ex["venue"], "publication_type": "Institutional report", "doi": "", "doi_url": "",
                       "official_url": ex["url"], "open_access_pdf_url": "", "local_pdf": "", "pdf_licence": "", "pdf_status": "not downloaded",
                       "analysis_basis": "Web page / search summary", "verification": "URL checked 2026-11-07 (IMF pages refuse automated requests)",
                       "all_version_dois": "", "found_in": "web search (institutional)", "is_proposal_seed": "False",
                       "apa7": f"{ex['authors']}. ({ex['year']}). {ex['title']}. {ex['venue']}. {ex['url']}"})
    write(META / "papers_master.csv", master)

    # ---------------- literature_matrix.csv
    fields27 = ["title", "authors", "year", "venue", "type_status", "doi", "official_url", "oa_pdf_url", "domain", "objective", "research_questions",
                "geography", "data_sources", "period", "frequency", "sample_size", "target", "features", "methods", "architecture", "validation",
                "metrics", "main_findings", "limitations_authors", "limitations_critical", "relevance", "adaptable_contribution"]
    keymap = dict(domain="domain", objective="objective", research_questions="rq", geography="geo", data_sources="data", period="period",
                  frequency="freq", sample_size="n", target="target", features="features", methods="methods", architecture="arch",
                  validation="validation", metrics="metrics", main_findings="findings", limitations_authors="lim_auth",
                  limitations_critical="lim_crit", relevance="relevance", adaptable_contribution="adapt")
    matrix = []
    by_key = {m["id"]: m for m in master}
    for it in inc:
        m = by_key[it["id"]]
        row = {"id": it["id"], "tier": it["tier"], "theme": m["theme"], "title": m["title"], "authors": m["authors"], "year": m["year"],
               "venue": m["venue"], "type_status": m["publication_type"], "doi": it["doi"], "official_url": m["official_url"],
               "oa_pdf_url": m["open_access_pdf_url"], "analysis_basis": m["analysis_basis"]}
        ex = EXTRACT.get(it["doi"]) or next((v for k, v in EXTRACT.items() if not it["doi"] and it["key"].startswith(k)), None)
        ft = FT.get(it["doi"], {})
        if ex:
            for f, k in keymap.items():
                row[f] = ft.get(k, ex.get(k, "Not reported"))
            if m["analysis_basis"] == "Full text":
                row = {k: (v.replace("Not reported in abstract", "Not reported in the paper sections read") if isinstance(v, str) else v) for k, v in row.items()}
            row["evidence_location"] = ft.get("evidence", "Abstract" if m["analysis_basis"] == "Abstract only" else "Title and bibliographic metadata only")
        else:
            role = ROLES.get(it["doi"] or it["key"], "Supporting reference")
            for f in keymap:
                row[f] = "Not extracted (supporting reference)"
            row["domain"] = m["theme"]
            row["relevance"] = "Supporting: " + role
            row["adaptable_contribution"] = role.split(":", 1)[-1].strip()
            row["evidence_location"] = ft.get("evidence", "Abstract/metadata (role only)")
        row["abstract_source"] = it.get("abstract_source", "OpenAlex/Crossref/arXiv record")
        matrix.append(row)
    write(ANA / "literature_matrix.csv", matrix, ["id", "tier", "theme", "analysis_basis"] + fields27 + ["evidence_location", "abstract_source"])

    # ---------------- methodology_comparison.csv
    meth = []
    doi2id = {it["doi"]: it for it in inc if it["doi"]}
    doi2id.update({k: it for it in inc for k in ["measuringthesecurityofexternalenergysupp"] if it["key"].startswith(k)})
    for doi, vals in CODES.items():
        it = doi2id[doi]
        meth.append({"id": it["id"], "study": short_cite(it), "doi": doi, "basis": by_key[it["id"]]["analysis_basis"], **dict(zip(COLS, vals))})
    write(ANA / "methodology_comparison.csv", meth)

    # ---------------- research_gaps.csv
    gap_rows = []
    for g in GAPS:
        sc = g["scores"]
        cites = [short_cite(doi2id[d]) if d in doi2id else d for d in g["strongest"]]
        cites = [c if cites.count(c) == 1 else c.replace(")", f", '{' '.join(doi2id[d]['title'].split()[:3])}...')") for c, d in zip(cites, g["strongest"])]
        gap_rows.append({"gap": g["id"], "name": g["name"], "strongest_existing_work": "; ".join(cites),
                         "what_is_achieved": g["achieved"], "what_remains": g["remaining"], "search_evidence": g["search_evidence"],
                         "novelty_verdict": g["novelty"], "data_feasibility": g["feasibility"], "proposed_experiment": g["experiment"],
                         **{f"score_{k}": v for k, v in sc.items()}, "score_total": sum(sc.values()), "rationale": g["rationale"]})
    ranked = sorted(gap_rows, key=lambda r: -r["score_total"])
    for r_, row in enumerate(ranked, 1):
        row["rank"] = r_
    write(ANA / "research_gaps.csv", gap_rows)

    # ---------------- search_log.csv
    key_of = {}
    pres = {r["key"]: r for r in csv.DictReader(open(RAW / "prescreen.csv", encoding="utf-8"))}
    title_to_key = {norm_title(r["title"]): r["key"] for r in pres.values()}
    inc_keys = {it["key"] for it in inc}
    per_query = defaultdict(set)
    for name, parse in PARSERS.items():
        p = RAW / f"{name}.jsonl"
        if not p.exists():
            continue
        for line in open(p, encoding="utf-8"):
            row = json.loads(line)
            rec = parse(row["item"])
            if not rec["title"]:
                continue
            k = title_to_key.get(norm_title(rec["title"])) or rec["doi"]
            per_query[(name, row["query"])].add(k)
    logs = []
    dbname = {"openalex": "OpenAlex API", "crossref": "Crossref REST API", "semanticscholar": "Semantic Scholar Graph API", "arxiv": "arXiv API",
              "snowball": "OpenAlex citation graph", "openalex_citations": "OpenAlex citation graph", "gapcheck_crossref": "Crossref REST API (gap check)",
              "crossref_gapcheck": "Crossref REST API (gap check)"}
    for f in sorted(RAW.glob("search_log_*.csv")):
        src = f.stem.replace("search_log_", "")
        for r in csv.DictReader(open(f, encoding="utf-8")):
            raw_src = {"snowball": "snowball", "gapcheck_local": "gapcheck_crossref", "gapcheck": "gapcheck"}.get(src, src)
            keys = per_query.get((raw_src, r["query"]), set())
            logs.append({"database": dbname.get(r["database"], r["database"]), "theme": r["theme"], "query": r["query"], "search_date": r["search_date"],
                         "total_hits_reported": r["total_hits"], "records_retrieved": r["retrieved"], "status": r["status"],
                         "unique_records_mapped": len(keys),
                         "screened_title_abstract": sum(1 for k in keys if pres.get(k, {}).get("prescreen") == "manual"),
                         "included": len(keys & inc_keys)})
    manual_rows = [
        ("OpenAlex API (Boolean gap check, run 1)", "A_global_landlocked", 'landlocked AND (oil OR petroleum OR fuel) AND (forecast OR forecasting OR prediction)', "12", "12",
         "ok; raw file overwritten on rerun; count recorded in session notes; 0 on-target"),
        ("OpenAlex API (Boolean gap check, run 1)", "A_global_landlocked", '(petroleum OR "oil products" OR ... fuel) AND import* AND forecast* AND (cross-country OR panel OR "global model" OR "multiple countries")', "30", "30",
         "ok; raw overwritten; 0 forecasting physical imports across countries"),
        ("OpenAlex API (Boolean gap check, run 1)", "A_global_landlocked", "(Comtrade) AND (forecast OR forecasting OR prediction)", ">=50", "50", "ok; raw overwritten"),
        ("OpenAlex API (Boolean gap check, run 1)", "B_dl_vs_gbm", "(LightGBM OR XGBoost OR gradient boosting) AND (LSTM OR GRU OR N-BEATS OR deep learning) AND (import OR imports OR international trade) AND forecast*", "36", "36", "ok; raw overwritten"),
        ("OpenAlex API (Boolean gap check, run 1)", "B_dl_vs_gbm", "(LightGBM OR XGBoost OR gradient boosting) AND (LSTM OR GRU OR deep learning) AND (oil OR petroleum OR fuel OR gasoline) AND (demand OR consumption OR import) AND forecasting", "49", "49", "ok; raw overwritten"),
        ("Google Scholar (browser)", "all", '"petroleum import" forecasting', "", "0", "blocked: 'unusual traffic' CAPTCHA page (HTTP 429); not bypassed; platform not used"),
        ("Connected Papers (browser)", "D_global_dl", "Principles and algorithms for forecasting groups of time series (Montero-Manso & Hyndman)", "", "28", "ok; 28-record related-paper list saved"),
        ("Connected Papers (browser)", "B_supply_disruption", "Measuring energy security: diversification of oil and gas supplies (Cohen et al.)", "", "0", "free monthly graph limit reached; list not retrievable"),
        ("ScienceDirect (browser)", "abstract retrieval", "doi.org/10.1016/j.ijforecast.2020.11.009", "", "0", "CAPTCHA; not bypassed; Elsevier records covered through Crossref/OpenAlex metadata and RePEc abstracts"),
        ("SpringerLink (browser)", "abstract retrieval", "6 Springer/Bloomsbury landing pages", "", "6", "abstracts read on public pages"),
        ("RePEc/IDEAS (web)", "abstract retrieval", "15 Elsevier article pages", "", "13", "13 abstracts; 1 without abstract; 1 page not found"),
        ("CORE", "all", "-", "", "0", "not used: API requires a key; open-access copies located through OpenAlex/Semantic Scholar instead"),
        ("SSRN / Wiley / IEEE Xplore / SpringerLink", "all", "covered through Crossref and OpenAlex indexing", "", "", "no separate platform searches; records appear via DOI registries"),
        ("Web search (institutional)", "institutional", "IEA oil security; World Bank Kyrgyz energy; UNCTAD LLDC energy; IMF oil import bill; IEA Central Asia; Comtrade release timing", "", "6 queries", "institutional reports listed separately"),
        ("Semantic Scholar Graph API", "all", "remaining 66 queries and batch abstract lookups", "", "", "HTTP 429 for most requests; 16 core queries attempted slowly"),
    ]
    for db, th, q, tot, ret, st in manual_rows:
        logs.append({"database": db, "theme": th, "query": q, "search_date": "2026-11-07", "total_hits_reported": tot, "records_retrieved": ret,
                     "status": st, "unique_records_mapped": "", "screened_title_abstract": "", "included": ""})
    write(META / "search_log.csv", logs)

    # ---------------- excluded_papers.csv
    reason_text = {
        "E0_off_topic_title": "Rule-based title screen: no combination of topic concepts (fuel/energy, trade, forecasting, security, region, method) in the title",
        "E1_electricity_renewables": "Rule-based: electricity, renewables or grid load (different target system)",
        "E2_price_or_financial_target": "Rule-based: price, volatility or financial-market target rather than volumes",
        "E3_upstream_or_engineering": "Rule-based: upstream production or engineering",
        "E4_non_research_item": "Rule-based: editorial, dataset deposit or non-research item",
        "E5_other_commodity_or_domain": "Rule-based: other commodity or domain (food, water, minerals, coal, gas)",
        "G0_gapcheck_result_without_boolean_match": "Crossref gap-check result that did not satisfy the gap's Boolean condition",
        "M0_title_abstract": "Manual title/abstract screening: not relevant to the review questions",
    }
    seeds_x = json.load(open(RAW / "excluded_seeds.json", encoding="utf-8"))
    excluded = []
    for k, r in pres.items():
        if k in inc_keys:
            continue
        code = r["prescreen"]
        if code == "manual":
            code = "M0_title_abstract"
            if r["doi"] in seeds_x:
                code = seeds_x[r["doi"]]
        excluded.append({"key": k, "title": r["title"], "year": r["year"], "venue": r["venue"], "doi": r["doi"], "found_in": r["found_in"],
                         "stage": "Rule-based title pre-screen" if code.startswith(("E", "G")) else ("Seed screening" if code.startswith("X") else "Manual title/abstract screening"),
                         "reason_code": code, "reason": reason_text.get(code, {"X1_upstream_well_production_out_of_scope": "Proposal seed outside this review's scope (well production)",
                                                                                 "X2_station_level_sales_redundant": "Proposal seed: station-level sales, redundant with included fuel-demand studies"}.get(code, code))})
    write(META / "excluded_papers.csv", excluded)

    # ---------------- stats
    dedup = json.load(open(RAW / "dedup_stats.json"))
    stats = {
        "raw_records_by_source": dedup["raw_records_by_source"], "raw_records_total": dedup["raw_records_total"],
        "connected_papers_records": 28, "unique_records": dedup["unique_works"], "multi_version_groups": dedup["multi_version_groups"],
        "prescreen": Counter(r["prescreen"] for r in pres.values()), "manual_screened": sum(1 for r in pres.values() if r["prescreen"] == "manual"),
        "included": len(inc), "core": sum(i["tier"] == "core" for i in inc), "support": sum(i["tier"] == "support" for i in inc),
        "institutional_extra": len(INSTITUTIONAL_EXTRA), "basis": Counter(m["analysis_basis"] for m in master[:len(inc)]),
        "types": Counter(m["publication_type"] for m in master), "themes": Counter(m["theme"] for m in master[:len(inc)]),
        "downloads": Counter(d["status"] for d in downloads.values()), "years": Counter(str(m["year"]) for m in master[:len(inc)]),
        "theme_year": Counter(f"{m['theme']}|{m['year']}" for m in master[:len(inc)]),
        "verification": Counter(i["verification"]["crossref_status"] for i in inc), "excluded": len(excluded),
        "search_queries_api": sum(1 for l in logs if l["unique_records_mapped"] != ""),
    }
    json.dump(stats, open(RAW / "stats.json", "w", encoding="utf-8"), indent=1, default=dict)
    print(json.dumps({k: stats[k] for k in ("raw_records_total", "unique_records", "manual_screened", "included", "core", "basis", "downloads", "excluded")}, default=dict, indent=1))


def short_cite(it):
    v = it.get("verification", {})
    auth = person_authors(v)
    fams = [a["family"] for a in auth] or [f for f, _ in parse_names(it["authors"])]
    year = year_of(it)
    if not fams:
        return f"{it['title'][:40]} ({year})"
    return f"{fams[0]} ({year})" if len(fams) == 1 else (f"{fams[0]} & {fams[1]} ({year})" if len(fams) == 2 else f"{fams[0]} et al. ({year})")


def write(path, rows, fields=None):
    fields = fields or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
