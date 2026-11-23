# -*- coding: utf-8 -*-
"""Condensed body of the proposal (Chapters I-III)."""
B = []
def ch(n, t): B.append(("chapter", (n, t)))
def h2(t): B.append(("h2", t))
def p(t): B.append(("p", t))
def bl(items): B.append(("bullets", items))
def nl(items): B.append(("numbered", items))
def tb(**kw): B.append(("table", kw))
def fg(**kw): B.append(("fig", kw))
def eq(t, n): B.append(("eq", (t, n)))

# ================================================================ CHAPTER I
ch("I", "Introduction")
h2("1.1 Background of the Study")
p("Landlocked economies cannot receive fuel through their own seaports. Their refined products cross at least one neighbouring country, and a few refiners or traders can supply nearly all of it. The United Nations lists 32 landlocked developing countries (UN-OHRLLS, n.d.), yet research on them concentrates on trade costs and transit rather than on forecasting the flows their economies depend on (World Trade Organization, 2021).")
p("Kyrgyzstan illustrates the risk. It uses roughly 1.6 to 2 million tonnes of petroleum products a year, and official statements put Russia’s share of supply at about 93% (Economist.kg, 2026; 24.kg, 2025). Russia restricted gasoline and diesel exports in 2023 and banned gasoline exports in 2024 and again from October to December 2025 (Global Trade Alert, 2023, 2025). Supplies to Kyrgyzstan were formally exempt, yet in mid-2026 AI-95 gasoline ran out at Bishkek stations, the government banned fuel exports, and stocks fell to two or three weeks of use against a 2.5-month target (Kun.uz, 2026; Kwan, 2026). Customs data captured the event: in August 2026 Kyrgyz gasoline imports in UN Comtrade were 16.9 thousand tonnes (kt), about 39% of the 2024–2025 monthly average.")
p("UN Comtrade reports monthly imports by country, six-digit Harmonized System (HS) code and partner, with net mass and customs value in separate fields (United Nations Statistics Division, n.d.), so physical volume need not be inferred from prices. The data are also released late, revised and sometimes inconsistent (Hu et al., 2022). These properties decide what a forecaster could actually have known on any date, and they are part of the problem studied here.")

h2("1.2 Statement of the Problem")
p("National statistics describe what fuel arrived in the past; they do not say how much is likely to arrive next month, how uncertain that is, or how likely a shortfall is. Supplier-concentration indices describe exposure but are rarely tested as predictors (Ang et al., 2015), and the only test found showed concentration to be a weak short-run signal (Kwon & Jeong, 2026). Studies that forecast petroleum imports are single-country, mostly annual, mostly in value terms and deterministic (Santi et al., 2023; Qin et al., 2026).")
p("The central research problem is therefore: *to what extent can monthly physical imports of refined petroleum in landlocked economies, and the risk of a supply shortfall, be forecast out of sample with calibrated uncertainty, using only the information available on the forecast date?* Answering it matters because stock policy and emergency purchasing depend on the lower tail of the supply distribution, not on its average.")

h2("1.3 Purpose and Objectives of the Study")
p("The purpose of the study is to determine whether such forecasts can be made with useful, calibrated accuracy, and under what conditions globally trained deep learning improves on gradient boosting and simple baselines. The specific objectives are to:")
nl([
    "build an audited, reproducible monthly panel of refined-fuel imports for landlocked economies, validated against official sources;",
    "define a shortfall target that separates supply stress from weak demand;",
    "compare baseline, tree-based and global neural models under evaluation that respects publication lags;",
    "measure by ablation the value of pooling, supplier structure and shock information;",
    "calibrate forecasts and compare shortfall warnings with concentration screening; and",
    "deliver a prototype risk monitor.",
])

h2("1.4 Research Questions and Hypotheses")
p("The study will answer four research questions, each paired with a working hypothesis that is fixed before modelling and will be tested at the 5% level with Holm (1979) correction. A hypothesis that is not supported is an acceptable, informative outcome.")
bl([
    "RQ1. Does training one model across countries improve Kyrgyz forecasts over local models and the seasonal naive benchmark? H1: global models reduce Kyrgyz MASE by at least 5% relative to the best local model at a three-month horizon.",
    "RQ2. Do global neural models outperform gradient boosting in normal and shock periods? H2: they do not beat LightGBM overall but do beat it in documented shock windows.",
    "RQ3. Do supplier structure and shock information add predictive value beyond a series’ own history? H3: they reduce pinball loss by at least 3% for high-dependence series.",
    "RQ4. Can calibrated forecasts warn of shortfalls better than concentration screening? H4: forecast-based shortfall probability gives higher PR-AUC, and higher recall at a fixed alert budget, than ranking by the Herfindahl–Hirschman index (HHI).",
])

