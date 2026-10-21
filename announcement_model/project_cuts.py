"""Health-aid cuts by country x donor x channel, 2026-2030, against the 2019-2023 average (Jiya's choices, 2026-10-21).

Flow f = (recipient r, original donor d, channel c). Base B_f = IHME DAH, average of 2019-2023 (constant 2023 k$, COVID-19
money included). For the dashboard's countries the yearly IHME files in country_data/ give all five years; for the other
workbook countries only 2019, 2022 and 2023 exist, so the base is their average. Each flow keeps B_f * m_f,y in year y.

KNOWN (a published number for that flow):
  - Global Fund, money from every source: 2026 = reduced GC7 / original GC7, 2027 = GC8 / original GC7.
  - Gavi: one Gavi-wide ratio, Gavi 6.0 new pledges / Gavi 5.0 pledges = 6.0 / 8.8 (Donor Tracker 2026: only about
    US$6B of the "US$9B+" is new money; Gavi 2020 summit: US$8.8B). The US is 0 (exit).
  - US through WHO = 0 (exit).
  - US bilateral + US-funded NGOs where there is an America First MOU: the MOU's yearly ratio (amount / prior US
    funding), from the team's year-by-year schedule or the whole-agreement ratio x the schedules' average shape.
  - Programme announcements: Swedish and UK country exits, the UK Africa bilateral path, the Netherlands' health
    budget (EUR 384M / 510M) and its halved UNICEF contribution.
PREDICTED:
  - Global Fund 2028-2030: the GC7 -> GC8 change keeps going at the same yearly rate, (GC8 / GC7)^(1/3) a year.
  - US bilateral + NGOs without an MOU: the average whole-agreement ratio of the 3 MOU countries with the closest
    aid / government health spending ratio (all three within +-50%), else the all-MOU average (prior-funding weighted);
    spread over the years with the MOU schedules' average shape.
  - Foundations, private and non-DAC governments (outside the Global Fund and Gavi): IHME 2025 / 2021-23 ratio.
  - Every other flow of a DAC donor: the donor's health budget target minus everything already fixed above for that
    donor (its Global Fund, Gavi, exits, announcements, MOUs), shared over its remaining flows as one equal cut:
        target_d,y = B_d * exp(alpha) * O_d,y ^ eps
        O_d,y = donor's total ODA in y / its 2019-2023 average
              = (OECD 2025 actual / 2019-23 average) x (outlook y / outlook 2025)   [oda_history.csv; Donor_ODA sheet]
        alpha, eps: fitted on IHME 2025 health aid vs OECD 2025 total aid across donors (health fell ~21% beyond what
        total aid explains and moves ~0.28x with it). Remaining flows keep min(1, max(0, (target - fixed) / rest)).
    2029-2030 extend each donor's 2025-28 outlook trend.
Writes model_data/announcement_cuts.csv (country x donor group x channel group: base, cut_<year>, known_cut_<year>)
and full audit tables in announcement_model/output/.

Usage (from the repo root):
    python announcement_model/project_cuts.py aid_cut_projections_announcements.xlsx
"""
import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

ap = argparse.ArgumentParser()
ap.add_argument("workbook", help="announcement workbook (aid_cut_projections_announcements.xlsx)")
ap.add_argument("--out", default=None, help="folder for the audit tables (default announcement_model/output)")
args = ap.parse_args()
WB, REPO = Path(args.workbook), Path(__file__).resolve().parent.parent
HERE = REPO / "announcement_model"
OUTDIR = Path(args.out) if args.out else HERE / "output"
OUTDIR.mkdir(parents=True, exist_ok=True)
YRS = [2026, 2027, 2028, 2029, 2030]
NY = len(YRS)
GAVI_WIDE = 6.0 / 8.8                 # Gavi 6.0 new pledges / Gavi 5.0 pledges (US$ B)
NN_K, NN_BAND = 3, np.log(1.5)        # similar-country rule for US aid without an MOU

