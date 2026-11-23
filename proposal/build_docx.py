# -*- coding: utf-8 -*-
"""Build the thesis proposal .docx following the Chapter 1 manuscript guidelines."""
import re
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK, WD_TAB_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import content as C
import body
C.B = body.B

FONT = "Times New Roman"
OUT = "Mashrapov_Thesis_Proposal.docx"
doc = Document()

# ---------------------------------------------------------------- styles
def set_font(style, size=12, bold=None, italic=None):
    style.font.name = FONT
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None: style.font.bold = bold
    if italic is not None: style.font.italic = italic
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), FONT)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]

def pfmt(style, before=0, after=0, double=True, indent=None, align=WD_ALIGN_PARAGRAPH.LEFT, keep=False):
    f = style.paragraph_format
    f.space_before = Pt(before); f.space_after = Pt(after)
    f.line_spacing_rule = WD_LINE_SPACING.DOUBLE if double else WD_LINE_SPACING.SINGLE
    f.first_line_indent = indent
    f.alignment = align
    f.keep_with_next = keep

S = doc.styles
set_font(S["Normal"]); pfmt(S["Normal"], indent=Inches(0.5))
set_font(S["Heading 1"], bold=True); pfmt(S["Heading 1"], before=0, after=12, indent=Inches(0), align=WD_ALIGN_PARAGRAPH.CENTER, keep=True)
S["Heading 1"].paragraph_format.page_break_before = True
set_font(S["Heading 2"], bold=True); pfmt(S["Heading 2"], indent=Inches(0), keep=True)
set_font(S["Heading 3"], bold=True, italic=True); pfmt(S["Heading 3"], indent=Inches(0), keep=True)
for nm in ("List Bullet", "List Number"):
    set_font(S[nm]); pfmt(S[nm], indent=None)
from docx.enum.style import WD_STYLE_TYPE
def new_style(name, base="Normal"):
    st = S.add_style(name, WD_STYLE_TYPE.PARAGRAPH); st.base_style = S[base]; return st
pre = new_style("Prefatory Heading"); set_font(pre, bold=True); pfmt(pre, after=12, indent=Inches(0), align=WD_ALIGN_PARAGRAPH.CENTER, keep=True)
tcap = new_style("Table Caption"); set_font(tcap); pfmt(tcap, before=12, after=6, double=False, indent=Inches(0), keep=True)
fcap = new_style("Figure Caption"); set_font(fcap); pfmt(fcap, before=6, after=12, double=False, indent=Inches(0))
cell = new_style("Table Text"); set_font(cell, size=10); pfmt(cell, double=False, indent=Inches(0))
refst = new_style("Reference"); set_font(refst); pfmt(refst, after=10, double=False, indent=Inches(-0.5))
refst.paragraph_format.left_indent = Inches(0.5)
figst = new_style("Figure"); set_font(figst); pfmt(figst, before=6, double=False, indent=Inches(0), align=WD_ALIGN_PARAGRAPH.CENTER, keep=True)
eqst = new_style("Equation"); set_font(eqst); pfmt(eqst, before=6, after=6, double=False, indent=Inches(0))
for lvl, ind in ((1, 0.0), (2, 0.3)):
    ts_ = new_style(f"toc {lvl}"); set_font(ts_); pfmt(ts_, after=6, double=False, indent=Inches(0))
    ts_.paragraph_format.left_indent = Inches(ind)
abbr = new_style("Abbreviation"); set_font(abbr); pfmt(abbr, after=6, double=False, indent=Inches(0))

# ---------------------------------------------------------------- inline markup
TOK = re.compile(r"(\*[^*]+\*|_\{[^}]*\}|\^\{[^}]*\})")
def add_runs(par, text, bold=False, italic=False, size=None):
    for part in TOK.split(text):
        if not part: continue
        r_italic, sub, sup = italic, False, False
        if part.startswith("*") and part.endswith("*"): part, r_italic = part[1:-1], True
        elif part.startswith("_{"): part, sub = part[2:-1], True
        elif part.startswith("^{"): part, sup = part[2:-1], True
        r = par.add_run(part); r.bold = bold or None; r.italic = r_italic or None
        if sub: r.font.subscript = True
        if sup: r.font.superscript = True
        if size: r.font.size = Pt(size)
    return par

