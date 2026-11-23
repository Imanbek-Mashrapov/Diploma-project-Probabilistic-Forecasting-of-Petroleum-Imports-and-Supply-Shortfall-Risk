"""Stage 6b: research-gap assessment (reviewer's synthesis), written as data so the CSV and the report agree.

Each gap cites DOIs of the strongest related work found. Scores are the reviewer's judgement on a 1-5 scale
(5 = strongest) and are explained in the 'rationale' fields; they are not computed from citation counts.
'search_evidence' summarises the Boolean checks (gapcheck_local.py and the first OpenAlex gap-check run).
"""

GAPS = [
    dict(
        id="A", name="Global cross-country learning for monthly physical petroleum-import forecasting in landlocked economies",
        strongest=["10.1016/j.ijforecast.2021.03.004", "10.1016/j.patcog.2021.108441", "10.1016/j.ijforecast.2020.11.009",
                   "10.1016/s0304-4076(96)01802-7", "10.3390/su151813592", "10.3390/forecast8050089", "10.3390/math11122625"],
        achieved="Theory and benchmarks show global models are not more restrictive than local ones and often win on related series "
                 "[[p:10.1016/j.ijforecast.2021.03.004|10.1016/j.patcog.2021.108441]]. Pooling across countries for fuel demand has a long history in econometrics "
                 "([[n:10.1016/s0304-4076(96)01802-7]] compare pooled and heterogeneous estimators for dynamic gasoline demand; abstract not available, findings not extracted). "
                 "Recent work pools short cross-country panels: a TFT for 25 OECD GDPs [[p:10.3390/math11122625]] and partial pooling on short annual panels, "
                 "whose gain reverses under strong heterogeneity [[p:10.3390/forecast8050089]].",
        remaining="Every petroleum-import forecasting study found is single-country (Indonesia, Taiwan, Thailand, China, India, Tanzania, Nepal) "
                  "and almost all use values, annual data or demand rather than monthly physical import volumes. No study pools landlocked importers.",
        search_evidence="First OpenAlex Boolean run: 'landlocked AND (oil OR petroleum OR fuel) AND forecast*' returned 12 records in total, none on target; "
                        "'fuel/petroleum AND import* AND forecast* AND (panel OR cross-country OR global model)' returned 30, none forecasting physical imports across countries. "
                        "Local Boolean check on the 5,230-record pool plus Crossref top 200: 11 and 41 matches, none on target.",
        novelty="Application-level novelty, not methodological: pooling is established; the new element is the target (monthly physical refined-product imports) and the landlocked panel.",
        feasibility="Feasible: 44 series in 22 countries (5,549 observations); Tier-1 evaluation set of 22 series. Weak co-movement (median year-on-year correlation near zero) limits the expected pooling gain.",
        experiment="Local (ETS/SARIMA, per-series LightGBM) vs global (pooled LightGBM, small GRU/N-BEATS) vs partially pooled (validation-shrunk) models; "
                   "rolling origin; MASE and pinball loss; leave-one-country-out transfer; HLN-corrected DM tests with Holm adjustment.",
        scores=dict(novelty=3, practical=4, evidence=4, data=4, experiment=5, publication=3),
        rationale="Well-defined and testable; the result may be null because of heterogeneity, which is still publishable if reported honestly.",
    ),
    dict(
        id="B", name="Deep learning versus gradient boosting under comparable data, horizons and evaluation",
        strongest=["10.1016/j.ijforecast.2021.10.004", "10.1016/j.ijforecast.2021.11.013", "10.1080/01605682.2022.2118629",
                   "10.48550/arxiv.2101.02118", "10.48550/arxiv.2207.08815", "10.3390/en18071685", "10.5281/zenodo.18467170", "10.1002/for.70165"],
        achieved="Extensively compared in general forecasting: tree-based global models dominated M5 [[p:10.1016/j.ijforecast.2021.10.004]]; DL combinations win on some M3 subsets at high cost [[p:10.1080/01605682.2022.2118629]]; "
                 "window-based GBRT matches many DL models [[p:10.48550/arxiv.2101.02118]]; trees beat DL on medium tabular data [[p:10.48550/arxiv.2207.08815]]. "
                 "In energy and trade, boosting usually wins on small data: XGBoost over LSTM for Thai transport energy [[p:10.3390/en18071685]] and CatBoost best for bilateral trade [[p:10.5281/zenodo.18467170]].",
        remaining="No controlled comparison on monthly physical fuel imports with identical information sets, horizons, rolling origins and probabilistic scores.",
        search_evidence="First OpenAlex run: 36 records for (boosting AND deep learning AND trade/import AND forecast) and 49 for (boosting AND deep learning AND oil/fuel AND demand AND forecast); "
                        "local check: 108 matches, dominated by electricity, price and building-energy studies.",
        novelty="Incremental. The direction of the result is predictable from prior evidence (boosting is likely to win); the value lies in shock-period stratification and calibration.",
        feasibility="Feasible with small models (16-64 hidden units). Neural models are expected to be data-limited.",
        experiment="Same features and windows for LightGBM (quantile objective) and GRU/TCN/N-BEATS; stratify errors by normal vs shock windows; report compute cost.",
        scores=dict(novelty=2, practical=3, evidence=5, data=4, experiment=5, publication=2),
        rationale="Necessary benchmark inside the thesis but weak as a headline claim.",
    ),
    dict(
        id="C", name="Calibrated probabilistic forecasting of petroleum imports",
        strongest=["10.1111/j.1467-9868.2007.00587.x", "10.1198/016214506000001437", "10.1016/j.ijforecast.2016.02.001",
                   "10.1016/j.ijforecast.2021.10.009", "10.1109/tnnls.2022.3217694", "10.48550/arxiv.1905.03222", "10.2139/ssrn.6893382"],
        achieved="Probabilistic forecasting and calibration theory are mature [[p:10.1111/j.1467-9868.2007.00587.x|10.1198/016214506000001437]]; electricity and retail have standard quantile benchmarks [[p:10.1016/j.ijforecast.2016.02.001|10.1016/j.ijforecast.2021.10.009]]; "
                 "conformal wrappers give distribution-free intervals [[p:10.48550/arxiv.1905.03222|10.1109/tnnls.2022.3217694]]. A 2026 preprint applies quantile regression to aviation-fuel demand for inventory planning [[p:10.2139/ssrn.6893382]].",
        remaining="Every petroleum-import and national fuel-demand forecasting study found reports point forecasts only (MAPE, RMSE, 'accuracy'). Interval coverage and calibration under shocks are not evaluated.",
        search_evidence="Local Boolean check (probabilistic terms AND fuel AND import/demand AND forecast): 15 matches; on-target only the aviation-fuel quantile preprint and ship-fuel interval prediction (engineering), none for national imports.",
        novelty="Genuine domain gap; methods are existing. Defensible as 'first calibrated probabilistic benchmark' for this target, not as a new method.",
        feasibility="Feasible: quantile LightGBM, conformalised intervals, likelihood-based GRU. Short test windows make coverage estimates noisy, so report confidence bands on coverage.",
        experiment="Compare pinball loss/CRPS, 80% and 95% coverage and interval width across models; PIT histograms; conformal recalibration; stratify by shock windows.",
        scores=dict(novelty=4, practical=4, evidence=4, data=4, experiment=4, publication=4),
        rationale="Strong combination of clear gap, direct policy use (risk bands), and standard evaluation tools.",
    ),
    dict(
        id="D", name="Publication-delay-aware (as-of) evaluation of trade-based fuel forecasts",
        strongest=["10.1016/s0164-0704(02)00062-9", "10.34989/swp-2011-16", "10.1002/for.70165", "10.48550/arxiv.2608.09033",
                   "10.21203/rs.3.rs-9995316/v1", "10.71889/5fylantbak.29865743", "10.2139/ssrn.1494582"],
        achieved="Real-time data are a mature topic in macroeconomics [[p:10.1016/s0164-0704(02)00062-9|10.1016/s1574-0706(05)01017-7]] and oil-price forecasting, with monthly real-time vintages for 1991-2010 [[p:10.34989/swp-2011-16]]. "
                 "World-trade nowcasting is evaluated on real-time datasets [[p:10.1002/for.70165]], and ML gains in inflation forecasting have been re-tested on vintages [[p:10.48550/arxiv.2608.09033]]. "
                 "A 2026 preprint masks inputs by release calendar for oil-export nowcasting in Norway and Thailand [[p:10.21203/rs.3.rs-9995316/v1]].",
        remaining="No study found forecasts commodity-level imports from UN Comtrade while respecting reporter-specific release dates, which range from about 2 to more than 6 months in the project's panel. "
                  "Comtrade does not publish full vintage histories, so revisions can only be measured from repeated snapshots.",
        search_evidence="Local Boolean check (real-time/vintage/publication-lag terms AND trade/oil AND forecast/nowcast): 20 matches; on-target only the macro, oil-price, world-trade and oil-export works listed.",
        novelty="Moderately novel in this domain: established concept, new application to reporter-specific trade-data release lags. Strong methodological hygiene contribution.",
        feasibility="Partly feasible: release dates exist (availability endpoint, first-seen dates); true vintages do not, so the design is 'as-of availability' plus snapshot-based revision checks, not full real-time replication.",
        experiment="Train/evaluate twice: (i) using latest data with oracle availability, (ii) as-of release dates; report the accuracy gap by horizon; repeat for 2025-2026 first-release vs later snapshots.",
        scores=dict(novelty=4, practical=5, evidence=4, data=3, experiment=4, publication=4),
        rationale="Directly affects whether a warning would have been available in time; data limits must be stated.",
    ),
    dict(
        id="E", name="Incremental forecasting value of supplier concentration, oil prices and geopolitical risk",
        strongest=["10.1257/aer.20191823", "10.1016/j.esr.2025.101695", "10.1016/j.eneco.2025.108595", "10.1016/j.energy.2025.137996",
                   "10.3389/fmars.2026.1956773", "10.1016/j.enpol.2011.06.034", "10.1016/j.eneco.2025.108594"],
        achieved="GPR is a standard index [[p:10.1257/aer.20191823]] and has explanatory links with energy imports and the survival of energy-import relationships [[p:10.1016/j.energy.2025.137996|10.1016/j.eneco.2025.108595]]. "
                 "GPR's contribution to crude-oil volatility forecasts has been tested [[p:10.1016/j.eneco.2025.108594]]. [[n:10.3389/fmars.2026.1956773]] show, out of sample, that dynamic trade-flow indicators outperform origin concentration for disruption warnings in Korea.",
        remaining="Out-of-sample incremental value of HHI, prices and GPR for fuel-import volume forecasts is untested; most GPR-import studies are explanatory (VAR, survival) rather than predictive. "
                  "Global GPR barely varies across small landlocked importers, and Kyrgyz shocks (Russian export bans) are not GPR events.",
        search_evidence="Local Boolean check (GPR/HHI/concentration AND import AND forecast/predict): 29 matches, of which on target are price-volatility forecasting with GPR and Kwon & Jeong's concentration benchmark.",
        novelty="Incremental; partially addressed by Kwon & Jeong for product-level imports in a maritime economy. A null result is plausible.",
        feasibility="Feasible as an ablation. Requires publication-lagged features to avoid leakage; supplier shares come from the same lagged Comtrade data.",
        experiment="Feature-group ablation (own history; + supplier HHI and shares; + Brent; + GPR; + event dummies) with pinball-loss differences and DM tests per group.",
        scores=dict(novelty=3, practical=3, evidence=3, data=4, experiment=5, publication=3),
        rationale="Cheap to test and informative even if null; should not be the headline.",
    ),
    dict(
        id="F", name="From probabilistic import forecasts to early warning of supply stress",
        strongest=["10.3389/fmars.2026.1956773", "10.3390/su16062284", "10.1109/icrera66237.2025.11283745", "10.3390/su10010283",
                   "10.2139/ssrn.4041666", "10.48550/arxiv.2407.16739", "10.1049/itr2.12083"],
        achieved="[[n:10.3389/fmars.2026.1956773]] already define disruption onsets as a persistent quantity shortfall with rising unit values and evaluate warnings out of sample against concentration screening. "
                 "Energy-crisis warnings exist at world level [[p:10.3390/su16062284]] and as index systems [[p:10.3390/su10010283]]; renewable-shortfall alarms use boosted forecasts plus a probabilistic classifier with PR-AUC and Brier scores [[p:10.1109/icrera66237.2025.11283745]].",
        remaining="No study turns calibrated, lag-aware forecasts of refined-fuel imports into warnings for landlocked importers, or checks warnings against documented fuel-supply events. "
                  "Import shortfalls are proxies; actual retail shortages are rarely observed (one exception: crowdsourced station data in hurricane studies [[p:10.1049/itr2.12083]]).",
        search_evidence="Local Boolean check (early warning/alarm AND fuel/oil/energy/import AND supply/shortage/disruption/security): 21 matches; closest are those listed.",
        novelty="Not novel as a concept; an extension of Kwon & Jeong to refined fuels, landlocked importers and probabilistic forecasts. Must cite that work as the nearest prior study.",
        feasibility="Weakest part: few documented events (2023-2026 Russian restrictions; mid-2026 Kyrgyz shortage), proxy labels, and recent data that are provisional.",
        experiment="Define stress as P(import < q-threshold of expected level) using the predictive distribution; compare PR-AUC, recall at a fixed alert budget and lead time with HHI ranking and a quantity-only rule; validate against a sourced event list.",
        scores=dict(novelty=3, practical=5, evidence=3, data=2, experiment=3, publication=4),
        rationale="High practical value; claims must be framed as import-supply stress, not domestic shortage.",
    ),
    dict(
        id="G", name="Landlocked economies as a distinct group in energy-import research",
        strongest=["10.1111/twec.13416", "10.3390/en15217822", "measuringthesecurityofexternalenergysupp", "10.3126/jsdpj.v1i1.52602",
                   "10.2139/ssrn.4368618", "10.22190/fueo201005025v"],
        achieved="Landlocked-country research centres on trade costs, transit and connectivity [[p:10.30875/9789287053305-003.zhtml|10.1111/twec.13416]]. Central Asian energy security is studied descriptively or with indices [[p:measuringthesecurityofexternalenergysupp|10.3390/en15217822]]. "
                 "Kyrgyz trade has been reshaped by post-2022 rerouting [[p:10.2139/ssrn.4368618]].",
        remaining="No quantitative forecasting study treats landlocked fuel importers as a group; their fuel imports appear only inside global datasets or single-country studies.",
        search_evidence="Local Boolean check (landlocked AND energy/fuel AND import/security/dependence): 20 matches, none forecasting fuel imports.",
        novelty="Under-explored but mainly a sampling frame; it becomes a scientific contribution only if landlocked-specific mechanisms (corridor dependence, single dominant supplier, transit delays) are shown to matter.",
        feasibility="Feasible, but the panel is heterogeneous (exporters, microstates, transit hubs); Tier-1 restriction reduces it to 13 countries.",
        experiment="Compare pooling within the landlocked panel against pooling with a non-landlocked control group of small importers; test whether supplier concentration interacts with landlocked status.",
        scores=dict(novelty=3, practical=4, evidence=3, data=3, experiment=3, publication=3),
        rationale="Useful framing and policy relevance; needs a control group to become a finding.",
    ),
    dict(
        id="H", name="Additional: data-quality-aware forecasting with UN Comtrade (mirror data, revisions, statistical imbalance)",
        strongest=["10.3390/su14031431", "10.1111/ecpo.70046", "10.71889/5fylantbak.29865743", "10.2139/ssrn.4368618"],
        achieved="Statistical imbalance in Comtrade records is widespread, including fossil fuels [[p:10.3390/su14031431]]; mirror discrepancies surged after 2019 and are affected by sanctions [[p:10.1111/ecpo.70046]]; UN energy statistics are revised [[p:10.71889/5fylantbak.29865743]].",
        remaining="Forecasting studies rarely report how trade-data quality (reporter vs mirror, provisional vs revised) affects accuracy or alert reliability.",
        search_evidence="Found through the main search and local checks; no forecasting study measuring this effect was found.",
        novelty="Moderately novel, practically important, low cost given the project's audit pipeline.",
        feasibility="Feasible: the project already has heading-vs-lines, partner-vs-World and mirror checks.",
        experiment="Robustness: re-run evaluation with mirror-based targets and with revision-affected months excluded; report sensitivity of rankings and alerts.",
        scores=dict(novelty=3, practical=4, evidence=3, data=4, experiment=4, publication=3),
        rationale="Strengthens credibility of all other results; good secondary contribution.",
    ),
]

