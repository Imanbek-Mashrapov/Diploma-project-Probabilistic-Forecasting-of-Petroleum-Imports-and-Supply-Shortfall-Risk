"""Evidence extraction, core tier, part C: global forecasting, deep learning vs boosting, probabilistic
forecasting, forecast evaluation and real-time data. Same conventions as extraction_core_a.py.
"""
NR = "Not reported in abstract"

E = {
    "10.1016/j.ijforecast.2021.03.004": dict(
        domain="Forecasting methodology (global vs local)", objective="Formalise local and global forecasting of groups of series",
        rq="When can global methods match or beat local ones?", geo="Not applicable", data="Benchmark collections (M-competition type)",
        period="Not applicable", freq="Various", n="Large benchmark sets", target="Generic time series",
        features="Lags of all series", methods="Global linear models, deep networks vs local methods", arch="Global AR (linear and neural)",
        validation="Benchmark holdouts", metrics=NR,
        findings="Global methods are not more restrictive than local ones; complexity of local methods grows with the set size; global linear models competitive with far fewer parameters",
        lim_auth=NR, lim_crit="Benchmarks have many long series; a 44-series panel with ~140 months is a much smaller setting",
        relevance="Very high: theoretical basis for RQ1 (local vs global)", adapt="Global AR baselines; capacity reasoning for small panels"),
    "10.1016/j.ijforecast.2020.11.009": dict(
        domain="Forecasting methodology (cross-learning)", objective="Investigate accuracy of cross-learning methods", rq=NR,
        geo="Not applicable", data="M4 subsets (per screening record)", period="Not applicable", freq=NR, n=NR, target="Generic series",
        features=NR, methods="Cross-learning (global) NN and linear models vs series-by-series", arch=NR, validation=NR, metrics=NR,
        findings=NR, lim_auth=NR, lim_crit="Abstract not available at screening; extraction pending",
        relevance="High: empirical evidence on cross-learning conditions", adapt="Homogeneity checks before pooling"),
    "10.1016/j.patcog.2021.108441": dict(
        domain="Forecasting methodology (global models)", objective="Identify when global models beat univariate benchmarks", rq="Effect of homogeneity, complexity, length and number of series",
        geo="Not applicable", data="Simulated series (AR and other DGPs)", period="Not applicable", freq="Simulated", n="Controlled simulation",
        target="Simulated series", features="Lags", methods="Global models (pooled regression, RNN, boosting per paper) vs univariate",
        arch=NR, validation="Simulation holdout", metrics=NR,
        findings="Performance depends on homogeneity, pattern complexity, model complexity, and series length/number (details in full text)",
        lim_auth=NR, lim_crit="Simulated data", relevance="Very high: guides model capacity for a 22-44 series panel", adapt="Heterogeneity diagnostics"),
    "10.3390/forecast8050089": dict(
        domain="Forecasting short annual panels", objective="Compare country-specific, pooled and shrunk parameter sharing for compositional forecasts",
        rq=NR, geo="Cross-country panels", data="Short annual compositional panels (energy mixes, employment etc.)", period=NR, freq="Annual",
        n=NR, target="Compositional shares", features=NR, methods="Replicator-dynamics model under three sharing regimes; log-ratio benchmarks; Dirichlet; pooled ML",
        arch=NR, validation="Expanding-window rolling origin", metrics=NR, findings="Title: pooling beats structure on short annual panels", lim_auth=NR,
        lim_crit="Compositions, not volumes", relevance="High: recent evidence that pooling helps on short cross-country panels",
        adapt="Shrinkage between local and global (validation-shrunk)"),
    "10.1080/01605682.2022.2118629": dict(
        domain="Forecasting methodology (stat vs ML vs DL)", objective="Test the value added by DL over ML and statistical methods",
        rq=NR, geo="Not applicable", data="M3 series", period="Not applicable", freq="Yearly, quarterly, monthly", n="M3 (3,003 series)",
        target="Generic", features=NR, methods="GluonTS DL models, ML and statistical", arch=NR, validation="M3 holdout", metrics=NR,
        findings="DL combinations beat most standard models, especially monthly and long horizons, but at high computational cost (truncated)",
        lim_auth=NR, lim_crit="Benchmark series, not trade", relevance="High: DL gains are conditional and costly", adapt="Ensembles; cost reporting"),
    "10.1016/j.ijforecast.2019.04.014": dict(
        domain="Forecasting competition", objective="Report the M4 competition", rq=NR, geo="Not applicable", data="100,000 series",
        period="Not applicable", freq="Yearly to hourly", n="100,000 series", target="Generic", features=NR, methods="61 methods",
        arch=NR, validation="Holdout", metrics="sMAPE, MASE, OWA; MSIS for intervals", findings="Summarises top-performing methods and major findings (details in full text)",
        lim_auth=NR, lim_crit="Mostly univariate; no exogenous drivers", relevance="High: evaluation conventions (MASE, interval scoring)", adapt="MASE, MSIS"),
    "10.1016/j.ijforecast.2021.11.013": dict(
        domain="Forecasting competition", objective="Report M5 Accuracy", rq=NR, geo="US (Walmart)", data="42,840 hierarchical sales series",
        period=NR, freq="Daily", n="42,840 series", target="Unit sales", features="Prices, calendar, events", methods="Many; top methods tree-based (per Januschowski et al.)",
        arch=NR, validation="Holdout", metrics="WRMSSE", findings="Results and best methods summarised", lim_auth=NR,
        lim_crit="Retail, large data", relevance="High: evidence that GBM-based global models dominate with exogenous features", adapt="Global LightGBM design"),
    "10.1007/s10618-022-00894-5": dict(
        domain="Forecast evaluation", objective="Document pitfalls of forecast evaluation in ML", rq=NR, geo="Not applicable", data="Illustrations",
        period="Not applicable", freq=NR, n=NR, target="Generic", features=NR, methods="Tutorial", arch=NR, validation=NR, metrics=NR,
        findings="Flawed evaluation practice leads ML studies to spurious conclusions", lim_auth=NR, lim_crit=NR,
        relevance="Very high: checklist for the project's evaluation design", adapt="Benchmark choice, leakage control, metric choice"),
    "10.1016/s0164-0704(02)00062-9": dict(
        domain="Real-time data", objective="How forecasts differ when using real-time vs latest-available data", rq="Does data vintage matter for forecasting?",
        geo="United States", data="Real-time macro data set (Philadelphia Fed)", period=NR, freq="Quarterly", n=NR, target="Macro aggregates",
        features=NR, methods="Univariate and other models", arch=NR, validation="Real-time vs latest-vintage comparison", metrics=NR,
        findings="Real-time data matter for some issues (e.g., lag length) and accuracy measures can be vintage-sensitive", lim_auth=NR,
        lim_crit="Macro aggregates, not trade", relevance="Very high: foundation for publication-lag-aware evaluation", adapt="Vintage-aware evaluation"),
    "10.48550/arxiv.2608.09033": dict(
        domain="Real-time ML forecasting", objective="Test whether ML gains survive real-time vintages", rq="Does the ML edge over the Phillips curve survive real-time data?",
        geo="United States", data="ALFRED vintages", period="2000-2026", freq="Monthly", n=NR, target="CPI and PCE inflation",
        features="Unemployment, payrolls, GDP, term spread", methods="RW, AR(1), Phillips curve, ADL-OLS vs RF, GB, elastic net, SVR",
        arch=NR, validation="Recursive re-estimation at 3, 6, 12 months on vintage-consistent panels", metrics=NR,
        findings="Examines whether ML advantage and SHAP rankings are artefacts of revised data (result truncated)", lim_auth=NR,
        lim_crit="Preprint", relevance="High: direct precedent for testing ML gains under real-time data", adapt="Revised vs real-time comparison design"),
    "10.1016/j.ijforecast.2021.10.004": dict(
        domain="Tree-based forecasting", objective="Explain the success of gradient-boosted trees in M5", rq=NR, geo="Not applicable", data="M5",
        period=NR, freq=NR, n=NR, target="Retail sales", features=NR, methods="Gradient boosted trees (LightGBM) vs DL", arch=NR,
        validation=NR, metrics=NR, findings="Tree-based methods outshone DL in M5; winners relied on them", lim_auth=NR,
        lim_crit="Large retail data", relevance="High: rationale for GBM as the main rival", adapt="Feature engineering for global GBM"),
    "10.1609/aaai.v37i9.26317": dict(
        domain="Deep learning for forecasting", objective="Question Transformer effectiveness for long-term forecasting", rq=NR, geo="Not applicable",
        data="Standard LTSF benchmarks", period="Not applicable", freq=NR, n=NR, target="Generic", features=NR,
        methods="LTSF-Linear vs Transformer models", arch="One-layer linear models", validation=NR, metrics=NR,
        findings="Simple linear models compete with or beat Transformers on LTSF benchmarks", lim_auth=NR, lim_crit=NR,
        relevance="High: argues against large Transformers on short series", adapt="Linear baselines"),
    "10.1016/j.ijforecast.2021.03.012": dict(
        domain="Deep learning for forecasting", objective="Interpretable multi-horizon forecasting with TFT", rq=NR, geo="Not applicable",
        data="Several real-world datasets", period=NR, freq=NR, n=NR, target="Generic", features="Static covariates, known future inputs, observed covariates",
        methods="TFT", arch="Recurrent local processing + interpretable self-attention + variable selection", validation=NR,
        metrics="Quantile losses (per paper)", findings="Introduces TFT", lim_auth=NR, lim_crit="Data-hungry relative to a 5,500-observation panel",
        relevance="Medium-high: quantile output and variable selection", adapt="Only as compact optional model"),
    "10.48550/arxiv.1905.10437": dict(
        domain="Deep learning for forecasting", objective="Univariate point forecasting with deep residual MLP stacks", rq=NR,
        geo="Not applicable", data="M3, M4, TOURISM", period="Not applicable", freq=NR, n=NR, target="Generic", features="Own history",
        methods="N-BEATS", arch="Backward/forward residual fully connected stacks", validation="Competition holdouts", metrics="sMAPE/MASE/OWA",
        findings="Improves 11% over statistical benchmark and 3% over M4 winner", lim_auth=NR, lim_crit="Univariate; ensembles of many models",
        relevance="High: candidate global DL model", adapt="Small N-BEATS ensemble"),
    "10.1016/j.ijforecast.2019.07.001": dict(
        domain="Probabilistic deep learning", objective="Probabilistic forecasting with autoregressive RNNs trained on related series", rq=NR,
        geo="Not applicable", data="Several real-world datasets", period=NR, freq=NR, n=NR, target="Generic", features="Covariates, lags",
        methods="DeepAR", arch="Autoregressive LSTM with likelihood output", validation=NR, metrics=NR,
        findings="More accurate than state of the art with less tuning (per abstract)", lim_auth=NR, lim_crit="Benefits from many related series",
        relevance="High: global probabilistic DL baseline", adapt="Likelihood-based global RNN"),
    "10.3390/en18071685": dict(
        domain="Transport energy forecasting", objective="Compare LSTM and XGBoost", rq=NR, geo="Thailand", data="Vehicle registrations, VKT, macro indicators",
        period="1993-2022", freq="Annual", n="30 years", target="Transport energy consumption", features="Vehicle stock by size, VKT, macro",
        methods="LSTM; XGBoost", arch=NR, validation="Train/test split", metrics="R2 and others", findings="XGBoost R2 0.95 vs LSTM 0.20 on test",
        lim_auth=NR, lim_crit="Very short annual sample; R2 not a forecasting metric", relevance="Medium: small-data GBM > DL in energy",
        adapt="Expect GBM advantage on short series"),
    "10.1111/j.1467-9868.2007.00587.x": dict(
        domain="Probabilistic forecast evaluation", objective="Diagnostic evaluation: maximise sharpness subject to calibration", rq=NR,
        geo="Not applicable", data="Not applicable", period="Not applicable", freq=NR, n=NR, target="Continuous variables", features=NR,
        methods="PIT histograms, marginal calibration plots, sharpness diagrams, proper scores", arch=NR, validation=NR, metrics="CRPS and others",
        findings="Distinguishes probabilistic, exceedance and marginal calibration", lim_auth=NR, lim_crit=NR,
        relevance="Very high: calibration diagnostics for RQ on probabilistic forecasts", adapt="PIT, coverage, sharpness"),
    "10.1016/j.ijforecast.2016.02.001": dict(
        domain="Probabilistic energy forecasting", objective="Report GEFCom2014", rq=NR, geo=NR, data="Load, price, wind, solar tracks", period=NR,
        freq=NR, n=NR, target="Energy quantities", features=NR, methods="Many; quantile-based", arch=NR, validation="Competition", metrics="Pinball loss",
        findings=NR, lim_auth=NR, lim_crit="Abstract not available at screening; extraction pending",
        relevance="High: shows probabilistic forecasting is mature in electricity, absent in fuel imports", adapt="Pinball-loss evaluation"),
    "10.1109/tnnls.2022.3217694": dict(
        domain="Probabilistic forecasting (conformal)", objective="Distribution-free PIs for non-stationary series", rq=NR, geo="Not applicable",
        data="Series with varying heteroscedasticity", period=NR, freq=NR, n=NR, target="Generic", features=NR,
        methods="EnCQR: bootstrap ensemble + conformalised quantile regression", arch="Wrapper over any model", validation=NR, metrics=NR,
        findings="Outperforms models that only do quantile regression (per abstract)", lim_auth=NR, lim_crit=NR,
        relevance="High: calibration method usable on top of LightGBM or GRU", adapt="EnCQR/CQR for coverage guarantees"),
    "10.1016/j.ijforecast.2021.10.009": dict(
        domain="Forecasting competition (uncertainty)", objective="Report M5 Uncertainty", rq=NR, geo="US (Walmart)", data="42,840 series",
        period=NR, freq="Daily", n="42,840 series", target="Unit sales quantiles", features=NR, methods="Many", arch=NR, validation="Holdout",
        metrics="Scaled pinball loss over nine quantiles", findings="Results and top methods summarised", lim_auth=NR, lim_crit="Retail",
        relevance="High: quantile evaluation design", adapt="Nine-quantile pinball evaluation"),
    "10.3390/math11122625": dict(
        domain="Multi-country macro forecasting", objective="Joint GDP forecasting for 25 OECD countries with TFT", rq=NR, geo="25 OECD countries",
        data=NR, period=NR, freq="Quarterly (per screening)", n="25 countries", target="GDP growth", features="Explanatory macro variables",
        methods="TFT vs regression models", arch="TFT", validation=NR, metrics=NR,
        findings="TFT outperforms regressions, especially during COVID-19 turbulence", lim_auth=NR,
        lim_crit="Few series; risk of overfitting not discussed in abstract", relevance="High: cross-country global DL on a small macro panel",
        adapt="Shock-period stratification"),
    "10.1198/016214506000001437": dict(
        domain="Probabilistic forecast evaluation", objective="Theory of proper scoring rules", rq=NR, geo="Not applicable", data="Not applicable",
        period="Not applicable", freq=NR, n=NR, target="Not applicable", features=NR, methods="Proper scoring rules (CRPS, interval score etc.)",
        arch=NR, validation=NR, metrics=NR, findings="Proper rules encourage honest forecasts; strictly proper rules as losses", lim_auth=NR,
        lim_crit=NR, relevance="Very high: CRPS and interval score", adapt="CRPS, interval score"),
    "10.48550/arxiv.1905.03222": dict(
        domain="Conformal prediction", objective="Combine conformal prediction with quantile regression", rq=NR, geo="Not applicable",
        data="Regression benchmarks", period="Not applicable", freq=NR, n=NR, target="Generic", features=NR, methods="CQR", arch=NR,
        validation=NR, metrics="Coverage, interval length", findings="Valid coverage with shorter adaptive intervals", lim_auth=NR,
        lim_crit="Exchangeability assumption violated by time series", relevance="High: calibration layer", adapt="CQR with time-series adaptations"),
    "10.48550/arxiv.2101.02118": dict(
        domain="Deep learning vs boosting", objective="Compare DL models with a window-based GBRT", rq=NR, geo="Not applicable",
        data="Standard DL benchmark datasets", period="Not applicable", freq=NR, n=NR, target="Generic", features="Windowed lags and covariates",
        methods="GBRT vs DL models", arch=NR, validation=NR, metrics=NR, findings="Well-configured GBRT competes with or beats many DL models (per abstract framing)",
        lim_auth=NR, lim_crit="Preprint", relevance="High: GBRT as strong baseline", adapt="Window-based GBM"),
    "10.48550/arxiv.2207.08815": dict(
        domain="Deep learning vs trees (tabular)", objective="Benchmark DL vs tree models on tabular data", rq=NR, geo="Not applicable",
        data="45 tabular datasets", period="Not applicable", freq="Not applicable", n="~10K samples per dataset", target="Generic",
        features=NR, methods="XGBoost, RF vs DL", arch=NR, validation="Benchmark with tuning budgets", metrics=NR,
        findings="Trees remain state of the art on medium-sized data", lim_auth=NR, lim_crit="Tabular, not time series",
        relevance="Medium-high: inductive-bias argument for small data", adapt="Expectation setting for H2"),
    "10.34989/swp-2011-16": dict(
        domain="Real-time oil forecasting", objective="Real-time forecasts of the real oil price", rq=NR, geo="Global oil market",
        data="Monthly real-time vintages", period="1991.1-2010.12", freq="Monthly", n=NR, target="Real price of oil",
        features="Global oil market variables, futures", methods="VAR, AR, ARMA, futures-based, no-change", arch=NR,
        validation="Real-time recursive", metrics="MSPE", findings="Real-time VAR forecasts beat no-change up to one year; MSPE reductions up to 25%",
        lim_auth=NR, lim_crit="Price not volume", relevance="Very high: real-time vintage construction in oil; backcasting/nowcasting to fill gaps",
        adapt="Backcast/nowcast of missing recent months"),
}
