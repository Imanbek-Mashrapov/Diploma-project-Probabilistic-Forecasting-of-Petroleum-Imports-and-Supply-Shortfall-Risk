# Section 2. Aim and Objectives

> **AI-ASSISTED DRAFT (working material, not final text).** Drafted by an AI research assistant from the approved proposal, `.claude/research_decisions.md` and the Phase 3 outputs. The student must rewrite it in their own words, read every cited work, and be able to defend each statement. The faculty caps plagiarism plus AI-generated content at 30%. Citation style: APA 7, as in the proposal. Project numbers come only from `petroleum-import-risk/reports/phase3/results.md`; detailed results belong in Section 4.

## 2.1 Aim

The aim is to determine whether monthly physical imports of refined petroleum in landlocked economies, and the risk of an import-shortfall signal, can be forecast out of sample with calibrated uncertainty using only information public on each forecast date. It also asks under what conditions globally trained neural models improve on gradient boosting and on simple baselines. Kyrgyzstan is the detailed case within a panel of landlocked economies.

Terminology used throughout: the study forecasts *recorded customs import mass* (tonnes). Its "import-shortfall signal" is a volume-based proxy: a three-month mean of recorded imports well below its own seasonal baseline. A signal is not a confirmed physical shortage, because it does not observe stocks, consumption, domestic refining or retail availability.

## 2.2 Objectives

The six objectives are those of the approved proposal (Section 1.3 of the proposal). The study sets out to:

1. build an audited, reproducible monthly panel of refined-fuel imports for landlocked economies from UN Comtrade, validated against official national sources;
2. define a supply-shortfall target that separates supply stress from weak demand;
3. compare baseline, tree-based and global neural models under rolling-origin evaluation that respects publication lags;
4. measure, through ablation, the value of cross-country pooling, supplier structure and shock information;
5. calibrate the forecast distributions and evaluate the resulting shortfall warnings against concentration-based screening; and
6. deliver a working prototype risk monitor for research and planning use.

After the Phase 0 review (2026-11-25) the student approved calling the outcome of Objective 2 an "import-shortfall signal" (decision R2). The objective wording above is kept verbatim; the renamed outcome is recorded as a deviation (Section 2.7).

## 2.3 Research questions and hypotheses

These were fixed before any model was trained. Each hypothesis is tested at the 5% level with Holm (1979) correction. A result that does not support a hypothesis is reported with the same prominence as one that does.

| RQ | Research question (proposal, verbatim) | Hypothesis (proposal, verbatim) |
|---|---|---|
| RQ1 | Does training a single model across countries improve forecasts for Kyrgyzstan compared with local models and the seasonal naive benchmark? | H1. Global models reduce the Kyrgyz mean absolute scaled error (MASE) by at least 5% relative to the best local model at a three-month horizon. |
| RQ2 | Do global neural models outperform gradient boosting, in normal periods and in shock periods? | H2. Global neural models do not outperform LightGBM overall, but do outperform it in documented shock windows. |
| RQ3 | Do supplier structure and documented shock information add predictive value beyond a series' own history? | H3. Adding supplier and shock information reduces pinball loss by at least 3% for series with high supplier dependence. |
| RQ4 | Can calibrated probabilistic forecasts warn of supply shortfalls better than screening by supplier concentration? | H4. Forecast-based shortfall probability achieves a higher PR-AUC, and higher recall at a fixed alert budget, than ranking by the Herfindahl-Hirschman index (HHI). |

The hypotheses are not reworded after seeing results. Instead, the way verdicts are *reported* follows the approved decisions (R4 and the 2026-11-25 student decision on H4). H1 is reported as not supported, because its 95% interval (−26.0% to +1.5%) excludes the pre-specified 5% gain, while whether global training is actually worse stays open with only two series; H2 receives a separate verdict for each half; H3 is reported as inconclusive; and H4 carries three qualifications (not significant against simple forecasts, not significant on import-dominant series, and an effective sample of 28 episodes). H4 is framed as an extension of Kwon and Jeong (2026), who compared dynamic trade-flow indicators with import concentration for a maritime economy.

## 2.4 Scope and delimitations

