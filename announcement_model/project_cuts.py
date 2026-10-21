"""Predicted health-aid cuts by country, 2026-2028: a four-layer model with Monte Carlo uncertainty.

Flow f = (recipient r, donor d, channel c) with 2023 baseline B_f (IHME DAH, k$, from the announcement workbook).
Projected P_f,y = B_f * m_f,y, where m comes from one of four layers:

  1. Announced (workbook rules: MOUs, Global Fund GC8, Gavi pledges, exits, US via Gavi/WHO = 0): used as is.
     US MOUs: the 16 year-by-year schedules run to 2030 (repo MOU sheet). The 19 whole-agreement ratios are spread over
     the years with the average shape of those 16 schedules (agreements are front-loaded).
  2. Foundations, private and non-DAC: IHME's own 2025 / 2021-23 ratio for that source group (Gates 1.07, etc.).
  3. US bilateral without an MOU: no country-level announcement. Default (Jiya's choice, 2026-10-21): these countries
     follow the signed MOUs' average yearly multiplier (weighted by prior US funding). Alternatives: "wind" (equal steps
     from the 2025 level to zero in 2030) or "cliff" (zero from 2026).
  4. Everything else a DAC donor gives (the residual):
       donor health envelope  H_d,y = B_d * exp(alpha) * O_d,y ^ eps
           O = OECD total-ODA multiplier; alpha, eps fitted across donors on IHME 2025 health vs OECD 2025 total ODA
       pot left after announced items = H_d,y - announced_d,y
       spread over the donor's recipients as m_f = lambda_d,y * (s_rd)^beta, clipped to [0, max(1, H/B)]
           s_rd = donor d's baseline in recipient r; beta fitted on Global Fund GC8 and US MOU cuts vs program size
           lambda solved so the donor's residual adds up to its pot.
Uncertainty: N draws of (alpha, eps) and beta from their estimated sampling distributions.
Years: 2024 = 2023 baseline (pre-cut). 2025 = IHME's 2025 preliminary / 2021-23 ratio by source x channel.
2026-2028 as above. 2029-2030: each donor's 2025-28 OECD trend is extended (log-linear); GC8 and Gavi 6.0 run through
2029 / 2030 and hold; MOU schedules and the no-MOU path keep moving.
Writes model_data/announcement_cuts.csv (the cut on each country x donor group x channel group, 2026-2030, in the
dashboard's groups), which the "Announced cuts + donor budget model" preset reads, plus the full outputs in --out.

Usage (from the repo root):
    python announcement_model/project_cuts.py aid_cut_projections_announcements.xlsx [--nomou signer|wind|cliff]
"""
import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ap = argparse.ArgumentParser()
ap.add_argument("workbook", help="announcement workbook (aid_cut_projections_announcements.xlsx)")
ap.add_argument("--nomou", default="signer", choices=["signer", "wind", "cliff"], help="US path where there is no MOU")
ap.add_argument("--out", default=None, help="folder for the full outputs (default announcement_model/output)")
args = ap.parse_args()
WB, REPO = Path(args.workbook), Path(__file__).resolve().parent.parent
OUTDIR = Path(args.out) if args.out else REPO / "announcement_model" / "output"
OUTDIR.mkdir(parents=True, exist_ok=True)
os.chdir(OUTDIR)
YRS = [2026, 2027, 2028, 2029, 2030]      # modeled years; 2024 = 2023 level, 2025 = IHME 2025 estimate
N_DRAWS = 300
rng = np.random.default_rng(20261021)

b = pd.read_excel(WB, sheet_name="Base_Projection")
oda = pd.read_excel(WB, sheet_name="Donor_ODA").dropna(subset=["IHME source"])
mou = pd.read_excel(WB, sheet_name="US_MOU")
gfa = pd.read_excel(WB, sheet_name="GF_Allocations")
trend = pd.read_csv(REPO / "model_data/ihme_trend.csv")
lines = pd.read_csv(REPO / "model_data/dah_lines.csv")
ci = pd.read_csv(REPO / "model_data/country_inputs.csv", index_col=0)

