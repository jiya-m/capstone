"""Save sudden-cut results so tests can check that the current model, with the default path and the later mechanisms
switched off, reproduces them. baseline_sudden.json was made by running this file at commit 5eb6111 (before TB spread,
malaria rebound, vaccine cohorts and HIV infection deaths) with the current model_data/country_inputs.csv.
Run from the repo root:  python tests/make_baseline.py

America First MOUs is the exception (audit I-02/I-03): the preset was redefined to follow each country's MOU schedule
year by year, only for countries with a signed MOU and schedule data, so the old model cannot produce it. Its entries
(KEN, NGA, MOZ; HND and IRQ cannot run it) are written by the current model with the later mechanisms switched off,
as test (a) runs it:  python tests/make_baseline.py --mou-only
They lock the schedule-driven results against unintended changes; tests/test_mou.py checks the schedule itself.

New HIV infections (audit I-05): the dashboard now shows the central run, not the median of the draws, so every
entry's line infections_5y was replaced by the central run. For the 90 non-MOU entries the original model (commit
5eb6111, n_draws=0) and the current model (later mechanisms off) give identical central infections (max difference 0),
so only that statistic changed; all other fields are as before."""
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

COUNTRIES = ["KEN", "NGA", "MOZ", "HND", "IRQ"]
FISCALS = {"none": scn.DEFAULT_FISCAL, "custom25": ("custom", 0.25, True, "pro_rata", "p75"),
           "max_lives": ("max", 0.0, True, "lives_first", "p75")}
N_DRAWS = 100
MOU = "America First MOUs"
NEW_MECHANISMS = ["tb_secondary", "mal_resurgence", "hiv_inf_death_untreated", "hiv_inf_death_treated"]  # 0 = off


def snapshot(res):
    L = res["lines"].set_index("line")
    cols = ["units_lost", "units_lost_lo", "units_lost_hi", "deaths_y1", "deaths_5y", "deaths_5y_lo", "deaths_5y_hi",
            "infections_5y", "net_loss_usd", "replaced_usd", "cov_drop_pp"]
    return {"lines": {l: {c: float(L.loc[l, c]) if L.loc[l, c] == L.loc[l, c] else None for c in cols} for l in L.index},
            "totals": {k: float(v) for k, v in res["totals"].items()},
            "path": {b: [float(x) for x in res["path"][b]] for b in hm.BUCKETS}}


def main():
    I, P = hm.load_inputs(), hm.load_params()
    out = {}
    for iso in COUNTRIES:
        for preset in scn.PRESETS:
            if preset == MOU and hasattr(scn, "mou_group") and scn.mou_group(I["ci"], iso) != "A":
                continue
            sc = scn.build_scenario(preset, scn.default_opts(preset, I["ci"]), I["ci"])
            for fk, ft in FISCALS.items():
                out[f"{iso}|{preset}|{fk}"] = snapshot(hm.run_country(iso, sc, hm.Fiscal(*ft), I, P, n_draws=N_DRAWS))
    p = Path(__file__).parent / "baseline_sudden.json"
    p.write_text(json.dumps(out))
    print(f"saved {len(out)} runs to {p}")


def refresh_mou():
    """Replace only the America First MOUs entries, with the current model and the later mechanisms switched off."""
    I, P = hm.load_inputs(), hm.load_params()
    P.loc[NEW_MECHANISMS, ["central", "low", "high"]] = 0.0
    p = Path(__file__).parent / "baseline_sudden.json"
    out = {k: v for k, v in json.loads(p.read_text()).items() if k.split("|")[1] != MOU}
    sc = scn.build_scenario(MOU, scn.default_opts(MOU, I["ci"]), I["ci"])
    for iso in COUNTRIES:
        if scn.mou_group(I["ci"], iso) != "A":
            continue
        for fk, ft in FISCALS.items():
            out[f"{iso}|{MOU}|{fk}"] = snapshot(hm.run_country(iso, sc, hm.Fiscal(*ft), I, P, n_draws=N_DRAWS))
    p.write_text(json.dumps(out))
    print(f"saved {len(out)} runs to {p} ({sum(k.split('|')[1] == MOU for k in out)} America First MOUs)")


if __name__ == "__main__":
    refresh_mou() if "--mou-only" in sys.argv else main()
