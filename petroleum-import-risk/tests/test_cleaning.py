import numpy as np
import pandas as pd

from src.ingestion.comtrade_client import ComtradeClient, task_id
from src.preprocessing.cleaning import resolve_mass


def row(net, qty, unit="kg", value=100.0, alt=0.0, alt_unit="N/A"):
    return dict(netWgt=net, qty=qty, qtyUnitAbbr=unit, altQty=alt, altQtyUnitAbbr=alt_unit, primaryValue=value,
                isNetWgtEstimated=False, isQtyEstimated=False)


def resolve(*rows):
    return resolve_mass(pd.DataFrame(rows))


def test_net_weight_preferred():
    r = resolve(row(2000.0, 9999.0)).iloc[0]
    assert r.mass_t == 2.0 and r.mass_source == "netWgt"


def test_zero_net_recovers_quantity_in_kg():
    r = resolve(row(0.0, 107037530.0)).iloc[0]
    assert r.mass_t == 107037.53 and r.mass_source == "qty_kg"


def test_physically_impossible_quantity_is_rejected():
    """Russia 271012 Oct 2017: 107,037,530 kg against 75,576 thousand litres is 1.42 kg/L."""
    r = resolve({**row(0.0, 107037530.0, alt=75576.0, alt_unit="1000 L"), "product_group": "gasoline"}).iloc[0]
    assert np.isnan(r.mass_t) and r.mass_source == "qty_rejected_density" and r.volume_kl == 75576.0


def test_plausible_density_keeps_quantity():
    r = resolve({**row(0.0, 74000000.0, alt=100000.0, alt_unit="1000 L"), "product_group": "gasoline"}).iloc[0]
    assert r.mass_t == 74000.0 and r.mass_source == "qty_kg"


def test_litres_are_never_converted():
    r = resolve(row(0.0, 5000.0, unit="l")).iloc[0]
    assert np.isnan(r.mass_t) and r.mass_source == "none"


def test_positive_value_without_mass_is_missing_not_zero():
    r = resolve(row(np.nan, 0.0, unit=None, value=5905686.0)).iloc[0]
    assert np.isnan(r.mass_t) and r.mass_source == "none"


def test_empty_row_is_marked_no_trade():
    assert resolve(row(0.0, 0.0, value=0.0)).iloc[0].mass_source == "no_trade_row"


def test_validate_rejects_count_mismatch():
    rows, problem = ComtradeClient.validate({"count": 3, "data": [{}], "error": ""})
    assert problem and len(rows) == 1


def test_validate_rejects_api_error():
    assert ComtradeClient.validate({"data": [], "error": "bad"})[1]


def test_split_prefers_period_then_code():
    p = {"period": "201501,201502", "cmdCode": "2710,271012"}
    assert [c["period"] for c in ComtradeClient._split(p)] == ["201501", "201502"]
    assert ComtradeClient._split({"period": "201501", "cmdCode": "2710"}) is None


def test_task_id_is_stable_and_param_sensitive():
    a = {"reporterCode": 417, "period": "201501", "flowCode": "M"}
    assert task_id("d", a) == task_id("d", dict(reversed(list(a.items()))))
    assert task_id("d", a) != task_id("d", {**a, "flowCode": "X"})
