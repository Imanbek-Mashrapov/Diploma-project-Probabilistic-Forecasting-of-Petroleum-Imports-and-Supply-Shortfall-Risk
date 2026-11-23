# Missing-data policy

Missing is never replaced with zero, and target values are never interpolated. Every month in `petroleum_imports_monthly` keeps a `data_status`, and the original value stays in `import_mass_t_original`.

## Status classes

| `data_status` | Meaning | How it is identified | Treatment |
|---|---|---|---|
| `observed` | Usable mass | Mass present and passes the checks | Target |
| `mass_rejected_by_check` | Mass reported but implausible | Unit value too low, or the leading supplier's mass failed the density test | Missing target; original kept |
| `value_reported_mass_missing` | Trade happened, mass unknown | Value present, no usable mass | Missing target. Never derive mass from value |
| `no_record_in_published_month` | Reporter published that month, no record for the product | Listing shows the month; no rows for this product | Missing. Could be zero or unreported |
| `reporting_interruption` | Month inside the reporter's span not published | Absent from the listing, between its first and last months | Missing, with a mask |
| `outside_reporting_span` | Before the first or after the last published month | Outside the listing's span | Not part of the series |

## The five cases

- **Genuine zero.** Comtrade has no explicit zero-trade rows here (0 rows with value 0), so no month can be confirmed as zero. A zero-import month is also implausible for these fuels. No value is set to zero.
- **Missing observation.** Covered by the classes above. A month may be missing from the source (`reporting_interruption`) or missing because of a check (`mass_rejected_by_check`).
- **Unreported trade flow.** `no_record_in_published_month` cannot be told apart from a true zero without a mirror source. Russian mirror data help only to 2021.
- **Product not classified consistently.** This is a series-level problem, so it sits in `classification_flag`, not `data_status`: `fuel_lines_suspect` for reporters with fuels apparently under another HS line, and `271019_misses_blended_diesel` where blends are large.
- **Reporting interruption.** Short gaps such as Kyrgyzstan's Sep-Oct 2019 and Jun-Jul 2026, and long ones such as Laos in 2021.

## Rules for the modelling stage

- Targets stay missing. A missing month is left out of loss calculations and is not forecast-scored.
- Short gaps in neural input windows may be filled for inputs only, with a mask feature. Filled values must never enter a target or a score.
- Rolling features use observed months only, and they record how many were available.
- Cleaning fields that look forward, such as `uv_relative`, must not be used as features.
- Annual values must not be spread over months.
- Nothing may be imputed from World rows, unit values or other countries.

## Preservation

`data/research/transformation_log.csv` lists every operation and how the original is kept. Raw Comtrade responses are unchanged, and `tests/test_research.py` checks every stored response against its download hash.