h2("1.5 Significance of the Study")
p("The study will contribute a tested benchmark of global deep learning against gradient boosting for monthly physical fuel imports, a transparent route from raw customs records to a validated physical target under real publication lags, and a public-data risk monitor; it does not claim a new neural architecture. It differs from earlier work by joining streams that have been studied separately: trade forecasting at annual or value scale (Sellami et al., 2024), backward-looking security-of-supply indices (Cohen et al., 2011), and customs-based early warning for a coastal economy (Kwon & Jeong, 2026).")
p("The study targets three audiences. Energy ministries, state fuel companies and statistical offices in landlocked economies gain an early, quantified signal for stock planning; fuel importers gain a public estimate of supply risk by product; and forecasting researchers gain evidence on when cross-learning and deep learning help on short, heterogeneous panels, a question on which the literature disagrees (Montero-Manso & Hyndman, 2021; Yolusever, 2026). The study also seeks to change two practices: monitoring supply risk with static indices instead of tested probabilistic forecasts, and evaluating trade forecasts on random splits instead of on data as they were released. The researcher, based in Bishkek, observed the 2026 shortage directly; the study grew from the question of whether public data could have anticipated it.")

h2("1.6 Scope and Delimitations")
p("The study will forecast monthly imports of a gasoline proxy (HS 271011 and 271012) and of distillates with blends (HS 271019 plus 271020) from January 2015 to the latest available month. Because HS 271019 mixes diesel, kerosene and fuel oil, the second target will be labelled “distillates,” never “diesel.” Crude oil and liquefied petroleum gas are excluded as targets. Customs records measure imports, not consumption, and the models are not intended to predict political decisions such as export bans.")

h2("1.7 Overview of Methodology and Definition of Terms")
p("The study will use a quantitative, comparative design in which each research question is answered by changing one component (model class, training scope, information source or output) while data, validation protocol and metrics stay fixed. Forecasts will be made at rolling origins using only data released by each origin, and scored with scale-free errors, proper scoring rules and formal tests. Key terms are used as follows:")
bl([
    "*Physical imports*: net mass recorded by customs, in tonnes.",
    "*Supply shortfall*: a month in which trailing three-month import mass falls below 75% of its seasonal baseline (Section 3.6).",
    "*Publication lag*: time between the end of a month and the first public release of its record; *as-of evaluation* uses only data released by the forecast origin.",
    "*Global model*: one model whose parameters are shared across all series; a *local model* is fitted to one series.",
    "*Calibration*: agreement between stated probabilities or interval levels and observed frequencies.",
])
p("Chapter II reviews the related literature and identifies the research gap; Chapter III presents the conceptual framework and methodology. Appendixes report preliminary data validation and a small pilot.")

# ================================================================ CHAPTER II
ch("II", "Review of Related Literature")
p("The review is organised thematically. It draws on a structured search of OpenAlex, Crossref, Semantic Scholar and arXiv plus citation chasing: 6,526 records reduced to 5,230 unique works, 1,600 were screened and 184 were included after verification against DOI registries. Google Scholar could not be searched systematically, so recall for grey literature is limited.")

h2("2.1 Forecasting Petroleum Imports")
p("Direct studies are few and single-country. Indonesia’s oil and gas imports were forecast with a multilayer perceptron on annual volumes (Wanto et al., 2019), SARIMA on monthly values (Santi et al., 2023) and a gated recurrent unit (Saputra et al., 2024); China’s import demand with machine-learning regressors (Qin et al., 2026); and Nepal’s petroleum imports, a landlocked case, econometrically without forecast comparison (Pradhan et al., 2023). Three weaknesses recur: values or annual totals instead of monthly physical flows; contemporaneous regressors that are unknown on the forecast date; and single splits with percentage or R^{2} metrics. One study turned annual data into 200 interpolated points and reported 99% accuracy (Khajoui et al., 2024). Two 2026 studies come closer, masking inputs by release calendar for oil exports (Intarasat et al., 2026) or forecasting raw-material trade with a Temporal Fusion Transformer (Arrar et al., 2025), but neither produces calibrated forecasts of fuel imports.")