wb = pd.read_excel(WB, sheet_name="Base_Projection")
oda = pd.read_excel(WB, sheet_name="Donor_ODA").dropna(subset=["IHME source"])
oda = oda[oda["ODA 2024"].notna()]
mou = pd.read_excel(WB, sheet_name="US_MOU")
gfa = pd.read_excel(WB, sheet_name="GF_Allocations").dropna(subset=["ISO3"]).drop_duplicates("ISO3").set_index("ISO3")
trend = pd.read_csv(REPO / "model_data/ihme_trend.csv")
ci = pd.read_csv(REPO / "model_data/country_inputs.csv", index_col=0)
hist = pd.read_csv(HERE / "oda_history.csv", index_col=0)
hist.columns = hist.columns.astype(int)

# --------------------------------------------------------------------------- base: 2019-2023 average per flow
KEY = ["Recipient ISO3", "IHME source (original donor)", "Channel"]
files = [f for f in glob.glob(str(REPO / "country_data/*.csv")) if open(f).readline().startswith("year,")]
cd = pd.concat([pd.read_csv(f, usecols=["year", "source", "channel", "recipient_isocode", "dah_23"],
                            dtype={"source": str, "channel": str}) for f in files])
cd = cd[cd.year.between(2019, 2023)]
full = cd.groupby(["recipient_isocode", "source", "channel"]).dah_23.sum() / 5   # k$, 5-year mean
full.index.names = KEY
have_full = set(cd.recipient_isocode)
wb["base"] = np.where(wb["Recipient ISO3"].isin(have_full),
                      wb.set_index(KEY).index.map(full).fillna(0.0).to_numpy(float),
                      wb[["DAH 2019", "DAH 2022", "DAH 2023"]].mean(axis=1).to_numpy(float))
# flows in the yearly files that the workbook lacks (no money in 2019, 2022 or 2023): add them with a rule
wb_keys = set(wb.set_index(KEY).index)
extra = full[[k not in wb_keys for k in full.index]].rename("base").reset_index()
extra = extra[extra.base > 0]
name_of = wb.drop_duplicates("Recipient ISO3").set_index("Recipient ISO3")["Recipient"]
chan_name = wb.drop_duplicates("Channel").set_index("Channel")["Channel name"]
grp_of = wb.drop_duplicates("IHME source (original donor)").set_index("IHME source (original donor)")["Donor group"]
NONDAC = {"China", "Corporate_donations", "Debt_repayments", "Gates Foundation", "Non_OECD_DAC_countries",
          "Non_OECD_non_DAC_countries", "Other", "Private_other", "Unallocable"}
mou_iso = set(mou.ISO3.dropna())
def rule_for(src, chan, iso):
    if chan == "GFATM": return "Global Fund"
    if src in NONDAC: return "Non-DAC"
    if src == "United_States":
        if chan in ("GAVI", "WHO"): return "Zero"
        if chan in ("BIL_USA", "USNGO", "INTLNGO", "US NGOs", "International NGOs"):
            return "US MOU" if iso in mou_iso else "US non-MOU"
        return "US other multilateral"
    if src == "Netherlands": return "NL UNICEF" if chan == "UNICEF" else "NL health"
    return "Residual"
if len(extra):
    extra = extra.assign(**{"Recipient": extra["Recipient ISO3"].map(name_of),
                            "Channel name": extra.Channel.map(chan_name).fillna(extra.Channel),
                            "Donor group": extra["IHME source (original donor)"].map(grp_of)
                            .fillna(extra["IHME source (original donor)"])})
    extra["Rule"] = [rule_for(s, c, i) for s, c, i in zip(extra["IHME source (original donor)"], extra.Channel,
                                                          extra["Recipient ISO3"])]
b = pd.concat([wb, extra], ignore_index=True)
b = b[b.base > 0].reset_index(drop=True)

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
B = b.base.to_numpy(float)
rule, donor, cname = b.Rule.to_numpy(), b["Donor group"].to_numpy(), b["Channel name"].to_numpy()
N = len(b)