# --------------------------------------------------------------------------- source / channel groups (repo naming)
NORDIC = {"Denmark", "Finland", "Norway", "Sweden", "Iceland"}
BIG = {"Canada", "France", "Germany", "Japan", "Netherlands"}
def src_grp(s):
    s = str(s)
    if s in ("United_States", "United_Kingdom"):
        return s.replace("_", " ")
    if s in BIG: return s
    if s in NORDIC: return "Nordics"
    if s == "Gates Foundation": return "Gates Foundation"
    if s == "Debt_repayments": return "Development-bank lending"
    if s in ("China", "Non_OECD_DAC_countries", "Non_OECD_non_DAC_countries"): return "Non-DAC governments"
    if s in ("Corporate_donations", "Private_other"): return "Other private"
    if s in ("Other", "Unallocable"): return "Other / unallocable"
    return "Other DAC governments"
def chan_grp(c):
    c = str(c)
    if c.startswith("BIL_") or c.startswith("US bilateral"): return "Bilateral agency"
    if c in ("US NGOs", "International NGOs", "US foundations"): return "NGOs"
    if c == "Gates Foundation": return "Gates direct"
    if "Development Bank" in c or c.startswith("World Bank"): return "Development banks"
    if c == "European Commission": return "EU institutions"
    if c == "PAHO": return "WHO"
    return c
b["src"] = b["IHME source (original donor)"].map(src_grp)
b["chan"] = b["Channel name"].map(chan_grp)
b["iso"] = b["Recipient ISO3"]
B = b["Baseline"].to_numpy(float, copy=True)

# --------------------------------------------------------------------------- layer 4 inputs: envelope fit (alpha, eps)
oda["o25"] = oda["Filled 2025"] / oda["ODA 2024"]
od = oda.dropna(subset=["ODA 2024"])
od = od[od["IHME source"] != "Other_OECD_DAC_countries"].assign(g=lambda d: d["IHME source"].map(src_grp))
og = od.groupby("g")[["ODA 2024", "Filled 2025"]].sum()
og["o25"] = og["Filled 2025"] / og["ODA 2024"]
tr = trend.groupby("src_grp")[["base_usd", "y2025_usd"]].sum()
tr["h25"] = tr.y2025_usd / tr.base_usd
E = og.join(tr, how="inner")
E_fit = E.drop(index="Japan")        # Japan's 2025 is a lumpy Gavi payment (health ratio 1.46 while ODA fell 15%)
env = sm.WLS(np.log(E_fit.h25), sm.add_constant(np.log(E_fit.o25)), weights=E_fit.base_usd).fit()
env_all = sm.WLS(np.log(E.h25), sm.add_constant(np.log(E.o25)), weights=E.base_usd).fit()

# --------------------------------------------------------------------------- beta: how cuts fall by program size
g = gfa[(gfa["GC7 original allocation (US$)"] > 1e6) & (gfa["GC8 allocation (US$)"] > 0)]
gf_fit = sm.OLS(np.log(g["GC8 allocation (US$)"] / g["GC7 original allocation (US$)"]),
                sm.add_constant(np.log(g["GC7 original allocation (US$)"]))).fit()
mm = mou.dropna(subset=["Prior US funding, same length ($M)"])
mm = mm[mm["Multiplier 2028"] > 0]
us_fit = sm.OLS(np.log(mm["Multiplier 2028"]), sm.add_constant(np.log(mm["Prior US funding, same length ($M)"]))).fit()
w1, w2 = 1 / gf_fit.bse.iloc[1] ** 2, 1 / us_fit.bse.iloc[1] ** 2
BETA = (gf_fit.params.iloc[1] * w1 + us_fit.params.iloc[1] * w2) / (w1 + w2)
BETA_SE = (w1 + w2) ** -0.5

# --------------------------------------------------------------------------- layer 3: US bilateral without an MOU
def latest(path, col):
    d = pd.read_csv(path)
    d = d[(d.time >= 2015) & (d.time <= 2024)].dropna(subset=[col]).sort_values("time")
    return d.groupby("geo")[col].last().rename(index=str.upper)
