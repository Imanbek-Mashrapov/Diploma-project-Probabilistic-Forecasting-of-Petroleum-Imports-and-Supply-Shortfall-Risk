# Decision log

Every change to cleaning rules, thresholds, targets, evaluation or model settings gets a dated entry with its reason.
Settings live in `config/settings.yaml`; this file records why they are what they are.

## 2026-11-24: rules v1.0 frozen for Phase 3

**Status:** frozen provisionally. The supervisor has not yet reviewed the cleaning rules and tier thresholds (open issue 3 in
`reports/phase2/unresolved_issues.md`). Any change after that review gets a new entry and a new `modeling.rules_version`,
and all Phase 3 stages are rerun.

### Data and cleaning (unchanged from Phase 2)
- Cleaning, unit-value checks and tier rules are exactly those in `docs/methodology.md` and the `screening` and `quality`
  blocks of `config/settings.yaml`, dataset version 1.0.0, snapshot 2026-11-02.
- Targets: gasoline proxy (`gasoline`, HS 271011+271012) and distillates (`middle_incl_blends`, HS 271019+271020).
- Series: the 44 Tier 1 and Tier 2 series from `data/research/country_product_coverage.csv` train the global models;
  the 22 Tier 1 series are evaluated.

### As-of rule
- An observation is visible at origin month M only if its `first_released` is on or before the last day of M.
  Every target row has a release date, so the median-lag fallback in the proposal was never needed.
- `first_released` comes from the current record. For months that were revised, it is the release date of the revision,
  so the rule is conservative (it can hide data that existed earlier in another form, never the reverse). The values
  themselves are the latest vintage, so revision effects are not yet measured; this needs a second snapshot.
- External indicators are shifted by release delays: Brent, GPR and Russia GPR 1 month; exchange rates and CPI 2 months.
- Shock events enter features only from `announced_date` (or `start_date` when no announcement date exists), and only
  while known to be active at the origin. The exposure share used to decide which countries an "EXPOSED" event touches
  is computed from the 12 months before the event, some of which may not have been released at announcement. The effect
  is limited to which series get a shock feature, not its timing.
- The published `uv_relative` uses a centred 13-month median, which looks into the future. It is never a feature. The
  model uses `uv_asof`: the latest visible Brent-deflated unit value against the median of the last 12 visible months.

### Targets and tasks
- Targets are `log1p(mass) − level`, where the level is the mean log mass of the last 12 visible months (at least 6).
  A series is skipped at an origin if its last visible month is more than 36 months old.
- Horizons count from the origin month: months 1, 3 and 6 after it, plus the mean of months 1-3 (`sum3`). Because of
  publication lag, a horizon-1 forecast is usually 3-4 months past the last visible observation. This is the honest,
  real-time definition.
- Shortfall probability uses the `sum3` forecast and the as-of baseline (same three calendar months over the previous three
  years, visible data only). Realised labels use the final data, as in `src/research/events.py`.

### Evaluation
- Origins 2021-01 to 2022-12 feed only the conformal step and the choice between neural candidates.
- Evaluated origins: 2023-01 to the last origin with released targets.
- Learned global models are refitted every 3 origins; between refits the older model is reused.
- Pre-specified comparisons: H1 uses LightGBM global against the best local model *chosen on the test block*, which favours
  the local side and makes H1 harder to support. H2 uses the neural model with the lower calibration-period MASE.
  H3 uses series whose largest-supplier share had a median ≥0.70 before 2023.
- Shortfall labels are weak (Phase 2: 39% of documented supply events triggered a label, and 130 of 171 label
  episodes have no documented event). H4 is therefore reported for the volume label (primary), thresholds 0.70 and 0.80,
  the supply-side label, and an event-calendar label.

### Models (deviations from the proposal)
- Run: naive, seasonal naive, 12-month mean, ETS (latest unbroken run of at least 36 months), SARIMA(0,1,1)(0,1,1)12 on log
  mass (handles gaps), LightGBM local and global, residual MLP (N-BEATS-style block stack) and GRU, both with a country
  embedding and averaged over 5 seeds.
- Not run in v1.0: random forest, XGBoost, TCN, the full N-BEATS and the Temporal Fusion Transformer. LightGBM covers the
  boosted-tree arm. The proposal allowed the TFT to be dropped. This is a scope decision to report as a limitation.
- Hyperparameters are fixed defaults (`modeling.lightgbm`, `modeling.neural`), not tuned. The same budget applies to every
  learned model.

## 2026-11-25: post-hoc recalibration of shortfall probabilities

**Why:** the v1.0 evaluation showed that the shortfall probabilities rank cases well (H4) but overstate risk about
twofold. The Brier score (0.081) was worse than a constant base-rate forecast (0.069).

**What:** Platt scaling (`modeling.recalibration`): logistic regression of the realised label on logit(p), fitted per
model and threshold on the previous 24 origins whose outcome had been released by the origin, pooled across all 44
series, and refitted every origin ("rolling"). It needs at least 10 shortfalls and 10 non-shortfalls, otherwise the value
is left missing. A sensitivity variant fits the map once at the first test origin (January 2023) and keeps it ("fixed").

**Status:** an extension decided *after* seeing test results. It is not part of the pre-specified hypotheses: H4 is
still tested on the raw probability, and the recalibrated rows are reported as exploratory. Isotonic regression was
not tried, to avoid choosing among methods on the test block.

**Result (2026-11-25 run):** mean probability 0.171 (raw), 0.100 (rolling) and 0.140 (fixed), against a base rate of 0.074.
The Brier score is 0.0806, 0.0697 and 0.0688, against a base-rate Brier of 0.0688. The overstatement is removed, but the level
has no skill beyond the base rate. The rolling map is monotone within each origin, so each month's ranking is unchanged; refitting
changes the scale between origins and lowers the pooled PR-AUC (0.190 to 0.137). The fixed map keeps the PR-AUC at 0.190.

**Monitor:** shows the rolling recalibrated probability, which is calibrated in level and has the same within-month
ranking. The raw value is kept as `p_shortfall_raw`.