h2("2.2 Energy Security, Concentration and Early Warning")
p("Energy-security research measures dependence with indices of supplier diversification (Cohen et al., 2011) and political or transit risk (Le Coq & Paltseva, 2009); a review of 104 studies found such indices context-specific and hard to compare (Ang et al., 2015). They describe exposure after the fact and are rarely tested as predictors. The closest precedent is Kwon and Jeong (2026), who predicted import-disruption onsets for 5,925 Korean products with walk-forward validation and found that concentration rankings performed below the base rate. Their setting is a maritime economy, all goods and a ranking output; whether their finding holds where one supplier provides over 90% of fuel is open. Geopolitical shocks, measured by the index of Caldara and Iacoviello (2022), lower energy import volumes in the short run (Lin & Zhang, 2025), and training windows that cross structural breaks can damage fuel forecasts (Li et al., 2022), so the 2022–2026 period is a natural stress test.")

h2("2.3 Global Models, Deep Learning and Gradient Boosting")
p("Global models trained across many series can match or beat local ones (Montero-Manso & Hyndman, 2021; Hewamalage et al., 2022b). This is what makes deep learning feasible here: about 130 Kyrgyz months cannot train a network, but a pooled panel may support a small one. The gain is not guaranteed: pooling reversed on heterogeneous short panels (Yolusever, 2026), while a multi-country Temporal Fusion Transformer (Lim et al., 2021) beat regressions for 25 OECD economies (Laborda et al., 2023). Recurrent networks (Hochreiter & Schmidhuber, 1997; Cho et al., 2014) and N-BEATS (Oreshkin et al., 2020) are standard neural candidates, but gradient-boosted trees (Chen & Guestrin, 2016; Ke et al., 2017) dominated the M5 competition (Makridakis et al., 2022a) and remain strong on medium-sized tabular data (Grinsztajn et al., 2022). A simple linear model even matched Transformers on larger benchmarks (Zeng et al., 2023). The literature therefore supports testing deep learning by regime and treating boosting as the main rival.")

h2("2.4 Probabilistic Forecasting and Real-Time Evaluation")
p("Probabilistic forecasts should maximise sharpness subject to calibration (Gneiting et al., 2007) and be scored with proper rules such as the continuous ranked probability score (Gneiting & Raftery, 2007). Electricity forecasting has a probabilistic benchmark tradition (Hong et al., 2016), and conformalised quantile regression offers a model-agnostic way to correct interval coverage (Romano et al., 2019). Separately, macroeconomics has shown that accuracy measured on revised data can differ from what was achievable in real time (Stark & Croushore, 2002; Baumeister & Kilian, 2011). Good evaluation practice requires rolling origins (Tashman, 2000), scale-free errors (Hyndman & Koehler, 2006) and formal tests (Diebold & Mariano, 1995; Harvey et al., 1997). None of the reviewed fuel-import studies reported calibrated distributions or lag-aware evaluation.")

h2("2.5 Synthesis and Research Gap")
p("Table 1 compares the closest studies and Table 2 summarises what is and is not yet known.")
tb(caption="Comparison of the Principal Related Studies",
   cols=["Study", "Problem and data", "Method", "Limitation for this study"],
   widths=[1.45, 1.8, 1.3, 1.45],
   rows=[
    ["Kwon & Jeong (2026)", "Disruption warning; Korea, 5,925 products, monthly", "Boosting, logistic; walk-forward", "Maritime; all goods; ranking only"],
    ["Wanto et al. (2019)", "Oil and gas imports; Indonesia, annual", "Neural network", "Annual; point forecast"],
    ["Santi et al. (2023)", "Oil and gas import value; Indonesia", "SARIMA", "Value, not mass; one model"],
    ["Pradhan et al. (2023)", "Petroleum imports; Nepal (landlocked)", "Econometric", "No forecast comparison"],
    ["Laborda et al. (2023)", "GDP; 25 OECD countries", "Multi-country TFT", "Not trade; supports pooling"],
    ["Cohen et al. (2011)", "Supply diversification", "HHI index", "Not tested as a predictor"],
   ])