W = REPO / "ext_data"
T = pd.DataFrame({"gdp_pc": latest(W / "reference/wdi/ny_gdp_pcap_cd.csv", "ny_gdp_pcap_cd"),
                  "hiv": latest(W / "wdi/sh_dyn_aids_zs.csv", "sh_dyn_aids_zs"),
                  "malaria": latest(W / "wdi/sh_mlr_incd_p3.csv", "sh_mlr_incd_p3"),
                  "ghed_gdp": latest(W / "reference/wdi/sh_xpd_ghed_gd_zs.csv", "sh_xpd_ghed_gd_zs"),
                  "pop": latest(W / "wdi/sp_pop_totl.csv", "sp_pop_totl")})

isus = (b["Donor group"] == "United_States") & b.Rule.isin(["US MOU", "US non-MOU"])
R = b[isus].groupby("iso").agg(us_base=("Baseline", "sum"), rule=("Rule", "first"))
R["signed"] = (R.rule == "US MOU").astype(int)

# --------------------------------------------------------------------------- US MOU multipliers 2026-2030
sched = ci[[f"mou_us_{y}" for y in YRS]] / 1e6                       # $M, team MOU sheet (16 countries)
M_ = mou.set_index("ISO3")
yby = {}
for iso_, r_ in M_.iterrows():
    prior = r_["Prior US funding per year ($M)"]
    if str(r_["Year-by-year source"]).startswith("User") and iso_ in sched.index and pd.notna(prior):
        v = sched.loc[iso_].to_numpy(float)
        v = pd.Series(v).ffill().to_numpy()                             # schedule ended: hold last year
        yby[iso_] = v / prior
# average shape: each year's amount / that agreement's 5-year mean, over complete 5-year schedules
full = [v for k, v in yby.items() if np.isfinite(sched.loc[k]).all()]
SHAPE5 = np.mean([v / v.mean() for v in full], 0)
SHAPE3 = SHAPE5[:3] / SHAPE5[:3].mean()
mou_mult = dict(yby)
for iso_, r_ in M_.iterrows():
    if iso_ in mou_mult: continue
    f = r_["Flat multiplier (whole agreement)"]
    n = int(r_["Years in agreement"]) if pd.notna(r_["Years in agreement"]) else 5
    shp = SHAPE3 if n <= 3 else SHAPE5
    shp = np.concatenate([shp, np.repeat(shp[-1], 5 - len(shp))])        # after a 3-year agreement: hold last year
    mou_mult[iso_] = f * shp

# --------------------------------------------------------------------------- fixed pieces
rule = b.Rule.to_numpy()
NY = len(YRS)
fixed = np.stack([b[f"Proj {min(y, 2028)}"].to_numpy(float, copy=True) for y in YRS], 1)   # workbook; 2029-30 hold 2028
is_res, is_nm, is_ndac, is_mou = rule == "Residual", rule == "US non-MOU", rule == "Non-DAC", rule == "US MOU"
for i in np.where(is_mou)[0]:
    mm_ = mou_mult.get(b.iso.iat[i])
    if mm_ is not None:
        fixed[i] = b.Baseline.iat[i] * mm_
ndac_ratio = b["src"].map(tr.h25).fillna(1.0).to_numpy(float, copy=True)
ndac_ratio[b["src"].eq("Other / unallocable").to_numpy()] = 1.0                 # IHME 2.3 there is reclassification
# OECD outlook ends in 2028: 2029-30 extend each donor's 2025-28 log-linear trend (flat where only 2025 is reported)
Omult = oda.set_index("IHME source")[["o25", "Mult 2026", "Mult 2027", "Mult 2028"]].astype(float)
slope = (np.log(Omult["Mult 2028"]) - np.log(Omult["o25"])) / 3
for y in (2029, 2030):
    Omult[f"Mult {y}"] = Omult["Mult 2028"] * np.exp(slope * (y - 2028))