# --------------------------------------------------------------------------- health vs total aid (IHME 2025 vs OECD 2025)
NG = {"Denmark", "Finland", "Norway", "Sweden", "Iceland"}
def fit_grp(s):
    if s in ("United_States", "United_Kingdom"): return s.replace("_", " ")
    if s in BIG: return s
    if s in NG: return "Nordics"
    return "Other DAC governments"
od = oda[~oda["IHME source"].isin(NONDAC | {"Other_OECD_DAC_countries"})].assign(g=lambda d: d["IHME source"].map(fit_grp))
og = od.groupby("g")[["ODA 2024", "Filled 2025"]].sum()
og["o25"] = og["Filled 2025"] / og["ODA 2024"]
tr = trend.groupby("src_grp")[["base_usd", "y2025_usd"]].sum()
tr["h25"] = tr.y2025_usd / tr.base_usd
E = og.join(tr, how="inner").drop(index="Japan")    # Japan's 2025 is a lumpy Gavi payment
env = sm.WLS(np.log(E.h25), sm.add_constant(np.log(E.o25)), weights=E.base_usd).fit()
ALPHA, EPS = float(env.params.iloc[0]), float(env.params.iloc[1])

# --------------------------------------------------------------------------- donors' total-aid path vs 2019-2023
Om = oda.set_index("IHME source")[["Filled 2025", "Filled 2026", "Filled 2027", "Filled 2028"]].astype(float)
Om.columns = [2025, 2026, 2027, 2028]
slope = (np.log(Om[2028]) - np.log(Om[2025])) / 3
for y in (2029, 2030):
    Om[y] = Om[2028] * np.exp(slope * (y - 2028))
avg1923 = hist[[2019, 2020, 2021, 2022, 2023]].mean(axis=1)
def oda_path(d):
    """Total ODA in 2026-2030 / its 2019-2023 average."""
    h = d if d in hist.index else "DAC_total"
    lvl25 = hist.at[h, 2025] / avg1923[h]
    row = Om.loc[d] if d in Om.index else Om.loc["Other_OECD_DAC_countries"]
    return lvl25 * np.array([row[y] / row[2025] for y in YRS])
def health_path(d):
    return np.exp(ALPHA) * oda_path(d) ** EPS

# --------------------------------------------------------------------------- US MOUs
sched = ci[[f"mou_us_{y}" for y in YRS]] / 1e6
M_ = mou.dropna(subset=["ISO3"]).set_index("ISO3")
yby = {}
for k, r in M_.iterrows():
    prior = r["Prior US funding per year ($M)"]
    if str(r["Year-by-year source"]).startswith("User") and k in sched.index and pd.notna(prior):
        yby[k] = pd.Series(sched.loc[k].to_numpy(float)).ffill().to_numpy() / prior
fullsch = [v for k, v in yby.items() if np.isfinite(sched.loc[k]).all()]
SHAPE5 = np.mean([v / v.mean() for v in fullsch], 0)
SHAPE3 = SHAPE5[:3] / SHAPE5[:3].mean()
def spread(f, n=5):
    shp = SHAPE3 if n <= 3 else SHAPE5
    return f * np.concatenate([shp, np.repeat(shp[-1], 5 - len(shp))])
mou_mult = dict(yby)
for k, r in M_.iterrows():
    if k not in mou_mult and pd.notna(r["Flat multiplier (whole agreement)"]):
        mou_mult[k] = spread(r["Flat multiplier (whole agreement)"],
                             int(r["Years in agreement"]) if pd.notna(r["Years in agreement"]) else 5)

# --------------------------------------------------------------------------- US without an MOU: similar countries
def latest(path, col):
    d = pd.read_csv(path)
    d = d[(d.time >= 2015) & (d.time <= 2024)].dropna(subset=[col]).sort_values("time")
    return d.groupby("geo")[col].last().rename(index=str.upper)
W = REPO / "ext_data"
T = pd.DataFrame({"gdp_pc": latest(W / "reference/wdi/ny_gdp_pcap_cd.csv", "ny_gdp_pcap_cd"),
                  "ghed_gdp": latest(W / "reference/wdi/sh_xpd_ghed_gd_zs.csv", "sh_xpd_ghed_gd_zs"),
                  "pop": latest(W / "wdi/sp_pop_totl.csv", "sp_pop_totl")})
