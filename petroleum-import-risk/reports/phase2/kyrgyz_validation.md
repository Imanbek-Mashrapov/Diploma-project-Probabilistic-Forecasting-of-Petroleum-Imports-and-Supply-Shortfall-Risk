# Kyrgyz validation

Comtrade compared with official Kyrgyz sources. Differences are investigated, not forced to match. Monthly official fuel statistics were not found, so nothing here is monthly by product, and no monthly official series was constructed.

## Sources compared

| Source | Product definition | Period | Unit | Compatibility |
|---|---|---|---|---|
| UN Comtrade, Kyrgyz reporter | HS 271012 (+271011); HS 271019 | Monthly, 2015 to Aug 2026 | kg net weight; USD | Base series |
| Fuel and Energy Balance, NSC, 2024 edition | Motor gasoline; diesel; fuel oil | Annual, to 2024 | Thousand tonnes | Gasoline is close. HS 271019 is wider than diesel plus fuel oil, as it also holds kerosene and lubricants |
| NSC table 4.03.00.12, import of main commodities | Motor gasoline; diesel; kerosene; liquefied gas | Annual, to 2025 | Thousand USD, CIF | Value only. Comparable for gasoline; 271019 also holds fuel oil and lubricants |
| NSC monthly express reports | All goods, no product detail | Monthly, 2024 to Aug 2026 | USD million | All-goods level only, so it tests vintages, not fuels |
| Press quotes of NSC trade reports | Undefined "fuels and lubricants"; motor gasoline | 2023; Jan-Feb 2025 | Thousand tonnes, USD | Secondary. Originals were not found |

The balance has no 2025 edition yet. NSC tables found give values, not tonnes, by commodity.

## Mass against the energy balance

Mean absolute gasoline difference: 4.5% over complete years (2015, 2018, 2020, 2021, 2022, 2023, 2024) and 3.7% from 2018. Years with fewer than 12 observed months are not valid comparisons. `gas_ct_with_volume_est_kt` adds the labelled litre-based estimate for Oct-Nov 2017, for this comparison only.

| year | gas_months_observed | gas_ct_kt | gas_ct_with_volume_est_kt | gas_teb_kt | gas_mass_ratio | gas_mass_ratio_with_estimate | mid_months_observed | mid_ct_kt | diesel_teb_kt | fuel_oil_teb_kt | mid_to_diesel_plus_fuel_oil |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2015 | 12 | 566.23 | 566.23 | 625.30 | 0.91 | 0.91 | 10 | 621.78 | 514.90 | 205.70 | 0.86 |
| 2016 | 11 | 381.25 | 381.25 | 532.90 | 0.72 | 0.72 | 12 | 552.70 | 347.40 | 33.30 | 1.45 |
| 2017 | 10 | 384.28 | 505.70 | 468.50 | 0.82 | 1.08 | 12 | 736.25 | 541.30 | 76.20 | 1.19 |
| 2018 | 12 | 642.16 | 642.16 | 632.20 | 1.02 | 1.02 | 12 | 816.75 | 706.10 | 13.80 | 1.13 |
| 2019 | 10 | 392.08 | 392.08 | 485.30 | 0.81 | 0.81 | 10 | 502.03 | 535.30 | 58.30 | 0.85 |
| 2020 | 12 | 488.26 | 488.26 | 550.70 | 0.89 | 0.89 | 12 | 599.78 | 533.00 | 76.10 | 0.98 |
| 2021 | 12 | 623.66 | 623.66 | 618.60 | 1.01 | 1.01 | 12 | 667.59 | 536.30 | 0.20 | 1.24 |
| 2022 | 12 | 546.63 | 546.63 | 578.40 | 0.95 | 0.95 | 11 | 552.08 | 490.60 | 0.40 | 1.12 |
| 2023 | 12 | 486.63 | 486.63 | 494.10 | 0.98 | 0.98 | 12 | 585.01 | 417.00 | 4.80 | 1.39 |
| 2024 | 12 | 529.60 | 529.60 | 522.10 | 1.01 | 1.01 | 12 | 894.36 | 646.10 | 176.30 | 1.09 |
| 2025 | 12 | 505.71 | 505.71 |  |  |  | 12 | 1,080.24 |  |  |  |

