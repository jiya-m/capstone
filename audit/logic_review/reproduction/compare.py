"""
Compare the independent reproduction (independent.csv, built from docs/SPEC.md only) with the dashboard's own values
in an audit snapshot (audit/snapshot_numbers.py output). Flags any cell that differs by more than 0.5%.

    .venv/bin/python audit/logic_review/reproduction/compare.py audit/<snapshot>.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
CASES = {1: "{}|none|Sudden (default)", 2: "{}|custom25|Sudden (default)", 3: "{}|none|Sudden (default)",
         4: "{}|none|Linear phase-out"}


def main(snap_path, us="Full US exit", oecd="OECD-reported 2025 aid cuts"):
    snap = pd.read_csv(snap_path, low_memory=False).set_index("key")
    ind = pd.read_csv(HERE / "independent.csv")
    rows = []
    for _, r in ind.iterrows():
        iso, c = r.iloc[0].split("|")
        c = int(c)
        key = f"{iso}|" + CASES[c].format(oecd if c == 3 else us)
        s = snap.loc[key]
        for col in ind.columns[1:]:
            a, b = s.get(col, np.nan), r[col]
            if pd.isna(a) and pd.isna(b):
                continue
            a = float(a)
            rel = (b - a) / abs(a) if a else (0.0 if (pd.isna(b) or abs(b) < 1e-9) else np.inf)
            rows.append((iso, c, col, a, b, rel))
    d = pd.DataFrame(rows, columns=["iso", "case", "col", "dashboard", "independent", "rel"])
    d.to_csv(HERE / "compare.csv", index=False)
    bad = d[d["rel"].abs() > 0.005]
    print(f"{len(d)} cells compared; {len(d) - len(bad)} within 0.5%; largest |difference| "
          f"{d['rel'].abs().replace(np.inf, np.nan).max():.4%}")
    if len(bad):
        print(bad.to_string())
    return len(bad)


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
