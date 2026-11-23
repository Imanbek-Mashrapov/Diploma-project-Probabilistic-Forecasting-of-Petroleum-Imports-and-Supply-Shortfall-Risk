"""Stage 4c: screening of the proposal's verified seed references (merged into the pool on 2026-11-07),
then assembly of the full included set with metadata in metadata/raw/included.json.

Seeds are screened like any other record: those outside the scope of this review are excluded with a reason.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "metadata" / "raw"

PF, ES, PR, GT, DL, GR, LL = ("petroleum_forecasting", "energy_security", "probabilistic_forecasting", "global_time_series",
                              "deep_learning", "geopolitical_risk", "landlocked_economies")
INCLUDE_BY_DOI = {
    "10.3390/math11122625": (GT, "core"),           # multi-country TFT for GDP: a cross-country global DL analogue
    "10.1080/15567036.2021.2024919": (PF, "support"),
    "10.30910/turkjans.1756810": (PF, "support"),
    "10.32479/ijeep.23912": (PF, "support"),
    "10.1198/016214506000001437": (PR, "core"),
    "10.3390/en18226044": (PF, "support"),
    "10.1016/j.knosys.2022.108687": (PF, "core"),
    "10.1038/s41598-026-72209-3": (PF, "support"),
    "10.1155/2024/6176898": (PF, "support"),
    "10.3390/bdcc8060065": (PF, "support"),
    "10.48550/arxiv.2402.01648": (PF, "core"),
    "10.1016/j.ijforecast.2018.09.001": (PF, "core"),
    "10.48550/arxiv.1905.03222": (PR, "core"),
    "10.48550/arxiv.2101.02118": (DL, "core"),
    "10.1038/s41560-020-0662-1": (PF, "support"),
    "10.1016/s0169-2070(96)00719-4": (GT, "support"),
    "10.1016/j.enpol.2011.05.008": (PF, "support"),
    "10.48550/arxiv.2207.08815": (DL, "core"),
    "10.1002/jae.659": (GR, "support"),
    # found by the local Boolean gap checks (gapcheck_local.py)
    "10.2139/ssrn.6893382": (PR, "support"),        # quantile regression for aviation fuel demand
    "10.71889/5fylantbak.29865743": (GT, "support"), # revisions in UN energy statistics
    "10.2139/ssrn.1494582": (GT, "support"),        # real-time datasets and data release
    "10.1016/j.eneco.2025.108594": (GR, "support"),  # GPR contribution to crude volatility forecasts
}
EXCLUDE_SEEDS = {
    "10.47065/bits.v6i3.5877": "X2_station_level_sales_redundant",
    "10.52589/ajmss-hsz2hi0h": "X2_station_level_sales_redundant",
    "10.1016/j.petsci.2022.05.005": "X2_station_level_sales_redundant",
    "10.20965/jaciii.2018.p0387": "X2_station_level_sales_redundant",
    "10.1016/j.rineng.2024.101776": "X1_upstream_well_production_out_of_scope",
    "10.1016/j.cageo.2022.105126": "X1_upstream_well_production_out_of_scope",
    "10.1016/j.petrol.2020.107013": "X1_upstream_well_production_out_of_scope",
    "10.1016/j.petrol.2021.109468": "X1_upstream_well_production_out_of_scope",
    "10.1016/j.petrol.2021.109937": "X1_upstream_well_production_out_of_scope",
    "10.2118/945228-g": "X1_upstream_well_production_out_of_scope",
    "10.3390/en18133584": "X1_upstream_well_production_out_of_scope",
    "10.1016/j.neucom.2018.09.082": "X1_upstream_well_production_out_of_scope",
    "10.1016/j.rineng.2026.110128": "X1_upstream_well_production_out_of_scope",
    "10.1016/j.energy.2020.119708": "X1_upstream_well_production_out_of_scope",
    "10.1016/j.petrol.2019.106682": "X1_upstream_well_production_out_of_scope",
    "10.1016/j.petrol.2022.111043": "X1_upstream_well_production_out_of_scope",
    "10.1016/j.petrol.2019.106223": "X1_upstream_well_production_out_of_scope",
}


def main():
    rows = {r["key"]: r for r in csv.DictReader(open(RAW / "prescreen.csv", encoding="utf-8"))}
    by_doi = {r["doi"]: r for r in rows.values() if r["doi"]}
    sel = json.load(open(RAW / "selection_round1.json", encoding="utf-8"))
    for doi, (theme, tier) in INCLUDE_BY_DOI.items():
        r = by_doi[doi]
        sel.append({"key": r["key"], "title": r["title"], "doi": doi, "theme": theme, "tier": tier, "row_round1": None})
    # records whose only source was the first OpenAlex gap-check run (raw file overwritten on rerun) are
    # carried over from the round-1 snapshot of included.json
    snap = {i["key"]: i for i in json.load(open(RAW / "included_round1_snapshot.json", encoding="utf-8"))}
    included = []
    for s in sel:
        r = rows.get(s["key"]) or snap[s["key"]]
        included.append({**{k: r[k] for k in ("key", "title", "year", "authors", "venue", "type", "doi", "all_dois", "n_versions",
                                              "openalex_id", "cited_by", "oa_pdf", "oa_license", "url", "publisher_host",
                                              "found_in", "themes", "queries", "abstract", "is_seed")},
                         "theme": s["theme"], "tier": s["tier"]})
    json.dump(included, open(RAW / "included.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump(EXCLUDE_SEEDS, open(RAW / "excluded_seeds.json", "w"), indent=1)
    print(len(included), "included;", sum(i["tier"] == "core" for i in included), "core")


if __name__ == "__main__":
    main()
