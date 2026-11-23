# -*- coding: utf-8 -*-
"""Text of the thesis proposal. Markup inside strings: _{x} subscript, ^{x} superscript, *x* italic."""

TITLE = "Probabilistic Forecasting of Petroleum Imports and Supply-Shortfall Risk in Landlocked Economies"

ABSTRACT = [
    "Landlocked economies buy almost all of their refined fuel over a few overland routes and from very few suppliers, and they hold small stocks. A decision by one exporter can therefore become a domestic shortage within weeks, as Kyrgyzstan experienced in mid-2026 when AI-95 gasoline ran out at Bishkek filling stations. Existing security-of-supply indices describe this dependence after the fact, and existing trade-forecasting studies mostly predict annual values for single countries, so planners lack a tested, forward-looking measure of supply risk.",
    "This proposal sets out a quantitative, comparative study that will test whether monthly physical imports of refined petroleum, and the probability of a supply shortfall, can be forecast out of sample with calibrated uncertainty using only information public on each forecast date. Simple baselines, gradient-boosted trees and small global neural networks will be compared on a UN Comtrade panel of landlocked economies, with Kyrgyzstan as the detailed case. Preliminary work has produced a validated panel of 44 series from 22 countries (5,549 monthly observations); Kyrgyz gasoline volumes agree with the national energy balance within 3.7%. Evaluation will use lag-aware rolling origins, proper scoring rules, conformal calibration and formal accuracy tests. The expected contribution is a tested benchmark, a transparent route from customs records to a validated physical target, and a prototype risk monitor.",
]
KEYWORDS = "petroleum imports; probabilistic forecasting; supply-shortfall risk; landlocked economies; global forecasting models; gradient boosting; conformal prediction; publication lag; Kyrgyzstan"

ABBREVIATIONS = [
    ("API", "Application programming interface"),
    ("CIF", "Cost, insurance and freight"),
    ("CPI", "Consumer price index"),
    ("CRPS", "Continuous ranked probability score"),
    ("DL", "Deep learning"),
    ("ETS", "Exponential smoothing (error, trend, seasonal)"),
    ("FX", "Foreign exchange (rate)"),
    ("GPR", "Geopolitical risk index"),
    ("GRU", "Gated recurrent unit"),
    ("HHI", "Herfindahl–Hirschman index"),
    ("HLN", "Harvey–Leybourne–Newbold (corrected Diebold–Mariano test)"),
    ("HS", "Harmonized Commodity Description and Coding System"),
    ("kt", "Thousand tonnes"),
    ("LLDC", "Landlocked developing country"),
    ("MASE", "Mean absolute scaled error"),
    ("N-BEATS", "Neural basis expansion analysis for time series"),
    ("NSC", "National Statistical Committee of the Kyrgyz Republic"),
    ("PR-AUC", "Area under the precision–recall curve"),
    ("RQ", "Research question"),
    ("SARIMA", "Seasonal autoregressive integrated moving average"),
    ("SHAP", "Shapley additive explanations"),
    ("TCN", "Temporal convolutional network"),
    ("TFT", "Temporal Fusion Transformer"),
    ("UN", "United Nations"),
    ("WAPE", "Weighted absolute percentage error"),
]

# Body: list of (kind, payload)
# kinds: chapter (num, title), h2, h3, p, bullets(list), numbered(list), table(dict), fig(dict), eq((text,num))
B = []
def ch(n, t): B.append(("chapter", (n, t)))
def h2(t): B.append(("h2", t))
def h3(t): B.append(("h3", t))
def p(t): B.append(("p", t))
def bl(items): B.append(("bullets", items))
def nl(items): B.append(("numbered", items))
def tb(**kw): B.append(("table", kw))
def fg(**kw): B.append(("fig", kw))
def eq(t, n): B.append(("eq", (t, n)))

# ---------------------------------------------------------------- CHAPTER I
ch("I", "Introduction")
h2("1.1 Background of the Study")
p("Most countries can receive fuel through several seaports and from many suppliers. Landlocked economies cannot. Their refined products cross at least one neighbouring country by rail, road or pipeline, and a small number of refiners or traders can account for nearly all of what arrives. The United Nations lists 32 landlocked developing countries (UN-OHRLLS, n.d.), and research on these countries has concentrated on trade costs and transit corridors rather than on forecasting the flows that keep their economies running (World Trade Organization, 2021; Athukorala & Hill, 2023).")
p("Kyrgyzstan is a clear example. The country uses roughly 1.6 to 2 million tonnes of petroleum products a year, produces little of its own, and official statements put Russia’s share of supply at about 93% (Economist.kg, 2026; 24.kg, 2025). Russia restricted gasoline and diesel exports in September 2023, imposed a six-month gasoline export ban from March 2024 and reinstated a gasoline export ban for all exporters from October to December 2025 (Global Trade Alert, 2023, 2025; Enerdata, 2024). Supplies to Kyrgyzstan under intergovernmental agreements were formally exempt (24.kg, 2025). Nevertheless, when Russian refinery output fell in 2026, AI-95 gasoline ran out at Bishkek stations, the government banned fuel exports, and reported stocks fell to two or three weeks of consumption against a government target of 2.5 months (Kun.uz, 2026; Kwan, 2026; Economist.kg, 2026). A formal exemption did not guarantee physical supply.")
p("Customs data record such events. In August 2026, Kyrgyz gasoline imports reported to UN Comtrade were 16.9 thousand tonnes (kt), about 39% of the 2024–2025 monthly average, and Russia’s share of that month’s gasoline fell to 44%. UN Comtrade publishes monthly records by reporting country, six-digit Harmonized System (HS) code and partner, with net mass in kilograms and customs value in US dollars kept in separate fields (United Nations Statistics Division, n.d.). Physical volume therefore does not have to be inferred from prices. The same database also has well-documented weaknesses: reporters publish late and irregularly, partner rows and aggregate rows can disagree, some masses are wrong, and records are revised (Hu et al., 2022; Qodirova & Ellerton, 2026). These weaknesses are not incidental to the present study; they determine what a forecaster could actually have known on any given date.")

h2("1.2 Statement of the Problem")
p("National import statistics in Kyrgyzstan and comparable countries describe what arrived in the past. They are not designed to say how much fuel is likely to arrive next month, how uncertain that estimate is, or how likely a supply shortfall is. Security-of-supply indices such as supplier concentration describe structural exposure but have rarely been tested as predictors (Ang et al., 2015), and the one study that did test them found concentration to be a weak short-run signal for a maritime economy (Kwon & Jeong, 2026). Studies that do forecast petroleum imports are single-country, mostly annual, mostly in value terms and almost always deterministic (Wanto et al., 2019; Santi et al., 2023; Saputra et al., 2024; Qin et al., 2026).")
p("The central research problem of this study is therefore the following: *To what extent can monthly physical imports of refined petroleum in landlocked economies, and the risk of a supply shortfall, be forecast out of sample with calibrated uncertainty, using only the information that was available on the forecast date?* The problem is broader than point forecasting. It comprises a validated physical target, point and quantile forecasts, a shortfall probability, calibration under publication lags and data revisions, and a form in which the result can be used by planners. Resolving it matters because stock policy, emergency purchasing and supplier diversification all depend on the lower tail of the supply distribution, not on its average.")

h2("1.3 Purpose and Objectives of the Study")
p("The primary purpose of the study is to determine whether monthly physical imports of refined petroleum and supply-shortfall risk in landlocked economies can be forecast with useful and well-calibrated accuracy, and under what conditions globally trained deep learning models improve on gradient boosting and on simple statistical baselines. The specific objectives are to:")
nl([
    "build an audited, reproducible monthly panel of refined-fuel imports for landlocked economies from UN Comtrade, validated against official national sources;",
    "define a supply-shortfall target that separates supply stress from weak demand;",
    "compare baseline, tree-based and global neural models under rolling-origin evaluation that respects publication lags;",
    "measure, through ablation, the value of cross-country pooling, supplier structure and shock information;",
    "calibrate the forecast distributions and evaluate the resulting shortfall warnings against concentration-based screening; and",
    "deliver a working prototype risk monitor for research and planning use.",
])

h2("1.4 Research Questions")
p("The study will answer the following four research questions. Their link to the methodology is shown in Table 8 (Section 3.12).")
bl([
    "RQ1. Does training a single model across countries improve forecasts for Kyrgyzstan compared with local models and the seasonal naive benchmark?",
    "RQ2. Do global neural models outperform gradient boosting, in normal periods and in shock periods?",
    "RQ3. Do supplier structure and documented shock information add predictive value beyond a series’ own history?",
    "RQ4. Can calibrated probabilistic forecasts warn of supply shortfalls better than screening by supplier concentration?",
])