CONTRIBUTIONS = [
    ("1. International monthly petroleum-import dataset for landlocked economies", "Incremental contribution",
     "Valuable resource and prerequisite, but derived from public Comtrade data; value depends on documented audit rules, tiers and reproducible code. Redistribution of Comtrade-derived files must respect UN Comtrade terms."),
    ("2. Comparison of local and global forecasting approaches", "Application of existing methods",
     "Theory and benchmarks exist [[p:10.1016/j.ijforecast.2021.03.004|10.1016/j.patcog.2021.108441|10.1016/j.ijforecast.2020.11.009]]; pooled-vs-heterogeneous estimators for gasoline demand date back to [[n:10.1016/s0304-4076(96)01802-7]]. New only as evidence for this target and panel; a null result is plausible given weak co-movement."),
    ("3. Direct comparison of gradient boosting and global deep learning", "Application of existing methods",
     "Well studied [[p:10.1016/j.ijforecast.2021.11.013|10.1080/01605682.2022.2118629|10.48550/arxiv.2101.02118|10.48550/arxiv.2207.08815]]. Keep as a controlled benchmark; do not make it the headline."),
    ("4. Probabilistic forecasts with uncertainty quantification and calibration", "Strong potential scientific contribution",
     "No national fuel-import or fuel-demand study found reports calibrated intervals; tools are mature. Strongest when combined with contribution 5."),
    ("5. Historical backtesting that respects publication delays", "Strong potential scientific contribution",
     "Established in macro and oil-price forecasting, absent for Comtrade-based commodity imports. Limited by missing vintages: frame as as-of availability plus snapshot revisions."),
    ("6. Integration of supplier concentration, petroleum prices and geopolitical risk", "Incremental contribution",
     "Explanatory links exist; predictive value untested here. [[n:10.3389/fmars.2026.1956773]] find that concentration adds little out of sample. Run as ablation; expect small or null gains."),
    ("7. Forecast-based early warning of import-supply stress", "Incremental contribution",
     "Concept and event definition already used by [[n:10.3389/fmars.2026.1956773]]. Extension to refined fuels and landlocked importers is new, but few events make it 'insufficiently supported' as a primary claim unless the event list is strengthened."),
    ("8. Empirical case study of Kyrgyzstan", "Application of existing methods",
     "High practical significance (2025-2026 supply stress), data validated against the national energy balance. Scientific value rests on the methods applied, not the location."),
]
