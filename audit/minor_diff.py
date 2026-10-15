"""
Diff audit/before_minor.csv against audit/after_minor.csv (made by snapshot_numbers.py) and attribute every changed
number to I-13, I-14 or I-15, or flag it. Run from the repo root:

    .venv/bin/python audit/minor_diff.py

Writes audit/minor_diff_summary.csv (one row per changed value, with the reason; large, gitignored) and
audit/minor_diff_counts.csv (changes by reason x preset x response), and prints a summary.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
A = pd.read_csv(ROOT / "audit" / "before_minor.csv", index_col="key", low_memory=False)
B = pd.read_csv(ROOT / "audit" / "after_minor.csv", index_col="key", low_memory=False)
assert list(A.index) == list(B.index), "row keys differ"
cols = A.columns.intersection(B.columns)
a, b = A[cols], B[cols]


def num(x):
    return pd.to_numeric(x, errors="coerce")


rows = []
# rows (country x preset x response x path) that include an aid rise, per the after run: any bucket has gains
gain_rows = set()
gcols = [c for c in B.columns if c == "T.gains"]
if gcols:
    gain_rows = set(B.index[num(B["T.gains"]).fillna(0) > 0])
I14_COLS = {c for c in cols if c.startswith("HB.") or c.startswith("F.ghes_pct_gov_spend") or c == "break_even"}
for key in a.index:
    ra, rb = a.loc[key], b.loc[key]
    same = (ra == rb) | (ra.isna() & rb.isna())
    for c in ra.index[~same.to_numpy()]:
        va, vb = ra[c], rb[c]
        fa, fb = num(pd.Series([va]))[0], num(pd.Series([vb]))[0]
        rel = abs(fb - fa) / max(1.0, abs(fa)) if np.isfinite(fa) and np.isfinite(fb) else np.inf
        parts = key.split("|")
        preset, resp = (parts[1], parts[2]) if len(parts) == 4 else (parts[1], "")
        tiny = np.isfinite(fa) and np.isfinite(fb) and (rel < 1e-9 or abs(fb - fa) < 1e-6)
        if c in I14_COLS:
            reason = "I-14: health share now World Bank latest year (one definition)"
        elif resp == "gradual":
            reason = "I-14: gradual budget money = points x (GHES 2023 / the new health share)"
        elif key in gain_rows or (key.startswith("ALL|IHME") and preset.startswith("IHME")):
            reason = "I-15: a line whose aid rises counts as no loss (was negative people / deaths)"
        elif tiny:
            reason = ("rounding (< 1e-9 relative or < 0.000001 absolute): yearly losses summed then averaged, and "
                      "people losing a service floored at 0 where the government replaces a line in full")
        else:
            reason = "UNEXPLAINED"
        rows.append({"key": key, "column": c, "before": va, "after": vb, "rel_change": rel, "reason": reason})
d = pd.DataFrame(rows)
d.to_csv(ROOT / "audit" / "minor_diff_summary.csv", index=False)          # every changed value (large; gitignored)
if len(d):                                                               # compact counts (committed)
    k = d["key"].str.split("|", expand=True)
    d.assign(preset=k[1], response=k[2].fillna("")).groupby(["reason", "preset", "response"]).agg(
        values=("column", "size"), runs=("key", "nunique"),
        max_abs_change=("rel_change", "max")).reset_index().to_csv(ROOT / "audit" / "minor_diff_counts.csv", index=False)
print(f"{a.size:,} values compared; {len(d):,} changed")
if len(d):
    print(d.groupby("reason").agg(values=("column", "size"), rows=("key", "nunique")).to_string())
    un = d[d.reason == "UNEXPLAINED"]
    if len(un):
        print("\nUNEXPLAINED changes:")
        print(un.head(30).to_string())
    sys.exit(1 if len(un) else 0)