h2("1.5 Research Hypotheses")
p("The working hypotheses below are fixed before any model is trained. Each will be tested at the 5% significance level with Holm correction for multiple comparisons (Holm, 1979). A result that does not support a hypothesis is treated as an acceptable and informative outcome.")
bl([
    "H1. Global models reduce the Kyrgyz mean absolute scaled error (MASE) by at least 5% relative to the best local model at a three-month horizon.",
    "H2. Global neural models do not outperform LightGBM overall, but do outperform it in documented shock windows.",
    "H3. Adding supplier and shock information reduces pinball loss by at least 3% for series with high supplier dependence.",
    "H4. Forecast-based shortfall probability achieves a higher PR-AUC, and higher recall at a fixed alert budget, than ranking by the Herfindahl–Hirschman index (HHI).",
])

h2("1.6 Significance of the Study")
p("*Contribution.* The study will make three kinds of contribution. The scientific contribution will be a tested benchmark of global deep learning against gradient boosting for monthly physical fuel imports, including an out-of-sample test of whether concentration screening works where one supplier dominates. The methodological contribution will be a transparent route from raw customs records to a validated physical target, with explicit treatment of publication lag and data vintage. The applied contribution will be a public-data risk monitor.")
p("*How the study differs from earlier work.* Previous studies have treated the relevant components separately: trade forecasting has moved toward graph and neural models at annual or aggregate scale (Sellami et al., 2024; Zhao et al., 2026), security-of-supply research has developed backward-looking indices (Cohen et al., 2011; Le Coq & Paltseva, 2009), and customs-based early warning has been demonstrated for a coastal economy across all goods (Kwon & Jeong, 2026). The present study “jumps in” where these streams meet: it forecasts physical monthly fuel flows, produces calibrated distributions rather than single numbers, evaluates them as the data were actually released, and does so for a group of countries that has not been studied as a group in forecasting research.")
p("*Target audience and why it matters to them.* The study addresses three audiences. For energy ministries, state fuel companies and statistical offices in landlocked economies, it offers an early, quantified signal for stock planning against targets such as Kyrgyzstan’s 2.5-month reserve. For fuel traders and importers, it offers a public estimate of supply risk by product. For forecasting researchers, it offers evidence on when cross-learning and deep learning help on short, heterogeneous economic panels, a question on which the literature disagrees (Montero-Manso & Hyndman, 2021; Yolusever, 2026).")
p("*Key issues and practices.* The study seeks to draw attention to two issues that are usually overlooked: that customs data are released late and revised, so many published forecasting results would not have been achievable in real time; and that the reliability of supply, not only its expected level, is what matters to a landlocked importer. The practices it seeks to influence are how fuel-supply risk is monitored (from static indices toward tested probabilistic forecasts) and how trade-forecasting studies are evaluated (from random or single splits toward rolling, lag-aware evaluation).")
p("*Motivation of the researcher.* The researcher lives in Bishkek and observed the 2026 shortage directly. The study grew out of the practical question of whether the shortage could have been anticipated from public data, and of how much warning such data could realistically provide.")

h2("1.7 Scope and Delimitations")
p("The study will forecast monthly imports of two products from January 2015 to the most recent month available: a gasoline proxy (HS 271011 and 271012) and distillates with blends (HS 271019 plus 271020). Liquefied petroleum gas will be described but not forecast, and crude oil and the HS 2710 heading total are excluded as targets. Separate diesel, jet-fuel and fuel-oil targets are not possible at the six-digit level, so the distillate target will always be labelled “distillates” rather than “diesel.” The geographic scope is landlocked economies with usable monthly reporting, extended with European landlocked economies that report reliably and enlarge the training panel. Customs records measure imports, not consumption; stocks, local refining and informal trade lie outside the data. The models are not intended to predict political decisions such as export bans, only how quickly measurable risk rises once early signals appear.")

h2("1.8 Overview of the Research Methodology")
p("The study will follow a quantitative, comparative, data-driven design. It will be organised as a sequence of controlled comparisons, each of which answers one research question by changing a single component (model class, training scope, information source or output type) while holding the data, validation protocol and metrics fixed. Forecasts will be produced at expanding rolling origins from January 2023 onward, using at each origin only data that had been released by that date. Point accuracy, quantile accuracy, interval coverage and shortfall detection will be measured with scale-free errors and proper scoring rules, and model differences will be tested with the corrected Diebold–Mariano test. Chapter III describes the design in full.")

h2("1.9 Definition of Terms")
bl([
    "Landlocked economy: a country without direct access to a seacoast; here, the UN list of landlocked developing countries plus European landlocked states with reliable reporting.",
    "Physical imports: the net mass of a product recorded by customs, in tonnes, as opposed to its customs value.",
    "Supply shortfall: a month in which the trailing three-month import mass falls below 75% of its seasonal baseline (Section 3.9).",
    "Publication lag: the time between the end of a reference month and the first public release of its customs record.",
    "As-of (real-time) evaluation: evaluation in which each forecast uses only data that had been published by the forecast origin.",
    "Global model: a single model whose parameters are shared across all series in the panel; a local model is fitted to one series only.",
    "Calibration: agreement between stated forecast probabilities or interval levels and observed frequencies.",
])

h2("1.10 Organization of the Proposal")
p("Chapter II reviews the related literature thematically and identifies the research gap. Chapter III presents the conceptual framework and the research methodology, including data, models, evaluation, the matching of research questions to methods, the work plan, reliability and validity, and ethics. The appendixes report the preliminary data-validation results and a small, untuned pilot that tested whether the design can run.")

# ---------------------------------------------------------------- CHAPTER II
ch("II", "Review of Related Literature")
p("This chapter reviews published and grey literature related to the study. The review is organised thematically, with a short chronological thread within each theme, and closes with a synthesis of what is and is not yet known. It builds on a structured search of OpenAlex, Crossref, Semantic Scholar and arXiv, supplemented by citation chasing and institutional sources: 79 queries returned 6,526 records, which reduced to 5,230 unique works; 1,600 titles and abstracts were screened and 184 works were included, each verified against a DOI registry or the publisher’s file. Google Scholar and ScienceDirect could not be searched systematically because of access restrictions, so recall for grey literature is lower than in a full systematic review.")

h2("2.1 Forecasting Petroleum and Energy Imports")
p("The direct literature on forecasting petroleum imports is thin and consists almost entirely of single-country studies. Early work forecast Indonesia’s annual export and import volumes of crude oil and products with a multilayer perceptron (Wanto et al., 2019) and Taiwan’s crude import demand with hybrid soft-computing schemes (Shao et al., 2014). More recent studies forecast Indonesia’s monthly oil and gas import values with SARIMA (Santi et al., 2023) and a gated recurrent unit (Saputra et al., 2024), India’s crude and product imports with ARIMA (Babu et al., 2024) and China’s oil import demand with machine-learning regressors (Qin et al., 2026). For a landlocked country, Pradhan et al. (2023) analysed Nepal’s petroleum imports econometrically but did not compare forecasting methods.")
p("Three weaknesses recur. First, most studies predict values, which mix price and quantity, or annual totals, which hide the monthly dynamics of a supply shock. Second, several use contemporaneous explanatory variables such as GDP that are not known on the forecast date, which leaks future information (Shao et al., 2014; Qin et al., 2026). Third, evaluation is often a single split with percentage or R^{2} metrics; one study converted annual data into 200 interpolated seasonal points before reporting 99% accuracy (Khajoui et al., 2024), a practice that inflates both the sample and the apparent skill. Two 2026 studies move closer to the present problem: a nowcasting model that masks inputs by release calendar for oil exports (Intarasat et al., 2026) and a Comtrade-based Temporal Fusion Transformer for raw-material trade (Arrar et al., 2025). Neither forecasts physical fuel imports with calibrated uncertainty.")

