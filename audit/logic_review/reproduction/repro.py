"""Independent reproduction of the funding-cut model from audit/logic_review/logic.md (sections 0-6),
with gaps filled from audit/METHOD.md where noted (see notes.md). Central values only.

Usage: python repro.py [--resurgence-exp t|t-1]
"""
import sys
import math
import numpy as np
import pandas as pd

from pathlib import Path
REPO = str(Path(__file__).resolve().parents[3])
OUT = str(Path(__file__).resolve().parent)

RES_EXP = "t"  # malaria resurgence exponent: 't' = years the cut has lasted (logic.md literal), 't-1' = METHOD.md
if "--resurgence-exp" in sys.argv:
    RES_EXP = sys.argv[sys.argv.index("--resurgence-exp") + 1]

P = pd.read_csv(f"{REPO}/model_params.csv").set_index("param")["central"].astype(float).to_dict()
CI = pd.read_csv(f"{REPO}/model_data/country_inputs.csv").set_index("iso3")
DAH = pd.read_csv(f"{REPO}/model_data/dah_lines.csv")
UCR = pd.read_csv(f"{REPO}/unit_cost_reference.csv")

YEARS = 5
DIRECT_CH = {"Bilateral agency", "NGOs", "Gates direct", "Other"}
BUCKETS = {
    "HIV": dict(direct=["hiv_art", "hiv_pmtct", "hiv_prev", "hiv_ovc"], care="hiv_care_ct", unspec="hiv_unspec", hss="hiv_hss"),
    "TB": dict(direct=["tb_ds", "tb_dr"], care=None, unspec="tb_unspec", hss="tb_hss"),
    "Malaria": dict(direct=["mal_itn", "mal_irs", "mal_cm"], care=None, unspec="mal_unspec", hss="mal_hss"),
    "Immunization": dict(direct=["imm"], care=None, unspec=None, hss=None),
}
ALL_LINES = sorted(DAH.line.unique())
OUT_LINES = ["hiv_art", "hiv_pmtct", "hiv_prev", "tb_ds", "tb_dr", "mal_itn", "mal_irs", "mal_cm", "imm"]
HIV_LINES = ["hiv_art", "hiv_pmtct", "hiv_prev"]

LAG = {"hiv_pmtct": [0.6, 1, 1, 1, 1], "tb_ds": [0.7, 1, 1, 1, 1], "tb_dr": [0.7, 1, 1, 1, 1],
       "mal_itn": [0.5, 1, 1, 1, 1], "mal_irs": [0.8, 1, 1, 1, 1], "mal_cm": [1, 1, 1, 1, 1]}
ART_HZ = [0.012, 0.028, 0.038, 0.045, 0.050]
IMM_W = [0.40, 0.35, 0.20, 0.05]
DR_TB_SHARE, DR_TB_COV = 0.04, 0.45
CPI = {2018: 304.702 / 251.107, 2020: 304.702 / 258.811, 2023: 1.0}  # METHOD.md (logic.md gives no factor)

# ---------------------------------------------------------------- scenarios
def cut_full_us_exit(src, ch):
    if src != "United States":
        return 0.0
    pairs = {"WHO": 1.0, "Gavi": 1.0, "UNFPA": 1.0, "Global Fund": 0.23}
    x = 1.0 if ch in DIRECT_CH else 0.0  # US multilateral cut = 0 apart from the pairs (METHOD.md)
    if ch in pairs:
        x = pairs[ch]
    y = 0.0
    return float(np.clip(1 - (1 - x) * (1 - y), -1, 1))


OECD = {"United States": 0.57, "Germany": 0.174, "France": 0.109, "United Kingdom": 0.108, "Japan": 0.056}


def cut_oecd(src, ch):
    x = OECD.get(src, 0.0)  # same cut on bilateral and multilateral money
    return float(np.clip(1 - (1 - x) * (1 - 0.0), -1, 1))


CASES = {
    1: dict(cut=cut_full_us_exit, path=[1, 1, 1, 1, 1], gov="none"),
    2: dict(cut=cut_full_us_exit, path=[1, 1, 1, 1, 1], gov="custom", theta=0.25),
    3: dict(cut=cut_oecd, path=[1, 1, 1, 1, 1], gov="none"),
    4: dict(cut=cut_full_us_exit, path=[0.2, 0.4, 0.6, 0.8, 1.0], gov="none"),
}

