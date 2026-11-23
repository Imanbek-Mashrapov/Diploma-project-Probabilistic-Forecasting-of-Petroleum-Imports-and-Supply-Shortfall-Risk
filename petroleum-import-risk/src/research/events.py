"""Sourced shock-event calendar and its comparison with the descriptive shortfall labels.

The calendar lives in config/shock_events.csv and is coded by hand from public sources.
This module validates it, works out which panel series each event touches, and checks
two things: whether labels fire during supply events, and whether label episodes have
any documented event behind them. Nothing here is used as a model feature.
"""
import logging

import numpy as np
import pandas as pd

from src.utils.config import REPORTS, ROOT, load_countries

log = logging.getLogger(__name__)
EVENTS_PATH = ROOT / "config" / "shock_events.csv"
OUT = REPORTS / "phase2"
TABLES = OUT / "tables"

ROLES = {"supply_shortfall", "demand_shock", "import_surge", "context"}
PRODUCT_SCOPES = {"gasoline", "distillates", "all_fuels", "crude"}
END_BASES = {"announced", "reported", "last_report", "assumed", "open"}
PRECISIONS = {"day", "month"}
CONFIDENCE = {"high", "medium", "low"}
EVENT_TYPES = {"export_restriction", "transit_disruption", "supply_disruption", "quota_limit", "logistics", "fx_shortage",
               "price_control", "sanctions", "refinery_outage", "demand_shock", "conflict"}
SHARE_COLUMNS = {"RUS": "russia_share"}  # supplier shares available in the monthly data
PRODUCTS = {"gasoline": ["gasoline"], "distillates": ["middle_incl_blends"], "all_fuels": ["gasoline", "middle_incl_blends"], "crude": []}
THRESHOLD = 0.75
EXPOSURE_MIN = 0.25
RESPONSE_LAG = 2  # a trailing three-month sum still reflects an event two months after it ends


def _codes(cell):
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    return [c.strip() for c in str(cell).split(";") if c.strip()]


def validate(events, countries=None):
    """Return a list of problems; an empty list means the calendar is usable."""
    known = set((countries if countries is not None else load_countries()).iso3)
    problems = []
    if events.event_id.duplicated().any():
        problems.append(f"duplicate event_id: {sorted(events.event_id[events.event_id.duplicated()])}")
    for e in events.itertuples():
        def bad(msg):
            problems.append(f"{e.event_id}: {msg}")
        for field, allowed in [("role", ROLES), ("product_scope", PRODUCT_SCOPES), ("end_basis", END_BASES),
                               ("date_precision", PRECISIONS), ("confidence", CONFIDENCE), ("event_type", EVENT_TYPES)]:
            if getattr(e, field) not in allowed:
                bad(f"{field}={getattr(e, field)!r} not in {sorted(allowed)}")
        if pd.isna(e.start_date):
            bad("start_date missing or not a date")
        if (e.end_basis == "open") != pd.isna(e.end_date):
            bad("end_date must be empty exactly when end_basis is 'open'")
        if pd.notna(e.start_date) and pd.notna(e.end_date) and e.end_date < e.start_date:
            bad("end_date before start_date")
        if not str(e.source1_url).startswith("https://"):
            bad("source1_url must be an https link")
        for i in (2, 3):
            url, publisher = getattr(e, f"source{i}_url"), getattr(e, f"source{i}_publisher")
            if pd.notna(url) and not str(url).startswith("https://"):
                bad(f"source{i}_url must be an https link")
            if pd.isna(url) != pd.isna(publisher):
                bad(f"source{i} needs both a publisher and a url")
        affected = _codes(e.affected_iso3)
        if not affected:
            bad("affected_iso3 is empty")
        elif affected in (["ALL"], ["EXPOSED"]):
            if affected == ["EXPOSED"] and e.origin_iso3 not in SHARE_COLUMNS:
                bad(f"EXPOSED needs an origin with supplier shares in the data: {sorted(SHARE_COLUMNS)}")
        else:
            unknown = set(affected) - known
            if unknown:
                bad(f"unknown affected codes {sorted(unknown)}")
        unknown = set(_codes(e.exempt_iso3)) - known
        if unknown:
            bad(f"unknown exempt codes {sorted(unknown)}")
    return problems


def load_events(path=EVENTS_PATH):
    events = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    for col in ["start_date", "end_date", "announced_date"]:
        events[col] = pd.to_datetime(events[col], format="%Y-%m-%d", errors="coerce")
    problems = validate(events)
    if problems:
        raise ValueError("shock_events.csv has problems:\n" + "\n".join(problems))
    return events


