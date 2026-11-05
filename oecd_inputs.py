"""Health aid by recipient x donor x channel x health area from the OECD Creditor Reporting System (CRS), in the same
column layout as the IHME DAH country files, so the dashboard and the Announced model can read it unchanged.
Replaces IHME DAH as the source of aid amounts (Jiya, 2026-11-05).

Input: the OECD CRS download (Data Explorer, DSD_CRS@DF_CRS, filtered to health sectors 121/122/123/130, gross
disbursements, constant 2024 US$ millions, 2008-2024). Kept in datasets/ (not committed).

What comes from where
  * Amounts: CRS. US$ millions in 2024 prices -> thousands of 2023 US$: x 1000 / 1.02 (the OECD workbook's factor).
    ODA grants, ODA loans (mostly World Bank IDA) and Gates private development finance are all kept.
  * Donor (IHME-style source name) and channel:
      DAC government  public sector, private sector, universities, PPPs, other -> BIL_<donor>;
                      NGOs & civil society -> NGO (US) / INTLNGO (others); multilateral (earmarked) -> MULTI_EARMARKED
      Gates Foundation -> source "Gates Foundation", channel GATES
      Global Fund, Gavi -> channel GFATM / GAVI, traced back to the donors who pay into them with each donor's share
                      of that fund in IHME's attribution for the same year (IHME is used for this ratio only)
      IDA, EU institutions, WHO, UNICEF, UNFPA, UNAIDS spending their own funds -> their own source and channel
  * Health area: CRS purpose code (13040 HIV, 12262 malaria, 12263 TB, 12264 COVID-19, 13020/13030/13010/13081
    reproductive & maternal, 12240 nutrition, 12250 other infectious, 123xx NCDs, 12110/12181/12230/12281 health
    systems, 12191/12182/12220/12261 other). All Gavi money other than COVID-19 is vaccines (nch_cnv).
  * Global Fund HIV / TB: the Global Fund reports joint HIV/TB grants under the HIV code (Zambia shows almost no TB).
    A country's Global Fund HIV + TB money is re-split with IHME's 2019-2023 HIV:TB split of Global Fund money there.
  * Service detail inside HIV, TB and malaria (ART, PMTCT, prevention, nets, ...): CRS has one code per disease, so
    each disease's amount is split with IHME's 2019-2023 program-area shares for that country and channel group
    (fallbacks: country, then all countries for that channel group, then all countries).

Outputs
  oecd_data/<ISO3>.csv, oecd_data/_index.csv   IHME DAH column layout (dah_23, hiv_dah_23, hiv_treat_dah_23, ...)
  model_data/dah_lines.csv                      service-model baseline (2021-2023 average, US$), as prepare_model did
  model_data/country_inputs.csv                 dah_all_purposes_base, dah_nch_base, us_health_aid_base patched

Usage (repo root):  python oecd_inputs.py "datasets/OECD.DCD.FSD,DSD_CRS@DF_CRS,,filtered,2026-11-04 01-44-10.csv"
"""
import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
IHME_DIR = HERE / "country_data"          # IHME DAH files: used only for fund shares and service splits
OUT_DIR = HERE / "oecd_data"
MODEL = HERE / "model_data"
TO_2023 = 1000 / 1.02                     # US$ M, 2024 prices -> k$, 2023 prices
SPLIT_YEARS = (2019, 2023)                # IHME years for the shares
MIN_CELL = 1000.0                         # k$/yr: smaller IHME cells fall back to a wider share

# CRS donor name -> (IHME-style source, ISO3 used in the BIL_ channel code)
DAC = {"Australia": ("Australia", "AUS"), "Austria": ("Austria", "AUT"), "Belgium": ("Belgium", "BEL"),
       "Canada": ("Canada", "CAN"), "Czechia": ("Czechia", "CZE"), "Denmark": ("Denmark", "DNK"),
       "Estonia": ("Estonia", "EST"), "Finland": ("Finland", "FIN"), "France": ("France", "FRA"),
       "Germany": ("Germany", "DEU"), "Greece": ("Greece", "GRC"), "Hungary": ("Other_OECD_DAC_countries", "HUN"),
       "Iceland": ("Iceland", "ISL"), "Ireland": ("Ireland", "IRL"), "Italy": ("Italy", "ITA"),
       "Japan": ("Japan", "JPN"), "Korea": ("Korea", "KOR"), "Latvia": ("Latvia", "LVA"),
       "Lithuania": ("Lithuania", "LTU"), "Luxembourg": ("Luxembourg", "LUX"), "Netherlands": ("Netherlands", "NLD"),
       "New Zealand": ("New_Zealand", "NZL"), "Norway": ("Norway", "NOR"), "Poland": ("Poland", "POL"),
       "Portugal": ("Portugal", "PRT"), "Romania": ("Romania", "ROU"), "Slovak Republic": ("Slovakia", "SVK"),
       "Slovenia": ("Slovenia", "SVN"), "Spain": ("Spain", "ESP"), "Sweden": ("Sweden", "SWE"),
       "Switzerland": ("Switzerland", "CHE"), "United Kingdom": ("United_Kingdom", "GBR"),
       "United States": ("United_States", "USA")}
