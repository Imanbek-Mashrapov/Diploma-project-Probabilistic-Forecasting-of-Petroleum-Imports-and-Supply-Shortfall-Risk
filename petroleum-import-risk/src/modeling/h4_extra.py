"""Exploratory H4 additions (R1, R2; decision log 2026-11-25). Not part of the four primary tests, not Holm-adjusted.

R1: on the Tier-1 sum3 cases of H4, compare the PR-AUC and recall at the alert budget of the LightGBM (global)
shortfall probability with (a) the shortfall probabilities of the local baselines and (b) a persistence rule (last
visible 3-month Q/B at the origin, lower = riskier). Differences use the same moving-block bootstrap as H4
(blocks of 6 origins, 2000 resamples, seed 0) on the cases both scores cover.
R2: the same comparison, and H4 against the HHI ranking, separately for series whose importer type is provisionally
"strict_importer" (imports assumed to be the dominant source of supply) and for the rest. The type is hand-assigned
and unsourced (reports/phase2/unresolved_issues.md item 4); only Kyrgyzstan has a supply balance.
"""
import numpy as np
import pandas as pd

from src.modeling import features as ft, metrics as mt

BENCHMARKS = ["naive", "snaive", "mean12", "sarima", "ets", "persistence"]
LABELS = {"naive": "Naive", "snaive": "Seasonal naive", "mean12": "12-month mean", "sarima": "SARIMA", "ets": "ETS",
          "persistence": "Persistence (last visible Q/B)", "hhi": "HHI ranking"}
STRATA = {"all": None, "import_dominant": True, "other": False}


def persistence_table(settings, monthly, cases):
    """Persistence score for every (origin, series) in `cases`, from visible data only. Score = -ratio (higher = riskier)."""
    months = ft.months_index(monthly)
    years = settings["modeling"]["shortfall"]["baseline_years"]
    rows = []
    for sid, pairs in cases[["origin", "series_id"]].drop_duplicates().groupby("series_id"):
        g = monthly[monthly.series_id == sid].set_index("month").reindex(months)
        mass, avail = g.import_mass_t.to_numpy(float), g.available_on.to_numpy(dtype="datetime64[ns]")
        for o in pairs.origin:
            r = ft.persistence_ratio(mass, avail, months, pd.Timestamp(o), years)
            rows.append({"origin": o, "series_id": sid, "persist_ratio": r, "persist_score": -r if not np.isnan(r) else np.nan})
    return pd.DataFrame(rows)


def benchmark_frame(d, probs, labels, persist, base_model="lgbm_global"):
    """H4 cases (evaluation origins with a realised ratio) with one score column per benchmark. NaN where a model has no forecast."""
    from src.modeling.evaluate import h4_frame
    s = h4_frame(d, probs, labels, base_model).rename(columns={"p_short_75": "score_lgbm"})
    for b in BENCHMARKS:
        if b == "persistence":
            s = s.merge(persist[["origin", "series_id", "persist_score"]].rename(columns={"persist_score": "score_persistence"}), on=["origin", "series_id"], how="left")
        else:
            p = probs[probs.model == b][["origin", "series_id", "p_short_75"]].rename(columns={"p_short_75": f"score_{b}"})
            s = s.merge(p, on=["origin", "series_id"], how="left")
    return s.rename(columns={"hhi_12m": "score_hhi"})


def _origin_index(frame):
    """Row positions per origin, in time order (the bootstrap resamples whole origins)."""
    return [np.asarray(ix) for _, ix in sorted(frame.groupby("origin").indices.items())]


def paired_bootstrap(y, a, b, groups, n_boot=2000, block=6, seed=0):
    """Moving-block bootstrap of PR-AUC(a) - PR-AUC(b), same resampling scheme and seed as `evaluate.h4`."""
    rng = np.random.default_rng(seed)
    n = len(groups)
    block = min(block, n)
    diffs = []
    for _ in range(n_boot):
        picks = []
        while len(picks) < n:
            st = rng.integers(0, n - block + 1)
            picks.extend(range(st, st + block))
        ix = np.concatenate([groups[i] for i in picks[:n]])
        if y[ix].any():
            diffs.append(mt.pr_auc(y[ix], a[ix]) - mt.pr_auc(y[ix], b[ix]))
    diffs = np.array(diffs)
    return [float(x) for x in np.nanpercentile(diffs, [2.5, 97.5])], float(np.mean(diffs <= 0)), len(diffs)


def episodes(frame, label="flag_75"):
    """Distinct series with a positive, and maximal runs of consecutive-origin positives (the effective number of events)."""
    pos = frame[frame[label].astype(bool)]
    n_ep = 0
    for _, g in pos.groupby("series_id"):
        o = pd.to_datetime(g.origin).drop_duplicates().sort_values()
        n_ep += int((o.diff().dt.days.fillna(99) > 31).sum())
    return int(pos.series_id.nunique()), n_ep


def compare_models(s, budget, label="flag_75", others=BENCHMARKS + ["hhi"]):
    """Rows: lgbm vs each other score on the cases both cover. `s` carries score_<name> columns and `label`."""
    rows = []
    for b in others:
        sh = s[s.score_lgbm.notna() & s[f"score_{b}"].notna()]
        y = sh[label].astype(bool).to_numpy()
        if len(sh) == 0 or not y.any():
            rows.append({"benchmark": b, "cases": int(len(sh)), "positives": int(y.sum())})
            continue
        a, o = sh.score_lgbm.to_numpy(float), sh[f"score_{b}"].to_numpy(float)
        ci, p, _ = paired_bootstrap(y, a, o, _origin_index(sh))
        rows.append({"benchmark": b, "cases": int(len(sh)), "positives": int(y.sum()), "base_rate": float(y.mean()),
                     "pr_auc_lgbm": mt.pr_auc(y, a), "pr_auc_benchmark": mt.pr_auc(y, o), "pr_auc_diff": mt.pr_auc(y, a) - mt.pr_auc(y, o),
                     "diff_ci95_lo": ci[0], "diff_ci95_hi": ci[1], "p_one_sided": p,
                     "recall_lgbm": mt.recall_at_budget(y, a, budget), "recall_benchmark": mt.recall_at_budget(y, o, budget)})
    return pd.DataFrame(rows)


def run_all(d, probs, labels, monthly, series, settings):
    """R1 (stratum 'all') and R2 (import-dominant vs other) tables. Returns (long table, strata description, json dict)."""
    budget = settings["modeling"]["alert_budget"]
    base = d[(d.model == "lgbm_global") & (d.task == "sum3")]
    from src.modeling.evaluate import h4_frame
    pairs = h4_frame(d, probs, labels)[["origin", "series_id"]]
    persist = persistence_table(settings, monthly, pairs)
    s = benchmark_frame(d, probs, labels, persist)
    dominant = series.set_index("series_id").importer_type_provisional.eq("strict_importer")
    s["import_dominant"] = s.series_id.map(dominant)
    tables, desc = [], []
    for name, flag in STRATA.items():
        sub = s if flag is None else s[s.import_dominant == flag]
        if sub.empty:
            continue
        tab = compare_models(sub, budget).assign(stratum=name)
        tables.append(tab)
        ns, ne = episodes(sub)
        y = sub.flag_75.astype(bool)
        desc.append({"stratum": name, "series": int(sub.series_id.nunique()), "cases": int(len(sub)), "positives": int(y.sum()),
                     "base_rate": float(y.mean()), "series_with_positive": ns, "episodes": ne})
    long = pd.concat(tables, ignore_index=True)
    return long, pd.DataFrame(desc), s
