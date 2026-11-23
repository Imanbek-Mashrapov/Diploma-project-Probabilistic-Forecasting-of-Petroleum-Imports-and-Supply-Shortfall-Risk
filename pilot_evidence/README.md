# Pilot evidence

Evidence behind Sections 3 and 10.5 of `Final_Diploma_Research_Topic_Selection_and_Research_Proposal.docx`. Data were downloaded on 1 November 2026.

| Folder | Contents |
|---|---|
| `raw_comtrade/` | UN Comtrade JSON responses: `kg/` (Kyrgyz imports by supplier, one file per month), `panel/` (world totals for the 24-country panel), availability listings |
| `raw_other/` | Brent spot price, Geopolitical Risk index, Fuel and Energy Balance 2024, retail fuel and crude output tables |
| `outputs/` | Audit tables, panel coverage, pilot scores, console logs |
| `scripts/` | Pull, audit and backtest code |

The scripts are the pilot versions. They expect `dl_comtrade/` and `dl_misc/` folders in the working directory, so paths need adjusting before a rerun, and they contain a site-packages line specific to this computer.

Exports were not pulled. June and July 2026, September and October 2019 are absent from Comtrade for Kyrgyzstan.

This is planning evidence, not thesis code. Rewrite the pipeline yourself in your own repository: the guideline requires authentic commit history and AI-use disclosure.