Omult = Omult[[f"Mult {y}" for y in YRS]]
donor = b["Donor group"].to_numpy()
dac_donors = [d for d in Omult.index if d in set(donor[is_res])]
s_rd = b.groupby(["Donor group", "iso"]).Baseline.transform("sum").to_numpy(float)

# 2025: IHME preliminary ratio by source x channel (all four disease buckets), falling back to the source ratio
tsc = trend.groupby(["src_grp", "chan_grp"])[["base_usd", "y2025_usd"]].sum()
tsc = (tsc.y2025_usd / tsc.base_usd.where(tsc.base_usd > 1e5)).dropna()
r25 = pd.Series([tsc.get((s_, c_), np.nan) for s_, c_ in zip(b.src, b.chan)]).fillna(b.src.map(tr.h25)).fillna(1.0)
P25 = B * r25.clip(0, 2).to_numpy()

def solve_lambda(base, w, pot, cap):
    """lambda so that sum(base * clip(lambda*w, 0, cap)) = pot."""
    if pot <= 0: return 0.0
    if (base * cap).sum() <= pot: return np.inf
    lo, hi = 0.0, 1.0
    while (base * np.minimum(hi * w, cap)).sum() < pot: hi *= 2
    for _ in range(50):
        mid = (lo + hi) / 2
        if (base * np.minimum(mid * w, cap)).sum() < pot: lo = mid
        else: hi = mid
    return (lo + hi) / 2

# US bilateral without an MOU. NOMOU_PATH = "signer" (default: MOU countries' average yearly multiplier, weighted by
# prior US funding), "wind" (equal steps from the 2025 IHME level to zero in 2030) or "cliff" (zero from 2026).
NOMOU_PATH = args.nomou
r25_row = P25 / np.where(B > 0, B, 1)
if NOMOU_PATH == "wind":
    NOMOU = np.outer(r25_row, [1 - (y - 2025) / 5 for y in YRS])
elif NOMOU_PATH == "signer":
    pr_ = M_["Prior US funding per year ($M)"].groupby(level=0).first()
    ks = [k for k, v in mou_mult.items() if np.isfinite(v).all() and pd.notna(pr_.get(k))]
    avg = np.average(np.stack([mou_mult[k] for k in ks]), axis=0, weights=[pr_[k] for k in ks])
    NOMOU = np.outer(np.ones_like(B), avg)
else:
    NOMOU = np.zeros((len(B), len(YRS)))

def run(alpha, eps, beta):
    """2026-2030 projection for every row (rows x 5) and each donor's envelope."""
    P = fixed.copy()
    P[is_ndac] = (B[is_ndac] * ndac_ratio[is_ndac])[:, None]
    P[is_nm] = B[is_nm, None] * NOMOU[is_nm]          # no MOU: see NOMOU_PATH
    env_out, lam_out = {}, {}
    for d in dac_donors:
        sel = donor == d
        res = sel & is_res
        Bd = B[sel].sum()
        w = s_rd[res] ** beta
        for j, y in enumerate(YRS):
            h = np.exp(alpha) * Omult.at[d, f"Mult {y}"] ** eps
            pot = Bd * h - P[sel & ~is_res, j].sum()
            cap = max(1.0, h)
            lam = solve_lambda(B[res], w, pot, cap)
            P[res, j] = B[res] * (np.minimum(lam * w, cap) if np.isfinite(lam) else cap)
            env_out[(d, y)], lam_out[(d, y)] = h, lam
    return P, env_out, lam_out

a0, e0 = env.params.iloc[0], env.params.iloc[1]
P0, env0, lam0 = run(a0, e0, BETA)
P_noalpha = run(0.0, e0, BETA)[0]                    # no common 2025 health drop beyond the ODA path
P_uniform = run(a0, e0, 0.0)[0]                      # cuts spread evenly (beta = 0)

