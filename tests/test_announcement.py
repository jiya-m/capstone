"""Tests for the 'Announced cuts + donor budget model' preset (announcement_model/). Run:  python -m pytest tests"""
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
    cuts = CSV.filter(like="cut_").to_numpy()
    assert cuts.shape[1] == len(scn.YEARS) and np.all((cuts >= -1) & (cuts <= 1))


def test_preset_registered():
    assert ANN in scn.PRESETS and ANN in scn.PRECOMPUTED_PRESETS
    assert SC.announcement and not scn.build_scenario("Full US exit", scn.default_opts("Full US exit", CI), CI).announcement


def test_cells_take_their_own_yearly_path():
    cells = I["lines"][I["lines"].iso3 == "ZMB"]
    cuts = SC.cuts_by_year(cells, "ZMB", I["trend_map"], AMAP)
    row = CSV[(CSV.iso3 == "ZMB") & (CSV.src_grp == "United States") & (CSV.chan_grp == "Bilateral agency")].iloc[0]
    want = [row[f"cut_{y}"] for y in scn.YEARS]
    us_bil = ((cells.src_grp == "United States") & (cells.chan_grp == "Bilateral agency")).to_numpy()
    assert us_bil.any()
    assert np.allclose(cuts[us_bil], want)
    assert want == sorted(want)                    # the no-MOU signer path deepens every year


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
