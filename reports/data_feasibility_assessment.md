# Data feasibility assessment

Snapshot 2026-11-02. No forecasting or modelling was done.

**Decision: the dataset is ready for the forecasting stage, using the 20-country core panel, with Kyrgyzstan as the case study. Do not use the panel as a plain list of "landlocked importers": several reporters are transit or export markets, and the distillate series is not comparable across all countries.**

## Status of the data collection

| Phase | State |
|---|---|
| 1. API documentation and authentication | Complete. Both keys tested on the data endpoint |
| 2. Kyrgyzstan pilot | Complete: 192 requests, 0 failures, all four flows |
| 3. Country coverage audit | Complete: 43 candidates, 204 requests, 0 failures |
| 4. Full partner-level panel | Complete: 324 keyed requests, 0 failures, 0 truncated; 416,267 partner rows for 28 reporters |
| 5. External indicators | Complete, with the exclusions below |
| 6. Data engineering | Complete. Datasets A-D built. Full data loaded into an embedded PostgreSQL 16 test instance with all constraints enforced (462,252 raw and 416,267 staging rows). `DATABASE_URL` is empty, so no permanent database exists yet, and Dataset D is file-only |
| 7. Quality assessment | Complete |
| 8. Research readiness | This document |

Requesting several periods in one call worked, and the two keys appear to share one quota: a per-operation counter kept falling across them. That rests on a single observation, and it is not documented.

## The ten questions

**1. Is the Kyrgyzstan dataset sufficiently complete?**
Yes, from 2015. The 136 monthly observations reproduce exactly: 136 of 140 months are published, and Sep-Oct 2019 and Jun-Jul 2026 are absent from Comtrade, still so on 2 Nov 2026. After quality checks, **133** months are usable for gasoline and 133 for middle and heavy distillates. Use 133, not 136.

**2. Which product categories have reliable monthly data?**

| Group | HS | Kyrgyz usable months from 2015 | Verdict |
|---|---|---|---|
| Gasoline proxy | 2710.12 (2710.11 under HS2007) | 133 | Reliable. Primary target. Also holds naphtha and blending components |
| Middle and heavy distillates | 2710.19 | 133 | Reliable as an aggregate. Not diesel: HS6 cannot separate diesel, jet, kerosene, fuel oil or lubricants |
| Distillates with blends | 2710.19 + 2710.20 | Added for comparison | Needed for reporters with blended road diesel |
| LPG | 2711.12, .13, .19 | 134 | Usable as a descriptive series |
| Biodiesel blends | 2710.20 | 19 | Too sparse for Kyrgyzstan alone |
| Crude | 2709 | 49 | Context only |

Separate diesel, jet fuel and fuel oil series do not exist in Comtrade at six digits.

**3. How many landlocked countries can be included?**

| Level | Countries | Series | Observations |
|---|---|---|---|
| Final tiers | Tier 1: 15. Tier 2: 13. Tier 3: 15 | | |
| Eligible panel | 22 | 44 | 5,535 |
| **Core panel (recommended)** | **20** | **35** (19 gasoline, 16 distillates) | **4,324** |
| Core, provisional strict importers | 12 | 23 | 2,841 |

Eligible requires a usable tier, at least 84 usable months with partner data, and no sign of mislabelled products. Core also requires exports below half of imports, and for distillates a blend share below 20%. Both cut-offs are judgment calls, listed at the end.

Partner data changed three tiers: Czechia moved from 3 to 1, and Slovakia and Serbia from 2 to 1. World rows had understated them.

Notable exclusions:
- No monthly data at all: Afghanistan, Central African Republic, Chad, Mali, Nepal, San Marino, Tajikistan, Turkmenistan. Liechtenstein reports within Switzerland.
- Too short: Austria, Bhutan, Ethiopia, Niger, South Sudan, Uganda.
- Mislabelled fuels suspected: Botswana, Eswatini, Lesotho, Malawi. One product line is under 5% of the other.
- Mongolia (72 months, ends 2021) and Belarus (76 months, ends April 2021, exports about 7 times imports). Mongolia is still worth a supplementary look because it is similarly dependent on Russia.