OWN = {"International Development Association [IDA]": ("World_Bank_IDA", "WB_IDA"),
       "EU Institutions": ("EU_Institutions", "EC"), "World Health Organisation [WHO]": ("WHO", "WHO"),
       "UNICEF": ("UNICEF", "UNICEF"), "UNFPA": ("UNFPA", "UNFPA"), "UNAIDS": ("UNAIDS", "UNAIDS")}
FUNDS = {"Global Fund": "GFATM", "Global Alliance for Vaccines and Immunization [GAVI]": "GAVI"}

# CRS purpose code -> IHME column (without _dah_23). HIV / TB / malaria get a placeholder split later.
SECTOR_COL = {13040: "hiv", 12262: "mal", 12263: "tb", 12264: "oid_covid", 12250: "oid_other",
              13020: "rmh_mh", 13030: "rmh_fp", 13010: "rmh_other", 13081: "rmh_hss_hrh", 12240: "nch_cnn",
              12110: "swap_hss_pp", 12181: "swap_hss_hrh", 12281: "swap_hss_hrh", 12230: "swap_hss_other",
              12191: "other", 12182: "other", 12220: "other", 12261: "other",
              12310: "ncd_other", 12320: "ncd_tobac", 12330: "ncd_other", 12340: "ncd_mental", 12350: "ncd_other",
              12382: "ncd_other"}
AREAS = ["rmh", "nch", "ncd", "hiv", "mal", "tb", "oid"]
DISEASES = ["hiv", "tb", "mal"]


def ihme_files() -> pd.DataFrame:
    files = [f for f in glob.glob(str(IHME_DIR / "*.csv")) if open(f).readline().startswith("year,")]
    return pd.concat([pd.read_csv(f, dtype={"source": str, "channel": str}) for f in files], ignore_index=True)


def chan_grp(c: str) -> str:
    import prepare_model
    return prepare_model.channel_group(c)


def read_crs(path: Path) -> pd.DataFrame:
    use = ["Donor", "RECIPIENT", "Recipient", "SECTOR", "Measure", "CHANNEL", "TIME_PERIOD", "OBS_VALUE"]
    d = pd.read_csv(path, usecols=use, low_memory=False)
    d = d[d.RECIPIENT.str.fullmatch("[A-Z]{3}")]            # drop regional rows ("O" = Oceania)
    d["k"] = d.OBS_VALUE.astype(float) * TO_2023
    return d.rename(columns={"RECIPIENT": "iso", "Recipient": "name", "TIME_PERIOD": "year"})