h2("2.2 Energy Security, Supplier Concentration and Early Warning")
p("Energy-security research measures dependence mainly through indices. Cohen et al. (2011) tracked diversification of oil and gas supply with the HHI; Le Coq and Paltseva (2009) added political and transit risk; and Ang et al. (2015), reviewing 104 studies, found that definitions are context-specific and indices hard to compare. For Central Asia, Akhmetov (2015) computed a risky external-supply index for oil well above the European Union’s. Network studies simulate how diversification makes the global oil trade more resilient (Chen et al., 2025), but such studies do not forecast out of sample. These indices are useful descriptions, but they look backward and have rarely been tested as predictors.")
p("The closest precedent for the present study is Kwon and Jeong (2026). Using monthly HS six-digit imports of 5,925 Korean products from 2010 to 2025 and walk-forward validation, they predicted import-disruption onsets, defined as persistent quantity shortfalls with rising unit values, and found that a top-5% watchlist had about 1.7 times the base-rate precision, while concentration rankings performed below the base rate. Their setting differs from the present one in three ways: Korea is a maritime economy, the target is all goods, and the output is a ranking rather than a calibrated volume. Whether their negative finding for concentration holds where one supplier provides over 90% of supply is an open question. Other early-warning work either evaluates in sample (Yokuş, 2024) or concerns electricity rather than traded fuel (Khan & Wyrwa, 2025).")

h2("2.3 Global Forecasting Models")
p("A global model is trained on many related series at once. Montero-Manso and Hyndman (2021) showed that global models are not more restrictive than local ones and can be more accurate as the number of series grows; simulation and benchmark studies support cross-learning when series share structure (Semenoglou et al., 2021; Hewamalage et al., 2022b). This is the only reason deep learning is feasible in the present setting: about 130 monthly Kyrgyz observations cannot train a neural network, whereas a pooled panel may support a small one. The benefit is not automatic. On short heterogeneous panels, pooling helped on Eurostat data but the gain reversed in simulation once cross-country differences became large (Yolusever, 2026), while a multi-country Temporal Fusion Transformer outperformed regressions for 25 OECD GDP series (Laborda et al., 2023). These findings are consistent if the value of pooling depends on how similar the series are, which is why the present study will test pooling directly rather than assume it.")

h2("2.4 Deep Learning Versus Gradient Boosting")
p("Recurrent networks such as long short-term memory (Hochreiter & Schmidhuber, 1997) and gated recurrent units (Cho et al., 2014) remain standard sequence models (Hewamalage et al., 2021), and probabilistic global networks such as DeepAR (Salinas et al., 2020) and N-BEATS (Oreshkin et al., 2020) have performed well on large benchmarks. However, tree ensembles (Breiman, 2001; Chen & Guestrin, 2016; Ke et al., 2017) dominated the M5 accuracy competition (Makridakis et al., 2022a; Januschowski et al., 2022), remain state of the art on medium-sized tabular data (Grinsztajn et al., 2022), and a windowed boosted tree competed with many deep models (Elsayed et al., 2021). A one-layer linear model matched long-horizon Transformers on far larger datasets than this study has (Zeng et al., 2023). In energy and trade, results depend on data volume: XGBoost far outperformed an LSTM on a single short annual series, whereas the Temporal Fusion Transformer (Lim et al., 2021) did well on a multi-country panel (Laborda et al., 2023). The literature therefore supports testing deep learning by regime and data size, and treating gradient boosting as the main rival rather than a formality.")

h2("2.5 Probabilistic Forecasting and Calibration")
p("The evaluation standard for probabilistic forecasts is settled: forecasts should maximise sharpness subject to calibration (Gneiting et al., 2007) and be scored with strictly proper rules such as the continuous ranked probability score (Gneiting & Raftery, 2007). Electricity forecasting has an established probabilistic benchmark tradition (Hong et al., 2016) and retail forecasting has the M5 uncertainty competition (Makridakis et al., 2022b). Model-agnostic calibration layers are available, including conformalised quantile regression (Romano et al., 2019) and adaptive conformal inference for time series (Zaffran et al., 2022). Neural networks are often poorly calibrated (Guo et al., 2017), so calibration must be measured rather than assumed. Despite this mature toolkit, no study of national fuel-import forecasting found in the review reported calibrated distributions.")

h2("2.6 Real-Time Data, Publication Lags and Data Quality")
p("Macroeconomic forecasting has long shown that results obtained on revised data can differ from what was achievable in real time (Stark & Croushore, 2002), and that unequal release dates create a “ragged edge” at the end of the sample (Wallis, 1986). Baumeister and Kilian (2011) built monthly real-time vintages for oil-market data and showed that conclusions about forecast accuracy depend on them. Trade data have specific problems: Comtrade contains statistical imbalances between headings and subheadings that are frequent for fossil fuels (Hu et al., 2022) and imputed quantities and unit values (Qodirova & Ellerton, 2026), and mirror-data discrepancies increased under sanctions (Golovanova et al., 2026). Evaluation practice in forecasting recommends rolling origins rather than random splits (Tashman, 2000), scale-free error measures (Hyndman & Koehler, 2006), care with cross-validation (Hewamalage et al., 2022a) and formal tests of predictive accuracy (Diebold & Mariano, 1995; Harvey et al., 1997). Publication-lag-aware evaluation of Comtrade-based forecasts was not found in the reviewed literature.")

h2("2.7 Geopolitical Shocks and Structural Change")
p("The news-based geopolitical risk (GPR) index of Caldara and Iacoviello (2022) is the standard measure of geopolitical tension. GPR shocks lower China’s energy import volumes in the short run (Lin & Zhang, 2025) and raise the hazard that energy-import relationships end, more for petroleum than for coal or gas (Peng et al., 2025). Refined products can become scarce even when crude oil is available, and product-dependent importers suffer most (Luong, 2026). For the region, Western sanctions on Russia after 2022 reshaped trade through Central Asia (Chupilkin et al., 2023). Structural change also affects forecast training: windows that cross a break can damage gasoline demand forecasts (Li et al., 2022). The period 2022–2026, with sanctions, export bans and shifting suppliers, therefore offers a direct test of model robustness.")

h2("2.8 Landlocked Economies and Kyrgyzstan")
p("Landlocked-country research concentrates on trade costs, transit and connectivity (World Trade Organization, 2021). Kyrgyzstan has been described as “double-landlocked” in trade-policy terms (Athukorala & Hill, 2023), and institutional sources report that over 90% of its oil products are imported, mainly from Russia and Kazakhstan (International Energy Agency, 2020, 2022). Import-dependence studies exist for Nepal (Pradhan et al., 2023), but landlocked importers have not been studied as a group in energy-import forecasting. Whether group status matters is itself an empirical question; the present study will treat it as context rather than claim it as a finding.")

h2("2.9 Synthesis: What Is Known and What Is Not Known")
p("Table 1 compares the studies closest to the proposed research, and Table 2 summarises what the reviewed literature establishes and what it leaves open.")
tb(caption="Comparison of the Principal Related Studies and Their Relevance to the Proposed Research",
   cols=["Study", "Problem and data", "Method", "Limitation relative to this study"],
   widths=[1.45, 1.75, 1.35, 1.45],
   rows=[
    ["Kwon & Jeong (2026)", "Import-disruption warning; Korea, 5,925 HS6 products, monthly", "Gradient boosting, logistic; walk-forward", "Maritime; all goods; ranking, no calibrated volume"],
    ["Wanto et al. (2019)", "Oil and gas import volume; Indonesia, annual", "Multilayer perceptron", "Annual; single country; point forecast"],
    ["Santi et al. (2023)", "Oil and gas import value; Indonesia, monthly", "SARIMA", "Value, not mass; one model"],
    ["Qin et al. (2026)", "Oil import demand; China", "Grey relational analysis, ML", "Contemporaneous regressors; point forecast"],
    ["Pradhan et al. (2023)", "Petroleum imports; Nepal (landlocked)", "Econometric analysis", "No forecast comparison"],
    ["Sellami et al. (2024)", "Bilateral trade; Comtrade, annual", "Graph neural networks vs random forest", "Annual; value, not mass"],
    ["Laborda et al. (2023)", "GDP; 25 OECD countries", "Multi-country TFT", "Not trade; supports pooling"],
    ["Intarasat et al. (2026)", "Oil-export nowcast; Norway, Thailand", "Release-calendar masking", "Exports; not probabilistic"],
    ["Cohen et al. (2011)", "Energy security; supply diversification", "HHI index", "Backward-looking; not tested as predictor"],
   ])
