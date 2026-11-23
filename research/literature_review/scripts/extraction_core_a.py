"""Evidence extraction, core tier, part A: petroleum/energy import forecasting and trade-flow forecasting.

One dict per paper, keyed by DOI. Values are taken from the abstract (basis 'abstract') unless a later
full-text pass replaces them (basis 'full text', with section/page locations in 'evidence').
'NR' means not reported in the source that was read. Nothing here is inferred beyond the source;
critical comments are marked as the reviewer's assessment in 'lim_crit'.
"""
NR = "Not reported in abstract"

E = {
    "10.21203/rs.3.rs-9995316/v1": dict(
        domain="Oil export nowcasting", objective="Real-time mixed-frequency nowcasting of monthly oil exports",
        rq=NR, geo="Norway; Thailand", data="Statistics Norway, Norwegian Petroleum, EPPO Thailand and market data (daily/weekly)",
        period=NR, freq="Monthly target; daily/weekly inputs", n=NR, target="Monthly oil export (value/volume as defined by official statistics)",
        features="Oil balance, destination markets, inventories, freight, volatility, news-event blocks", methods="Deep learning (VP-OilEx-STFN) with vintage-aware patches",
        arch="Patch-based fusion network with release-calendar masking, country export gates, benchmark-anchor calibration",
        validation="Real-time (vintage-aware) design per abstract", metrics=NR,
        findings="Proposes release-calendar masking so that only information available at the forecast date is used",
        lim_auth=NR, lim_crit="Preprint, not peer reviewed; two exporters only; architecture complexity is high relative to monthly sample sizes",
        relevance="High: closest found example of publication-lag-aware forecasting for an oil trade flow", adapt="Release-calendar masking; vintage-aware feature construction"),
    "10.1088/1742-6596/1255/1/012016": dict(
        domain="Oil and gas trade forecasting", objective="Forecast export and import volumes of crude oil, oil products and gas",
        rq=NR, geo="Indonesia", data="Statistics Indonesia (BPS), Indonesian Customs", period=NR, freq="Annual (per abstract: 'for the coming years')",
        n=NR, target="Export/import volume of crude oil, oil products and gas", features="Lagged values (12-input network)",
        methods="ANN backpropagation", arch="MLP 12-5-1 (best of 12-5-1, 12-8-1, 12-10-1, 12-14-1)", validation=NR,
        metrics="'Accuracy' 83%, MSE", findings="12-5-1 network selected as best", lim_auth=NR,
        lim_crit="Single country; no benchmark against naive/statistical models reported; accuracy metric not scale-free and not defined in abstract",
        relevance="Medium: direct petroleum-import forecasting precedent, illustrates the low methodological baseline", adapt="None beyond problem framing"),
    "10.34148/teknika.v13i2.861": dict(
        domain="Oil and gas trade forecasting", objective="Forecast monthly value of oil and gas exports and imports",
        rq=NR, geo="Indonesia", data="BPS monthly series", period="1993-2023", freq="Monthly", n=NR, target="Import and export value (USD)",
        features="Own history", methods="GRU", arch="Gated recurrent unit network", validation=NR, metrics="MAPE (export 12.19%, import 14.30%)",
        findings="GRU forecasts with MAPE of 12-14%", lim_auth=NR,
        lim_crit="Value not physical volume; no baselines in abstract; MAPE only; single series per flow",
        relevance="Medium: monthly import forecasting with DL on one country", adapt="None; shows need for baselines and scale-free metrics"),
    "10.30598/barekengvol17iss4pp2047-2058": dict(
        domain="Oil and gas import forecasting", objective="Forecast monthly value of oil and gas imports", rq=NR, geo="Indonesia",
        data="Monthly import value series", period="From 2000s (start month truncated in abstract)", freq="Monthly", n=NR,
        target="Import value of oil and gas", features="Own history", methods="SARIMA", arch="Seasonal ARIMA", validation=NR,
        metrics=NR, findings="SARIMA reproduces seasonal pattern of imports", lim_auth=NR,
        lim_crit="Value-based, univariate, single country, no uncertainty evaluation",
        relevance="Medium: statistical baseline precedent for monthly petroleum imports", adapt="Seasonal statistical baseline"),
    "10.1155/2014/257947": dict(
        domain="Crude oil import demand forecasting", objective="Predict imported crude oil demand with single- and two-stage hybrid models",
        rq=NR, geo="Taiwan", data="Taiwan crude oil data with 23 explanatory variables", period="1993-2010", freq=NR, n=NR,
        target="Imported crude oil demand", features="23 macro/energy explanatory variables, reduced by variable selection",
        methods="MLR, SVR, ANN, ELM; two-stage hybrids (selection + prediction)", arch="Two-stage hybrid", validation=NR,
        metrics="MAPE, RMSE, MAD", findings="Two-stage hybrids proposed; selection of fewer significant variables before prediction",
        lim_auth=NR, lim_crit="Short sample; contemporaneous explanatory variables may not be available at forecast time (leakage risk)",
        relevance="Medium: import-demand ML with exogenous features", adapt="Feature pre-selection; leakage warning"),
    "10.1007/s11135-025-02268-7": dict(
        domain="Petroleum product import demand (econometrics)", objective="Identify determinants of petroleum product import demand",
        rq=NR, geo="Tanzania", data=NR, period=NR, freq=NR, n=NR, target="Petroleum product import demand", features=NR,
        methods="ARDL, ECM", arch="Cointegration framework", validation=NR, metrics=NR, findings=NR, lim_auth=NR,
        lim_crit="Explanatory, not out-of-sample forecasting", relevance="Medium: import-demand determinants for a developing importer",
        adapt="Candidate drivers (income, price) for features"),
    "10.3126/jsdpj.v1i1.52602": dict(
        domain="Petroleum product imports (trend analysis)", objective="Trend analysis of petroleum product imports",
        rq=NR, geo="Nepal (landlocked)", data="Nepal Oil Corporation", period="Apr 1987 - Feb 2018", freq=NR, n=NR,
        target="Imported petroleum products", features="Time trend", methods="Trend and regression analysis (Excel, SPSS)", arch="Linear trend",
        validation="None reported", metrics=NR, findings="Import dependence rising; petrol consumption increases 0.11 units per time unit",
        lim_auth=NR, lim_crit="Descriptive trend fitting; no forecast evaluation", relevance="Medium: one of very few landlocked petroleum-import studies",
        adapt="Context for Nepal as a panel member"),
    "10.3390/su151813592": dict(
        domain="Oil demand forecasting, cross-country", objective="Forecast oil demand using endogenous and exogenous factors; compare importers and exporters",
        rq="Stability of ML models for exporters vs importers (stated as gap)", geo="30 countries", data=NR, period="2000-2020", freq="Annual",
        n="30 countries x 21 years", target="Oil demand", features="Emissions, income, energy price, GDP, population, urbanisation, trade, inflation, FDI and exogenous factors",
        methods="Machine learning (models not named in truncated abstract)", arch=NR, validation=NR, metrics=NR, findings=NR, lim_auth=NR,
        lim_crit="Annual panel; demand not imports; contemporaneous macro features", relevance="High: one of few cross-country ML oil studies separating importers",
        adapt="Panel feature design; importer/exporter stratification"),
    "10.32479/ijeep.15572": dict(
        domain="Diesel demand forecasting", objective="Forecast monthly HSD demand", rq=NR, geo="India", data="Indiastat",
        period="1991-2022", freq="Monthly", n=NR, target="High-speed diesel demand", features="Own history",
        methods="ANN (MLP), extreme learning machine vs ARIMA-type models", arch="MLP; ELM", validation=NR, metrics=NR,
        findings="Comparison of ANN with traditional methods (result truncated in abstract)", lim_auth=NR,
        lim_crit="Demand not imports; single country", relevance="Medium: links import dependence (>80%) to supply-disruption motivation", adapt="None"),
    "10.21203/rs.3.rs-2257631/v1": dict(
        domain="Gasoline and diesel consumption forecasting", objective="Compare SARIMA and neural network", rq=NR, geo="India", data=NR, period=NR,
        freq=NR, n=NR, target="Gasoline (MS) and diesel (HSD) consumption", features="Own history", methods="SARIMA; neural network", arch=NR,
        validation=NR, metrics="MAPE", findings="Equal accuracy for gasoline; SARIMA clearly better for diesel", lim_auth=NR,
        lim_crit="Preprint; MAPE only", relevance="Medium: evidence that statistical baselines can beat neural nets on fuel series", adapt="Keep SARIMA/ETS baselines"),
    "10.2139/ssrn.7203258": dict(
        domain="Fuel import dependence (panel econometrics)", objective="Effect of renewables on fuel import dependence",
        rq=NR, geo="Bangladesh, India, Nepal, Pakistan, Sri Lanka", data="World Development Indicators", period="2001-2025", freq="Annual",
        n="5 countries x 25 years", target="Fuel imports (% of merchandise imports)", features="Renewable consumption, energy use, manufacturing VA, exports, GDP growth",
        methods="Pooled OLS, FE, RE; Driscoll-Kraay, PCSE, FGLS", arch="Panel regression", validation="Not a forecasting study",
        metrics=NR, findings="Renewable energy consumption has no statistically significant effect (per abstract)", lim_auth=NR,
        lim_crit="SSRN working paper; value share not physical volume", relevance="Medium: shows the dominant explanatory (not predictive) panel design",
        adapt="Contrast: explanatory vs forecasting framing"),
    "10.5281/zenodo.18467170": dict(
        domain="Bilateral trade-flow forecasting", objective="Out-of-time ML forecasting of bilateral trade flows", rq=NR,
        geo="Global dyad panel", data="Dyad-year trade data", period="1991-2021", freq="Annual", n="Global dyads (size NR)", target="Bilateral trade flow (transformed)",
        features="Only pre-forecast-year information: lagged dyad trade, scale proxies, dyad importance, exporter/importer IDs",
        methods="Ridge, Random Forest, CatBoost", arch="Tree ensembles vs regularised linear", validation="Strict temporal split: train to 2016, validate 2017-2019, test 2020-2021",
        metrics="RMSE on transformed target", findings="CatBoost best, Random Forest second; consistent gains from nonlinear learning", lim_auth=NR,
        lim_crit="Venue quality uncertain (Zenodo DOI, 'Policy Research Journal'); annual data",
        relevance="High: global (pooled) tree models with information-set discipline for trade flows", adapt="Information-set rule; pooled boosting with entity IDs"),
    "10.1002/for.70165": dict(
        domain="Trade nowcasting", objective="Nowcast world trade with machine learning", rq=NR, geo="World", data="Real-time datasets",
        period=NR, freq="Monthly", n=NR, target="World trade", features="Large predictor set; pre-selection and factor extraction",
        methods="Random forest, gradient boosting, macroeconomic random forest, linear gradient boosting, OLS, Markov-switching, quantile regression, DFM, elastic net",
        arch="Three-step: pre-selection, factors, ML regression", validation="Multiple horizons and real-time datasets", metrics=NR,
        findings="Regression-based ML (macro RF, linear GB) beats tree-based and traditional methods significantly", lim_auth=NR,
        lim_crit="Aggregate world trade, not commodity- or country-specific", relevance="High: real-time ML trade forecasting evidence",
        adapt="Real-time evaluation; linear-boosting variants as baselines"),
    "10.1016/j.physa.2024.129977": dict(
        domain="Economic forecasting with trade networks", objective="Use international trade network features in ML macro forecasting", rq=NR,
        geo="Multi-country", data=NR, period=NR, freq=NR, n=NR, target=NR, features="Trade network topology", methods="Machine learning", arch=NR,
        validation=NR, metrics=NR, findings=NR, lim_auth=NR, lim_crit="Abstract not available at screening; extraction pending",
        relevance="Medium: network/supplier-structure features as predictors", adapt="Network-derived features"),
    "10.3389/fmars.2026.1956773": dict(
        domain="Import supply disruption early warning", objective="Test whether dynamic trade-flow indicators predict disruptions better than origin-concentration screening",
        rq="Predictive validity of concentration heuristic, out of sample", geo="Korea (maritime-dependent)", data="Korea Customs Service open statistics",
        period="2010-2025", freq="Monthly", n="5,925 HS6 products x 20 partners; ~161,000 out-of-sample product-months",
        target="Proxy disruption onset: persistent quantity shortfall with rising unit values, standardised by product history",
        features="Dynamic trade-flow indicators vs origin concentration", methods="Prediction models vs concentration benchmark (details in full text)",
        arch=NR, validation="Out-of-sample", metrics="1.3 million model and benchmark scores (metrics in full text)",
        findings="Title: dynamic trade-flow indicators outperform import concentration", lim_auth=NR,
        lim_crit="Proxy-defined events; maritime economy; product-level not fuel-specific",
        relevance="Very high: closest prior work to the proposed early-warning component; uses the same quantity-plus-unit-value signature",
        adapt="Event definition, concentration benchmark, out-of-sample alert evaluation"),
    "10.1007/s41060-025-00781-4": dict(
        domain="Raw-material trade-flow forecasting", objective="Forecast international raw material trade flows with TFT", rq=NR, geo=NR, data=NR,
        period=NR, freq=NR, n=NR, target="Trade flows", features=NR, methods="Temporal Fusion Transformer", arch="TFT", validation=NR, metrics=NR,
        findings=NR, lim_auth=NR, lim_crit="Abstract not available at screening; extraction pending", relevance="Medium: global DL on trade flows",
        adapt="TFT configuration for trade panels"),
    "10.1080/01605682.2026.2757161": dict(
        domain="Trade network forecasting under disruption", objective="Predict bilateral trade and country network status under shocks",
        rq=NR, geo="Global; major economies", data="Global trade network", period=NR, freq=NR, n=NR, target="Bilateral trade value and volume; network properties",
        features="Network structure under attack operators", methods="Network-evolution model vs ML baselines", arch="Attack-operator network framework",
        validation=NR, metrics="Forecast accuracy (>80% per abstract)", findings="Network model outperforms ML baselines; distinct disruption profiles",
        lim_auth=NR, lim_crit="Accuracy definition unclear in abstract", relevance="Medium: disruption-aware trade forecasting", adapt="Shock scenarios as stress tests"),
    "10.1016/j.econmod.2021.02.013": dict(
        domain="Import forecasting", objective="Forecast imports using information from abroad (partner data)", rq=NR, geo=NR, data=NR, period=NR,
        freq=NR, n=NR, target="Imports", features="Foreign/partner indicators", methods=NR, arch=NR, validation=NR, metrics=NR, findings=NR,
        lim_auth=NR, lim_crit="Abstract not available at screening; extraction pending", relevance="High: partner-side information for import forecasting",
        adapt="Supplier-side (e.g., Russian export) indicators"),
    "10.3390/su14031431": dict(
        domain="Trade data quality", objective="Characterise statistical imbalance in UN Comtrade records", rq=NR,
        geo="15 reporters incl. Russian Federation", data="UN Comtrade", period="1996-2016", freq="Annual records", n="15 reporters",
        target="Imbalance between heading totals and sum of subheadings", features=NR, methods="Frequency analysis; co-clustering", arch=NR,
        validation=NR, metrics=NR, findings="Imbalance widespread and clustered; fossil fuels among affected categories", lim_auth=NR,
        lim_crit="Annual data and large reporters only", relevance="High: justifies the project's supplier-sum and heading-vs-lines checks",
        adapt="Data audit rules for HS 2710 lines"),
    "10.48550/arxiv.2402.01648": dict(
        domain="Import forecasting", objective="Forecast imports of OECD countries and Iran with LSTM", rq=NR, geo="OECD selected countries; Iran",
        data="World Bank, WTO, IMF", period="1970-2019 (annual, interpolated to quarterly)", freq="Annual converted to seasonal", n="200 data points",
        target="Total imports", features="Own history", methods="LSTM", arch=NR, validation="75/25 split", metrics="'99% accuracy'",
        findings="Reports 99% accuracy", lim_auth="COVID-19 effects not incorporated",
        lim_crit="Interpolated annual data inflates sample; random/simple split; accuracy claim not credible without baselines",
        relevance="Low-medium: example of weak evaluation practice in import forecasting", adapt="Cautionary example only"),
    "10.1016/j.knosys.2022.108687": dict(
        domain="Oil import dependence forecasting", objective="Forecast oil import dependence with fuzzy time series and multi-objective optimisation",
        rq=NR, geo="China", data=NR, period=NR, freq=NR, n=NR, target="Oil import dependence ratio", features=NR,
        methods="Fuzzy time series; multi-objective optimisation", arch=NR, validation=NR, metrics=NR, findings=NR, lim_auth=NR,
        lim_crit="Abstract not available at screening; extraction pending", relevance="Medium: import-dependence forecasting", adapt=NR),
    "10.1016/j.ijforecast.2018.09.001": dict(
        domain="Fuel demand forecasting (military logistics)", objective="Long-term forecasting of fuel demand at theatre entry points",
        rq=NR, geo=NR, data=NR, period=NR, freq=NR, n=NR, target="Fuel demand", features=NR, methods=NR, arch=NR, validation=NR, metrics=NR,
        findings=NR, lim_auth=NR, lim_crit="Abstract not available at screening; extraction pending",
        relevance="Medium: fuel supply-chain forecasting in a top forecasting journal", adapt=NR),
}
