"""
Diff audit/before_malaria.csv against audit/after_malaria.csv (made by snapshot_numbers.py) for the malaria batch
(I-06, I-11, I-27 and I-17 malaria parts). Run from the repo root:

    .venv/bin/python audit/malaria_diff.py

Attributes every changed value: malaria lines and bucket, the totals and year/path values that include malaria deaths,
the malaria per-US$1M card and the All Countries sums may change; HIV, TB and immunization lines and buckets, aid and
fiscal values may not. Prints the report tables (countries below, presets, cards) and exits 1 if anything else moved.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
A = pd.read_csv(ROOT / "audit" / "before_malaria.csv", index_col="key", low_memory=False)
B = pd.read_csv(ROOT / "audit" / "after_malaria.csv", index_col="key", low_memory=False)
assert list(A.index) == list(B.index) and list(A.columns) == list(B.columns)
COUNTRIES = {"NGA": "Nigeria", "COD": "DR Congo", "UGA": "Uganda", "MOZ": "Mozambique", "BFA": "Burkina Faso",
             "TZA": "Tanzania", "KEN": "Kenya", "ETH": "Ethiopia", "MWI": "Malawi", "NER": "Niger", "HND": "Honduras"}
num = lambda x: pd.to_numeric(x, errors="coerce")  # noqa: E731


def allowed(col: str) -> str | None:
    """Why this column may change, or None."""
    if col.startswith(("L.mal_", "B.Malaria.", "path.Malaria.", "card.Malaria.")):
        return "malaria line, bucket, path or card"
    if col in ("T.deaths_5y", "T.deaths_5y_lo", "T.deaths_5y_hi", "T.deaths_y1") or col.startswith("C.") or \
            (col.startswith("Y.") and col.endswith(".deaths")):
        return "total deaths (include malaria)"
    if col.startswith("sum.") and ("Malaria" in col or "deaths" in col or "infections" in col):
        return "All Countries sum"
    if col == "break_even":
        return "break-even (deaths-based)"
    return None


same = (A == B) | (A.isna() & B.isna())
fa, fb = A.apply(num), B.apply(num)
tiny = ((fa - fb).abs() < 1e-6) | ((fa - fb).abs() <= 1e-9 * fa.abs())
changed = ~same & ~tiny.fillna(False)
rows, bad = [], []
for c in A.columns[changed.any().to_numpy()]:
    why = allowed(c)
    n = int(changed[c].sum())
    rows.append((why or "UNEXPLAINED", c, n))
    if why is None:
        bad.append((c, n, list(A.index[changed[c].to_numpy()][:5])))
d = pd.DataFrame(rows, columns=["reason", "column", "values"])
print(f"{A.size:,} values compared; {int(changed.values.sum()):,} changed (beyond rounding)")
print(d.groupby("reason")["values"].sum().to_string())
if bad:
    print("\nUNEXPLAINED changes (column, values, first rows):")
    for b in bad[:30]:
        print(" ", b)

# ---- report: listed countries, Full US exit, no response, sudden cut ----
def k(iso, preset="Full US exit"):
    return f"{iso}|{preset}|none|Sudden (default)"


rep = []
for iso, name in COUNTRIES.items():
    r = {"Country": name}
    for l, lab in (("mal_cm", "Treatment"), ("mal_itn", "Bednets"), ("mal_irs", "Spraying")):
        r[f"{lab} cov"] = f"{num(A.loc[k(iso), f'L.{l}.cov0']):.0%} -> {num(B.loc[k(iso), f'L.{l}.cov0']):.0%}"
        r[f"{lab} deaths"] = f"{num(A.loc[k(iso), f'L.{l}.deaths_5y']):,.0f} -> {num(B.loc[k(iso), f'L.{l}.deaths_5y']):,.0f}"
    r["Malaria deaths"] = f"{num(A.loc[k(iso), 'B.Malaria.deaths_5y']):,.0f} -> {num(B.loc[k(iso), 'B.Malaria.deaths_5y']):,.0f}"
    r["All deaths"] = f"{num(A.loc[k(iso), 'T.deaths_5y']):,.0f} -> {num(B.loc[k(iso), 'T.deaths_5y']):,.0f}"
    r["Card deaths per $1M"] = f"{A.loc[k(iso), 'card.Malaria.deaths']} -> {B.loc[k(iso), 'card.Malaria.deaths']}"
    rep.append(r)
pd.set_option("display.width", 250)
print("\nFull US exit, no response, sudden cut (deaths 2026-2030):")
print(pd.DataFrame(rep).set_index("Country").to_string())

print("\nAll Countries, per preset (default settings):")
pre = []
for key in [x for x in A.index if x.startswith("ALL|")]:
    pre.append({"Preset": key.split("|")[1],
                "Malaria deaths before": num(A.loc[key, "sum.deaths_5y_Malaria"]),
                "Malaria deaths after": num(B.loc[key, "sum.deaths_5y_Malaria"]),
                "All deaths before": num(A.loc[key, "sum.deaths_5y"]),
                "All deaths after": num(B.loc[key, "sum.deaths_5y"])})
pre = pd.DataFrame(pre).set_index("Preset")
pre["Malaria change"] = (pre["Malaria deaths after"] / pre["Malaria deaths before"] - 1).map(lambda v: f"{v:+.1%}")
print(pre.round(0).to_string())
sys.exit(1 if bad else 0)
