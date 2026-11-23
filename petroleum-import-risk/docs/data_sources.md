# Data sources

All sources were retrieved on 2 November 2026 unless stated. The energy balance was first downloaded on 1 November 2026.

| Source | Publisher | Coverage used | Frequency | Access | Location | Use |
|---|---|---|---|---|---|---|
| Comtrade final data | UN Statistics Division, <https://comtradeapi.un.org> | 2011 to Aug 2026, 43 candidates | Monthly | Free key; 500 calls a day | `data/raw/un_comtrade/` | Target, suppliers |
| Comtrade annual, mirror, all-goods pulls | Same | 2015-2025 | Annual, monthly | Free key | `annual_world/`, `mirror_russia/`, `kgz_all_goods/` | Validation |
| Comtrade reference files | Same | HS2007-HS2022 | Static | Public | `data/raw/reference/` | Codes |
| Europe Brent, WTI spot | US EIA, <https://www.eia.gov/dnav/pet/> | To Sep 2026 | Monthly average | Public | `data/raw/oil_prices/` | Indicator |
| Geopolitical Risk index | Caldara and Iacoviello, <https://www.matteoiacoviello.com/gpr.htm> | To Sep 2026 | Monthly | Public | `data/raw/gpr/` | Indicator |
| Exchange rates | BIS, WS_XRU, <https://stats.bis.org> | To Sep 2026 | Monthly average | Public | `data/raw/fx/` | Indicator |
| CPI, all items | IMF, <https://api.imf.org> | 40 countries, to 2026 | Monthly | Public | `data/raw/macroeconomic/` | Indicator |
| GDP, population, industry share, inflation | World Bank WDI | To 2025 | Annual | Public | `data/raw/macroeconomic/` | Annual covariate |
| Fuel and Energy Balance, 2024 edition | National Statistical Committee, <https://stat.gov.kg/ru/publications/toplivno-energeticheskij-balans/> | 1999, 2005-2024 | Annual | Public | `data/raw/energy_balance/` | Validation, dependency |
| Table 4.03.00.12, imports of main commodities | Same, <https://stat.gov.kg/ru/statistics/vneshneekonomicheskaya-deyatelnost/> | 1994-2025 | Annual | Public | `data/raw/official_kg/` | Validation |
| Export-import operations, express reports | Same | Monthly, 2024 to Aug 2026; 20 reports | Monthly | Public | `data/raw/official_kg/` | Vintage check |

## Not used

| Source | Reason |
|---|---|
| EIA API | Needs a key, and the public files cover the same series |
| NBKR | BIS supplies the same exchange rates with one format across countries |
| JODI | No Kyrgyz, Uzbek, Turkmen or Mongolian data, as found in the pilot |
| Industrial production | No consistent monthly source across the panel |
| Press articles | Used only as secondary quotes in `kyrgyz_validation.md`, never as data |

## Comtrade notes

- Authentication: header `Ocp-Apim-Subscription-Key`.
- `isReported`, `isAggregate` and `legacyEstimationFlag` were not defined in the public documentation found, so they are carried but not relied upon.
- Records may be revised. Each pull is a dated snapshot.