# Monte Carlo over (alpha, eps) and beta: country totals per year
iso_v = b["iso"].values
cov_env = env.cov_params().to_numpy()
draws = []
for k in range(N_DRAWS):
    a, e = rng.multivariate_normal(env.params.to_numpy(), cov_env)
    P = run(a, e, rng.normal(BETA, BETA_SE))[0]
    draws.append(pd.DataFrame(P, columns=YRS).groupby(iso_v).sum())
DR = np.stack([d.to_numpy() for d in draws], 2)                       # country x year x draw
DR_idx = draws[0].index

# full year table: 2023 (base), 2024, 2025, 2026-2030
ALLY = [2023, 2024, 2025] + YRS
PY = np.column_stack([B, B, P25, P0])
PY_noalpha = np.column_stack([B, B, P25, P_noalpha])
PY_uniform = np.column_stack([B, B, P25, P_uniform])

# --------------------------------------------------------------------------- disease split (repo dah_lines, 70 countries)
cell = ["iso", "src", "chan"]
lb = lines.groupby(["iso3", "src_grp", "chan_grp", "bucket"]).usd.sum().unstack(fill_value=0) / 1e3   # k$
lb.index.names = cell
BUCKETS = ["HIV", "TB", "Malaria", "Immunization"]
cols = {f"y{y}": PY[:, i] for i, y in enumerate(ALLY)}
bc = b[cell].assign(**cols).groupby(cell).sum().join(lb, how="left").fillna(0)
sh = bc[BUCKETS].div(bc["y2023"].where(bc["y2023"] > 0), axis=0).fillna(0)
sh = sh.div(sh.sum(1).clip(lower=1), axis=0)
sh["Other health"] = 1 - sh.sum(1)
DIS = {y: sh.mul(bc[f"y{y}"], axis=0).groupby(level="iso").sum() / 1e3 for y in ALLY}   # $M by disease
has_lines = set(lines.iso3)

# --------------------------------------------------------------------------- channel groups for display
def disp(row):
    c, r_ = row["Channel name"], row.Rule
    if row["Donor group"] == "United_States" and r_ in ("US MOU", "US non-MOU"): return "US bilateral"
    if c == "Global Fund": return "Global Fund"
    if c == "Gavi": return "Gavi"
    if c in ("WHO", "UNICEF", "UNFPA", "UNAIDS", "PAHO"): return "UN agencies"
    if "Development Bank" in c or c.startswith("World Bank"): return "Development banks"
    if r_ == "Non-DAC": return "Foundations & private"
    return "Other donors"
b["disp"] = b.apply(disp, axis=1)
b["layer"] = np.where(is_res, "modeled: donor envelope", np.where(is_nm, "assumed: no MOU, signer path",
             np.where(is_ndac, "data: IHME 2025 trend", "announced")))
out = b[["iso", "Recipient", "Donor group", "Channel name", "disp", "Rule", "layer"]].copy()
for i, y in enumerate(ALLY):
    out[f"y{y}"] = PY[:, i]
out["y2028_noalpha"], out["y2028_uniform"] = P_noalpha[:, 2], P_uniform[:, 2]
out.to_csv("rows_v2.csv", index=False)

# --------------------------------------------------------------------------- GHES (US$ M) for gap ratios
ghes = (ci.ghes_2023 / 1e6).rename("ghes")
ghes_wdi = (T.ghed_gdp / 100 * T.gdp_pc * T["pop"] / 1e6)
pop = T["pop"]
r2 = lambda v: round(float(v), 2)

