"""Tornado chart of the 20 most influential inputs (from sensitivity.csv). Needs plotly + kaleido (image export).

    .venv/bin/python audit/logic_review/tornado.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

HERE = Path(__file__).parent
d = pd.read_csv(HERE / "sensitivity.csv").head(20).iloc[::-1]
base = float(d["base_d5"].iloc[0])
lab = [f"{r.input}  [{r.low} / {r.high}]" for r in d.itertuples()]
fig = go.Figure()
fig.add_bar(y=lab, x=(d["d5_low"] - base) / 1e3, orientation="h", name="input at its low value", marker_color="#2e86c1")
fig.add_bar(y=lab, x=(d["d5_high"] - base) / 1e3, orientation="h", name="input at its high value", marker_color="#c0392b")
fig.update_layout(barmode="overlay", height=820, width=1250, template="simple_white",
                  title=f"All-country extra deaths 2026-2030 (Full US Exit, no government replacement): change from "
                        f"{base / 1e6:.2f}M when one input moves",
                  xaxis_title="change in deaths (thousands)", legend=dict(orientation="h", y=-0.08),
                  margin=dict(l=420, r=30, t=60, b=80), font=dict(size=12))
fig.add_vline(x=0, line_color="black")
fig.write_image(HERE / "tornado.png", scale=1.5)
print("saved tornado.png")
