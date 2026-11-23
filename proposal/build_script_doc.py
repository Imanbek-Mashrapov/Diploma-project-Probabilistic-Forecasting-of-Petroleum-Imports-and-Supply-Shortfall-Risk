# -*- coding: utf-8 -*-
"""Speaker script (per slide) and Q&A preparation for the proposal presentation."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

F = "Century Gothic"
NAVY = RGBColor(0x14, 0x21, 0x3D); AMBER = RGBColor(0xC8, 0x64, 0x1B); MUTED = RGBColor(0x5F, 0x6B, 0x7A)

SLIDES = [
 ("Title", "0:30",
  ["Good morning. My name is Imanbek Mashrapov, and my supervisor is Dr. Remudin Reshid Mekuria.",
   "My proposal is about one practical question: can we tell, in advance and with an honest measure of uncertainty, how much fuel a landlocked country is likely to import next month, and how likely a supply shortfall is?",
   "I study a panel of landlocked economies, and I use Kyrgyzstan as the detailed case, for reasons the next slide makes clear."],
  "Let me start with why this matters."),
 ("One supplier’s decision can empty the pumps", "1:15",
  ["Kyrgyzstan has no seaport and almost no refining of its own. About 93 percent of its petroleum products come from one country, Russia.",
   "Russia restricted fuel exports in 2023, banned gasoline exports in 2024, and banned them again at the end of 2025. Kyrgyzstan was formally exempt. Even so, in July 2026 AI-95 gasoline ran out at Bishkek stations, and the government banned fuel exports.",
   "The customs data show the shock clearly. In August 2026 Kyrgyzstan imported 16.9 thousand tonnes of gasoline, only about 39 percent of a normal month. Reported stocks fell to two or three weeks, against a government target of two and a half months.",
   "So a formal exemption did not guarantee physical supply. And planners had no forward-looking number to warn them."],
  "So what exactly is missing?"),
 ("No tested measure of future supply risk exists", "1:15",
  ["Three research streams come close to this problem, but none solves it.",
   "Trade forecasting studies mostly predict annual totals or import values, for one country, as a single number.",
   "Security-of-supply research uses concentration indices such as the Herfindahl–Hirschman index. These describe exposure after the fact and are rarely tested as predictors.",
   "The closest work, by Kwon and Jeong in 2026, builds an early-warning system from customs data, but for Korea, a maritime economy, across all goods, and the output is a ranking, not a forecast of volume.",
   "The gap is the combination on the right: monthly physical volumes, for landlocked economies, with calibrated uncertainty, using only data that was public on the forecast date. A new country alone is not a gap; this combination is."],
  "From that gap I derived six objectives."),
 ("Six objectives turn the gap into a study", "1:00",
  ["First, build an audited monthly dataset from UN Comtrade and check it against official Kyrgyz statistics.",
   "Second, define a shortfall in a way that separates real supply stress from simply weak demand.",
   "Third, compare simple baselines, gradient-boosted trees and small global neural networks, evaluated the way the data were actually released.",
   "Fourth, measure, one piece at a time, what pooling countries, supplier data and shock data add.",
   "Fifth, calibrate the forecasts and test whether they warn of shortfalls better than concentration screening.",
   "And sixth, turn the result into a prototype risk monitor that a planner could actually use."],
  "These objectives lead to four research questions."),
 ("Four questions, four testable hypotheses", "1:30",
  ["Each question has a hypothesis with a number attached, fixed before any model is trained.",
   "RQ1 asks whether training one model across many countries helps Kyrgyz forecasts. H1 says a global model reduces the error, measured by MASE, by at least five percent at a three-month horizon.",
   "RQ2 asks whether neural networks beat gradient boosting. My hypothesis is deliberately cautious: not overall, but possibly during shocks.",
   "RQ3 asks whether supplier structure and shock information add value beyond a series’ own history. H3 expects at least a three percent improvement in quantile loss for highly dependent series.",
   "RQ4 asks whether calibrated forecasts give better warnings than simply ranking by supplier concentration.",
   "All tests use the five percent level with Holm correction. And if a hypothesis is not supported, that is a valid and useful result, not a failure."],
  "These questions come out of the literature, which I summarise next."),
 ("What the literature knows, and what it does not", "1:15",
  ["I searched four scholarly databases systematically: about 6,500 records, 1,600 screened, and 184 studies included and verified.",
   "On the left is what is established. Single-country import forecasts exist. Global models help when series are similar. Boosted trees are very strong on small tabular data. Probabilistic scoring and conformal calibration are mature. And in macroeconomics, we know data revisions can change which model looks best.",
   "On the right is what is not yet known: monthly physical forecasts across landlocked economies, whether pooling helps when series move weakly together, whether neural models gain during shocks, calibrated forecasts for fuel imports, and evaluation that respects publication lags.",
   "My study sits exactly where the right-hand column is."],
  "Here is how I put these pieces together."),
 ("Conceptual framework", "1:15",
  ["The framework reads from left to right.",
   "Inputs are only the information that was public at the forecast date: the import history, supplier structure, announced export bans, prices and risk indices, and release dates.",
   "The forecasting process varies the model class and whether training is local or global. It produces quantiles, and a conformal step corrects the intervals.",
   "The output is a forecast distribution of import volume, and from it, a shortfall probability. These are evaluated for accuracy, calibration and warning quality, and compared with concentration screening.",
   "At the bottom left are the conditions that can change the results: publication lag and revisions, differences between countries, structural breaks, and data quality. The four hypotheses test the arrows in the middle."],
  "The framework depends on good data, so let me show what has already been built."),
 ("A validated panel built from public customs data", "1:15",
  ["The data stage is complete. From UN Comtrade I built a training pool of 44 series from 22 countries, with 5,549 monthly observations. The evaluation set is the 22 best-reported series from 13 countries.",
   "Series were not sampled at random; they were selected by fixed rules on coverage, gaps and data quality, set before any modelling.",
   "I validated the Kyrgyz data against the national energy balance. From 2018 the gasoline volumes differ by only 3.7 percent on average.",
   "Other sources are the national statistics committee for validation, Brent prices, the geopolitical risk index, exchange rates and inflation, and Global Trade Alert for dated export restrictions."],
  "Here is what the Kyrgyz series actually looks like."),
 ("The Kyrgyz target: volatile, gappy, shock-sensitive", "1:00",
  ["The top panel is gasoline, the bottom is distillates, in thousand tonnes per month from 2015 to August 2026.",
   "Gasoline has a real seasonal pattern: high in December, low in September. Distillates show no clear seasonality, but their level shifts upward in 2024.",
   "The grey bands are months that are missing or failed quality checks. An important rule: I never fill these by interpolation, because that would invent data and make the models look better than they are.",
   "The orange band marks the late-2025 Russian gasoline ban, and you can see the sharp drop."],
  "Now, which models will I use?"),
 ("Complexity is added only if it earns its place", "1:15",
  ["Models are introduced as a staircase of increasing complexity.",
   "The lower bounds are naive forecasts, such as last year’s same month. Any model that cannot beat these has no practical value.",
   "Then come statistical models, ETS and SARIMA; then tree ensembles, LightGBM and XGBoost, which I treat as the main rival; then small global neural networks such as GRU, TCN and N-BEATS. A compact Temporal Fusion Transformer and a graph layer are optional extras.",
   "The neural networks are deliberately small, because the data are small. And every learned model predicts quantiles, not just one number, so we get a range."],
  "How will I decide which model wins?"),
 ("Evaluated as the data were actually released", "1:30",
  ["This is the core of the method. Customs data are published with a delay, often two to three months for Kyrgyzstan and much longer for some countries.",
   "So at every forecast origin, the model sees only the data that had actually been released by that date. This is called as-of, or real-time, evaluation. Origins roll forward month by month from January 2023, and I forecast one, three and six months ahead.",
   "There are no random train-test splits, because neighbouring months share the same shocks. All settings are frozen before a final test block that is run only once.",
   "I score point accuracy with MASE, the quantiles with pinball loss and CRPS, intervals by coverage and width, and shortfall warnings with PR-AUC, which suits rare events. Differences are tested with the corrected Diebold–Mariano test, and I always report effect sizes as well."],
  "The key output is the shortfall risk itself."),
 ("Shortfall risk comes from the forecast distribution", "1:00",
  ["A shortfall month is defined simply: the last three months of imports fall below 75 percent of the same months in the previous three years.",
   "A supply-side shortfall also requires a rising unit price, so that we separate a supply problem from simply low demand. I also test thresholds of 70 and 80 percent.",
   "Instead of training a separate classifier on very few events, the risk is read directly from each model’s forecast distribution: the probability that this ratio falls below 0.75, given what was known at the time.",
   "This probability is then compared with the standard alternative, ranking countries by supplier concentration."],
  "Does the idea work at all? A small pilot gives a first answer."),
 ("An untuned pilot shows there is signal to model", "1:15",
  ["Before the main study, I ran a deliberately simple pilot only to check that the design runs end to end.",
   "For the next three months of Kyrgyz gasoline, the error fell from about 28 percent for the 12-month average to about 21 percent for a local LightGBM model. So there is signal to model.",
   "But I want to be careful. There were only about 22 test months, no tuning and no significance test, so this ranks nothing.",
   "And the August 2026 shock is instructive: the model predicted 38 thousand tonnes, with a lower bound of 20; the actual was 16.9. A model that uses only its own history missed the shock. That is exactly why the study tests supplier and shock information, and calibration."],
  "Here is how the remaining work is organised."),
 ("From validated data to a risk monitor", "0:45",
  ["Stages one and two, data collection and validation, are done. The next step is to have the cleaning rules reviewed and frozen, and to take a second data snapshot so revisions can be measured.",
   "Then I build the as-of feature store, run the model benchmark and calibration in months two to four, and complete evaluation and ablation.",
   "The final two months go to the risk monitor prototype and writing the thesis."],
  "To finish, what will the study deliver?"),
 ("What the study will deliver, and its limits", "1:15",
  ["The scientific contribution is a tested benchmark: when global deep learning helps over gradient boosting for fuel imports, and whether concentration screening works where one supplier dominates.",
   "The methodological contribution is a transparent, reproducible route from raw customs records to a validated physical target under real publication lags.",
   "The applied contribution is a public-data risk monitor with a fan chart, risk status and supplier mix.",
   "I also want to be clear about the limits. Customs records measure imports, not consumption. Data from 2025 onward are provisional. One product code mixes several fuels. And true shocks are few, so no conclusion will rest on a single event.",
   "Ethically, all data are public and aggregate, the work gives no guidance on evading trade restrictions, and AI assistance is disclosed under faculty rules."],
  "Thank you."),
 ("Thank you", "0:15",
  ["Thank you for your attention. I would welcome your questions and feedback on the proposal."],
  None),
]

QA = [
 ("Motivation and scope", [
  ("Why landlocked economies, and not all importers?",
   "Landlocked countries depend on transit through neighbours and on very few suppliers, so a single export decision reaches their pumps quickly. That makes forecasting supply risk especially valuable there. I do not claim that “landlocked” is itself a causal factor; I use the group as the study setting, and some European landlocked states are included because they report reliably and enlarge the training panel."),
  ("Why Kyrgyzstan as the case study?",
   "It has about 93% dependence on one supplier, a well-documented shortage in 2026, and national statistics I can validate against. It is also the only Central Asian country with good enough monthly data to be in the evaluation set."),
  ("Is this really new? Haven’t people forecast oil imports before?",
   "They have, but almost always for one country, with annual or value data, and as a single number. The closest early-warning study is Kwon and Jeong (2026) for Korea. What has not been tested is monthly physical volumes for landlocked economies, with calibrated uncertainty and with evaluation that respects publication delays. That combination is the gap; I do not claim each piece is new."),
  ("Why do you forecast imports and not consumption?",
   "Monthly consumption data are not publicly available across countries, while customs imports are. For a country that imports nearly all its fuel, imports are the supply side that matters. I state clearly that imports are not consumption, because stocks and informal trade sit in between."),
  ("Can your model predict export bans?",
   "No, and it is not designed to. Political decisions are not predictable from trade data. What the model can show is how quickly measurable risk rises once early signals appear, such as a falling Russian share or a rising unit price."),
 ]),
 ("Data", [
  ("How reliable is UN Comtrade data?",
   "It has known problems: late and irregular reporting, inconsistent totals, wrong masses and revisions. I treat these as part of the method. I rebuild totals from partner rows, check physical densities and unit prices, and validated Kyrgyz gasoline against the national energy balance: within 3.7% on average from 2018."),
  ("Why do you use tonnes rather than US dollars?",
   "Values mix price and quantity. When prices rise, the value of imports can go up even if fewer tonnes arrive. A planner needs to know physical volume, and Comtrade reports net mass separately, so I never have to infer volume from price."),
  ("What do you do with missing months?",
   "They are never filled with zeros and the target is never interpolated, because that would invent data and inflate accuracy. Missing months are labelled and simply left out of training loss and scoring."),
  ("What about the 2016–2017 discrepancy with Russian mirror data?",
   "In those years Russia reports exporting about three times what Kyrgyzstan records importing, and the cause is unknown. So I will report results both with and without 2015–2017, and the conclusions should not depend on that choice."),
  ("Recent data may be revised. Doesn’t that affect your results?",
   "Yes, and that is the most serious limitation. Records from 2025 onward appear to be first releases. I will evaluate on data as first released, which is what a forecaster would have had, and take a second snapshot to measure revisions directly."),
  ("Why is distillates not called diesel?",
   "The six-digit code 2710.19 mixes diesel, kerosene, jet fuel and fuel oil. Calling it diesel would be inaccurate, so the target is labelled “distillates”."),
  ("How did you choose the countries? Isn’t that cherry-picking?",
   "Selection uses rules fixed before modelling: minimum observed months, coverage, maximum gap length, recent data, enough supplier detail and a minimum size. The rules are written down and will be reviewed and frozen with my supervisor before any model is trained."),
 ]),
 ("Models", [
  ("Why use deep learning if trees are often better on small data?",
   "That is exactly what RQ2 tests. I expect trees to be hard to beat overall, which is why my hypothesis is cautious. Deep learning becomes feasible only because I pool many countries; the networks are kept small. If neural models do not help, that is a valid finding."),
  ("How can you train a neural network on about 130 Kyrgyz months?",
   "I cannot on Kyrgyz data alone. A global model is trained on the whole panel of 44 series, about 5,500 observations, and shares parameters across countries. Whether that sharing helps Kyrgyzstan is RQ1."),
  ("Why not a large Transformer?",
   "With about 140 monthly steps per series, large Transformers would overfit, and published work shows simple models can match them even on much larger data. I include only a compact Temporal Fusion Transformer and drop it if validation does not support it."),
  ("Why not use graph neural networks for the trade network?",
   "About 20 country nodes are not enough for a defensible graph-learning problem. Supplier links enter as hand-built features, and a single graph layer is tested only as an optional ablation."),
  ("What is a conformal step, in simple terms?",
   "After the model predicts a range, I check on a later period how often reality fell inside that range. If an 80% range only caught 65% of outcomes, the conformal step widens it until the coverage is right. In the pilot, nominal 80% intervals covered only 62–75% of Kyrgyz outcomes, so this step is needed."),
 ]),
 ("Evaluation and results", [
  ("Why MASE and not MAPE or R²?",
   "MAPE becomes unstable when a month is close to zero, and R² is not a good criterion for comparing forecasts. MASE compares the error with a simple seasonal benchmark, so it can be compared across countries of very different size."),
  ("What does “as-of” evaluation mean, and why is it important?",
   "At each forecast date the model sees only data that had actually been published by then. Customs data arrive with a delay of months, so ignoring this would let the model use information no planner had, and the results would look better than they could be in reality."),
  ("Why not use a normal random train-test split or cross-validation?",
   "Neighbouring months share the same shocks, so random splits leak future information into training and give optimistic results. Rolling-origin evaluation always trains on the past and tests on the future."),
  ("How will you know a difference between models is real?",
   "I use the corrected Diebold–Mariano test with Holm correction for multiple comparisons, and I always report effect sizes with bootstrap intervals, because tests have low power with short test periods. I distinguish statistical from practical significance."),
  ("Why a 75% threshold for a shortfall?",
   "It marks a substantial drop relative to the same season in previous years, and in the clean data it gives a reasonable number of episodes (11 for gasoline, 7 for distillates). Because any threshold is a judgement, I also test 70% and 80%."),
  ("Your pilot missed the August 2026 shock. Doesn’t that show the method fails?",
   "The pilot used only each series’ own history, without supplier or shock information and without calibration, and it was untuned. Missing the shock is precisely what motivates H3 and H4. The pilot shows the design runs and that there is signal; it does not rank models."),
  ("Concentration is near its maximum for Kyrgyzstan. Can H4 even be tested?",
   "That is a real difficulty: the median HHI for Kyrgyz gasoline is 0.89, so it varies little. That is why H4 is tested on pooled events across the whole panel, and why changes in the Russian share may matter more than the index itself."),
  ("What if none of your hypotheses are supported?",
   "Then the thesis reports that clearly. A tested finding that pooling, deep learning or supplier data do not help on this kind of data is still a contribution, and it would be useful to planners and researchers."),
 ]),
 ("Practical use, ethics and process", [
  ("Who would actually use the risk monitor?",
   "Energy ministries, state fuel companies and statistical offices for stock planning against targets such as the 2.5-month reserve, and fuel importers for a public estimate of supply risk. Because of publication lags, it is an early-warning tool, not a live feed."),
  ("Is this innovative in the Kyrgyz context?",
   "Kyrgyzstan currently has no public, tested forecast of fuel supply risk. The study adapts probabilistic forecasting and real-time evaluation to that local need and delivers a working prototype, which fits the faculty’s definition of innovation as meaningful local adaptation."),
  ("Are there ethical risks?",
   "All data are public, aggregate and non-personal; API keys are never stored in code. The work supports planning and gives no guidance on evading trade restrictions. Any practitioner feedback on the prototype will be voluntary and anonymous."),
  ("Did you use AI tools?",
   "Yes, and it is disclosed as faculty rules require, with prompt records kept. Every result and every design choice must be one I can explain and defend myself."),
  ("Is the timeline realistic?",
   "The hardest and slowest part, collecting and validating the data, is already finished and tested. The remaining work is six months of modelling, evaluation and the prototype, with a clear order of stages and a frozen design that limits rework."),
 ]),
]

TIPS = ["Speak to the slide’s headline first, then explain the detail.",
        "Use the numbers exactly as on the slides: 93%, 16.9 kt, 44 series, 22 countries, 5,549 observations, 3.7%.",
        "If you do not know an answer, say what would be needed to find it; do not guess.",
        "When challenged on a weakness, acknowledge it first, then explain how the design handles it.",
        "Planned total: about 17 minutes. If time is short, shorten slides 6, 9 and 14."]

# ---------------------------------------------------------------- build
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for m in ("top_margin", "bottom_margin", "left_margin", "right_margin"): setattr(sec, m, Inches(1))

def fontify(style, size, bold=None, color=None):
    style.font.name = F; style.font.size = Pt(size)
    if bold is not None: style.font.bold = bold
    if color is not None: style.font.color.rgb = color
    rpr = style.element.get_or_add_rPr(); rf = rpr.find(qn("w:rFonts"))
    if rf is None: rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"): rf.set(qn(a), F)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]

S = doc.styles
fontify(S["Normal"], 11); S["Normal"].paragraph_format.space_after = Pt(6); S["Normal"].paragraph_format.line_spacing = 1.15
fontify(S["Title"], 22, True, NAVY)
for nm, sz in (("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11)):
    fontify(S[nm], sz, True, NAVY)
    pf = S[nm].paragraph_format; pf.space_before = Pt(14 if nm == "Heading 1" else 10); pf.space_after = Pt(4); pf.keep_with_next = True
fontify(S["List Bullet"], 11)

def para(text, italic=False, color=None, bold=False, size=None):
    p = doc.add_paragraph(); r = p.add_run(text); r.italic = italic; r.bold = bold
    if color: r.font.color.rgb = color
    if size: r.font.size = Pt(size)
    return p

doc.add_paragraph("Presentation Script and Q&A Preparation", style="Title")
para("Probabilistic Forecasting of Petroleum Imports and Supply-Shortfall Risk in Landlocked Economies", bold=True)
para("Imanbek Mashrapov · Supervisor: Dr. Remudin Reshid Mekuria · Ala-Too International University", color=MUTED)
total = sum(int(t.split(":")[0]) * 60 + int(t.split(":")[1]) for _, t, _, _ in SLIDES)
para(f"16 slides · planned speaking time about {total // 60} min {total % 60:02d} s, leaving time for questions.", color=MUTED)

doc.add_heading("Delivery tips", level=1)
for t in TIPS: doc.add_paragraph(t, style="List Bullet")

doc.add_heading("Part 1. Slide-by-slide script", level=1)
for i, (ttl, tm, lines, trans) in enumerate(SLIDES, 1):
    h = doc.add_heading(f"Slide {i}. {ttl}", level=2)
    r = h.add_run(f"   ({tm})"); r.font.color.rgb = MUTED; r.font.size = Pt(10); r.bold = False
    for ln in lines: para(ln)
    if trans:
        p = doc.add_paragraph(); r1 = p.add_run("Transition: "); r1.bold = True; r1.font.color.rgb = AMBER
        r2 = p.add_run(trans); r2.italic = True

doc.add_page_break()
doc.add_heading("Part 2. Anticipated questions and suggested answers", level=1)
n = 0
for grp, items in QA:
    doc.add_heading(grp, level=2)
    for q, a in items:
        n += 1
        p = doc.add_paragraph(); p.paragraph_format.keep_with_next = True; p.paragraph_format.space_before = Pt(6)
        r = p.add_run(f"Q{n}. {q}"); r.bold = True; r.font.color.rgb = NAVY
        para(a)

doc.save("Mashrapov_Presentation_Script_and_QA.docx")
print("saved; questions:", n, "time:", total)