tb(caption="What Is Known and Not Yet Known From the Reviewed Literature",
   cols=["Theme", "What is established", "What is not yet known"],
   widths=[1.4, 2.3, 2.3],
   rows=[
    ["Fuel-import forecasting", "Single-country point forecasts", "Monthly physical forecasts across landlocked economies"],
    ["Global models", "Cross-learning helps when series are similar", "Whether pooling helps weakly co-moving fuel series"],
    ["Deep learning vs trees", "Trees are strong on small tabular data", "Whether neural models gain in shock periods"],
    ["Probabilistic forecasting", "Proper scoring and conformal calibration", "Calibrated distributions for fuel imports"],
    ["Real-time evaluation", "Revisions change conclusions in macroeconomics", "Lag-aware evaluation of Comtrade forecasts"],
    ["Supply security", "Concentration describes exposure", "Its predictive value under a dominant supplier"],
   ])
p("*Research gap.* A new country alone is not a gap. The gap appears when the problem’s requirements are set against the closest streams: trade forecasting predicts annual or value flows, security-of-supply research measures dependence after the fact, and customs early warning ranks products for a coastal economy. No study was found that tests, for landlocked economies, whether monthly physical fuel imports and shortfalls can be forecast out of sample with calibrated uncertainty under real publication lags, or whether pooling and supplier information help. This is a finding of the stated search, not proof of absence, and the study does not assume the integrated approach is superior; that is the question it will answer.")

# ================================================================ CHAPTER III
ch("III", "Conceptual Framework and Research Methodology")
h2("3.1 Conceptual Framework")
p("The framework (Figure 1) links the information released by a forecast origin, through a forecasting process, to a predictive distribution of future physical imports, from which shortfall probability is derived and evaluated. It draws on the global-model argument (Montero-Manso & Hyndman, 2021), the principle of sharpness subject to calibration (Gneiting et al., 2007) and the real-time-data argument (Stark & Croushore, 2002). Its key assumptions are that import dynamics are stable enough within a training window to be learned, that cleaned customs net mass measures physical supply, that a seasonal three-month shortfall is a reasonable proxy for supply stress, and that forecast errors are close enough to exchangeable for conformal calibration. Each will be checked, not assumed. Table 3 lists the variables.")
fg(path="figures/fig_conceptual.png", width=5.9, caption="Conceptual Framework of the Study")
tb(caption="Variables of the Study",
   cols=["Role", "Variable", "Measurement"],
   widths=[1.4, 2.3, 2.3],
   rows=[
    ["Dependent", "Monthly import mass (gasoline proxy, distillates)", "Log tonnes, cleaned net mass"],
    ["Dependent", "Shortfall indicator and probability", "Equations 2 and 3"],
    ["Independent (design)", "Model class; local or global training", "Baseline, boosted tree, neural network"],
    ["Independent (information)", "Own history; supplier structure", "Lags 1–12; trailing HHI, Russia share"],
    ["Independent (information)", "Shocks; prices; risk; macro", "Announced bans; Brent; GPR; FX; CPI"],
    ["Moderating", "Publication lag, revisions, heterogeneity, breaks", "Release dates; vintages; break tests"],
   ])

h2("3.2 Research Design")
p("The study will be quantitative, comparative and predictive, based on secondary data. A quantitative design fits because the questions concern measurable accuracy, calibration and detection; a comparative design fits because each question asks whether one modelling choice beats another under identical conditions. The study will not make causal claims: external indicators are candidate predictors, not causes.")

h2("3.3 Data, Sources and Research Setting")
p("The data will be secondary, quantitative time series (Table 4). The primary records are monthly bilateral customs entries of reporter, HS code, partner, month, net mass and value. Official Kyrgyz statistics will be used for validation, and a hand-coded calendar of export restrictions, each with source and announcement date, will be compiled. The setting is the refined-fuel trade of landlocked economies, extended with European landlocked states that report reliably; the population is every monthly gasoline and distillate import series for these countries in UN Comtrade from 2015. Kyrgyzstan is the detailed case because of its single-supplier dependence, its documented 2026 shortage and its national validation data. No human participants are involved.")
tb(caption="Data Sources and Their Use",
   cols=["Source", "Frequency", "Use"],
   widths=[2.6, 1.0, 2.4],
   rows=[
    ["UN Comtrade API (United Nations Statistics Division, n.d.)", "Monthly", "Targets, suppliers, release dates"],
    ["Russia as reporter (mirror data)", "Monthly", "Cross-check of Kyrgyz imports"],
    ["NSC energy balance and reports (National Statistical Committee of the Kyrgyz Republic, 2026)", "Annual / monthly", "Mass and value checks; vintages"],
    ["Brent price (U.S. Energy Information Administration, n.d.); GPR (Caldara & Iacoviello, 2022)", "Daily / monthly", "External conditions"],
    ["Exchange rates, CPI, World Bank indicators (World Bank, n.d.)", "Monthly / annual", "External conditions; scale"],
    ["Export restrictions (Global Trade Alert, 2023, 2025)", "Event", "Shock calendar"],
   ])