def main(crs_path: Path):
    crs = read_crs(crs_path)
    ihme = ihme_files()
    num = [c for c in ihme.columns if c.endswith("_dah_23")]
    ihme[num] = ihme[num].fillna(0.0)
    ih = ihme[ihme.year.between(*SPLIT_YEARS)]

    # ------------------------------------------------------------------ donor, channel
    def donor_channel(r):
        if r.Donor in DAC:
            src, iso = DAC[r.Donor]
            ch = r.CHANNEL
            if ch == 20000:
                return src, "NGO" if src == "United_States" else "INTLNGO"
            if ch == 40000:
                return src, "MULTI_EARMARKED"
            return src, f"BIL_{iso}"
        if r.Donor == "Gates Foundation":
            return "Gates Foundation", "GATES"
        if r.Donor in OWN:
            return OWN[r.Donor]
        if r.Donor in FUNDS:
            return "__fund__", FUNDS[r.Donor]
        raise ValueError(f"unmapped CRS donor {r.Donor}")
    dc = crs[["Donor", "CHANNEL"]].drop_duplicates()
    dc[["source", "channel"]] = [donor_channel(r) for r in dc.itertuples()]
    crs = crs.merge(dc, on=["Donor", "CHANNEL"])

    # ------------------------------------------------------------------ health area column
    crs["col"] = crs.SECTOR.map(SECTOR_COL)
    if crs.col.isna().any():
        raise ValueError(f"unmapped CRS sectors {sorted(crs.loc[crs.col.isna(), 'SECTOR'].unique())}")
    gavi = (crs.channel == "GAVI") & (crs.col != "oid_covid")
    crs.loc[gavi, "col"] = "nch_cnv"

    # ------------------------------------------------------------------ Global Fund HIV/TB re-split (IHME ratio)
    gf_ih = ih[ih.channel == "GFATM"].groupby("recipient_isocode")[["hiv_dah_23", "tb_dah_23"]].sum()
    gf_tb_share = (gf_ih.tb_dah_23 / gf_ih.sum(axis=1)).dropna()
    gf = (crs.channel == "GFATM") & crs.col.isin(["hiv", "tb"]) & crs.iso.isin(gf_tb_share.index)
    g = crs[gf].groupby(["iso", "name", "year", "Donor", "Measure", "CHANNEL", "source", "channel"], as_index=False).k.sum()
    sh = g.iso.map(gf_tb_share)
    crs = pd.concat([crs[~gf], g.assign(col="hiv", k=g.k * (1 - sh)), g.assign(col="tb", k=g.k * sh)],
                    ignore_index=True)

    # ------------------------------------------------------------------ trace Global Fund / Gavi back to donors
    # IHME's donor shares of each fund's money in that recipient and year (they differ by recipient); a recipient-year
    # IHME lacks (2024, or a country without an IHME file) takes the recipient's latest earlier year, else the
    # all-recipient shares of that year
    # COVID-19 money (C19RM, COVAX) has its own donor mix, so it takes shares from IHME's COVID money, the rest from
    # IHME's non-COVID money
    parts = [crs[crs.source != "__fund__"]]
    ihme = ihme.assign(noncovid=ihme.dah_23 - ihme.oid_covid_dah_23)
    for fund in ("GFATM", "GAVI"):
        for covid, wcol in ((False, "noncovid"), (True, "oid_covid_dah_23")):
            x = ihme[ihme.channel == fund]
            rw = x.groupby(["recipient_isocode", "year", "source"])[wcol].sum()
            rw = (rw / rw.groupby(level=[0, 1]).transform("sum")).dropna()
            gw = x.groupby(["year", "source"])[wcol].sum()
            gw = (gw / gw.groupby(level=0).transform("sum")).dropna()
            r_years = rw.reset_index().groupby("recipient_isocode").year.apply(lambda s: sorted(set(s))).to_dict()
            g_years = sorted(gw.index.get_level_values(0).unique())
            f = crs[(crs.source == "__fund__") & (crs.channel == fund) & ((crs.col == "oid_covid") == covid)]
            f = f.drop(columns="source")
            out = []
            for (iso, yr), grp in f.groupby(["iso", "year"]):
                ys = [y for y in r_years.get(iso, []) if y <= yr]
                if ys:
                    w = rw.loc[(iso, ys[-1])]
                else:
                    w = gw.loc[max([y for y in g_years if y <= yr], default=g_years[0])]
                out.append(grp.merge(w.rename("w").reset_index(), how="cross"))
            if out:
                f = pd.concat(out, ignore_index=True)
                parts.append(f.assign(k=f.k * f.w).drop(columns="w"))
    crs = pd.concat(parts, ignore_index=True)

    # ------------------------------------------------------------------ wide table in the IHME layout
    keys = ["year", "source", "channel", "iso"]
    wide = crs.pivot_table(index=keys, columns="col", values="k", aggfunc="sum", fill_value=0.0)
    wide.columns = [f"{c}_dah_23" for c in wide.columns]
    wide = wide.reset_index()
    wide["cg"] = wide.channel.map(chan_grp)

    # service split inside each disease: IHME 2019-23 program shares (country x channel group, with fallbacks)
    ih = ih.assign(cg=ih.channel.map(chan_grp))
    for dz in DISEASES:
        prog = [c for c in ihme.columns if c.startswith(f"{dz}_") and c.endswith("_dah_23") and c != f"{dz}_dah_23"]
        levels = [(["recipient_isocode", "cg"], ["iso", "cg"]), (["recipient_isocode"], ["iso"]), (["cg"], ["cg"]),
                  ([], [])]
        S = pd.DataFrame(np.nan, index=wide.index, columns=prog)
        for ik, wk in levels:
            if ik:
                t = ih.groupby(ik)[prog].sum() / (SPLIT_YEARS[1] - SPLIT_YEARS[0] + 1)
            else:
                t = ih[prog].sum().to_frame().T / (SPLIT_YEARS[1] - SPLIT_YEARS[0] + 1)
            tot = t.sum(axis=1)
            t = t[tot >= MIN_CELL].div(tot[tot >= MIN_CELL], axis=0)
            if wk:
                t.index.names = wk
                look = wide[wk].merge(t, left_on=wk, right_index=True, how="left")[prog]
                look.index = wide.index
            else:
                look = pd.DataFrame(np.repeat(t.to_numpy(), len(wide), 0), index=wide.index, columns=prog)
            S = S.fillna(look)
        col = f"{dz}_dah_23"
        amt = wide[col] if col in wide else 0.0
        for c in prog:
            wide[c] = S[c] * amt
    # every IHME column, totals rebuilt from the parts
    for c in num:
        if c not in wide:
            wide[c] = 0.0
    wide[num] = wide[num].fillna(0.0)
    for a in AREAS:
        wide[f"{a}_dah_23"] = wide[[c for c in num if c.startswith(f"{a}_") and c != f"{a}_dah_23"]].sum(axis=1)
    wide["swap_hss_total_dah_23"] = wide[[c for c in num if c.startswith("swap_hss_") and
                                          c != "swap_hss_total_dah_23"]].sum(axis=1)
    totals = [f"{a}_dah_23" for a in AREAS] + ["swap_hss_total_dah_23", "other_dah_23", "unalloc_dah_23"]
    wide["dah_23"] = wide[totals].sum(axis=1)
    raw = crs.groupby("iso").k.sum()
    assert np.allclose(wide.groupby("iso").dah_23.sum().reindex(raw.index), raw, rtol=1e-6), "amounts not preserved"

    names = crs.drop_duplicates("iso").set_index("iso").name
    wide = wide.rename(columns={"iso": "recipient_isocode"})
    wide["recipient_country"] = wide.recipient_isocode.map(names)
    wide["prelim_est"] = 0
    cols = ["year", "source", "channel", "recipient_isocode", "recipient_country", "prelim_est", "dah_23"] + num
    wide = wide[cols].sort_values(["year", "source", "channel"])
    wide[cols[6:]] = wide[cols[6:]].round(3)

    OUT_DIR.mkdir(exist_ok=True)
    for f in OUT_DIR.glob("*.csv"):
        f.unlink()
    idx = []
    for iso, d in wide.groupby("recipient_isocode"):
        d = d[(d[cols[6:]].abs() > 0).any(axis=1)]
        d.to_csv(OUT_DIR / f"{iso}.csv", index=False)
        idx.append({"recipient_country": names[iso], "recipient_isocode": iso, "file": f"{iso}.csv"})
    pd.DataFrame(idx).to_csv(OUT_DIR / "_index.csv", index=False)
    print(f"oecd_data: {len(idx)} recipients, {wide.year.min()}-{wide.year.max()}, "
          f"2019-23 avg ${wide[wide.year.between(2019, 2023)].dah_23.sum() / 5e6:.1f}B/yr")
    write_model_inputs(wide)


