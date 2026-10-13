"""
I-01 before/after: aid at risk, 5-year deaths and US share of aid for six countries, and all-country totals per preset,
with model_data built WITHOUT (before) and WITH (after) IHME's elim_ch filter. Run from the repo root:

    .venv/bin/python audit/i01_before_after.py <folder with the pre-fix model_data files>

Prints markdown tables (pasted into audit/I-01.md). The model code is only called, never changed.
"""
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)

import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

if len(sys.argv) < 2:
    sys.exit("usage: .venv/bin/python audit/i01_before_after.py <folder with the pre-fix model_data files>")
BEFORE = Path(sys.argv[1])
AFTER = hm.MODEL_DIR
SIX = ["KEN", "NGA", "ETH", "SOM", "HND", "MOZ"]
P = hm.load_params()


def country_rows(model_dir):
    I = hm.load_inputs(model_dir)
    out = {}
    for preset in ("Full US exit", "America First MOUs"):
        sc = scn.build_scenario(preset, scn.default_opts(preset, I["ci"]), I["ci"])
        for iso in SIX:
            r = hm.run_country(iso, sc, hm.Fiscal(*scn.DEFAULT_FISCAL), I, P, n_draws=400)
            out[(preset, iso)] = (r["totals"]["gross"], r["totals"]["deaths_5y"])
    us = {}
    for iso in SIX:
        L = I["lines"][I["lines"].iso3 == iso]
        us[iso] = (L.loc[L.src_grp == "United States", "usd"].sum() / L["usd"].sum(), L["usd"].sum())
    return out, us


def pct(a, b):
    return f"{(b / a - 1) * 100:+.1f}%" if a else "n/a"


def main():
    b_rows, b_us = country_rows(BEFORE)
    a_rows, a_us = country_rows(AFTER)
    print("| Scenario | Country | Aid at risk before | after | change | Deaths 2026-2030 before | after | change |")
    print("|---|---|---|---|---|---|---|---|")
    for (preset, iso), (g0, d0) in b_rows.items():
        g1, d1 = a_rows[(preset, iso)]
        print(f"| {preset} | {iso} | ${g0 / 1e6:,.1f}M | ${g1 / 1e6:,.1f}M | {pct(g0, g1)} | {d0:,.0f} | {d1:,.0f} | {pct(d0, d1)} |")
    print()
    print("| Country | Modelled baseline before | after | change | US share of modelled aid before | after |")
    print("|---|---|---|---|---|---|")
    for iso in SIX:
        (s0, t0), (s1, t1) = b_us[iso], a_us[iso]
        print(f"| {iso} | ${t0 / 1e6:,.1f}M | ${t1 / 1e6:,.1f}M | {pct(t0, t1)} | {s0:.1%} | {s1:.1%} |")
    print()
    print("| Preset (no backfill, 70 countries) | Aid at risk before | after | change | Deaths 2026-2030 before | after | change "
          "| Deaths 2031-2035 before | after |")
    print("|---|---|---|---|---|---|---|---|---|")
    for preset in scn.PRECOMPUTED_PRESETS:
        name = scn.precomputed_path(Path("."), preset).name
        o, n = pd.read_csv(BEFORE / name), pd.read_csv(AFTER / name)
        print(f"| {preset} | ${o.gross_loss_usd.sum() / 1e9:,.2f}B | ${n.gross_loss_usd.sum() / 1e9:,.2f}B | "
              f"{pct(o.gross_loss_usd.sum(), n.gross_loss_usd.sum())} | {o.deaths_5y.sum():,.0f} | {n.deaths_5y.sum():,.0f} | "
              f"{pct(o.deaths_5y.sum(), n.deaths_5y.sum())} | {o.deaths_after_2030.sum():,.0f} | {n.deaths_after_2030.sum():,.0f} |")


if __name__ == "__main__":
    main()
