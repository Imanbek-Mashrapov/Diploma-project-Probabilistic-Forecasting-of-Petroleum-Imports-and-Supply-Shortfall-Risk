# -*- coding: utf-8 -*-
"""Build a 16:9 Century Gothic deck (Google Slides size) for the thesis proposal."""
import re, copy
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from lxml import etree

F = "Century Gothic"
NAVY = RGBColor(0x14, 0x21, 0x3D); AMBER = RGBColor(0xE0, 0x7A, 0x1F); INK = RGBColor(0x22, 0x2B, 0x38)
MUTED = RGBColor(0x5F, 0x6B, 0x7A); TINT = RGBColor(0xEE, 0xF2, 0xF7); WHITE = RGBColor(255, 255, 255)
ICE = RGBColor(0xC9, 0xD6, 0xE8); LAMBER = RGBColor(0xFB, 0xEB, 0xDC)

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(10), Inches(5.625)
BLANK = prs.slide_layouts[6]

# theme fonts -> Century Gothic (so Google Slides / PowerPoint theme picks it up)
theme_part = [p for p in prs.part.package.iter_parts() if p.partname.endswith("theme1.xml")][0]
root = etree.fromstring(theme_part.blob)
ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
for tag in ("a:majorFont", "a:minorFont"):
    root.find(f".//{tag}/a:latin", ns).set("typeface", F)
root.find(".//a:fontScheme", ns).set("name", "Century Gothic")
theme_part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

def bg(slide, color):
    f = slide.background.fill; f.solid(); f.fore_color.rgb = color