# ---------------------------------------------------------------- global mix (used only if a country has no base in K_b)
def known_lines(b):
    cfg = BUCKETS[b]
    return cfg["direct"] + ([cfg["care"]] if cfg["care"] else [])


GLOBAL_BASE = DAH.groupby("line").usd.sum().to_dict()


def mix_for(base, b):
    K = known_lines(b)
    tot = sum(base.get(l, 0.0) for l in K)
    src = base if tot > 0 else GLOBAL_BASE
    tot = sum(src.get(l, 0.0) for l in K)
    return {l: (src.get(l, 0.0) / tot if tot > 0 else 0.0) for l in K}


def effective(G, base):
    """G: dict line -> amount. Returns (E dict for direct lines + care kappa part, nonservice total)."""
    k = P["hss_kappa"]
    E, ns = {}, 0.0
    for b, cfg in BUCKETS.items():
        mix = mix_for(base, b)
        U = G.get(cfg["unspec"], 0.0) if cfg["unspec"] else 0.0
        S = G.get(cfg["hss"], 0.0) if cfg["hss"] else 0.0
        for l in cfg["direct"]:
            E[l] = G.get(l, 0.0) + (U + k * S) * mix[l]
        mc = 0.0
        if cfg["care"]:
            c = cfg["care"]
            mc = mix[c]
            pool = G.get(c, 0.0) + (U + S) * mc
            E[c] = k * pool
            ns += (1 - k) * pool
        ns += (1 - k) * S * (1 - mc)
    return E, ns

# ---------------------------------------------------------------- country epi / costs
def nz(v, default=np.nan):
    return default if (v is None or (isinstance(v, float) and math.isnan(v))) else v


def unit_costs(r, iso):
    markup = 1 / (1 - P["asd_share"])
    gdp = nz(r["gdp_pc"], 1000.0)
    sc = (max(gdp, 200) / 1000) ** P["uc_scale_elast"]
    site = UCR[(UCR.kind == "art_site_cost") & (UCR.key == iso)]
    if len(site):
        s = float(site.value.iloc[0]) * CPI[int(site.cost_year.iloc[0])]
    else:
        arv = float(UCR[(UCR.kind == "art_site_default") & (UCR.key == "arv")].value.iloc[0])
        non = float(UCR[(UCR.kind == "art_site_default") & (UCR.key == "non_arv")].value.iloc[0])
        s = (arv + non * sc) * CPI[2018]
    uc = {"hiv_art": s * P["uc_art_mult"] * markup, "hiv_pmtct": P["uc_pmtct"], "hiv_ovc": P["uc_ovc"]}
    inc = nz(r["sh_hiv_incd_tl"]) / nz(r["sp_pop_totl"]) * 1000
    inc = 0.3 if math.isnan(inc) else float(np.clip(inc, 0.05, 10))
    uc["hiv_prev"] = P["cpia_ref"] * (1 / inc) ** 0.5
    ig = r["income_group"] if r["income_group"] in ("low_income", "lower_middle_income") else "upper_middle_income"
    for l, kind, mult in (("tb_ds", "tb_ds_cost", "uc_tb_mult"), ("tb_dr", "tb_dr_cost", "uc_tb_mult")):
        v = float(UCR[(UCR.kind == kind) & (UCR.key == ig)].value.iloc[0])
        uc[l] = v * P[mult] * markup
    uc.update(mal_itn=P["uc_itn"], mal_irs=P["uc_irs"], mal_cm=P["uc_mal_cm"], imm=P["uc_imm"])
    return uc, inc