Central Asia in the core means Kyrgyzstan, Uzbekistan from 2019 and Kazakhstan gasoline. Kazakhstan's distillates fail on exports.

**4. How many usable country-product-month observations are available?**
**4,324 in the core panel; 5,535 in the eligible panel**, January 2015 to August 2026. The pilot figures of 43 series, 22 countries and 4,942 observations are superseded. The new counts use partner-level mass and stricter checks, and the membership differs.

**5. Is quantity data sufficiently complete?**
Yes. Of 416,267 partner rows, 407,743 use net weight. A further 5,917 use a kg quantity, and these are concentrated in Bolivia (8.5% of its mass), Kazakhstan (6.8%) and Zambia (5.7%). Where both exist, they agree within 1% on 97.2% of rows. 2,603 rows have no usable mass, and 4 were rejected on density (2 Kyrgyz, 2 Uzbek). Litres are never converted into `mass_t`, and mass is never derived from value.

**6. Are bilateral supplier records sufficiently complete?**
Yes. In the core panel, 4,310 of 4,324 series-months have supplier records covering at least 90% of import value. Partner values match World values in all but one series-month of the comparison. Hungary has no partner-level imports for 2015-2016, only World rows.

World rows lacked mass in up to 43 months per series (Luxembourg gasoline), so rebuilding totals from partners is necessary, not optional.

**7. Which external variables match reliably?**

| Variable | Source | Coverage | Status |
|---|---|---|---|
| Brent, WTI | EIA | 100%, to Sep 2026 | Match |
| Global GPR, GPRT, GPRA | Caldara-Iacoviello | 100%, to Sep 2026 | Match |
| Russia, Ukraine, Türkiye, China GPR | Same | 100% | Match, as supplier-side series |
| Monthly FX | BIS, period average | 27 of 28 countries, 93% | Match |
| Monthly CPI | IMF | 27 of 28 countries, 93% | Match |
| GDP, population, industry share, annual inflation | World Bank | To 2025 | Annual only. Static or lagged covariates; never treated as monthly |

Series end on different dates by country, so release timing has to be handled at modelling time.

**8. Which variables should be excluded?**
- Country-level GPR for the panel: exists for only 2 of 28 countries (Switzerland, Hungary), and for no Central Asian country.
- HS 2710.19 alone for Hungary (57% blends), Slovakia (55%), Luxembourg (32%) and Czechia (21%).
- Vehicle fleet: the World Bank indicator has 2 values in total.
- Monthly industrial production: not collected, because no consistent source covers the panel.
- Gross weight: all Kyrgyz rows hold zero.

**9. What limitations could still weaken the research?**
1. **Partner may mean seller, not route.** Rwanda's and Zambia's leading partner is the UAE, and Zimbabwe's is Singapore, so records seem to show origin or trader, not the corridor. This is my inference from the patterns; the field definition should be checked. A shared-supplier feature would not measure shared transit risk, which matters for RQ3.
2. **Publication lag differs widely.** Median lag from January 2021 is 68 days for Kyrgyzstan and under 90 days for 11 of the 20 core countries, but at least 200 days for eight (Andorra, Burundi, Burkina Faso, Kazakhstan, Laos, Rwanda, Zambia, Zimbabwe). True as-of replay will shrink the global training set at recent origins. The pilot did not show this.
3. **The 2026 shock window is thin.** Only 14 of the 20 core countries reach January 2026, and 11 reach June 2026. Rwanda stops in 2022, Laos and Zambia in 2023, and Burkina Faso in 2024.
4. **HS 2710.19 is a mixture.** It runs at 0.85-1.45 of diesel plus fuel oil in the balance.
5. **2015-2017 gasoline is weaker.** Ratios of 0.72-0.91 against the balance, compared with a 3.7% mean absolute difference from 2018.
6. **Russian mirror data end in 2021**, as the proposal found.
7. **Comtrade flags are undocumented.** `isReported` is False on most rows, and the public documentation I found does not define `isAggregate` or `legacyEstimationFlag`. Reported and estimated records cannot be fully separated. Only the explicit weight and quantity estimate flags are used.
8. **Importer types are provisional.** `importer_type_provisional` was set by hand and needs checking before the strict-importer ablation.
9. **Unexplained heading gap.** For Hungary, six-digit lines differ from the 2710 heading by more than 1% in 43 months. Paraguay (3) and Lesotho (2) show it rarely. I did not find the cause, and these lines are used as reported.

