> **AI-ASSISTED DRAFT. The student must rewrite this text in their own words.** The faculty caps plagiarism plus AI-generated content at 30%. This is working material, not final prose. Style: APA 7, as in the approved proposal (`proposal/content.py`). Report Section 1 (Problems): problem statement, market research, and literature/analog review. The literature part builds on `research/literature_review/` (184 verified works); only works verified in this pass are cited (see the Verification log). "Abstract only" marks claims that rest on an abstract or on the project's extraction matrix.

# 1. Problems

## 1.1 Problem statement

Landlocked fuel importers receive refined petroleum products over a few land routes, from a few suppliers, through a few border crossings. A policy decision upstream, such as a refinery outage or an export restriction, can therefore change what arrives within weeks. For such a country the practical question is not only how much fuel will be consumed, but how much will physically cross the border next month, and how likely it is that this will fall well below normal.

Two things make this question hard to answer with the tools that exist today. First, customs statistics describe the past. Monthly import records reach public databases after a lag that differs by reporting country, so a decision-maker sees a fall in imports after the weeks in which it mattered. Second, planners lack a tested forward-looking signal. Supplier-concentration indices describe the origin mix but give no probability of a fall, and demand-forecasting models answer a different question (Section 1.4).

The problem addressed here is therefore stated in the study's own terms. The aim is a calibrated, probabilistic forecast of monthly physical imports of refined products for landlocked economies, with Kyrgyzstan as the detailed case, and an import-shortfall signal derived from that forecast: the probability that recorded imports fall below a stated reference level. The signal is a statistical object computed from customs records. A decline in recorded imports is not a confirmed physical shortage. Stocks, domestic production, re-exports, recording errors and timing can all separate the two, and the study does not observe retail availability. The signal is meant to prioritise attention, not to certify a shortage.

The problem has three testable parts: whether pooled models forecast imports better than country-by-country models, whether the stated forecast intervals are honest (calibrated) at the horizons a planner needs, and whether screening by the forecast distribution beats screening by a concentration ranking. These parts are formalised as objectives and hypotheses in Section 2.

## 1.2 Market research: the Kyrgyz and regional fuel market

Kyrgyzstan has small domestic oil and gas resources and relies on imports of oil and oil products (IEA, 2022). The project's own validated data show how that reliance varies by fuel. They come from the national Fuel and Energy Balance (2024 edition, thousand tonnes), processed in `petroleum-import-risk/reports/phase2/tables/kyrgyz_import_dependency.csv`, and are annual, to 2024. Net import dependency, defined as (imports minus exports) divided by domestic use, was 0.77 for gasoline and 0.86 for diesel in 2024. Domestic production is a minor and unstable source for gasoline: it supplied 24% of domestic use in 2016, 33% in 2017, 26% in 2018 and 23% in 2024, but only 2% to 5% in 2020 and 2022 to 2023. Fuel oil is a different case, where Kyrgyzstan was a net exporter in several years (2021 to 2023). Stocks vary widely. Year-end gasoline stock cover (year-end stock divided by average monthly use) reached 4.49 months in 2022 and fell to 1.99 in 2023, so a cushion at one year-end does not guarantee one at the next. These are annual, year-end figures and say nothing about monthly shortfalls.

The supply side depends on Russia. A trade-press item reports that Russia is "the main supplier of fuel and lubricants" (Kun.uz, 2026), and another that about 95% of annual needs, around 2 million tonnes, were historically covered by duty-free imports from Russia (Economist.kg, 2026). That 95% is a historical, press-reported figure, not a measured current share. The approved proposal quotes about 93%; no source for that number was verified in this pass `[UNVERIFIED: 93% Russia share, not found in a checked source]`. Russia's export measures are the main documented external shock. Russia banned gasoline and diesel exports from 21 September 2023 (Global Trade Alert, 2023), and announced a six-month gasoline export ban from March 2024 that exempted Kyrgyzstan and other Eurasian Economic Union members (Enerdata, 2024). A Kyrgyz press report in 2025 stated that a Russian gasoline ban was not expected to affect Kyrgyz supply because of an intergovernmental agreement (24.kg, 2025). An exemption on paper does not prove that physical deliveries were unchanged, which is a question for data.