h2("3.4 Data Collection Procedure and Sampling")
p("Data will be collected by a Python pipeline that queries the Comtrade API with credentials kept in environment variables, stores each raw response with its retrieval date and hash, and writes versioned datasets. This instrument already exists: it holds 878 validated responses and passes 24 automated tests. A second snapshot will be taken before modelling so that revisions can be measured.")
p("No random sample will be drawn. Series will be selected purposively by rules fixed before modelling (Table 5). In preliminary work these rules gave an evaluation set of 22 series from 13 countries (3,021 monthly observations) and a training pool of 44 series from 22 countries (5,549 observations); Figure 2 shows coverage. Kyrgyzstan is the only Central Asian country in Tier 1.")
tb(caption="Series Selection Criteria by Tier",
   cols=["Tier", "Criteria", "Use"],
   widths=[0.7, 3.9, 1.4],
   rows=[
    ["1", "≥120 observed months; ≥85% coverage; no gap over six months; data to mid-2025 or later; ≥84 supplier months; median ≥100 t; exports below half of imports", "Evaluation and training"],
    ["2", "≥84 observed months and ≥84 supplier months", "Training only"],
    ["3", "Sparse or unusable reporting", "Descriptive only"],
   ])
fg(path="figures/fig09_coverage_heatmap.png", width=4.4, caption="Observed Gasoline Months per Year by Reporting Country (Lines Separate Tiers 1, 2 and 3)")

h2("3.5 Data Preparation")
p("Monthly totals will be rebuilt from partner rows, because the aggregate “World” row can be zero while partner rows contain trade. Masses will be accepted only in kilograms, with physically plausible implied densities, and unit values will be checked against a Brent-deflated rolling median; implausible masses will be removed while the original record is kept. Outliers will be flagged but kept, because shocks are the object of study. Missing months will never be filled with zeros and targets will never be interpolated; missing months will be excluded from training loss and scoring.")

h2("3.6 Key Measures")
p("Supplier concentration will be measured with the HHI, where s_{ijt} is the share of partner j in the import mass of series i in month t, pooled over a trailing twelve months:")
eq("HHI_{it} = Σ_{j} s_{ijt}^{2}", 1)
p("With Q_{it} the trailing three-month import mass and B_{it} the mean of the same calendar months in the previous three years, a shortfall month is")
eq("S_{it} = 1[ Q_{it} / B_{it} < 0.75 ]", 2)
p("with thresholds of 0.70 and 0.80 as sensitivity checks. Shortfall risk will be derived from each model’s forecast distribution, given the information set of data released by origin τ (r_{it} is the release date of observation t):")
eq("p̂_{i,τ+h} = Pr( Q_{i,τ+h} / B_{i,τ+h} < 0.75 | x_{it} : r_{it} ≤ τ )", 3)

