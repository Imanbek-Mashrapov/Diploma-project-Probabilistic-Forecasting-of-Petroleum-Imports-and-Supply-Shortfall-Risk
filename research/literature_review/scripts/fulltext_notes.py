"""Full-text pass (2026-11-07): evidence locations and field overrides for papers read in full.
PDF page numbers refer to the files in papers/ (for arXiv copies, the preprint pagination); MDPI articles were read
as HTML in the browser pane and are cited by section. Overrides replace the abstract-based extraction fields.
"""
FT = {
    "10.3389/fmars.2026.1956773": dict(
        evidence="p1 abstract (440 events, walk-forward with confirmation-lag embargo, top-5% precision ~1.7x base rate, 31% event capture, median lead 9 months, concentration below base rate); "
                 "p3 sec 2.1-2.2 (Korea Customs Service HS10 monthly value and net weight; event = persistent quantity shortfall + rising unit value; four hypotheses); "
                 "p5 (embargo h+m-1 months so labels are certifiable in real time; 9 annual folds 2015-2023); p11 sec 4.2-4.5 (concentration describes exposure, not short-horizon risk; ~4% precision at 2% base rate; GPR, port and freight data named as next predictors; limitations: top-20 partners fixed ex post, rerouting can mask or mimic events)",
        methods="Gradient boosted ensembles and logistic benchmark vs concentration rankings", validation="Walk-forward by calendar year with confirmation-lag embargo",
        metrics="Watchlist precision at budget, event capture, first-alert lead; paired annual comparisons and moving-block bootstrap",
        findings="ML rankings reach ~1.7x base-rate precision in the top 5% and capture 31% of onsets with 9-month median lead; concentration ranking performs below base rate; no monotonic gradient of events across concentration quintiles",
        lim_auth="Partner universe fixed ex post; rerouting can hide or create events; price condition filters substitution imperfectly; maritime economy only",
        lim_crit="Does not model statistical publication lags (Korean customs data are timely); no probabilistic volume forecasts; product-level, not fuel-specific"),
    "10.21203/rs.3.rs-9995316/v1": dict(
        evidence="p2-3 abstract (benchmarks: seasonal naive, SARIMA, SARIMAX, VAR/VECM, MIDAS, ARDL-MIDAS, DFM; RMSE -15.6% Norway, -8.1% Thailand vs strongest benchmark, paired loss tests); "
                 "p7 sec 3 (information set: a datum enters only if visible by the nowcast date under its release calendar); p15 (rolling results use the point branch; interval estimation left for deployment); "
                 "p21-24 (end-of-month nowcast, not full intramonth vintages; shorter histories for freight/news/destination blocks)",
        period="Not extracted", metrics="MAE, RMSE, MAPE, log-RMSE; paired loss comparisons",
        findings="Best accuracy in both countries; RMSE reduced 15.6% (Norway) and 8.1% (Thailand) vs strongest benchmark",
        lim_auth="End-of-month rather than intramonth vintages; uneven block histories", lim_crit="Preprint; export values for two exporters; no interval evaluation; heavy architecture"),
    "10.1016/j.patcog.2021.108441": dict(
        evidence="arXiv copy p30 (global models roughly equivalent whether data are in one long or many short homogeneous series; local AR degrades with short series); p31 sec 7 (LightGBM and RNN best in many scenarios; LightGBM much faster; global models need the right amount of complexity)",
        findings="Global models handle many short series well; LightGBM matches RNNs at far lower cost; performance depends on matching model complexity to data"),
    "10.48550/arxiv.2608.09033": dict(
        evidence="p1 abstract; p2 (ALFRED vintages reconstruct what a real-time forecaster saw); p19 (out-of-sample SHAP); p22 sec 6-7 (ML edge, essentially Gradient Boosting at 6-12 months, survives real-time data; feature-importance identity shifts)",
        findings="ML advantage, confined to gradient boosting at 6- and 12-month horizons, survives real-time data; the predictors driving forecasts change between revised and real-time data"),
    "10.3390/forecast8050089": dict(
        evidence="HTML abstract and sec 7 Conclusions (three Eurostat panels, rolling origin, country-clustered tests, model confidence sets; best sharing regime cuts MASE by 15.3%-27.8%; simulation shows the gain reverses once cross-country heterogeneity is appreciable)",
        data="Three Eurostat panels (educational attainment, municipal waste routes)", freq="Annual", validation="Expanding-window rolling origin; walk-forward tuning of shrinkage",
        metrics="MASE; country-clustered equal-predictive-ability tests; model confidence sets",
        findings="Parameter sharing (pooling or validation-selected shrinkage) reduces MASE by 15.3-27.8% vs country-specific estimation; gain reverses with appreciable heterogeneity",
        lim_auth="Short annual panels from one statistical producer; not compared with large-scale cross-learning"),
    "10.3390/su16062284": dict(
        evidence="HTML sec 3.2 (crisis = energy market pressure index above mean + 2 SD), sec 3.4 (indicators dropped for lack of monthly data, incl. world energy import-export data), sec 4.2-4.3 (goodness of fit and prediction accuracy reported; no out-of-sample design found in the text)",
        target="Crisis month: energy market pressure index > mean + 2 SD", validation="In-sample fit and classification accuracy (no out-of-sample test found)",
        lim_auth="Several indicators unavailable monthly", lim_crit="In-sample '99%' claim is not evidence of early-warning skill"),
    "10.3390/su151813592": dict(
        evidence="HTML abstract and methods (SVR described; 30 countries 2000-2020; sanctions and COVID-19 as exogenous factors)",
        methods="Statistical models and AI models incl. SVR", findings="SVR has the lowest error and highest stability for both importers and exporters; sanctions and COVID-19 reduce demand most; trade liberalisation increases it"),
    "10.32479/ijeep.15572": dict(
        evidence="p5 (train/test split), p7 (NNAR lowest RMSE; 12-month point forecasts, Table 3-4)", validation="Train/test split", metrics="RMSE and others (Table 3)",
        findings="Neural network autoregression (NNAR) gives lowest RMSE; 12-month point forecasts"),
    "10.21203/rs.3.rs-2257631/v1": dict(evidence="p3, p5 (MAPE as the only accuracy measure; PPAC monthly data)", metrics="MAPE only"),
    "10.48550/arxiv.2402.01648": dict(evidence="p2, p7 (annual data 1970-2019 converted to 200 'seasonal' points; 75/25 split; '99% accuracy')",
                                      lim_crit="Interpolated annual data and a single split; no baselines; accuracy claim not credible"),
    "10.1088/1742-6596/1255/1/012016": dict(evidence="p4-5 (customs data 1996-2016; testing on 2004-2015 with 2016 target; Table 4: 12-5-1 best, 83% 'accuracy', test MSE 0.028)",
                                             period="1996-2016", validation="Single train/test split", findings="12-5-1 MLP selected; 83% 'accuracy'"),
    "10.30598/barekengvol17iss4pp2047-2058": dict(evidence="p1 abstract (test on Jan-Apr 2023; best SARIMA(2,1,0)(0,1,1); MAPE 13.90%), p4 (procedure)",
                                                  validation="Holdout of 4 months", metrics="MAPE 13.90%"),
    "10.32479/ijeep.23912": dict(evidence="p2, p4, p7 (Chad, annual 2011-2019 train, 2020-2023 out-of-sample; time-series CV with sliding windows)"),
}