In July 2026 Kyrgyzstan itself imposed an indefinite ban on road and rail fuel exports to prevent shortages, citing earlier Russian restrictions (Kun.uz, 2026). A second report states that reserves covered about 1.5 months, against an official aim of at least 2.5 months, and that contracts or talks with Belarus, China, Uzbekistan and Kazakhstan were under way, at higher cost than Russian supply (Economist.kg, 2026). Both reports contain no import volumes. The detailed course of the 2026 AI-95 gasoline episode and its retail effects, as described in the approved proposal, remain `[UNVERIFIED: press]` beyond the two items above. These are news items: they describe the setting and do not count as measurement.

Market research therefore shows a market that is highly import-dependent for road fuels, concentrated on one supplier, exposed to supplier policy, and recently stressed, while the only official quantities are annual and arrive with a long lag. Official monthly fuel tonnage is not available (project feasibility report, `reports/phase2/research_feasibility_report.md`), which is why the study uses monthly customs records and why the shortfall signal is defined on them.

## 1.3 Analogs: existing monitoring tools

Several public tools track oil supply or trade. None is designed for the problem of Section 1.1.

**IEA Oil Market Report.** A monthly publication with statistics and commentary on supply, demand, inventories, prices, refining and trade for IEA and selected non-IEA countries (IEA, 2026a). It is a global and regional market-balance product. It gives no probabilistic forecast of one country's monthly imports of a given product, and landlocked Central Asian importers are not its unit of analysis.

**IEA emergency stocks and MOSES.** The IEA's oil security system rests on an obligation for each member to hold stocks equal to at least 90 days of net oil imports; the page states that net exporters are exempt and that drawdowns are reported to the Secretariat (IEA, 2026b). The Model of Short-term Energy Security (MOSES) adds indicators for disruption risk and resilience for IEA members (Jewell, 2011). These tools assess preparedness and vulnerability. They are built around member countries and emergency stocks, and are not a forward distribution of next month's physical imports for a non-member importer.

**JODI Oil World Database.** The Joint Organisations Data Initiative, coordinated by the IEF with partners including the IEA, OPEC and UNSD, aims to improve global oil data transparency, and its latest update on 19 November 2026 covered September 2026 data for 44 countries (JODI, 2026). It is a data-collection tool. The page implies a lag of about two months and offers no forecast. Coverage of the countries studied here was not checked `[UNVERIFIED: JODI coverage of the study countries]`.

**UN Comtrade.** The UN Statistics Division's database holds annual and monthly merchandise imports and exports by product and partner, reported by about 200 countries and areas, revised when countries send corrections (United Nations Statistics Division, 2026). It is the data source of this study, not a warning tool. Its releases differ by reporter and are revised, which is why the study emulates release lags (Section 1.9).

**Security-of-supply indices.** Academic indices of oil vulnerability and supplier diversification are reviewed in Section 1.5. They rank exposure and rarely test prediction.

Overall, the analogs measure market balance, preparedness, data or exposure. A public, calibrated, release-lag-aware probability of a monthly import shortfall for landlocked importers was not found among them. This is a statement about the tools checked on their official pages on 2026-11-25, not a survey of all national systems.

## 1.4 Literature review: petroleum and energy import forecasting

Most petroleum forecasting studies model demand, not physical imports. Gasoline demand has been forecast with machine learning in Australia (Li et al., 2022), and diesel demand in India with a neural autoregression that had the lowest error among the methods compared (Sharma et al., 2024). Petroleum-product imports have been studied with explanatory models, for example ARDL and error-correction models for Tanzania, which test determinants and do not evaluate out-of-sample forecasts (Sizza et al., 2025, abstract only). A 30-country panel forecasts annual oil demand, and support vector regression had the lowest error, but the target is demand and the features are contemporaneous macro variables (Zhu, 2023). For monthly flows with timely inputs, regression-based machine learning beat tree-based and traditional methods for aggregate world trade (Chinn et al., 2026, abstract only), and a release-calendar-aware network nowcasts oil exports of Norway and Thailand (Intarasat et al., 2026, preprint, not peer reviewed). The evidence is dominated by single countries, annual or value data, point forecasts, and demand rather than monthly physical imports of refined products. In the project's search no study pooled landlocked importers (`research_gaps.csv`, gap A).

## 1.5 Energy security, import dependency and supplier concentration

