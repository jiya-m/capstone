"""
Automated checks for the dashboard audit (Step 4). Run from the repo root:

    .venv/bin/python audit/checks.py

Runs the model for every country x every donor preset x every government response and checks the invariants listed
in AUDIT.md; also runs global checks (precomputed files, monotonicity, zero cut, data reconciliation for Sections 1-3).
Writes audit/checks_results.csv (one row per country-scenario-check) and audit/checks_summary.csv / .md.
The model and app code are only imported and called, never changed.
"""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)

import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

OUT = ROOT / "audit"
TOL = 1e-6
I, P = hm.load_inputs(), hm.load_params()
CI, LINES = I["ci"], I["lines"]
PC = hm.draw_params(P, 0)
KAPPA = float(PC["hss_kappa"][0])
COUNTRIES = [c for c in CI.index if c in set(LINES.iso3)]
PRESETS = list(scn.PRESETS)
RESPONSES = {
    "none": scn.DEFAULT_FISCAL,
    "custom25": ("custom", 0.25, True, "pro_rata", "p75"),
    "max": ("max", 0.0, True, "pro_rata", "p75"),
    "gradual": ("gradual", 0.0, True, "pro_rata", "p75"),
}
rows: list[dict] = []


def rec(iso, preset, resp, check, ok, value="", detail=""):
    rows.append({"iso3": iso, "preset": preset, "response": resp, "check": check, "pass": bool(ok),
                 "value": value if isinstance(value, str) else f"{value:.6g}" if value == value else "nan",
                 "detail": detail})


def close(a, b, rel=1e-6, abs_=1e-6):
    return abs(a - b) <= max(abs_, rel * max(abs(a), abs(b)))


def gov_add_for(iso):
    """What the dashboard passes for 'Gradual budget increase' with its defaults (Steady, 0.5 points a year)."""
    b = hm.health_budget(iso, I)
    room = float(b["room_pct"]) if b["room_pct"] == b["room_pct"] else 0.0
    if room <= 0 or not (b["gov_spend_usd"] == b["gov_spend_usd"]):
        return None
    pts = scn.gov_shape("Steady", 0.5, room)
    return tuple(float(v) for v in hm.gov_add_from_points(pts, b["gov_spend_usd"])) if any(pts) else None


# --------------------------------------------------------------------------- #
# Independent reimplementation of the documented scenario cuts (for the 1-(1-a)(1-b) check)
# --------------------------------------------------------------------------- #
DIRECT = {"Bilateral agency", "NGOs", "Gates direct", "Other"}
US_PAIRS = {("United States", "WHO"): 1.0, ("United States", "Gavi"): 1.0, ("United States", "UNFPA"): 1.0,
            ("United States", "Global Fund"): 0.23}
OECD = {"United States": 0.57, "Germany": 0.174, "France": 0.109, "United Kingdom": 0.108, "Japan": 0.056}


def expected_cut(preset, iso, src, chan, bucket, opts):
    if preset == "IHME 2025 preliminary estimates":
        return 1.0 - I["trend_map"].get((src, chan, bucket), 1.0)
    direct = chan in DIRECT
    a, pair, ch = 0.0, {}, {}
    if preset in ("Full US exit", "Combined retreat"):
        if src == "United States" and direct:
            a = 1.0
        pair = US_PAIRS
    if preset == "America First MOUs":
        if src == "United States" and direct:
            a = scn.mou_cuts(CI, opts["mou_year"]).get(iso, opts["non_mou_cut"])
        pair = US_PAIRS
    if preset in ("OECD-reported 2025 aid cuts", "Combined retreat") and src in OECD:
        if not (preset == "Combined retreat" and src == "United States"):
            a = OECD[src]
    if preset == "Global Fund & Gavi shortfalls":
        ch = {"Global Fund": 0.28, "Gavi": 0.24}
    if preset == "Custom":
        a = (opts["custom_direct"][src] if direct else opts["custom_multi"][src]) / 100
    a = pair.get((src, chan), a)
    b = ch.get(chan, 0.0)
    return float(np.clip(1 - (1 - a) * (1 - b), -1, 1))