- **Commodities.** The two forecast targets are the gasoline proxy (HS 271011 + 271012) and distillates including blends (HS 271019 + 271020). "Distillates" is never read as "diesel": six-digit codes cannot separate diesel, jet fuel or fuel oil. LPG is described only. Crude oil (HS 2709) is context and is never combined with refined products. The 2710 heading is a reconciliation check only.
- **Panel.** Landlocked economies, from the UN list of landlocked developing countries plus European landlocked states with reliable reporting (`config/countries.csv`, 43 candidates). "Landlocked" is a sampling frame: there is no non-landlocked control group, so the study makes no comparative claim about landlocked status. Tier 1 (22 series, 13 countries, 3,021 observations) is evaluated; Tiers 1 and 2 (44 series, 22 countries, 5,549 observations) train the global models (`reports/phase2/research_feasibility_report.md`). Kyrgyzstan is the only Central Asian Tier 1 country.
- **Period.** Data from January 2015 to August 2026 (one Comtrade snapshot, 2026-11-02, dataset v1.0.0). Rolling forecast origins run from January 2023 to July 2026 (43 origins); origins from January 2021 to December 2022 serve only for calibration.
- **Out of scope.** Consumption, stocks, refinery runs, transit and re-exports, informal trade and retail availability are not observed. Import dependency (production, consumption, stocks) is known only for Kyrgyzstan and only annually. No causal claims are made.

## 2.5 Success criteria

**Set retrospectively (after results were seen); require supervisor approval.** The proposal fixed the hypotheses but not a formal criterion for each objective. The criteria below were proposed by the drafting assistant after the Phase 3 results existed and must be confirmed by the student and supervisor before they are used to judge any objective.

| Objective | Success criterion |
|---|---|
| 1. Panel | Documented cleaning rules; absent months never filled; raw responses stored with hashes; agreement with an official national source reported; series tiers stated. |
| 2. Target | A pre-specified rule, checked against a sourced event calendar, whose agreement with documented supply events and its ability to separate supply stress from weak demand are reported, whatever they show. |
| 3. Comparison | All models scored on the same origins and cases with data visible at each origin; the same fixed budget for each learned model; at least five seeds for neural models. Outcome tied to the pre-registered H1 and H2 tests (verdicts as reported, whatever they show). |
| 4. Ablation | Each planned variant run one at a time with the model family fixed; effect sizes with intervals reported. Outcome tied to the pre-registered H3 test (verdict as reported). |
| 5. Calibration and warnings | Interval coverage within `[TOLERANCE TO BE AGREED WITH SUPERVISOR, e.g. ±5 percentage points]` of the 80% and 95% nominal levels; shortfall probabilities scored with PR-AUC, Brier score and recall at a fixed alert budget, against HHI and against simple forecasts. Outcome tied to the pre-registered H4 test (verdict as reported). |
| 6. Prototype | The monitor runs from stored model output, its interfaces are documented and tested, and its wording does not exceed the evidence. |

## 2.6 Objectives versus outcomes

Status labels: *met*, *partly met*, *not met*, *planned*. Evidence paths are relative to `petroleum-import-risk/`.

| # | Status | Evidence | Deviation from the proposal |
|---|---|---|---|
| 1 | Largely met (v1.0); supervisor sign-off of cleaning and tier rules still pending. Three open items: tier selection used the test block, importer types are unsourced, national validation exists only for Kyrgyzstan | `reports/phase2/research_feasibility_report.md`; `data/research/VERSION.json`; `docs/decision_log.md` | Tier selection used the full 2015-2026 window, which includes the test block. Importer types are hand-assigned and unsourced. The validation against an official national source covers Kyrgyzstan only. |
| 2 | **Defined, not validated** (partly met) | `reports/phase2/event_validation.md` (labels fired in 13 of 33 documented supply events); `reports/phase3/results.md` (supply-side label: PR-AUC 0.098, p = 0.113) | The proposal's wording ("separates supply stress from weak demand") is not demonstrated. The outcome is renamed "import-shortfall signal" (R2). |
| 3 | Partly met | `reports/phase3/results.md` (accuracy tables); `data/modeling/forecasts_raw.parquet` | Nine models run. Random forest, XGBoost, TCN, full N-BEATS and TFT were not run. Hyperparameters are fixed defaults, not tuned. The design is pseudo-real-time on the latest vintage, not first-release data. |
| 4 | Partly met | `reports/phase3/results.md` (ablation table) | The eight planned variants have a run, plus three extra. SHAP was not computed. The strict-importer variant rests on unsourced types. H3 is inconclusive. |
| 5 | Partly met | `reports/phase3/results.md` (calibration, H4, exploratory R1-R2); `reports/phase3/tables/shortfall_calibration.csv` | Conformal calibration done. Recalibration of probabilities was added post hoc. H4 beats HHI but not simple forecasts, and not on import-dominant series. Lead time was not computed. |
| 6 | Partly met: the prototype works locally, but its dashboard wording is being revised to R2 terminology; public deployment planned | `src/monitor/`; `docker-compose.yml`; `tests/`; `.claude/phase0_audit.md` item 2.4 | Monitor wording still to be aligned with R2 and R7 (revision in progress). No public deployment yet. |

