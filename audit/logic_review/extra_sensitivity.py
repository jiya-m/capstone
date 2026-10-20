import sys, numpy as np
sys.path.insert(0, "audit/logic_review"); sys.argv=["x"]
import importlib.util
spec = importlib.util.spec_from_file_location("s", "audit/logic_review/sensitivity.py")
# reuse helpers without re-running the whole sweep
src = open("audit/logic_review/sensitivity.py").read().split("rows = []")[0]
g = {"__file__": "audit/logic_review/sensitivity.py"}; exec(src, g)
I0, P0, total, with_param, with_ci = g["I0"], g["P0"], g["total"], g["with_param"], g["with_ci"]
import prepare_model as pm
ci = I0["ci"]
base = total(); print("base", base)
u5 = np.where(ci.index.isin(pm.SSA), 0.75, 0.40)
print("malaria u5 only", with_ci("malaria_deaths", ci["malaria_deaths"] * u5))
for risk in (0.20, 0.40, 0.60):
    print("ART 5y risk", risk, with_param("art_hazard_mult", risk / 0.1730))
