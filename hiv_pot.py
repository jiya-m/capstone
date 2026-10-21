"""MOU countries: the US HIV money under each America First MOU as one fungible pot, and how to split it across HIV
services.

Pot in year t = the MOU's US amount that year x the HIV share of US health aid (IHME, US HIV aid / all US health aid,
2021-2023 average). It replaces US bilateral and NGO HIV money; every other donor's HIV money follows the Announced
donor cuts. Systems and management money keeps its current share of the pot (it has no service effect in the model),
so the rest, the service pot, is what is split across ART, PMTCT, prevention and orphan support, three ways:

  current   - by today's US split across those services
  minimax   - smallest worst coverage drop: each dollar goes to the service (ART or PMTCT, the HIV services with a
              coverage figure) whose coverage is falling most; prevention and orphan support keep their current share
  people    - fewest people losing services: each dollar goes where it keeps the most people served (people on ART,
              women on PMTCT, children supported, infections averted)

Money to people and coverage uses the same per-dollar rates as run_country (unit cost, donor-funded pool, continuity),
taken from a 1% cut of US direct HIV money; they are linear in money lost, capped at the people covered today.
Feeds: the "MOU HIV Money" section of the Dashboard (model_section.mou_hiv_section).
"""
import numpy as np
import pandas as pd

import health_model as hm
import scenarios as scn

US = "United States"
HIV_LINES = hm.DIRECT["HIV"]                       # ART, PMTCT, prevention, orphan support
COV_LINES = ["hiv_art", "hiv_pmtct"]               # the HIV services with a coverage figure
YEARS = [hm.YEAR0 + t for t in range(hm.N_YEARS)]
OBJECTIVES = {"current": "Current split", "minimax": "Smallest worst drop", "people": "Fewest people lost"}
MOU_YEARS = 5                                      # an MOU with only a total is spread evenly over 2026-2030
STEPS = 2000                                       # the pot is handed out in this many equal pieces


def mou_us_by_year(iso3: str, ci: pd.DataFrame, signed: pd.DataFrame | None = None):
    """US$ the MOU gives each year 2026-2030 (nominal, as written): the year-by-year schedule, with the last year held
    after it ends, else the MOU total / 5 each year. None without a signed MOU with an amount."""
    signed = scn.mou_signed() if signed is None else signed
    if iso3 not in set(signed["iso3"]):
        return None
    r = ci.loc[iso3] if iso3 in ci.index else pd.Series(dtype=float)
    if pd.notna(r.get(f"mou_us_{YEARS[0]}")):
        out, last = [], None
        for y in YEARS:
            v = r.get(f"mou_us_{y}")
            last = float(v) if pd.notna(v) else last
            out.append(last)
        return np.array(out)
    tot = signed.set_index("iso3")["us_funding_total"].get(iso3) if "us_funding_total" in signed else np.nan
    return np.full(len(YEARS), float(tot) / MOU_YEARS) if pd.notna(tot) and tot > 0 else None


def hiv_share(iso3: str, inputs: dict) -> float:
    """US HIV aid / all US health aid (IHME, 2021-2023 average, every channel)."""
    lines, ci = inputs["lines"], inputs["ci"]
    us = lines[(lines.iso3 == iso3) & (lines.src_grp == US)]
    tot = float(ci.loc[iso3].get("us_health_aid_base", np.nan)) if iso3 in ci.index else np.nan
    return float(us[us.bucket == "HIV"].usd.sum() / tot) if tot and tot > 0 else np.nan


def _lines(res):
    return res["lines"].set_index("line").reindex(HIV_LINES)


