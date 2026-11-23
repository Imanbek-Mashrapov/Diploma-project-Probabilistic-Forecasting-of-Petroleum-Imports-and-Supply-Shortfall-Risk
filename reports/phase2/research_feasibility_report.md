# Research feasibility report

Snapshot 2026-11-02, dataset version 1.0.0. No forecasting model was trained. Figures come from `data/research/` and `reports/phase2/tables/`.

## Recommendation: CONDITIONAL GO

The data can support the research. Kyrgyz gasoline is well validated from 2018, a global panel is feasible, and supplier data are nearly complete. The condition is about the most recent months, which are also the most important ones: Kyrgyz records from 2025 onward seem to be first-release figures that official statistics later revise upward, so the depth of the 2025-2026 shock is uncertain.

**Before any model runs:**
1. Have a supervisor review and freeze the cleaning and tier rules.
2. Treat 2025-2026 as provisional, and evaluate on data as first released.
3. Take a second Comtrade snapshot, so revisions can be measured instead of assumed.
4. Lag every feature to its release date.
5. Build a sourced event list before using any shortfall label as a validation target.

Baselines and pipeline work can start now.

## The ten questions

### 1. Is the collected data sufficient for the proposed research?

Yes for monthly forecasting and supplier analysis. Partly for shock analysis: there are few documented events, and the newest are the least certain. The panel has 44 usable series and 5,549 observations in 22 countries.

### 2. Which countries have long and reliable monthly series?

Thirteen countries have at least one Tier 1 series in the main experiment.

| Series | Tier 1 countries |
|---|---|
| Gasoline (11) | Andorra, Armenia, Azerbaijan, Bolivia, Hungary, Kyrgyzstan, Luxembourg, Moldova, North Macedonia, Paraguay, Switzerland |
| Distillates with blends (11) | Andorra, Armenia, Bolivia, Czechia, Kyrgyzstan, Luxembourg, Moldova, North Macedonia, Paraguay, Serbia, Switzerland |

Tier 2 adds Burkina Faso, Burundi, Kazakhstan, Laos, Rwanda, Slovakia, Uzbekistan, Zambia and Zimbabwe, each with stated limits. Tier 3 covers 21 countries per product, with reasons in `country_product_coverage.csv`. Kazakhstan and Uzbekistan are Tier 2, so Kyrgyzstan is the only Central Asian country in Tier 1.

### 3. Which products belong in the main experiment?

- **Gasoline proxy (HS 271011/12):** primary target.
- **Distillates with blends (HS 271019 + 271020):** second target. For Kyrgyzstan this is identical to 271019, as Kyrgyz blends are negligible in mass.
- **LPG:** descriptive only.
- **Excluded as targets:** crude, the 2710 heading total, and biodiesel blends alone.

Separate diesel, jet fuel and fuel oil targets are not possible with Comtrade.

### 4. Is a global panel feasible?

Yes, with limits. Evaluation should use the Tier 1 set of **22 series, 13 countries and 3,021 observations**, while training may use Tier 1 and 2 together, **44 series, 22 countries and 5,549 observations**. That suits small models only, as the proposal already concluded.

Reasons for caution:
- Series co-move weakly: the median pairwise correlation of year-on-year gasoline changes is close to zero, so pooling may help mainly through shared dynamics, not shared shocks.
- The panel is mixed: exporters, transit markets, microstates and low-income importers.
- Only 12 of 22 gasoline series reach June 2026.
- Eight of the 22 panel countries have a median release lag of at least 200 days, which shrinks true as-of training sets.

Whether pooling helps Kyrgyzstan remains a question for the experiments.

### 5. Is Kyrgyzstan suitable as the main case study?

Yes. It is Tier 1 for both products, with 133 of 140 months observed in each.

| Check | Result |
|---|---|
| Gasoline mass against the energy balance | 3.7% mean absolute difference from 2018 |
| Gasoline value against the official table | Within 5% in 2022-2024 |
| Gasoline exports against the balance | Close match (2024: 77.6 and 76.4 kt) |
| Partner rows against World | No month differs by more than 5% in value |
| Russian mirror | 0.93-1.02 in 2018 and 2021; 0.33-0.37 in 2016-2017 |

Weak points: 2015-2017 gasoline, and 2025-2026 because of first-release data. Report results both with and without 2015-2017.

### 6. Are supplier data sufficient for measuring concentration?

Yes. In 99.4% of series-months, partner rows with mass cover at least 90% of import value, and only 81 of 6,505 series-months have an unallocated partner share above 10%.

