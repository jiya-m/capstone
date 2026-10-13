"""Tests for the malaria batch (audit I-06, I-11, I-27 and I-17 malaria parts). Run:  python -m pytest tests"""
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import malaria_inputs as mi  # noqa: E402
import model_section as ms  # noqa: E402
import scenarios as scn  # noqa: E402

I, P = hm.load_inputs(), hm.load_params()
CI = I["ci"]
NONE = hm.Fiscal(*scn.DEFAULT_FISCAL)
MODEL = sorted(set(I["lines"].iso3))
MAL = [c for c in MODEL if CI.loc[c, "malaria_deaths"] > 0]


def _map(name, metric=None):
    return mi.at_year(mi.load(name, metric))


# ---------------- I-11 A-D: coverage and cases ----------------
def test_treatment_coverage_is_map_effective_treatment():
    t = _map("treatment", "Effective Treatment")
    for iso in MAL:                                    # every malaria country has a MAP value
        assert CI.loc[iso, "mal_cm_cov"] == pytest.approx(t[iso] / 100)
        assert CI.loc[iso, "mal_cm_cov_source"] == "MAP 2025" and CI.loc[iso, "mal_cm_cov_year"] == 2025
    no_map = sorted(c for c in MODEL if c not in t.index)
    assert no_map == ["EGY", "FJI", "JAM", "JOR", "LBY", "LSO", "MDA", "MNG", "MUS"]
    assert all(CI.loc[c, "mal_cm_cov_source"] == "default" for c in no_map)


def test_cases_are_map_pf_plus_pv():
    pf, pv = _map("pf_cases"), _map("pv_cases")
    for iso in ("NGA", "ETH", "PAK", "KEN"):
        assert CI.loc[iso, "malaria_cases"] == pytest.approx(pf.get(iso, 0) + pv.get(iso, 0))
        assert str(CI.loc[iso, "malaria_cases_source"]).startswith("MAP 2025")
    assert CI.loc["ETH", "malaria_cases"] > pf["ETH"]           # Ethiopia has P. vivax too


def test_bednets_map_else_survey_from_2015_else_default():
    use = _map("itn", "Use")
    assert CI.loc["NGA", "mal_itn_cov"] == pytest.approx(use["NGA"] / 100)
    assert CI.loc["HTI", "mal_itn_cov_source"] == "survey" and CI.loc["HTI", "mal_itn_cov_year"] == 2017
    assert np.isnan(CI.loc["IDN", "mal_itn_cov"]) and CI.loc["IDN", "mal_itn_cov_source"] == "default"  # survey 2007
    assert (pd.to_numeric(CI["mal_itn_cov_year"], errors="coerce").dropna() >= 2015).all()


def test_spraying_map_africa_only():
    irs = mi.load("irs", "Coverage")
    assert CI.loc["NGA", "mal_irs_cov"] == 0 and CI.loc["NGA", "mal_irs_cov_source"] == "MAP 2025"   # real zero
    assert CI.loc["ZMB", "mal_irs_cov"] == pytest.approx(_map("irs", "Coverage")["ZMB"] / 100)
    assert "IDN" not in mi.irs_modelled(irs) and np.isnan(CI.loc["IDN", "mal_irs_cov"])                 # no estimate


def test_spraying_without_map_estimate_uses_what_donor_money_buys():
    r = hm.run_country("IDN", scn.build_scenario("Full US exit", {}, CI), NONE, I, P, n_draws=0)
    L = r["lines"].set_index("line")
    assert L.loc["mal_irs", "cov0"] == pytest.approx(L.loc["mal_irs", "base_usd"] / L.loc["mal_irs", "unit_cost"]
                                                     / L.loc["mal_irs", "need"])
    assert L.loc["mal_irs", "cov_source"] == "implied by donor spending"
    assert L.loc["mal_itn", "cov_source"] == "assumed" and L.loc["mal_cm", "cov_source"] == "MAP 2025"


# ---------------- combined vector control (Lives Saved Tool) ----------------
def test_combined_vector_control_formula():
    row = CI.loc["ZMB"].copy()
    Pc = hm.draw_params(P, 0)
    ep = hm.epi(row, Pc)
    nc = ep["need_cov"]
    par, itn0 = nc["mal_itn"]
    irs0 = nc["mal_irs"][1]
    z = {k: np.zeros(1) for k in ("mal_itn", "mal_irs", "mal_cm")}
    assert all(v[0] == 0 for v in hm.malaria_levels(row, Pc, z, nc).values())
    u = dict(z, mal_itn=np.array([0.1 * par]))
    got = hm.malaria_levels(row, Pc, u, nc)
    Ev, D0 = Pc["mal_vc_eff"][0], row["malaria_deaths"]
    c0, c1 = 1 - (1 - itn0) * (1 - irs0), 1 - (1 - (itn0 - 0.1)) * (1 - irs0)
    assert got["mal_itn"][0] == pytest.approx(D0 * ((1 - Ev * c1) / (1 - Ev * c0) - 1))
    assert got["mal_irs"][0] == pytest.approx(0) and got["mal_cm"][0] == pytest.approx(0)
    # where people are also sprayed, losing a net matters less than with nets alone
    alone = dict(nc, mal_irs=(par, 0.0))
    assert got["mal_itn"][0] < hm.malaria_levels(row, Pc, u, alone)["mal_itn"][0]


