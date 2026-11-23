"""Methodology coding of forecasting and early-warning studies for analysis/methodology_comparison.csv.
Codes come from the extraction (abstract or full text). 'NR' = not reported in the source read; it is not
counted as 'No' in summaries. Columns: target_type, frequency, scope (single/multi-country), models,
global (pooled across series), probabilistic, validation, real_time (publication-lag aware), naive_baseline,
significance_test, metrics.
"""
NR = "NR"
COLS = ["target_type", "frequency", "scope", "models", "global", "probabilistic", "validation", "real_time",
        "naive_baseline", "significance_test", "metrics"]

CODES = {
    "10.1088/1742-6596/1255/1/012016": ("Physical volume (crude, products, gas)", "Annual", "Single", "ANN", "No", "No", "Single holdout", "No", "No", "No", "Accuracy %, MSE"),
    "10.34148/teknika.v13i2.861": ("Import value", "Monthly", "Single", "GRU", "No", "No", NR, "No", NR, NR, "MAPE"),
    "10.30598/barekengvol17iss4pp2047-2058": ("Import value", "Monthly", "Single", "SARIMA", "No", "No", "Single holdout (4 months)", "No", "No", "No", "MAPE"),
    "10.1155/2014/257947": ("Import demand (crude)", NR, "Single", "MLR, SVR, ANN, ELM, hybrids", "No", "No", NR, "No", NR, NR, "MAPE, RMSE, MAD"),
    "10.1007/978-981-97-8031-0_81": ("Production and imports (crude, POL)", "Annual", "Single", "ARIMA", "No", "No", NR, "No", NR, NR, NR),
    "10.1007/s10553-026-02011-4": ("Oil import demand", "Annual", "Single", "Grey relational + ML", "No", "No", NR, "No", NR, NR, NR),
    "10.1007/978-3-032-09945-7_39": ("Crude import demand", NR, "Single", "Multiple regression, elasticities", "No", "No", "In-sample", "No", NR, NR, "Elasticities"),
    "10.1016/j.energy.2018.08.127": ("Import dependence ratio", "Annual", "Single", "NMGM-ARIMA (grey + ARIMA)", "No", "No", NR, "No", NR, NR, "MAE"),
    "10.1016/j.jclepro.2019.05.314": ("Import dependence ratio", "Annual", "Single", "Grey-type hybrid (per title)", "No", "No", NR, "No", NR, NR, NR),
    "10.1016/j.knosys.2022.108687": ("Import dependence ratio", NR, "Single", "Fuzzy time series + multi-objective optimisation", "No", NR, NR, "No", NR, NR, NR),
    "10.1007/s11135-025-02268-7": ("Product import demand", "Annual", "Single", "ARDL, ECM, structural breaks", "No", "No", "In-sample", "No", NR, NR, "Elasticities"),
    "10.3126/jsdpj.v1i1.52602": ("Product imports", NR, "Single", "Linear trend", "No", "No", "None", "No", "No", "No", NR),
    "10.3390/su151813592": ("Oil demand", "Annual", "Multi (30)", "ML", "Yes (panel)", "No", NR, "No", NR, NR, NR),
    "10.32479/ijeep.15572": ("Diesel demand", "Monthly", "Single", "MLP, ELM, NNAR vs ARIMA-type", "No", "No", "Single holdout", "No", NR, "No", "RMSE and others"),
    "10.21203/rs.3.rs-2257631/v1": ("Gasoline and diesel consumption", NR, "Single", "SARIMA, NN", "No", "No", NR, "No", NR, NR, "MAPE"),
    "10.48550/arxiv.2402.01648": ("Total imports (value)", "Annual interpolated", "Multi", "LSTM", NR, "No", "75/25 split", "No", "No", "No", "Accuracy %"),
    "10.5281/zenodo.18467170": ("Bilateral trade value", "Annual", "Global dyads", "Ridge, RF, CatBoost", "Yes", "No", "Temporal split (train/val/test)", "Partly (pre-forecast information only)", NR, NR, "RMSE"),
    "10.1002/for.70165": ("World trade", "Monthly", "World aggregate", "RF, GB, macro RF, linear GB, OLS, MS, QR, DFM, EN", "n/a", "No", "Real-time datasets, multiple horizons", "Yes", "Yes (benchmarks)", "Yes", NR),
    "10.1007/s41060-025-00781-4": ("Raw-material trade flows", NR, "Multi", "TFT vs RF, GAT", "Yes", "Partly (TFT quantiles)", NR, "No", "No", NR, "R2"),
    "10.1080/01605682.2026.2757161": ("Bilateral trade value/volume", NR, "Multi", "Network model vs ML", "Yes", "No", NR, "No", NR, NR, "Accuracy %"),
    "10.29105/trendinomics.v2i2.19": ("Trade flows", "Monthly", "Multi", "PCA/LASSO + LSTM", "Yes", "No", "Multiple horizons", "No", "No", "Yes (panel DM)", NR),
    "10.21203/rs.3.rs-9995316/v1": ("Oil export value", "Monthly", "Multi (2)", "Patch-based DL fusion network vs SARIMA(X), VAR/VECM, MIDAS, DFM", "Partly (country gates)", "No (point branch)", "Rolling end-of-month", "Yes (release-calendar masking)", "Yes (seasonal naive)", "Yes (paired loss)", "MAE, RMSE, MAPE, log-RMSE"),
    "10.3389/fmars.2026.1956773": ("Disruption onset (quantity shortfall + unit value)", "Monthly", "Single country (5,925 products)", "GBM ensembles, logistic vs concentration", "Yes (product panel)", "Partly (risk scores)", "Walk-forward with label embargo", "Partly (label confirmation lag)", "Yes (concentration, base rate)", "Yes (paired, block bootstrap)", "Watchlist precision, capture, lead time"),
    "10.3390/su16062284": ("Energy-crisis month", "Monthly", "World", "Logit", "n/a", "Yes (probability)", "In-sample only", "No", "No", "No", "Fit, classification accuracy"),
    "10.1109/icrera66237.2025.11283745": ("Renewable shortfall event", "Hourly", "Multi (5)", "GBM + probabilistic classifier", "No (country-specific)", "Yes", "Blocked CV", "No", NR, NR, "MAE, RMSE, MAPE, PR-AUC, Brier"),
    "10.3390/en18071685": ("Transport energy consumption", "Annual", "Single", "LSTM, XGBoost", "No", "No", "Train/test split", "No", "No", "No", "R2 and others"),
    "10.3390/en11071687": ("Composite supply-security score", "Annual", "Single", "ARIMA-XGBoost", "No", "No", NR, "No", NR, NR, NR),
    "10.3390/math11122625": ("GDP growth", "Quarterly", "Multi (25)", "TFT vs regressions", "Yes", "Yes (quantiles)", NR, "No", NR, NR, NR),
    "10.48550/arxiv.2608.09033": ("Inflation", "Monthly", "Single", "RW, AR, Phillips, ADL vs RF, GB, EN, SVR", "No", "No", "Recursive, vintage-consistent", "Yes", "Yes", NR, NR),
    "10.34989/swp-2011-16": ("Real oil price", "Monthly", "World", "VAR, AR, ARMA, futures, no-change", "n/a", "No", "Recursive real-time", "Yes", "Yes (no-change)", NR, "MSPE"),
    "10.1016/s0304-4076(96)01802-7": ("Gasoline demand", NR, "Multi", "Pooled vs heterogeneous estimators", "Yes (pooled)", NR, NR, NR, NR, NR, NR),
    "10.1016/j.energy.2021.122312": ("Gasoline demand", NR, "Single", "ML regression", "No", NR, NR, "No", NR, NR, NR),
    "10.32479/ijeep.23912": ("Petroleum product demand", "Annual", "Single (Chad, landlocked)", "Grey-ANN hybrid", "No", "No", "Holdout 2020-2023 + sliding-window CV", "No", NR, NR, NR),
    "10.3390/forecast8050089": ("Compositional shares", "Annual", "Multi (Eurostat panels)", "Replicator, Dirichlet, log-ratio, pooled ML", "Compared (local, pooled, shrunk)", "No", "Expanding-window rolling origin", "No", "Yes (random walk, no-change)", "Yes (clustered tests, MCS)", "MASE"),
}