tb(caption="Summary of What Is Known and Not Yet Known From the Reviewed Literature",
   cols=["Theme", "What is established", "What is not yet known"],
   widths=[1.4, 2.3, 2.3],
   rows=[
    ["Fuel-import forecasting", "Single-country studies with point forecasts are feasible", "Monthly physical forecasts across a panel of landlocked economies"],
    ["Global models", "Cross-learning helps when series share structure", "Whether pooling helps short, weakly co-moving fuel series"],
    ["Deep learning vs trees", "Trees are strong on small tabular data", "Whether neural models gain in shock periods for fuel imports"],
    ["Probabilistic forecasting", "Proper scoring and conformal calibration are mature", "Calibrated distributions for national fuel imports"],
    ["Real-time evaluation", "Revisions change conclusions in macroeconomics", "Lag-aware evaluation of Comtrade-based forecasts"],
    ["Supply security", "Concentration indices describe exposure", "Predictive value of concentration where one supplier dominates"],
   ])
p("*Research gap.* A new country alone is not a research gap. The gap appears when the requirements of the problem are set against what the closest research streams provide. Trade forecasting predicts annual or value flows at large scale; security-of-supply research measures dependence after the fact; and customs-based early warning, the closest stream, targets a coastal economy across all goods and ranks products. No study was found that tests, for landlocked economies, whether monthly physical refined-fuel imports and shortfalls can be forecast out of sample with calibrated uncertainty under real publication lags, or whether pooling across such countries and adding supplier information helps. This is a finding of the stated search, not proof that no such study exists, and the study does not assume that the integrated approach is superior; that is the empirical question it will answer.")

# ---------------------------------------------------------------- CHAPTER III
ch("III", "Conceptual Framework and Research Methodology")
h2("3.1 Conceptual Framework")
p("The conceptual framework (Figure 1) orders the study around a single relationship: the information available at a forecast origin is transformed by a forecasting process into a predictive distribution of future physical imports, from which a shortfall probability is derived and then evaluated. The framework draws on three inputs from the review: the global-model argument that shared parameters can compensate for short series (Montero-Manso & Hyndman, 2021), the probabilistic-forecasting principle of sharpness subject to calibration (Gneiting et al., 2007), and the real-time-data argument that only released information may be used (Stark & Croushore, 2002).")
fg(path="figures/fig_conceptual.png", width=6.0, caption="Conceptual Framework of the Study")
p("The framework rests on four key assumptions: that the relationship between past and future imports is stable enough within a training window to be learned; that customs net mass, after cleaning, is a valid measure of physical supply; that a trailing three-month shortfall against a seasonal baseline is a reasonable proxy for supply stress; and that forecast errors are close enough to exchangeable for conformal calibration to be approximately valid. Each assumption will be checked rather than taken for granted. Table 3 lists the variables and their presumed relationships.")
tb(caption="Variables of the Study and Their Role in the Conceptual Framework",
   cols=["Role", "Variable", "Measurement"],
   widths=[1.4, 2.2, 2.4],
   rows=[
    ["Dependent", "Monthly import mass of gasoline proxy and distillates", "Log tonnes, cleaned customs net mass"],
    ["Dependent", "Supply-shortfall indicator and probability", "Equations 2 and 3"],
    ["Independent (design)", "Model class; training scope (local or global)", "Baseline, boosted tree, neural network"],
    ["Independent (information)", "Own lags, rolling statistics, seasonal lag", "Lags 1–12 of released data"],
    ["Independent (information)", "Supplier structure", "Trailing HHI, Russia share, top-supplier share"],
    ["Independent (information)", "Shock calendar; prices; risk; macro", "Announced bans; Brent; GPR; FX; CPI"],
    ["Moderating", "Publication lag, revisions, panel heterogeneity, structural breaks", "Release dates; vintages; importer type; break tests"],
   ])

h2("3.2 Research Design")
p("The study will be a quantitative, comparative and predictive study based on secondary data. A quantitative design is appropriate because the research questions concern measurable forecast accuracy, calibration and detection performance, and because the data are numerical time series. A comparative design is appropriate because each research question asks whether one modelling choice performs better than another under identical conditions. The design will not attempt causal inference: correlations between external indicators and imports will be treated as candidate predictive signals, not as causes.")

h2("3.3 Type of Data")
p("The study will use secondary, quantitative, monthly and annual time-series data. The primary data will be monthly bilateral customs records, each a tuple of reporter, HS code, partner, trade flow, month, net mass and customs value. Supporting data will be annual national energy balances, national commodity tables and monthly operational reports for validation, together with daily oil prices, monthly geopolitical-risk indices, monthly exchange rates and consumer prices, and annual development indicators as external conditions. A hand-coded calendar of documented export restrictions, each with its source and announcement date, will be compiled from public sources.")

h2("3.4 Sources of Data")
p("Table 4 lists the sources. All are public, and none contains personal information.")
tb(caption="Data Sources and Their Use in the Study",
   cols=["Source", "Frequency", "Use"],
   widths=[2.4, 1.0, 2.6],
   rows=[
    ["UN Comtrade public API (United Nations Statistics Division, n.d.)", "Monthly", "Target, suppliers, exports, release dates"],
    ["Russia as reporter (mirror data)", "Monthly", "Cross-check of Kyrgyz imports"],
    ["NSC fuel and energy balance (National Statistical Committee, 2026)", "Annual", "Mass check, dependency, stock cover"],
    ["NSC commodity tables and monthly reports", "Annual / monthly", "Value check; first and latest vintages"],
    ["Brent and WTI spot prices (U.S. Energy Information Administration, n.d.)", "Daily", "External condition"],
    ["Global and Russia GPR (Caldara & Iacoviello, 2022)", "Monthly", "External condition"],
    ["Exchange rates and CPI", "Monthly", "External condition"],
    ["World Development Indicators (World Bank, n.d.)", "Annual", "Scale only; never interpolated"],
    ["Documented export restrictions (e.g., Global Trade Alert, 2023, 2025)", "Event", "Shock calendar"],
   ])

h2("3.5 Research Setting, Population and Selection Criteria")
p("The research setting is the international trade in refined petroleum products of landlocked economies. The population is all monthly reporter–product series of gasoline and distillate imports for landlocked economies in UN Comtrade from January 2015 onward. Kyrgyzstan is the detailed case because of its high dependence on a single supplier, its documented 2026 shortage and the availability of national validation data. The study does not involve human participants or informants, except for an optional, voluntary usability review of the prototype (Section 3.16).")

h2("3.6 Data Collection Procedure and Instrumentation")
p("Data will be collected by a purpose-built Python pipeline that queries the Comtrade API with credentials stored only in environment variables. The pipeline stores every raw response together with its retrieval date and a cryptographic hash, resumes from checkpoints after interruptions, and writes versioned datasets. This instrument has already been built and tested in the preliminary stage: it holds 878 validated responses, all of which match their download hashes, and 24 automated tests pass. A second Comtrade snapshot will be taken before modelling so that revisions between snapshots can be measured. External series will be downloaded from their official interfaces and stored in the same versioned way.")

h2("3.7 Sample and Sampling Procedure")
p("The study will not draw a random sample. Instead, it will apply purposive, criteria-based selection to the full population of candidate series, using rules fixed before modelling (Table 5). Figure 2 shows the resulting coverage. In the preliminary stage these rules yielded an evaluation set (Tier 1) of 22 series from 13 countries with 3,021 monthly observations, and a training pool (Tiers 1 and 2) of 44 series from 22 countries with 5,549 observations. Kyrgyzstan is the only Central Asian country in Tier 1; Kazakhstan and Uzbekistan are in Tier 2, and Tajikistan and Turkmenistan have no monthly data.")
tb(caption="Series Selection Criteria by Tier",
   cols=["Tier", "Criteria", "Use"],
   widths=[0.8, 3.7, 1.5],
   rows=[
    ["Tier 1", "At least 120 observed months and 85% coverage of the window; no gap over six months; data to June 2025 or later; at least 84 supplier months; median at least 100 t; exports below half of imports; no classification flag", "Evaluation and training"],
    ["Tier 2", "At least 84 observed months and at least 84 supplier months", "Training only"],
    ["Tier 3", "Remaining series with sparse or unusable reporting", "Descriptive only"],
   ])
fg(path="figures/fig09_coverage_heatmap.png", width=5.0, caption="Observed Gasoline Months per Year by Reporting Country (Lines Separate Tiers 1, 2 and 3)")