Objectives 2 to 5 are therefore not fully met in the sense of the proposal. The thesis reports them as partly met rather than adjusting the objectives after the fact.

## 2.7 Deviations from the proposal

| Item | Proposal | What was done | Consequence |
|---|---|---|---|
| Data vintage | Evaluate on first-release data | One snapshot (2026-11-02) with latest values; availability emulated by each record's `first_released` date | Design is "pseudo-real-time"; Kyrgyz 2025-26 claims carry a warning (R3). A second snapshot (2026-11-25) measures revisions only. |
| Models | Random forest, XGBoost, GRU, TCN, N-BEATS, TFT | Naive, seasonal naive, 12-month mean, ETS, SARIMA, LightGBM (local, global), residual MLP, GRU | The neural arm is small; H2 speaks only about these models. |
| Robustness | COVID exclusion, with/without 2015-17, Bai-Perron breaks (Bai & Perron, 2003), SHAP (Lundberg & Lee, 2017), lead time | Not run | Declared as open items (R6); to be run or kept as limitations. |
| Tuning | Tune before each test block | Fixed defaults, same budget for all learned models | Neural models may be under-tuned. |
| Recalibration | Not planned | Platt scaling added on 2026-11-25 after test results were seen | Exploratory only; H4 is tested on the raw probability. |
| Outcome name | "Supply shortfall" | "Import-shortfall signal" | Reflects what customs mass can show (R2). |
| Tier selection | Not specified | Tiers chosen on the full window | Possible selection bias; a pre-2023 re-screen is planned. |
| Cleaning rule | Not specified | Unit-value rule uses a centred 13-month median | Sensitivity run planned (R5). |
| Post-hoc exploratory analyses | Not planned | R1 (H4 against simple-forecast benchmarks) and R2 (H4 by import-dominance strata) were added after the primary results were seen; R3 (second snapshot, 2026-11-25) was added to measure revisions | Exploratory only; the pre-specified H4 verdict is unchanged. Labelled exploratory wherever reported. |
| Error analysis | Error analysis by country, season and supplier dependence (`proposal/content.py`, around line 283) | Not done | Open item; to be run or kept as a limitation. |
| Graph-attention arm | Optional graph-attention model | Not run | H2 speaks only about the MLP and GRU. |
| H1 comparator | Best local model | The best local model was chosen on the test block (local LightGBM) | Tilts the H1 interval slightly toward the local model; the "not supported" verdict stands as pre-specified. |

---

## References (APA 7; as listed in the approved proposal or in `section1_literature_review.md`)

Bai, J., & Perron, P. (2003). Computation and analysis of multiple structural change models. *Journal of Applied Econometrics, 18*(1), 1-22. https://doi.org/10.1002/jae.659

Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics, 6*(2), 65-70. [UNVERIFIED: not checked against Crossref, no DOI in the proposal list]

Kwon, M., & Jeong, D. (2026). Dynamic trade flow indicators outperform import concentration in supply disruption early warning for a maritime-dependent economy. *Frontiers in Marine Science, 13*, 1956773. https://doi.org/10.3389/fmars.2026.1956773

Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. In *Advances in Neural Information Processing Systems* (Vol. 30).

*Verification note:* the entries are copied from the existing reference lists; this draft did not re-resolve their DOIs.
