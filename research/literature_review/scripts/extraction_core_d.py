"""Evidence extraction, core tier, part D: records whose abstracts were obtained from publisher landing pages
or RePEc/IDEAS (metadata/raw/manual_abstracts.json). Entries here override part A/B/C entries with the same DOI.
"""
NR = "Not reported in abstract"

E = {
    "10.1007/s10553-026-02011-4": dict(
        domain="Oil import demand forecasting", objective="Effect of new-energy supply growth on China's oil import demand; best forecasting method",
        rq=NR, geo="China", data="China statistical yearbooks", period=NR, freq="Annual (yearbook data)", n=NR, target="Oil import demand",
        features="Indicator combinations chosen by grey relational analysis (new-energy supply: wind, solar, hydro, nuclear)",
        methods="Grey relational analysis + machine learning; comparison of models", arch=NR, validation="Comparative experiments", metrics=NR,
        findings="Proposes the method with highest accuracy and stability (model not named in abstract)", lim_auth=NR,
        lim_crit="Annual yearbook data; contemporaneous features; single country", relevance="High: most recent ML oil-import-demand study",
        adapt="Energy-transition covariates are irrelevant for Kyrgyz short-term volumes; illustrates the annual single-country norm"),
    "10.1007/978-3-032-09945-7_39": dict(
        domain="Crude oil import demand (econometrics)", objective="Determinants and elasticities of Thailand's crude oil imports", rq=NR,
        geo="Thailand", data=NR, period=NR, freq=NR, n=NR, target="Crude oil import demand",
        features="GDP, OPEC production, domestic energy production, Dubai price", methods="Multiple regression; elasticity analysis",
        arch=NR, validation="In-sample", metrics="Elasticities", findings="Price elasticities -0.011 (SR) and -0.015 (LR); income 0.212 and 0.298",
        lim_auth=NR, lim_crit="Title promises AI-based forecasting but abstract reports regression only; no out-of-sample test",
        relevance="Medium: shows import demand is price-inelastic, so price features may add little to short-term volume forecasts",
        adapt="Expectation for price ablation (H3)"),
    "10.1007/978-981-97-8031-0_81": dict(
        domain="Petroleum production and import forecasting", objective="Forecast crude and POL production and imports with ARIMA", rq=NR,
        geo="India", data=NR, period="1987-2022", freq="Annual", n="36 years", target="Production and imports of crude oil and POL",
        features="Own history", methods="ARIMA", arch=NR, validation=NR, metrics=NR,
        findings="Crude production falling; product output and imports rising over the next five years", lim_auth=NR,
        lim_crit="Annual univariate; no accuracy evaluation reported in abstract", relevance="Medium: physical import forecasting precedent", adapt="None"),
    "10.1007/s11135-025-02268-7": dict(
        domain="Petroleum product import demand (econometrics)", objective="Determinants of total and product-specific petroleum import demand",
        rq=NR, geo="Tanzania", data="Bulk Procurement System imports", period="1990-2021", freq="Annual", n="32 years",
        target="Total and product imports (gasoline/diesel, kerosene, jet fuel)", features="Exchange rate, oil prices, growth, demographics",
        methods="ARDL bounds test, ECM, structural-break analysis", arch=NR, validation="In-sample", metrics="Elasticities",
        findings="Brent and exchange rate long-run determinants; inelastic demand; structural breaks change cointegration conclusions",
        lim_auth=NR, lim_crit="Explanatory; annual", relevance="High: product-level refined imports in a developing importer; structural breaks matter",
        adapt="Break-aware modelling; exchange rate as candidate feature"),
    "10.1007/s41060-025-00781-4": dict(
        domain="Raw-material trade-flow forecasting", objective="Multi-horizon TFT forecasts of raw-material trade flows", rq=NR, geo="Global",
        data="UN Comtrade, CEPII Gravity, World Bank", period=NR, freq=NR, n=NR, target="Trade flows", features="Gravity and macro covariates",
        methods="TFT vs random forest and graph attention networks", arch="TFT", validation=NR, metrics="R2",
        findings="17% increase in R2 over baselines; robust in COVID-19 and Ukraine-conflict periods", lim_auth=NR,
        lim_crit="R2 is not a forecast-accuracy standard; no naive or statistical baselines in abstract", relevance="High: Comtrade-based DL trade forecasting",
        adapt="Use MASE and naive baselines instead of R2"),
    "10.1016/j.ijforecast.2020.11.009": dict(
        domain="Forecasting methodology (cross-learning)", objective="Accuracy of cross-learning NN vs series-by-series models", rq=NR,
        geo="Not applicable", data="M4 monthly series", period="Not applicable", freq="Monthly", n="M4 monthly subset", target="Generic",
        features="Lags", methods="Cross-learning neural networks vs local models; combinations", arch="NN", validation="M4 holdout", metrics=NR,
        findings="Cross-learning is promising if suitable strategies extract information from large diverse datasets",
        lim_auth=NR, lim_crit="Large datasets; transfer to 44 series uncertain", relevance="High", adapt="Combine local and global forecasts"),
    "10.1016/j.ijforecast.2016.02.001": dict(
        domain="Probabilistic energy forecasting", objective="Introduce GEFCom2014 and review probabilistic energy forecasting", rq=NR,
        geo="International competition", data="Load, price, wind, solar tracks", period=NR, freq="Hourly", n="581 participants, 61 countries",
        target="Energy quantities (probabilistic)", features=NR, methods="Competition entries", arch=NR, validation="Competition evaluation",
        metrics=NR, findings="Reviews progress and gives 12 predictions for energy forecasting", lim_auth=NR, lim_crit="Electricity-sector focus",
        relevance="High: maturity of probabilistic forecasting in electricity, contrast with fuel imports", adapt="Quantile-based evaluation"),
    "10.1016/j.ijforecast.2018.09.001": dict(
        domain="Fuel demand forecasting (military supply chain)", objective="Long-term fuel demand at theatre entry points", rq=NR, geo=NR,
        data="War-fighter demand patterns; supply network structure", period=NR, freq=NR, n=NR, target="Fuel demand at entry point",
        features="Demand patterns and network configuration", methods="Simulation-based aggregation", arch=NR, validation=NR, metrics=NR,
        findings="Produces an empirical distribution of demand; sensitive to demand pattern, network configuration and constraints", lim_auth=NR,
        lim_crit="Military context; simulation rather than statistical learning", relevance="High: rare distributional fuel-supply forecast in IJF",
        adapt="Report peak timing and lead time, not only means"),
    "10.1016/j.enpol.2009.05.069": dict(
        domain="Energy security measurement", objective="Short-term external supply risk index for EU members", rq=NR, geo="EU Member States",
        data=NR, period=NR, freq=NR, n=NR, target="Supply risk index (oil, gas, coal)", features="Diversification, supplier political risk, transit risk, economic impact",
        methods="Composite index", arch=NR, validation="Not predictive", metrics=NR, findings="Exposure differs by fuel; aggregate indices can mislead",
        lim_auth=NR, lim_crit="No predictive validation", relevance="High: transit risk component matters for landlocked importers",
        adapt="Transit-risk and supplier-risk features"),
    "10.1016/j.enpol.2007.11.011": dict(
        domain="Oil vulnerability measurement", objective="Rank oil importers by vulnerability", rq=NR, geo="26 net oil importers", data=NR,
        period="2004", freq="Cross-section", n="26 countries", target="Oil vulnerability index", features="Nine indicators incl. supplier diversification and political risk",
        methods="PCA composite index", arch=NR, validation="Not predictive", metrics=NR, findings="Large differences across and within regions",
        lim_auth=NR, lim_crit="Single year; no link to subsequent disruptions", relevance="Medium-high: indicator menu for vulnerability features", adapt="Indicator selection"),
    "10.1016/j.rser.2014.10.064": dict(
        domain="Energy security review", objective="Review definitions, dimensions and indexes of energy security", rq=NR, geo="Not applicable",
        data="104 studies (2001-2014)", period="2001-2014", freq="Not applicable", n="104 studies", target="Not applicable", features=NR,
        methods="Literature review", arch=NR, validation=NR, metrics=NR, findings="Concept is contextual and dynamic; indices vary widely and are hard to compare",
        lim_auth=NR, lim_crit=NR, relevance="High: conceptual basis; separates supply security from forecasting", adapt="Definition of supply stress"),
    "10.1016/j.econmod.2021.02.013": dict(
        domain="Import forecasting", objective="Leading indicator of imports from partners' export expectations", rq=NR, geo="Six advanced economies",
        data="Business surveys of trading partners", period=NR, freq=NR, n="6 countries", target="Import growth", features="Partners' export expectations ('Import Climate')",
        methods="Leading-indicator forecasting", arch=NR, validation=NR, metrics=NR, findings="Import Climate outperforms domestic business-cycle indicators",
        lim_auth=NR, lim_crit="Advanced economies; aggregate imports", relevance="Very high: supplier-side information predicts imports",
        adapt="Supplier-side signals (e.g., Russian export-ban status) as features"),
    "10.1016/j.energy.2018.08.127": dict(
        domain="Oil import dependence forecasting", objective="Forecast China's foreign oil dependence 2017-2030", rq=NR, geo="China", data=NR,
        period="To 2016; forecast 2017-2030", freq="Annual", n=NR, target="Oil import dependence", features="Own history (two dimensions)",
        methods="NMGM grey model + ARIMA on residuals", arch="Hybrid", validation=NR, metrics="MAE 2.1-2.3%",
        findings="Dependence rises from ~65% (2016) to over 80% by 2030", lim_auth=NR, lim_crit="Long-horizon point forecast without intervals",
        relevance="Medium: typical long-run dependence forecasting", adapt="None"),
    "10.1016/j.energy.2014.02.091": dict(
        domain="Oil supply risk measurement", objective="Modified diversification index with country risk and export potential", rq=NR,
        geo="China, Japan, US, EU", data=NR, period=NR, freq=NR, n="4 importers", target="External oil supply risk", features="Supplier shares, country risk, potential exports",
        methods="Modified diversification index", arch=NR, validation="Not predictive", metrics=NR, findings="Importers weight supplier risk and export potential differently",
        lim_auth=NR, lim_crit="No predictive validation", relevance="High: risk-weighted concentration as feature", adapt="Risk-weighted HHI"),
    "10.1016/j.physa.2024.129977": dict(
        domain="Economic forecasting with trade networks", objective="Use trade-network descriptors in ML growth forecasts", rq=NR,
        geo="200+ countries", data="Section-level trade data", period="2010-2022", freq="Annual", n="200+ countries", target="Economic growth",
        features="Network topology descriptors, recent growth, population, primary sector", methods="RF, XGBoost, LightGBM vs linear", arch=NR,
        validation=NR, metrics=NR, findings="Non-linear models beat linear; about half of top features are network descriptors (SHAP)", lim_auth=NR,
        lim_crit="Annual GDP target", relevance="High: trade-structure features add predictive value in cross-country ML", adapt="Network/supplier features"),
    "10.1016/j.energy.2025.137996": dict(
        domain="Geopolitical risk and energy imports", objective="Dynamic responses of China's energy imports to GPR shocks", rq=NR, geo="China",
        data="Monthly imports, GPR", period="Jan 2008 - Dec 2024", freq="Monthly", n="204 months", target="Energy import volumes and values",
        features="GPR shocks; renewables", methods="Local projections", arch=NR, validation="Not predictive", metrics=NR,
        findings="GPR shocks lower volumes short term and raise them later; crude oil adjusts most", lim_auth=NR,
        lim_crit="Explanatory impulse responses, not forecasts; large importer", relevance="High: monthly GPR-import link that motivates H3",
        adapt="Lag structure of GPR effects"),
    "10.1016/j.eneco.2025.108595": dict(
        domain="Geopolitical risk and energy import survival", objective="Survival of energy-import relationships and GPR effects", rq=NR,
        geo="Global", data="HS6 trade data", period="1995-2022", freq="Annual", n="300,971 trade spells", target="Hazard of import-relationship ending",
        features="Exporter GPR", methods="Survival analysis", arch=NR, validation="Not predictive", metrics=NR,
        findings="Exporter GPR raises disruption hazard, more for petroleum; weaker for OECD exporters", lim_auth=NR,
        lim_crit="Annual; relationship survival not volumes", relevance="High: supplier-country GPR predicts petroleum supply breaks",
        adapt="Supplier-weighted GPR feature"),
}


