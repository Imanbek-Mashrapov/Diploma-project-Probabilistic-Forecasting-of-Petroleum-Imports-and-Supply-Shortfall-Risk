"""API tests for the risk monitor. Need the Phase 3 outputs (python run.py features / backtest / evaluate)."""
import pytest

from src.modeling import panel as pn

pytestmark = pytest.mark.skipif(not (pn.MODELING / "forecasts.parquet").exists(), reason="run the Phase 3 stages first")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from src.monitor.api import app
    return TestClient(app)


def test_health_reports_latest_origin(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_risk_table_probabilities_are_valid_and_sorted(client):
    rows = client.get("/risk").json()["rows"]
    assert len(rows) > 10
    p = [x["p_shortfall"] for x in rows if x["p_shortfall"] is not None]
    assert all(0 <= v <= 1 for v in p) and p == sorted(p, reverse=True)
    assert {x["status"] for x in rows} <= {"green", "amber", "red", "unknown"}


def test_forecast_quantiles_are_ordered_and_history_respects_release(client):
    body = client.get("/forecast/KGZ/gasoline").json()
    for f in body["forecasts"]:
        assert f["q025_t"] <= f["q100_t"] <= f["q500_t"] <= f["q900_t"] <= f["q975_t"]
    origin = body["origin"]
    assert all(h["month"] <= origin for h in body["history"] if h["public_at_origin"])


def test_past_origin_can_be_replayed(client):
    assert client.get("/forecast/KGZ/distillates", params={"origin": "2024-03"}).json()["origin"] == "2024-03"


@pytest.mark.parametrize("path", ["/forecast/XXX/gasoline", "/forecast/KGZ/gasoline?origin=1999-01", "/suppliers/ZZZ/gasoline"])
def test_unknown_inputs_return_404(client, path):
    assert client.get(path).status_code == 404


@pytest.mark.parametrize("path", ["/forecast/KGZ/diesel", "/forecast/KG/gasoline", "/risk?origin=2024-3", "/suppliers/KGZ/gasoline?months=0"])
def test_invalid_inputs_return_422(client, path):
    assert client.get(path).status_code == 422


def test_suppliers_shares_sum_to_one(client):
    s = client.get("/suppliers/KGZ/gasoline").json()["suppliers"]
    assert abs(sum(x["share"] for x in s) - 1) < 1e-9 and s[0]["iso3"] == "RUS"


def test_events_for_kyrgyzstan_include_2026_crisis(client):
    ids = {e["event_id"] for e in client.get("/events/KGZ").json()}
    assert "KGZ_2026_SUPPLY_CRISIS" in ids