Energy security has many definitions and indicators (Ang et al., 2015, abstract only). Import-focused indices combine supplier shares, supplier risk and vulnerability: an oil vulnerability index for importing countries (Gupta, 2008) and a diversification measure for the EU (Le Coq & Paltseva, 2009). The IEA's short-term model adds disruption-oriented indicators (Jewell, 2011), and early-warning systems for oil security in China are index-based (Wang et al., 2018). The Herfindahl-Hirschman index (HHI) of supplier shares is the common core; a Serbian case, a landlocked market, applies it to oil and derivatives (Veselinović & Radukić, 2021, abstract only).

The HHI has three limits as a predictor. It is a static description of the origin mix and says nothing about whether, when or how far volumes will fall. It is share-based, so it misses a fall in total volume that leaves shares unchanged, and it scores a single stable-contract supplier as risky. It yields a ranking, not a probability. The only out-of-sample test found is by Kwon and Jeong (2026), a full-text study of Korean product-level imports: concentration rankings performed below the base rate for disruption onsets, while gradient-boosted rankings of dynamic trade-flow indicators captured about 31% of onsets with a median lead of nine months. This is one maritime, non-fuel-specific economy and it does not model publication lags.

## 1.6 Landlocked economies, transit dependence and fuel supply

Research on landlocked countries centres on trade costs, transit and connectivity (World Trade Organization, 2021; Athukorala & Hill, 2023, who describe Kyrgyzstan as a double-landlocked transition economy, abstract only). Energy-security work on the region is mostly descriptive or index-based: Akhmetov (2015) constructs supply and export-demand indices for Central Asia (abstract only), and Kosowska and Kosowski (2022) study Kyrgyzstan and Tajikistan with a focus on hydropower (abstract only). Sanctions after 2022 rerouted trade into Russia through the Caucasus and Central Asia (Chupilkin et al., 2023, abstract only). No forecasting study of landlocked fuel importers as a group was found in the searches run to 2026-11-07. They appear as a trade-cost category, and in energy research as single cases.

## 1.7 Oil supply disruptions and export restrictions

The disruption literature is mostly about crude oil, prices and large importers. Extreme-value and copula models describe tail risk of oil and gas supply disruptions (Gülpınar & Katata, 2013, abstract only). Geopolitical risk is measured by a news-based index (Caldara & Iacoviello, 2022), and its links with energy imports are explanatory: a shock lowers China's energy import volumes in the short run (Lin & Zhang, 2025) and raises the hazard that energy-import relationships end, more for oil (Peng et al., 2025); both are abstract-only. For refined products, a 2026 working paper finds that crack spreads rose more where prewar refined-product import dependence was higher (Luong, 2026, abstract only, not peer reviewed). Disruptions to refined fuels start in the supplier's refineries and export policy, which a global risk index does not capture, and a policy exemption need not protect physical supply. Documented export restrictions are therefore treated as an event calendar to validate warnings, not as a predictor.

## 1.8 Global and local models; probabilistic forecasting and calibration

A global model trained across series is not more restrictive than a local one in theory (Montero-Manso & Hyndman, 2021). Simulations show that global models cope with many short series and that gradient boosting can match recurrent networks at lower cost (Hewamalage et al., 2022, full text). Tree-based global models did well in the M5 competition (Januschowski et al., 2022; Makridakis et al., 2022), and trees often outperform deep networks on tabular data (Grinsztajn et al., 2022, preprint). On short cross-country panels, pooling reduced error by 15% to 28% against country-specific estimation, but the gain reversed under strong heterogeneity (Yolusever, 2026, full text, annual compositional data). Global learning and boosting are therefore strong defaults whose gains depend on similarity across series, and none of this evidence concerns monthly refined-fuel imports.

A probabilistic forecast should be calibrated and as sharp as possible (Gneiting et al., 2007) and be assessed with strictly proper scoring rules (Gneiting & Raftery, 2007). Conformalised quantile regression gives distribution-free interval adjustments (Romano et al., 2019, preprint), and extensions handle time series, where exchangeability fails (Xu & Xie, 2023; Zaffran et al., 2022, preprint). Probabilistic early warnings combine boosted forecasts with a classifier in renewable supply shortfalls (Khan & Wyrwa, 2025, abstract only, hourly electricity), while in petroleum probabilistic output is rare: a 2026 SSRN preprint applies quantile regression to aviation-fuel demand (Salim, 2026, abstract only). None of the petroleum import or fuel-demand studies above reports coverage or calibration.

