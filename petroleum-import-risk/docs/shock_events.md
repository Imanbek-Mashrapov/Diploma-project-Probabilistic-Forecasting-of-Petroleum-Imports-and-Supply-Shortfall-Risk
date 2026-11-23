# Shock-event calendar

`config/shock_events.csv` lists documented supply shocks, policy measures and demand shocks that could move refined-fuel imports in the panel countries from 2015 to November 2026. Each event cites at least one public source. The feasibility report required this list before any shortfall label is used as a validation target.

`run.py events` validates the file, then compares it with the descriptive shortfall labels. Output goes to `reports/phase2/event_validation.md` and two tables in `reports/phase2/tables/`.

## What the calendar is for

- **Checking the labels.** Do labels fire during documented supply events, and does each label episode have an event behind it?
- **Stratified evaluation.** Shock windows for reporting forecast error separately in normal and disrupted periods.
- **As-of features later.** `announced_date` records when the event became public. A model may only use an event from that date on.

It is not a ground-truth list of every shortage. Coverage depends on English and Russian-language press, so small markets are under-covered. A missing event does not prove that nothing happened.

## Columns

| Column | Meaning |
|---|---|
| `event_id` | Unique key: `<affected or origin>_<year>_<short name>` |
| `affected_iso3` | Semicolon list of ISO3 codes; `ALL` for global shocks; `EXPOSED` for every panel country whose Russian supplier share was at least 25% in the 12 months before the start |
| `exempt_iso3` | Countries excluded from an `EXPOSED` event, such as EAEU members under intergovernmental agreements |
| `origin_iso3` | Country that caused the event, if any. `EXPOSED` needs an origin with supplier shares in the data; only Russia has them |
| `product_scope` | `gasoline`, `distillates`, `all_fuels` or `crude`. Crude events touch refiners and are listed for context only |
| `event_type` | Mechanism: export restriction, transit disruption, supply disruption, quota limit, logistics, FX shortage, price control, sanctions, refinery outage, demand shock, conflict |
| `role` | What the event predicts for imports, below |
| `start_date`, `end_date` | Event dates. Empty `end_date` means still running at the last check |
| `end_basis` | `announced` (scheduled end), `reported` (end reported), `last_report` (last report found), `assumed` (coder's estimate), `open` |
| `date_precision` | `day` or `month`. Month-precision dates use the first or last day of the month |
| `announced_date` | First public date, where known |
| `confidence` | See below |
| `source1`-`source3` | Publisher and https link |

### Roles

| Role | Expected effect on the affected country's imports | Counts as explaining a shortfall label |
|---|---|---|
| `supply_shortfall` | Fall, from the supply side | Yes |
| `demand_shock` | Fall, from lower demand | Yes, as demand |
| `import_surge` | Rise, because domestic refining is cut | No |
| `context` | Unclear: price shocks, supplier switches, policy responses, crude-only events | No |

### Confidence

- **high**: two or more independent sources agree on the dates, or a primary official source.
- **medium**: one reputable source, or sources that disagree on dates or scope.
- **low**: indirect evidence only, such as a single press report of a risk rather than a shortage.

## Coding rules

1. Code an event only if a source describes it. Do not infer events from the import data.
2. Prefer official sources, then wire services and trade press, then national press.
3. Record disagreements between sources in `notes` and lower the confidence.
4. Split an event when its terms change materially, as with the 2024 Russian ban suspended from 20 May to 31 July.
5. Keep EAEU exemptions explicit. Russian bans formally excluded Kyrgyzstan, Kazakhstan, Armenia and Belarus, but deliveries to Kyrgyzstan still fell in 2025-2026, which is coded as a separate Kyrgyz event.
6. Do not edit an event to make it match a label.

## How the comparison works

The label rule is the one in the paper: a month is flagged when the trailing three-month mass falls below 75% of the mean of the same three months in the previous three years. The supply-side variant also needs the three-month mean of `uv_relative` above 1.

An event window runs from the start month to two months after the end month, because a three-month sum still reflects the event for two months. Open events run to the last month with data.

## First results (snapshot 2026-11-02, 37 events)

- Supply events with data cover 33 event-series pairs. The label fired in 13 of them (39%).
- Of 171 label episodes in the 44 eligible series, 17 overlap a supply event, 24 overlap the COVID-19 demand shock, and 130 have no documented supply or demand event.
- The supply-side unit-value check does not separate them: 51% of months pass it in episodes with a supply event, and 59% in episodes without one.
- Labels fire where the supply shock was large and the country depended on the supplier: Azerbaijani gasoline during each Russian ban, Uzbek diesel in 2023 and 2025-2026, Swiss fuels in the 2022 Rhine low water, Hungary in late 2022 and Bolivia from late 2024.
- Labels miss several well-documented shortages: Laos 2021-2022, Zimbabwe 2018-2019, Paraguay 2024 and the 2018 Rhine low water. Shortages driven by foreign-exchange rationing often show up as queues and prices rather than lower monthly tonnage.
- For Kyrgyzstan, 1 of 18 episodes has a supply event behind it (gasoline, Sep-Dec 2025). Two more fall in the COVID-19 window. The 2026 crisis cannot be tested, because Comtrade has no Kyrgyz data for June and July 2026.

### Data problem found on the way

Burundi gasoline imports in 2016 are about 5 tonnes a month, against several thousand in 2015 and 2017. This looks like a unit error in the source. It makes Burundi's 2017 ratios meaningless, and the cleaning rules did not catch it.

## Implications for the shortfall target

1. Do not train or evaluate a classifier on these labels as ground truth. Most episodes have no documented cause, and many documented shortages leave no label.
2. Keep the main risk output as in the paper: the probability, from the forecast distribution, that next months' mass falls below 75% of its seasonal baseline. Evaluate it as a probabilistic forecast (calibration, Brier score), not as event detection.
3. Use the calendar for stratified error reporting (shock windows) and for case studies, including Kyrgyzstan 2025-2026.
4. Drop the unit-value supply-side filter or redesign it. In its current form it does not discriminate.
5. Any alert evaluation against events (PR-AUC, recall at a fixed alert budget) should pool supply events across the panel and report the small number of events with the result.

These are proposals for the supervisor to approve before the protocol is frozen.

## Maintenance

- Recheck open events at each new Comtrade snapshot.
- Add events found later with their source, and rerun `run.py events`.
- Events not yet coded: further Druzhba halts in March and August 2026, Armenia's LPG supply problems at Upper Lars, and Burkina Faso convoy attacks, where no fuel-specific source was found.
