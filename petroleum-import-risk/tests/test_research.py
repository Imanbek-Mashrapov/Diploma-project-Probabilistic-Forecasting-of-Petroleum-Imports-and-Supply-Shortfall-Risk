"""Checks on the final research datasets. These run against built data, so run phase2 first."""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from src.utils.config import DATA, RAW, load_countries, load_settings

R = DATA / "research"


@pytest.fixture(scope="module")
def monthly():
    return pd.read_parquet(R / "petroleum_imports_monthly.parquet")


@pytest.fixture(scope="module")
def bilateral():
    return pd.read_parquet(R / "petroleum_imports_bilateral.parquet")


@pytest.fixture(scope="module")
def concentration():
    return pd.read_parquet(R / "supplier_concentration_monthly.parquet")


def test_monthly_key_is_unique(monthly):
    assert not monthly.duplicated(["iso3", "product_group", "period"]).any()


def test_bilateral_key_is_unique_and_has_no_world_rows(bilateral):
    assert not bilateral.duplicated(["iso3", "product_group", "partner_code", "period"]).any()
    assert (bilateral.partner_code != 0).all()


def test_heading_is_not_in_bilateral(bilateral):
    assert "total_2710" not in set(bilateral.product_group)


def test_every_candidate_country_and_product_is_present(monthly):
    assert set(monthly.iso3) == set(load_countries().iso3)
    assert monthly.groupby("iso3").product_group.nunique().eq(7).all()


def test_target_is_never_filled(monthly):
    """Mass exists only for observed months, and only where the source had mass."""
    assert monthly[monthly.data_status != "observed"].import_mass_t.isna().all()
    assert monthly[monthly.import_mass_t.notna()].import_mass_t_original.notna().all()
    observed = monthly[monthly.import_mass_t.notna()]
    assert (observed.import_mass_t == observed.import_mass_t_original).all()


def test_no_zero_substituted_for_missing(monthly):
    assert (monthly.import_mass_t.dropna() > 0).all()


def test_monthly_equals_sum_of_partners(monthly, bilateral):
    """Totals must come from partners alone, so World rows cannot be double counted."""
    m = monthly[(monthly.product_group == "gasoline") & (monthly.total_source == "partner_sum") & monthly.import_mass_t.notna()]
    b = bilateral[bilateral.product_group == "gasoline"].groupby(["iso3", "period"]).import_mass_t.sum().rename("partner_sum").reset_index()
    joined = m.merge(b, on=["iso3", "period"])
    assert len(joined) == len(m)
    assert np.allclose(joined.import_mass_t, joined.partner_sum)


def test_blend_group_is_the_sum_of_its_parts(monthly):
    w = monthly.pivot_table(index=["iso3", "period"], columns="product_group", values="import_value_usd", aggfunc="sum")
    both = w.dropna(subset=["middle_heavy", "biodiesel_blend", "middle_incl_blends"])
    assert np.allclose(both.middle_heavy + both.biodiesel_blend, both.middle_incl_blends, rtol=1e-6)


def test_concentration_bounds(concentration):
    assert concentration.hhi.between(0, 1.000001).all()
    assert concentration.largest_supplier_share.between(0, 1.000001).all()
    assert (concentration.top3_supplier_share + 1e-9 >= concentration.largest_supplier_share).all()
    assert (concentration.hhi + 1e-9 >= 1 / concentration.active_suppliers).all()


def test_hhi_formula_on_one_month(bilateral, concentration):
    b = bilateral[(bilateral.iso3 == "KGZ") & (bilateral.product_group == "gasoline") & (bilateral.period == 202608) & bilateral.partner_type.isin(["country", "unallocated_nes"])]
    share = b.import_mass_t / b.import_mass_t.sum()
    row = concentration[(concentration.iso3 == "KGZ") & (concentration.product_group == "gasoline") & (concentration.period == 202608)].iloc[0]
    assert row.hhi == pytest.approx((share ** 2).sum())


def test_annual_data_stay_annual():
    assert set(pd.read_parquet(R / "external_indicators_monthly.parquet").frequency) == {"M"}
    assert "year" in pd.read_parquet(R / "external_indicators_annual.parquet").columns


def test_raw_responses_are_unchanged():
    """Every stored Comtrade response still matches the hash taken when it was downloaded."""
    root = RAW / "un_comtrade" / load_settings()["snapshot_id"]
    checked = 0
    for line in (root / "manifest.jsonl").open(encoding="utf-8"):
        rec = json.loads(line)
        if rec.get("sha256"):
            assert hashlib.sha256((root / rec["file"]).read_bytes()).hexdigest() == rec["sha256"]
            checked += 1
    assert checked > 800


def test_version_hashes_match():
    version = json.loads((R / "VERSION.json").read_text(encoding="utf-8"))
    for name, meta in version["files"].items():
        assert hashlib.sha256((R / name).read_bytes()).hexdigest() == meta["sha256"]