## Value against the official commodity table

| year | gas_ct_usd_m | gas_nsc_usd_m | gas_value_ratio | mid_ct_usd_m | diesel_nsc_usd_m | kerosene_nsc_usd_m | mid_value_to_diesel_plus_kerosene | lpg_ct_usd_m | lpg_nsc_usd_m | lpg_value_ratio |
|---|---|---|---|---|---|---|---|---|---|---|
| 2015 | 280.39 | 354.83 | 0.79 | 362.02 | 228.33 | 51.96 | 1.29 | 4.36 | 4.77 | 0.91 |
| 2016 | 128.04 | 180.26 | 0.71 | 198.51 | 131.11 | 56.59 | 1.06 | 1.69 | 2.94 | 0.58 |
| 2017 | 226.87 | 220.52 | 1.03 | 329.48 | 225.18 | 54.31 | 1.18 | 6.02 | 6.10 | 0.99 |
| 2018 | 306.73 | 301.96 | 1.02 | 489.45 | 409.13 | 48.20 | 1.07 | 16.05 | 16.05 | 1.00 |
| 2019 | 178.42 | 221.71 | 0.80 | 267.61 | 289.11 | 38.72 | 0.82 | 8.27 | 11.46 | 0.72 |
| 2020 | 155.46 | 172.61 | 0.90 | 251.90 | 210.33 | 24.16 | 1.07 | 13.04 | 15.62 | 0.83 |
| 2021 | 340.37 | 388.01 | 0.88 | 344.80 | 278.34 | 31.53 | 1.11 | 39.80 | 13.86 | 2.87 |
| 2022 | 334.63 | 352.40 | 0.95 | 484.47 | 352.65 | 94.91 | 1.08 | 19.56 | 22.05 | 0.89 |
| 2023 | 286.93 | 287.66 | 1.00 | 447.22 | 272.39 | 91.79 | 1.23 | 28.64 | 31.79 | 0.90 |
| 2024 | 322.89 | 327.43 | 0.99 | 741.80 | 481.85 | 120.91 | 1.23 | 61.31 | 53.06 | 1.16 |
| 2025 | 321.64 | 409.96 | 0.78 | 706.73 |  | 118.23 |  | 51.01 | 63.85 | 0.80 |

Possible explanations:
- **2015, 2016 and 2025 gasoline, ratios of 0.71-0.79.** Comtrade's value is below the national figure. For 2025 this fits the first-release pattern below. For 2015-2016 the cause is not known.
- **2019.** Two months are absent from Comtrade.
- **HS 271019 above diesel plus kerosene.** Expected, because the line also covers fuel oil and lubricants, which this table does not list.
- **LPG 2021, ratio 2.87.** Unexplained. HS 2711.19 may hold non-LPG gases.
- **2025 diesel.** The official table reads USD 48.1 billion, which looks like a data-entry error. It is excluded and left in the raw file.

## First-release check, all goods

For 2025 onward, each month's Comtrade total is compared with the first and the latest figure in the monthly NSC reports.