def epi(r, Eb, uc):
    art = nz(r["sh_hiv_artc_zs"]) / 100
    pm = nz(r["sh_hiv_pmtc_zs"]) / 100
    if math.isnan(pm):
        pm = art
    tbinc = nz(r["all_forms_of_tb_incidence_estimated"])
    par = nz(r["malaria_pop_at_risk"])
    itn = nz(r["mal_itn_cov"])
    if math.isnan(itn):
        itn = P["mal_itn_default_use"]
    irs_money = Eb["mal_irs"] / uc["mal_irs"] / par if par and par > 0 else np.nan
    irs_money = float(np.clip(irs_money, 0, 1)) if not math.isnan(irs_money) else np.nan
    irs_map = nz(r["mal_irs_cov"])
    irs = irs_money if math.isnan(irs_map) else max(irs_map, nz(irs_money, 0.0))
    cm = nz(r["mal_cm_cov"])
    if math.isnan(cm):
        cm = P["mal_cm_default_cov"]
    need = {"hiv_art": nz(r["plhiv"]), "hiv_pmtct": nz(r["hiv_pos_pregnancies"]), "tb_ds": tbinc,
            "tb_dr": DR_TB_SHARE * tbinc, "mal_itn": par, "mal_irs": par, "mal_cm": nz(r["malaria_cases"]),
            "imm": nz(r["births"]), "hiv_prev": np.nan}
    cov = {"hiv_art": art, "hiv_pmtct": pm, "tb_ds": nz(r["sh_tbs_dtec_zs"]) / 100, "tb_dr": DR_TB_COV,
           "mal_itn": itn, "mal_irs": irs, "mal_cm": cm, "imm": nz(r["sh_imm_idpt"]) / 100, "hiv_prev": np.nan}
    covered = {l: cov[l] * need[l] for l in need}
    covered["hiv_art"] = max(art * need["hiv_art"] - pm * need["hiv_pmtct"], 0.0)
    return need, cov, covered

# ---------------------------------------------------------------- core run
def weib_F(x):
    lam = P["hiv_survival_median"] / math.log(2) ** (1 / 2.25)
    return 1 - math.exp(-((max(x, 0) / lam) ** 2.25))