def label_series(monthly, iso3, product, threshold=THRESHOLD):
    """Monthly shortfall labels for one series, using the rule from the paper.

    ratio: trailing three-month mass over the mean of the same three months in the previous
    three years (missing years skipped). supply_side: the three-month mean of uv_relative is
    above 1, i.e. prices were high for the season. uv_relative uses future months, so the
    flag is descriptive only.
    """
    s = monthly[(monthly.iso3 == iso3) & (monthly.product_group == product)].set_index("month").sort_index().asfreq("MS")
    q = s.import_mass_t.rolling(3, min_periods=3).sum()
    base = pd.concat([q.shift(12), q.shift(24), q.shift(36)], axis=1).mean(axis=1)
    ratio = q / base
    uv = s.uv_relative.where(s.import_mass_t.notna()).rolling(3, min_periods=2).mean()
    out = pd.DataFrame({"ratio": ratio, "flag": ratio < threshold, "uv3": uv})
    out["supply_side"] = out.flag & (out.uv3 > 1)
    out.loc[ratio.isna(), ["flag", "supply_side"]] = False
    return out


def episodes(labels):
    """Consecutive flagged months as episodes: start, end, months, minimum ratio."""
    flag = labels.flag
    starts = flag & ~flag.shift(1, fill_value=False)
    ids = starts.cumsum().where(flag)
    rows = []
    for _, g in labels[flag].groupby(ids[flag]):
        rows.append({"start": g.index.min(), "end": g.index.max(), "months": len(g), "min_ratio": g.ratio.min(),
                     "supply_side_months": int(g.supply_side.sum())})
    return pd.DataFrame(rows, columns=["start", "end", "months", "min_ratio", "supply_side_months"])


def exposure(monthly, iso3, product, origin, start):
    """Median supplier share from origin in the 12 months before the event."""
    col = SHARE_COLUMNS[origin]
    s = monthly[(monthly.iso3 == iso3) & (monthly.product_group == product)].set_index("month")[col]
    window = s[(s.index >= start - pd.DateOffset(months=12)) & (s.index < start)]
    return float(window.median()) if window.notna().any() else np.nan


def expand(events, monthly, panel):
    """One row per event x panel series it touches. panel: DataFrame of eligible iso3, product_group."""
    rows = []
    for e in events.itertuples():
        exempt = set(_codes(e.exempt_iso3))
        affected = _codes(e.affected_iso3)
        for product in PRODUCTS[e.product_scope]:
            series = panel[panel.product_group == product].iso3
            if affected not in (["ALL"], ["EXPOSED"]):
                series = series[series.isin(affected)]
            for iso3 in series:
                share = np.nan
                if affected == ["EXPOSED"]:
                    share = exposure(monthly, iso3, product, e.origin_iso3, _month(e.start_date))
                    if iso3 in exempt or not share >= EXPOSURE_MIN:
                        continue
                rows.append({"event_id": e.event_id, "role": e.role, "iso3": iso3, "product_group": product,
                             "exposure_share": share, "confidence": e.confidence})
    return pd.DataFrame(rows, columns=["event_id", "role", "iso3", "product_group", "exposure_share", "confidence"])


def _month(ts):
    return pd.Timestamp(ts).to_period("M").to_timestamp()


def event_window(event, last_month):
    start = _month(event.start_date)
    end = _month(event.end_date) if pd.notna(event.end_date) else last_month
    return start, min(end + pd.DateOffset(months=RESPONSE_LAG), last_month)


def check_events(events, touched, labels):
    """Did labels fire while each event was under way?"""
    by_id = events.set_index("event_id")
    rows = []
    for t in touched.itertuples():
        lab = labels[(t.iso3, t.product_group)]
        last = lab.index.max()
        start, end = event_window(by_id.loc[t.event_id], last)
        w = lab.loc[start:end] if start <= last else lab.iloc[0:0]
        evaluable = int(w.ratio.notna().sum())
        rows.append({**t._asdict(), "window_start": start.strftime("%Y-%m"), "window_end": end.strftime("%Y-%m") if start <= last else "",
                     "evaluable_months": evaluable, "flagged_months": int(w.flag.sum()),
                     "supply_side_months": int(w.supply_side.sum()),
                     "min_ratio": round(float(w.ratio.min()), 3) if evaluable else np.nan,
                     "outcome": "no_data" if evaluable == 0 else ("label_fired" if w.flag.any() else "no_label")})
    return pd.DataFrame(rows).drop(columns="Index", errors="ignore")


def check_episodes(events, touched, labels):
    """Does each label episode overlap a documented event for the same series?"""
    by_id = events.set_index("event_id")
    rows = []
    for (iso3, product), lab in labels.items():
        mine = touched[(touched.iso3 == iso3) & (touched.product_group == product)]
        windows = [(r.event_id, r.role, *event_window(by_id.loc[r.event_id], lab.index.max())) for r in mine.itertuples()]
        for ep in episodes(lab).itertuples():
            hits = [(eid, role) for eid, role, s, e in windows if s <= ep.end and e >= ep.start]
            roles = {r for _, r in hits}
            # Only events that predict lower imports can explain a shortfall label; context and
            # import-surge events are listed but do not count as an explanation.
            explained = "supply_shortfall" if "supply_shortfall" in roles else "demand_shock" if "demand_shock" in roles else "none"
            rows.append({"iso3": iso3, "product_group": product, "start": ep.start.strftime("%Y-%m"), "end": ep.end.strftime("%Y-%m"),
                         "months": ep.months, "min_ratio": round(ep.min_ratio, 3), "supply_side_months": ep.supply_side_months,
                         "events": ";".join(eid for eid, r in hits if r in ("supply_shortfall", "demand_shock")),
                         "context_events": ";".join(eid for eid, r in hits if r not in ("supply_shortfall", "demand_shock")),
                         "explained_by": explained})
    return pd.DataFrame(rows, columns=["iso3", "product_group", "start", "end", "months", "min_ratio", "supply_side_months", "events", "context_events", "explained_by"])