## 1.9 Real-time data, publication lags and leakage

Results can change when forecasts use the data actually available at the time (Stark & Croushore, 2002; Croushore, 2006), including under data revision (Agyekum & Obese, 2026, preprint, full text: the machine-learning edge, confined to boosting, survives real-time data). Cross-validation that ignores time order can mislead for autoregressive models (Bergmeir et al., 2018). Customs data add their own issues: statistical imbalance in UN Comtrade (Hu et al., 2022) and mirror discrepancies affected by sanctions (Golovanova et al., 2026), both abstract only. Comtrade does not publish full vintage histories, so only release dates can be respected, not revisions. This study therefore uses a pseudo-real-time design with release-lag emulation on the latest vintage, a deviation from the first-release evaluation promised in the approved proposal; a second snapshot is used only to measure revisions (reported in Section 4). Among the petroleum studies, only the Norway and Thailand preprint masks inputs by release calendar (Intarasat et al., 2026).

## 1.10 Synthesis and research gap

The literature shows five things. (1) Petroleum import and fuel-demand forecasting is single-country, mostly annual or value-based, and reports point forecasts. (2) Supply-security indices, including HHI, are descriptive; the one out-of-sample test found (Kwon & Jeong, 2026) reports concentration performing below base rate, in a maritime, non-fuel-specific setting. (3) Landlocked fuel importers are studied as cases or as a trade-cost group, not as a forecasting panel. (4) Global learning and boosting are strong in general forecasting, but benefit depends on series similarity. (5) Calibration, conformal methods and release-date-aware evaluation are mature elsewhere but rare in petroleum trade.

The gap that follows is an application and evaluation gap, not a new method. In the searches run to 2026-11-07 (project search log; bibliographic data re-verified 2026-11-25), no study was found that provides a calibrated, release-lag-aware probabilistic benchmark for monthly physical imports of refined products in landlocked economies, or that compares screening by the forecast distribution with screening by a concentration ranking for import-shortfall signals (declines in customs-recorded imports, which are not observed supply shortfalls) outside the Korean case of Kwon and Jeong (2026). The methods are existing, and absence from these searches does not prove absence from the literature (`research_gaps.csv`; about 25 claims rest on abstracts only). The study's own results are reported in Section 4, not here.

## 1.11 Comparison of key studies

| Study | Setting and target | Method | Probabilistic output | Release lags handled | Relevance |
|---|---|---|---|---|---|
| Zhu (2023) | 30 countries, annual oil demand | Statistical models and AI (SVR) | No | No | Pooled panel, but demand and annual |
| Sharma et al. (2024) | India, monthly diesel demand | ARIMA-type, ANN | No | No | Monthly fuel, demand not imports |
| Sizza et al. (2025) | Tanzania, petroleum import demand | ARDL, ECM | No | No | Import determinants, explanatory |
| Kwon & Jeong (2026) | Korea, monthly product imports, disruption onset | Gradient boosting vs concentration | Rankings, PR | Not modelled | Nearest prior study for the H4 screening comparison |
| Intarasat et al. (2026) | Norway, Thailand, oil exports | Deep network | No | Yes (preprint) | Release-calendar masking |
| Chinn et al. (2026) | World trade, monthly | ML nowcasting | No | Real-time design | Real-time ML for trade |
| Yolusever (2026) | Cross-country annual panels | Pooled and shrunk models | No | No | Pooling gain reverses with heterogeneity |
| Hewamalage et al. (2022) | Simulated short series | Global models, LightGBM, RNN | No | No | Global models on many short series |
| Khan & Wyrwa (2025) | Europe, hourly renewable shortfall | Boosting plus classifier | Yes (alarm) | No | Probabilistic warning template |
| Akhmetov (2015) | Central Asia, oil security | Indices | No | No | Regional descriptive baseline |

# References (APA 7)

24.kg. (2025). *Russia's gasoline export ban not to affect fuel supplies to Kyrgyzstan*. https://24.kg/english/338006_Russias_gasoline_export_ban_not_to_affect_fuel_supplies_to_Kyrgyzstan

Agyekum, L., & Obese, O. (2026). *Forecasting in the fog: Real-time versus revised-data evidence on machine learning's edge over the Phillips curve*. arXiv. https://doi.org/10.48550/arxiv.2608.09033