**10. Is the dataset ready for forecasting experiments?**
**Yes.** Kyrgyz baselines, global models and supplier-structure experiments can all proceed on the core panel. Three steps come first: recompute the shortfall labels, have the rules below reviewed, and lag `dataset_d_integrated` to release dates.

## Corrections to the research proposal

Each of these changes something already written, so they should be carried into the thesis.

| Proposal says | Finding |
|---|---|
| 136 usable monthly observations | 136 are published; 133 are usable per product |
| Oct-Nov 2017 gasoline is a mass error | Confirmed as bad, with a more specific cause. Net weight is blank and `qty` is also wrong: 107,038 t over 75.6M litres is 1.42 kg/L. Rows with a true net weight imply 0.741 kg/L |
| Set those months to missing | Kept missing in `mass_t`. A labelled estimate from litres (55.9 and 65.5 kt) lives in a separate column. With it, 2017 is 1.08 of the balance |
| 8 distillate shortfall episodes | **Must be recomputed.** Aug-Sep 2015 (176.7 and 233.6 kt at USD 179 and 105/t) fail the unit-value check, and they inflated the 2016 baseline |
| Other unit-value failures | Also rejected: Feb 2016 gasoline, Feb 2022 distillates. Apr 2024 distillates has a suspect value, so its mass is kept and flagged |
| HS 2710.19 runs about 1.4 times diesel | Fairer against diesel plus fuel oil: 0.85-1.45 across years (2024: 1.09, against 1.38 for diesel alone) |
| Median lag 72 days | 68 days from January 2021; earlier years are backfilled |
| 43 series, 22 countries, 4,942 observations | Core panel of 35 series, 20 countries, 4,324 observations |
| Heterogeneous panel tagged by hand | Measured exports show Belarus, Slovakia, Serbia gasoline, and Azerbaijan, Kazakhstan and Hungary distillates export more than they import |
| Partner-level panel needs an API key | Done. It covers 28 reporters |
| Exchange rate is planned, not verified | Verified: BIS monthly averages |
| Exports not yet pulled | Pulled. Gasoline exports match the balance closely (2024: 77.6 vs 76.4 kt; 2015: 31.85 vs 31.8 kt), which is independent support for the target |

Confirmed unchanged: the 3.7% gasoline reconciliation from 2018, and the August 2026 episode (16.9 kt, Russia 44%, USD 1,149/t).

## Rules that need a supervisor's review

These decide which data survive, and several thresholds are my judgment rather than established standards:

- Density bounds: gasoline 0.68-0.80, LPG 0.48-0.62, other 0.60-1.05 kg/L (`src/preprocessing/cleaning.py`).
- Relative unit value: Brent-deflated, against a centred 13-month median. Below 0.5 removes mass; above 2.0 only flags. A centred window uses future months, which is acceptable for cleaning history but must not feed live or as-of features.
- Product-split check at 5%.
- Core panel cut-offs: exports below 50% of imports and blend share below 20%. Two series sit close to these lines: Serbia's distillates stay in at 0.45, and Czechia's distillates fall out on blends at 21%.
- Tier thresholds and the 84-month minimum (`config/settings.yaml`).