| period | comtrade_total_usd_m | nsc_first_usd_m | nsc_latest_usd_m | comtrade_to_first | comtrade_to_latest |
|---|---|---|---|---|---|
| 202501 | 841.590 | 841.600 | 898.300 | 1.000 | 0.937 |
| 202502 | 914.658 | 914.600 | 991.200 | 1.000 | 0.923 |
| 202503 | 1,055.568 | 1,055.600 | 1,219.800 | 1.000 | 0.865 |
| 202504 | 1,000.952 | 1,050.500 | 1,214.900 | 0.953 | 0.824 |
| 202505 | 1,074.152 | 1,074.200 | 1,182.700 | 1.000 | 0.908 |
| 202506 | 1,013.844 | 1,013.800 | 1,083.300 | 1.000 | 0.936 |
| 202507 | 973.086 | 973.100 | 1,076.800 | 1.000 | 0.904 |
| 202508 | 943.692 | 946.600 | 1,033.600 | 0.997 | 0.913 |
| 202509 | 876.839 | 887.800 | 1,034.700 | 0.988 | 0.847 |
| 202510 | 1,080.035 | 1,102.200 | 1,173.900 | 0.980 | 0.920 |
| 202511 | 946.829 | 962.700 | 1,168.400 | 0.984 | 0.810 |
| 202512 | 1,285.449 | 1,285.400 | 1,285.400 | 1.000 | 1.000 |
| 202601 | 926.152 | 926.100 | 956.700 | 1.000 | 0.968 |
| 202602 | 854.592 | 854.600 | 938.800 | 1.000 | 0.910 |
| 202603 | 1,019.437 | 1,019.400 | 1,071.200 | 1.000 | 0.952 |
| 202604 | 1,196.451 | 1,196.400 | 1,283.200 | 1.000 | 0.932 |
| 202605 | 1,188.927 | 1,188.900 | 1,206.900 | 1.000 | 0.985 |
| 202606 |  | 1,403.800 | 1,441.300 |  |  |
| 202607 |  | 1,466.200 | 1,471.100 |  |  |
| 202608 | 1,369.706 | 1,369.700 | 1,369.700 | 1.000 | 1.000 |

Most months match the first national release, and none matches the latest. The national figures are later revised upward while the Comtrade record stays put, at least so far. This is all-goods evidence: how far fuel is affected is not known. It explains why the gasoline value is 0.78 of the official figure in 2025 only partly, since all goods sit near 0.90.

## Reporter against partner

Imports are CIF and exports FOB, and customs dates differ, so a ratio near 1 is expected, not exact.

| product_group | year | export_kt | import_kt | mass_ratio_imports_to_exports | value_ratio_imports_to_exports |
|---|---|---|---|---|---|
| gasoline | 2015 | 793.96 | 558.96 | 0.70 | 0.63 |
| gasoline | 2016 | 1,023.03 | 382.86 | 0.37 | 0.34 |
| gasoline | 2017 | 1,128.35 | 371.19 | 0.33 | 0.45 |
| gasoline | 2018 | 506.58 | 515.85 | 1.02 | 1.06 |
| gasoline | 2020 | 543.84 | 376.99 | 0.69 | 0.74 |
| gasoline | 2021 | 640.60 | 593.46 | 0.93 | 0.96 |
| middle_heavy | 2015 | 822.65 | 816.52 | 0.99 | 0.63 |
| middle_heavy | 2016 | 546.85 | 298.88 | 0.55 | 0.58 |
| middle_heavy | 2017 | 711.72 | 617.53 | 0.87 | 0.94 |
| middle_heavy | 2018 | 761.80 | 649.29 | 0.85 | 0.90 |
| middle_heavy | 2020 | 735.49 | 496.08 | 0.67 | 0.79 |
| middle_heavy | 2021 | 729.10 | 628.43 | 0.86 | 0.77 |

Russian figures end in December 2021. In 2016-2017, Russia reports about three times Kyrgyz gasoline imports, and more than the national balance as well (1,023 against 533 kt in 2016), so simple Kyrgyz under-recording does not explain it. Transit through Kyrgyzstan, re-routing or different product coding are possible; none could be tested here. Other partners:

| exporter | product_group | year | export_kt | import_kt | mass_ratio_imports_to_exports |
|---|---|---|---|---|---|
| KAZ | gasoline | 2018 | 5.36 | 117.04 | 21.83 |
| KAZ | gasoline | 2020 | 102.00 | 106.18 | 1.04 |
| KAZ | gasoline | 2021 | 4.87 | 18.91 | 3.88 |
| KAZ | gasoline | 2023 | 6.73 | 47.73 | 7.09 |
| KAZ | middle_heavy | 2015 | 80.45 | 207.78 | 2.58 |
| KAZ | middle_heavy | 2016 | 86.49 | 246.46 | 2.85 |
| KAZ | middle_heavy | 2017 | 216.60 | 107.46 | 0.50 |
| KAZ | middle_heavy | 2018 | 122.92 | 154.95 | 1.26 |
| KAZ | middle_heavy | 2020 | 100.08 | 94.60 | 0.95 |
| KAZ | middle_heavy | 2021 | 12.79 | 15.87 | 1.24 |
| KAZ | middle_heavy | 2022 | 14.25 | 24.83 | 1.74 |
| KAZ | middle_heavy | 2023 | 63.68 | 61.53 | 0.97 |
| KAZ | middle_heavy | 2024 | 5.11 | 193.33 | 37.83 |
| KAZ | middle_heavy | 2025 | 273.68 | 328.69 | 1.20 |
| UZB | middle_heavy | 2022 | 3.15 | 3.16 | 1.00 |
| UZB | middle_heavy | 2023 | 4.66 | 4.83 | 1.04 |
| UZB | middle_heavy | 2024 | 3.72 | 3.64 | 0.98 |
| UZB | middle_heavy | 2025 | 8.89 | 9.12 | 1.03 |

Kazakh pairs vary greatly by year, sometimes by more than 20 times, while Uzbek pairs agree. Small corridors need caution.

## Press figures

| claim | press_kt | comtrade_kt | press_usd_m | comtrade_usd_m | comtrade_basis |
|---|---|---|---|---|---|
| Fuels and lubricants, all of 2023 | 630.0 | 1,071.6 | 277.0 | 734.2 | gasoline + HS 271019 |
| Motor gasoline, first two months of 2025 | 170.2 | 131.3 | 73.3 | 75.4 | gasoline, Jan-Feb 2025 |

Neither is a valid check. "Fuels and lubricants" is undefined, and a Jan-Feb 2025 figure of 170.2 kt with USD 73.3 million implies USD 431/t, far below that period's customs values. The original reports should be obtained.

## Import dependency

Dependency is how much of domestic use comes from net imports. It differs from supplier concentration, which is how few suppliers provide those imports. It is computed for Kyrgyzstan only, because this project holds no comparable production and consumption data for other countries. Panel exports-to-imports ratios describe trade orientation and are not dependency measures.

Net import dependency = (imports - exports) / domestic use. Values above 1 mean imports also went into stocks, and negative values mean a net exporter. Stock cover = year-end stock / average monthly use.