Akhmetov, A. (2015). Measuring the security of external energy supply and energy exports demand in Central Asia. *International Journal of Energy Economics and Policy*. https://econjournals.com/index.php/ijeep/article/view/1244

Ang, B. W., Choong, W. L., & Ng, T. S. (2015). Energy security: Definitions, dimensions and indexes. *Renewable and Sustainable Energy Reviews, 42*, 1077-1093. https://doi.org/10.1016/j.rser.2014.10.064

Athukorala, P., & Hill, H. (2023). Trade policy in a 'double-landlocked' transition economy: Kyrgyzstan. *The World Economy, 46*(12), 3455-3471. https://doi.org/10.1111/twec.13416

Bergmeir, C., Hyndman, R. J., & Koo, B. (2018). A note on the validity of cross-validation for evaluating autoregressive time series prediction. *Computational Statistics & Data Analysis, 120*, 70-83. https://doi.org/10.1016/j.csda.2017.11.003

Caldara, D., & Iacoviello, M. (2022). Measuring geopolitical risk. *American Economic Review, 112*(4), 1194-1225. https://doi.org/10.1257/aer.20191823

Chinn, M., Meunier, B., & Stumpner, S. (2026). Nowcasting world trade with machine learning: A three-step approach. *Journal of Forecasting, 45*(6), 2954-2968. https://doi.org/10.1002/for.70165

Chupilkin, M., Javorcik, B., & Plekhanov, A. (2023). *The Eurasian roundabout: Trade flows into Russia through the Caucasus and Central Asia*. SSRN. https://doi.org/10.2139/ssrn.4368618

Croushore, D. (2006). Forecasting with real-time macroeconomic data. In *Handbook of economic forecasting* (pp. 961-982). Elsevier. https://doi.org/10.1016/S1574-0706(05)01017-7

Economist.kg. (2026, July 22). *Fuel stocks for 1.5 months: Kyrgyzstan diversifies imports* [in Russian]. https://economist.kg/transport/2026/07/22/zapasy-gsm-diversifikaciya-importa.md

Enerdata. (2024, February 29). *Russia will impose a six-month ban on gasoline exports from March 2024*. https://www.enerdata.net/publications/daily-energy-news/russia-will-impose-six-month-ban-gasoline-exports-march-2024.html

Global Trade Alert. (2023). *Russia: Restriction on the export of motor gasoline and diesel fuel*. https://globaltradealert.org/state-act/77973-russia-restriction-on-the-export-of-motor-gasoline-and-diesel-fuel

Gneiting, T., Balabdaoui, F., & Raftery, A. E. (2007). Probabilistic forecasts, calibration and sharpness. *Journal of the Royal Statistical Society: Series B, 69*(2), 243-268. https://doi.org/10.1111/j.1467-9868.2007.00587.x

Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association, 102*(477), 359-378. https://doi.org/10.1198/016214506000001437

Golovanova, S., Rodichev, A., & Zinyakov, Y. (2026). Discrepancies in trade statistics in 2003-2024: The impact of sanctions. *Economics & Politics, 38*(3), 653-664. https://doi.org/10.1111/ecpo.70046

Grinsztajn, L., Oyallon, E., & Varoquaux, G. (2022). *Why do tree-based models still outperform deep learning on tabular data?* arXiv. https://doi.org/10.48550/arxiv.2207.08815

Gülpınar, N., & Katata, K. (2013). Modelling oil and gas supply disruption risks using extreme-value theory and copula. *Journal of Applied Statistics, 41*(1), 2-25. https://doi.org/10.1080/02664763.2013.827160

Gupta, E. (2008). Oil vulnerability index of oil-importing countries. *Energy Policy, 36*(3), 1195-1211. https://doi.org/10.1016/j.enpol.2007.11.011

Hewamalage, H., Bergmeir, C., & Bandara, K. (2022). Global models for time series forecasting: A simulation study. *Pattern Recognition, 124*, 108441. https://doi.org/10.1016/j.patcog.2021.108441

Hu, L., Song, C., Ye, S., & Gao, P. (2022). Spatiotemporal statistical imbalance: A long-term neglected defect in UN Comtrade dataset. *Sustainability, 14*(3), 1431. https://doi.org/10.3390/su14031431

Intarasat, U., Bootwisas, N., & Marupanthorn, P. (2026). *VP-OilEx-STFN: Structural-gated mixed-frequency nowcasting for oil export prediction in Norway and Thailand* [Preprint]. Research Square. https://doi.org/10.21203/rs.3.rs-9995316/v1