def run(iso, case):
    cfg = CASES[case]
    r = CI.loc[iso]
    rows = DAH[DAH.iso3 == iso].copy()
    rows["cut"] = [cfg["cut"](s, c) for s, c in zip(rows.src_grp, rows.chan_grp)]
    base = rows.groupby("line").usd.sum().to_dict()
    Eb, nsb = effective(base, base)
    path = cfg["path"]
    G = []  # per year dict
    for t in range(YEARS):
        g = (rows.usd * rows.cut * path[t]).groupby(rows.line).sum().to_dict()
        G.append({l: max(v, 0.0) for l, v in g.items()})
    L = np.array([sum(g.values()) for g in G])
    # government response
    surge = max(0.0, r["ghes_growth_p75"] - max(r["ghes_growth_median"], 0.0))
    stress = float(np.clip(1 - (r["interest_pct_revenue"] - 10) / 40, 0.25, 1))
    capacity = r["ghes_2023"] * surge * stress
    E, NS, N, budget = [], [], [], []
    for t in range(YEARS):
        e, ns = effective(G[t], base)
        want = cfg.get("theta", 0.0) * L[t] if cfg["gov"] == "custom" else 0.0
        R = min(want, capacity)
        bud = min(R, L[t])
        share = bud / L[t] if L[t] > 0 else 0.0  # pro-rata: everything gets budget x its share of the loss
        E.append(e); NS.append(ns); budget.append(bud)
        N.append({l: v - v * share for l, v in e.items()})
    budget = np.array(budget)

    uc, inc = unit_costs(r, iso)
    need, cov, covered = epi(r, Eb, uc)
    cont = P["continuity"]
    units = {l: np.zeros(YEARS) for l in OUT_LINES}
    for t in range(YEARS):
        for l in OUT_LINES:
            if l == "hiv_art":
                n_all = N[t]["hiv_art"] + N[t]["hiv_care_ct"]
                eb_all = Eb["hiv_art"] + Eb["hiv_care_ct"]
                eb_own = Eb["hiv_art"]
            else:
                n_all, eb_all, eb_own = N[t][l], Eb[l], Eb[l]
            c = covered[l]
            if not math.isnan(c) and eb_own / uc[l] > c:
                u = c * n_all / eb_all
            else:
                u = n_all / uc[l]
            u *= (1 - cont)
            if not math.isnan(c):
                u = min(u, c)
            units[l][t] = max(u, 0.0)

    # ---------------- deaths, 10-year arrays (index 0..4 = 2026-30, 5..9 = 2031-35)
    T = 10
    D = {l: np.zeros(T) for l in OUT_LINES}
    INF = {l: np.zeros(T) for l in HIV_LINES}
    a = cov["hiv_art"]
    # PMTCT
    D["hiv_pmtct"][:5] = units["hiv_pmtct"] * P["pmtct_vt_reduction"] * P["pmtct_infant_mort"] * np.array(LAG["hiv_pmtct"])
    INF["hiv_pmtct"][:5] = units["hiv_pmtct"] * P["pmtct_vt_reduction"]
    # TB
    h = nz(r["tb_hiv_share"], 0.0)
    a0 = nz(a, 0.0)
    dcfr = (1 - h) * (P["tb_cfr_untreated_neg"] - P["tb_cfr_treated_neg"]) + \
        h * (P["tb_cfr_untreated_pos"] * (1 - 0.3 * a0) - P["tb_cfr_treated_pos"] * (1 - 0.3 * a0))
    D["tb_ds"][:5] = units["tb_ds"] * dcfr * np.array(LAG["tb_ds"])
    D["tb_dr"][:5] = units["tb_dr"] * P["tb_dr_dcfr"] * np.array(LAG["tb_dr"])
    cfr_un = (1 - h) * P["tb_cfr_untreated_neg"] + h * P["tb_cfr_untreated_pos"] * (1 - 0.3 * a0)
    cfr_tr = (1 - h) * P["tb_cfr_treated_neg"] + h * P["tb_cfr_treated_pos"] * (1 - 0.3 * a0)
    ctb = np.clip(cov["tb_ds"] - units["tb_ds"] / need["tb_ds"], 0, 1)
    for s in range(YEARS):
        sec = (units["tb_ds"][s] + units["tb_dr"][s]) * P["tb_secondary"]
        for lagy in (1, 2):
            t = s + lagy
            c = ctb[min(t, 4)]
            D["tb_ds"][t] += 0.5 * sec * (c * cfr_tr + (1 - c) * cfr_un)
    # Immunization
    u5 = nz(r["sh_dyn_mort"], 50.0)
    tr = nz(r["trend_u5mr"], -0.009)
    level = np.array([P["imm_deaths_per_child_ref"] * P["imm_u5_share"] * np.clip(u5 * (1 + tr) ** t / 50, 0.3, 2.5)
                      for t in range(T)])
    for s in range(YEARS):
        for k, w in enumerate(IMM_W):
            D["imm"][s + k] += units["imm"][s] * w * level[s + k]
    # Malaria
    D0 = nz(r["malaria_deaths"], 0.0)
    if D0 > 0:
        Ev, Ec = P["mal_vc_eff"], P["mal_cm_eff"]
        par, cases = need["mal_itn"], need["mal_cm"]
        n0, r0, cc0 = cov["mal_itn"], cov["mal_irs"], cov["mal_cm"]
        vc = lambda n, rr: 1 - (1 - n) * (1 - rr)
        cv0 = vc(n0, r0)
        tm = nz(r["trend_malaria_deaths"], 0.0)
        for t in range(YEARS):
            n1 = np.clip(n0 - units["mal_itn"][t] / par, 0, 1)
            r1 = np.clip(r0 - units["mal_irs"][t] / par, 0, 1)
            cc1 = np.clip(cc0 - units["mal_cm"][t] / cases, 0, 1)
            rv = (1 - Ev * vc(n1, r1)) / (1 - Ev * cv0)
            rc = (1 - Ec * cc1) / (1 - Ec * cc0)
            tot = D0 * (rv * rc - 1)
            dv, dc = abs(D0 * (rv - 1)), abs(D0 * (rc - 1))
            vshare = tot * dv / (dv + dc) if dv + dc > 0 else 0.0
            cshare = tot * dc / (dv + dc) if dv + dc > 0 else 0.0
            fi, fr = cv0 - vc(n1, r0), cv0 - vc(n0, r1)
            wi = fi / (fi + fr) if fi + fr > 0 else 0.5
            yr = (1 + tm) ** t
            res = (1 + P["mal_resurgence"]) ** ((t + 1) if RES_EXP == "t" else t)
            D["mal_itn"][t] = vshare * wi * LAG["mal_itn"][t] * yr * res
            D["mal_irs"][t] = vshare * (1 - wi) * LAG["mal_irs"][t] * yr * res
            D["mal_cm"][t] = cshare * LAG["mal_cm"][t] * yr
    # ART cohorts
    cohorts = []  # [start_year_index, size]
    off = np.zeros(T)
    prev = 0.0
    hz = [P["art_hazard_mult"] * x for x in ART_HZ]
    for t in range(YEARS):
        u = units["hiv_art"][t]
        if u > prev:
            cohorts.append([t, u - prev])
        elif u < prev:
            drop = prev - u
            for c in reversed(cohorts):  # newest return first
                take = min(c[1], drop); c[1] -= take; drop -= take
                if drop <= 0:
                    break
        prev = u
        dth = inf = 0.0
        for st, sz in cohorts:
            yrs = t - st
            dth += sz * hz[min(yrs, 4)]
            inf += sz * P["art_transmission"] * (0.5 if yrs == 0 else 1.0)
        D["hiv_art"][t] = dth
        INF["hiv_art"][t] = inf
        off[t] = sum(sz for _, sz in cohorts)
    for k in range(5):  # 2031-35
        t = 5 + k
        frac = (1 - P["art_reengage"]) ** (k + 0.5)
        dth = inf = 0.0
        for st, sz in cohorts:
            yrs = t - st
            dth += sz * frac * hz[min(yrs, 4)]
            inf += sz * frac * P["art_transmission"]
        D["hiv_art"][t] = dth
        INF["hiv_art"][t] = inf
        off[t] = sum(sz for _, sz in cohorts) * frac
    INF["hiv_prev"][:5] = units["hiv_prev"]
    # Deaths from new infections (adult: off-ART and prevention)
    cart = np.clip(a - off / need["hiv_art"], 0, 1)
    for src in ("hiv_art", "hiv_prev"):
        for t in range(T):
            risk = cart[t] * P["hiv_inf_death_treated"] + (1 - cart[t]) * P["hiv_inf_death_untreated"]
            tot = 0.0
            for s in range(t + 1):
                tot += INF[src][s] * (weib_F(t - s + 0.5) - weib_F(t - s - 0.5))
            D[src][t] += tot * risk

    out = {"key": f"{iso}|{case}", "T.base": sum(base.values()), "T.gross": L.mean(), "T.replaced": budget.mean(),
           "T.net": (L - budget).mean()}
    out["T.deaths_5y"] = sum(D[l][:5].sum() for l in OUT_LINES)
    out["C.deaths"] = sum(D[l][5:].sum() for l in OUT_LINES)
    for l in OUT_LINES:
        p = f"L.{l}."
        out[p + "base_usd"] = Eb[l]
        out[p + "gross_loss_usd"] = np.mean([E[t][l] for t in range(YEARS)])
        out[p + "net_loss_usd"] = np.mean([N[t][l] for t in range(YEARS)])
        out[p + "unit_cost"] = uc[l]
        out[p + "need"] = need[l]
        out[p + "cov0"] = cov[l]
        out[p + "units_lost"] = units[l].mean()
        out[p + "cov_drop_pp"] = units[l].mean() / need[l] * 100 if need[l] and not math.isnan(need[l]) else np.nan
        out[p + "deaths_5y"] = D[l][:5].sum()
        out[p + "infections_5y"] = INF[l][:5].sum() if l in HIV_LINES else np.nan
    # diagnostics (not in the requested CSV)
    diag = dict(capacity=capacity, care_eb=Eb["hiv_care_ct"], care_gross=np.mean([E[t]["hiv_care_ct"] for t in range(YEARS)]),
                inc_per_1000=inc, art_covered=covered["hiv_art"],
                conservation=max(abs(sum(E[t].values()) + NS[t] - L[t]) for t in range(YEARS)),
                deaths_by_line_after2030={l: D[l][5:].sum() for l in OUT_LINES},
                inf_after2030=INF["hiv_art"][5:].sum())
    return out, diag


if __name__ == "__main__":
    res, diags = [], {}
    for iso in ["KEN", "NGA", "IND", "HND", "MOZ"]:
        for case in CASES:
            o, d = run(iso, case)
            res.append(o); diags[o["key"]] = d
    df = pd.DataFrame(res)
    fn = "independent.csv" if RES_EXP == "t" else "independent_resurgence_tminus1.csv"
    df.to_csv(f"{OUT}/{fn}", index=False)
    pd.set_option("display.width", 250)
    print(df[["key", "T.base", "T.gross", "T.replaced", "T.net", "T.deaths_5y", "C.deaths"]].round(0).to_string())
    for k, d in diags.items():
        print(k, {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in d.items() if kk != "deaths_by_line_after2030"})