def write_model_inputs(dah: pd.DataFrame):
    """model_data/dah_lines.csv and the three aid columns of country_inputs.csv, as prepare_model built them from
    IHME (same service lines, years and groups)."""
    import prepare_model as pm
    lo, hi = pm.BASE_YEARS
    ny = hi - lo + 1
    base = dah[dah.year.between(lo, hi) & dah.recipient_isocode.isin(pm.ISO3)].copy()
    base["src_grp"] = base.source.map(pm.source_group)
    base["chan_grp"] = base.channel.map(pm.channel_group)
    rows = []
    for line, (bucket, cols) in pm.LINES.items():
        g = base.groupby(["recipient_isocode", "src_grp", "chan_grp"])[[f"{c}_dah_23" for c in cols]].sum().sum(axis=1)
        g = (g / ny * 1e3)
        g = g[g.abs() > 0].rename("usd").reset_index()
        g["line"], g["bucket"] = line, bucket
        rows.append(g)
    lines = pd.concat(rows).rename(columns={"recipient_isocode": "iso3"})
    lines = lines[lines.iso3.isin(pm.DASHBOARD_ISO3)]
    lines["usd"] = lines.usd.round(2)
    lines.to_csv(MODEL / "dah_lines.csv", index=False)
    print(f"dah_lines: {len(lines):,} rows, {lines.iso3.nunique()} countries, ${lines.usd.sum() / 1e9:.2f}B/yr")

    p = MODEL / "country_inputs.csv"
    ci = pd.read_csv(p, index_col=0)
    by = base.groupby("recipient_isocode")
    ci["dah_all_purposes_base"] = (by.dah_23.sum() / ny * 1e3).reindex(ci.index)
    ci["dah_nch_base"] = (by.nch_dah_23.sum() / ny * 1e3).reindex(ci.index).fillna(0.0)
    us = base[base.source == "United_States"].groupby("recipient_isocode").dah_23.sum() / ny * 1e3
    ci["us_health_aid_base"] = us.reindex(ci.index).fillna(0.0)
    ci.to_csv(p)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("crs", type=Path, help="OECD CRS health download (csv)")
    main(ap.parse_args().crs)