| fuel | year | production | imports | exports | domestic_use | stock_end | net_import_dependency | domestic_production_share | stock_cover_months |
|---|---|---|---|---|---|---|---|---|---|
| diesel | 2015 | 56.10 | 514.90 | 0.60 | 539.80 | 59.40 | 0.95 | 0.10 | 1.32 |
| diesel | 2016 | 106.30 | 347.40 | 0.04 | 481.50 | 31.30 | 0.72 | 0.23 | 0.78 |
| diesel | 2017 | 89.50 | 541.30 | 2.20 | 619.80 | 39.90 | 0.87 | 0.14 | 0.77 |
| diesel | 2018 | 79.30 | 706.10 | 0.90 | 750.00 | 74.20 | 0.94 | 0.10 | 1.19 |
| diesel | 2019 | 83.00 | 535.30 | 16.70 | 641.20 | 34.50 | 0.81 | 0.13 | 0.65 |
| diesel | 2020 | 57.90 | 533.00 | 17.30 | 518.50 | 89.50 | 0.99 | 0.10 | 2.07 |
| diesel | 2021 | 96.90 | 536.30 | 1.20 | 620.14 | 101.40 | 0.86 | 0.15 | 1.96 |
| diesel | 2022 | 115.30 | 490.60 | 1.20 | 623.50 | 82.10 | 0.78 | 0.19 | 1.58 |
| diesel | 2023 | 125.70 | 417.00 | 0.90 | 498.50 | 124.70 | 0.83 | 0.23 | 3.00 |
| diesel | 2024 | 176.10 | 646.10 | 4.40 | 746.70 | 194.90 | 0.86 | 0.21 | 3.13 |
| fuel_oil | 2015 | 136.00 | 205.70 | 0.00 | 282.20 | 86.20 | 0.73 | 0.40 | 3.67 |
| fuel_oil | 2016 | 74.90 | 33.30 | 0.40 | 147.00 | 47.10 | 0.22 | 0.69 | 3.84 |
| fuel_oil | 2017 | 62.60 | 76.20 | 7.20 | 115.40 | 63.30 | 0.60 | 0.45 | 6.58 |
| fuel_oil | 2018 | 156.50 | 13.80 | 33.70 | 172.60 | 27.10 | -0.12 | 0.92 | 1.88 |
| fuel_oil | 2019 | 115.40 | 58.30 | 44.10 | 126.10 | 30.50 | 0.11 | 0.66 | 2.90 |
| fuel_oil | 2020 | 84.30 | 76.10 | 30.70 | 61.70 | 97.70 | 0.74 | 0.53 | 19.00 |
| fuel_oil | 2021 | 151.30 | 0.20 | 128.20 | 43.00 | 78.00 | -2.98 | 1.00 | 21.77 |
| fuel_oil | 2022 | 163.90 | 0.40 | 123.85 | 45.19 | 73.30 | -2.73 | 1.00 | 19.47 |
| fuel_oil | 2023 | 174.60 | 4.80 | 118.30 | 49.90 | 84.40 | -2.27 | 0.97 | 20.30 |
| fuel_oil | 2024 | 166.60 | 176.30 | 117.90 | 218.50 | 90.90 | 0.27 | 0.49 | 4.99 |
| gasoline | 2015 | 115.10 | 625.30 | 31.80 | 689.70 | 79.30 | 0.86 | 0.16 | 1.38 |
| gasoline | 2016 | 171.30 | 532.90 | 6.80 | 739.00 | 37.00 | 0.71 | 0.24 | 0.60 |
| gasoline | 2017 | 234.80 | 468.50 | 6.60 | 691.50 | 41.60 | 0.67 | 0.33 | 0.72 |
| gasoline | 2018 | 218.80 | 632.20 | 28.30 | 791.80 | 72.20 | 0.76 | 0.26 | 1.09 |
| gasoline | 2019 | 103.00 | 485.30 | 17.30 | 576.40 | 65.80 | 0.81 | 0.18 | 1.37 |
| gasoline | 2020 | 13.00 | 550.70 | 2.20 | 545.10 | 81.80 | 1.01 | 0.02 | 1.80 |
| gasoline | 2021 | 20.70 | 618.60 | 0.40 | 590.90 | 129.10 | 1.05 | 0.03 | 2.62 |
| gasoline | 2022 | 24.30 | 578.40 | 0.60 | 531.60 | 199.10 | 1.09 | 0.04 | 4.49 |
| gasoline | 2023 | 25.80 | 494.10 | 6.70 | 610.10 | 101.20 | 0.80 | 0.05 | 1.99 |
| gasoline | 2024 | 156.00 | 522.10 | 76.40 | 579.20 | 122.70 | 0.77 | 0.23 | 2.54 |

Kyrgyzstan depends heavily on imported gasoline and diesel, at 0.77 and 0.86 of domestic use in 2024. The balance shows domestic gasoline output jumping from 25.8 to 156 kt in 2024, which reduces dependency and explains part of the fall; it should be confirmed before use. Fuel oil dependency is unstable because domestic use is small.
