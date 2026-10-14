"""
Batch 4b, item 1 (L-50): the ART cost each country uses now, and the observed HIV treatment spending per person on ART.
Read-only with respect to the model.

    .venv/bin/python audit/batch4b_art_check.py

Observed treatment spending per person on ART = total HIV spending x treatment-and-care share / people receiving ART:
  total HIV spending: ten Brink et al. 2025 appendix Table B2 (p. 8) for its countries that are modelled (15; most
      recent GAM year, nominal US$); otherwise WHO GHED `dis11_usd` (HIV/AIDS and other STDs, million current US$,
      latest year with a value; datasets/WHO_GHED);
  treatment-and-care share: the country's Global Fund GC7 module share ("Treatment, care and support";
      `unspec_hiv_treatment` in country_inputs.csv, Batch 3+4 item 2; a WHO-region median where the country has no grant);
  people receiving ART: UNAIDS AIDSinfo 2026 estimates, "People receiving antiretroviral therapy", All ages, unrounded
      `Data value`, same year as the spending (datasets/UNAIDS_2026).
Nominal US$ of the spending year are put in 2023 US$ with the US CPI-U annual averages (BLS: 2015 237.017, 2016 240.007,
2017 245.120, then health_model.CPI_U). The model's full cost = site cost x 1 / (1 - asd_share) x uc_art_mult.
Writes audit/logic_review/batch4b_art_check.csv.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402

CPI = {2015: 237.017, 2016: 240.007, 2017: 245.120, **hm.CPI_U}
B2 = {"AZE": (2023, 14_770_145), "KHM": (2022, 31_565_694), "CIV": (2022, 180_080_436), "DOM": (2022, 72_921_868),
      "SWZ": (2019, 102_113_481), "KEN": (2022, 764_057_567), "KGZ": (2023, 12_523_725), "MWI": (2022, 259_699_300),
      "MDA": (2023, 10_625_628), "MNG": (2021, 2_474_731), "MOZ": (2019, 557_780_695), "ZAF": (2023, 1_863_907_174),
      "TJK": (2023, 3_503_630), "UGA": (2020, 538_920_127), "ZWE": (2023, 310_440_134)}
OUT = ROOT / "audit" / "logic_review" / "batch4b_art_check.csv"


def inflate(v, y):
    return v * CPI[2023] / CPI[int(y)]


def main():
    I, P = hm.load_inputs(), hm.load_params()
    ci = I["ci"]
    iso_all = sorted(set(I["lines"].iso3))
    Pc = hm.draw_params(P, 0)
    markup = 1.0 / (1.0 - float(Pc["asd_share"][0]))
    # (a) the cost now used
    a = pd.read_csv(ROOT / "audit" / "logic_review" / "batch34_art_costs.csv").set_index("iso3")
    g = pd.read_excel(ROOT / "datasets" / "GHCC_UCSR" / "GHCC_UCSR_HIV_ART.xlsx")
    g["price_year"] = pd.to_numeric(g["Reported Currency Year"], errors="coerce").fillna(g["Reference Year"])
    ok = (g["Output unit"].isin(["Per Person Treated Per Year", "Per Patient Year", "Per Person Served Per Year",
                                 "Per Person Seen In Year On ART"]) & (g["Perspective"] == "Provider")
          & pd.to_numeric(g["Mean Unit Cost"], errors="coerce").notna()
          & ~g["Above Service Costs Included"].astype(str).str.startswith("Some") & (g.price_year >= 2015))
    g = g[ok]
    cmap = {"Côte d'Ivoire": "CIV", "Eswatini": "SWZ", "Ghana": "GHA", "India": "IND", "Indonesia": "IDN", "Kenya": "KEN",
            "Malawi": "MWI", "Nigeria": "NGA", "South Africa": "ZAF", "Tanzania, United Republic of": "TZA",
            "Uganda": "UGA", "Zambia": "ZMB"}
    g["iso3"] = g.Country.map(cmap)
    rec = g.groupby("iso3").agg(ghcc_records=("uc" if "uc" in g else "Mean Unit Cost", "size"),
                                price_years=("price_year", lambda s: "/".join(sorted({str(int(x)) for x in s}))),
                                kinds=("Economic / Financial", lambda s: "/".join(sorted(set(s)))),
                                settings=("Ownership", lambda s: "/".join(sorted({str(x) for x in s}))))
    # (b) observed treatment spending per person on ART
    u = pd.read_csv(ROOT / "datasets" / "UNAIDS_2026" / "UNAIDS_Estimates_2026.csv", low_memory=False,
                    usecols=["Indicator", "Subgroup", "Area ID", "Area Level", "Time Period", "Data value"])
    u = u[(u["Area Level"] == 2) & (u.Indicator == "People receiving antiretroviral therapy") & (u.Subgroup == "All ages")]
    u["Data value"] = pd.to_numeric(u["Data value"], errors="coerce")
    art = u.dropna(subset=["Data value"]).set_index(["Area ID", "Time Period"])["Data value"]
    gh = pd.read_excel(ROOT / "datasets" / "WHO_GHED" / "GHED_data_2026-10-14.xlsx", sheet_name="Data",
                       usecols=["code", "year", "dis11_usd"]).dropna(subset=["dis11_usd"])
    gh = gh[(gh.dis11_usd > 0)].sort_values("year").groupby("code").tail(1).set_index("code")
    rows = []
    for iso in iso_all:
        row = ci.loc[iso]
        site = float(row["art_site_cost"])
        full = site * markup
        r = {"iso3": iso, "site_cost_2023": site, "full_cost_now": full, "source": row["art_site_cost_source"],
             "own_study": str(row["art_site_cost_source"]).startswith("own"),
             "gate_site_50_600": 50 <= site <= 600, "gate_full_50_600": 50 <= full <= 600,
             "ghcc_records": int(rec.ghcc_records.get(iso, 0)), "price_years": rec.price_years.get(iso, ""),
             "cost_kind": ("economic x 0.981 (GHCC) and financial (Rosen 2021)" if iso in rec.index else
                           "financial (Rosen 2021)" if iso in ("LSO", "ZMB", "ZWE", "MWI", "UGA") and str(row["art_site_cost_source"]).startswith("own") else "fallback"),
             "setting": rec.settings.get(iso, "")}
        if iso in B2:
            yr, tot = B2[iso]
            r.update({"spend_source": f"Optima Table B2 ({yr})", "spend_year": yr, "total_hiv_spend_usd": tot})
        elif iso in gh.index:
            yr = int(gh.loc[iso, "year"])
            r.update({"spend_source": f"WHO GHED dis11_usd ({yr})", "spend_year": yr, "total_hiv_spend_usd": float(gh.loc[iso, "dis11_usd"]) * 1e6})
        else:
            r.update({"spend_source": "", "spend_year": np.nan, "total_hiv_spend_usd": np.nan})
        r["treatment_share"] = float(row["unspec_hiv_treatment"])
        r["treatment_share_source"] = row["unspec_hiv_source"]
        if r["spend_source"]:
            yr = int(r["spend_year"])
            n_art = art.get((iso, yr), np.nan)
            r["people_on_art_unaids"] = n_art
            if n_art and not np.isnan(n_art) and n_art > 0:
                r["observed_treat_spend_pp_nominal"] = r["total_hiv_spend_usd"] * r["treatment_share"] / n_art
                r["observed_treat_spend_pp_2023"] = inflate(r["observed_treat_spend_pp_nominal"], yr)
                r["total_spend_pp_2023"] = inflate(r["total_hiv_spend_usd"] / n_art, yr)
        r["ratio_ghcc_to_observed"] = r["full_cost_now"] / r["observed_treat_spend_pp_2023"] if r.get("observed_treat_spend_pp_2023") else np.nan
        rows.append(r)
    t = pd.DataFrame(rows).set_index("iso3")
    t["who_region"] = ci.who_region.reindex(t.index)
    t.to_csv(OUT)
    pd.set_option("display.width", 250)
    print(f"countries: {len(t)}; own study {int(t.own_study.sum())}; site gate fails {int((~t.gate_site_50_600).sum())}; "
          f"full-cost gate fails {int((~t.gate_full_50_600).sum())}: {list(t.index[~t.gate_full_50_600])}")
    have = t.dropna(subset=["observed_treat_spend_pp_2023"])
    print(f"observed spending per person on ART available for {len(have)} countries (Optima {int(have.spend_source.str.startswith('Optima').sum())}, GHED {int(have.spend_source.str.startswith('WHO').sum())})")
    print(f"ratio GHCC full cost / observed: median {have.ratio_ghcc_to_observed.median():.2f}, IQR {have.ratio_ghcc_to_observed.quantile(.25):.2f}-{have.ratio_ghcc_to_observed.quantile(.75):.2f}; "
          f"above 1 in {int((have.ratio_ghcc_to_observed > 1).sum())} of {len(have)}")
    print(have.groupby("who_region").ratio_ghcc_to_observed.median().round(2).to_dict())
    print(t.loc[[i for i in B2 if i in t.index], ["full_cost_now", "total_spend_pp_2023", "treatment_share", "observed_treat_spend_pp_2023", "ratio_ghcc_to_observed", "people_on_art_unaids"]].round(2).to_string())


if __name__ == "__main__":
    main()