# --------------------------------------------------------------------------- #
# Per-run checks
# --------------------------------------------------------------------------- #
def per_run(iso, preset, resp, res, fiscal_t, opts):
    T, L, B, C, F = res["totals"], res["lines"], res["buckets"], res["committed"], res["fiscal"]
    Lx = L.set_index("line")
    Bx = B.set_index("bucket")
    show = L[(L["base_usd"] > 0) | (L["net_loss_usd"] != 0)]
    gains = T.get("gains", 0) > 0

    # 1-2 displayed values finite and non-negative
    disp = {f"T.{k}": T[k] for k in ("base", "gross", "replaced", "net", "deaths_5y", "deaths_5y_lo", "deaths_5y_hi",
                                     "deaths_y1")}
    disp.update({f"B.{b}.{k}": Bx.loc[b, k] for b in hm.BUCKETS for k in ("gross_loss_usd", "replaced_usd",
                                                                            "net_loss_usd", "deaths_5y")})
    disp["HIV.infections_5y"] = Bx.loc["HIV", "infections_5y"]
    disp.update({f"C.{k}": v for k, v in C["after_parts"].items()})
    disp["C.after_2030"] = C["after_2030"]
    for r in show.itertuples():
        for k in ("base_usd", "net_loss_usd", "unit_cost", "units_lost", "deaths_5y", "deaths_5y_lo", "deaths_5y_hi"):
            disp[f"L.{r.line}.{k}"] = getattr(r, k)
        if r.need == r.need and r.need > 0:
            disp[f"L.{r.line}.cov0"] = r.cov0
            disp[f"L.{r.line}.cov_drop_pp"] = r.cov_drop_pp
    disp.update({f"F.{k}": F[k] for k in ("ghes", "capacity", "replacement")})
    bad_nan = [k for k, v in disp.items() if not np.isfinite(float(v))]
    rec(iso, preset, resp, "displayed_finite", not bad_nan, len(bad_nan), "; ".join(bad_nan[:8]))
    neg = [k for k, v in disp.items() if np.isfinite(float(v)) and float(v) < -1e-6]
    rec(iso, preset, resp, "displayed_nonnegative", not neg or gains, len(neg),
        ("aid gains in scenario; " if gains else "") + "; ".join(neg[:8]))

    # 3-4 coverage
    cov_bad, cap_bad = [], []
    for r in show.itertuples():
        if not (r.need == r.need and r.need > 0 and r.cov0 == r.cov0):
            continue
        after = r.cov0 - r.cov_drop_pp / 100
        if not (0 <= r.cov0 <= 1 + TOL) or after < -1e-6 or after > r.cov0 + 1e-6:
            cov_bad.append(f"{r.line}: {r.cov0:.3f}->{after:.3f}")
        if r.units_lost > r.cov0 * r.need * (1 + 1e-6) + 1e-6:
            cap_bad.append(f"{r.line}: {r.units_lost:.0f}>{r.cov0 * r.need:.0f}")
    rec(iso, preset, resp, "coverage_in_0_1_and_after_le_before", not cov_bad, len(cov_bad), "; ".join(cov_bad))
    rec(iso, preset, resp, "people_losing_le_people_covered", not cap_bad, len(cap_bad), "; ".join(cap_bad))

    # 5-6 money ordering
    ok = (T["net"] <= T["gross"] + TOL) and (T["gross"] <= T["base"] * (1 + 1e-9) + TOL) and \
         (-TOL <= T["replaced"] <= T["gross"] + TOL)
    rec(iso, preset, resp, "net_le_gross_le_base_and_replaced_le_gross", ok, T["gross"] / T["base"] if T["base"] else 0,
        f"net={T['net']:.0f} gross={T['gross']:.0f} base={T['base']:.0f} replaced={T['replaced']:.0f}")
    if fiscal_t[0] in ("custom", "max"):
        rec(iso, preset, resp, "replaced_le_fiscal_capacity", T["replaced"] <= F["capacity"] + TOL,
            T["replaced"] - F["capacity"], f"replaced={T['replaced']:.0f} capacity={F['capacity']:.0f}")
    # line-level: net loss per line <= gross per line
    lbad = [r.line for r in L.itertuples() if r.net_loss_usd > r.gross_loss_usd + 1e-6 or r.replaced_usd < -1e-6]
    rec(iso, preset, resp, "line_net_le_line_gross", not lbad, len(lbad), "; ".join(lbad))

    # 7-9 deaths
    dneg = [k for k, v in disp.items() if ("deaths" in k or k.startswith("C.")) and float(v) < -1e-6]
    rec(iso, preset, resp, "deaths_nonnegative", not dneg or gains, len(dneg), "; ".join(dneg[:8]))
    rbad = []
    trip = [("T", T["deaths_5y_lo"], T["deaths_5y"], T["deaths_5y_hi"]),
            ("C.after", C["after_2030_lo"], C["after_2030"], C["after_2030_hi"]),
            ("C.committed", C["deaths_lo"], C["deaths"], C["deaths_hi"]),
            ("HIV.inf", Bx.loc["HIV", "infections_5y_lo"], Bx.loc["HIV", "infections_5y"],
             Bx.loc["HIV", "infections_5y_hi"])]
    trip += [(f"B.{b}", Bx.loc[b, "deaths_5y_lo"], Bx.loc[b, "deaths_5y"], Bx.loc[b, "deaths_5y_hi"]) for b in hm.BUCKETS]
    trip += [(f"L.{r.line}", r.deaths_5y_lo, r.deaths_5y, r.deaths_5y_hi) for r in show.itertuples()]
    for name, lo, c, hi in trip:
        if not (lo - 1e-6 <= c <= hi + 1e-6):
            rbad.append(f"{name}: {lo:.1f} <= {c:.1f} <= {hi:.1f}")
    rec(iso, preset, resp, "range_lo_le_central_le_hi", not rbad, len(rbad), "; ".join(rbad[:6]))
    ybad = [n for n, a, b in [("T", T["deaths_y1"], T["deaths_5y"])] +
            [(r.line, r.deaths_y1, r.deaths_5y) for r in L.itertuples()] if a > b + 1e-6 and not gains]
    rec(iso, preset, resp, "year1_le_5year", not ybad, len(ybad), "; ".join(ybad))

    # 10 sums
    sb = []
    for b in hm.BUCKETS:
        s = L.loc[L["bucket"] == b, "deaths_5y"].sum()
        if not close(s, Bx.loc[b, "deaths_5y"], 1e-9, 1e-6):
            sb.append(f"{b}: lines {s:.3f} vs bucket {Bx.loc[b, 'deaths_5y']:.3f}")
    if not close(B["deaths_5y"].sum(), T["deaths_5y"], 1e-9, 1e-6):
        sb.append(f"buckets {B['deaths_5y'].sum():.3f} vs total {T['deaths_5y']:.3f}")
    for k_b, k_t in (("gross_loss_usd", "gross"), ("replaced_usd", "replaced"), ("net_loss_usd", "net")):
        if not close(B[k_b].sum(), T[k_t], 1e-6, 1.0):
            sb.append(f"{k_b}: buckets {B[k_b].sum():.0f} vs total {T[k_t]:.0f}")
    rec(iso, preset, resp, "lines_sum_to_buckets_sum_to_totals", not sb, len(sb), "; ".join(sb))
    # path chart and headline agree
    pth = res["path"]
    rec(iso, preset, resp, "path_chart_sums_to_headline", close(pth.values.sum(), T["deaths_5y"], 1e-9, 1e-6) and
        close(pth.iloc[0].sum(), T["deaths_y1"], 1e-9, 1e-6), pth.values.sum() - T["deaths_5y"])
    # kappa / unspecified spreading conserves money: direct-line effective losses + non-service systems money = bucket
    cells = res["cells"]
    kb = []
    for b in ("HIV", "TB", "Malaria"):
        hss = cells.loc[cells["line"] == hm.HSS[b], "loss"].sum()
        direct = L.loc[L["bucket"] == b, "gross_loss_usd"].sum()
        bucket = Bx.loc[b, "gross_loss_usd"]
        if not close(direct + (1 - KAPPA) * hss, bucket, 1e-6, 1.0):
            kb.append(f"{b}: direct {direct:.0f} + (1-k)hss {(1 - KAPPA) * hss:.0f} vs bucket {bucket:.0f}")
    rec(iso, preset, resp, "unspec_and_kappa_conserve_money", not kb, len(kb), "; ".join(kb))
    # 1-(1-a)(1-b) applied once, exactly as documented
    exp = np.array([expected_cut(preset, iso, s, c, b, opts) for s, c, b in
                    zip(cells["src_grp"], cells["chan_grp"], cells["bucket"])])
    diff = np.abs(exp - cells["cut"].to_numpy()) if len(cells) else np.zeros(1)
    rec(iso, preset, resp, "cut_formula_matches_documented_scenario", diff.max() < 1e-9, float(diff.max()))

    # 11-12 table and hero agree with the headline
    import model_section as ms   # imported here: streamlit-free functions only
    rws = ms._service_rows(show)
    tb = []
    if not close(rws["deaths_5y"].sum(), T["deaths_5y"], 1e-9, 1e-6):
        tb.append(f"table deaths {rws['deaths_5y'].sum():.2f} vs headline {T['deaths_5y']:.2f}")
    o_base, o_net = T["base"] - rws["base_usd"].sum(), T["net"] - rws["net_loss_usd"].sum()
    if o_base < -1 or o_net < -1:
        tb.append(f"Other Aid row negative (shown as $0): base {o_base:.0f}, net {o_net:.0f}")
    rec(iso, preset, resp, "table_total_row_equals_headline", not tb, len(tb), "; ".join(tb))
    care, _ = ms.care_breakdown(Lx)
    ppl = rws.loc[rws["line"] != "hiv_prev", "units_lost"].sum()
    rec(iso, preset, resp, "hero_people_equals_table_people", close(care, ppl, 1e-9, 0.5), care - ppl,
        f"hero {care:.0f} table {ppl:.0f}")
    # per-year label: aid at risk per year equals the scenario's yearly loss
    G = float(np.clip(cells.groupby("line")["loss"].sum(), 0, None).sum()) if len(cells) else 0.0
    rec(iso, preset, resp, "aid_at_risk_is_per_year_not_5yr_total", close(G, T["gross"], 1e-9, 1.0), T["gross"] / G if G else 1)
    # coverage shown as fraction (not percent)
    pct_bad = [r.line for r in show.itertuples() if r.cov0 == r.cov0 and r.cov0 > 1.0 + TOL]
    rec(iso, preset, resp, "coverage_is_fraction_not_percent", not pct_bad, len(pct_bad), "; ".join(pct_bad))
    return T