def run(monthly, eligibility, write=True):
    events = load_events()
    panel = eligibility[eligibility.eligible & eligibility.product_group.isin(["gasoline", "middle_incl_blends"])][["iso3", "product_group"]]
    labels = {(r.iso3, r.product_group): label_series(monthly, r.iso3, r.product_group) for r in panel.itertuples()}
    touched = expand(events, monthly, panel)
    by_event = check_events(events, touched, labels)
    by_episode = check_episodes(events, touched, labels)
    summary = summarise(events, touched, by_event, by_episode)
    if write:
        TABLES.mkdir(parents=True, exist_ok=True)
        by_event.to_csv(TABLES / "event_label_check.csv", index=False)
        by_episode.to_csv(TABLES / "label_episodes_vs_events.csv", index=False)
        (OUT / "event_validation.md").write_text(report(events, summary, by_event, by_episode), encoding="utf-8")
        log.info("event validation: %s", summary)
    return events, by_event, by_episode, summary


def summarise(events, touched, by_event, by_episode):
    supply = by_event[(by_event.role == "supply_shortfall") & (by_event.outcome != "no_data")]
    eps = by_episode
    return {
        "events": len(events),
        "countries_with_events": int(touched.iso3.nunique()),
        "supply_event_series": len(supply),
        "supply_event_series_with_label": int((supply.outcome == "label_fired").sum()),
        "episodes": len(eps),
        "episodes_with_supply_event": int((eps.explained_by == "supply_shortfall").sum()),
        "episodes_with_demand_event": int((eps.explained_by == "demand_shock").sum()),
        "episodes_unexplained": int((eps.explained_by == "none").sum()),
        "supply_side_share_explained": _share(eps[eps.explained_by == "supply_shortfall"]),
        "supply_side_share_unexplained": _share(eps[eps.explained_by == "none"]),
    }


def _share(eps):
    """Share of episode months that pass the supply-side unit-value check."""
    return round(float(eps.supply_side_months.sum() / eps.months.sum()), 3) if len(eps) else float("nan")


def report(events, s, by_event, by_episode):
    hit_rate = s["supply_event_series_with_label"] / s["supply_event_series"] if s["supply_event_series"] else float("nan")
    supply = by_event[by_event.role == "supply_shortfall"].copy()
    kgz = by_episode[by_episode.iso3 == "KGZ"]
    lines = [
        "# Shock events and shortfall labels",
        "",
        "Generated by `run.py events` from `config/shock_events.csv`. Method and coding rules: [docs/shock_events.md](../../docs/shock_events.md).",
        "",
        "## Summary",
        "",
        f"- {s['events']} sourced events touch {s['countries_with_events']} panel countries.",
        f"- Supply events with data: {s['supply_event_series']} event-series pairs. The label fired in {s['supply_event_series_with_label']} ({hit_rate:.0%}).",
        f"- Label episodes: {s['episodes']}. With a supply event: {s['episodes_with_supply_event']}. With a demand shock: {s['episodes_with_demand_event']}. "
        f"With no documented supply or demand event: {s['episodes_unexplained']}.",
        f"- Months passing the supply-side unit-value check: {s['supply_side_share_explained']:.0%} in episodes with a supply event, "
        f"{s['supply_side_share_unexplained']:.0%} in episodes without one.",
        "",
        "Most label episodes have no documented event behind them, and documented events often leave no label. "
        "The labels are a weak proxy and must not be used as ground truth for a shortfall classifier. "
        "Absence of a documented event is not proof that nothing happened: the calendar is built from English-language "
        "press and official sources and is thinner for small markets.",
        "",
        "## Supply events: did the label fire?",
        "",
        "| Event | Series | Window | Evaluable | Flagged | Min ratio | Outcome |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in supply.sort_values(["event_id", "iso3", "product_group"]).itertuples():
        ratio = "" if pd.isna(r.min_ratio) else f"{r.min_ratio:.2f}"
        lines.append(f"| {r.event_id} | {r.iso3} {r.product_group} | {r.window_start} to {r.window_end} | {r.evaluable_months} | {r.flagged_months} | {ratio} | {r.outcome} |")
    lines += ["", "## Kyrgyz label episodes", "", "| Product | Start | End | Min ratio | Supply-side months | Events | Context | Explained by |", "|---|---|---|---|---|---|---|---|"]
    for r in kgz.itertuples():
        lines.append(f"| {r.product_group} | {r.start} | {r.end} | {r.min_ratio:.2f} | {r.supply_side_months} | {r.events or '-'} | {r.context_events or '-'} | {r.explained_by} |")
    lines += ["", "Full tables: `tables/event_label_check.csv` and `tables/label_episodes_vs_events.csv`.", ""]
    return "\n".join(lines)
