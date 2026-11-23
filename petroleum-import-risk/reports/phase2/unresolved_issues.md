# Unresolved data issues and next actions

Ordered by importance. Full issue list: `data/research/data_quality_report.csv`.

## Must do before forecasting

| # | Issue | Next action | Who |
|---|---|---|---|
| 1 | Recent Kyrgyz records are first-release values, and later national figures run about 9% higher at the median for all goods. The effect on fuel is unknown | Take a new Comtrade snapshot at least quarterly. Evaluate on first-release data, and report 2025-2026 with a warning | Student, automated |
| 2 | Late-2025 gasoline: Comtrade value is 0.78 of the official value | Reconcile when the 2025 energy balance is published, probably around early 2027 | Student |
| 3 | Cleaning rules and tier thresholds are judgment calls | Supervisor review, then freeze them before any model runs | Supervisor |
| 4 | Provisional importer types were set by hand | Verify each country against a named source, or drop the strict-importer ablation | Student |
| 5 | Shortfall labels are descriptive and not checked against events | Build a sourced event list, and label only after that | Student |

## Should do

| # | Issue | Next action |
|---|---|---|
| 6 | Official Kyrgyz tonnage by fuel, monthly, was not found | Ask NSC or the Customs Service for monthly fuel imports by mass, including Jun-Jul 2026 |
| 7 | 2016-2017 Russian gasoline exports are about three times Kyrgyz imports, unexplained | Report results with and without 2015-2017. Ask NSC or customs whether transit explains it |
| 8 | Meaning of partner (origin, consignment or trader) is unconfirmed | Check the UN IMTS guidance and each reporter's metadata |
| 9 | `isReported`, `isAggregate`, `legacyEstimationFlag` are undocumented | Ask Comtrade support |
| 10 | Press figures quoted from NSC could not be matched | Obtain the original NSC foreign trade reports |
| 11 | Monthly and annual Comtrade disagree for some reporter-years, such as Laos 2015-2016, Zimbabwe 2020, Luxembourg gasoline 2022 | Keep flagged. Consider excluding those years in robustness checks |
| 12 | Hungary: six-digit lines differ from the heading in many months | Investigate before relying on Hungarian distillates |

## Accepted limits

- HS six digits cannot separate diesel, jet fuel, kerosene, fuel oil or lubricants.
- No Russian mirror data after 2021.
- No monthly data for Afghanistan, Central African Republic, Chad, Mali, Nepal, San Marino, Tajikistan or Turkmenistan.
- No confirmed genuine zero months.
- Import dependency is available only for Kyrgyzstan.
- Only 1 Central Asian country reaches Tier 1.

## Data collection still possible

| Data | Why | Effort |
|---|---|---|
| Comtrade snapshots over time | Measures revisions directly | Low |
| 2025 energy balance | Validates the 2025 shock | Waiting |
| Production and consumption for panel countries (UN Energy Statistics or IEA) | Allows import dependency beyond Kyrgyzstan | Medium; access to be checked |
| Sourced calendar of export restrictions | Needed for shock features and RQ3 | Medium |
| Customs data by HS8/10 | Would separate diesel and gasoline | Depends on official access |