Two limits matter:
- Kyrgyz gasoline concentration is high in most years (median 12-month HHI 0.89), so it has little variation to work with as a predictor.
- Partner seems to mean origin or seller, not corridor. Rwanda's and Zambia's leading partner is the UAE. So shared-supplier features may not measure shared route risk.

Supplier concentration is separate from import dependency, which can be computed only for Kyrgyzstan: 0.77 for gasoline and 0.86 for diesel in 2024.

### 7. Which external indicators are reliable and useful?

| Indicator | Reliability | Evidence of usefulness so far |
|---|---|---|
| Brent, WTI | High, complete | Weak on average (median rho about 0.1) |
| Global and Russia GPR | High, complete | Weak on average; signs vary |
| Monthly exchange rates (BIS) | High, 27 of 28 countries | Weak on average |
| Monthly CPI (IMF) | High, 27 of 28 countries | Weak on average |
| GDP, population | Annual only | 0 of 39 series with p < 0.05 at annual level |

None of the 40 Kyrgyz correlations passes correction for multiple tests. Across the panel, 155 of 862 do, but overlapping windows inflate that count and signs differ by country. Weak linear correlation does not rule out a role during shocks, so keep these for the ablation tests, without expecting much from them. Country GPR is excluded (2 of 28 countries), as are vehicle fleet and monthly industrial production (no usable data).

### 8. What are the most serious data limitations?

1. Recent records are provisional, and national figures are later revised up.
2. The 2025 gasoline value gap, at 0.78 of the official figure.
3. Few documented shocks, with thin coverage in 2026: Jun-Jul 2026 are absent for Kyrgyzstan itself.
4. HS 271019 mixes fuels, and it means different things across countries unless blends are added.
5. Six reporters seem to file fuels under another HS line.
6. Unexplained differences with Russian exports in 2016-2017, and no Russian data after 2021.
7. Publication lags vary from about a month to over two years.

### 9. What additional data collection is necessary?

Necessary: repeat Comtrade snapshots, the 2025 energy balance when published, and a sourced event calendar. Useful: official monthly fuel tonnage from NSC or customs, panel production and consumption data, and verified importer types. See `unresolved_issues.md`.

### 10. What methodological risks must be addressed before forecasting?

| Risk | Control |
|---|---|
| Vintage leakage: training on later-revised data that a real forecaster would not have | Store snapshots; evaluate as first released; keep the release date |
| Publication-lag leakage | As-of replay with `first_released` |
| Look-ahead cleaning: `uv_relative` and rejections use future months | Never use them as features; apply a real-time version in tests |
| Structural breaks, including the Jul 2025 gasoline shift and Apr 2024 distillate shift | Time-based validation; test training windows |
| Mixed panel distorting pooled models | Keep tier and country groups; run ablations; stratify results |
| Too few shock events for classifier evaluation | Report exceedance probabilities, use pooled events, avoid claims from single events |
| Noisy targets | Keep the next-three-month total as a target; use robust losses and scaled metrics |
| Testing many hypotheses | Fix the hypotheses in advance; correct for multiple tests |
| Gaps treated as data | Mask missing months, and never score them |
| Tuning on the final test period | Freeze settings before running it once |

## What the analysis changed

- **Seasonality is weaker than assumed.** Kyrgyz gasoline has a real pattern, highest in December and lowest in September, but HS 271019 has no clear one (p = 0.42). Median seasonal strength across the panel is 0.22.
- **Shortfall labels moved less than I warned in Phase 1.** The proposal's 11 and 8 episodes reproduce exactly from uncleaned data, and clean data give 11 and 7. The dates do shift, though, and Sep 2025 onward is in the provisional period.
- **Phase 1's "core" panel is superseded** by the stricter tiers here: 35 core series become 22 Tier 1 series.
- **Weakness of 2015-2017 is now explained in part** by mirror evidence, though the cause remains unknown.

## Deliverables

| # | Deliverable | Location |
|---|---|---|
| 1 | Dataset inventory | `reports/phase2/dataset_inventory.md` |
| 2 | Data-quality assessment | `data/research/data_quality_report.csv` |
| 3 | Coverage matrix | `data/research/country_product_coverage.csv` |
| 4 | EDA report with charts | `reports/phase2/eda_report.md` |
| 5 | Validated datasets | `data/research/` |
| 6 | Pipeline documentation | `docs/`, `README.md`, `src/research/` |
| 7 | This report | `reports/phase2/research_feasibility_report.md` |
| 8 | Unresolved issues | `reports/phase2/unresolved_issues.md` |
| Extra | Kyrgyz validation | `reports/phase2/kyrgyz_validation.md` |