def main():
    t0 = time.time()
    # ---------------- per-run checks ----------------
    for preset in PRESETS:
        opts = scn.default_opts(preset, CI)
        sc = scn.build_scenario(preset, opts, CI)
        for resp, ft in RESPONSES.items():
            for iso in COUNTRIES:
                gov_add = gov_add_for(iso) if resp == "gradual" else None
                res = hm.run_country(iso, sc, hm.Fiscal(*ft), I, P, n_draws=400, gov_add_usd=gov_add)
                per_run(iso, preset, resp, res, ft, opts)
    print(f"per-run checks done in {time.time() - t0:.0f}s")

    # ---------------- precomputed files vs a fresh run ----------------
    for preset in scn.PRECOMPUTED_PRESETS:
        path = scn.precomputed_path(hm.MODEL_DIR, preset)
        old = pd.read_csv(path).set_index("iso3")
        new = hm.run_all(scn.build_scenario(preset, scn.default_opts(preset, CI), CI), hm.Fiscal(*scn.DEFAULT_FISCAL), I,
                         P, n_draws=scn.ALL_COUNTRY_DRAWS).set_index("iso3")
        for iso in new.index:
            cols = [c for c in new.columns if c in old.columns]
            d = {c: abs(new.loc[iso, c] - old.loc[iso, c]) / max(1.0, abs(new.loc[iso, c])) for c in cols
                 if pd.notna(new.loc[iso, c]) or pd.notna(old.loc[iso, c])}
            worst = max(d, key=lambda c: d[c] if d[c] == d[c] else 1.0)
            rec(iso, preset, "none", "precomputed_csv_matches_fresh_run", d[worst] < 1e-6, d[worst], worst)
        missing = set(new.columns) - set(old.columns)
        rec("ALL", preset, "none", "precomputed_csv_has_all_columns", not missing, len(missing), ", ".join(missing))
        # also the dashboard's own country run == the All Countries row
        for iso in ("KEN", "NGA", "MOZ", "HND", "IRQ"):
            r = hm.run_country(iso, scn.build_scenario(preset, scn.default_opts(preset, CI), CI),
                               hm.Fiscal(*scn.DEFAULT_FISCAL), I, P, n_draws=400)
            ok = close(r["totals"]["deaths_5y"], old.loc[iso, "deaths_5y"], 1e-6, 1e-3) and \
                close(r["totals"]["gross"], old.loc[iso, "gross_loss_usd"], 1e-9, 1.0)
            rec(iso, preset, "none", "dashboard_country_equals_all_countries_row", ok,
                r["totals"]["deaths_5y"] - old.loc[iso, "deaths_5y"])
    print(f"precomputed checks done in {time.time() - t0:.0f}s")

    # ---------------- monotonic in the size of the cut, and zero cut ----------------
    for preset in PRESETS:
        opts = scn.default_opts(preset, CI)
        for resp in ("none", "custom25"):
            for iso in COUNTRIES:
                vals = []
                for k in (0.0, 0.25, 0.5, 0.75, 1.0):
                    sc = scn.build_scenario(preset, opts, CI)
                    sc.scale = k
                    r = hm.run_country(iso, sc, hm.Fiscal(*RESPONSES[resp]), I, P, n_draws=2)
                    vals.append((r["totals"]["deaths_5y"], r["committed"]["deaths"], r["totals"]["net"],
                                 r["totals"]["gross"]))
                    if k == 0.0:
                        z = max(abs(r["totals"]["deaths_5y"]), abs(r["totals"]["gross"]), abs(r["committed"]["deaths"]))
                        rec(iso, preset, resp, "zero_cut_gives_zero", z < 1e-6, z)
                d5 = [v[0] for v in vals]
                cm = [v[1] for v in vals]
                nt = [v[2] for v in vals]
                gains = vals[-1][3] < 0
                mono = all(d5[i + 1] >= d5[i] - 1e-6 for i in range(4)) and all(cm[i + 1] >= cm[i] - 1e-6 for i in range(4))
                rec(iso, preset, resp, "more_cut_never_fewer_deaths", mono or gains,
                    min(d5[i + 1] - d5[i] for i in range(4)), "deaths 0/25/50/75/100%: " + ", ".join(f"{x:.0f}" for x in d5)
                    + (" (scenario raises aid)" if gains else ""))
                rec(iso, preset, resp, "more_cut_never_less_net_loss", all(nt[i + 1] >= nt[i] - 1e-6 for i in range(4)) or gains,
                    min(nt[i + 1] - nt[i] for i in range(4)))
    print(f"monotonic checks done in {time.time() - t0:.0f}s")

    # ---------------- data checks ----------------
    # no line in two buckets
    lb = LINES.groupby("line")["bucket"].nunique()
    rec("ALL", "", "", "no_line_in_two_buckets", (lb == 1).all(), int((lb > 1).sum()))
    # model line baselines vs IHME DAH bucket totals (country_data, 2021-23 average, thousands of US$)
    idx = pd.read_csv(ROOT / "country_data" / "_index.csv")
    f_of = dict(zip(idx.recipient_isocode, idx.file))
    bcol = {"HIV": "hiv_dah_23", "TB": "tb_dah_23", "Malaria": "mal_dah_23", "Immunization": "nch_cnv_dah_23"}
    for iso in COUNTRIES:
        if iso not in f_of:
            rec(iso, "", "", "line_baselines_equal_IHME_bucket_totals", False, "", "no country_data file")
            continue
        cd = pd.read_csv(ROOT / "country_data" / f_of[iso])
        cd = cd[cd.year.between(2021, 2023)]
        mod = LINES[LINES.iso3 == iso].groupby("bucket")["usd"].sum()
        bad = []
        for b, c in bcol.items():
            ihme = cd[c].sum() / 3 * 1e3
            m = mod.get(b, 0.0)
            if not close(m, ihme, 0.005, 1000):
                bad.append(f"{b}: model {m / 1e6:.2f}M vs IHME {ihme / 1e6:.2f}M")
        rec(iso, "", "", "line_baselines_equal_IHME_bucket_totals", not bad, len(bad), "; ".join(bad))
    # percentages: coverage inputs stored as percent in 0-100
    for c in ("sh_hiv_artc_zs", "sh_hiv_pmtc_zs", "sh_tbs_dtec_zs", "sh_mlr_nets_zs", "sh_mlr_tret_zs", "sh_imm_idpt",
              "sh_xpd_ghed_ge_zs"):
        v = CI[c].dropna()
        rec("ALL", "", "", f"percent_scale_{c}", bool(((v >= 0) & (v <= 100)).all() and v.median() > 1),
            float(v.max()), f"min {v.min():.2f} median {v.median():.1f} max {v.max():.1f}; n>100: {(v > 100).sum()}")
    for iso in CI.index:
        hb = hm.health_budget(iso, I)
        s = hb["share_pct"]
        rec(iso, "", "", "health_share_in_0_100", s != s or 0 < s < 100, s, hb["gov_source"])
    # unit costs inside their documented ranges; country-specific vs default
    ref = pd.read_csv(ROOT / "unit_cost_reference.csv")
    art_specific = set(ref.loc[ref.kind == "art_site_cost", "key"])
    lo_p = {k: np.array([float(P.loc[k, "low"])]) for k in P.index}
    hi_p = {k: np.array([float(P.loc[k, "high"])]) for k in P.index}
    for iso in CI.index:
        row = CI.loc[iso]
        uc_c, uc_lo, uc_hi = hm.unit_costs(row, PC), hm.unit_costs(row, lo_p), hm.unit_costs(row, hi_p)
        bad = [k for k in uc_c if not (min(uc_lo[k][0], uc_hi[k][0]) - 1e-9 <= uc_c[k][0] <= max(uc_lo[k][0], uc_hi[k][0]) + 1e-9)]
        ig = row.get("income_group")
        rec(iso, "", "", "unit_costs_inside_parameter_range", not bad, len(bad),
            f"ART {'country study' if iso in art_specific else 'default (ARV median + GDP-scaled staff)'}; "
            f"TB income group {'World Bank' if isinstance(ig, str) and ig else 'GDP fallback'}: {hm.income_group(row)}"
            + (f"; out of range: {bad}" if bad else ""))
    # currency: constant-2023 GDP equals nominal GDP in 2023
    for iso in CI.index:
        f = ROOT / "macro_data" / f"{iso}.csv"
        if not f.exists():
            rec(iso, "", "", "gdp_constant2023_equals_nominal_in_2023", False, "", "no macro file")
            continue
        m = pd.read_csv(f)
        r = m[m.year == 2023]
        if len(r) and pd.notna(r["gdp_usd_bn"].iloc[0]) and pd.notna(r["gdp_usd_bn_2023"].iloc[0]):
            a, b = r["gdp_usd_bn"].iloc[0], r["gdp_usd_bn_2023"].iloc[0]
            rec(iso, "", "", "gdp_constant2023_equals_nominal_in_2023", close(a, b, 1e-6), b / a)
        else:
            rec(iso, "", "", "gdp_constant2023_equals_nominal_in_2023", False, "", "2023 GDP missing")
    # Section 1: stacked components = total; 2023 matches the raw IHME file
    raw = pd.read_csv(ROOT / "datasets" / "IHME_HEALTH_SPENDING_1995_2023_Y2026M09D21.CSV", encoding="utf-8-sig",
                      usecols=["iso3", "level", "year", "the_total_mean", "ghes_total_mean", "ppp_total_mean",
                               "oop_total_mean", "dah_total_mean"])
    raw = raw[raw.level == "Country"].set_index(["iso3", "year"])
    for iso in CI.index:
        f = ROOT / "spending_data" / f"{iso}.csv"
        if not f.exists():
            rec(iso, "", "", "section1_components_sum_to_total", False, "", "no spending file")
            continue
        sp = pd.read_csv(f)
        sp = sp[sp.year.between(2015, 2023)]
        comp = sp[["dah_total_mean", "ghes_total_mean", "ppp_total_mean", "oop_total_mean"]].sum(axis=1)
        rel = (comp / sp["the_total_mean"] - 1).abs().max()
        rec(iso, "", "", "section1_components_sum_to_total", rel < 0.01, rel)
        r23 = sp[sp.year == 2023]
        if len(r23) and (iso, 2023) in raw.index:
            d = max(abs(r23[c].iloc[0] - raw.loc[(iso, 2023), c]) / max(1, abs(raw.loc[(iso, 2023), c]))
                    for c in ("the_total_mean", "ghes_total_mean", "dah_total_mean"))
            rec(iso, "", "", "section1_2023_matches_raw_IHME_file", d < 1e-6, d)
        # Section 2 DAH (IHME DAH database) vs Section 1 DAH (IHME spending database), 2023
        if iso in f_of and len(r23):
            cd = pd.read_csv(ROOT / "country_data" / f_of[iso])
            s2 = cd.loc[cd.year == 2023, "dah_23"].sum()
            s1 = r23["dah_total_mean"].iloc[0]
            rec(iso, "", "", "section2_dah_2023_matches_section1_dah_2023", close(s2, s1, 0.02), s2 / s1 if s1 else np.nan,
                f"Section 2 {s2 / 1e3:.1f}M vs Section 1 {s1 / 1e3:.1f}M")
    # Section 3: WEO identity, revenue items vs file total, COFOG shares, and the default year's coverage levels
    for iso in CI.index:
        mf, rf, cf = (ROOT / d / f"{iso}.csv" for d in ("macro_data", "revenue_data", "cofog_all"))
        if not mf.exists():
            continue
        mac = pd.read_csv(mf)
        rev = pd.read_csv(rf) if rf.exists() else None
        spd = pd.read_csv(cf) if cf.exists() else None
        ry = set(rev.year) if rev is not None else set()
        sy = set(spd.year) if spd is not None else set()
        if not (ry or sy):
            rec(iso, "", "", "section3_has_data", False, "", "no revenue or COFOG file")
            continue
        both = sorted(ry & sy, reverse=True)
        y = both[0] if both else sorted(ry | sy, reverse=True)[0]
        r = mac[mac.year == y]
        if len(r) and r[["gov_revenue_pct_gdp", "gov_expenditure_pct_gdp", "gov_net_lending_pct_gdp"]].notna().all(axis=1).iloc[0]:
            R, E, NL = (float(r[c].iloc[0]) for c in ("gov_revenue_pct_gdp", "gov_expenditure_pct_gdp", "gov_net_lending_pct_gdp"))
            rec(iso, str(y), "", "section3_weo_spending_minus_revenue_equals_borrowing", abs((E - R) + NL) <= 0.5, (E - R) + NL)
        else:
            rec(iso, str(y), "", "section3_weo_totals_present_for_default_year", False, "", "WEO totals missing: each "
                "side sized from its own file")
        if rev is not None and y in ry:
            g = rev[rev.year == y]
            if g["total_pct_gdp"].notna().any():
                d = g["pct_gdp"].sum() - g["total_pct_gdp"].dropna().iloc[0]
                rec(iso, str(y), "", "section3_revenue_items_sum_to_file_total", abs(d) <= 0.5, d, g["coverage"].iloc[0])
            rec(iso, str(y), "", "section3_revenue_mix_is_general_government",
                "general" in str(g["coverage"].iloc[0]).lower(), "", f"revenue file coverage: {g['coverage'].iloc[0]}")
        if spd is not None and y in sy:
            g = spd[spd.year == y]
            s = g["pct_outlays"].sum()
            rec(iso, str(y), "", "section3_cofog_shares_sum_to_100", abs(s - 100) <= 0.5, s)
            rec(iso, str(y), "", "section3_spending_mix_is_general_government",
                "general" in str(g["coverage"].iloc[0]).lower(), "", f"COFOG coverage: {g['coverage'].iloc[0]}")

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "checks_results.csv", index=False)
    summ = (out.groupby("check")["pass"].agg(runs="size", passed="sum").assign(failed=lambda d: d.runs - d.passed)
            .sort_values("failed", ascending=False))
    summ.to_csv(OUT / "checks_summary.csv")
    lines_md = ["| Check | Runs | Passed | Failed |", "|---|---|---|---|"]
    lines_md += [f"| {k} | {r.runs} | {r.passed} | {r.failed} |" for k, r in summ.iterrows()]
    (OUT / "checks_summary.md").write_text("\n".join(lines_md) + "\n")
    print(summ.to_string())
    print(f"done in {time.time() - t0:.0f}s; {len(out)} rows")


if __name__ == "__main__":
    main()