def pot_inputs(iso3: str, inputs: dict, ptab: pd.DataFrame) -> dict | None:
    """Everything the split needs for one country: pot each year, US direct HIV money now, the service part of it by
    line (E), people and coverage points per dollar lost by line, other donors' HIV loss by line and year (O), and
    the most people each line can lose (people covered today)."""
    ci = inputs["ci"]
    mou = mou_us_by_year(iso3, ci)
    share = hiv_share(iso3, inputs)
    if mou is None or not np.isfinite(share) or share <= 0:
        return None
    cells = inputs["lines"][inputs["lines"].iso3 == iso3]
    us_direct = cells[(cells.src_grp == US) & cells.chan_grp.isin(hm.DIRECT_CHANNELS) & (cells.bucket == "HIV")]
    D = float(us_direct.usd.sum())
    if D <= 0:
        return None
    fiscal = hm.Fiscal("none")
    # 1% cut of US direct HIV money: per-dollar rates and (x100) the service money it pays for by line
    probe = _lines(hm.run_country(iso3, hm.Scenario(src_direct={US: 1.0}, bucket_only="HIV", scale=0.01), fiscal,
                                  inputs, ptab, n_draws=2))
    net1 = probe["net_loss_2026"].fillna(0.0)
    E = net1 * 100
    per = lambda col: (probe[col].fillna(0.0) / net1.where(net1 > 0)).fillna(0.0)  # noqa: E731
    ku, kp = per("units_lost_2026"), per("cov_drop_pp_2026")
    # other donors: Announced donor cuts on HIV with US bilateral and NGO money left out (the pot replaces it)
    sc = scn.build_scenario(scn.ANNOUNCED, scn.default_opts(scn.ANNOUNCED, ci), ci)
    sc.bucket_only = "HIV"
    amap = dict(inputs.get("announce_map") or hm._announcement_cuts_default())
    for c in set(us_direct.chan_grp):
        amap[(iso3, US, c)] = np.zeros(hm.N_YEARS)
    other = _lines(hm.run_country(iso3, sc, fiscal, {**inputs, "announce_map": amap}, ptab, n_draws=2))
    O = other[[f"net_loss_{y}" for y in YEARS]].fillna(0.0).clip(lower=0.0).to_numpy()
    need, cov0 = probe["need"], probe["cov0"]
    covered = (need * cov0).fillna(np.inf)
    covered["hiv_art"] = max(covered["hiv_art"] - covered["hiv_pmtct"], 0.0) if np.isfinite(covered["hiv_pmtct"]) \
        else covered["hiv_art"]
    pot = mou * share
    return {"iso3": iso3, "mou": mou, "share": share, "pot": pot, "D": D, "E": E.to_numpy(),
            "service_share": float(E.sum() / D), "service_pot": np.minimum(pot, D) * float(E.sum() / D),
            "ku": ku.to_numpy(), "kp": kp.to_numpy(), "O": O, "covered": covered.to_numpy(),
            "need": need.to_numpy(), "cov0": cov0.to_numpy()}


def _units(net, ku, covered):
    return np.minimum(ku * np.maximum(net, 0.0), covered)


def allocate(budget: float, E, O_t, ku, covered, need, objective: str) -> np.ndarray:
    """US$ of the service pot to each HIV line in one year (never more than the US money the line has now)."""
    E = np.asarray(E, dtype=float)
    if budget >= E.sum():
        return E.copy()
    prop = budget * E / E.sum() if E.sum() > 0 else np.zeros_like(E)
    if objective == "current":
        return prop
    x = np.zeros_like(E)
    cov_idx = [HIV_LINES.index(l) for l in COV_LINES]
    if objective == "minimax":                       # prevention and orphan support keep their current share
        for i in range(len(E)):
            if i not in cov_idx:
                x[i] = prop[i]
    left = budget - x.sum()
    step = budget / STEPS
    while left > 1e-6:
        s = min(step, left)
        net = O_t + E - x
        room = E - x > 1e-9
        if objective == "minimax":
            drop = np.where(np.isfinite(need) & (need > 0), _units(net, ku, covered) / np.where(need > 0, need, 1), -1.0)
            cand = [i for i in cov_idx if room[i] and drop[i] > 0]
            if not cand:                             # coverage lines whole: the rest by current share
                cand = [i for i in range(len(E)) if room[i]]
            i = max(cand, key=lambda k: drop[k])
        else:
            gain = _units(net, ku, covered) - _units(net - s, ku, covered)
            i = max((k for k in range(len(E)) if room[k]), key=lambda k: gain[k])
        g = min(s, E[i] - x[i])
        x[i] += g
        left -= g
    return x


def hiv_pot(iso3: str, inputs: dict, ptab: pd.DataFrame) -> dict | None:
    """The pot and its three splits: a long table (objective, year, line, US$ to the line, money lost, people losing
    the service, coverage drop in points, coverage %) plus the pot inputs. None for a country without an MOU amount."""
    pi = pot_inputs(iso3, inputs, ptab)
    if pi is None:
        return None
    rows = []
    for obj in OBJECTIVES:
        for t, y in enumerate(YEARS):
            x = allocate(pi["service_pot"][t], pi["E"], pi["O"][:, t], pi["ku"], pi["covered"], pi["need"], obj)
            net = pi["O"][:, t] + pi["E"] - x
            units = _units(net, pi["ku"], pi["covered"])
            for i, l in enumerate(HIV_LINES):
                ok = np.isfinite(pi["need"][i]) and pi["need"][i] > 0
                drop = units[i] / pi["need"][i] * 100 if ok else np.nan
                rows.append({"objective": obj, "year": y, "line": l, "label": hm.LINE_LABELS[l], "alloc_usd": x[i],
                             "us_now_usd": pi["E"][i], "net_loss_usd": net[i], "units_lost": units[i],
                             "cov_drop_pp": drop,
                             "cov_pct": pi["cov0"][i] * 100 - drop if ok else np.nan})
    return {**pi, "table": pd.DataFrame(rows)}