rows = []
for iso, grp in out.groupby("iso"):
    tot = {y: grp[f"y{y}"].sum() / 1e3 for y in ALLY}
    base = tot[2023]
    di = DR_idx.get_loc(iso)
    rng_ = {y: [r2(base - np.percentile(DR[di, j] / 1e3, 95)), r2(base - np.percentile(DR[di, j] / 1e3, 5))] for j, y in enumerate(YRS)}
    gh = ghes.get(iso, np.nan)
    if not np.isfinite(gh): gh = ghes_wdi.get(iso, np.nan)
    ch = grp.groupby("disp")[[f"y{y}" for y in ALLY]].sum() / 1e3
    lay = grp.groupby("layer")[[f"y{y}" for y in ALLY]].sum() / 1e3
    rec = {"iso3": iso, "country": grp.Recipient.iloc[0], "base": r2(base),
           "years": {y: r2(v) for y, v in tot.items()},
           "gap_range": rng_,
           "gap2028_noalpha": r2(base - grp.y2028_noalpha.sum() / 1e3), "gap2028_uniform": r2(base - grp.y2028_uniform.sum() / 1e3),
           "ghes": None if not np.isfinite(gh) else round(float(gh), 1),
           "pop_m": None if not np.isfinite(pop.get(iso, np.nan)) else round(pop.get(iso) / 1e6, 2),
           "channels": {k: {y: r2(v[f"y{y}"]) for y in ALLY} for k, v in ch.iterrows() if v["y2023"] > 0.05},
           "layers": {k: {y: r2(v["y2023"] - v[f"y{y}"]) for y in ALLY} for k, v in lay.iterrows()},
           "disease": None}
    if iso in has_lines and iso in DIS[2023].index:
        rec["disease"] = {k: {y: r2(DIS[y].at[iso, k]) for y in ALLY} for k in BUCKETS + ["Other health"]}
    if iso in R.index and R.at[iso, "signed"] == 0 and R.at[iso, "us_base"] > 0:
        rec["us_no_mou"] = r2(R.at[iso, "us_base"] / 1e3)
    if iso in mou_mult:
        rec["mou"] = {"mult": [round(float(x), 3) for x in mou_mult[iso]], "yearly": iso in yby}
    rows.append(rec)
rows.sort(key=lambda r: -(r["base"] - r["years"][2028]))

us = donor == "United_States"
tot_y = {y: round(PY[:, i].sum() / 1e3, 1) for i, y in enumerate(ALLY)}
tot_rng = {y: [round(float(np.percentile(DR[:, j].sum(0) / 1e3, 5)), 1), round(float(np.percentile(DR[:, j].sum(0) / 1e3, 95)), 1)] for j, y in enumerate(YRS)}
chan_y = pd.DataFrame(PY, columns=ALLY).groupby(b["disp"].values).sum().div(1e3).round(1)
meta = {
    "alpha": round(a0, 3), "eps": round(e0, 3), "alpha_se": round(env.bse.iloc[0], 3), "eps_se": round(env.bse.iloc[1], 3),
    "env_r2": round(env.rsquared, 2), "env_n": int(env.nobs), "eps_with_japan": round(env_all.params.iloc[1], 3),
    "beta": round(BETA, 3), "beta_se": round(BETA_SE, 3),
    "beta_gf": round(gf_fit.params.iloc[1], 3), "beta_gf_se": round(gf_fit.bse.iloc[1], 3), "n_gf": int(gf_fit.nobs),
    "beta_us": round(us_fit.params.iloc[1], 3), "beta_us_se": round(us_fit.bse.iloc[1], 3), "n_us": int(us_fit.nobs),
    "envelope_points": {k: {"oda25": round(v.o25, 3), "health25": round(v.h25, 3)} for k, v in E.iterrows()},
    "ndac_ratios": {k: round(float(v), 3) for k, v in tr.h25.items()},
    "donors": {d: {"base_musd": round(B[donor == d].sum() / 1e3, 1), **{f"env_{y}": round(env0[(d, y)], 3) for y in YRS},
                   **{f"proj_{y}": round(P0[donor == d, j].sum() / B[donor == d].sum(), 3) for j, y in enumerate(YRS)}} for d in dac_donors},
    "years": ALLY, "total": tot_y, "total_range": tot_rng,
    "total_noalpha": {y: round(PY_noalpha[:, i].sum() / 1e3, 1) for i, y in enumerate(ALLY)},
    "by_channel": {k: v.to_dict() for k, v in chan_y.iterrows()},
    "us_by_year": {y: round(PY[us, i].sum() / 1e3, 1) for i, y in enumerate(ALLY)},
    "us_mou_by_year": {y: round(PY[us & is_mou, i].sum() / 1e3, 1) for i, y in enumerate(ALLY)},
    "us_nomou_base": round(B[is_nm].sum() / 1e3, 1), "n_nomou": int((R.signed == 0).sum()),
    "mou_shape5": [round(float(x), 3) for x in SHAPE5], "n_yby": len(yby), "n_flat": len(mou_mult) - len(yby),
    "nomou_path": NOMOU_PATH, "nomou_mult": [round(float(x), 3) for x in NOMOU[is_nm][0]] if is_nm.any() else [], "oda_29_30": {d: [round(float(Omult.at[d, "Mult 2029"]), 3), round(float(Omult.at[d, "Mult 2030"]), 3)] for d in dac_donors},
    "oecd_us": round(float(Omult.at["United_States", "Mult 2028"]), 3), "us_ihme25": round(float(tr.at["United States", "h25"]), 3),
    "n_draws": N_DRAWS,
}
dis_tot = {k: {y: round(float(DIS[y].loc[DIS[y].index.isin(has_lines), k].sum()), 1) for y in ALLY} for k in BUCKETS + ["Other health"]}
meta["by_disease"] = dis_tot
json.dump({"meta": meta, "rows": rows}, open("results_v2.json", "w"), separators=(",", ":"))