International Energy Agency. (2022). *Kyrgyzstan 2022: Energy policy review*. https://www.iea.org/reports/kyrgyzstan-2022

International Energy Agency. (2026a). *Oil market report: October 2026*. https://www.iea.org/reports/oil-market-report-october-2026

International Energy Agency. (2026b). *Oil security and emergency response*. https://www.iea.org/about/oil-security-and-emergency-response

Januschowski, T., Wang, Y., Torkkola, K., Erkkilä, T., Hasson, H., & Gasthaus, J. (2022). Forecasting with trees. *International Journal of Forecasting, 38*(4), 1473-1481. https://doi.org/10.1016/j.ijforecast.2021.10.004

Jewell, J. (2011). *The IEA model of short-term energy security (MOSES)* (IEA Energy Papers). OECD Publishing. https://doi.org/10.1787/5k9h0wd2ghlv-en

Joint Organisations Data Initiative. (2026). *JODI-Oil world database*. https://www.jodidata.org/oil/

Khan, A., & Wyrwa, A. (2025). An early warning system for renewable energy supply shortfalls in Europe using integrated machine learning and spatiotemporal energy data. In *2025 14th International Conference on Renewable Energy Research and Applications (ICRERA)* (pp. 1344-1350). IEEE. https://doi.org/10.1109/ICRERA66237.2025.11283745

Kosowska, K., & Kosowski, P. (2022). Energy security of hydropower producing countries: The cases of Tajikistan and Kyrgyzstan. *Energies, 15*(21), 7822. https://doi.org/10.3390/en15217822

Kun.uz. (2026, July 15). *Kyrgyzstan imposes indefinite ban on fuel exports to prevent shortages*. https://kun.uz/en/news/2026/07/15/kyrgyzstan-imposes-indefinite-ban-on-fuel-exports-to-prevent-shortages-ea7730

Kwon, M., & Jeong, D. (2026). Dynamic trade flow indicators outperform import concentration in supply disruption early warning for a maritime-dependent economy. *Frontiers in Marine Science, 13*, 1956773. https://doi.org/10.3389/fmars.2026.1956773

Le Coq, C., & Paltseva, E. (2009). Measuring the security of external energy supply in the European Union. *Energy Policy, 37*(11), 4474-4481. https://doi.org/10.1016/j.enpol.2009.05.069

Li, Z., Zhou, B., & Hensher, D. A. (2022). Forecasting automobile gasoline demand in Australia using machine learning-based regression. *Energy, 239*, 122312. https://doi.org/10.1016/j.energy.2021.122312

Lin, B., & Zhang, Z. (2025). Anchoring security in uncertainty: The dynamic responses of China's energy imports to geopolitical risk shocks. *Energy, 335*, 137996. https://doi.org/10.1016/j.energy.2025.137996

Luong, P. V. (2026). *Geopolitical shocks in vertically linked petroleum products supply chains* [Working paper]. SSRN. https://doi.org/10.2139/ssrn.7679879

Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2022). M5 accuracy competition: Results, findings, and conclusions. *International Journal of Forecasting, 38*(4), 1346-1364. https://doi.org/10.1016/j.ijforecast.2021.11.013

Montero-Manso, P., & Hyndman, R. J. (2021). Principles and algorithms for forecasting groups of time series: Locality and globality. *International Journal of Forecasting, 37*(4), 1632-1653. https://doi.org/10.1016/j.ijforecast.2021.03.004

Peng, S., Wang, L., & Chen, Y. (2025). The survival of global energy imports and the impact of geopolitical risks. *Energy Economics, 147*, 108595. https://doi.org/10.1016/j.eneco.2025.108595

Romano, Y., Patterson, E., & Candès, E. J. (2019). *Conformalized quantile regression*. arXiv. https://doi.org/10.48550/arxiv.1905.03222

Salim, H. (2026). *Hybrid SARIMA-XGBoost framework with quantile regression for aviation fuel demand forecasting and inventory planning* [Preprint]. SSRN. https://doi.org/10.2139/ssrn.6893382

Sharma, A. M., Baby, S., & Raghu, V. (2024). Forecasting high speed diesel demand in India with econometric and machine learning methods. *International Journal of Energy Economics and Policy, 14*(1), 496-506. https://doi.org/10.32479/ijeep.15572

