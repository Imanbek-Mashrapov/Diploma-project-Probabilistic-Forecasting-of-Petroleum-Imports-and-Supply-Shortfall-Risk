# Processing methodology

Phase 1 collected raw data and built working datasets. Phase 2 validates them and builds the research datasets in `data/research/`. No predictive model is fitted anywhere.

## Flow

```text
data/raw/                raw responses, never modified
   |  python run.py process
data/analytical/         Phase 1 datasets
   |  python run.py phase2
data/research/           research datasets, versioned
reports/phase2/          inventory, EDA, validation, feasibility
```

## Mass

1. Use net weight when it is positive.
2. Otherwise use `qty` or `altQty` only when the unit is literally kg.
3. Where a volume is reported on the same row, the implied density must be physically possible. Bounds in kg/L: gasoline 0.68-0.80, LPG 0.48-0.62, others 0.60-1.05.
4. Rows that fail keep their volume. A labelled estimate (`volume × the median density the reporter shows on rows with true net weight`) is stored apart and never enters `import_mass_t`.
5. Tonnes = kg / 1000. Litres and value are never converted into mass.

## Aggregation

- Totals are the sum of partner rows. World rows are a check, and a labelled fallback where no partner rows exist. The two are never added together.
- The 2710 heading is not summed with its six-digit lines, and it is excluded from the bilateral dataset.
- Crude is never combined with refined products.
- Requests use classic mode with totals for second partner, transport mode and customs procedure, so breakdown rows cannot double count.
- Overlapping downloads are de-duplicated on the natural key, keeping the latest retrieval.

## Product groups

| Group | HS | Note |
|---|---|---|
| `gasoline` | 271011 (HS2007), 271012 (HS2012 on) | Proxy for motor gasoline; also holds naphtha and blending components. Oils with biodiesel left this line in HS2012 |
| `middle_heavy` | 271019 | Diesel, kerosene, jet fuel, fuel oil and lubricants together |
| `middle_incl_blends` | 271019 + 271020 | Comparable across reporters, because blended diesel goes to 271020. **Main distillate definition** |
| `biodiesel_blend` | 271020 | Context |
| `lpg` | 271112, 271113, 271119 | Descriptive; 271119 may hold other gases |
| `crude` | 2709 | Context |
| `total_2710` | 2710 | Check only |

## Quality checks at month level

- Unit value is compared with a fixed plausible band and with its own centred 13-month median after Brent deflation.
- Too low means mass is overstated, so mass is removed and the original kept. Too high usually means a bad value, so it is only flagged.
- Outliers on log mass (|z| above 4) are flagged and kept, because shocks are the object of study.
- These checks use later months, so they are for cleaning history only and must not be repeated unchanged in real time.

## Supplier concentration

For each country, product and month, with `s_i` a supplier's share of import mass:

```text
HHI = Σ s_i²
```

Also reported: largest share, top-three share, active suppliers, Russia's share, and `hhi_12m`, which pools mass over a trailing 12 months so one thin month cannot dominate. It requires at least 6 observed months. Reporters listed as their own partner, bunkers and special categories are excluded. Unallocated "nes" partners remain as one partner, with `nes_share` reported.

## Import dependency

Net import dependency = (imports - exports) / domestic use, annual, from the energy balance, for Kyrgyzstan only. Concentration and dependency measure different things, and no country outside Kyrgyzstan is labelled import-dependent here.

## Country-product tiers

Rules are in `src/research/coverage.py`, and every candidate appears in `country_product_coverage.csv`.

| Tier | Requirements |
|---|---|
| 1, main experiment | Target product; at least 120 observed months; at least 85% coverage of the 140-month window; no gap above 6 months; reaches June 2025 or later; at least 84 supplier months; median of at least 100 t; exports under half of imports; no classification flag |
| 2, usable with limits | At least 84 observed months and supplier months; median of at least 100 t; no suspected fuel mislabelling; LPG caps here |
| 3, unsuitable | Everything else, with a stated reason |

These replace the Phase 1 "core" definition because they add recency and gap rules.

## Exploratory methods

- **Seasonality:** month-of-year index and Kruskal-Wallis test. STL (period 12, robust) on the longest gap-free stretch only.
- **Breaks:** PELT with L2 cost on observed log mass, minimum segment 6 months, penalty 3 log(n) σ², σ from first differences. Gaps are skipped, not filled.
- **Scale:** mass per person, using the latest World Bank population.
- **Volatility:** robust sd of monthly log change, between adjacent months only.
- **Correlation:** Spearman on year-on-year log changes at leads of 0, 1, 3 and 6 months, with Benjamini-Hochberg correction. Overlapping windows make p-values too small.

## Reproducing

```bash
.venv/Scripts/python run.py validation_pull
```
```bash
.venv/Scripts/python run.py phase2
```
```bash
.venv/Scripts/python -m pytest -q tests
```

`data/research/VERSION.json` records the snapshot, window and a hash of each output.