h2("3.8 Data Preparation")
p("Monthly totals will be rebuilt from partner rows, because the aggregate “World” row can be zero or too low while partner rows contain trade. Net weight will be used when positive; other quantity fields will be accepted only when their unit is kilograms. Where a volume is reported on the same row, the implied density must be physically plausible (for example 0.68–0.80 kg/L for gasoline). Unit values will be compared with a plausible band and with their centred 13-month median after deflating by the Brent price: an implausibly low unit value indicates overstated mass, which will be removed while the original record is kept. Outliers beyond four robust deviations on log mass will be flagged but kept, because shocks are the object of study. Missing months will never be replaced with zeros and target values will never be interpolated; each month will carry a status label, and missing months will be excluded from training loss and from scoring. Figure 3 shows the resulting Kyrgyz series.")
fg(path="figures/fig01_kyrgyz_monthly_imports.png", width=6.0, caption="Kyrgyz Monthly Imports of Gasoline Proxy and Distillates, January 2015 to August 2026, in Thousand Tonnes")

h2("3.9 Key Measures")
p("Supplier concentration will be measured with the Herfindahl–Hirschman index, where s_{ijt} is the share of partner j in the import mass of series i in month t:")
eq("HHI_{it} = Σ_{j} s_{ijt}^{2}", 1)
p("Because a single thin month can dominate Equation 1, mass will be pooled over a trailing twelve months, with at least six observed months required. Let Q_{it} be the trailing three-month import mass and B_{it} the mean of the same three calendar months in the previous three years. A shortfall month will be defined as")
eq("S_{it} = 1[ Q_{it} / B_{it} < 0.75 ]", 2)
p("A supply-side shortfall will additionally require a positive standardised change in unit value, which separates supply stress from weak demand, and thresholds of 0.70 and 0.80 will be used as sensitivity checks. Rather than training a separate classifier on these rare and unverified labels, shortfall risk will be derived from each model’s forecast distribution, conditioned on the information set F_{i,τ} available at origin τ:")
eq("p̂_{i,τ+h} = Pr( Q_{i,τ+h} / B_{i,τ+h} < 0.75 | F_{i,τ} ),   F_{i,τ} = { x_{it} : r_{it} ≤ τ }", 3)
p("where r_{it} is the release date of observation t. Labels will be checked against the sourced event list before they are used for evaluation.")

h2("3.10 Forecasting Models")
p("Models will be introduced in order of increasing complexity (Table 6), so that the benefit of each added component can be measured. The seasonal naive forecast and the twelve-month mean are essential lower bounds: a model that cannot beat them has no practical value. Gradient boosting will use quantile objectives on lag-feature tables. Neural models will be deliberately small (16 to 64 hidden units, a country embedding of size 8, dropout), and the compact Temporal Fusion Transformer will be dropped if validation does not support it. All learned models will output the 10th, 50th and 90th percentiles (and the 2.5th and 97.5th for 95% intervals) by minimising the pinball loss, and conformalised quantile regression (Romano et al., 2019) will then adjust the intervals on a chronologically later calibration window.")
tb(caption="Planned Model Progression (Complexity Increases Downward)",
   cols=["Model", "Scope", "Role"],
   widths=[2.6, 1.2, 2.2],
   rows=[
    ["Naive, seasonal naive, 12-month mean", "Local", "Lower bound"],
    ["ETS, SARIMA", "Local", "Statistical reference (H1)"],
    ["Random forest", "Global", "Tree baseline"],
    ["LightGBM, XGBoost", "Local and global", "Main rival (H1, H2)"],
    ["GRU, TCN, N-BEATS", "Global", "Neural candidates (H2)"],
    ["Compact Temporal Fusion Transformer", "Global", "Quantiles, variable selection"],
    ["Graph attention layer on supplier links", "Global", "Optional ablation arm only"],
   ])

h2("3.11 Data Analysis Plan")
p("*Validation protocol.* Evaluation will use expanding rolling origins (Tashman, 2000), with monthly origins from January 2023 to the last available month and horizons of one, three and six months plus the next-three-month total. At each origin only data released by that date will be visible (“as-of replay”); where a release date is unavailable, the reporter’s median publication lag will be applied and marked. Random splitting will not be used, because neighbouring months share shocks and would give optimistic estimates. Hyperparameters and feature sets will be tuned only on data before each test block and frozen before a final block that is run once. Leave-one-country-out training will test transfer to unseen countries.")
p("*Metrics.* Table 7 lists the metrics. MASE (Hyndman & Koehler, 2006) is the primary point metric, because it is scale-free and comparable across countries. With n test months and in-sample seasonal differences of period m = 12,")
eq("MASE = [ (1/n) Σ_{t} |y_{t} − ŷ_{t}| ] / [ (1/(T−m)) Σ_{t=m+1}^{T} |y_{t} − y_{t−m}| ]", 4)
p("Mean absolute percentage error will not be used, because near-zero months make it unstable, and R^{2} will not be used for model selection.")
tb(caption="Evaluation Metrics and Their Purpose",
   cols=["Task", "Metric", "Reason for use"],
   widths=[1.2, 2.4, 2.4],
   rows=[
    ["Point", "MASE (primary), WAPE, RMSE, MAE", "Comparable across countries (Hyndman & Koehler, 2006)"],
    ["Quantile", "Pinball loss, CRPS approximation", "Proper scoring (Gneiting & Raftery, 2007)"],
    ["Interval", "Empirical coverage at 80% and 95%, mean width", "Coverage versus sharpness"],
    ["Shortfall", "PR-AUC, Brier score, recall at fixed alert budget, lead time", "Suited to rare events (Saito & Rehmsmeier, 2015; Brier, 1950)"],
    ["Comparison", "HLN test, Holm correction, block-bootstrap intervals", "Low power, so effect sizes are also reported"],
   ])
p("*Statistical comparison.* Differences between models will be assessed with the Harvey–Leybourne–Newbold corrected Diebold–Mariano test (Diebold & Mariano, 1995; Harvey et al., 1997), with Holm correction and moving-block bootstrap intervals. Because pairwise tests have low power on short test sets, effect sizes will always be reported and statistical significance will be distinguished from practical significance. Results will be stratified into normal months and documented shock windows.")
p("*Ablation and explanation.* An ablation study will remove one information source at a time with the model family and tuning budget held fixed: global training replaced by local; strict importers only; no supplier features; no shock calendar; no external indicators; no lagged unit value; training stopped before 2022; and no conformal step. Tree SHAP values (Lundberg & Lee, 2017) will be computed for LightGBM, and errors will be analysed by country, product, season, supplier dependence and importer type.")

h2("3.12 Matching Research Questions to Methods")
p("Table 8 shows that every research question can be answered with the proposed methods and specifies the comparison and metric for each hypothesis.")
tb(caption="Alignment of Research Questions, Hypotheses, Methods and Evaluation",
   cols=["RQ / H", "Manipulated component", "Comparison", "Evaluation"],
   widths=[0.8, 2.0, 1.6, 1.6],
   rows=[
    ["RQ1 / H1", "Global vs local training; strict-importer panel", "Best local model, seasonal naive", "MASE at h = 3, HLN test"],
    ["RQ2 / H2", "LightGBM, XGBoost vs GRU, TCN, N-BEATS, compact TFT", "LightGBM", "MASE and pinball loss, by normal and shock windows"],
    ["RQ3 / H3", "Supplier and shock features added or removed", "Own-history model", "Pinball loss, high-dependence series"],
    ["RQ4 / H4", "Calibrated shortfall probability", "HHI ranking", "PR-AUC, recall at alert budget, calibration"],
   ])

h2("3.13 Flow of Research Activities")
p("Figure 4 shows the sequence of research stages and Table 9 gives the planned schedule, objectives and outputs. The first two stages were completed in the preliminary phase; the third is the immediate next step.")
fg(path="figures/fig_flow.png", width=6.0, caption="Flow of Research Activities From Data Acquisition to the Risk Monitor")
tb(caption="Research Stages, Objectives and Indicative Schedule",
   cols=["Stage", "Objective", "Output", "Timing"],
   widths=[1.5, 2.1, 1.6, 0.8],
   rows=[
    ["1–2. Acquisition and validation", "Assemble and audit the panel", "Validated dataset v1.0 (done)", "Done"],
    ["3. Rule freeze", "Review cleaning and tier rules; second snapshot", "Frozen rules; revision log", "Month 1"],
    ["4. As-of feature store", "Lag every feature to its release date", "Feature tables by origin", "Month 1–2"],
    ["5. Model benchmark", "Fit baselines, trees and neural models", "Forecast archive", "Month 2–3"],
    ["6. Calibration and risk", "Conformal step; shortfall probabilities", "Calibrated forecasts", "Month 3"],
    ["7. Evaluation and ablation", "Test H1–H4; robustness checks", "Results tables and figures", "Month 4"],
    ["8. Monitor and thesis", "Build prototype; write thesis", "Risk monitor; final thesis", "Month 5–6"],
   ])