Sizza, H., Nyangarika, A., & Kivevele, T. (2025). Determinants of petroleum product import demand in Tanzania: A time series analysis using ARDL and ECM approaches. *Quality & Quantity, 60*(1), 995-1021. https://doi.org/10.1007/s11135-025-02268-7

Stark, T., & Croushore, D. (2002). Forecasting with a real-time data set for macroeconomists. *Journal of Macroeconomics, 24*(4), 507-531. https://doi.org/10.1016/S0164-0704(02)00062-9

United Nations Statistics Division. (2026). *UN Comtrade*. https://comtrade.un.org/

Veselinović, M., & Radukić, S. (2021). Measuring supply concentration on the Serbian oil and oil derivates market by Herfindahl-Hirschman index. *Facta Universitatis, Series: Economics and Organization*, 343. https://doi.org/10.22190/FUEO201005025V

Wang, Q., Tang, H., Yuan, X., Wang, M., Xiao, H., & Ma, Z. (2018). An early warning system for oil security in China. *Sustainability, 10*(1), 283. https://doi.org/10.3390/su10010283

World Trade Organization. (2021). Landlocked developing countries and trade bottlenecks. In *Easing trade bottlenecks of landlocked developing countries* (pp. 5-6). https://doi.org/10.30875/9789287053305-003.zhtml

Xu, C., & Xie, Y. (2023). Conformal prediction for time series. *IEEE Transactions on Pattern Analysis and Machine Intelligence, 45*(10), 11575-11587. https://doi.org/10.1109/TPAMI.2023.3272339

Yolusever, A. (2026). Pooling beats structure on short annual panels: Parameter sharing and the forecast accuracy of evolutionary models for compositional time series. *Forecasting, 8*(5), 89. https://doi.org/10.3390/forecast8050089

Zaffran, M., Dieuleveut, A., Féron, O., Goude, Y., & Josse, J. (2022). *Adaptive conformal predictions for time series*. arXiv. https://doi.org/10.48550/arxiv.2202.07282

Zhu, H. (2023). Oil demand forecasting in importing and exporting countries: AI-based analysis of endogenous and exogenous factors. *Sustainability, 15*(18), 13592. https://doi.org/10.3390/su151813592

# Verification log

Method codes: CR = Crossref API re-queried 2026-11-25 (title, first authors, author count, year, container, volume, pages matched); DC = DataCite API re-queried; PM = earlier verification and extraction recorded in `papers_master.csv`/`literature_matrix.csv` (relied on, not redone); WF = official page fetched with WebFetch/WebSearch on 2026-11-25 (content read, no DOI). Claim basis: F = full text per matrix, A = abstract only, M = metadata only, Web = web page.

