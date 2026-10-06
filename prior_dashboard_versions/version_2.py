"""
Who funds health in each country?  (IHME Development Assistance for Health, 1990-2025)

Run:   streamlit run app.py
Data:  ./country_data/<Country>.csv   (created by prepare_data.py)
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Full-width kwarg differs by Streamlit version (older: use_container_width, 1.50+: width="stretch")
_ver = tuple(int(x) for x in st.__version__.split(".")[:2] if x.isdigit())
WIDE = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}

# --------------------------------------------------------------------------- #
# Settings you may want to edit
# --------------------------------------------------------------------------- #
DATA_DIR = Path(__file__).parent / "country_data"          # DAH, one file per recipient
SPEND_DIR = Path(__file__).parent / "spending_data"        # total spending, one file per ISO3
YEAR_MIN, YEAR_MAX = 2015, 2030          # chart 1 x-axis window, fixed (future years stay blank)
SPEND_YEAR_MIN, SPEND_YEAR_MAX = 2015, 2030   # chart 2 x-axis window, fixed
TOP_N_FUNDERS = 10                       # chart 1 shows this many funders individually, fixed
DEFAULT_COUNTRY = "Kenya"
HATCH_SHAPE = "+"                        # plotly pattern: "+" grid, "x" crosshatch, "/" diagonal

# Channels treated as "NGO / foundation" money. IHME does NOT record whether a
# recipient government knew about a flow -- channel is only a proxy. These are
# the defaults; the sidebar lets you change them live.
DEFAULT_NONGOV_CHANNELS = ["NGO", "INTLNGO", "US_FOUND", "GATES"]

CHANNEL_LABELS = {
    "NGO": "US NGOs", "INTLNGO": "International NGOs", "US_FOUND": "US foundations",
    "GATES": "Gates Foundation", "GAVI": "Gavi", "GFATM": "Global Fund", "CEPI": "CEPI",
    "WHO": "WHO", "PAHO": "PAHO", "UNICEF": "UNICEF", "UNFPA": "UNFPA", "UNAIDS": "UNAIDS",
    "UNITAID": "Unitaid", "WB_IDA": "World Bank (IDA)", "WB_IBRD": "World Bank (IBRD)",
    "WB": "World Bank", "AfDB": "African Development Bank", "AsDB": "Asian Development Bank",
    "IDB": "Inter-American Development Bank", "EC": "European Commission",
    "EEA": "European Economic Area", "BIL_USA": "US bilateral (USAID/State/etc.)",
}

HFA_LABELS = {
    "total": "Total health (all focus areas)",
    "hiv": "HIV/AIDS",
    "mal": "Malaria",
    "tb": "Tuberculosis",
    "rmh": "Reproductive & maternal health",
    "nch": "Newborn & child health",
    "oid": "Other infectious diseases",
    "ncd": "Non-communicable diseases",
    "swap_hss_total": "Health systems strengthening / SWAps",
    "other": "Other",
    "unalloc": "Unallocated",
}
HFAS_WITH_PROGRAM_AREAS = ["hiv", "mal", "tb", "rmh", "nch", "oid", "ncd", "swap_hss_total"]

PA_LABELS = {
    "treat": "Treatment", "prev": "Prevention", "pmtct": "Prevention of mother-to-child transmission",
    "ovc": "Orphans & vulnerable children", "care": "Care & support", "ct": "Counseling & testing",
    "amr": "Drug resistance", "diag": "Diagnosis", "con_nets": "Bednets", "con_irs": "Indoor spraying",
    "con_oth": "Other vector control", "comm_con": "Community outreach", "fp": "Family planning",
    "mh": "Maternal health", "cnn": "Nutrition", "cnv": "Vaccines", "ebz": "Ebola", "zika": "Zika",
    "covid": "COVID-19", "tobac": "Tobacco", "mental": "Mental health", "pp": "Pandemic preparedness",
    "hss_other": "HSS - other", "hss_hrh": "HSS - human resources", "hss_me": "HSS - ME",
    "hrh": "Human resources", "other": "Other",
}
NON_COUNTRY_ISO = {"WLD", "INKIND", "QZA"}

# Chart 2 components: (column prefix, label, colour). Stack order = bottom to top.
SPEND_PARTS = [
    ("ghes", "Government spending", "#1b6ca8"),
    ("ppp", "Prepaid private spending", "#7a5195"),
    ("oop", "Out-of-pocket spending", "#e08a1e"),
    ("dah", "Development assistance for health (DAH)", "#2a9d6f"),
]
SPEND_LAST_OBSERVED = 2023                 # 2024+ are IHME expected values

# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def load_countries() -> pd.DataFrame:
    """One row per selectable location, keyed by ISO3, with whichever files exist."""
    dah = load_index()[["recipient_country", "recipient_isocode", "file", "is_country"]]
    dah = dah.rename(columns={"recipient_isocode": "iso3", "file": "dah_file"})
    sp_path = SPEND_DIR / "_index.csv"
    sp = pd.read_csv(sp_path) if sp_path.exists() else pd.DataFrame(columns=["iso3", "location_name"])
    m = dah.merge(sp, on="iso3", how="outer")
    m["name"] = m["location_name"].fillna(m["recipient_country"])   # prefer the spending-file name
    m["is_country"] = m["is_country"].fillna(True).astype(bool)
    m["has_spend"] = m["location_name"].notna()
    m["label"] = m["name"] + m["is_country"].map({True: "", False: "  (non-country)"})
    return m.sort_values(["is_country", "name"], ascending=[False, True]).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_spending(iso3: str) -> pd.DataFrame:
    return pd.read_csv(SPEND_DIR / f"{iso3}.csv")


@st.cache_data(show_spinner=False)
def load_index() -> pd.DataFrame:
    idx_path = DATA_DIR / "_index.csv"
    if idx_path.exists():
        idx = pd.read_csv(idx_path)
    else:  # fall back to scanning the folder
        rows = []
        for f in sorted(DATA_DIR.glob("*.csv")):
            if f.name.startswith("_"):
                continue
            head = pd.read_csv(f, nrows=1, usecols=["recipient_country", "recipient_isocode"])
            rows.append({**head.iloc[0].to_dict(), "file": f.name})
        idx = pd.DataFrame(rows)
    idx["is_country"] = ~idx["recipient_isocode"].isin(NON_COUNTRY_ISO)
    idx["label"] = idx["recipient_country"] + idx["is_country"].map({True: "", False: "  (non-country)"})
    return idx.sort_values(["is_country", "recipient_country"], ascending=[False, True]).reset_index(drop=True)


@st.cache_data(show_spinner="Loading country spreadsheet...")
def load_country(file: str) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / file)
    df["source"] = df["source"].str.replace("_", " ").str.strip()
    return df


def program_area_options(df: pd.DataFrame, hfa: str) -> dict:
    # SWAp/HSS columns are named swap_hss_<area>_dah_23 (the category itself is swap_hss_total)
    prefix = "swap_hss_" if hfa == "swap_hss_total" else f"{hfa}_"
    opts = {}
    for c in df.columns:
        if c.startswith(prefix) and c.endswith("_dah_23") and c != f"{hfa}_dah_23":
            key = c[len(prefix):-len("_dah_23")]
            opts[c] = PA_LABELS.get(key, key)
    return dict(sorted(opts.items(), key=lambda kv: kv[1]))


def fmt_usd(m: float) -> str:
    """Format an amount given in US$ millions as $x.xM / $x.xB / $x.xT."""
    a = abs(m)
    if a >= 1e6:
        return f"${m / 1e6:,.1f}T"
    if a >= 1e3:
        return f"${m / 1e3:,.1f}B"
    return f"${m:,.1f}M"


def pick_unit(max_millions: float):
    """Choose axis unit for values given in US$ millions -> (divisor, word, suffix)."""
    if max_millions >= 1e6:
        return 1e6, "trillions", "T"
    if max_millions >= 1e3:
        return 1e3, "billions", "B"
    return 1.0, "millions", "M"


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# --------------------------------------------------------------------------- #
# Page
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="Health financing", page_icon="📊", layout="wide")
st.title("Health financing by country")
st.caption("IHME Development Assistance for Health (1990-2025) and Global Health Spending (1995-2023, "
           "expected 2024-2050). Constant 2023 US$.")

if not DATA_DIR.exists():
    st.error("No `country_data/` folder found. Run `python prepare_data.py <path to the IHME DAH CSV>` first.")
    st.stop()

if not SPEND_DIR.exists() or not (SPEND_DIR / "_index.csv").exists():
    st.warning(
        "Chart 2 (health spending) needs a `spending_data/` folder next to `app.py`, and it isn't there yet. "
        "Copy the folder in, or build it with `python prepare_spending.py <HEALTH_SPENDING_1995_2023 .CSV> "
        "<EXPECTED_HEALTH_SPENDING_2024_2050 .CSV>`, then reload."
    )

countries = load_countries()

# ---- general control: country only, centred ------------------------------- #
_, mid, _ = st.columns([1, 2, 1])
with mid:
    default_i = int(countries.index[countries["name"] == DEFAULT_COUNTRY][0]) if (countries["name"] == DEFAULT_COUNTRY).any() else 0
    country_label = st.selectbox("Country", countries["label"], index=default_i)
crow = countries[countries["label"] == country_label].iloc[0]
country_name = crow["name"]

st.divider()

# =========================================================================== #
# CHART 1 - who funds health (DAH)
# =========================================================================== #
st.header(f"1. Who funds health aid in {country_name}?")

if pd.isna(crow["dah_file"]):
    st.info(f"{country_name} is not a recipient in the IHME DAH database (typically a high-income country), "
            "so there is no aid-funder breakdown to show.")
else:
    df = load_country(crow["dah_file"])
    c1, c2 = st.columns(2)
    with c1:
        hfa = st.selectbox("Health category", list(HFA_LABELS), format_func=HFA_LABELS.get, key="c1_hfa")
    value_col, metric_label = "dah_23", HFA_LABELS["total"]
    if hfa != "total":
        value_col, metric_label = f"{hfa}_dah_23", HFA_LABELS[hfa]
        pas = program_area_options(df, hfa) if hfa in HFAS_WITH_PROGRAM_AREAS else {}
        if pas:
            with c2:
                pa = st.selectbox("Program area", ["All program areas"] + list(pas),
                                  format_func=lambda k: k if k == "All program areas" else pas[k],
                                  key=f"c1_pa_{hfa}")
            if pa != "All program areas":
                value_col, metric_label = pa, f"{HFA_LABELS[hfa]}: {pas[pa]}"
    nongov = st.multiselect(
        "Funneled indirectly (checkered)",
        options=list(CHANNEL_LABELS), default=DEFAULT_NONGOV_CHANNELS, key="c1_ngo",
        format_func=lambda c: f"{CHANNEL_LABELS[c]} ({c})",
        help="IHME doesn't record whether a government knew about a flow. "
             "The channel that delivered the money is used as a proxy.",
    )

    d = df[["year", "source", "channel", value_col]].rename(columns={value_col: "val"})
    d["val"] = d["val"] / 1e3                       # thousands of US$ -> millions of US$
    d["route"] = d["channel"].isin(nongov).map({True: "ngo", False: "gov"})
    last_data_year = int(df.loc[df["dah_23"] != 0, "year"].max()) if (df["dah_23"] != 0).any() else YEAR_MIN

    window = d[(d["year"] >= YEAR_MIN) & (d["year"] <= YEAR_MAX)]
    ranked = window.groupby("source")["val"].sum().sort_values(ascending=False)
    ranked = ranked[ranked > 0]
    top = list(ranked.index[:TOP_N_FUNDERS])
    window = window.assign(source=window["source"].where(window["source"].isin(top), "All other sources"))
    agg = window.groupby(["year", "source", "route"], as_index=False)["val"].sum()
    # which organizations the checkered money went through, per bar (for hover text)
    ngo_detail = (window[window["route"] == "ngo"].groupby(["year", "source", "channel"])["val"].sum().reset_index())
    ngo_detail = ngo_detail[ngo_detail["val"] > 0]
    ngo_detail["txt"] = ngo_detail["channel"].map(lambda c: CHANNEL_LABELS.get(c, c)) + ": " + ngo_detail["val"].map(fmt_usd)
    ngo_hover = ngo_detail.groupby(["year", "source"])["txt"].apply("<br>".join).to_dict()
    # axis unit adapts to size (millions / billions / trillions)
    unit_div, unit_name, unit_sfx = pick_unit(agg.groupby("year")["val"].sum().max() if len(agg) else 0)
    agg["val"] = agg["val"] / unit_div
    order = top + (["All other sources"] if (agg["source"] == "All other sources").any() else [])

    palette = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b", "#e377c2",
               "#17becf", "#bcbd22", "#393b79", "#637939", "#843c39", "#7b4173", "#3182bd", "#e6550d"]
    colors = {s: palette[i % len(palette)] for i, s in enumerate(top)}
    colors["All other sources"] = "#9aa0a6"

    st.subheader(f"{country_name} - {metric_label}")
    latest = d[d["year"] == last_data_year]
    tot = latest["val"].sum()
    if tot > 0:
        ngo_share = latest.loc[latest["route"] == "ngo", "val"].sum() / tot
        top_src = latest.groupby("source")["val"].sum().idxmax()
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Total in {last_data_year}", fmt_usd(tot))
        m2.metric(f"Funneled indirectly, {last_data_year}", f"{ngo_share:.0%}")
        m3.metric(f"Largest funder, {last_data_year}", top_src)
    else:
        st.info("No funding recorded for this selection.")

    fig = go.Figure()
    for s in order:
        col = colors[s]
        for route in ("gov", "ngo"):
            sub = agg[(agg["source"] == s) & (agg["route"] == route)]
            if sub.empty:
                continue
            marker = dict(color=col, line=dict(color=col, width=0.5))
            if route == "ngo":
                marker = dict(
                    color=hex_to_rgba(col, 0.25), line=dict(color=col, width=0.8),
                    pattern=dict(shape=HATCH_SHAPE, fgcolor=col, bgcolor=hex_to_rgba(col, 0.15), size=7, solidity=0.55),
                )
            if route == "ngo":
                custom = [ngo_hover.get((y, s), "") for y in sub["year"]]
                hover = (f"<b>{s}</b><br>Funneled through:<br>%{{customdata}}<br>%{{x}} total: $%{{y:,.1f}}{unit_sfx}<extra></extra>")
            else:
                custom = None
                hover = f"<b>{s}</b><br>Government-facing channel<br>%{{x}}: $%{{y:,.1f}}{unit_sfx}<extra></extra>"
            fig.add_bar(
                x=sub["year"], y=sub["val"], name=s, legendgroup=s,
                showlegend=(route == "gov" or not ((agg["source"] == s) & (agg["route"] == "gov")).any()),
                marker=marker, customdata=custom, hovertemplate=hover,
            )
    fig.add_bar(x=[None], y=[None], name="Solid: government-facing channels", legendgroup="_key1",
                marker=dict(color="#555"), hoverinfo="skip")
    for ch in nongov:
        fig.add_bar(x=[None], y=[None], name=f"Checkered: via {CHANNEL_LABELS.get(ch, ch)}", legendgroup=f"_key_{ch}",
                    marker=dict(color="rgba(85,85,85,0.25)", line=dict(color="#555", width=0.8),
                                pattern=dict(shape=HATCH_SHAPE, fgcolor="#555", bgcolor="rgba(85,85,85,0.15)", size=7, solidity=0.55)),
                    hoverinfo="skip")
    if last_data_year < YEAR_MAX:
        fig.add_vrect(x0=last_data_year + 0.5, x1=YEAR_MAX + 0.5, fillcolor="rgba(128,128,128,0.10)", line_width=0,
                      annotation_text="no data yet (forecast to come)", annotation_position="top left",
                      annotation_font=dict(size=12, color="gray"))
    fig.update_layout(
        barmode="stack", height=560, margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(range=[YEAR_MIN - 0.5, YEAR_MAX + 0.5], dtick=1, tickangle=-45, title=""),
        yaxis=dict(title=f"US$ {unit_name} (constant 2023)", rangemode="tozero"),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01),
        bargap=0.15, hovermode="closest",
    )
    st.plotly_chart(fig, **WIDE)

    if crow["is_country"] and last_data_year < 2024:
        st.caption(f"IHME's recipient-level aid data ends in {last_data_year}: 2024-2025 estimates exist only as "
                   "unallocated totals with no country attached, so they can't be shown here.")
    st.caption(
        "**Reading the chart:** colour = who the money originally came from (source). Checkered = delivered through "
        "NGO/foundation channels, a *proxy* for flows that may bypass the recipient government. IHME does not record "
        "government awareness directly, and some government-facing channels (e.g. bilateral agencies, the Global Fund) "
        "also fund NGOs on the ground."
    )

st.divider()

# =========================================================================== #
# CHART 2 - total health spending by source: past vs expected
# =========================================================================== #
st.header(f"2. Total health spending in {country_name}: past and expected")

if not crow["has_spend"] or not (SPEND_DIR / f"{crow['iso3']}.csv").exists():
    st.info(f"{country_name} isn't in the IHME health-spending dataset (it covers 204 countries and territories), "
            "so there is no spending breakdown to show.")
else:
    sp = load_spending(crow["iso3"])
    if True:
        view = st.radio("Show as", ["US$ total", "US$ per person", "Share of total (%)"],
                        horizontal=True, key="c2_view")
        y0, y1 = SPEND_YEAR_MIN, SPEND_YEAR_MAX

    w = sp[(sp["year"] >= y0) & (sp["year"] <= y1)].copy()
    sfx2 = ""
    if view == "US$ total":
        for k, _, _ in SPEND_PARTS:
            w[f"v_{k}"] = w[f"{k}_total_mean"] / 1e3
        _div, _name, sfx2 = pick_unit(w["the_total_mean"].max() / 1e3 if len(w) else 0)
        for k, _, _ in SPEND_PARTS:
            w[f"v_{k}"] = w[f"v_{k}"] / _div
        ylab = f"US$ {_name} (constant 2023)"
    elif view == "US$ per person":
        for k, _, _ in SPEND_PARTS:
            w[f"v_{k}"] = w[f"{k}_per_cap_mean"]
        ylab = "US$ per person (constant 2023)"
    else:
        for k, _, _ in SPEND_PARTS:
            w[f"v_{k}"] = 100 * w[f"{k}_total_mean"] / w["the_total_mean"]
        ylab = "% of total health spending"

    proj = w["projected"] == 1
    fig2 = go.Figure()
    for k, label, col in SPEND_PARTS:
        fig2.add_bar(
            x=w["year"], y=w[f"v_{k}"], name=label,
            marker=dict(color=col, line=dict(color=col, width=0.5), opacity=[0.55 if p else 1.0 for p in proj]),
            hovertemplate=(f"<b>{label}</b><br>%{{x}}: "
                           + ("%{y:,.1f}%" if view.startswith("Share")
                              else "$%{y:,.0f}" if view == "US$ per person"
                              else f"$%{{y:,.1f}}{sfx2}") + "<extra></extra>"),
        )
    if y1 > SPEND_LAST_OBSERVED:
        fig2.add_vrect(x0=max(y0, SPEND_LAST_OBSERVED + 1) - 0.5, x1=y1 + 0.5, fillcolor="rgba(128,128,128,0.10)",
                       line_width=0, annotation_text="IHME expected (projected)", annotation_position="top left",
                       annotation_font=dict(size=12, color="gray"))
    fig2.update_layout(
        barmode="stack", height=540, margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(range=[y0 - 0.5, y1 + 0.5], dtick=1, tickangle=-45, title=""),
        yaxis=dict(title=ylab, rangemode="tozero", **({"range": [0, 100]} if view.startswith("Share") else {})),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01),
        bargap=0.15, hovermode="closest",
    )
    st.plotly_chart(fig2, **WIDE)

    last_obs = sp[sp["year"] == SPEND_LAST_OBSERVED].iloc[0]
    end = sp[sp["year"] == min(y1, int(sp["year"].max()))].iloc[0]
    k1, k2, k3 = st.columns(3)
    k1.metric(f"Total spending, {SPEND_LAST_OBSERVED}", fmt_usd(last_obs['the_total_mean'] / 1e3))
    k2.metric(f"DAH share of total, {SPEND_LAST_OBSERVED}", f"{last_obs['dah_total_mean'] / last_obs['the_total_mean']:.0%}")
    k3.metric(f"DAH share of total, {int(end['year'])} (expected)" if end["year"] > SPEND_LAST_OBSERVED else f"DAH share, {int(end['year'])}",
              f"{end['dah_total_mean'] / end['the_total_mean']:.0%}")
    st.caption(
        "Solid bars are IHME's estimates through 2023; paler bars after 2023 are IHME's *expected* (projected) spending. "
        "Government, prepaid private and out-of-pocket are domestic sources; DAH is aid from abroad. The four parts add up "
        "to total health spending. DAH here comes from the spending dataset, so it can differ very slightly from the "
        "aid database used in chart 1."
    )