def field(par, instr, placeholder=""):
    def fc(t):
        r = par.add_run(); e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), t); r._r.append(e)
    fc("begin")
    r = par.add_run(); it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = instr; r._r.append(it)
    fc("separate"); par.add_run(placeholder); fc("end")

# ---------------------------------------------------------------- page setup
def setup(sec):
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.top_margin = sec.bottom_margin = sec.right_margin = Inches(1)
    sec.left_margin = Inches(1.5)
    sec.header_distance = sec.footer_distance = Inches(0.5)

def pgnum(sec, fmt, start):
    sp = sec._sectPr
    el = sp.find(qn("w:pgNumType"))
    if el is None: el = OxmlElement("w:pgNumType"); sp.append(el)
    el.set(qn("w:fmt"), fmt); el.set(qn("w:start"), str(start))

sec = doc.sections[0]; setup(sec)

# ---------------------------------------------------------------- title page
def tp(text, before=0, bold=False, size=12, italic=False):
    p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Inches(0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.paragraph_format.space_before = Pt(before)
    add_runs(p, text, bold=bold, italic=italic, size=size); return p
tp("ALA-TOO INTERNATIONAL UNIVERSITY", bold=True)
tp("Informatics and Engineering Department", before=4)
tp(C.TITLE.upper(), before=96, bold=True, size=14)
tp("A Thesis Proposal", before=60)
tp("Presented to the Informatics and Engineering Department,", before=48)
tp("Ala-Too International University,")
tp("in Partial Fulfilment of the Requirements of the Research Methodology Course")
tp("By", before=60)
tp("Imanbek Mashrapov", before=6, bold=True)
tp("Supervisor", before=48)
tp("Dr. Remudin Reshid Mekuria", before=6, bold=True)
tp("Bishkek, Kyrgyzstan", before=84)
tp("November 2026")

# ---------------------------------------------------------------- prefatory section
sec = doc.add_section(WD_SECTION.NEW_PAGE); setup(sec); pgnum(sec, "lowerRoman", 2)
sec.header.is_linked_to_previous = False; sec.footer.is_linked_to_previous = False
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER; fp.paragraph_format.first_line_indent = Inches(0)
field(fp, "PAGE", "ii")
# title section: ensure empty header/footer (already empty by default)

def pre_heading(t, first=False):
    p = doc.add_paragraph(t.upper(), style="Prefatory Heading")
    if not first: p.paragraph_format.page_break_before = True
    return p

pre_heading("Abstract", first=True)
for t in C.ABSTRACT: add_runs(doc.add_paragraph(), t)
p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Inches(0.5)
add_runs(p, "*Keywords:* " + C.KEYWORDS)

pre_heading("Table of Contents")
p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Inches(0); p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
field(p, 'TOC \\o "1-2" \\h \\z \\u', "Right-click and choose Update Field to build the table of contents.")
pre_heading("List of Tables")
p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Inches(0); p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
field(p, 'TOC \\h \\z \\f t', "Update field to build the list of tables.")
pre_heading("List of Figures")
p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Inches(0); p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
field(p, 'TOC \\h \\z \\f f', "Update field to build the list of figures.")
pre_heading("List of Abbreviations")
for a, d in C.ABBREVIATIONS:
    p = doc.add_paragraph(style="Abbreviation"); p.paragraph_format.tab_stops.add_tab_stop(Inches(1.3))
    r = p.add_run(a); r.bold = True; p.add_run("\t" + d)

# ---------------------------------------------------------------- main section
sec = doc.add_section(WD_SECTION.NEW_PAGE); setup(sec); pgnum(sec, "decimal", 1)
sec.header.is_linked_to_previous = False; sec.footer.is_linked_to_previous = False
hp = sec.header.paragraphs[0]; hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT; hp.paragraph_format.first_line_indent = Inches(0)
field(hp, "PAGE", "1")
sec.footer.paragraphs[0].text = ""

counters = {"table": 0, "fig": 0}
first_chapter = [True]

def chapter_heading(line1, line2):
    p = doc.add_paragraph(style="Heading 1")
    if first_chapter[0]:
        p.paragraph_format.page_break_before = False; first_chapter[0] = False
    p.add_run(line1.upper()); p.add_run().add_break(WD_BREAK.LINE); p.add_run(line2.upper())

def set_cell_width(c, inches):
    c.width = Inches(inches)

def shade(c, color):
    tcPr = c._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), color); tcPr.append(sh)

