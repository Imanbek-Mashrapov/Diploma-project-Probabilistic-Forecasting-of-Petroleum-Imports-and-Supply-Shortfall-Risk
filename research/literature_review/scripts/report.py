"""Stage 8c: build final/Literature_Review_and_Research_Gap_Analysis.docx from the analysis files.

Citations in the prose use [[p:...]] / [[n:...]] markers (see report_text.py) and are resolved against
metadata/papers_master.csv; an unknown marker raises an error so no unverified source can enter the text.
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).parent))
from build_outputs import DATACITE, parse_names, person_authors, year_of  # noqa: E402
from gaps import CONTRIBUTIONS, GAPS  # noqa: E402
from report_text import *  # noqa: E402,F403

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "metadata" / "raw"
OUT = ROOT / "final" / "Literature_Review_and_Research_Gap_Analysis.docx"
FIG = ROOT / "final" / "figures"
ACCENT = RGBColor(0x1F, 0x3A, 0x5F)
FONT = "Calibri"
STATS = json.load(open(RAW / "stats.json", encoding="utf-8"))
DATACITE.update(json.load(open(RAW / "datacite_verification.json", encoding="utf-8")))

# ----------------------------------------------------------------- bibliography and citation resolution
VER = {i["key"]: i for i in json.load(open(RAW / "verified.json", encoding="utf-8"))}
MASTER = list(csv.DictReader(open(ROOT / "metadata" / "papers_master.csv", encoding="utf-8-sig")))
INST_SHORT = {"iea_kyrgyzstan_2022": ("International Energy Agency", "2022"), "iea_kyrgyzstan_profile": ("International Energy Agency", "2020"),
              "unctad_2026_hormuz": ("UNCTAD", "2026"), "imf_wp_06_171": ("International Monetary Fund", "2006"),
              "imf_wp_11_194": ("Rasmussen & Roitman", "2011"), "un_ohrlls_lldc": ("UN-OHRLLS", "n.d.")}
REF = {}   # citation id -> dict(fams, year, apa, sortkey)
for m in MASTER:
    if m["theme"] == "Institutional report":
        fam, yr = INST_SHORT[m["id"]]
        REF[m["id"]] = dict(fams=[fam], year=yr, apa=m["apa7"], sort=fam.lower())
        continue
    it = next(i for i in VER.values() if (i["doi"] and i["doi"] == m["doi"]) or (not i["doi"] and i["title"] == m["title"]) or
              (not i["doi"] and (i["verification"].get("crossref_title") == m["title"])))
    auth = person_authors(it["verification"])
    fams = [a["family"] for a in auth if a["family"]] or [f for f, _ in parse_names(it["authors"]) if f]
    cid = it["doi"] or it["key"]
    REF[cid] = dict(fams=fams or ["Anonymous"], year=str(year_of(it)), apa=m["apa7"], sort=(fams[0] if fams else "zzz").lower())
# a/b suffixes for identical author-year labels
groups = defaultdict(list)
for cid, r in REF.items():
    lab = (r["fams"][0], len(r["fams"]) > 2 and "etal" or "|".join(r["fams"][:2]), r["year"])
    groups[lab].append(cid)
for lab, ids in groups.items():
    if len(ids) > 1:
        for s_, cid in zip("abcdefgh", sorted(ids, key=lambda c: REF[c]["apa"])):
            REF[cid]["year"] += s_
            REF[cid]["apa"] = re.sub(r"\((\d{4})\)", rf"(\g<1>{s_})", REF[cid]["apa"], count=1)
USED = set()


def resolve(cid):
    if cid not in REF:
        hits = [k for k in REF if k.startswith(cid)]
        if len(hits) != 1:
            raise KeyError(f"citation not in verified bibliography: {cid}")
        cid = hits[0]
    USED.add(cid)
    return REF[cid]


def label(r, narrative):
    f, y = r["fams"], r["year"]
    amp = "and" if narrative else "&"
    name = f[0] if len(f) == 1 else (f"{f[0]} {amp} {f[1]}" if len(f) == 2 else f"{f[0]} et al.")
    return f"{name} ({y})" if narrative else f"{name}, {y}"


def cite_text(text):
    def rep(m):
        kind, ids = m.group(1), m.group(2).split("|")
        refs = [resolve(i) for i in ids]
        if kind == "n":
            return "; ".join(label(r, True) for r in refs)
        return "(" + "; ".join(label(r, False) for r in refs) + ")"
    return re.sub(r"\[\[(p|n):([^\]]+)\]\]", rep, text)


# ----------------------------------------------------------------- document helpers
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, side, Cm(2.2))


def style_font(st, size, bold=False, color=None):
    st.font.name, st.font.size, st.font.bold = FONT, Pt(size), bold
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), FONT)
    if color is not None:
        st.font.color.rgb = color


style_font(doc.styles["Normal"], 10.5)
doc.styles["Normal"].paragraph_format.space_after = Pt(5)
doc.styles["Normal"].paragraph_format.line_spacing = 1.12
for name, size, b, a in (("Title", 22, 0, 6), ("Heading 1", 15, 18, 6), ("Heading 2", 12.5, 12, 4), ("Heading 3", 11, 8, 3)):
    st = doc.styles[name]
    style_font(st, size, True, ACCENT)
    st.paragraph_format.space_before, st.paragraph_format.space_after, st.paragraph_format.keep_with_next = Pt(b), Pt(a), True
for name in ("List Bullet", "List Number"):
    style_font(doc.styles[name], 10.5)


def runs(p, text, size=None, italic=False, color=None):
    for i, part in enumerate(cite_text(text).split("**")):
        if part:
            r = p.add_run(part)
            r.bold = i % 2 == 1
            r.italic = italic
            if size:
                r.font.size = Pt(size)
            if color:
                r.font.color.rgb = color


def P(text, size=None, italic=False, align=None, after=None, color=None):
    p = doc.add_paragraph()
    runs(p, text, size, italic, color)
    if align:
        p.alignment = align
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def H(text, level):
    return doc.add_heading(text, level=level)


def B(items, style="List Bullet"):
    for t in items:
        p = doc.add_paragraph(style=style)
        runs(p, t)
        p.paragraph_format.space_after = Pt(2)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def T(headers, rows, widths, size=8.5, zebra=True):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ""
        runs(c.paragraphs[0], f"**{h}**", size, color=RGBColor(0xFF, 0xFF, 0xFF)); shade(c, "1F3A5F")
    trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            for li, line in enumerate(str(val).split("\n")):
                p = cells[i].paragraphs[0] if li == 0 else cells[i].add_paragraph()
                p.paragraph_format.space_after = Pt(1); p.paragraph_format.line_spacing = 1.0
                runs(p, line, size)
            if zebra and ri % 2 == 1:
                shade(cells[i], "F2F5F9")
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return t


def QA(rows, w1=4.0, w2=12.6):
    T(["Question", "Evidence and assessment"], rows, [w1, w2], size=9, zebra=True)


def figure(path, caption, width=16.2):
    doc.add_picture(str(path), width=Cm(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    P(caption, size=9, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, color=RGBColor(0x55, 0x55, 0x55))


def caption(text):
    P(text, size=9, italic=True, color=RGBColor(0x55, 0x55, 0x55), after=2)


# ----------------------------------------------------------------- content
S = STATS
pres = S["prescreen"]
basis = S["basis"]
dl = S["downloads"]
meth = list(csv.DictReader(open(ROOT / "analysis" / "methodology_comparison.csv", encoding="utf-8-sig")))
gaps_csv = {r["gap"]: r for r in csv.DictReader(open(ROOT / "analysis" / "research_gaps.csv", encoding="utf-8-sig"))}
n_meth = len(meth)
cnt = lambda col: sum(1 for r in meth if r[col].startswith(("Yes", "Partly", "Compared")))  # noqa: E731

# Title page
P("ALA-TOO INTERNATIONAL UNIVERSITY · Faculty of Engineering and Informatics", size=10, align=WD_ALIGN_PARAGRAPH.CENTER, color=ACCENT, after=30)
doc.add_paragraph("Literature Review and Research Gap Analysis", style="Title").alignment = WD_ALIGN_PARAGRAPH.CENTER
P("for the diploma project", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, after=4)
P("**Probabilistic Forecasting of Petroleum Imports and Supply-Shortfall Risk in Landlocked Economies: "
  "Global Deep Learning versus Gradient Boosting, with a Case Study of Kyrgyzstan**", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, after=24)
T(["Item", "Value"], [
    ["Review type", "Systematic, reproducible literature search with critical synthesis and gap analysis"],
    ["Search date", "7 November 2026"],
    ["Records identified / unique", f"{S['raw_records_total']:,} / {S['unique_records']:,}"],
    ["Included works", f"{S['included']} ({S['core']} core with detailed extraction, {S['support']} supporting) + {S['institutional_extra']} institutional reports"],
    ["Analysis basis", f"full text {basis.get('Full text', 0)}, abstract only {basis.get('Abstract only', 0)}, metadata only {basis.get('Metadata only', 0)}"],
    ["Citation style", "APA 7th edition"],
    ["Supporting files", "research/literature_review/metadata/ and analysis/ (CSV), papers/ (open-licence PDFs), scripts/ (code)"],
    ["AI use", "Search, screening support, extraction and drafting were carried out with an AI assistant (Claude). All records were verified against DOI registries; see Section 2.6."],
], [4.5, 12.1], zebra=False)
doc.add_page_break()

# ===================================================================== 1
H("1. Executive summary", 1)
P(f"This review asked what is genuinely missing in research on forecasting petroleum imports and import-supply stress, and where a "
  f"project built on a monthly UN Comtrade panel of about 22 landlocked economies (44 country-product series) can make a defensible contribution. "
  f"Four scholarly APIs (OpenAlex, Crossref, Semantic Scholar, arXiv), citation chasing from 12 anchor papers, Connected Papers, "
  f"publisher and RePEc pages and institutional sources were searched with 79 queries in eight themes. {S['raw_records_total']:,} records "
  f"reduced to {S['unique_records']:,} unique works; {S['manual_screened']:,} were screened by title and abstract and {S['included']} were included. "
  f"Every included record was verified against Crossref, DataCite or doi.org, or against the publisher's PDF for the three records without a "
  f"registered DOI; no retraction or correction notices were found.")
P("**Main findings**", after=2)
B([
    f"**Petroleum-import forecasting is a thin and methodologically weak literature.** Every petroleum-import forecasting study found is single-country "
    f"(Indonesia, Taiwan, Thailand, China, India, Tanzania, Nepal), most use annual data or import values rather than physical monthly volumes, "
    f"and all report point forecasts only [[p:{INDO_ANN}|{INDO_GRU}|{TAIWAN}|{CHINA_ML}|{TANZ}]]. Of {n_meth} coded forecasting and early-warning "
    f"studies, only {cnt('naive_baseline')} report a naive benchmark and {cnt('significance_test')} test accuracy differences formally (Figure 3).",
    f"**Global forecasting and the boosting-versus-deep-learning question are well researched in general.** Global models are theoretically "
    f"justified [[p:{MMH}|{HEW_SIM}]], and boosted trees dominate on small and tabular data [[p:{TREES}|{GRINS}|{ELSAYED}]]. Comparing them on a new "
    f"target is useful but incremental.",
    f"**Calibrated probabilistic forecasts and publication-lag-aware evaluation are the clearest gaps.** Probabilistic forecasting is mature "
    f"in electricity and retail [[p:{GEF}|{M5U}]] but absent from national fuel-import forecasting; real-time evaluation is established in "
    f"macroeconomics and oil prices [[p:{CROUSH}|{BK}]] but not for Comtrade-based commodity imports, whose reporter-specific release lags reach several months.",
    f"**The early-warning idea is not new.** [[n:{KWON}]] already predict product-level import disruptions out of sample, define events as "
    f"a persistent quantity shortfall with rising unit values, and show that concentration rankings perform below the base rate. "
    f"The project must cite this as its nearest prior work and present its warning component as an extension.",
    f"**Landlocked importers are not studied as a group** in forecasting research; landlocked-country work concentrates on trade costs and transit "
    f"[[p:{LLDC}|{KG_TRADE}]]. Group status becomes a scientific finding only if tested against a non-landlocked control group.",
])
P("**Strongest defensible contribution.** A lag-aware, calibrated probabilistic forecasting benchmark for monthly refined-fuel imports "
  "across landlocked economies, evaluated as the data were actually available, with a test of whether its predictive distributions give "
  "earlier and more reliable warnings of import-supply stress than concentration screening. Local-versus-global and boosting-versus-deep-learning "
  "comparisons should be reported as controlled benchmarks inside this design, not as the headline.", after=4)
P("**Priority actions.** (1) Reframe the title and research questions around calibration and as-of evaluation; (2) treat Kwon and Jeong (2026) "
  "and VP-OilEx-STFN (2026) as the closest prior work; (3) build the release-date availability table before any modelling; "
  "(4) define 'import-supply stress' and never equate it with domestic shortage; (5) strengthen the event list with dated, sourced episodes.")

# ===================================================================== 2
H("2. Research scope and review methodology", 1)
H("2.1 Objectives", 2)
B(["Establish the state of research on petroleum and energy import forecasting, supply-disruption prediction, probabilistic and global forecasting, "
   "geopolitical and supplier-structure effects, and landlocked-economy energy security.",
   "Identify gaps that are genuine, defensible and testable with the project's data, without assuming that the proposed topic is novel.",
   "Assess each proposed contribution and recommend a methodology and experiment matrix that the evidence supports."])
H("2.2 Review questions", 2)
B(["RQ-R1. Which methods, data and evaluation designs are used to forecast petroleum imports and related supply quantities?",
   "RQ-R2. What evidence exists on global (cross-series) models and on gradient boosting versus deep learning for short economic panels?",
   "RQ-R3. Are probabilistic, calibrated and publication-lag-aware evaluations used for trade or energy-import forecasts?",
   "RQ-R4. Do supplier concentration, prices and geopolitical risk add predictive (not only explanatory) value?",
   "RQ-R5. Have forecasts been turned into early warnings of import-supply stress, and how were warnings validated?",
   "RQ-R6. Are landlocked economies studied as a distinct group in energy-import research?"], style="List Number")
H("2.3 Protocol", 2)
P("The review followed eight stages: (1) inspection of the project's data and proposal; (2) execution of the search strategy through APIs; "
  "(3) normalisation, deduplication and preprint-journal matching; (4) rule-based title pre-screening followed by manual title/abstract screening; "
  "(5) verification against DOI registries and retrieval of open-licence full texts; (6) evidence extraction; (7) thematic synthesis and gap analysis; "
  "(8) assembly of deliverables. All code is in scripts/ and all intermediate files in metadata/raw/, so every count in this document can be regenerated.")
H("2.4 Inclusion and exclusion criteria", 2)
T(["Include if the work contributes to at least one of:", "Exclude if:"], [[
    "1. petroleum or energy import forecasting\n2. energy supply-chain disruption prediction\n3. probabilistic forecasting\n4. global time-series forecasting\n"
    "5. deep learning vs gradient boosting comparisons\n6. geopolitical and macroeconomic risk modelling\n7. supplier concentration and energy security\n"
    "8. international trade-flow forecasting\n9. energy security in landlocked economies\n+ foundational methods regardless of age",
    "• unrelated to the review questions or only mentions a keyword\n• duplicate or alternative version (merged, history kept)\n"
    "• no verifiable bibliographic information\n• predatory or low-quality signals (judged case by case)\n"
    "• electricity/renewables, price/financial targets, upstream production or other commodities, unless methodologically central"]], [8.3, 8.3], zebra=False)
H("2.5 Tiers and analysis basis", 2)
P(f"**Core** works ({S['core']}) received the full 27-field extraction in analysis/literature_matrix.csv. **Supporting** works ({S['support']}) "
  "are cited for one specific point (a method, a test, a data fact), recorded in the matrix as a role statement; their other fields are marked "
  "'Not extracted (supporting reference)'. The **analysis basis** of every record is stated explicitly: **full text** (PDF or HTML read, with page "
  "or section locations in the matrix), **abstract only**, or **metadata only** (no abstract accessible without bypassing access controls; no "
  "claims are drawn from these beyond their titles).")
H("2.6 Integrity rules and AI use", 2)
B(["No paper, author, DOI, result or quotation was generated without a source record; every in-text citation in this document is resolved "
   "automatically against the verified bibliography, and an unknown citation stops the build.",
   "Google Scholar, ScienceDirect and Semantic Scholar web pages returned CAPTCHAs or rate limits; these were not bypassed (Section 3.3).",
   "PDFs were stored only under Creative Commons, public-domain or arXiv terms; other open copies are recorded as links.",
   "Citation counts were not used to judge quality. Preprints, working papers and commentaries are labelled as such.",
   "This review was prepared with an AI assistant. The faculty guideline limits combined plagiarism and AI-generated text to 30% and requires AI "
   "prompt records: use this document as a structured evidence base, re-read key sources, and write the thesis chapter in your own words."])

# ===================================================================== 3
H("3. Search strategy and databases", 1)
H("3.1 Query groups", 2)
P("Queries covered the eight themes requested (A-G) plus neighbouring topics discovered during screening (H). Synonyms were spread across queries "
  "because the APIs rank by relevance rather than strict Boolean matching; strict Boolean conditions were applied in the gap checks (Section 3.4).")
from search import QUERIES  # noqa: E402
T(["Theme", "Queries (79)"], [[k.replace("_", " "), "; ".join(v)] for k, v in QUERIES.items()], [3.2, 13.4], size=8)
H("3.2 Sources, access mode and yield", 2)
src = S["raw_records_by_source"]
T(["Source", "Access", "Records", "Status and notes"], [
    ["OpenAlex", "REST API, 79 queries x 25 results", f"{src['openalex']:,}", "Complete. Later Boolean gap-check runs hit HTTP 429 (daily limit)"],
    ["Crossref", "REST API, 79 queries x 20 results", f"{src['crossref']:,}", "Complete; also used for DOI verification of every included record"],
    ["arXiv", "API, 79 queries x 10 results", f"{src['arxiv']}", "Complete"],
    ["Semantic Scholar", "Graph API", f"{src['semanticscholar']}", "Unauthenticated pool returned HTTP 429 for most requests; 16 core queries attempted slowly"],
    ["OpenAlex citation graph", "Backward and forward citations of 12 anchors", f"{src['snowball']}", "Anchors: global forecasting, GPR, diversification indices, oil-import dependence, trade networks, M5, DeepAR, Kyrgyz energy security"],
    ["Proposal seed list", "66 references from the topic proposal", f"{src['seedrecords']}", "All 66 re-verified; screened like other records (17 excluded as out of scope)"],
    ["Crossref gap checks", "Top 200 per gap + Boolean filter", f"{src['gapcheck_crossref']:,}", "Only Boolean matches were read"],
    ["Connected Papers", "Browser", "28", "One graph retrieved (Montero-Manso & Hyndman); second blocked by the free monthly limit"],
    ["Google Scholar", "Browser", "0", "Blocked by an 'unusual traffic' CAPTCHA; not bypassed; not used"],
    ["ScienceDirect", "Browser", "0", "CAPTCHA on article pages; Elsevier metadata obtained through Crossref/OpenAlex and abstracts through RePEc/IDEAS"],
    ["SpringerLink, Bloomsbury", "Public landing pages (browser)", "6 abstracts", "Abstracts read; no paywalled content"],
    ["RePEc / IDEAS", "Public pages", "13 abstracts", "Used for Elsevier economics and forecasting journals"],
    ["CORE", "-", "0", "Not used: the API requires a key; open copies were found through OpenAlex and Semantic Scholar"],
    ["SSRN, Wiley, IEEE Xplore, SpringerLink", "Via Crossref/OpenAlex", "-", "Covered through DOI registries rather than separate platform searches"],
    ["IEA, World Bank, IMF, UNCTAD, UN", "Web search, 6 queries", "6 reports", "Classified separately as institutional reports"],
], [3.2, 3.6, 1.7, 8.1], size=8)
H("3.3 Access limitations", 2)
P("Three platforms could not be searched as intended. Google Scholar and ScienceDirect presented CAPTCHA challenges and the Semantic Scholar API "
  "was rate-limited throughout the day. OpenAlex, which carried most of the search, began returning HTTP 429 after about 2,000 requests, which "
  "interrupted the Boolean gap checks. Consequently: (i) recall for grey literature indexed mainly by Google Scholar is lower than a full "
  "systematic review would achieve; (ii) 35 included records are analysed at metadata level only; (iii) the gap checks rely on a documented "
  "fallback (Section 3.4). These limitations are repeated in Section 13.")
H("3.4 Gap-specific Boolean checks", 2)
P("For each candidate gap a strict Boolean condition was defined (for example: landlocked AND (oil OR petroleum OR fuel) AND (forecast OR predict)). "
  "Five conditions were run as database-side counts in OpenAlex before the rate limit (results: 12, 30, at least 50, 36 and 49 records). All eight "
  "conditions were then applied to the titles and abstracts of the full deduplicated pool plus the Crossref top 200 for each gap, and every match "
  "was read. The results are reported with each gap in Section 9 and in metadata/raw/gap_matches.json.")

# ===================================================================== 4
H("4. Screening and selection", 1)
figure(FIG / "fig1_prisma.png", "Figure 1. Flow of records through identification, deduplication, screening and inclusion.", 13.5)
P("**Deduplication.** Records were merged when they shared a DOI or a normalised title. Preprint and journal versions were merged into "
  f"{S['multi_version_groups']} version groups; the journal DOI is used for citation and all version DOIs are kept in papers_master.csv.")
P("**Rule-based title pre-screen.** Long abstracts mention almost every keyword, so the pre-screen used titles only. A record went to manual "
  "screening if its title combined topic concepts (for example fuel or energy with trade, forecasting or security; forecasting with probabilistic, "
  "global or evaluation terms; trade with forecasting, geopolitics or data revisions; landlocked or Central Asian countries with energy or trade). "
  "Records whose titles were about electricity, prices, upstream production or other commodities were excluded unless they also mentioned imports "
  "or global models. Two random samples of excluded titles (110 records) were read to check the rules; the rules were widened after the first "
  "sample and the second sample contained only isolated relevant items, which were added manually (for example the XGBoost and LightGBM "
  "papers and a study of Comtrade data quality).")
P(f"**Manual screening.** {S['manual_screened']:,} titles were read, with abstracts consulted where needed. {S['included']} works were included. "
  "Decisions are stored by stable key (DOI or normalised title) so that rebuilding the candidate table does not change them.")
T(["Exclusion reason", "Records"], [
    ["Off-topic title (rule)", f"{pres.get('E0_off_topic_title', 0):,}"],
    ["Electricity, renewables or grid load (rule)", f"{pres.get('E1_electricity_renewables', 0)}"],
    ["Price, volatility or financial target (rule)", f"{pres.get('E2_price_or_financial_target', 0)}"],
    ["Other commodity, upstream production or non-research item (rule)", f"{pres.get('E3_upstream_or_engineering', 0) + pres.get('E4_non_research_item', 0) + pres.get('E5_other_commodity_or_domain', 0)}"],
    ["Crossref gap-check result without Boolean match", f"{pres.get('G0_gapcheck_result_without_boolean_match', 0):,}"],
    ["Manual title/abstract screening (incl. 17 out-of-scope proposal seeds)", f"{S['manual_screened'] - (S['included'] - 3):,}"],
    ["Total excluded (metadata/excluded_papers.csv)", f"{S['excluded']:,}"],
], [12.6, 4.0], zebra=True)
P("**Verification.** "
  f"{S['verification'].get('resolved', 0)} DOIs resolved at Crossref with title similarity of at least 0.85; "
  f"{S['verification'].get('doi_not_in_crossref', 0)} are DataCite or other-agency DOIs (arXiv, SSRN, Zenodo, a university thesis, JaLC), of which 18 resolved at DataCite, "
  "one through doi.org, and one (an Indonesian journal article) is not registered with any agency and was verified from the journal's PDF. "
  "Two works have no DOI (LightGBM at NeurIPS 2017; a 2015 IJEEP article on Central Asian energy security, read in full). No retraction or "
  "correction notices were found in Crossref update metadata.")

# ===================================================================== 5
H("5. Overview of the selected literature", 1)
themes = Counter(m["theme"] for m in MASTER if m["theme"] != "Institutional report")
tiers = Counter((m["theme"], m["tier"]) for m in MASTER if m["theme"] != "Institutional report")
T(["Theme", "Core", "Supporting", "Total"], [[t, tiers[(t, "core")], tiers[(t, "support")], n] for t, n in themes.most_common()] +
  [["Institutional reports (separate class)", "-", S["institutional_extra"], S["institutional_extra"]]], [9.6, 2.2, 2.4, 2.4], zebra=True)
types = Counter(m["publication_type"] for m in MASTER)
T(["Publication type and status", "Works"], [[k, v] for k, v in types.most_common()], [12.6, 4.0], zebra=True)
figure(FIG / "fig2_years_themes.png", "Figure 2. Included works by publication period and theme.", 15.5)
P("Three features of the corpus matter for interpretation. First, it is recent: the largest share of included works appeared in 2025-2026, "
  "and many of those are preprints or working papers (SSRN, arXiv, Research Square) that have not completed peer review. Second, the "
  "methodological core (global models, scoring rules, real-time data, competitions) is older and published in established forecasting journals, "
  "whereas the applied petroleum-import studies are scattered across regional journals and conference chapters. Third, landlocked and "
  "Central Asian sources are mostly descriptive policy analyses rather than quantitative forecasting studies.")

# ===================================================================== 6
H("6. Thematic literature review", 1)
P("Each theme answers the same seven questions. Statements are labelled where they are the reviewer's interpretation rather than a "
  "finding reported by a study.")

H("6.1 Petroleum and energy import forecasting", 2)
P(f"The direct literature consists of single-country studies of import values, volumes, import demand or import dependence. Indonesia's oil and gas "
  f"imports were forecast with an MLP on annual customs volumes [[p:{INDO_ANN}]], with a GRU on monthly values [[p:{INDO_GRU}]] and with SARIMA "
  f"[[p:{INDO_SAR}]]; Taiwan's crude import demand with single- and two-stage hybrids [[p:{TAIWAN}]]; China's oil import demand with grey relational "
  f"analysis and machine learning [[p:{CHINA_ML}]]; China's and India's import dependence with grey-ARIMA and related hybrids "
  f"[[p:{CHINA_DEP}|{INDIA_DEP}|{CHINA_FUZZY}]]; and India's crude and product imports with ARIMA [[p:{INDIA_ARIMA}]]. Econometric import-demand "
  f"studies estimate elasticities rather than forecasts [[p:{TANZ}|{THAI_IMP}|{NEPAL}]]. The closest cross-country study forecasts annual oil "
  f"demand (not imports) for 30 countries [[p:{ZHU30}]]. Two 2026 works move closer to the project: an oil-export nowcasting model that masks "
  f"inputs by release calendar [[p:{VPOIL}]] and a Comtrade-based Temporal Fusion Transformer for raw-material trade flows [[p:{TFT_TRADE}]].")
QA([
    ["1. What has been researched?", "Single-country forecasts of import value, volume, demand and dependence; elasticity estimation; nowcasting of oil exports; DL on Comtrade trade flows."],
    ["2. Common approaches", "ARIMA/SARIMA, grey models and grey hybrids, MLP/GRU/LSTM, SVR, ARDL/ECM."],
    ["3. Common datasets", "National statistics and customs (BPS, Indiastat/PPAC, China yearbooks, Nepal Oil Corporation); WDI; UN Comtrade only in trade-flow studies."],
    ["4. Strongest results", f"No method is consistently superior. SARIMA matched or beat a neural network for Indian gasoline and diesel [[p:{MSHSD}]]; NNAR had the lowest RMSE for Indian diesel [[p:{HSD}]]; SVR was most accurate and stable in the 30-country panel [[p:{ZHU30}]]. Interpretation: results are not comparable because targets, frequencies and metrics differ."],
    ["5. Recurring limitations", "Value instead of physical volume; annual or interpolated data [[p:" + KHAJOUI + "]]; single holdouts; no naive benchmark; MAPE, R2 or 'accuracy %' as metrics; contemporaneous explanatory variables that would not be known at forecast time; no intervals."],
    ["6. Open questions", "Monthly physical refined-product imports across countries; calibrated uncertainty; evaluation as of data release; behaviour in supply shocks."],
    ["7. Methods to adapt", f"Information-set discipline from out-of-time trade forecasting [[p:{DYAD}]]; release-calendar masking [[p:{VPOIL}]]; strong classical benchmarks (seasonal naive, SARIMA) as in [[n:{VPOIL}]]."],
])

H("6.2 Energy supply security and disruption", 2)
P(f"Energy security research is dominated by indices: diversification of supply sources [[p:{COHEN}]], composite supply-risk indices with political "
  f"and transit risk [[p:{LECOQ}]], vulnerability indices for oil importers [[p:{GUPTA}]] and risk-weighted diversification [[p:{YANGIDX}]]. "
  f"[[n:{ANG}]] reviewed 104 such studies and found definitions to be contextual and indices hard to compare. Early-warning work ranges from "
  f"index systems [[p:{EWS_CHINA}]] to a logit model of world energy crises defined by an energy-market pressure index above two standard "
  f"deviations, evaluated in sample [[p:{EWS_WORLD}]], and to boosted forecasts turned into probabilistic shortfall alarms for renewable "
  f"electricity [[p:{EWS_RES}]]. The decisive study for this project is [[n:{KWON}]] (full text read): monthly HS6 customs data for Korea, 440 "
  f"proxy disruption onsets, walk-forward validation with a label-confirmation embargo, and a direct comparison with concentration screening.")
QA([
    ["1. What has been researched?", "Index-based measurement of supply security and vulnerability; network resilience of oil trade; a few predictive early-warning systems; observed fuel shortages only in hurricane evacuations [[p:" + HURR + "|" + HURR2 + "]]."],
    ["2. Common approaches", "HHI and Shannon-type diversification, PCA composites, factor analysis, logit EWS, network simulation, EVT/copula risk models."],
    ["3. Common datasets", "BP/IEA statistics, national balances, bilateral trade (Comtrade, customs), country-risk ratings."],
    ["4. Strongest results", f"Out-of-sample: ML watchlists reached about 1.7 times the base-rate precision in the top 5%, captured 31% of onsets with a median 9-month lead, while concentration rankings performed below the base rate [[p:{KWON}]] (p. 1, sec. 4.2)."],
    ["5. Recurring limitations", "Indices are rarely validated against later disruptions; in-sample 'accuracy' claims [[p:" + EWS_WORLD + "]]; disruptions are proxies because no event register exists [[p:" + KWON + "]]."],
    ["6. Open questions", "Whether forecast distributions, rather than ranking scores, give usable warnings; how warnings behave when data arrive months late; refined-fuel and landlocked settings."],
    ["7. Methods to adapt", f"Quantity-plus-unit-value event signature, embargoed walk-forward evaluation, event-level capture and lead time [[p:{KWON}]]; PR-AUC, Brier score and reliability for alarms [[p:{EWS_RES}]]; ROC-based evaluation of warning indicators [[p:{EWI_ROC}]]."],
])

H("6.3 Global forecasting models", 2)
P(f"[[n:{MMH}]] show that global models are not more restrictive than local ones and that local complexity grows with the number of series. "
  f"[[n:{HEW_SIM}]] find in simulations that global models handle many short series well and that LightGBM matches RNNs at much lower cost "
  f"(full text, sec. 7). [[n:{SEMEN}]] report that cross-learning is promising when information can be extracted from large, diverse datasets. "
  f"For short cross-country panels, recent evidence is mixed: pooling or shrinkage reduced MASE by 15-28% on Eurostat panels, but the gain "
  f"reversed in simulations once cross-country heterogeneity was appreciable [[p:{POOL}]] (sec. 7); a multi-country TFT beat regressions for "
  f"25 OECD GDP series, especially in turbulent periods [[p:{LABORDA}]].")
QA([
    ["1. What has been researched?", "Theory of locality vs globality, simulation studies, large benchmarks (M4, Monash), panels in macro and retail."],
    ["2. Common approaches", "Pooled linear AR, LightGBM on lag features, RNN/N-BEATS/DeepAR trained across series, partial pooling and clustering."],
    ["3. Common datasets", "M3, M4, M5, Tourism, Monash archive; Eurostat and OECD panels."],
    ["4. Strongest results", "Global models outperform local ones on related series and often on heterogeneous ones; pooling benefits shrink as heterogeneity grows."],
    ["5. Recurring limitations", "Benchmarks have many long series; small heterogeneous economic panels are rarely studied."],
    ["6. Open questions", "Whether pooling helps with 22-44 weakly co-moving fuel-import series; which form of partial pooling is best."],
    ["7. Methods to adapt", f"Validation-selected shrinkage between local and global [[p:{POOL}]]; leave-one-country-out transfer [[p:{METAZERO}]]; retraining schedules and forecast stability [[p:{RETRAIN}|{STAB}]]."],
])
P(f"**Disagreement.** Simulation and benchmark evidence favours global models [[p:{MMH}|{HEW_SIM}]], while the short-panel study finds the "
  f"advantage reversing under heterogeneity [[p:{POOL}]]. Interpretation: both are consistent; the project's weak co-movement makes a small or null "
  f"pooling gain plausible, so a partially pooled model should be a first-class candidate.")

H("6.4 Deep learning versus gradient boosting", 2)
P(f"Tree-based methods dominated the M5 competition [[p:{M5A}|{TREES}]]; DL combinations beat other methods on some M3 subsets but at high "
  f"computational cost [[p:{MAKR22}]]; a window-based gradient-boosted tree competes with many DL models [[p:{ELSAYED}]]; and trees remain state of "
  f"the art on medium-sized tabular data [[p:{GRINS}]]. A one-layer linear model matched Transformers on long-horizon benchmarks [[p:{ZENG}]]. "
  f"In energy, XGBoost reached an R2 of 0.95 against 0.20 for LSTM on annual Thai transport energy [[p:{THAI_DL}]]; in trade, CatBoost was best "
  f"for out-of-time bilateral flows [[p:{DYAD}]] and regression-based boosting variants were best for real-time world-trade nowcasts [[p:{NOWWT}]].")
QA([
    ["1. What has been researched?", "Large competitions and benchmarks, plus many small domain comparisons."],
    ["2. Common approaches", "LightGBM/XGBoost/CatBoost on lagged features vs LSTM/GRU/TCN/N-BEATS/TFT/DeepAR."],
    ["3. Common datasets", "M-competitions, LTSF benchmarks, tabular benchmark suites; small national energy series."],
    ["4. Strongest results", "Boosting wins or ties on small and tabular data; DL gains appear with many long series, ensembles and large budgets."],
    ["5. Recurring limitations", "Unequal tuning budgets, different information sets, single splits, R2 as a metric, no statistical tests."],
    ["6. Open questions", "Behaviour in shock windows; calibration of probabilistic outputs; whether small neural models add value in pooled 5,000-observation panels."],
    ["7. Methods to adapt", "Identical features and windows for both families; equal tuning budgets; compute cost reporting; stratification by normal and shock periods."],
])
P(f"**Disagreement.** [[n:{LABORDA}]] found a TFT superior on a 25-country panel, while [[n:{THAI_DL}]] found LSTM far worse than XGBoost on a "
  f"single short series. Interpretation: the difference is consistent with data volume and with cross-series training, not evidence that one family is universally better.")

H("6.5 Probabilistic forecasting and calibration", 2)
P(f"The evaluation framework is settled: forecasts should maximise sharpness subject to calibration [[p:{GNEIT07}]] and be scored with strictly "
  f"proper rules such as the CRPS and interval score [[p:{GR07}]]. Electricity forecasting has a probabilistic benchmark tradition (GEFCom2014; "
  f"581 participants) [[p:{GEF}]], retail has nine-quantile evaluation in M5 Uncertainty [[p:{M5U}]], and there are model-agnostic calibration "
  f"layers: conformalised quantile regression [[p:{CQR}]], its ensemble time-series variant [[p:{ENCQR}]], adaptive conformal inference [[p:{ACI}]] "
  f"and ensemble conformal intervals [[p:{ENBPI}]]. In fuels, probabilistic outputs are rare: a simulation-based distribution of military fuel demand "
  f"[[p:{LOBO}]] and a 2026 preprint using quantile regression for aviation-fuel inventory planning [[p:{AVIATION}]].")
QA([
    ["1. What has been researched?", "Theory of scoring and calibration; competitions; conformal methods; quantile boosting and quantile RNNs [[p:" + QGBM + "|" + MQRNN + "]]."],
    ["2. Common approaches", "Quantile regression (linear, boosting, neural), likelihood-based DL (DeepAR), conformal wrappers, bootstrap intervals."],
    ["3. Common datasets", "Electricity load, price, wind, solar; retail sales."],
    ["4. Strongest results", "Quantile-based ensembles win GEFCom-type tracks; conformal layers restore coverage on top of any model."],
    ["5. Recurring limitations", "Exchangeability assumptions; coverage estimates are noisy on short test windows; shock periods break calibration."],
    ["6. Open questions", "Calibration of fuel-import forecasts, especially in supply shocks; tail quantiles for shortfall risk [[p:" + XQGB + "]]."],
    ["7. Methods to adapt", "Pinball loss over several quantiles, CRPS, empirical coverage with confidence bands, PIT histograms, rolling-origin conformal calibration [[p:" + ROCONF + "]]."],
])

H("6.6 Geopolitical risk and external shocks", 2)
P(f"The news-based GPR index [[p:{GPR}]] is the standard measure. Monthly local projections show that GPR shocks lower China's energy import "
  f"volumes in the short run and raise them later, with crude oil adjusting most [[p:{LINZ}]]; a survival analysis of 300,971 HS6 energy-import "
  f"spells finds that exporter-country GPR raises the hazard of a relationship ending, more for petroleum than for coal or gas [[p:{PENG}]]. "
  f"GPR's predictive contribution has been tested for crude-oil volatility [[p:{DELIS}]], not for import volumes. Refined products can become "
  f"scarce even when crude is available, and crack spreads rose more where pre-war product import dependence was higher [[p:{EVENTCRACK}]]. "
  f"For Kyrgyzstan, sanctions on Russia changed the structure of trade: EU exports to Armenia, Kazakhstan and the Kyrgyz Republic rose sharply after "
  f"2022, especially for sanctioned goods [[p:{ROUNDABOUT}]], and mirror-data discrepancies surged after 2019 [[p:{DISCREP}]].")
QA([
    ["1. What has been researched?", "Explanatory effects of GPR on imports, prices and trade-relationship survival; sanctions and rerouting."],
    ["2. Common approaches", "VAR/local projections, survival models, event studies, gravity and difference-in-differences."],
    ["3. Common datasets", "GPR index, Comtrade/HS6 trade, customs data, price series."],
    ["4. Strongest results", "Robust explanatory links between exporter GPR and petroleum import disruption hazard [[p:" + PENG + "]]."],
    ["5. Recurring limitations", "Explanatory designs do not test out-of-sample value; the global GPR index barely varies across small importers."],
    ["6. Open questions", "Does supplier-weighted GPR improve volume forecasts once own history is known? Kwon and Jeong list GPR as a natural next predictor (p. 11)."],
    ["7. Methods to adapt", "Supplier-share-weighted country GPR; event dummies for documented export bans; structural-break flags for 2022 [[p:" + BAIPERRON + "]]."],
])

H("6.7 Supplier concentration", 2)
P(f"HHI-type concentration is the default exposure measure [[p:{COHEN}|{SERBIA}]], often adjusted for political, transit or export-capacity risk "
  f"[[p:{LECOQ}|{YANGIDX}]]. Its predictive validity was untested until [[n:{KWON}]], who found no monotonic relation between concentration quintiles "
  f"and later disruption onsets and little contribution of the concentration block once flow dynamics were known (p. 11). Supply-side information "
  f"can predict imports when it captures partners' expectations: an 'Import Climate' built from partners' export expectations beat domestic "
  f"indicators for six advanced economies [[p:{GRIMME}]].")
QA([
    ["1. What has been researched?", "Measurement of concentration and risk-weighted diversification; one out-of-sample test of concentration as a warning signal."],
    ["2. Common approaches", "HHI, Shannon index, risk-weighted indices, network centrality."],
    ["3. Common datasets", "Bilateral trade by partner; country-risk ratings."],
    ["4. Strongest results", "Concentration describes structural exposure but does not rank short-horizon disruption risk [[p:" + KWON + "]]."],
    ["5. Recurring limitations", "Static indices; no link to subsequent events."],
    ["6. Open questions", "Whether concentration interacts with landlocked status, where a single overland corridor matters."],
    ["7. Methods to adapt", "Concentration as a benchmark ranking and as an ablation block, not as the main signal."],
])

H("6.8 Landlocked economies and Kyrgyzstan", 2)
P(f"Landlocked-country research concentrates on trade costs, transit corridors and connectivity [[p:{LLDC}|{KG_TRADE}]]. Central Asian energy "
  f"security has been quantified with risky-external-supply indices, which put the regional oil index well above the EU's [[p:{AKHMETOV}]], and "
  f"discussed for Kyrgyzstan and Tajikistan as hydropower producers [[p:{KOSOWSKA}]]. Import-dependence studies exist for Nepal "
  f"[[p:{NEPAL}|{NEPAL2}]] and a fuel-demand forecast exists for Chad [[p:{CHAD}]]. Institutional sources state that over 90% of Kyrgyz oil "
  f"products are imported, mainly from Russia and Kazakhstan [[p:{IEA_PROF}|{IEA_KG}]], and that refined products make up most of vulnerable "
  f"economies' net oil imports [[p:{UNCTAD}]]. Kyrgyz trade statistics show mirror discrepancies with China [[p:{MIRROR_KG}|{MIRROR_KG2}]].")
QA([
    ["1. What has been researched?", "Trade costs and transit; descriptive or index-based energy security; single-country import dependence."],
    ["2. Common approaches", "Policy analysis, indices, gravity models."],
    ["3. Common datasets", "WTO trade policy reviews, IEA balances, national statistics."],
    ["4. Strongest results", "Central Asian oil supply risk is high relative to the EU [[p:" + AKHMETOV + "]]."],
    ["5. Recurring limitations", "No forecasting; no cross-country quantitative comparison of fuel imports."],
    ["6. Open questions", "Whether landlocked importers share forecastable dynamics distinct from coastal small importers."],
    ["7. Methods to adapt", "Use the UN-OHRLLS list to define the group [[p:" + OHRLLS + "]]; add a non-landlocked control group to test group-specific effects."],
])

H("6.9 Trade-data timeliness and quality (emerged during the review)", 2)
P(f"Real-time data change forecasting conclusions in macroeconomics [[p:{CROUSH}|{CROUSH_HB}|{RTD09}]]. In oil, [[n:{BK}]] built monthly vintages "
  f"and showed real-time VAR forecasts of the real oil price beat the no-change forecast. A 2026 study finds that the ML edge in inflation "
  f"forecasting survives real-time data while the identity of important predictors changes [[p:{FOG}]] (full text, sec. 6). Trade-balance "
  f"announcements are revised [[p:{TRADEREV}]], as are UN energy statistics [[p:{UNREV}]], and the 'ragged edge' of unequal availability is a "
  f"long-standing problem [[p:{RAGGED}]]. Comtrade records contain statistical imbalances between headings and subheadings, frequent for fossil "
  f"fuels [[p:{COMTRADE_IMB}]], and imputed quantities and unit values [[p:{COMTRADE_UV}]]. Interpretation: these facts make publication-lag-aware "
  f"and data-quality-aware evaluation a substantive part of the research, not a technicality.")

# ===================================================================== 7
H("7. Comparative methodology analysis", 1)
figure(FIG / "fig3_methods_profile.png", f"Figure 3. Design features of {n_meth} coded forecasting and early-warning studies "
       "(analysis/methodology_comparison.csv). 'Not reported' is not counted as 'no'.", 16)
rows = [[r["study"], r["target_type"], r["frequency"], r["scope"], r["global"], r["probabilistic"], r["validation"], r["real_time"]] for r in meth]
T(["Study", "Target", "Freq.", "Scope", "Global", "Probabilistic", "Validation", "Lag-aware"], rows, [2.6, 2.6, 1.4, 1.9, 1.5, 1.7, 2.6, 2.2], size=7)
caption("Table 7.1. Coded designs (NR = not reported in the source read). Full table with models, baselines, tests and metrics: analysis/methodology_comparison.csv.")
P("**Established patterns (supported by several studies).** Studies of petroleum imports and fuel demand use single-country models, single "
  "holdouts and scale-dependent or percentage metrics; probabilistic outputs and lag-aware evaluation are almost absent outside electricity, "
  "macroeconomics and the two 2026 trade/oil works. **Individual results (one study each).** Release-calendar masking improved oil-export "
  "nowcasts [[p:" + VPOIL + "]]; dynamic indicators beat concentration screening [[p:" + KWON + "]]; partial pooling beat country-specific "
  "estimation on short panels [[p:" + POOL + "]]. **Interpretation.** The project can differentiate itself mainly through evaluation "
  "design: lag-aware rolling origins, strong naive and seasonal baselines, probabilistic scores and formal tests.")

# ===================================================================== 8
H("8. Critical evaluation of previous research", 1)
B([
    f"**Target mismatch.** Import values mix price and quantity; annual data hide the monthly dynamics of supply shocks; demand and consumption are "
    f"not imports. The few studies that forecast physical import volumes use annual data [[p:{INDO_ANN}|{INDIA_ARIMA}]].",
    f"**Information leakage.** Several studies forecast with contemporaneous explanatory variables (GDP, prices, macro aggregates) that are not "
    f"known at the forecast date [[p:{TAIWAN}|{ZHU30}|{CHINA_ML}]]. The out-of-time trade study is an exception: it restricts inputs to information "
    f"available before the forecast year [[p:{DYAD}]].",
    f"**Weak evaluation.** Single train/test splits, interpolated samples (annual data turned into 200 'seasonal' points with a 75/25 split and "
    f"'99% accuracy' [[p:{KHAJOUI}]]), MAPE-only or R2-based comparisons [[p:{MSHSD}|{TFT_TRADE}|{THAI_DL}]], and in-sample claims for early "
    f"warning [[p:{EWS_WORLD}]]. Established forecasting practice recommends rolling origins, scale-free errors and tests "
    f"[[p:{TASHMAN}|{MASE}|{PITFALLS}|{DM}|{HLN}]].",
    "**Title-content mismatch.** One conference chapter titled as AI-based forecasting reports a regression and elasticity analysis in its "
    f"abstract [[p:{THAI_IMP}]]. Interpretation: titles alone overstate the amount of ML import forecasting in the literature.",
    f"**Proxy events.** No register of fuel-supply disruptions exists; studies infer events from quantities and prices [[p:{KWON}]] or use "
    f"crowdsourced station data in special cases [[p:{HURR}]]. Import declines can reflect demand, stockpiling, smuggling, rerouting or reporting "
    "changes, not shortage.",
    f"**Data quality is rarely examined.** Comtrade imbalances and mirror discrepancies are documented [[p:{COMTRADE_IMB}|{DISCREP}]] but "
    "forecasting studies do not test how they affect accuracy.",
    "**Correlation versus causation.** GPR-import studies estimate associations or impulse responses; they do not establish that GPR "
    "improves forecasts, and they do not identify causal effects for small importers.",
])

# ===================================================================== 9
H("9. Research gap identification", 1)
P("Each gap was tested against the strongest related work and a Boolean search (Section 3.4). Gaps are not declared novel by default; where "
  "existing work covers part of a gap, the remaining opportunity is stated precisely.")
for g in GAPS:
    r = gaps_csv[g["id"]]
    H(f"Gap {g['id']}. {g['name']}", 2)
    T(["Aspect", "Assessment"], [
        ["1. Strongest existing work", "; ".join(f"[[n:{d}]]" for d in g["strongest"])],
        ["2. What it achieved", g["achieved"]],
        ["3. What remains", g["remaining"]],
        ["4. Search evidence", g["search_evidence"]],
        ["5. Novelty verdict", g["novelty"]],
        ["6. Can the project's data address it?", g["feasibility"]],
        ["7. Proposed experiment", g["experiment"]],
        ["Scores (1-5)", ", ".join(f"{k} {v}" for k, v in g["scores"].items()) + f"; total {sum(g['scores'].values())}; rank {r['rank']}"],
    ], [4.0, 12.6], size=8.5)

# ===================================================================== 10
H("10. Assessment of the proposed contributions", 1)
T(["Proposed contribution", "Classification", "Reasoning"], [[a, b, c] for a, b, c in CONTRIBUTIONS], [4.6, 3.2, 8.8], size=8.5)
P("Interpretation: contributions 4 and 5 together form the defensible core; 2, 3 and 6 are the controlled experiments that make the core "
  "credible; 7 is the applied payoff and should be presented with explicit limits; 1 and 8 are enabling resources rather than scientific claims.")

# ===================================================================== 11
H("11. Recommended research methodology", 1)
P("The recommendations use the project's own data audit (petroleum-import-risk research feasibility report, snapshot 2 November 2026): "
  "44 usable series in 22 countries (5,549 observations); a Tier-1 evaluation set of 22 series in 13 countries (3,021 observations); Kyrgyzstan "
  "Tier-1 for gasoline and distillates; weak co-movement between series; median Kyrgyz publication lag of about 72 days and at least 200 days for "
  "8 of 22 countries; and indications that 2025-2026 Kyrgyz records are first releases later revised upward.")
recs = [
    ("Research design", "Pre-registered forecasting experiment with fixed hypotheses, rolling-origin evaluation and a final test block run once; the review's gap ranking puts calibration (C) and lag-aware evaluation (D) first."),
    ("Dataset construction", "Keep the audited pipeline; add a release-date table per reporter-month (first availability, from the Comtrade availability endpoint and repeated snapshots); keep heading-vs-lines and partner-vs-World checks [[p:" + COMTRADE_IMB + "]]."),
    ("Target variable", "Monthly physical import mass (tonnes) for gasoline (HS 271012) and the distillate aggregate; value and unit value as secondary series; log or scaled transforms for pooling."),
    ("Feature engineering", "Own lags and seasonal lags, rolling statistics, partner shares and HHI, supplier-weighted GPR [[p:" + GPR + "|" + PENG + "]], Brent with release lags, documented export-ban dummies, release-age indicators [[p:" + VPOIL + "]]. Every feature is lagged to its release date."),
    ("Local vs global", "Local ETS/SARIMA and per-series LightGBM; global LightGBM with country and product identifiers; partially pooled (validation-shrunk) variant [[p:" + POOL + "]]; leave-one-country-out transfer."),
    ("Statistical baselines", "Naive, seasonal naive, 12-month mean, ETS, SARIMA; report every model relative to seasonal naive (MASE) [[p:" + MASE + "]]."),
    ("Gradient boosting", "LightGBM with quantile objectives (5-95%) and early stopping on a time-ordered validation block [[p:" + LGBM + "|" + QGBM + "]]."),
    ("Deep learning", "Only small global models justified by about 5,500 observations: GRU (16-64 units), TCN, N-BEATS ensemble [[p:" + NBEATS + "]], DeepAR-style likelihood output [[p:" + DEEPAR + "]]; a compact TFT only if validation supports it [[p:" + TFT + "]]; no large Transformers [[p:" + ZENG + "]]."),
    ("Probabilistic forecasting", "Quantile sets (0.05-0.95) or full predictive distributions; scored with pinball loss and CRPS [[p:" + GR07 + "]]."),
    ("Calibration", "Empirical coverage at 80% and 95% with binomial confidence bands, PIT histograms [[p:" + GNEIT07 + "]]; conformal recalibration within each rolling origin [[p:" + ENCQR + "|" + ACI + "|" + ROCONF + "]]."),
    ("Supply-stress event definition", "Define 'import-supply stress' as an observed import quantity below the 10th (and 5th) percentile of the forecast distribution issued with the realistic lag, preferably jointly with a rise in unit value [[p:" + KWON + "]]. Validate against a dated, sourced list of export bans and station shortages. **Do not equate import shortfall with domestic shortage**: stocks, smuggling, rerouting through third countries [[p:" + ROUNDABOUT + "]] and demand shifts can all lower recorded imports."),
    ("Rolling-origin validation", "Expanding window, monthly origins from 2023 (or 2021 for more test points), tuning only on pre-origin data [[p:" + TASHMAN + "|" + BERGCV + "]]; a final untouched block."),
    ("Publication-lag-aware backtesting", "At each origin use only reporter-months published by that date; compare with an oracle design that uses all data to quantify the timing penalty [[p:" + CROUSH + "|" + BK + "]]; evaluate 2025-2026 on first releases and on later snapshots."),
    ("Forecast horizons", "h = 1, 3 and 6 months from the last observed month, and the corresponding real-time horizons once lags are added; next-three-month totals for stress alerts."),
    ("Significance testing", "Diebold-Mariano with HLN small-sample correction [[p:" + DM + "|" + HLN + "]] or fixed-smoothing asymptotics [[p:" + FIXSM + "]]; panel versions across countries [[p:" + PEPA + "]]; Holm correction across hypotheses; model confidence sets as a robustness check."),
    ("Ablation studies", "Feature blocks (own history; + supplier structure; + Brent; + GPR; + event dummies); pooling scope (Kyrgyzstan only; Tier 1; Tier 1+2; + non-landlocked controls); model family."),
    ("Robustness checks", "Mirror-based targets; exclusion of revision-affected months; alternative event thresholds; structural breaks [[p:" + BAIPERRON + "]]; Tier-1 vs Tier-1+2 training; random-seed variability for neural models."),
]
T(["Element", "Recommendation"], [[a, b] for a, b in recs], [3.6, 13.0], size=8.5)

# ===================================================================== 12
H("12. Proposed experimental design", 1)
P("The matrix reorders the original four research questions so that the strongest gaps lead. All hypotheses are tested at 5% with Holm correction.")
T(["RQ", "Hypothesis", "Independent variables", "Models", "Baselines", "Metrics", "Expected evidence"], [
    ["RQ1 Calibration (Gap C)", "H1: quantile LightGBM with conformal recalibration achieves nominal 80%/95% coverage (within binomial bands) and lower CRPS than unrecalibrated models", "Model; calibration method; shock vs normal window", "Quantile LightGBM, GRU likelihood, N-BEATS ensemble; CQR/EnCQR", "Seasonal naive with empirical intervals; ETS intervals", "Pinball loss, CRPS, coverage, width, PIT", "Coverage tables by window; reliability plots"],
    ["RQ2 Lag-aware evaluation (Gap D)", "H2: accuracy measured as-of release dates is significantly worse than under oracle availability, and model rankings change", "Availability regime (oracle vs as-of); horizon", "All models", "Same models under oracle data", "MASE, CRPS differences; rank correlation", "Timing penalty by horizon and country lag"],
    ["RQ3 Local vs global (Gap A)", "H3: global or partially pooled models reduce Kyrgyz MASE by at least 5% vs the best local model at h = 3", "Pooling scope", "Local ETS/SARIMA/LightGBM; global LightGBM; shrunk; global GRU", "Seasonal naive", "MASE, CRPS; HLN-DM", "Pooling gain with confidence intervals; LOCO transfer"],
    ["RQ4 Boosting vs DL (Gap B)", "H4: neural models do not beat LightGBM overall but may in shock windows", "Model family; window type", "LightGBM vs GRU/TCN/N-BEATS (+TFT optional)", "Seasonal naive", "MASE, CRPS by window; compute time", "Stratified error table"],
    ["RQ5 Feature value (Gap E)", "H5: supplier structure, Brent and GPR each reduce pinball loss by at least 3% for high-dependence series", "Feature blocks", "Global LightGBM (fixed)", "Own-history-only model", "Pinball loss differences; DM", "Ablation table; null results reported"],
    ["RQ6 Warning skill (Gap F)", "H6: forecast-based stress probabilities give higher PR-AUC and recall at a fixed alert budget than HHI ranking and a quantity-only rule", "Signal type; lead time", "Probabilistic forecasts -> exceedance probability", "HHI ranking [[p:" + KWON + "]]; quantity rule; climatology", "PR-AUC, recall at budget, Brier, lead time", "Event-level capture against sourced event list"],
    ["RQ7 Landlocked group (Gap G, optional)", "H7: pooling within landlocked importers helps more than pooling with non-landlocked small importers", "Training population", "Global LightGBM", "Same with control group", "MASE, CRPS", "Comparison of pooling gains"],
], [2.2, 3.5, 2.0, 2.4, 2.0, 2.2, 2.3], size=7.5)

# ===================================================================== 13
H("13. Final scientific verdict and recommendations", 1)
figure(FIG / "fig4_gap_scores.png", "Figure 4. Reviewer scores of candidate gaps on six criteria (1-5). Scores are judgements explained in Section 9, not computed indices.", 16)
ranked = sorted(gaps_csv.values(), key=lambda r: int(r["rank"]))
T(["Rank", "Gap", "Total", "Nov.", "Prac.", "Evid.", "Data", "Exp.", "Pub."],
  [[r["rank"], f"{r['gap']}. {r['name'][:60]}", r["score_total"], r["score_novelty"], r["score_practical"], r["score_evidence"], r["score_data"],
    r["score_experiment"], r["score_publication"]] for r in ranked], [1.1, 8.0, 1.2, 1.05, 1.05, 1.05, 1.05, 1.05, 1.05], size=8)
caption("Nov. = novelty; Prac. = practical significance; Evid. = evidence from existing literature; Data = data feasibility; Exp. = experimental feasibility; Pub. = publication value.")
QA([
    ["1. What is already well researched?", "Global vs local forecasting theory and benchmarks; boosting vs deep learning on small data; scoring rules and calibration; real-time data in macroeconomics; energy-security indices; explanatory effects of GPR on imports."],
    ["2. What has received limited attention?", "Monthly physical fuel-import forecasting; cross-country fuel-import panels; predictive (not explanatory) value of supplier structure and GPR; trade-data quality in forecasting."],
    ["3. What appears genuinely underexplored?", "Calibrated probabilistic forecasts of fuel imports; evaluation as of reporter-specific Comtrade release dates; forecast-distribution-based warnings for landlocked fuel importers."],
    ["4. Which proposed contributions are defensible?", "Probabilistic forecasting with calibration (4) and lag-aware backtesting (5) as the core; local vs global (2), boosting vs DL (3) and feature ablations (6) as controlled benchmarks; early warning (7) as a qualified extension."],
    ["5. What should be modified?", "Move 'Global Deep Learning versus Gradient Boosting' out of the title; replace 'supply-shortfall risk' with 'import-supply stress'; position Kwon and Jeong (2026) as nearest prior work; drop claims that the early-warning concept or global modelling is new; add a control group if the landlocked framing is kept as a finding."],
    ["6. Strongest possible contribution", "A reproducible, lag-aware, calibrated probabilistic benchmark for monthly refined-fuel imports across landlocked economies, showing (a) how much accuracy is lost to publication delays, (b) whether intervals remain calibrated in supply shocks, and (c) whether forecast distributions warn of import-supply stress earlier than concentration screening."],
    ["7. Priorities for publication quality", "Pre-specified hypotheses; strong baselines; probabilistic scores with tests; honest null results; data and code release (subject to Comtrade terms); a sourced event list; explicit limits of import data."],
    ["8. Risks that could invalidate the work", "Revisions of recent Kyrgyz data larger than the shock signal; too few events for warning metrics; leakage through features not lagged to release dates; heterogeneity that makes pooling useless; misreading import shortfall as shortage; dependence on unverified 2026 preprints."],
    ["9. Is it feasible with the available data?", "Yes for RQ1-RQ5 (data audited, panel sufficient for small models); partly for RQ6 (event scarcity); optional RQ7 needs additional control countries from the same pipeline."],
    ["10. What to do next", "(1) build the release-date table and a second Comtrade snapshot; (2) freeze cleaning rules and hypotheses with the supervisor; (3) compile the sourced event list; (4) run baselines and the oracle-vs-as-of comparison before any neural model; (5) re-read the full texts of the core sources you cite, especially those analysed at abstract or metadata level here."],
])
P("**Final recommendation.** Pursue the direction ranked first and second above as one study. A suggested working title: "
  "'Real-Time Probabilistic Forecasting of Refined-Fuel Imports and Import-Supply Stress in Landlocked Economies: Evidence from a "
  "Cross-Country Panel with a Kyrgyzstan Case Study'. Keep the comparison of global deep learning and gradient boosting as a research "
  "question inside the study, where a null result remains informative.")
H("13.1 Limitations of this review", 2)
B(["Google Scholar, ScienceDirect and most Semantic Scholar requests were unavailable, so grey literature and some Elsevier abstracts are under-covered.",
   f"{basis.get('Metadata only', 0)} included works are analysed at metadata level and {basis.get('Abstract only', 0)} at abstract level; only "
   f"{basis.get('Full text', 0)} were read in full. Findings attributed to abstract-only works should be checked in full text before citing.",
   "Boolean gap checks in OpenAlex were interrupted by rate limits; five database-side counts were obtained, and the rest rely on a local filter of the pool and Crossref top results.",
   "Screening was performed by one reviewer (with AI assistance) without independent double screening; the rule-based pre-screen was checked on samples only.",
   "Many of the most relevant works are 2025-2026 preprints or working papers whose results may change in peer review.",
   "Gap scores are judgements; another reviewer could weight the criteria differently."])

# ===================================================================== 14
H("14. Bibliography", 1)
P("APA 7th edition. Includes every work included in the review and the institutional reports; DOIs are given as links. Work types and "
  "peer-review status are listed in metadata/papers_master.csv.", size=9.5, italic=True)
for cid in sorted(REF, key=lambda c: (REF[c]["sort"], REF[c]["year"])):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.9)
    p.paragraph_format.first_line_indent = Cm(-0.9)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(REF[cid]["apa"])
    r.font.size = Pt(9)

# ===================================================================== appendices
H("Appendix A. Execution report", 1)
T(["Measure", "Value"], [
    ["Total records discovered", f"{S['raw_records_total']:,} (+28 Connected Papers cross-check records)"],
    ["Unique publications after deduplication", f"{S['unique_records']:,}"],
    ["Screened by title/abstract", f"{S['manual_screened']:,}"],
    ["Included in analysis", f"{S['included']} ({S['core']} core with detailed extraction) + {S['institutional_extra']} institutional reports"],
    ["Full-text papers reviewed", f"{basis.get('Full text', 0)}"],
    ["Abstract-only records", f"{basis.get('Abstract only', 0)}"],
    ["Metadata-only records", f"{basis.get('Metadata only', 0)}"],
    ["Downloaded PDFs (open licence)", f"{dl.get('downloaded', 0)}"],
    ["Research gaps assessed", f"{len(GAPS)} (A-G requested, H added)"],
    ["Excluded records with reasons", f"{S['excluded']:,}"],
], [7.0, 9.6])
H("Appendix B. Deliverables", 1)
T(["File", "Content"], [
    ["final/Literature_Review_and_Research_Gap_Analysis.docx", "This document"],
    ["metadata/papers_master.csv", "Included works with verified metadata, type/status, analysis basis, PDF status and APA reference"],
    ["metadata/search_log.csv", "Every query with database, date, hits, retrieved, screened and included counts, plus non-API sources"],
    ["metadata/excluded_papers.csv", "Every excluded unique record with stage and reason"],
    ["analysis/literature_matrix.csv", "27-field extraction with evidence locations"],
    ["analysis/research_gaps.csv", "Gap assessment, scores and ranks"],
    ["analysis/methodology_comparison.csv", "Coded designs of forecasting and early-warning studies"],
    ["papers/<theme>/", f"{dl.get('downloaded', 0)} open-licence PDFs"],
    ["metadata/raw/, scripts/", "Raw API responses, intermediate tables and the code that regenerates every output"],
], [7.4, 9.2], size=8.5)

doc.save(OUT)

# resolve citation markers in the gap table so the CSV reads the same as the report
gap_path = ROOT / "analysis" / "research_gaps.csv"
gap_rows = list(csv.DictReader(open(gap_path, encoding="utf-8-sig")))
with open(gap_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, list(gap_rows[0].keys()))
    w.writeheader()
    strongest = {g["id"]: "; ".join(f"[[n:{d}]]" for d in g["strongest"]) for g in GAPS}
    w.writerows([{k: cite_text(strongest[r["gap"]] if k == "strongest_existing_work" else v) for k, v in r.items()} for r in gap_rows])
unused = [c for c in REF if c not in USED]
print("saved", OUT, "| citations used:", len(USED), "| bibliography:", len(REF))