flat = []
for r in rows:
    d = {"iso3": r["iso3"], "country": r["country"]}
    d |= {f"total {y}": v for y, v in r["years"].items()}
    d |= {f"gap {y}": r2(r["base"] - v) for y, v in r["years"].items() if y >= 2025}
    d |= {f"gap {y} 90% low": v[0] for y, v in r["gap_range"].items()} | {f"gap {y} 90% high": v[1] for y, v in r["gap_range"].items()}
    d["gov health spending 2023"] = r["ghes"]
    for k, v in r["channels"].items():
        d |= {f"{k} {y}": v[y] for y in ALLY}
    if r["disease"]:
        for k, v in r["disease"].items():
            d |= {f"{k} {y}": v[y] for y in ALLY}
    flat.append(d)
pd.DataFrame(flat).to_csv("country_gaps_v2.csv", index=False)
with open("fit_v2.txt", "w") as f:
    f.write("ENVELOPE: log(IHME health 2025 ratio) = alpha + eps * log(OECD ODA 2025 ratio), WLS by baseline, Japan excluded\n")
    f.write(env.summary2().as_text() + "\n\nWith Japan:\n" + env_all.summary2().tables[1].to_string() + "\n\n")
    f.write("BETA, Global Fund: log(GC8/GC7) on log(GC7)\n" + gf_fit.summary2().tables[1].to_string() + "\n\n")
    f.write("BETA, US MOU: log(2028 multiplier) on log(prior US funding)\n" + us_fit.summary2().tables[1].to_string() + "\n\n")
    f.write(f"Pooled beta (inverse-variance): {BETA:.4f} (SE {BETA_SE:.4f})\n\n")
    f.write(f"MOU year shape (amount / agreement mean, 2026-2030, {len(full)} complete schedules): {np.round(SHAPE5, 3).tolist()}\n")
# --------------------------------------------------------------------------- dashboard input: cuts in the repo's groups
ex = b[["iso", "src", "chan"]].assign(base=B, **{f"p{y}": P0[:, j] for j, y in enumerate(YRS)})
ex = ex.groupby(["iso", "src", "chan"]).sum()
ex = ex[ex.base > 0]
cuts_out = pd.DataFrame({f"cut_{y}": (1 - ex[f"p{y}"] / ex.base).clip(-1, 1).round(4) for y in YRS})
cuts_out.insert(0, "base_2023_kusd", ex.base.round(1))
cuts_out.index.names = ["iso3", "src_grp", "chan_grp"]
cuts_out.to_csv(REPO / "model_data" / "announcement_cuts.csv")

print(json.dumps({k: meta[k] for k in ["total", "total_range", "us_by_year", "us_mou_by_year", "mou_shape5", "n_yby", "n_flat", "by_disease"]}, indent=0))
print(chan_y)