| Reference | How verified | Basis | Status |
|---|---|---|---|
| Agyekum & Obese (2026) | DC + PM | F | Verified (preprint) |
| Akhmetov (2015) | PM (no DOI; journal URL) | A | Verified by URL in PM only |
| Ang et al. (2015); Athukorala & Hill (2023) | CR + PM | A | Verified |
| Bergmeir et al. (2018) | CR + PM | M | Verified |
| Caldara & Iacoviello (2022) | CR + PM | A | Verified |
| Chinn et al. (2026); Chupilkin et al. (2023) | CR + PM | A | Verified (Chupilkin is an SSRN working paper) |
| Croushore (2006) | CR + PM | M | Verified |
| Gneiting et al. (2007); Gneiting & Raftery (2007) | CR + PM | A | Verified |
| Golovanova et al. (2026); Hu et al. (2022) | CR + PM | A | Verified |
| Grinsztajn et al. (2022); Romano et al. (2019); Zaffran et al. (2022) | DC + PM | A | Verified (arXiv preprints) |
| Gülpınar & Katata (2013); Gupta (2008) | CR + PM | A | Verified |
| Hewamalage et al. (2022) | CR + PM | F | Verified |
| Intarasat et al. (2026) | CR + PM | F | Verified (Research Square preprint, not peer reviewed) |
| Januschowski et al. (2022); Makridakis et al. (2022); Montero-Manso & Hyndman (2021) | CR + PM | A | Verified |
| Jewell (2011) | CR + PM | A | Verified; Crossref lists no authors, author from PM, not independently confirmed. The IEA MOSES report page returned 404 on 2026-11-25, so the MOSES description rests on this record only |
| Khan & Wyrwa (2025); Kosowska & Kosowski (2022) | CR + PM | A | Verified |
| Kwon & Jeong (2026) | CR + PM | F | Verified |
| Le Coq & Paltseva (2009); Li et al. (2022) | CR + PM | A | Verified |
| Lin & Zhang (2025); Peng et al. (2025) | CR + PM | A | Verified |
| Luong (2026); Salim (2026) | CR + PM | A | Verified (SSRN preprints, not peer reviewed) |
| Sharma et al. (2024); Yolusever (2026); Zhu (2023) | CR + PM | F | Verified |
| Sizza et al. (2025) | CR + PM | A | Verified (Crossref title has `&amp;`) |
| Stark & Croushore (2002); Veselinović & Radukić (2021); Wang et al. (2018); Xu & Xie (2023) | CR + PM | A | Verified |
| World Trade Organization (2021) | CR + PM | M | Verified; organisational author; claim limited to topic |
| IEA (2022) | Page fetched 2026-11-25 (WF) | Web | Verified for import reliance only |
| IEA (2026a) Oil Market Report, October 2026 | WF 2026-11-25 | Web | Verified; page says published 14 October 2026 and describes scope |
| IEA (2026b) Oil security and emergency response | WF/search snippet 2026-11-25 | Web | Verified from search result summary (90 days of net imports; net exporters exempt); the page itself was not opened |
| JODI (2026) | WF 2026-11-25 | Web | Verified for coordination, partners, and the 19 Nov 2026 update; the page did not state products or coverage |
| United Nations Statistics Division (2026) UN Comtrade | WF 2026-11-25 | Web | Verified |
| Kun.uz (2026) | WF 2026-11-25 | Web | Verified: 15 July 2026, indefinite ban on road and rail fuel exports, Russia named main supplier, no figures |
| Economist.kg (2026) | WF 2026-11-25 | Web | Verified: 22 July 2026, about 1.5 months reserves, 2.5-month aim, 95% historical Russian share; fetched through summary, Russian original not read line by line |
| Global Trade Alert (2023) | WF 2026-11-25 | Web | Verified: gasoline and diesel export ban announced 21 Sep 2023 (page headline); no decree number on page |
| Enerdata (2024) | WF 2026-11-25 | Web | Verified: 29 Feb 2024, six-month ban from 1 March 2024; exemptions include Kyrgyzstan |
| 24.kg (2025) | Page fetched 2026-11-25 | Web | Verified for the exemption statement |

Stage A restructure (2026-11-25): Section 1 was rebuilt to the faculty structure (problem statement, market research, analogs, literature review). Removed from the review to meet the length limit, still verified in `papers_master.csv` but not cited here: Baltagi & Griffin (1997), Baumeister & Kilian (2011), Beccue et al. (2018), Champahom et al. (2025), Cohen et al. (2011), Gately & Streifel (1997), Grimme et al. (2021), Hewamalage et al. (2022b), Hong et al. (2016), Jensen et al. (2024), Korneev & Pechishcheva (2022), Laborda et al. (2023), Makridakis et al. (2022a, c), Martin & Swanson (2009), Pradhan et al. (2023), Qin et al. (2026), Semenoglou et al. (2021), Yang et al. (2014); 18 removals. Dropped after checking: Global Trade Alert (2025), cited in the proposal under the title "temporary ban on petrol exports reinstated ... 1 October-31 December 2025"; the URL fetched on 2026-11-25 returned a different act (government termination of the gasoline export ban, 31 Jan 2026), so the proposal's citation title and claim need checking. Also dropped: Arkhangelskaya (2026), UNCTAD (2026), IMF working papers, Briggs (2025), Times of Central Asia (Kwan, 2026), not re-verified. Counts: 55 works cited (some rows group several); all bibliographic records verified; 0 tagged `[UNVERIFIED]` in the reference list. Three claims in the text carry an inline `[UNVERIFIED]` tag: the 93% Russia share, the 2026 AI-95 episode detail, and JODI coverage of the study countries. Project figures in 1.2 come from `kyrgyz_import_dependency.csv` (annual, thousand tonnes, net import dependency and stock cover as defined in `kyrgyz_validation.md`); they were read from that file, not recomputed. Claims resting on abstracts only are marked "abstract only"; support was checked against the extraction matrix, not by re-reading every full text.
