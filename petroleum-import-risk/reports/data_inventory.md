# Data inventory

Snapshot `2026-11-02`.

| dataset | source | granularity | period | coverage | rows | access |
|---|---|---|---|---|---|---|
| Dataset A bilateral | UN Comtrade | HS6 x partner x month x flow | 201101-202608 | 28 reporters | 416267 | Public preview; key for full panel |
| Dataset B monthly | UN Comtrade | country x product x month x flow | 201001-202608 | 36 reporters | 62485 | Derived |
| dataset_c_global_monthly | EIA, Caldara-Iacoviello | global x month | 201001-202609 | global | 201 | Public files |
| dataset_c_country_monthly | BIS, IMF, Caldara-Iacoviello | country x month | 201001-202610 | 41 countries | 8151 | Public API/files |
| dataset_c_country_annual | World Bank WDI | country x year (annual, not interpolated) | 2010-2025 | 42 countries | 672 | Public API |
| dataset_d_integrated | Datasets B and C, supplier metrics | eligible series x month, same-month values | 201501-202608 | 22 countries | 5698 | Derived |
| Kyrgyz Fuel and Energy Balance | National Statistical Committee | fuel x year (annual, kt) | 1999-2024 | Kyrgyzstan | 376 | Public XLSX, 2024 edition |