def add_table(d):
    num = d.get("num")
    if num is None:
        counters["table"] += 1; num = str(counters["table"])
    cp = doc.add_paragraph(style="Table Caption")
    r = cp.add_run(f"Table {num}. "); r.bold = True
    add_runs(cp, d["caption"], italic=True)
    field(cp, f'TC "Table {num}. {d["caption"]}" \\f t \\l 1')
    t = doc.add_table(rows=1, cols=len(d["cols"])); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, h in enumerate(d["cols"]):
        c = t.rows[0].cells[i]; c.paragraphs[0].style = "Table Text"; add_runs(c.paragraphs[0], h, bold=True); shade(c, "DCE6F1")
    for row in d["rows"]:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].paragraphs[0].style = "Table Text"; add_runs(cells[i].paragraphs[0], v)
    for ri, row in enumerate(t.rows):
        for i, c in enumerate(row.cells):
            set_cell_width(c, d["widths"][i])
            if ri < len(t.rows) - 1:
                for cp_ in c.paragraphs: cp_.paragraph_format.keep_with_next = True
        trPr = row._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); trPr.append(cs)
    # repeat header row
    trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); trPr.append(th)
    sp = doc.add_paragraph(); sp.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE  # spacer
    sp.paragraph_format.space_after = Pt(0)

def add_fig(d):
    num = d.get("num")
    if num is None:
        counters["fig"] += 1; num = str(counters["fig"])
    p = doc.add_paragraph(style="Figure"); p.add_run().add_picture(d["path"], width=Inches(d["width"]))
    cp = doc.add_paragraph(style="Figure Caption")
    r = cp.add_run(f"Figure {num}. "); r.bold = True
    add_runs(cp, d["caption"], italic=True)
    field(cp, f'TC "Figure {num}. {d["caption"]}" \\f f \\l 1')

def add_eq(text, n):
    p = doc.add_paragraph(style="Equation")
    ts = p.paragraph_format.tab_stops
    ts.add_tab_stop(Inches(3.0), WD_TAB_ALIGNMENT.CENTER); ts.add_tab_stop(Inches(6.0), WD_TAB_ALIGNMENT.RIGHT)
    p.add_run("\t"); add_runs(p, text); p.add_run(f"\t({n})")

def render(kind, x):
    if kind == "chapter": chapter_heading(f"Chapter {x[0]}", x[1])
    elif kind == "h2": doc.add_paragraph(x, style="Heading 2")
    elif kind == "h3": doc.add_paragraph(x, style="Heading 3")
    elif kind == "p": add_runs(doc.add_paragraph(), x)
    elif kind == "bullets":
        for it in x:
            q = doc.add_paragraph(style="List Bullet"); add_runs(q, it)
    elif kind == "numbered":
        for it in x:
            q = doc.add_paragraph(style="List Number"); add_runs(q, it)
    elif kind == "table": add_table(x)
    elif kind == "fig": add_fig(x)
    elif kind == "eq": add_eq(*x)

for kind, x in C.B: render(kind, x)

# references
p = doc.add_paragraph("REFERENCES", style="Heading 1")
alltext = " ".join(str(x) for k, x in C.B) + " ".join(str(i) for a in C.APPX for i in a[2])
def key(ref):
    m = re.match(r"([^,.(]+?)(?:,|\.| \()", ref); sur = m.group(1).strip()
    y = re.search(r"\((\d{4}|n\.d\.)", ref).group(1)
    return sur, y
used = []
for ref in C.REFERENCES:
    sur, y = key(ref)
    if re.search(re.escape(sur) + r"[^)]{0,80}?" + re.escape(y), alltext): used.append(ref)
    else: print("UNCITED", sur, y)
for m in set(re.findall(r"([A-Z][\w\-À-ſ\.]+(?: [A-Z][\w]+)?)(?: et al\.)?,? \(?(\d{4}[ab]?|n\.d\.)", alltext)):
    if not any(r.startswith(m[0]) or (" "+m[0]) in r[:60] for r in used): print("MISSING REF?", m)
print("refs used", len(used))
for ref in sorted(used, key=lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower())):
    add_runs(doc.add_paragraph(style="Reference"), ref)

# appendixes
for letter, title, items in C.APPX:
    chapter_heading(f"Appendix {letter}", title)
    for kind, x in items: render(kind, x)

doc.core_properties.title = C.TITLE
doc.core_properties.author = "Imanbek Mashrapov"
doc.save(OUT)
print("saved", OUT)
