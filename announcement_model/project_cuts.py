"""Health-aid cuts by country x donor x channel, 2026-2030: one cut per donor, overridden by known channel numbers.

Flow f = (recipient r, donor d, channel c) with 2023 baseline B_f (IHME DAH, k$, from the announcement workbook).
Projected P_f,y = B_f * m_f,y. Each flow gets exactly one multiplier (nothing is stacked: the Global Fund and Gavi
cut because donors cut, so a donor's cut and a channel's cut are never multiplied together).

KNOWN (a published number for that flow):
  - Global Fund, every donor's money (foundations' and private money included): the recipient's own allocation ratio. 2026 = reduced GC7 / original GC7,
    2027-2030 = GC8 / original GC7 (GC8 runs to 2029; 2030 holds).
  - Gavi: the donor's Gavi 6.0 / 5.0 pledge ratio where it is published (UK, Norway, France); US = 0 (exit).
  - US through WHO = 0 (exit, January 2026).
  - US bilateral and US NGOs in a country with an America First MOU: the MOU's year-by-year schedule (16 countries),
    or its whole-agreement ratio spread over the years with the schedules' average shape (the rest).
  - Donor programme announcements: Sweden's and the UK's country exits, the UK's Africa bilateral path, the
    Netherlands' health budget (EUR 384M / 510M) and its halved UNICEF contribution.
PREDICTED (no published number for that flow):
  - Every other flow from a DAC donor (all channels: bilateral, NGOs, UN agencies, development banks, and Gavi where
    the pledge is not published): the donor's own announced total-aid path (OECD ODA outlook, 2026-2028), the same
    cut on every channel. 2029-2030 extend the donor's 2025-28 log-linear trend.
  - US bilateral in a country without an MOU: the signed MOUs' average yearly multiplier, weighted by prior US funding.
    Income group and the aid / government health spending ratio were tested as predictors of the MOU cut and do not
    beat the plain average out of sample (leave-one-out), so the average is used (see fit_v3.txt).
  - Foundations, private, non-DAC governments, development-bank lending: IHME's 2025 / 2021-23 ratio for the source.
Writes model_data/announcement_cuts.csv: per country x donor group x channel group, the 2023 base and the cut in
each year, split into the known part and the predicted part (cut = known_cut + predicted part).

Usage (from the repo root):
    python announcement_model/project_cuts.py aid_cut_projections_announcements.xlsx
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ap = argparse.ArgumentParser()
ap.add_argument("workbook", help="announcement workbook (aid_cut_projections_announcements.xlsx)")
ap.add_argument("--out", default=None, help="folder for the fit notes (default announcement_model/output)")
args = ap.parse_args()
WB, REPO = Path(args.workbook), Path(__file__).resolve().parent.parent
OUTDIR = Path(args.out) if args.out else REPO / "announcement_model" / "output"
OUTDIR.mkdir(parents=True, exist_ok=True)
YRS = [2026, 2027, 2028, 2029, 2030]

b = pd.read_excel(WB, sheet_name="Base_Projection")
oda = pd.read_excel(WB, sheet_name="Donor_ODA").dropna(subset=["IHME source"])
mou = pd.read_excel(WB, sheet_name="US_MOU")
gfa = pd.read_excel(WB, sheet_name="GF_Allocations").dropna(subset=["ISO3"]).drop_duplicates("ISO3").set_index("ISO3")
trend = pd.read_csv(REPO / "model_data/ihme_trend.csv")
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
rule, donor, iso = b.Rule.to_numpy(), b["Donor group"].to_numpy(), b.iso.to_numpy()
N, NY = len(b), len(YRS)

# --------------------------------------------------------------------------- donor total-aid paths (OECD outlook)
oda["o25"] = oda["Filled 2025"] / oda["ODA 2024"]
Om = oda.set_index("IHME source")[["o25", "Mult 2026", "Mult 2027", "Mult 2028"]].astype(float)
slope = (np.log(Om["Mult 2028"]) - np.log(Om["o25"])) / 3            # 2029-30: extend the 2025-28 trend
for y in (2029, 2030):
    Om[f"Mult {y}"] = Om["Mult 2028"] * np.exp(slope * (y - 2028))
Om = Om[[f"Mult {y}" for y in YRS]]
DAC_ALL = Om.loc["Other_OECD_DAC_countries"].to_numpy()                  # donors with no row of their own
def donor_path(d):
    return Om.loc[d].to_numpy() if d in Om.index else DAC_ALL

# --------------------------------------------------------------------------- US MOU multipliers 2026-2030
sched = ci[[f"mou_us_{y}" for y in YRS]] / 1e6                        # $M, team MOU sheet (16 countries)
M_ = mou.dropna(subset=["ISO3"]).set_index("ISO3")
yby = {}
for k, r in M_.iterrows():
    prior = r["Prior US funding per year ($M)"]
    if str(r["Year-by-year source"]).startswith("User") and k in sched.index and pd.notna(prior):
        yby[k] = pd.Series(sched.loc[k].to_numpy(float)).ffill().to_numpy() / prior   # schedule ended: hold last year
full = [v for k, v in yby.items() if np.isfinite(sched.loc[k]).all()]
SHAPE5 = np.mean([v / v.mean() for v in full], 0)                       # agreements are front-loaded
SHAPE3 = SHAPE5[:3] / SHAPE5[:3].mean()
mou_mult = dict(yby)
for k, r in M_.iterrows():
    if k in mou_mult or pd.isna(r["Flat multiplier (whole agreement)"]):
        continue
    n = int(r["Years in agreement"]) if pd.notna(r["Years in agreement"]) else 5
    shp = SHAPE3 if n <= 3 else SHAPE5
    mou_mult[k] = r["Flat multiplier (whole agreement)"] * np.concatenate([shp, np.repeat(shp[-1], 5 - len(shp))])
prior_w = M_["Prior US funding per year ($M)"].groupby(level=0).first()
ks = [k for k, v in mou_mult.items() if np.isfinite(v).all() and pd.notna(prior_w.get(k))]
SIGNER_AVG = np.average(np.stack([mou_mult[k] for k in ks]), axis=0, weights=[prior_w[k] for k in ks])

# --------------------------------------------------------------------------- does income or aid dependence predict the MOU cut?
def latest(path, col):
    d = pd.read_csv(path)
    d = d[(d.time >= 2015) & (d.time <= 2024)].dropna(subset=[col]).sort_values("time")
    return d.groupby("geo")[col].last().rename(index=str.upper)
W = REPO / "ext_data"
T = pd.DataFrame({"gdp_pc": latest(W / "reference/wdi/ny_gdp_pcap_cd.csv", "ny_gdp_pcap_cd"),
                  "ghed_gdp": latest(W / "reference/wdi/sh_xpd_ghed_gd_zs.csv", "sh_xpd_ghed_gd_zs"),
                  "pop": latest(W / "wdi/sp_pop_totl.csv", "sp_pop_totl")})
ghes = (ci.ghes_2023 / 1e6).combine_first(T.ghed_gdp / 100 * T.gdp_pc * T["pop"] / 1e6)
X = pd.DataFrame({"dah": b.groupby("iso").Baseline.sum() / 1e3, "ghes": ghes, "gdp": T.gdp_pc})
X["lr"] = np.log(X.dah / X.ghes)                                       # log(aid / government health spending)
X["inc"] = pd.cut(X.gdp, [0, 1145, 4515, 1e9], labels=["LIC", "LMIC", "UMIC+"]).astype(str)   # World Bank FY26
D = pd.DataFrame({"f": M_["Flat multiplier (whole agreement)"], "w": M_["Prior US funding, same length ($M)"]})
D = D.groupby(level=0).first().join(X).replace([np.inf, -np.inf], np.nan).dropna(subset=["f", "w", "lr"])
def loo_rmse(formula):
    e = 0.0
    for k in D.index:
        tr = D.drop(k)
        p = (np.average(tr.f, weights=tr.w) if formula is None
             else smf.wls(formula, tr, weights=tr.w).fit().predict(D.loc[[k]]).iloc[0])
        e += (D.at[k, "f"] - p) ** 2 * D.at[k, "w"]
    return np.sqrt(e / D.w.sum())
TESTS = {"average": loo_rmse(None), "f ~ lr": loo_rmse("f ~ lr"), "f ~ C(inc)": loo_rmse("f ~ C(inc)"),
         "f ~ lr + C(inc)": loo_rmse("f ~ lr + C(inc)")}

# --------------------------------------------------------------------------- one multiplier per flow
M = np.ones((N, NY))
known = np.zeros(N, bool)
src_label = np.empty(N, object)
proj = np.stack([b[f"Proj {min(y, 2028)}"].to_numpy(float) for y in YRS], 1) / np.where(B > 0, B, 1)[:, None]
gf26 = b.iso.map(gfa["Ratio 2026 (reduced GC7)"]).to_numpy(float)
gf27 = b.iso.map(gfa["Ratio 2027-28 (GC8)"]).to_numpy(float)
ihme = b.src.map(trend.groupby("src_grp")[["base_usd", "y2025_usd"]].sum().pipe(lambda t: t.y2025_usd / t.base_usd))
ihme = ihme.fillna(1.0).to_numpy(float, copy=True)
ihme[b.src.eq("Other / unallocable").to_numpy()] = 1.0                  # IHME 2.3 there is reclassification
gf_total = 12.64 / 15.7                                                   # GF 8th / 7th replenishment, all donors

for i in range(N):
    r, d = rule[i], donor[i]
    if r == "Global Fund" or b["Channel name"].iat[i] == "Global Fund":     # foundations' GF money too
        a, c = gf26[i], gf27[i]
        if np.isfinite(a) and np.isfinite(c):
            M[i] = [a, c, c, c, c]; known[i] = True; src_label[i] = "Global Fund allocation (GC8)"
        else:
            M[i] = gf_total; src_label[i] = "Global Fund total pledges"
    elif r in ("Gavi", "Exit", "NL health", "NL UNICEF", "UK Africa bilateral"):
        M[i] = proj[i]; known[i] = True
        src_label[i] = {"Gavi": "Gavi pledge", "Exit": "Country exit", "NL health": "Netherlands health budget",
                        "NL UNICEF": "Netherlands health budget", "UK Africa bilateral": "UK Africa path"}[r]
    elif r == "Zero":
        M[i] = 0.0; known[i] = True; src_label[i] = "US exit (Gavi, WHO)"
    elif r == "US MOU" and b.iso.iat[i] in mou_mult:
        M[i] = mou_mult[b.iso.iat[i]]; known[i] = True; src_label[i] = "America First MOU"
    elif r in ("US MOU", "US non-MOU"):
        M[i] = SIGNER_AVG; src_label[i] = "US bilateral, no MOU (MOU average)"
    elif r in ("US other multilateral", "Residual"):
        M[i] = donor_path(d); src_label[i] = "Donor's total-aid cut"
    elif r == "Non-DAC":
        M[i] = ihme[i]; src_label[i] = "IHME 2025 trend"
    else:
        raise ValueError(f"unhandled rule {r}")

P = B[:, None] * M
print("rules -> labels:\n", pd.crosstab(b.Rule, src_label).to_string())
tot = P.sum(0) / 1e6
print("all recipients, $B:", round(B.sum() / 1e6, 2), [round(t, 2) for t in tot])
print("known share of loss by year:", [round(((B - P[:, j]) * known).sum() / max((B - P[:, j]).sum(), 1), 3)
                                       for j in range(NY)])

# --------------------------------------------------------------------------- dashboard input
loss = B[:, None] - P
ex = b[["iso", "src", "chan"]].assign(base=B, **{f"l{y}": loss[:, j] for j, y in enumerate(YRS)},
                                      **{f"k{y}": loss[:, j] * known for j, y in enumerate(YRS)})
ex = ex.groupby(["iso", "src", "chan"]).sum()
ex = ex[ex.base > 0]
out = pd.DataFrame({f"cut_{y}": (ex[f"l{y}"] / ex.base).clip(-1, 1).round(4) for y in YRS})
for y in YRS:
    out[f"known_cut_{y}"] = (ex[f"k{y}"] / ex.base).clip(-1, 1).round(4)
out.insert(0, "base_2023_kusd", ex.base.round(1))
out.index.names = ["iso3", "src_grp", "chan_grp"]
out.to_csv(REPO / "model_data" / "announcement_cuts.csv")

with open(OUTDIR / "fit_v3.txt", "w") as f:
    f.write("US bilateral without an MOU: predictors of the MOU whole-agreement multiplier (n = %d MOUs, weighted by "
            "prior US funding).\nLeave-one-out RMSE (lower is better):\n" % len(D))
    for k, v in TESTS.items():
        f.write(f"  {k:18s} {v:.4f}\n")
    f.write("lr = log(2023 health aid / government health spending); inc = World Bank income group (GDP per capita).\n")
    f.write(smf.wls("f ~ lr + C(inc)", D, weights=D.w).fit().summary2().tables[1].to_string() + "\n\n")
    f.write(f"Used: the average path {np.round(SIGNER_AVG, 3).tolist()} (2026-2030, share of 2023 kept).\n")
    f.write(f"MOU year shape (amount / agreement mean, {len(full)} complete schedules): {np.round(SHAPE5, 3).tolist()}\n")
print(open(OUTDIR / "fit_v3.txt").read())
