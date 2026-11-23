"""Evidence extraction, core tier, part B: energy security, supply disruption and early warning,
geopolitical risk and sanctions, landlocked economies. Same conventions as extraction_core_a.py.
"""
NR = "Not reported in abstract"

E = {
    "10.3390/su16062284": dict(
        domain="Energy crisis early warning", objective="Identify determinants of world energy crises with a binary logit early-warning model",
        rq=NR, geo="World", data="Thirteen indicators (stocks, production-consumption balance, imports, drilling, inflation, dollar, activity, GPR)",
        period="Jan 1973 - Dec 2022", freq="Monthly", n="600 months", target="Energy-crisis month (binary)", features="13 indicators incl. geopolitical risk",
        methods="Binary logit", arch=NR, validation=NR, metrics="Predicted probability of crisis months", findings="Crises driven by supply-demand imbalances, investment, macro-financial disruption and geopolitical risk; model reported to predict crisis months 'with 99% probability'",
        lim_auth=NR, lim_crit="Few crisis episodes; in-sample fit claims; global not country level", relevance="High: early-warning framing with GPR as predictor",
        adapt="Event-based evaluation; GPR as covariate"),
    "10.3390/su10010283": dict(
        domain="Oil security early warning", objective="Construct an early-warning indicator system for China's oil security", rq=NR, geo="China",
        data="23 sub-indicators (resource, market, consumption security)", period=NR, freq="Annual", n=NR, target="Composite oil-security level",
        features="23 indicators", methods="Factor analysis (SPSS)", arch="Composite index", validation="None (index construction)", metrics=NR,
        findings="Oil security level threatened and declining, eased by substitutes", lim_auth=NR, lim_crit="Index, not a predictive model; no out-of-sample test",
        relevance="Medium: dominant 'index-based early warning' approach the project contrasts with", adapt="Indicator taxonomy"),
    "10.1109/icrera66237.2025.11283745": dict(
        domain="Renewable supply shortfall early warning", objective="Probabilistic shortage alarms for renewable output up to 72 h", rq=NR,
        geo="DE, DK, ES, IT, PL", data="ENTSO-E/OPSD, ERA5/PECD", period=NR, freq="Hourly", n=NR, target="Shortfall event (>10% overprediction)",
        features="Weather, recent generation/load, time encodings", methods="Gradient-boosted trees + probabilistic classifier", arch="Two-stage: point forecast then alarm classifier",
        validation="Blocked time-series CV", metrics="MAE, RMSE, MAPE, PR-AUC (0.38-0.53), Brier (0.21-0.26)",
        findings="Useful alarms up to 72 h with near-linear reliability at 48 h", lim_auth=NR, lim_crit="Conference paper; electricity domain",
        relevance="High: template for forecast-to-alarm design and its metrics (PR-AUC, Brier, reliability)", adapt="Two-stage alarm design; PR-AUC and Brier"),
    "10.1049/itr2.12083": dict(
        domain="Fuel shortage prediction", objective="Model fuel shortages during hurricane evacuations", rq=NR, geo="Florida, USA",
        data="GasBuddy crowdsourced shortage data; evacuation surveys", period="Recent hurricanes (Irma etc.)", freq="Daily", n=NR,
        target="Share of stations without fuel", features="Evacuation traffic demand", methods="SIR epidemic model; optimal control", arch=NR,
        validation=NR, metrics=NR, findings="Shortages behave like an epidemic and correlate with evacuation traffic", lim_auth=NR,
        lim_crit="Local demand shock, not import supply", relevance="Medium: one of the few studies that observes actual retail shortages rather than proxies",
        adapt="Distinguish observed shortages from import proxies"),
    "10.1016/j.enpol.2011.06.034": dict(
        domain="Energy security measurement", objective="Measure diversification of oil and gas supplies in OECD", rq=NR, geo="OECD",
        data=NR, period="Last decade before 2011", freq="Annual", n=NR, target="Diversification indices", features="Supplier shares; political, size and transport risk adjustments",
        methods="HHI-type diversification indices", arch=NR, validation="Not predictive", metrics=NR,
        findings="Little change in oil diversification; gas diversification increased; heterogeneity across countries", lim_auth=NR,
        lim_crit="Descriptive; no link to future disruptions", relevance="High: standard supplier-concentration measure used as feature and benchmark",
        adapt="Risk-adjusted HHI"),
    "10.3390/en11071687": dict(
        domain="Energy supply security forecasting", objective="Forecast China's energy supply security level", rq=NR, geo="China",
        data="Comprehensive evaluation indicators", period=NR, freq="Annual", n=NR, target="Composite energy supply security score",
        features=NR, methods="ARIMA-XGBoost hybrid", arch="Two hybrid approaches", validation=NR, metrics=NR,
        findings="Energy supply security is dynamic; hybrid approach proposed", lim_auth=NR, lim_crit="Target is a constructed index; very short annual series",
        relevance="Medium: hybrid boosting for security forecasting", adapt="Hybrid residual modelling"),
    "10.48550/arxiv.2407.16739": dict(
        domain="Supply-chain shortfall forecasting", objective="Forecast first-tier supply disruptions at Ford", rq=NR, geo="Ford global plants",
        data="500,000+ multivariate series (capacity, inventory, utilisation, processing)", period=NR, freq=NR, n=">500,000 series",
        target="Supply shortfall", features="Factory Physics features", methods="Attention seq2seq DL with clustering of heterogeneous subgroups",
        arch="Enhanced attention seq2seq", validation=NR, metrics=NR, findings="Methodology for heterogeneous large panels (details in full text)",
        lim_auth=NR, lim_crit="Proprietary data; industrial not national", relevance="Medium: shortfall forecasting with heterogeneous global models",
        adapt="Grouping heterogeneous series"),
    "10.22190/fueo201005025v": dict(
        domain="Oil market concentration", objective="Measure supply concentration on Serbia's oil and derivatives market", rq=NR, geo="Serbia (landlocked)",
        data=NR, period=NR, freq=NR, n=NR, target="HHI", features="Market shares", methods="Herfindahl-Hirschman index", arch=NR,
        validation="Not predictive", metrics=NR, findings="Concentration level measured over time (values in full text)", lim_auth=NR,
        lim_crit="Domestic market competition, not import-origin concentration", relevance="Medium: landlocked oil-products HHI application",
        adapt="HHI computation conventions"),
    "10.2139/ssrn.4041666": dict(
        domain="Early-warning evaluation", objective="Evaluate early-warning indicators of banking crises with ROC analysis", rq=NR,
        geo="Six countries", data="Balanced panel of candidate EWIs", period=NR, freq=NR, n="6 countries", target="Crisis events",
        features="Credit, debt service, interbank rates, reserves", methods="ROC-based evaluation", arch=NR, validation=NR, metrics="ROC/AUC",
        findings="Credit-based indicators give stable signals; linear combinations improve predictive power", lim_auth=NR,
        lim_crit="Banking domain; few events", relevance="Medium: evaluation of rare-event warnings with ROC", adapt="ROC/PR curves and signal stability"),
    "10.1257/aer.20191823": dict(
        domain="Geopolitical risk measurement", objective="Construct a news-based geopolitical risk index and estimate its effects", rq=NR,
        geo="Global; country-specific indices", data="Newspaper article counts", period="1985 onward (historical back to 1900)", freq="Monthly",
        n=NR, target="GPR index", features="Text counts of geopolitical tensions", methods="Text-based index; VAR-type analyses", arch=NR,
        validation=NR, metrics=NR, findings="High GPR lowers real activity and returns and shifts capital flows; threats drive effects",
        lim_auth=NR, lim_crit="English-language newspapers; global index has little cross-country variation for small economies",
        relevance="Very high: source of the GPR feature", adapt="GPR global, threats/acts; country GPR where available"),
    "10.2139/ssrn.7679879": dict(
        domain="Refined-product supply disruption", objective="Effects of the 2026 Iran war on refined-product premiums and supply", rq="Where products repriced; what limited replacement; how prices linked to trade",
        geo="US, northwest Europe, Hormuz", data="Prices, Hormuz shipping, inventories, refinery operations, US exports", period="2026 event window",
        freq="Daily/monthly", n=NR, target="Crack spreads and premiums", features="Prewar import dependence, inventories, utilisation",
        methods="Event estimates; joint production, storage and spatial arbitrage framework", arch=NR, validation="Not predictive", metrics=NR,
        findings="Crack spreads rose; larger increases where prewar refined-product import dependence was higher; inventories buffer, high utilisation amplifies",
        lim_auth=NR, lim_crit="Working paper; prices rather than volumes", relevance="High: refined products can be scarce even when crude is available",
        adapt="Refined products as the right target level"),
    "10.2139/ssrn.4368618": dict(
        domain="Sanctions and trade rerouting", objective="Document trade flows into Russia via the Caucasus and Central Asia after 2022", rq=NR,
        geo="EU, Russia, Armenia, Kazakhstan, Kyrgyz Republic", data="HS6 bilateral monthly exports", period="Around 2022", freq="Monthly",
        n=NR, target="EU exports to Russia and to CCA3", features="Sanctioned vs non-sanctioned products", methods="Descriptive and difference comparisons",
        arch=NR, validation="Not predictive", metrics=NR, findings="Direct EU-Russia exports fell sharply; EU exports to Armenia, Kazakhstan and Kyrgyz Republic rose, especially for sanctioned goods",
        lim_auth=NR, lim_crit="Working paper (EBRD)", relevance="High: Kyrgyz trade data are affected by re-export and rerouting after 2022",
        adapt="Structural-break flags for 2022"),
    "10.1111/ecpo.70046": dict(
        domain="Trade statistics quality", objective="Assess discrepancies between direct and mirror data and sanction effects", rq=NR,
        geo="All available reporters", data="Bilateral flows at HS2", period="2003-2024", freq="Annual", n=NR, target="Mirror discrepancy",
        features="Sanction status", methods="Panel analysis", arch=NR, validation=NR, metrics=NR,
        findings="Discrepancies fell until 2019 then surged; sanctioned countries show lower, sanction-imposing countries higher discrepancies",
        lim_auth=NR, lim_crit="HS2 aggregation", relevance="High: trade-data quality deteriorated in the project's test period",
        adapt="Mirror checks as data-quality features"),
    "10.3390/en15217822": dict(
        domain="Energy security (Central Asia)", objective="Analyse energy security of hydropower producers Tajikistan and Kyrgyzstan", rq=NR,
        geo="Kyrgyzstan; Tajikistan", data=NR, period=NR, freq=NR, n=NR, target="Energy security dimensions", features=NR,
        methods="Qualitative and indicator analysis", arch=NR, validation="Not predictive", metrics=NR, findings=NR, lim_auth=NR,
        lim_crit="Electricity-focused", relevance="High: one of the few Kyrgyz energy-security papers", adapt="Context for Kyrgyz import dependence"),
    "measuringthesecurityofexternalenergysupp": dict(
        domain="Energy security (Central Asia)", objective="Measure risky external energy supply (REES) and export demand (REED) in Central Asia",
        rq=NR, geo="Central Asian republics vs EU and OPEC", data=NR, period=NR, freq=NR, n=NR, target="REES and REED indices",
        features="Supplier and destination risk", methods="Disaggregated REES/REED indices", arch=NR, validation="Not predictive", metrics=NR,
        findings="Regional oil REES index significantly higher than the EU's", lim_auth=NR, lim_crit="No DOI found; index not forecast",
        relevance="High: quantifies Central Asian oil-supply risk", adapt="Risk-weighted supplier index as feature"),
    "10.1111/twec.13416": dict(
        domain="Trade policy (Kyrgyzstan)", objective="Examine Kyrgyz trade policy as a double-landlocked transition economy", rq=NR,
        geo="Kyrgyzstan", data="WTO Trade Policy Review", period=NR, freq=NR, n=NR, target=NR, features=NR, methods="Policy analysis", arch=NR,
        validation=NR, metrics=NR, findings="Open economy with modest growth dividend; high remittance dependence", lim_auth=NR, lim_crit=NR,
        relevance="Medium: context for Kyrgyz trade structure", adapt="Context"),
    "10.29105/trendinomics.v2i2.19": dict(
        domain="Trade forecasting under geopolitical uncertainty", objective="Hybrid econometric-LSTM forecasts of trade flows", rq=NR,
        geo="Countries trading with China and the US", data=NR, period=NR, freq="Monthly", n=NR, target="Trade flows",
        features="PCA/LASSO-selected predictors; convergence clubs", methods="Club convergence + PCA + LASSO + LSTM", arch="LSTM",
        validation="Multiple horizons", metrics="Panel Diebold-Mariano", findings="Outperforms LSTM benchmarks; significant gains one month ahead",
        lim_auth=NR, lim_crit="Young journal; benchmarks limited to LSTM variants", relevance="Medium: panel DM tests for trade forecasts",
        adapt="Panel DM testing"),
}
