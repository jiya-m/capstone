"""Tests for the 'Announced donor cuts' preset (announcement_model/). Run:  python -m pytest tests"""
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

I, P = hm.load_inputs(), hm.load_params()
CI, AMAP = I["ci"], I["announce_map"]
NONE = hm.Fiscal(*scn.DEFAULT_FISCAL)
ANN = scn.ANNOUNCED
SC = scn.build_scenario(ANN, scn.default_opts(ANN, CI), CI)
CSV = pd.read_csv(hm.MODEL_DIR / hm.ANNOUNCE_FILE)


def test_file_covers_every_country_and_cuts_are_bounded():
    assert set(I["lines"].iso3) - set(CSV.iso3) <= {"GUY"}     # no 2023 IHME baseline: pooled path
    gy = I["lines"][I["lines"].iso3 == "GUY"]
    assert (SC.cuts_by_year(gy, "GUY", I["trend_map"], AMAP)[:, 2] * gy.usd.to_numpy()).sum() > 0
    cuts = CSV[[f"cut_{y}" for y in scn.YEARS]].to_numpy()
    known = CSV[[f"known_cut_{y}" for y in scn.YEARS]].to_numpy()
    assert np.all((cuts >= -1) & (cuts <= 1)) and np.all((known >= -1) & (known <= 1))


def test_preset_registered():
    assert ANN in scn.PRESETS and ANN in scn.PRECOMPUTED_PRESETS
    assert scn.UI_PRESETS == [ANN, "Custom"]
    assert SC.announcement and not scn.build_scenario("Full US exit", scn.default_opts("Full US exit", CI), CI).announcement


def test_cells_take_their_own_yearly_path():
    cells = I["lines"][I["lines"].iso3 == "ZMB"]
    cuts = SC.cuts_by_year(cells, "ZMB", I["trend_map"], AMAP)
    row = CSV[(CSV.iso3 == "ZMB") & (CSV.src_grp == "United States") & (CSV.chan_grp == "Bilateral agency")].iloc[0]
    want = [row[f"cut_{y}"] for y in scn.YEARS]
    us_bil = ((cells.src_grp == "United States") & (cells.chan_grp == "Bilateral agency")).to_numpy()
    assert us_bil.any()
    assert np.allclose(cuts[us_bil], want)
    assert (np.diff(want) > -1e-3).all() and want[-1] > want[0] + 0.2   # the similar countries' path deepens


def test_without_the_file_nothing_is_cut():
    cells = I["lines"][I["lines"].iso3 == "ZMB"]
    assert np.all(SC.cuts_by_year(cells, "ZMB", I["trend_map"], {}) == 0)


def test_run_country_and_precomputed_file():
    r = hm.run_country("ZMB", SC, NONE, I, P, n_draws=100)
    lost = r["years"]["aid_lost_usd"].to_numpy()
    assert np.all(lost > 0) and np.all(np.diff(lost) > 0)
    assert r["totals"]["deaths_5y"] > 0
    pre = pd.read_csv(scn.precomputed_path(hm.MODEL_DIR, ANN))
    assert len(pre) == I["lines"].iso3.nunique()


def test_inputs_cached_before_the_file_existed_still_cut():
    """A running app keeps load_inputs() cached across a code update, so its inputs can lack announce_map."""
    stale = {k: v for k, v in I.items() if k != "announce_map"}
    r = hm.run_country("ZMB", SC, NONE, stale, P, n_draws=50)
    assert r["years"]["aid_lost_usd"].gt(0).all()


def test_global_fund_cut_is_the_allocation_not_stacked_on_donor_cuts():
    """Every donor's Global Fund money in a country gets the same cut (the country's allocation ratio): the Global
    Fund cuts because donors cut, so a donor's own cut is never applied on top. 2026-2027 are the published
    allocations; from 2028 the GC7 -> GC8 change continues at the same yearly rate (predicted)."""
    gf = CSV[(CSV.iso3 == "ZMB") & (CSV.chan_grp == "Global Fund")]
    assert len(gf) > 3
    cut = gf[[f"cut_{y}" for y in scn.YEARS]].to_numpy()
    known = gf[[f"known_cut_{y}" for y in scn.YEARS]].to_numpy()
    assert np.allclose(cut.std(0), 0, atol=1e-3)
    assert np.allclose(cut[:, :2], known[:, :2]) and np.allclose(known[:, 2:], 0)
    kept27 = 1 - cut[0, 1]
    assert np.allclose(1 - cut[0, 2:], kept27 * kept27 ** (np.arange(1, 4) / 3), atol=1e-3)


def test_total_health_aid_uses_the_2019_2023_average():
    """The money headline covers all health aid against the 2019-2023 average, COVID-19 money included."""
    tot = hm.announcement_totals()
    assert 1.2e9 < tot["KEN"]["base"] < 1.4e9                  # Kenya: 1.30, 1.40, 1.47, 1.30, 0.94 $B
    for iso in ("KEN", "ZMB"):
        t = tot[iso]
        assert np.all(t["lost"] > 0) and np.all(t["known"] <= t["lost"] + 1)
    assert tot["KEN"]["lost"][-1] > tot["KEN"]["lost"][0]       # the MOU cliff in 2030


def test_donor_cut_is_uniform_across_its_predicted_channels():
    de = CSV[(CSV.iso3 == "ZMB") & (CSV.src_grp == "Germany") & ~CSV.chan_grp.isin(["Global Fund", "Gavi"])]
    assert len(de) > 1 and np.allclose(de["cut_2028"], de["cut_2028"].iloc[0], atol=1e-3)


def test_known_loss_is_part_of_total_loss():
    for iso in ("ZMB", "KEN", "GUY"):
        cells = I["lines"][I["lines"].iso3 == iso]
        total = np.clip((cells.usd.to_numpy()[:, None] * SC.cuts_by_year(cells, iso, I["trend_map"], AMAP)).sum(0), 0, None)
        known = hm.known_loss_by_year(iso, I)
        assert np.all(known <= total + 1)
    assert hm.known_loss_by_year("KEN", I).sum() > 0            # MOU + Global Fund