h2("3.7 Models and Data Analysis")
p("*Models.* Models will be added in order of complexity so that each component’s benefit can be measured: naive, seasonal naive and twelve-month mean (lower bounds); ETS and SARIMA (local references); random forest; LightGBM and XGBoost (main rivals); and small global GRU, TCN and N-BEATS networks and a compact Temporal Fusion Transformer, retained only if validation supports it. Neural capacity will stay small (16–64 hidden units, a country embedding, dropout). Learned models will output quantiles by minimising pinball loss, and conformalised quantile regression (Romano et al., 2019) will adjust intervals on a later calibration window.")
p("*Validation.* Evaluation will use expanding rolling origins from January 2023, with horizons of one, three and six months plus the next-three-month total. At each origin only data released by that date will be visible; where a release date is missing, the reporter’s median lag will be applied. Random splits will not be used. Tuning will use only past data, and settings will be frozen before a final test block run once. Leave-one-country-out training will test transfer.")
p("*Metrics and tests.* MASE (Hyndman & Koehler, 2006) will be the primary point metric because it is comparable across countries; with seasonal period m = 12,")
eq("MASE = [ (1/n) Σ_{t} |y_{t} − ŷ_{t}| ] / [ (1/(T−m)) Σ_{t=m+1}^{T} |y_{t} − y_{t−m}| ]", 4)
p("Quantiles will be scored with pinball loss and an approximate CRPS, intervals by coverage and width at 80% and 95%, and shortfall warnings by PR-AUC, Brier score and recall at a fixed alert budget, which suit rare events (Saito & Rehmsmeier, 2015). Model differences will be tested with the corrected Diebold–Mariano test (Harvey et al., 1997) with Holm correction, and effect sizes with bootstrap intervals will always be reported because tests have low power on short samples. An ablation will remove one information source at a time (pooling, supplier features, shock calendar, external indicators, pre-2022 data, conformal step), and SHAP values (Lundberg & Lee, 2017) will help explain LightGBM forecasts. Table 6 matches each research question to its method.")
tb(caption="Matching of Research Questions to Methods and Evaluation",
   cols=["RQ / H", "Manipulated component", "Comparison", "Evaluation"],
   widths=[0.8, 2.0, 1.6, 1.6],
   rows=[
    ["RQ1 / H1", "Global vs local training", "Best local model, seasonal naive", "MASE at h = 3; HLN test"],
    ["RQ2 / H2", "Neural (GRU, TCN, N-BEATS, TFT) vs boosted trees", "LightGBM", "MASE, pinball loss by normal and shock windows"],
    ["RQ3 / H3", "Supplier and shock features added or removed", "Own-history model", "Pinball loss, high-dependence series"],
    ["RQ4 / H4", "Calibrated shortfall probability", "HHI ranking", "PR-AUC, recall at alert budget, calibration"],
   ])

h2("3.8 Flow of Research Activities and Data Recording")
p("Figure 3 and Table 7 show the planned stages. Every raw response, dataset and forecast will be stored with its version, date and input snapshot, all figures will be regenerated from scripts, and a decision log will record each change to rules or settings.")
fg(path="figures/fig_flow.png", width=5.9, caption="Flow of Research Activities")
tb(caption="Research Stages, Outputs and Indicative Schedule",
   cols=["Stage", "Output", "Timing"],
   widths=[2.6, 2.3, 1.1],
   rows=[
    ["1–2. Data acquisition and validation", "Validated dataset v1.0", "Completed"],
    ["3. Rule review and second snapshot", "Frozen rules; revision log", "Month 1"],
    ["4. As-of feature store", "Feature tables by origin", "Months 1–2"],
    ["5–6. Model benchmark and calibration", "Forecast archive; calibrated quantiles", "Months 2–3"],
    ["7. Evaluation, ablation, robustness", "Tests of H1–H4", "Month 4"],
    ["8. Risk monitor and thesis", "Prototype; final thesis", "Months 5–6"],
   ])

h2("3.9 Reliability and Validity")
p("Reliability will rest on versioned snapshots, frozen rules, scripted analysis, at least five random seeds and matched tuning budgets. The main threat to internal validity is information leakage, which will be controlled by as-of replay, by fitting all preprocessing on past data only, and by using a shock only after it was announced. Construct validity has been checked in preliminary work (Appendix A): Kyrgyz gasoline mass agrees with the national energy balance within a mean absolute 3.7% from 2018. Because 2016–2017 mirror data disagree sharply and post-2025 records appear to be first releases, results will be reported with and without 2015–2017 and evaluated on first-release data. External validity will be examined by leave-one-country-out tests and sensitivity checks on thresholds, lags, COVID-19 months and structural breaks (Bai & Perron, 2003); no claim will rest on a single shock.")

h2("3.10 Ethical Considerations")
p("All data are public, aggregate and non-personal, and will be used within their providers’ terms; API keys will never be stored in code. The work supports supply planning and gives no guidance on evading trade restrictions. Any practitioner review of the prototype will be voluntary and anonymous. Negative results will be reported as prominently as positive ones, all sources will be cited, and AI assistance will be disclosed in line with faculty rules.")