h2("3.14 Recording and Management of Data")
p("All raw responses, intermediate files and final datasets will be stored with version numbers, retrieval dates and hashes, and every forecast will be stored with its origin date, model version and input snapshot so that past performance can be reported honestly. Code will be kept under version control, and all figures and tables in the thesis will be regenerated from scripts rather than edited by hand. A decision log will record every change to cleaning rules, thresholds or model settings, with its date and reason.")

h2("3.15 Reliability and Validity")
p("*Reliability.* The study will be reproducible by design: fixed and versioned data snapshots, frozen rules, scripted analysis, at least five random seeds for every learned model, and matched tuning budgets so that complex models are not advantaged.")
p("*Internal validity.* The main threat is information leakage. It will be controlled by as-of replay, by fitting normalisation and tuning only on past data, by excluding same-month unit values and look-ahead cleaning fields, and by using a shock only once it had been announced.")
p("*Construct validity.* The physical target has been checked against official sources (Appendix A): Kyrgyz gasoline mass agrees with the national energy balance within a mean absolute 3.7% from 2018, and partner rows with mass cover at least 90% of import value in 99.4% of 6,505 series-months. Because 2016–2017 Russian mirror data are about three times recorded Kyrgyz imports, results will be reported with and without 2015–2017. Records from 2025 onward appear to be first-release figures, so evaluation will use data as first released.")
p("*External validity and robustness.* Generalisation will be assessed by leave-one-country-out training and by sensitivity checks on shortfall thresholds (0.70, 0.75, 0.80), baseline windows, lag assumptions, exclusion of COVID-19 months, and structural-break tests (Bai & Perron, 2003). Claims based on a single shock event will be avoided.")

h2("3.16 Ethical Considerations")
p("All data are public, aggregate and non-personal, and they will be used within the terms of their providers. API keys will be stored in the environment and never in the code repository. The work is decision support for supply planning and will provide no guidance on evading trade restrictions. If practitioners are asked to review the prototype, participation will be voluntary and anonymous, and no personal data will be stored. All sources will be cited, null and negative results will be reported with the same prominence as positive ones, and any use of AI assistance will be disclosed in line with faculty rules, with every result explainable by the author at the defence.")

