"""Tests for the shock-event calendar and its comparison with shortfall labels. No built data needed."""
import pandas as pd
import pytest

from src.research import events as ev


def monthly_frame(iso3="AAA", product="gasoline", values=None, russia=0.9, start="2015-01-01"):
    months = pd.date_range(start, periods=len(values), freq="MS")
    return pd.DataFrame({"iso3": iso3, "product_group": product, "month": months, "import_mass_t": values,
                         "uv_relative": 1.1, "russia_share": russia})


def event_row(**kw):
    row = {"event_id": "E1", "title": "t", "affected_iso3": "KGZ", "exempt_iso3": None, "origin_iso3": "RUS",
           "product_scope": "gasoline", "event_type": "export_restriction", "role": "supply_shortfall",
           "start_date": pd.Timestamp("2018-01-05"), "end_date": pd.Timestamp("2018-02-10"), "end_basis": "reported",
           "date_precision": "day", "announced_date": pd.NaT, "confidence": "high",
           "source1_publisher": "P", "source1_url": "https://example.org/a", "source2_publisher": None, "source2_url": None,
           "source3_publisher": None, "source3_url": None, "notes": None}
    row.update(kw)
    return pd.DataFrame([row])


def test_calendar_in_config_is_valid():
    events = ev.load_events()
    assert len(events) >= 30
    assert events.source1_url.str.startswith("https://").all()
    assert events.event_id.is_unique


def test_calendar_covers_kyrgyz_and_russian_events():
    ids = set(ev.load_events().event_id)
    assert {"KGZ_2026_SUPPLY_CRISIS", "RUS_2023_GASOLINE_BAN", "RUS_2025_GASOLINE_BAN"} <= ids


@pytest.mark.parametrize("change, message", [
    ({"role": "shock"}, "role"),
    ({"end_basis": "open"}, "end_basis is 'open'"),
    ({"end_date": pd.Timestamp("2017-12-01")}, "before start_date"),
    ({"source1_url": "http://example.org"}, "https link"),
    ({"affected_iso3": "XXX"}, "unknown affected"),
    ({"affected_iso3": "EXPOSED", "origin_iso3": "KAZ"}, "EXPOSED needs"),
    ({"source2_url": "https://example.org/b"}, "both a publisher and a url"),
])
def test_validate_catches_problems(change, message):
    problems = ev.validate(event_row(**change))
    assert any(message in p for p in problems), problems


def test_validate_accepts_good_row():
    assert ev.validate(event_row()) == []


def test_label_fires_when_mass_drops_below_three_quarters():
    values = [100.0] * 36 + [100.0] * 6 + [50.0] * 3 + [100.0] * 9
    labels = ev.label_series(monthly_frame(values=values), "AAA", "gasoline")
    flagged = labels.index[labels.flag]
    # Low months are Jul-Sep 2018. Jul's window is 250/300 = 0.83, so flags run Aug-Oct.
    assert flagged.tolist() == list(pd.date_range("2018-08-01", "2018-10-01", freq="MS"))
    assert labels.loc["2018-09-01", "ratio"] == pytest.approx(0.5)
    assert labels.loc["2018-09-01", "supply_side"]  # uv_relative above 1 in the test data
    eps = ev.episodes(labels)
    assert len(eps) == 1 and eps.months.iloc[0] == 3


def test_label_needs_three_full_months():
    values = [100.0] * 40 + [None] + [100.0] * 5
    labels = ev.label_series(monthly_frame(values=values), "AAA", "gasoline")
    assert not labels.flag.any()
    assert labels.loc["2018-05-01":"2018-07-01", "ratio"].isna().all()


def test_exposed_events_use_supplier_share_and_exemptions():
    values = [100.0] * 48
    monthly = pd.concat([monthly_frame("AAA", values=values, russia=0.9), monthly_frame("BBB", values=values, russia=0.1),
                         monthly_frame("CCC", values=values, russia=0.9)])
    panel = pd.DataFrame({"iso3": ["AAA", "BBB", "CCC"], "product_group": "gasoline"})
    events = event_row(affected_iso3="EXPOSED", exempt_iso3="CCC")
    countries = pd.DataFrame({"iso3": ["AAA", "BBB", "CCC", "KGZ"]})
    assert ev.validate(events, countries) == []
    touched = ev.expand(events, monthly, panel)
    assert touched.iso3.tolist() == ["AAA"]
    assert touched.exposure_share.iloc[0] == pytest.approx(0.9)


def test_episode_is_explained_only_by_overlapping_supply_event():
    values = [100.0] * 36 + [100.0] * 6 + [50.0] * 3 + [100.0] * 9
    monthly = monthly_frame(values=values)
    labels = {("AAA", "gasoline"): ev.label_series(monthly, "AAA", "gasoline")}
    events = pd.concat([event_row(event_id="HIT", affected_iso3="AAA", start_date=pd.Timestamp("2018-07-01"), end_date=pd.Timestamp("2018-09-30")),
                        event_row(event_id="CTX", affected_iso3="AAA", role="context", start_date=pd.Timestamp("2018-01-01"), end_date=pd.Timestamp("2019-01-31")),
                        event_row(event_id="MISS", affected_iso3="AAA", start_date=pd.Timestamp("2016-01-01"), end_date=pd.Timestamp("2016-02-28"))])
    touched = pd.DataFrame({"event_id": ["HIT", "CTX", "MISS"], "role": ["supply_shortfall", "context", "supply_shortfall"],
                            "iso3": "AAA", "product_group": "gasoline", "exposure_share": None, "confidence": "high"})
    out = ev.check_episodes(events, touched, labels)
    assert out.events.tolist() == ["HIT"]
    assert out.context_events.tolist() == ["CTX"]
    assert out.explained_by.tolist() == ["supply_shortfall"]
    by_event = ev.check_events(events, touched, labels).set_index("event_id")
    assert by_event.loc["HIT", "outcome"] == "label_fired"
    assert by_event.loc["MISS", "outcome"] == "no_label"


def test_open_event_runs_to_last_month():
    e = event_row(end_date=pd.NaT, end_basis="open").iloc[0]
    start, end = ev.event_window(e, pd.Timestamp("2018-06-01"))
    assert start == pd.Timestamp("2018-01-01") and end == pd.Timestamp("2018-06-01")
