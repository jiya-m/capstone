"""Tests for the MOU HIV pot and its splits (hiv_pot.py). Run:  python -m pytest tests"""
import logging
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import hiv_pot as hp  # noqa: E402

I, P = hm.load_inputs(), hm.load_params()


@pytest.fixture(scope="module")
def ken():
    return hp.hiv_pot("KEN", I, P)


def test_pot_is_mou_times_us_hiv_share(ken):
    us = I["lines"][(I["lines"].iso3 == "KEN") & (I["lines"].src_grp == "United States")]
    share = us[us.bucket == "HIV"].usd.sum() / I["ci"].loc["KEN", "us_health_aid_base"]
    mou = np.array([I["ci"].loc["KEN", f"mou_us_{y}"] for y in hp.YEARS])
    assert ken["share"] == pytest.approx(share)
    assert np.allclose(ken["pot"], mou * share)


def test_mou_with_only_a_total_is_spread_over_five_years():
    tot = hp.scn.mou_signed().set_index("iso3").loc["ZMB", "us_funding_total"]
    assert np.allclose(hp.mou_us_by_year("ZMB", I["ci"]), tot / 5)
    assert hp.mou_us_by_year("GUY", I["ci"]) is None


def test_every_split_spends_the_service_pot_within_us_money(ken):
    T = ken["table"]
    for obj in hp.OBJECTIVES:
        for t, y in enumerate(hp.YEARS):
            d = T[(T.objective == obj) & (T.year == y)]
            assert d.alloc_usd.sum() == pytest.approx(min(ken["service_pot"][t], ken["E"].sum()), rel=1e-6)
            assert (d.alloc_usd.to_numpy() <= ken["E"] + 1e-3).all()


def test_each_split_beats_todays_split_on_its_own_goal(ken):
    T = ken["table"]
    for y in hp.YEARS:
        d = T[T.year == y]
        worst = d.groupby("objective").cov_drop_pp.max()
        people = d.groupby("objective").units_lost.sum()
        assert worst["minimax"] <= worst["current"] + 0.05
        assert people["people"] <= people["current"] + 1
    last = T[T.year == hp.YEARS[-1]]
    assert last.groupby("objective").cov_drop_pp.max()["minimax"] < last.groupby("objective").cov_drop_pp.max()["current"] - 1