ghes = (ci.ghes_2023 / 1e6).combine_first(T.ghed_gdp / 100 * T.gdp_pc * T["pop"] / 1e6)
X = pd.DataFrame({"dah": b.groupby("iso").base.sum() / 1e3, "ghes": ghes})
X["lr"] = np.log(X.dah / X.ghes).replace([np.inf, -np.inf], np.nan)
D = pd.DataFrame({"f": M_["Flat multiplier (whole agreement)"], "w": M_["Prior US funding, same length ($M)"]})
D = D.groupby(level=0).first().join(X).dropna(subset=["f", "w", "lr"])
F_AVG = float(np.average(D.f, weights=D.w))
nomou = {}
for iso in sorted(set(b.iso[rule == "US non-MOU"])):
    if iso in X.index and np.isfinite(X.at[iso, "lr"]):
        dd = (D.lr - X.at[iso, "lr"]).abs().sort_values()[:NN_K]
        if (dd < NN_BAND).all():
            nomou[iso] = {"f": float(D.loc[dd.index, "f"].mean()), "match": list(dd.index),
                          "ratio": float(np.exp(X.at[iso, "lr"]))}
            continue
    nomou[iso] = {"f": F_AVG, "match": [], "ratio": float(np.exp(X.at[iso, "lr"])) if iso in X.index else None}

# --------------------------------------------------------------------------- fixed multipliers (known, or predicted)
M = np.full((N, NY), np.nan)
KN = np.zeros((N, NY), bool)
lab = np.empty(N, object)
gf26 = b.iso.map(gfa["Ratio 2026 (reduced GC7)"]).to_numpy(float)
gf27 = b.iso.map(gfa["Ratio 2027-28 (GC8)"]).to_numpy(float)
ihme = b.src.map(tr.h25).fillna(1.0).to_numpy(float, copy=True)
ihme[b.src.eq("Other / unallocable").to_numpy()] = 1.0
UK_AFRICA = [0.72, 0.58, 0.44, 0.44, 0.44]
EXIT = [0.5, 0, 0, 0, 0]
for i in range(N):
    r, d, c, iso = rule[i], donor[i], cname[i], b.iso.iat[i]
    if c == "Global Fund":
        a, g = gf26[i], gf27[i]
        if not (np.isfinite(a) and np.isfinite(g)):
            a = g = 12.64 / 15.7                                    # all-donor pledge ratio where no allocation
        step = g ** (1 / 3) if g > 0 else 0.0
        M[i] = [a, g, g * step, g * step ** 2, g * step ** 3]
        KN[i, :2] = True
        lab[i] = "Global Fund"
    elif c == "Gavi":
        M[i] = 0.0 if d == "United_States" else GAVI_WIDE
        KN[i] = True
        lab[i] = "US exit (Gavi, WHO)" if d == "United_States" else "Gavi replenishment"
    elif r == "Zero":                                            # US through WHO
        M[i] = 0.0; KN[i] = True; lab[i] = "US exit (Gavi, WHO)"
    elif r == "US MOU" and iso in mou_mult:
        M[i] = mou_mult[iso]; KN[i] = True; lab[i] = "America First MOU"
    elif r in ("US MOU", "US non-MOU"):
        M[i] = spread(nomou.get(iso, {"f": F_AVG})["f"]); lab[i] = "US, no MOU (similar countries)"
    elif r == "Exit":
        M[i] = EXIT; KN[i] = True; lab[i] = "Country exit"
    elif r == "UK Africa bilateral":
        M[i] = UK_AFRICA; KN[i] = True; lab[i] = "UK Africa path"
    elif r == "NL health":
        M[i] = 384 / 510; KN[i] = True; lab[i] = "Netherlands health budget"
    elif r == "NL UNICEF":
        M[i] = 0.5; KN[i] = True; lab[i] = "Netherlands health budget"
    elif r == "Non-DAC":
        M[i] = ihme[i]; lab[i] = "Foundations & non-DAC (IHME 2025 trend)"
    elif r in ("US other multilateral", "Residual"):
        lab[i] = "Donor's remaining aid (balanced to its target)"   # filled below
    else:
        raise ValueError(f"unhandled rule {r}")

