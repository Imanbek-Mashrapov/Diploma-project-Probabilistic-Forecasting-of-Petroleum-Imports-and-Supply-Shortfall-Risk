"""Stage 4a: rule-based title pre-screening with recorded reasons.

Every unique record gets a pre-screen decision: 'manual' (goes to manual title/abstract screening)
or an exclusion code. Rules look at the title only, because long abstracts mention every keyword.
Seeds, Connected Papers neighbours and gap-check hits always go to manual screening.
Output: metadata/raw/prescreen.csv
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "metadata" / "raw"

C = {
    "fuel": r"petroleum|oil product|refined|gasoline|petrol\b|diesel|motor fuel|\bfuels?\b|crude|\boil\b|lpg",
    "energy": r"energy",
    "trade": r"import|export|\btrade|comtrade",
    "forecast": r"forecast|predict|nowcast|early warning|projection",
    "prob": r"probabilist|quantile|interval|conformal|uncertainty|calibrat|scoring rule|density forecast|distributional",
    "global": r"global (forecasting )?models?|cross-learning|cross learning|locality|groups of time series|sets? of (related )?time series|many time series|panel|multiple time series|pooled",
    "ml": r"deep learning|neural|lstm|\bgru\b|transformer|n-beats|deepar|boosting|lightgbm|xgboost|random forest|machine learning|tree-based|trees",
    "security": r"energy security|security of (energy )?supply|supply security|disruption|shortage|shortfall|resilien|vulnerab|diversif|concentration|herfindahl|dependen",
    "geo": r"geopolit|sanction|embargo|\bwar\b|conflict",
    "region": r"landlocked|kyrgyz|central asia|tajik|kazakh|uzbek|mongolia|armenia|nepal|bolivia|paraguay|zambia|moldova|eurasian economic",
    "dataq": r"revision|vintage|real-time|real time|publication lag|release|mirror|ragged",
    "eval": r"forecast(ing)? accuracy|predictive (accuracy|ability)|forecast evaluation|cross-validation|rolling origin|out-of-sample|scoring rules|competition",
    "demand": r"demand|consumption|elasticit",
    "foundation": r"foundation model|meta-learning|pretrained|pre-trained|zero-shot|transfer learning",
}
EXCLUDE = [
    ("E1_electricity_renewables", r"electric|solar|photovolt|\bwind\b|\bload\b|power (system|grid|plant|generation)|microgrid|smart grid|charging|battery|hydrogen|hydropower|grid"),
    ("E2_price_or_financial_target", r"\bprices?\b|volatility|stock|returns|futures|exchange rate|inflation|market efficiency|spillover|connectedness"),
    ("E3_upstream_or_engineering", r"well\b|reservoir|drilling|petrophysic|refinery (unit|operation)|distillation|corrosion|pipeline leak|production forecasting|oil production|soft sensor|seismic"),
    ("E4_non_research_item", r"^(editorial|commentary|dispatches|from the editors|news|book review|erratum|retracted)|replication data|data supporting|database \(|panel session"),
    ("E5_other_commodity_or_domain", r"wheat|grain|rice|sunflower|olive|food|water|crop|livestock|malaria|cardio|health|tourism|minerals?|gallium|coal|natural gas|lng"),
]


def keep(t):
    has = {k: bool(re.search(p, t)) for k, p in C.items()}
    return (
        (has["fuel"] and (has["trade"] or has["forecast"] or has["security"] or has["geo"] or has["demand"]))
        or (has["energy"] and has["security"])
        or (has["energy"] and has["trade"])
        or (has["trade"] and has["demand"])
        or has["eval"]
        or (has["forecast"] and (has["prob"] or has["global"] or has["foundation"]))
        or (has["forecast"] and has["ml"] and (has["trade"] or has["fuel"] or has["energy"]))
        or (has["trade"] and (has["forecast"] or has["geo"] or has["security"] or has["dataq"]))
        or (has["region"] and (has["fuel"] or has["energy"] or has["trade"] or "landlocked" in t))
        or (has["dataq"] and has["forecast"])
    )


def main():
    rows = list(csv.DictReader(open(RAW / "candidates.csv", encoding="utf-8")))
    cp = set()
    for line in open(RAW / "connectedpapers_montero_manso_2021.tsv", encoding="utf-8").readlines()[1:]:
        cp.add(re.sub(r"[^a-z0-9]+", "", line.split("\t")[0].lower())[:150])
    # Crossref gap-check results were screened by their Boolean condition (gapcheck_local.py); only matches were read
    import json
    gm = json.load(open(RAW / "gap_matches.json", encoding="utf-8"))
    matched = {(h["doi"] or h["title"].lower()) for g in gm.values() for h in g["matches"]}
    out = []
    for r in rows:
        t = r["title"].lower()
        nt = re.sub(r"[^a-z0-9]+", "", t)[:150]
        forced = r["is_seed"] == "True" or nt in cp
        only_gap_cr = r["found_in"] == "gapcheck_crossref"
        if only_gap_cr and (r["doi"] or t) not in matched:
            decision = "G0_gapcheck_result_without_boolean_match"
        elif forced or only_gap_cr:
            decision = "manual"
        elif not keep(t):
            decision = "E0_off_topic_title"
        else:
            decision = "manual"
            for code, pat in EXCLUDE:
                # keep price/electricity papers only when they are about probabilistic/global method design
                if re.search(pat, t) and not re.search(C["trade"] + "|" + C["global"] + "|import", t):
                    decision = code
                    break
        r["prescreen"] = decision
        r["in_connected_papers"] = nt in cp
        out.append(r)
    fields = list(out[0].keys())
    with open(RAW / "prescreen.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(out)
    from collections import Counter
    print(Counter(r["prescreen"] for r in out))


if __name__ == "__main__":
    main()