# ---------------------------------------------------------------- REFERENCES (APA)
REFERENCES = [
"24.kg. (2025). *Russia’s gasoline export ban not to affect fuel supplies to Kyrgyzstan*. https://24.kg/english/338006_Russias_gasoline_export_ban_not_to_affect_fuel_supplies_to_Kyrgyzstan",
"Akhmetov, A. (2015). Measuring the security of external energy supply and energy exports demand in Central Asia. *International Journal of Energy Economics and Policy*. https://econjournals.com/index.php/ijeep/article/view/1244",
"Ang, B. W., Choong, W. L., & Ng, T. S. (2015). Energy security: Definitions, dimensions and indexes. *Renewable and Sustainable Energy Reviews, 42*, 1077–1093. https://doi.org/10.1016/j.rser.2014.10.064",
"Arrar, D., Ounoughi, C., Kamel, N., Kalvet, T., Tiits, M., & Ben Yahia, S. (2025). High-accuracy prediction of international raw material trade flows using temporal fusion transformer. *International Journal of Data Science and Analytics, 20*(6), 5631–5651. https://doi.org/10.1007/s41060-025-00781-4",
"Athukorala, P., & Hill, H. (2023). Trade policy in a ‘double-landlocked’ transition economy: Kyrgyzstan. *The World Economy, 46*(12), 3455–3471. https://doi.org/10.1111/twec.13416",
"Babu, N. C., Pranav, C. N., Ganesh, L., & Nagamani, P. T. (2024). Forecasting crude oil and petroleum oil and lubricants production and imports using ARIMA model. *Lecture Notes in Electrical Engineering*, 769–774. https://doi.org/10.1007/978-981-97-8031-0_81",
"Bai, J., & Perron, P. (2003). Computation and analysis of multiple structural change models. *Journal of Applied Econometrics, 18*(1), 1–22. https://doi.org/10.1002/jae.659",
"Baumeister, C., & Kilian, L. (2011). *Real-time forecasts of the real price of oil* (Bank of Canada Staff Working Paper 2011-16). https://doi.org/10.34989/swp-2011-16",
"Breiman, L. (2001). Random forests. *Machine Learning, 45*, 5–32. https://doi.org/10.1023/A:1010933404324",
"Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review, 78*(1), 1–3.",
"Caldara, D., & Iacoviello, M. (2022). Measuring geopolitical risk. *American Economic Review, 112*(4), 1194–1225. https://doi.org/10.1257/aer.20191823",
"Chen, S., et al. (2025). Adaptive strategies to enhance resilience in the global oil trade network. *Energy Strategy Reviews, 62*, 101921. https://doi.org/10.1016/j.esr.2025.101921",
"Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. In *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 785–794). https://doi.org/10.1145/2939672.2939785",
"Cho, K., van Merriënboer, B., Gulcehre, C., Bahdanau, D., Bougares, F., Schwenk, H., & Bengio, Y. (2014). Learning phrase representations using RNN encoder–decoder for statistical machine translation. In *Proceedings of EMNLP* (pp. 1724–1734). https://doi.org/10.3115/v1/D14-1179",
"Chupilkin, M., Javorcik, B., & Plekhanov, A. (2023). *The Eurasian roundabout: Trade flows into Russia through the Caucasus and Central Asia*. SSRN. https://doi.org/10.2139/ssrn.4368618",
"Cohen, G., Joutz, F., & Loungani, P. (2011). Measuring energy security: Trends in the diversification of oil and natural gas supplies. *Energy Policy, 39*(9), 4860–4869. https://doi.org/10.1016/j.enpol.2011.06.034",
"Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics, 13*(3), 253–263. https://doi.org/10.1080/07350015.1995.10524599",
"Economist.kg. (2026, July 22). *Fuel stocks for 1.5 months: Kyrgyzstan diversifies imports* [in Russian]. https://economist.kg/transport/2026/07/22/zapasy-gsm-diversifikaciya-importa.md",
"Elsayed, S., Thyssens, D., Rashed, A., Jomaa, H. S., & Schmidt-Thieme, L. (2021). *Do we really need deep learning models for time series forecasting?* arXiv. https://doi.org/10.48550/arXiv.2101.02118",
"Enerdata. (2024). *Russia will impose a six-month ban on gasoline exports from March 2024*. https://www.enerdata.net/publications/daily-energy-news/russia-will-impose-six-month-ban-gasoline-exports-march-2024.html",
"Global Trade Alert. (2023). *Russia: Restriction on the export of motor gasoline and diesel fuel* (Decree No. 1537). https://globaltradealert.org/state-act/77973-russia-restriction-on-the-export-of-motor-gasoline-and-diesel-fuel",
"Global Trade Alert. (2025). *Russia: Temporary ban on petrol exports reinstated for all exporters, 1 October–31 December 2025*. https://globaltradealert.org/state-act/94735-russia-temporary-ban-on-petrol-exports-reinstated-for-all-exporters-1-october-31-december-2025",
"Gneiting, T., Balabdaoui, F., & Raftery, A. E. (2007). Probabilistic forecasts, calibration and sharpness. *Journal of the Royal Statistical Society: Series B, 69*(2), 243–268. https://doi.org/10.1111/j.1467-9868.2007.00587.x",
"Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association, 102*(477), 359–378. https://doi.org/10.1198/016214506000001437",
"Golovanova, S., Rodichev, A., & Zinyakov, Y. (2026). Discrepancies in trade statistics in 2003–2024: The impact of sanctions. *Economics & Politics, 38*(3), 653–664. https://doi.org/10.1111/ecpo.70046",
"Grinsztajn, L., Oyallon, E., & Varoquaux, G. (2022). *Why do tree-based models still outperform deep learning on tabular data?* arXiv. https://doi.org/10.48550/arXiv.2207.08815",
"Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of modern neural networks. In *Proceedings of the 34th International Conference on Machine Learning* (Vol. 70, pp. 1321–1330).",
"Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction mean squared errors. *International Journal of Forecasting, 13*(2), 281–291. https://doi.org/10.1016/S0169-2070(96)00719-4",
"Hewamalage, H., Ackermann, K., & Bergmeir, C. (2022a). Forecast evaluation for data scientists: Common pitfalls and best practices. *Data Mining and Knowledge Discovery, 37*(2), 788–832. https://doi.org/10.1007/s10618-022-00894-5",
"Hewamalage, H., Bergmeir, C., & Bandara, K. (2021). Recurrent neural networks for time series forecasting: Current status and future directions. *International Journal of Forecasting, 37*(1), 388–427. https://doi.org/10.1016/j.ijforecast.2020.06.008",
"Hewamalage, H., Bergmeir, C., & Bandara, K. (2022b). Global models for time series forecasting: A simulation study. *Pattern Recognition, 124*, 108441. https://doi.org/10.1016/j.patcog.2021.108441",
"Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. *Neural Computation, 9*(8), 1735–1780. https://doi.org/10.1162/neco.1997.9.8.1735",
"Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics, 6*(2), 65–70.",
"Hong, T., Pinson, P., Fan, S., Zareipour, H., Troccoli, A., & Hyndman, R. J. (2016). Probabilistic energy forecasting: Global Energy Forecasting Competition 2014 and beyond. *International Journal of Forecasting, 32*(3), 896–913. https://doi.org/10.1016/j.ijforecast.2016.02.001",
"Hu, L., Song, C., Ye, S., & Gao, P. (2022). Spatiotemporal statistical imbalance: A long-term neglected defect in UN Comtrade dataset. *Sustainability, 14*(3), 1431. https://doi.org/10.3390/su14031431",
"Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of Forecasting, 22*(4), 679–688. https://doi.org/10.1016/j.ijforecast.2006.03.001",
"Intarasat, U., Bootwisas, N., & Marupanthorn, P. (2026). *VP-OilEx-STFN: Structural-gated mixed-frequency nowcasting for oil export prediction in Norway and Thailand* [Preprint]. Research Square. https://doi.org/10.21203/rs.3.rs-9995316/v1",
"International Energy Agency. (2020). *Kyrgyzstan energy profile*. https://www.iea.org/reports/kyrgyzstan-energy-profile",
"International Energy Agency. (2022). *Kyrgyzstan 2022: Energy policy review*. https://www.iea.org/reports/kyrgyzstan-2022",
"Januschowski, T., Wang, Y., Torkkola, K., Erkkilä, T., Hasson, H., & Gasthaus, J. (2022). Forecasting with trees. *International Journal of Forecasting, 38*(4), 1473–1481. https://doi.org/10.1016/j.ijforecast.2021.10.004",
"Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. In *Advances in Neural Information Processing Systems* (Vol. 30, pp. 3146–3154).",
"Khajoui, S., Dehyadegari, S., & Jalaee, S. A. (2024). *Forecasting imports in OECD member countries and Iran by using neural network algorithms of LSTM*. arXiv. https://doi.org/10.48550/arXiv.2402.01648",
"Khan, A., & Wyrwa, A. (2025). An early warning system for renewable energy supply shortfalls in Europe using integrated machine learning and spatiotemporal energy data. In *2025 14th International Conference on Renewable Energy Research and Applications* (pp. 1344–1350). https://doi.org/10.1109/ICRERA66237.2025.11283745",
"Kun.uz. (2026, July 15). *Kyrgyzstan imposes indefinite ban on fuel exports to prevent shortages*. https://kun.uz/en/news/2026/07/15/kyrgyzstan-imposes-indefinite-ban-on-fuel-exports-to-prevent-shortages-ea7730",
"Kwan, S. (2026, July). Kyrgyzstan fuel crisis: Bishkek relaxes fuel import rules to ease supply pressures. *The Times of Central Asia*. https://timesca.com/kyrgyzstan-fuel-crisis-import-rules/",
"Kwon, M., & Jeong, D. (2026). Dynamic trade flow indicators outperform import concentration in supply disruption early warning for a maritime-dependent economy. *Frontiers in Marine Science, 13*, 1956773. https://doi.org/10.3389/fmars.2026.1956773",
"Laborda, J., Ruano, S., & Zamanillo, I. (2023). Multi-country and multi-horizon GDP forecasting using temporal fusion transformers. *Mathematics, 11*(12), 2625. https://doi.org/10.3390/math11122625",
"Le Coq, C., & Paltseva, E. (2009). Measuring the security of external energy supply in the European Union. *Energy Policy, 37*(11), 4474–4481. https://doi.org/10.1016/j.enpol.2009.05.069",
"Li, Z., Zhou, B., & Hensher, D. A. (2022). Forecasting automobile gasoline demand in Australia using machine learning-based regression. *Energy, 239*, 122312. https://doi.org/10.1016/j.energy.2021.122312",
"Lim, B., Arık, S. Ö., Loeff, N., & Pfister, T. (2021). Temporal fusion transformers for interpretable multi-horizon time series forecasting. *International Journal of Forecasting, 37*(4), 1748–1764. https://doi.org/10.1016/j.ijforecast.2021.03.012",
"Lin, B., & Zhang, Z. (2025). Anchoring security in uncertainty: The dynamic responses of China’s energy imports to geopolitical risk shocks. *Energy, 335*, 137996. https://doi.org/10.1016/j.energy.2025.137996",
"Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. In *Advances in Neural Information Processing Systems* (Vol. 30).",
"Luong, P. V. (2026). *Geopolitical shocks in vertically linked petroleum products supply chains*. SSRN. https://doi.org/10.2139/ssrn.7679879",
"Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2022a). M5 accuracy competition: Results, findings, and conclusions. *International Journal of Forecasting, 38*(4), 1346–1364. https://doi.org/10.1016/j.ijforecast.2021.11.013",
"Makridakis, S., Spiliotis, E., Assimakopoulos, V., Chen, Z., Gaba, A., Tsetlin, I., & Winkler, R. L. (2022b). The M5 uncertainty competition: Results, findings and conclusions. *International Journal of Forecasting, 38*(4), 1365–1385. https://doi.org/10.1016/j.ijforecast.2021.10.009",
"Montero-Manso, P., & Hyndman, R. J. (2021). Principles and algorithms for forecasting groups of time series: Locality and globality. *International Journal of Forecasting, 37*(4), 1632–1653. https://doi.org/10.1016/j.ijforecast.2021.03.004",
"National Statistical Committee of the Kyrgyz Republic. (2026). *Fuel and energy balance, 2024 edition*. https://stat.gov.kg/ru/publications/toplivno-energeticheskij-balans/",
"Oreshkin, B. N., Carpov, D., Chapados, N., & Bengio, Y. (2020). N-BEATS: Neural basis expansion analysis for interpretable time series forecasting. In *International Conference on Learning Representations*. https://doi.org/10.48550/arXiv.1905.10437",
"Peng, S., Wang, L., & Chen, Y. (2025). The survival of global energy imports and the impact of geopolitical risks. *Energy Economics, 147*, 108595. https://doi.org/10.1016/j.eneco.2025.108595",
"Pradhan, B. L., Upadhyay, H. P., Malla-Pradhan, R., & Kafle, M. (2023). An econometric analysis of imported petroleum products of Nepal. *Journey for Sustainable Development and Peace Journal, 1*(1), 67–80. https://doi.org/10.3126/jsdpj.v1i1.52602",
"Qin, Y., Huang, Y., Wang, Y., Zhao, Z., Zhu, C., Wang, J., & Wei, B. (2026). Oil import demand forecasting based on machine learning technology under energy transformation background. *Chemistry and Technology of Fuels and Oils, 61*(6), 1602–1611. https://doi.org/10.1007/s10553-026-02011-4",
"Qodirova, N., & Ellerton, M. (2026). Imputed weights and unit values in public UN Comtrade: Evidence on the cost of friend-shoring. *Commentary and Critique, 9*. https://doi.org/10.62432/appe.cc.2026.9.36",
"Romano, Y., Patterson, E., & Candès, E. J. (2019). Conformalized quantile regression. In *Advances in Neural Information Processing Systems* (Vol. 32). https://doi.org/10.48550/arXiv.1905.03222",
"Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. *PLoS ONE, 10*(3), e0118432. https://doi.org/10.1371/journal.pone.0118432",
"Salinas, D., Flunkert, V., Gasthaus, J., & Januschowski, T. (2020). DeepAR: Probabilistic forecasting with autoregressive recurrent networks. *International Journal of Forecasting, 36*(3), 1181–1191. https://doi.org/10.1016/j.ijforecast.2019.07.001",
"Santi, V. M., Wahyu, R., & Hadi, I. (2023). Forecasting the value of Indonesia’s oil and gas imports using seasonal autoregressive integrated moving average model. *BAREKENG: Jurnal Ilmu Matematika dan Terapan, 17*(4), 2047–2058. https://doi.org/10.30598/barekengvol17iss4pp2047-2058",
"Saputra, I. A., Vitianingsih, A. V., Kristyawan, Y., Maukar, A. L., & Rusdi, J. F. (2024). Forecasting model of export and import value of oil and gas using gated recurrent unit method. *Teknika, 13*(2), 239–243. https://doi.org/10.34148/teknika.v13i2.861",
"Sellami, B., et al. (2024). Harnessing graph neural networks to predict international trade flows. *Big Data and Cognitive Computing, 8*(6), 65. https://doi.org/10.3390/bdcc8060065",
"Semenoglou, A.-A., Spiliotis, E., Makridakis, S., & Assimakopoulos, V. (2021). Investigating the accuracy of cross-learning time series forecasting methods. *International Journal of Forecasting, 37*(3), 1072–1084. https://doi.org/10.1016/j.ijforecast.2020.11.009",
"Shao, Y. E., Lu, C.-J., & Hou, C.-D. (2014). Hybrid soft computing schemes for the prediction of import demand of crude oil in Taiwan. *Mathematical Problems in Engineering, 2014*, 257947. https://doi.org/10.1155/2014/257947",
"Stark, T., & Croushore, D. (2002). Forecasting with a real-time data set for macroeconomists. *Journal of Macroeconomics, 24*(4), 507–531. https://doi.org/10.1016/S0164-0704(02)00062-9",
"Tashman, L. J. (2000). Out-of-sample tests of forecasting accuracy: An analysis and review. *International Journal of Forecasting, 16*(4), 437–450. https://doi.org/10.1016/S0169-2070(00)00065-0",
"UN-OHRLLS. (n.d.). *List of landlocked developing countries*. Retrieved November 1, 2026, from https://www.un.org/ohrlls/content/list-lldcs",
"United Nations Statistics Division. (n.d.). *UN Comtrade database: Public API*. Retrieved November 2, 2026, from https://comtradeapi.un.org/",
"U.S. Energy Information Administration. (n.d.). *Europe Brent spot price FOB, daily*. Retrieved November 1, 2026, from https://www.eia.gov/dnav/pet/hist/RBRTEd.htm",
"Wallis, K. F. (1986). Forecasting with an econometric model: The ‘ragged edge’ problem. *Journal of Forecasting, 5*(1), 1–13. https://doi.org/10.1002/for.3980050102",
"Wanto, A., Herawan Hayadi, B., Subekti, P., Sudrajat, D., Wikansari, R., Bhawika, G. W., Sumartono, E., & Surya, S. (2019). Forecasting the export and import volume of crude oil, oil products and gas using ANN. *Journal of Physics: Conference Series, 1255*(1), 012016. https://doi.org/10.1088/1742-6596/1255/1/012016",
"World Bank. (n.d.). *World development indicators API*. Retrieved November 1, 2026, from https://api.worldbank.org/v2/",
"World Trade Organization. (2021). Landlocked developing countries and trade bottlenecks. In *Easing trade bottlenecks of landlocked developing countries* (pp. 5–6). https://doi.org/10.30875/9789287053305-003",
"Yokuş, T. (2024). Early warning systems for world energy crises. *Sustainability, 16*(6), 2284. https://doi.org/10.3390/su16062284",
"Yolusever, A. (2026). Pooling beats structure on short annual panels: Parameter sharing and the forecast accuracy of evolutionary models for compositional time series. *Forecasting, 8*(5), 89. https://doi.org/10.3390/forecast8050089",
"Zaffran, M., Dieuleveut, A., Féron, O., Goude, Y., & Josse, J. (2022). Adaptive conformal predictions for time series. In *Proceedings of the 39th International Conference on Machine Learning*. https://doi.org/10.48550/arXiv.2202.07282",
"Zeng, A., Chen, M., Zhang, L., & Xu, Q. (2023). Are transformers effective for time series forecasting? *Proceedings of the AAAI Conference on Artificial Intelligence, 37*(9), 11121–11128. https://doi.org/10.1609/aaai.v37i9.26317",
"Zhao, T., et al. (2026). Global trade network prediction based on spatiotemporal graph neural network and gradient boosting model. *Scientific Reports*. https://doi.org/10.1038/s41598-026-72209-3",
]