# --------------------------------------------------------------------------- donor targets: the rest shares what is left
rest = np.isnan(M[:, 0])
dtab = []
for d in sorted(set(donor[rest])):
    sel = donor == d
    Bd, Rb = B[sel].sum(), B[sel & rest].sum()
    hp = health_path(d)
    for j, y in enumerate(YRS):
        target = Bd * hp[j]
        fixed = (B[sel & ~rest] * M[sel & ~rest, j]).sum()
        lam = float(np.clip((target - fixed) / Rb, 0.0, 1.0)) if Rb > 0 else np.nan
        M[sel & rest, j] = lam
        dtab.append({"donor": d, "year": y, "base_musd": Bd / 1e3, "oda_vs_2019_23": oda_path(d)[j],
                     "health_target_ratio": hp[j], "target_musd": target / 1e3, "fixed_musd": fixed / 1e3,
                     "rest_base_musd": Rb / 1e3, "rest_kept": lam,
                     "donor_total_kept": ((B[sel] * M[sel, j]).sum() / Bd)})
dtab = pd.DataFrame(dtab)
assert not np.isnan(M).any()

P = B[:, None] * M
loss = B[:, None] - P
print(f"alpha {ALPHA:.3f}  eps {EPS:.3f}  Gavi-wide {GAVI_WIDE:.3f}  MOU average {F_AVG:.3f}")
print("all recipients, $B: base", round(B.sum() / 1e6, 2), "kept", [round(v, 2) for v in P.sum(0) / 1e6])
print("known share of loss:", [round((loss[:, j] * KN[:, j]).sum() / loss[:, j].sum(), 3) for j in range(NY)])

# --------------------------------------------------------------------------- outputs
ex = b[["iso", "src", "chan"]].assign(base=B, **{f"l{y}": loss[:, j] for j, y in enumerate(YRS)},
                                      **{f"k{y}": loss[:, j] * KN[:, j] for j, y in enumerate(YRS)})
ex = ex.groupby(["iso", "src", "chan"]).sum()
ex = ex[ex.base > 0]
out = pd.DataFrame({f"cut_{y}": (ex[f"l{y}"] / ex.base).clip(-1, 1).round(4) for y in YRS})
for y in YRS:
    out[f"known_cut_{y}"] = (ex[f"k{y}"] / ex.base).clip(-1, 1).round(4)
out.insert(0, "base_kusd", ex.base.round(1))
out.index.names = ["iso3", "src_grp", "chan_grp"]
out.to_csv(REPO / "model_data" / "announcement_cuts.csv")

rows = b[["iso", "Recipient", "Donor group", "Channel name", "Rule"]].assign(label=lab, base_kusd=B.round(1))
for j, y in enumerate(YRS):
    rows[f"kept_{y}"] = M[:, j].round(4)
    rows[f"known_{y}"] = KN[:, j]
rows.to_csv(OUTDIR / "rows_v4.csv", index=False)
dtab.round(4).to_csv(OUTDIR / "donor_targets_v4.csv", index=False)
pd.DataFrame([{"iso3": k, "aid_to_ghes": v["ratio"], "matches": " ".join(v["match"]) or "none: MOU average",
               "agreement_ratio": v["f"]} for k, v in nomou.items()]).to_csv(OUTDIR / "us_no_mou_v4.csv", index=False)
with open(OUTDIR / "fit_v4.txt", "w") as f:
    f.write("Health vs total aid: log(IHME 2025 health ratio) = alpha + eps * log(OECD 2025 ODA ratio), WLS, Japan out\n")
    f.write(env.summary2().tables[1].to_string() + "\n\n")
    f.write(f"Gavi-wide ratio {GAVI_WIDE:.4f}; MOU average (prior-funding weighted) {F_AVG:.4f}; "
            f"MOU year shape {np.round(SHAPE5, 3).tolist()}\n")