def text(slide, x, y, w, h, runs, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, name=None, spacing=None):
    """runs: str or list of paragraphs; a paragraph is str or list of (text, dict)."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name: tb.name = name
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing: p.space_after = Pt(spacing)
        segs = para if isinstance(para, list) else [(para, {})]
        for s, o in segs:
            r = p.add_run(); r.text = s
            r.font.name = F; r.font.size = Pt(o.get("size", size)); r.font.bold = o.get("bold", bold)
            r.font.italic = o.get("italic", False); r.font.color.rgb = o.get("color", color)
    return tb

def box(slide, x, y, w, h, fill=TINT, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08, name=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line: s.line.color.rgb = line; s.line.width = Pt(1.25)
    else: s.line.fill.background()
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: s.adjustments[0] = radius
    if name: s.name = name
    return s

def circle_num(slide, x, y, d, label, fill=AMBER, color=WHITE, size=14):
    c = box(slide, x, y, d, d, fill=fill, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    r = p.add_run(); r.text = label; r.font.name = F; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = color
    return c

def title(slide, t, kicker=None):
    if kicker: text(slide, 0.6, 0.38, 8.8, 0.3, kicker.upper(), size=11, color=AMBER, bold=True)
    text(slide, 0.6, 0.62, 8.8, 0.7, t, size=26, color=NAVY, bold=True, name="Title")

def footer(slide, n, dark=False):
    c = ICE if dark else MUTED
    text(slide, 0.6, 5.2, 6, 0.25, "Mashrapov · Petroleum import risk in landlocked economies", size=9, color=c)
    text(slide, 8.4, 5.2, 1.0, 0.25, str(n), size=9, color=c, align=PP_ALIGN.RIGHT)

slides = []
def new(dark=False):
    s = prs.slides.add_slide(BLANK); bg(s, NAVY if dark else WHITE); slides.append(s); return s

# 1 ---- title
s = new(dark=True)
text(s, 0.6, 0.6, 6, 0.3, "THESIS PROPOSAL · RESEARCH METHODOLOGY", size=11, color=AMBER, bold=True)
text(s, 0.6, 1.1, 8.6, 1.9, "Probabilistic Forecasting of Petroleum Imports and Supply-Shortfall Risk in Landlocked Economies", size=30, color=WHITE, bold=True)
text(s, 0.6, 3.25, 8, 0.35, "Kyrgyzstan as the detailed case", size=16, color=ICE, bold=False)
text(s, 0.6, 4.15, 5, 0.9, [[("Imanbek Mashrapov", {"bold": True, "color": WHITE})], "Supervisor: Dr. Remudin Reshid Mekuria", "Ala-Too International University · November 2026"], size=12, color=ICE)
s.notes_slide.notes_text_frame.text = "Introduce the topic: forecasting how much fuel a landlocked country will import next month, and how likely a shortfall is."

# 2 ---- why it matters: stat callouts
s = new(); title(s, "One supplier’s decision can empty the pumps", "Background")
stats = [("93%", "of Kyrgyz petroleum products come from Russia", "Official estimate"),
         ("16.9 kt", "gasoline imported in Aug 2026, about 39% of the 2024–25 monthly average", "UN Comtrade"),
         ("2–3 wk", "of fuel stocks reported in mid-2026, against a 2.5-month target", "Press reports")]
for i, (big, lab, src) in enumerate(stats):
    x = 0.6 + i * 3.0
    box(s, x, 1.55, 2.75, 2.75, fill=TINT)
    text(s, x + 0.25, 1.8, 2.3, 0.8, big, size=40, color=AMBER, bold=True)
    text(s, x + 0.25, 2.7, 2.3, 1.1, lab, size=13, color=INK)
    text(s, x + 0.25, 3.9, 2.3, 0.3, src, size=10, color=MUTED)
text(s, 0.6, 4.5, 8.8, 0.5, "Russian export bans in 2023, 2024 and late 2025; Bishkek AI-95 shortage and fuel-export ban in July 2026.", size=12, color=MUTED)
footer(s, 2)
s.notes_slide.notes_text_frame.text = "Landlocked economies buy fuel over a few overland routes from few suppliers and hold small stocks. In 2026 a formal exemption from Russian bans did not guarantee physical supply."

# 3 ---- problem & gap
s = new(); title(s, "No tested measure of future supply risk exists", "Problem and research gap")
streams = [("Trade forecasting", "Annual or value flows; single countries; point forecasts"),
           ("Security-of-supply indices", "Concentration (HHI) describes exposure after the fact; rarely tested"),
           ("Customs early warning", "Closest work (Kwon & Jeong, 2026): maritime Korea, all goods, a ranking")]
for i, (h, d) in enumerate(streams):
    y = 1.5 + i * 1.08
    box(s, 0.6, y, 4.3, 0.92, fill=TINT)
    text(s, 0.8, y + 0.12, 3.9, 0.3, h, size=14, color=NAVY, bold=True)
    text(s, 0.8, y + 0.45, 3.9, 0.45, d, size=11, color=INK)
box(s, 5.3, 1.5, 4.1, 3.08, fill=NAVY)
text(s, 5.6, 1.7, 3.6, 0.3, "THE GAP", size=11, color=AMBER, bold=True)
text(s, 5.6, 2.05, 3.55, 2.4, "Can monthly physical fuel imports of landlocked economies, and the risk of a shortfall, be forecast out of sample with calibrated uncertainty, using only data public on the forecast date?", size=15, color=WHITE)
footer(s, 3)
s.notes_slide.notes_text_frame.text = "The three streams have been studied separately. A new country alone is not a gap; the gap is the combination of monthly physical target, calibration, publication lags and landlocked panel."

# 4 ---- objectives
s = new(); title(s, "Six objectives turn the gap into a study", "Purpose and objectives")
objs = ["Build an audited monthly panel from UN Comtrade, validated against official data",
        "Define a shortfall target that separates supply stress from weak demand",
        "Compare baselines, boosted trees and global neural models under lag-aware evaluation",
        "Measure by ablation the value of pooling, supplier and shock information",
        "Calibrate forecasts and test warnings against concentration screening",
        "Deliver a prototype Fuel Import Risk Monitor"]
for i, o in enumerate(objs):
    c, r = i % 2, i // 2
    x, y = 0.6 + c * 4.5, 1.5 + r * 1.15
    box(s, x, y, 4.25, 0.95, fill=TINT)
    circle_num(s, x + 0.2, y + 0.22, 0.5, str(i + 1))
    text(s, x + 0.9, y + 0.12, 3.2, 0.75, o, size=12, color=INK, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 4)

# 5 ---- RQs and hypotheses
s = new(); title(s, "Four questions, four testable hypotheses", "Research questions")
rq = [("RQ1", "Does cross-country training help Kyrgyz forecasts?", "H1: global models cut MASE ≥5% vs best local model (h = 3)"),
      ("RQ2", "Do neural models beat gradient boosting?", "H2: not overall, but yes in shock windows"),
      ("RQ3", "Do supplier and shock data add value?", "H3: pinball loss falls ≥3% for high-dependence series"),
      ("RQ4", "Can forecasts warn better than concentration?", "H4: higher PR-AUC and recall than HHI ranking")]
for i, (k, q, h) in enumerate(rq):
    y = 1.4 + i * 0.84
    box(s, 0.6, y, 8.8, 0.74, fill=TINT if i % 2 == 0 else WHITE, line=None if i % 2 == 0 else ICE)
    text(s, 0.8, y, 0.8, 0.76, k, size=16, color=AMBER, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 1.65, y, 3.6, 0.76, q, size=13, color=NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 5.35, y, 3.9, 0.76, h, size=12, color=INK, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.6, 4.82, 8.8, 0.25, "All tested at 5% with Holm correction; an unsupported hypothesis is a valid result.", size=10, color=MUTED)
footer(s, 5)

# 6 ---- literature
s = new(); title(s, "What the literature knows, and what it does not", "Review of related literature")
known = ["Single-country import forecasts (Indonesia, China, Nepal)", "Global models help when series are similar", "Boosted trees are strong on small tabular data", "Proper scoring and conformal calibration are mature", "Data revisions change forecast conclusions"]
unknown = ["Monthly physical forecasts across landlocked economies", "Whether pooling helps weakly co-moving fuel series", "Whether neural models gain in shock periods", "Calibrated distributions for fuel imports", "Lag-aware evaluation of Comtrade forecasts"]
for j, (hd, items, fill, hc) in enumerate([("Known", known, TINT, NAVY), ("Not yet known", unknown, LAMBER, AMBER)]):
    x = 0.6 + j * 4.5
    box(s, x, 1.45, 4.25, 3.55, fill=fill)
    text(s, x + 0.3, 1.6, 3.7, 0.35, hd, size=16, color=hc, bold=True)
    tb = text(s, x + 0.3, 2.05, 3.75, 2.9, items, size=12, color=INK, spacing=7)
    for p in tb.text_frame.paragraphs:
        pPr = p._p.get_or_add_pPr(); pPr.set("marL", str(Emu(Inches(0.2)))); pPr.set("indent", str(-Emu(Inches(0.2))))
        bu = etree.SubElement(pPr, "{http://schemas.openxmlformats.org/drawingml/2006/main}buChar"); bu.set("char", "•")
footer(s, 6)
s.notes_slide.notes_text_frame.text = "Structured search: 6,526 records, 5,230 unique, 1,600 screened, 184 included and verified."

# 7 ---- conceptual framework
s = new(); title(s, "Conceptual framework", "Chapter III")
s.shapes.add_picture("figures/fig_conceptual_cg.png", Inches(1.05), Inches(1.35), height=Inches(3.75))
footer(s, 7)
s.notes_slide.notes_text_frame.text = "Information released by the forecast origin goes through the forecasting process to a predictive distribution, then to shortfall probability and evaluation. Moderating conditions: publication lag, heterogeneity, breaks, data quality."

# 8 ---- data & sample
s = new(); title(s, "A validated panel built from public customs data", "Data and sample")
for i, (big, lab) in enumerate([("44", "series in the training pool"), ("22", "countries"), ("5,549", "monthly observations"), ("3.7%", "mean gap vs Kyrgyz energy balance")]):
    y = 1.45 + i * 0.9
    text(s, 0.6, y, 1.9, 0.6, big, size=28, color=AMBER, bold=True)
    text(s, 2.0, y + 0.05, 2.7, 0.6, lab, size=12, color=INK, anchor=MSO_ANCHOR.MIDDLE)
box(s, 5.0, 1.45, 4.4, 3.5, fill=TINT)
text(s, 5.25, 1.6, 4.0, 0.3, "Sources", size=14, color=NAVY, bold=True)
srcs = [("UN Comtrade API", "monthly mass, value, partners, release dates"), ("Kyrgyz NSC", "energy balance and reports for validation"),
        ("Brent, GPR, FX, CPI", "external conditions"), ("Global Trade Alert", "dated export restrictions")]
for i, (a, b) in enumerate(srcs):
    text(s, 5.25, 2.05 + i * 0.7, 4.0, 0.65, [[(a, {"bold": True, "color": NAVY})], b], size=12, color=INK)
footer(s, 8)
s.notes_slide.notes_text_frame.text = "Purposive, rule-based selection: Tier 1 evaluation set 22 series from 13 countries (3,021 obs). Kyrgyzstan is the only Central Asian country in Tier 1."

# 9 ---- Kyrgyz series
s = new(); title(s, "The Kyrgyz target: volatile, gappy, shock-sensitive", "Preliminary data")
s.shapes.add_picture("figures/fig01_kyrgyz_monthly_imports.png", Inches(0.6), Inches(1.35), height=Inches(3.65))
box(s, 6.75, 1.45, 2.65, 3.45, fill=TINT)
text(s, 6.95, 1.6, 2.3, 3.2, [[("Gasoline", {"bold": True, "color": NAVY})], "Seasonal: peak in December, low in September", "",
                               [("Distillates", {"bold": True, "color": NAVY})], "No clear seasonality; level shift in 2024", "",
                               [("Rule", {"bold": True, "color": AMBER})], "Missing months are never interpolated"], size=12, color=INK)
footer(s, 9)

# 10 ---- models
s = new(); title(s, "Complexity is added only if it earns its place", "Models")
steps = [("Lower bounds", "Naive, seasonal naive, 12-month mean"), ("Statistical", "ETS, SARIMA (local)"), ("Trees", "Random forest, LightGBM, XGBoost"),
         ("Global neural", "GRU, TCN, N‑BEATS (16–64 units)"), ("Optional", "Compact TFT, graph layer as ablation")]
for i, (h, d) in enumerate(steps):
    x = 0.6 + i * 1.78; y = 3.55 - i * 0.48
    box(s, x, y, 1.62, 4.95 - y, fill=NAVY if i == 2 else TINT)
    col = WHITE if i == 2 else NAVY
    text(s, x + 0.15, y + 0.15, 1.35, 0.35, h, size=13, color=AMBER if i == 2 else NAVY, bold=True)
    text(s, x + 0.15, y + 0.55, 1.35, 1.0, d, size=11, color=WHITE if i == 2 else INK)
text(s, 0.6, 1.45, 5.2, 0.9, "All learned models output quantiles (pinball loss); a conformal step then corrects interval coverage. Boosted trees are the main rival.", size=12, color=INK)
footer(s, 10)

# 11 ---- evaluation
s = new(); title(s, "Evaluated as the data were actually released", "Evaluation design")
# timeline diagram
y0 = 1.75
box(s, 0.6, y0, 5.2, 0.42, fill=TINT, shape=MSO_SHAPE.RECTANGLE)
text(s, 0.75, y0, 3.5, 0.42, "History released by origin τ", size=11, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
box(s, 5.8, y0, 1.0, 0.42, fill=ICE, shape=MSO_SHAPE.RECTANGLE)
text(s, 5.8, y0, 1.0, 0.42, "Lag", size=11, color=NAVY, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
box(s, 6.8, y0, 2.6, 0.42, fill=AMBER, shape=MSO_SHAPE.RECTANGLE)
text(s, 6.8, y0, 2.6, 0.42, "Forecast h = 1, 3, 6", size=11, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.6, 2.3, 8.8, 0.3, "Origins roll monthly from January 2023; no random splits; settings frozen before a final block run once.", size=11, color=MUTED)
mets = [("Point", "MASE (primary), WAPE"), ("Quantiles", "Pinball loss, CRPS"), ("Intervals", "80% / 95% coverage and width"), ("Shortfall", "PR-AUC, Brier, recall at alert budget")]
for i, (a, b) in enumerate(mets):
    x = 0.6 + i * 2.23
    box(s, x, 2.85, 2.05, 1.35, fill=TINT)
    text(s, x + 0.18, 2.98, 1.75, 0.3, a, size=13, color=NAVY, bold=True)
    text(s, x + 0.18, 3.35, 1.75, 0.8, b, size=11, color=INK)
text(s, 0.6, 4.45, 8.8, 0.5, "Differences: corrected Diebold–Mariano (HLN) test with Holm correction, plus effect sizes with bootstrap intervals.", size=12, color=INK)
footer(s, 11)

# 12 ---- shortfall
s = new(); title(s, "Shortfall risk comes from the forecast distribution", "Key measures")
box(s, 0.6, 1.5, 8.8, 0.85, fill=TINT)
text(s, 0.85, 1.5, 8.4, 0.85, [[("Shortfall month:  ", {"bold": True, "color": NAVY}), ("S = 1[ Q / B < 0.75 ]", {"size": 18})]], size=14, color=INK, anchor=MSO_ANCHOR.MIDDLE)
box(s, 0.6, 2.5, 8.8, 0.85, fill=TINT)
text(s, 0.85, 2.5, 8.4, 0.85, [[("Risk:  ", {"bold": True, "color": NAVY}), ("P( Q / B < 0.75 | data released by origin τ )", {"size": 18})]], size=14, color=INK, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.6, 3.6, 8.8, 1.3, ["Q = trailing three-month import mass; B = same months averaged over the previous three years.",
                             "A supply-side shortfall also needs a rising unit value; thresholds 0.70 and 0.80 as sensitivity checks.",
                             "Compared against ranking by supplier concentration (HHI = Σ s²)."], size=12, color=INK, spacing=6)
footer(s, 12)

# 13 ---- pilot (native chart)
s = new(); title(s, "An untuned pilot shows there is signal to model", "Preliminary results")
cd = CategoryChartData(); cd.categories = ["Seasonal naive", "12-month mean", "LightGBM, local", "LightGBM, global", "GRU, global"]
cd.add_series("Next-3-month WAPE (%)", (29.2, 28.4, 20.7, 23.6, 28.5))
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(1.4), Inches(5.4), Inches(3.6), cd)
ch = gf.chart; ch.has_legend = False; ch.has_title = True
ch.chart_title.text_frame.text = "Kyrgyz gasoline, next-3-month WAPE (%), lower is better"
tp = ch.chart_title.text_frame.paragraphs[0]; tp.runs[0].font.size = Pt(11); tp.runs[0].font.name = F; tp.runs[0].font.bold = False; tp.runs[0].font.color.rgb = MUTED
ch.font.name = F; ch.font.size = Pt(11); ch.font.color.rgb = INK
pl = ch.plots[0]; pl.gap_width = 60; pl.has_data_labels = True
pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
ser = pl.series[0]
for idx in range(5):
    pt = ser.points[idx]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = AMBER if idx == 2 else ICE
    tf_ = pt.data_label.text_frame; tf_.text = ('%.1f' % (29.2, 28.4, 20.7, 23.6, 28.5)[idx]); pt.data_label.position = XL_LABEL_POSITION.OUTSIDE_END
    rr = tf_.paragraphs[0].runs[0]; rr.font.name = F; rr.font.size = Pt(11); rr.font.color.rgb = INK
ch.value_axis.visible = False; ch.value_axis.has_major_gridlines = False
ch.category_axis.reverse_order = True; ch.category_axis.format.line.fill.background()
box(s, 6.3, 1.45, 3.1, 3.5, fill=NAVY)
text(s, 6.55, 1.65, 2.7, 3.2, [[("Caution", {"bold": True, "color": AMBER})], "About 22 test months, no tuning, no significance test.", "",
                               [("Aug 2026 shock", {"bold": True, "color": AMBER})], "Forecast 38.1 kt (lower bound 20.5 kt); actual 16.9 kt. Own history alone missed it."], size=12, color=WHITE)
footer(s, 13)

# 14 ---- plan
s = new(); title(s, "From validated data to a risk monitor", "Work plan")
s.shapes.add_picture("figures/fig_flow_cg.png", Inches(0.6), Inches(1.4), width=Inches(8.8))
text(s, 0.6, 4.75, 8.8, 0.3, "Stages 1–2 complete · rule freeze next · modelling months 2–4 · monitor and thesis months 5–6", size=11, color=MUTED)
footer(s, 14)

# 15 ---- contributions & limits
s = new(); title(s, "What the study will deliver, and its limits", "Contribution")
cols = [("Scientific", "Tested benchmark: global deep learning vs gradient boosting, and concentration screening tested out of sample"),
        ("Methodological", "Transparent route from customs records to a validated physical target, under real publication lags"),
        ("Applied", "Public-data Fuel Import Risk Monitor: fan chart, risk status, supplier mix")]
for i, (h, d) in enumerate(cols):
    x = 0.6 + i * 3.0
    box(s, x, 1.45, 2.75, 2.1, fill=TINT)
    text(s, x + 0.22, 1.6, 2.35, 0.3, h, size=14, color=NAVY, bold=True)
    text(s, x + 0.22, 2.0, 2.35, 1.5, d, size=12, color=INK)
text(s, 0.6, 3.8, 8.8, 1.2, [[("Limits:  ", {"bold": True, "color": AMBER}), ("customs records are imports, not consumption; 2025–26 data are provisional; HS 271019 mixes fuels; shocks are few.", {})],
                             [("Ethics:  ", {"bold": True, "color": AMBER}), ("public, aggregate, non-personal data; no guidance on evading restrictions; AI use disclosed.", {})]], size=12, color=INK, spacing=8)
footer(s, 15)

# 16 ---- close
s = new(dark=True)
text(s, 0.6, 1.6, 8.8, 0.9, "Thank you", size=40, color=WHITE, bold=True)
text(s, 0.6, 2.6, 8.8, 0.6, "Questions and feedback on the proposal are welcome", size=16, color=ICE)
text(s, 0.6, 4.3, 8.8, 0.5, "Imanbek Mashrapov · Ala-Too International University", size=12, color=ICE)

prs.save("Mashrapov_Proposal_Presentation.pptx")
print("saved", len(prs.slides))