# ---------------------------------------------------------------- APPENDIXES
APPX = []
APPX.append(("A", "Preliminary Data Validation Results", [
    ("p", "This appendix reports work already executed on the data snapshot of 2 November 2026 (dataset version 1.0.0). It is descriptive; no forecasting model was fitted to the final datasets."),
    ("table", dict(caption="Validation of the Kyrgyz Comtrade Series Against Official and Mirror Sources",
        cols=["Check", "Result"], widths=[3.4, 2.6],
        rows=[["Gasoline mass vs national energy balance", "3.7% mean absolute difference from 2018"],
              ["Gasoline value vs NSC commodity table", "Within 5% in 2022–2024"],
              ["2025 gasoline value vs NSC", "Ratio 0.78 (first-release effect suspected)"],
              ["Gasoline exports vs energy balance (2024)", "77.6 kt vs 76.4 kt"],
              ["Partner-row sum vs World row", "No month differs by more than 5% in value"],
              ["Russian mirror data, 2018 and 2021", "Ratio 0.93–1.02"],
              ["Russian mirror data, 2016–2017", "Ratio 0.33–0.37 (cause unknown)"],
              ["Usable Kyrgyz months per product", "133 of 140"]], num="A1")),
    ("fig", dict(path="figures/fig01_kyrgyz_monthly_imports.png", width=5.8, caption="Kyrgyz Monthly Imports, January 2015 to August 2026, in Thousand Tonnes (Grey Bands Mark Missing or Rejected Months)", num="A1")),
    ("p", "Exploratory analysis found that Kyrgyz gasoline imports vary significantly by calendar month (Kruskal–Wallis p < 0.001), highest in December and lowest in September, while distillates show no clear seasonal pattern (p = 0.42). Co-movement between countries is weak: the median pairwise correlation of year-on-year gasoline changes is 0.04. Kyrgyz gasoline has a median trailing-twelve-month HHI of 0.89 (Figure A2), which leaves little variation for concentration to explain and is a direct difficulty for H4. Net import dependency in 2024 was 0.77 for gasoline and 0.86 for diesel. The clean data give 11 gasoline and 7 distillate shortfall episodes among 112 evaluable months under Equation 2."),
    ("fig", dict(path="figures/fig08_kyrgyz_supplier_concentration.png", width=5.6, caption="Kyrgyz Supplier Concentration (Trailing HHI) and Russia’s Monthly Share", num="A2")),
]))
APPX.append(("B", "Untuned Pilot Forecast", [
    ("p", "A small, deliberately untuned pilot was run only to check that the design can be executed end to end. It used an earlier 43-series panel with World-row totals, without as-of replay, and test targets from September 2024 to August 2026. About 22 Kyrgyz test months are too few to rank models, and no significance test was run; the results below are indicative only and are not findings of the study."),
    ("table", dict(caption="Untuned Pilot: Kyrgyz Gasoline WAPE (%), Lower Is Better",
        cols=["Model", "h = 1", "h = 3", "Next 3 months"], widths=[2.4, 1.2, 1.2, 1.2],
        rows=[["Seasonal naive", "49.6", "49.6", "29.2"],
              ["12-month mean", "38.9", "39.5", "28.4"],
              ["LightGBM, local", "30.4", "32.0", "20.7"],
              ["LightGBM, global", "30.6", "34.8", "23.6"],
              ["GRU, global", "33.5", "42.9", "28.5"]], num="B1")),
    ("p", "The next-three-month error fell from about 28% for the twelve-month mean to about 21% for local LightGBM, which suggests there is signal to model. For August 2026 the median forecast was 38.1 kt with a lower bound of 20.5 kt, while the actual value was 16.9 kt: autoregressive features alone did not anticipate the shock, and nominal 80% intervals covered only 62–75% of Kyrgyz outcomes. These observations motivate the calibration step and the supplier and shock features tested under H3 and H4."),
]))
