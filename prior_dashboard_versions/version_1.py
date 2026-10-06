import io
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
COUNTRY = "Kenya"
FLAG = "🇰🇪"
FISCAL_YEAR = "FY2026/27"
DEFAULT_CSV = Path(__file__).parent / "kenya_health_data.csv"

REQUIRED_COLUMNS = {"section", "name", "detail", "value"}
PROFILE_KEYS = ["population_m", "gdp_kes_bn", "gov_revenue_kes_bn", "gov_spending_kes_bn"]

SOURCE_COLORS = {
    "Government": "#183B56",
    "Gavi": "#F4B942",
    "Global Fund": "#D94F4F",
    "US": "#2C7BE5",
}
FALLBACK_COLORS = ["#7B61FF", "#20A4A4", "#C2185B", "#8D6E63"]

# (text colour, card background) cycled across scenarios in CSV order
SCENARIO_PALETTE = [
    ("#B42318", "#FFF5F5"),
    ("#B54708", "#FFF8ED"),
    ("#087443", "#F0FAF5"),
]

st.set_page_config(
    page_title=f"{COUNTRY} Health Financing Dashboard",
    page_icon=FLAG,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Streamlit >=1.50 uses width="stretch"; older versions (e.g. 1.37) use use_container_width.
_ST_VERSION = tuple(int(p) for p in st.__version__.split(".")[:2])
WIDTH_KW = {"width": "stretch"} if _ST_VERSION >= (1, 50) else {"use_container_width": True}


def html(s: str) -> None:
    """Render HTML. Lines are stripped and joined so Markdown never
    mistakes indented HTML for a code block."""
    st.markdown("".join(line.strip() for line in s.splitlines()), unsafe_allow_html=True)


def fmt_money(bn: float) -> str:
    """Format a US$-billion amount as $1.23B, or $123M when under a billion."""
    return f"${bn:,.2f}B" if abs(bn) >= 1 else f"${bn * 1000:,.0f}M"


# ---------------------------------------------------------
# STYLING
# ---------------------------------------------------------
html("""
<style>
.stApp { background: #F7F9FC; color: #172033; }
.block-container { padding-top: 1.2rem; padding-bottom: 1rem; max-width: 1500px; }
.country-header { text-align: center; margin-bottom: 18px; }
.country-header h1 { font-size: 42px; margin: 0; font-weight: 750; letter-spacing: -1px; }
.flag { font-size: 42px; vertical-align: middle; margin-left: 12px; }
.metric-label { color: #68758A; font-size: 12px; font-weight: 700;
                text-transform: uppercase; letter-spacing: .05em; }
.metric-value { color: #172033; font-size: 27px; font-weight: 750; margin-top: 3px; }
.metric-sub { color: #7C8798; font-size: 12px; margin-top: 2px; margin-bottom: 14px; }
.section-title { font-size: 21px; font-weight: 720; margin: 18px 0 10px 0; }
.source-note { color: #6B7688; font-size: 11px; line-height: 1.4; margin-top: 12px; }
</style>
""")


def stat(label, value, sub="", color="#172033", size=27):
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else '<div style="height:10px"></div>'
    return (
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value" style="color:{color};font-size:{size}px">{value}</div>'
        f"{sub_html}"
    )


# ---------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data(raw: bytes) -> dict:
    """Parse the long-format CSV (section, name, detail, value[, source]).

    Money in the CSV is in KES billions; everything is converted to
    US$ billions here using the `kes_per_usd` assumption."""
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing column(s): {', '.join(sorted(missing))}")

    for c in ("section", "name", "detail"):
        df[c] = df[c].fillna("").astype(str).str.strip()
    if "source" not in df.columns:
        df["source"] = ""
    df["source"] = df["source"].fillna("").astype(str).str.strip()
    df["section"] = df["section"].str.lower()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    bad = df[df["value"].isna()]
    if not bad.empty:
        rows = ", ".join(str(i + 2) for i in bad.index)  # +2 = header row + 1-indexing
        raise ValueError(f"Non-numeric or empty 'value' on CSV row(s): {rows}")

    def section(name):
        return df[df["section"] == name]

    # Assumptions + FX
    assumptions = section("assumption").set_index("name")["value"].to_dict()
    fx = assumptions.get("kes_per_usd", 0)
    if fx <= 0:
        raise ValueError("Add an assumption row named 'kes_per_usd' (KES per US$)")

    # Profile
    p = section("profile").set_index("name")["value"].to_dict()
    missing_keys = [k for k in PROFILE_KEYS if k not in p]
    if missing_keys:
        raise ValueError(f"Missing profile row(s): {', '.join(missing_keys)}")
    profile = {
        "population_m": p["population_m"],
        "gdp_usd_bn": p["gdp_kes_bn"] / fx,
        "gov_revenue_usd_bn": p["gov_revenue_kes_bn"] / fx,
        "gov_spending_usd_bn": p["gov_spending_kes_bn"] / fx,
    }

    # Government spending by category
    gov = section("gov_spending").groupby("name", sort=False)["value"].sum() / fx
    if gov.empty or "Health" not in gov.index:
        raise ValueError("gov_spending section needs at least a 'Health' row")

    # Health funding: programme x source
    hf = section("health_funding")
    if hf.empty or "Government" not in set(hf["detail"]):
        raise ValueError("health_funding section needs rows with detail = 'Government'")
    programmes = hf["name"].drop_duplicates().tolist()
    sources = hf["detail"].drop_duplicates().tolist()
    sources = ["Government"] + [s for s in sources if s != "Government"]
    funding = (
        hf.pivot_table(index="name", columns="detail", values="value", aggfunc="sum", fill_value=0)
        .reindex(programmes)
        .reindex(columns=sources, fill_value=0)
    ) / fx

    # Which sources sit inside the government health budget (vs off-budget)
    ob = section("on_budget")
    on_budget = ob.loc[ob["value"] > 0, "name"].tolist() if not ob.empty else sources
    on_budget = [s for s in on_budget if s in sources]

    # Scenarios (mortality_factor is optional and defaults to 1.0)
    sc = section("scenario")
    scen_order = sc["name"].drop_duplicates().tolist()
    scenarios = sc.pivot_table(index="name", columns="detail", values="value", aggfunc="first").reindex(scen_order)
    if "funding_cut" not in scenarios.columns or scenarios["funding_cut"].isna().any():
        raise ValueError("Every scenario needs a 'funding_cut' row")

    notes = df[df["source"] != ""][["section", "name", "detail", "value", "source"]].reset_index(drop=True)

    return {
        "profile": profile,
        "gov": gov,
        "funding": funding,
        "on_budget": on_budget,
        "scenarios": scenarios,
        "assumptions": assumptions,
        "notes": notes,
    }


# ---------------------------------------------------------
# SCENARIO MODEL
# ---------------------------------------------------------
def run_scenario(cut, mortality_factor, exposed_annual, years, new_financing, lives_per_bn):
    funding_loss = exposed_annual * years * cut
    financing_gap = max(funding_loss - new_financing, 0.0)
    surplus = max(new_financing - funding_loss, 0.0)
    share_offset = 1.0 if funding_loss <= 0 else min(new_financing / funding_loss, 1.0)

    gross_lives = funding_loss * lives_per_bn * mortality_factor
    lives_saved = gross_lives * share_offset
    return {
        "funding_loss": funding_loss,
        "new_financing": new_financing,
        "financing_gap": financing_gap,
        "surplus": surplus,
        "share_offset": share_offset,
        "gross_lives_at_risk": gross_lives,
        "lives_saved": lives_saved,
        "lives_at_risk": gross_lives - lives_saved,
    }


# ---------------------------------------------------------
# HEADER + DATA SOURCE
# ---------------------------------------------------------
html(f"""
<div class="country-header">
<h1>{COUNTRY} <span class="flag">{FLAG}</span></h1>
<div style="color:#68758A; font-size:14px;">Health financing &amp; funding scenarios · {FISCAL_YEAR} budget · figures in US$</div>
</div>
""")

with st.expander("Data source", expanded=False):
    uploaded = st.file_uploader(
        "Upload a CSV to replace the default data (columns: section, name, detail, value, source)",
        type="csv",
    )

if uploaded is not None:
    raw, source_label = uploaded.getvalue(), uploaded.name
elif DEFAULT_CSV.exists():
    raw, source_label = DEFAULT_CSV.read_bytes(), DEFAULT_CSV.name
else:
    st.error(f"No data found. Put `{DEFAULT_CSV.name}` next to this script or upload a CSV above.")
    st.stop()

try:
    data = load_data(raw)
except Exception as e:  # show a readable message instead of a traceback
    st.error(f"Could not read **{source_label}**: {e}")
    st.stop()

profile = data["profile"]
gov = data["gov"]
funding = data["funding"]
on_budget = data["on_budget"]
scenarios = data["scenarios"]
assumptions = data["assumptions"]

POP = profile["population_m"]
GDP = profile["gdp_usd_bn"]
REVENUE = profile["gov_revenue_usd_bn"]
SPENDING = profile["gov_spending_usd_bn"]
FX = assumptions["kes_per_usd"]
YEARS = int(assumptions.get("horizon_years", 5))
DEFAULT_LIVES_PER_BN = int(assumptions.get("lives_per_usd_bn", 12000))
DEFAULT_COFINANCING = float(assumptions.get("kenya_cofinancing_usd_bn", 0.0))

external_sources = [c for c in funding.columns if c != "Government"]
total_health = funding.to_numpy().sum()
on_budget_health = funding[on_budget].to_numpy().sum()
external_total = total_health - funding["Government"].sum()

# Consistency checks between the CSV sections
if abs(gov.sum() - SPENDING) > 0.05:
    st.warning(
        f"Spending categories sum to ${gov.sum():.2f}B but the profile total is ${SPENDING:.2f}B."
    )
if abs(gov["Health"] - on_budget_health) > 0.05:
    st.warning(
        f"Health line in gov_spending (${gov['Health']:.2f}B) doesn't match the sum of on-budget "
        f"health_funding sources ({', '.join(on_budget)}): ${on_budget_health:.2f}B."
    )

with st.expander("Sources & notes for every figure"):
    st.caption(
        f"Money in the CSV is in KES billions; the dashboard converts at {FX:g} KES per US$. "
        "Rows marked DERIVED are calculated, not quoted."
    )
    st.dataframe(data["notes"], hide_index=True, **WIDTH_KW)


# ---------------------------------------------------------
# TOP: PROFILE + THREE CHARTS
# ---------------------------------------------------------
left, right = st.columns([0.28, 0.72], gap="large")

with left:
    with st.container(border=True):
        html('<div class="section-title" style="margin-top:0">Country profile</div>')
        html(
            stat("Population", f"{POP:,.1f}M", "mid-2026 (KNBS)")
            + stat("GDP", f"${GDP:,.1f}B", "nominal, calendar 2025")
            + stat("Government revenue", f"${REVENUE:,.1f}B", f"{FISCAL_YEAR} budget")
            + stat("Government spending", f"${SPENDING:,.1f}B", f"{FISCAL_YEAR} budget")
        )

with right:
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=("Revenue vs spending", "Government spending", "Health financing by programme"),
        horizontal_spacing=0.14,
    )

    fig.add_trace(
        go.Bar(
            x=["Revenue", "Spending"],
            y=[REVENUE, SPENDING],
            marker_color=["#173F5F", "#8EA8BD"],
            text=[f"${REVENUE:.1f}B", f"${SPENDING:.1f}B"],
            textposition="auto",
            hovertemplate="%{x}: $%{y:.2f}B<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=gov.values,
            y=gov.index,
            orientation="h",
            marker_color=["#1B6CA8" if n == "Health" else "#8EA8BD" for n in gov.index],
            hovertemplate="%{y}: $%{x:.2f}B<extra></extra>",
        ),
        row=1,
        col=2,
    )

    health_by_programme = funding.sum(axis=1) * 1000  # US$ millions
    fig.add_trace(
        go.Bar(
            x=health_by_programme.values,
            y=health_by_programme.index,
            orientation="h",
            marker_color="#28A77A",
            hovertemplate="%{y}: $%{x:,.0f}M<extra></extra>",
        ),
        row=1,
        col=3,
    )

    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        font=dict(family="Arial", color="#172033"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_xaxes(title_text="US$ B", row=1, col=1)
    fig.update_xaxes(title_text="US$ B", row=1, col=2)
    fig.update_xaxes(title_text="US$ M", row=1, col=3)
    fig.update_yaxes(showgrid=False, zeroline=False, automargin=True)
    fig.update_yaxes(autorange="reversed", row=1, col=2)  # keep CSV order, top to bottom
    fig.update_yaxes(autorange="reversed", row=1, col=3)
    st.plotly_chart(fig, **WIDTH_KW)


# ---------------------------------------------------------
# DERIVED KPIs (all computed from the CSV)
# ---------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
kpis = [
    (k1, "Health % of gov. spending", f"{gov['Health'] / SPENDING:.1%}", "national health vote ÷ total budget"),
    (k2, "Total health financing", fmt_money(total_health), "all sources, per year"),
    (k3, "Health financing % of GDP", f"{total_health / GDP:.1%}", "excludes county & private spending"),
    (k4, "External share of health", f"{external_total / total_health:.1%}", ", ".join(external_sources) or "none"),
    (k5, "Health spend per person", f"${total_health * 1000 / POP:,.0f}", "per year, all sources"),
]
for col, label, value, sub in kpis:
    with col:
        with st.container(border=True):
            html(stat(label, value, sub, size=24))


# ---------------------------------------------------------
# FUNDING BY PROGRAMME & SOURCE
# ---------------------------------------------------------
html('<div class="section-title">Health financing by programme &amp; funding source</div>')

fig_sources = go.Figure()
fallback = iter(FALLBACK_COLORS)
for src in funding.columns:
    fig_sources.add_trace(
        go.Bar(
            y=funding.index,
            x=funding[src] * 1000,
            name=src,
            orientation="h",
            marker_color=SOURCE_COLORS.get(src) or next(fallback, "#999999"),
            hovertemplate=f"{src}: $%{{x:,.0f}}M<extra></extra>",
        )
    )
fig_sources.update_layout(
    barmode="stack",
    height=420,
    margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor="white",
    plot_bgcolor="white",
    legend=dict(orientation="h", y=1.08, x=0),
    xaxis_title="US$ millions per year",
    font=dict(family="Arial", color="#172033"),
)
fig_sources.update_xaxes(showgrid=True, gridcolor="#EEF1F5")
fig_sources.update_yaxes(showgrid=False, autorange="reversed", automargin=True)
st.plotly_chart(fig_sources, **WIDTH_KW)


# ---------------------------------------------------------
# SCENARIOS: CONTROLS
# ---------------------------------------------------------
html(f'<div class="section-title">{YEARS}-year funding scenarios</div>')
st.markdown(
    "Adjust the levers below. Every number is recalculated from the CSV inputs and these "
    "controls. Outputs are scenario estimates built on a global lives-per-$ assumption, "
    "not Kenya-specific forecasts."
)

control_col, scenario_col = st.columns([0.28, 0.72], gap="large")

with control_col:
    with st.container(border=True):
        st.markdown("### Financing levers")

        additional_health = st.slider(
            f"Additional government health allocation ($B over {YEARS} yrs)",
            0.0,
            max(3.0, round(DEFAULT_COFINANCING * 2, 1)),
            float(DEFAULT_COFINANCING),
            0.05,
            format="%.2f",
            help="Default is Kenya's pledged ~$850M extra domestic health spending under the US framework.",
        )
        tax_increase = st.slider(
            f"Increase in government revenue ($B over {YEARS} yrs)",
            0.0, 5.0, 0.0, 0.1, format="%.1f",
        )
        health_share = st.slider("Health share of additional revenue", 0, 100, 10, 5, format="%d%%")

        st.markdown("---")
        st.markdown("**Which funding is being cut?**")
        cut_sources = st.multiselect(
            "Funding sources subject to the cut",
            options=list(funding.columns),
            default=external_sources,
            label_visibility="collapsed",
        )

        st.markdown("**Model assumption**")
        lives_per_bn = st.number_input(
            "Lives affected per $1B",
            min_value=0,
            value=DEFAULT_LIVES_PER_BN,
            step=1000,
        )
        html(
            '<div class="source-note">Default derived from Stover et al. (2025, Lancet Global Health): '
            "global deaths if US health funding ended, per $ of US funding. It is an average across "
            "many countries and programmes, so treat results as an order of magnitude.</div>"
        )

# ---------------------------------------------------------
# SCENARIOS: CALCULATION
# ---------------------------------------------------------
new_financing = additional_health + tax_increase * (health_share / 100)
exposed_by_programme = funding[cut_sources].sum(axis=1) if cut_sources else pd.Series(0.0, index=funding.index)
exposed_annual = float(exposed_by_programme.sum())


def mortality_factor_of(row):
    v = row.get("mortality_factor", 1.0)
    return 1.0 if pd.isna(v) else float(v)


results = {
    name: run_scenario(
        cut=row["funding_cut"],
        mortality_factor=mortality_factor_of(row),
        exposed_annual=exposed_annual,
        years=YEARS,
        new_financing=new_financing,
        lives_per_bn=lives_per_bn,
    )
    for name, row in scenarios.iterrows()
}

# ---------------------------------------------------------
# SCENARIO CARDS
# ---------------------------------------------------------
with scenario_col:
    if exposed_annual == 0:
        st.info("No funding is exposed: select at least one source to cut in the controls.")

    cols = st.columns(len(results), gap="medium")
    for i, (col, (name, r)) in enumerate(zip(cols, results.items())):
        color, bg = SCENARIO_PALETTE[i % len(SCENARIO_PALETTE)]
        with col:
            with st.container(border=True):
                html(f"""
                <div style="background:{bg}; border-radius:10px; padding:12px 14px; margin-bottom:12px;">
                <div style="font-size:20px; font-weight:800; color:#172033; margin-bottom:8px;">{name}</div>
                <div class="metric-label">Funding cut</div>
                <div style="color:{color}; font-size:30px; font-weight:800;">{scenarios.loc[name, 'funding_cut']:.0%}</div>
                <div class="metric-sub" style="margin-bottom:0">{fmt_money(r['funding_loss'])} lost over {YEARS} yrs</div>
                </div>
                """)
                html(stat("Lives at risk (remaining)", f"{r['lives_at_risk']:,.0f}", color="#B42318", size=28))
                html(stat("Lives saved via new financing", f"{r['lives_saved']:,.0f}", color="#087443", size=28))
                html('<div class="metric-label">Share of loss offset</div>')
                st.progress(r["share_offset"], text=f"{r['share_offset']:.0%} offset")

                if r["financing_gap"] > 0:
                    html(f"""
                    <div style="background:#FFF4E5; border:1px solid #F3C46B; border-radius:10px;
                    padding:10px 14px; margin-top:8px;">
                    <div style="color:#8A5A00; font-size:10px; font-weight:800;
                    text-transform:uppercase; letter-spacing:.05em;">Remaining financing gap</div>
                    <div style="color:#7A4F00; font-size:24px; font-weight:800;">{fmt_money(r['financing_gap'])}</div>
                    </div>
                    """)
                else:
                    html(f"""
                    <div style="background:#ECFDF3; border:1px solid #A6F4C5; border-radius:10px;
                    padding:10px 14px; margin-top:8px;">
                    <div style="color:#067647; font-size:10px; font-weight:800;
                    text-transform:uppercase; letter-spacing:.05em;">Loss fully offset</div>
                    <div style="color:#067647; font-size:24px; font-weight:800;">+{fmt_money(r['surplus'])} surplus</div>
                    </div>
                    """)


# ---------------------------------------------------------
# SCENARIO COMPARISON
# ---------------------------------------------------------
html('<div class="section-title">Scenario comparison</div>')

names = list(results.keys())
bar_colors = [SCENARIO_PALETTE[i % len(SCENARIO_PALETTE)][0] for i in range(len(names))]

fig_cmp = make_subplots(
    rows=1,
    cols=3,
    subplot_titles=("Lives at risk", "Lives saved", "Share of funding loss offset"),
)
fig_cmp.add_trace(
    go.Bar(x=names, y=[results[n]["lives_at_risk"] for n in names], marker_color=bar_colors,
           hovertemplate="%{y:,.0f} lives<extra></extra>"),
    row=1, col=1,
)
fig_cmp.add_trace(
    go.Bar(x=names, y=[results[n]["lives_saved"] for n in names], marker_color="#087443",
           hovertemplate="%{y:,.0f} lives<extra></extra>"),
    row=1, col=2,
)
offsets = [results[n]["share_offset"] * 100 for n in names]
fig_cmp.add_trace(
    go.Bar(x=names, y=offsets, marker_color="#2C7BE5",
           text=[f"{x:.0f}%" for x in offsets], textposition="auto",
           hovertemplate="%{y:.0f}%<extra></extra>"),
    row=1, col=3,
)
fig_cmp.update_layout(
    height=360, showlegend=False, paper_bgcolor="white", plot_bgcolor="white",
    margin=dict(l=20, r=20, t=60, b=20), font=dict(family="Arial", color="#172033"),
)
fig_cmp.update_yaxes(showgrid=True, gridcolor="#EEF1F5")
fig_cmp.update_xaxes(showgrid=False)
st.plotly_chart(fig_cmp, **WIDTH_KW)


# ---------------------------------------------------------
# WHERE THE CUT LANDS (by programme)
# ---------------------------------------------------------
html('<div class="section-title">Where the cut lands, by programme</div>')
chosen = st.radio("Scenario", names, horizontal=True, label_visibility="collapsed")
cut = scenarios.loc[chosen, "funding_cut"]
mf = mortality_factor_of(scenarios.loc[chosen])

loss_bn = exposed_by_programme * YEARS * cut
prog = pd.DataFrame({
    "Annual funding exposed ($M)": exposed_by_programme * 1000,
    f"Funding lost over {YEARS} yrs ($M)": loss_bn * 1000,
    "Lives at risk (before offset)": loss_bn * lives_per_bn * mf,
})
loss_col = f"Funding lost over {YEARS} yrs ($M)"

p_left, p_right = st.columns([0.55, 0.45], gap="large")
with p_left:
    fig_p = go.Figure(
        go.Bar(
            x=prog[loss_col],
            y=prog.index,
            orientation="h",
            marker_color="#D94F4F",
            hovertemplate="%{y}: $%{x:,.0f}M<extra></extra>",
        )
    )
    fig_p.update_layout(
        height=360, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="white", plot_bgcolor="white",
        xaxis_title=f"US$ millions lost over {YEARS} years", font=dict(family="Arial", color="#172033"),
    )
    fig_p.update_xaxes(showgrid=True, gridcolor="#EEF1F5")
    fig_p.update_yaxes(showgrid=False, autorange="reversed", automargin=True)
    st.plotly_chart(fig_p, **WIDTH_KW)
with p_right:
    st.dataframe(
        prog.style.format({
            "Annual funding exposed ($M)": "{:,.0f}",
            loss_col: "{:,.0f}",
            "Lives at risk (before offset)": "{:,.0f}",
        }),
        **WIDTH_KW,
        height=360,
    )

# Export
summary = pd.DataFrame(results).T
summary.index.name = "scenario"
st.download_button(
    "Download scenario results (CSV, US$ billions)",
    summary.round(4).to_csv().encode("utf-8"),
    file_name="scenario_results.csv",
    mime="text/csv",
)

html(f"""
<div class="source-note">
<b>Interpretation:</b> Inputs are read from <code>{source_label}</code> (KES converted at {FX:g} per US$).
Funding lost = annual funding from the selected sources × {YEARS} years × cut %. New financing =
additional government allocation + (revenue increase × health share). Lives at risk = funding lost ×
lives per $1B, reduced in proportion to the share of the loss offset. The health figures cover
national-level budget and donor funding only; county-government and private health spending are
excluded. These are illustrative model outputs, not forecasts.
</div>
""")