import sys, logging, numpy as np
sys.path.insert(0, "."); logging.disable(logging.WARNING)
import health_model as hm, scenarios as scn
I, P = hm.load_inputs(), hm.load_params()
SC = scn.build_scenario("Full US exit", {}, I["ci"]); F = hm.Fiscal(*scn.DEFAULT_FISCAL)
tot = 0; lo = hi = cen = 0
for c in sorted(set(I["lines"].iso3)):
    r = hm.run_country(c, SC, F, I, P, n_draws=400, keep_draws=True)
    d = r["draws"]["deaths"]
    # sum over lines and years per draw
    arr = sum(np.asarray(v).reshape(400, -1).sum(axis=1) for v in d.values()) if isinstance(d, dict) else np.asarray(d).reshape(400, -1).sum(axis=1)
    tot = tot + arr
    lo += r["totals"]["deaths_5y_lo"]; hi += r["totals"]["deaths_5y_hi"]; cen += r["totals"]["deaths_5y"]
print("central", cen, "sum of country percentiles", lo, hi)
print("percentiles of summed draws", np.percentile(tot, [2.5, 97.5]), "mean", tot.mean(), "median", np.median(tot))