def test_each_vector_line_capped_at_its_own_coverage():
    for iso in ("NGA", "ZMB", "UGA", "IDN"):
        L = hm.run_country(iso, scn.build_scenario("Full US exit", {}, CI), NONE, I, P, n_draws=0)["lines"]
        L = L.set_index("line")
        for l in ("mal_itn", "mal_irs", "mal_cm"):
            assert L.loc[l, "units_lost"] <= L.loc[l, "cov0"] * L.loc[l, "need"] + 1e-6
    # MAP shows no spraying in Nigeria, but donor IRS money still buys some: coverage = max(MAP, what money buys)
    L = hm.run_country("NGA", scn.build_scenario("Full US exit", {}, CI), NONE, I, P, n_draws=0)["lines"].set_index("line")
    implied = L.loc["mal_irs", "base_usd"] / L.loc["mal_irs", "unit_cost"] / L.loc["mal_irs", "need"]
    assert CI.loc["NGA", "mal_irs_cov"] == 0 and L.loc["mal_irs", "cov0"] == pytest.approx(implied)
    assert L.loc["mal_irs", "cov_source"].startswith("implied by donor spending; MAP 2025")
    assert L.loc["mal_irs", "deaths_5y"] > 0
    Z = hm.run_country("ZMB", scn.build_scenario("Full US exit", {}, CI), NONE, I, P, n_draws=0)["lines"].set_index("line")
    assert Z.loc["mal_irs", "cov0"] == pytest.approx(CI.loc["ZMB", "mal_irs_cov"])   # MAP above what money buys


# ---------------- I-06: malaria death trend ----------------
def test_trend_is_map_pf_cases_2015_2025_clipped():
    d = mi.load("pf_cases")
    g = d[(d.iso3 == "KEN") & d.year.between(2015, 2025) & (d.value > 0)]
    fit = float(np.expm1(np.polyfit(g["year"], np.log(g["value"]), 1)[0]))
    assert CI.loc["KEN", "trend_malaria_deaths"] == pytest.approx(fit)
    assert CI.loc["ETH", "trend_malaria_deaths"] == 0.05 and CI.loc["ETH", "trend_malaria_deaths_fit"] > 0.05
    assert CI["trend_malaria_deaths"].between(-0.05, 0.05).all()
    assert (CI.loc[["EGY", "JOR", "LBY"], "trend_malaria_deaths"] == 0).all()        # no MAP data: 0
    clipped = CI.loc[MAL, "trend_malaria_deaths_fit"].abs() > 0.05
    assert int(clipped.sum()) == 19


def test_under5_trend_unchanged():
    assert "trend_u5mr" in CI and CI["trend_u5mr"].between(-0.08, 0.02).all()


# ---------------- I-27 (malaria): treatment cost ----------------
def test_malaria_treatment_cost_sourced():
    r = P.loc["uc_mal_cm"]
    assert (r["central"], r["low"], r["high"], r["status"]) == (14, 4, 47, "sourced")
    assert "White et al. 2011" in r["source"]


# ---------------- E and I-17: display ----------------
def test_service_table_shows_source_and_year():
    r = hm.run_country("KEN", scn.build_scenario("Full US exit", {}, CI), NONE, I, P, n_draws=0)
    rows = ms._service_rows(r["lines"][(r["lines"]["base_usd"] > 0) | (r["lines"]["net_loss_usd"] != 0)])
    html = ms._service_table_html(rows, "Kenya", r["totals"])
    assert html.count("(MAP 2025)") == 3                       # bednets, spraying, treatment
    assert {"mal_itn", "mal_irs"} <= set(rows["line"])         # no longer merged


def test_data_years_lists_malaria_as_map_2025():
    t = ms.data_years_table(CI, MODEL)
    for name in ("Malaria cases needing treatment", "Malaria treatment coverage", "Bednet use",
                 "Indoor spraying coverage"):
        assert t.loc[name, "Year"].startswith("2025") and "MAP" in t.loc[name, "Source"]
    assert t.loc["Malaria death trend", "Year"] == "2015-2025"


def test_apply_is_idempotent():
    again = mi.apply(CI)
    for c in ("mal_cm_cov", "mal_itn_cov", "mal_irs_cov", "malaria_cases", "malaria_cases_prev", "trend_malaria_deaths"):
        a, b = CI[c], again[c]
        assert (((a - b).abs() < 1e-9) | (a.isna() & b.isna())).all(), c
