"""
Diff audit/before_fiscal.csv against audit/after_fiscal.csv (snapshot_numbers.py) for I-26 (interest data for the
debt-stress factor) and I-17 (data years, wording only). Run from the repo root:

    .venv/bin/python audit/fiscal_diff.py

Allowed changes: the fiscal-space values (interest, stress factor, capacity, replacement) in any run, and any value in
runs with a government response ("Replace a Set Share", "As Much as Fiscal Space Allows", gradual), whose replacement
is capped by fiscal capacity. Runs with no government response must not change otherwise. Exits 1 if anything else
moved. Prints the country table and all-country totals by preset and response (sudden cut).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
A = pd.read_csv(ROOT / "audit" / "before_fiscal.csv", index_col="key", low_memory=False)
B = pd.read_csv(ROOT / "audit" / "after_fiscal.csv", index_col="key", low_memory=False)
assert list(A.index) == list(B.index) and list(A.columns) == list(B.columns)
num = lambda x: pd.to_numeric(x, errors="coerce")  # noqa: E731
FISCAL_COLS = {"F.interest_pct_revenue", "F.stress_factor", "F.capacity", "F.replacement"}
COUNTRIES = {"NGA": "Nigeria", "PAK": "Pakistan", "IDN": "Indonesia", "VNM": "Vietnam", "KEN": "Kenya",
             "ETH": "Ethiopia", "MOZ": "Mozambique", "HND": "Honduras"}

same = (A == B) | (A.isna() & B.isna())
fa, fb = A.apply(num), B.apply(num)
tiny = ((fa - fb).abs() < 1e-6) | ((fa - fb).abs() <= 1e-9 * fa.abs())
changed = ~same & ~tiny.fillna(False)
resp = pd.Series([k.split("|")[2] if k.count("|") == 3 else "" for k in A.index], index=A.index)
counts, bad = {}, []
for c in A.columns[changed.any().to_numpy()]:
    for key in A.index[changed[c].to_numpy()]:
        if c in FISCAL_COLS:
            why = "fiscal-space values (interest, stress, capacity)"
        elif resp[key] in ("custom25", "max", "gradual"):
            why = "run with a government response (replacement capped by fiscal capacity)"
        else:
            why = "UNEXPLAINED"
            bad.append((key, c, A.loc[key, c], B.loc[key, c]))
        counts[why] = counts.get(why, 0) + 1
print(f"{A.size:,} values compared; {int(changed.values.sum()):,} changed")
for k, v in counts.items():
    print(f"  {k}: {v:,}")
if bad:
    print("UNEXPLAINED (first 20):")
    for b in bad[:20]:
        print(" ", b)


def k(iso, r):
    return f"{iso}|Full US exit|{r}|Sudden (default)"


rows = []
for iso, name in COUNTRIES.items():
    f = lambda col, r="none", fmt="{:,.0f}": (  # noqa: E731
        f"{fmt.format(num(A.loc[k(iso, r), col]))} -> {fmt.format(num(B.loc[k(iso, r), col]))}")
    rows.append({"Country": name, "Interest % revenue": f("F.interest_pct_revenue", fmt="{:.1f}"),
                 "Stress factor": f("F.stress_factor", fmt="{:.2f}"),
                 "Capacity US$/yr": f("F.capacity", fmt="${:,.0f}"),
                 "Deaths, Replace 25%": f("T.deaths_5y", "custom25"),
                 "Deaths, As Much as Fiscal Space": f("T.deaths_5y", "max")})
pd.set_option("display.width", 250)
print("\nFull US exit, sudden cut (deaths 2026-2030):")
print(pd.DataFrame(rows).set_index("Country").to_string())

print("\nAll countries, deaths 2026-2030 (sudden cut), by preset and response:")
keys = [x for x in A.index if x.count("|") == 3 and x.endswith("|Sudden (default)")]
df = pd.DataFrame({"preset": [x.split("|")[1] for x in keys], "resp": [x.split("|")[2] for x in keys],
                   "before": num(A.loc[keys, "T.deaths_5y"]).values, "after": num(B.loc[keys, "T.deaths_5y"]).values})
t = df.groupby(["preset", "resp"])[["before", "after"]].sum()
t["change"] = (t["after"] / t["before"] - 1).map(lambda v: f"{v:+.2%}" if np.isfinite(v) else "")
print(t.round(0).to_string())
sys.exit(1 if bad else 0)