# Core records for which only bibliographic metadata could be obtained (Elsevier/Bloomsbury abstracts blocked or absent).
MD = "Not available: metadata only (abstract not accessible without bypassing access controls)"


def _meta_only(domain, relevance):
    return dict(domain=domain, objective=MD, rq=MD, geo=MD, data=MD, period=MD, freq=MD, n=MD, target=MD, features=MD,
                methods=MD, arch=MD, validation=MD, metrics=MD, findings=MD, lim_auth=MD,
                lim_crit="No claims are drawn from this record beyond its title", relevance=relevance, adapt="Retrieve full text through library access before citing findings")


E.update({
    "10.1016/j.jclepro.2019.05.314": _meta_only("Oil import dependence forecasting (India)", "Medium: title indicates a forecast of India's oil import dependence"),
    "10.1016/j.energy.2021.122312": _meta_only("Gasoline demand forecasting (Australia, ML regression)", "Medium: ML fuel-demand forecasting in a top energy journal"),
    "10.1016/s0304-4076(96)01802-7": _meta_only("Pooled vs heterogeneous estimators for gasoline demand", "High: earliest pooled-vs-country comparison for fuel demand; findings must be read in full text before use"),
    "10.1016/j.esr.2025.101695": _meta_only("EPU and GPR effects on oil imports (China)", "High: title indicates estimated effects of GPR on oil imports"),
    "10.5040/9798881888824.ch-6": _meta_only("Central Asian trade with Russia after 2022", "High: post-2022 trade context for Kyrgyzstan"),
    "10.1016/j.knosys.2022.108687": _meta_only("Oil import dependence forecasting (China, fuzzy time series)", "Medium: import-dependence forecasting precedent"),
})
