import streamlit as st
import pandas as pd
import pyreadstat
import io
import tempfile
import os
import numpy as np
from datetime import datetime
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Survey Productivity Dashboard",
    page_icon="📋"
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Dark, industrial-utilitarian theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}
.stApp {
    background-color: #0d0f14;
    color: #e0e6f0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #111318;
    border-right: 1px solid #1e2230;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stFileUploader label,
[data-testid="stSidebar"] p {
    color: #8a9bc4 !important;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── Title ── */
.main-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: #e0e6f0;
    letter-spacing: -0.02em;
    border-bottom: 2px solid #2a6af5;
    padding-bottom: 0.4rem;
    margin-bottom: 0.2rem;
}
.main-subtitle {
    font-size: 0.78rem;
    color: #4a5a7a;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.05em;
    margin-bottom: 1.5rem;
}

/* ── Metric cards ── */
.metric-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #111318;
    border: 1px solid #1e2230;
    border-top: 2px solid #2a6af5;
    border-radius: 4px;
    padding: 1rem 1.2rem;
    flex: 1;
}
.metric-card .label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #4a5a7a;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.3rem;
}
.metric-card .value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: #2a6af5;
}
.metric-card .sub {
    font-size: 0.7rem;
    color: #4a5a7a;
    margin-top: 0.2rem;
}

/* ── Section headers ── */
.section-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #4a5a7a;
    border-bottom: 1px solid #1e2230;
    padding-bottom: 0.4rem;
    margin: 1.5rem 0 1rem 0;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1e2230;
    border-radius: 4px;
}

/* ── Alerts ── */
.warning-box {
    background: #1a1208;
    border-left: 3px solid #f5a623;
    padding: 0.6rem 1rem;
    border-radius: 0 4px 4px 0;
    font-size: 0.8rem;
    color: #f5a623;
    margin: 0.5rem 0;
    font-family: 'IBM Plex Mono', monospace;
}
.info-box {
    background: #0a1020;
    border-left: 3px solid #2a6af5;
    padding: 0.6rem 1rem;
    border-radius: 0 4px 4px 0;
    font-size: 0.8rem;
    color: #5a8af5;
    margin: 0.5rem 0;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Download button ── */
.stDownloadButton > button {
    background-color: #2a6af5;
    color: white;
    border: none;
    border-radius: 3px;
    padding: 0.5rem 1.4rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    transition: background 0.2s;
}
.stDownloadButton > button:hover {
    background-color: #1a5ae0;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #111318;
    border-bottom: 1px solid #1e2230;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4a5a7a;
    border-radius: 0;
    padding: 0.6rem 1.2rem;
}
.stTabs [aria-selected="true"] {
    color: #2a6af5 !important;
    border-bottom: 2px solid #2a6af5;
    background: transparent !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #4a5a7a !important;
    background: #111318;
    border: 1px solid #1e2230;
}

/* ── Slider ── */
.stSlider > div > div > div {
    background-color: #2a6af5;
}

/* ── Select & input ── */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background-color: #111318;
    border-color: #1e2230;
    color: #e0e6f0;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="main-title">Survey Productivity Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Enumerator performance tracking & quality control</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Data Source")
    uploaded_file = st.file_uploader("Upload File", type=["dta", "xlsx", "xls"])

    st.markdown("---")
    st.markdown("### 🗓 Date Format")
    header_style = st.selectbox(
        "Date Header Style",
        ["Pretty (e.g., 10 Sep 2025)", "Safe (e.g., d_10Sep2025)", "Compact (e.g., 10Sep2025)", "ISO (e.g., 2025-09-10)"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### ⚙️ Filters")
    date_range_filter = st.checkbox("Filter by date range", value=False)

    st.markdown("---")
    st.markdown("### 🚨 QC Thresholds")
    outlier_low = st.slider("Flag if daily count below", 0, 10, 2)
    outlier_high = st.slider("Flag if daily count above", 5, 100, 20)

if uploaded_file is None:
    st.markdown('<div class="info-box">⬅ Upload a .dta, .xlsx, or .xls file from the sidebar to get started.</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────
# READ FILE
# ─────────────────────────────────────────────
try:
    file_bytes = uploaded_file.read()
    if uploaded_file.name.lower().endswith(".dta"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dta") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        df, meta = pyreadstat.read_dta(tmp_path, apply_value_formats=True)
        os.unlink(tmp_path)
    else:
        df = pd.read_excel(io.BytesIO(file_bytes))
    with st.sidebar:
        st.success(f"✓ {len(df):,} rows loaded")
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

# ─────────────────────────────────────────────
# FIX COLUMN NAMES
# ─────────────────────────────────────────────
if isinstance(df.columns, pd.MultiIndex):
    df.columns = ["_".join(map(str, col)) for col in df.columns]
df.columns = [str(c).strip() for c in df.columns]

# ─────────────────────────────────────────────
# COLUMN SELECT
# ─────────────────────────────────────────────
col_options = ["Select a column"] + list(df.columns)

with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔗 Column Mapping")
    enum_col    = st.selectbox("Enumerator Column",          col_options, index=col_options.index("enum")      if "enum"      in col_options else 0)
    date_col    = st.selectbox("Date Column",                col_options, index=col_options.index("starttime") if "starttime" in col_options else 0)
    consent_col = st.selectbox("Consent Column (optional)",  col_options)
    addr1_col   = st.selectbox("Address Column 1 (optional)",col_options)
    addr2_col   = st.selectbox("Address Column 2 (optional)",col_options)
    uid_col     = st.selectbox("Unique ID Column (optional)", col_options)

if enum_col == "Select a column" or date_col == "Select a column":
    st.markdown('<div class="warning-box">⚠ Please map the Enumerator and Date columns in the sidebar.</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────
# RENAME & CLEAN
# ─────────────────────────────────────────────
rename_map = {enum_col: "enum", date_col: "date"}
if consent_col != "Select a column": rename_map[consent_col] = "consent"
if addr1_col   != "Select a column": rename_map[addr1_col]   = "addr1"
if addr2_col   != "Select a column": rename_map[addr2_col]   = "addr2"
if uid_col     != "Select a column": rename_map[uid_col]     = "uid"

df = df.rename(columns=rename_map)

# Date clean – handle timezone-aware datetimes
df["date"] = pd.to_datetime(df["date"], errors="coerce")
if hasattr(df["date"].dtype, "tz") and df["date"].dtype.tz is not None:
    df["date"] = df["date"].dt.tz_localize(None)
df = df.dropna(subset=["date"])
df["date"] = df["date"].dt.normalize()

def clean(x):
    return "Unknown" if pd.isna(x) else str(x).strip()

df["enum"] = df["enum"].apply(clean)
for c in ["addr1", "addr2"]:
    if c in df.columns:
        df[c] = df[c].apply(clean)

# Consent mapping
if "consent" in df.columns:
    def map_consent(x):
        x = str(x).lower().strip()
        return "Yes" if x in ["yes", "1", "true", "y"] else "No"
    df["Consent_Status"] = df["consent"].apply(map_consent)

# ─────────────────────────────────────────────
# DUPLICATE DETECTION
# ─────────────────────────────────────────────
duplicate_warnings = []
if "uid" in df.columns:
    dups = df[df.duplicated(subset=["uid"], keep=False)]
    if not dups.empty:
        dup_count = dups["uid"].nunique()
        duplicate_warnings.append(f"⚠ {dup_count} unique IDs appear more than once (possible duplicates).")

# ─────────────────────────────────────────────
# DATE RANGE FILTER
# ─────────────────────────────────────────────
min_date = df["date"].min().date()
max_date = df["date"].max().date()

if date_range_filter:
    with st.sidebar:
        st.markdown("**Date Range**")
        date_from = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
        date_to   = st.date_input("To",   value=max_date, min_value=min_date, max_value=max_date)
    df = df[(df["date"].dt.date >= date_from) & (df["date"].dt.date <= date_to)]
    if df.empty:
        st.warning("No data in selected date range.")
        st.stop()

# ─────────────────────────────────────────────
# ENUMERATOR FILTER
# ─────────────────────────────────────────────
with st.sidebar:
    all_enums = sorted(df["enum"].unique().tolist())
    selected_enums = st.multiselect("Filter Enumerators", all_enums, default=all_enums)

if selected_enums:
    df = df[df["enum"].isin(selected_enums)]
if df.empty:
    st.warning("No data after filtering.")
    st.stop()

# ─────────────────────────────────────────────
# SUMMARY STATS
# ─────────────────────────────────────────────
total_surveys   = len(df)
total_enums     = df["enum"].nunique()
total_days      = df["date"].nunique()
avg_per_day     = total_surveys / total_days if total_days > 0 else 0
consent_pct     = (df["Consent_Status"] == "Yes").mean() * 100 if "Consent_Status" in df.columns else None

# ─────────────────────────────────────────────
# METRIC CARDS
# ─────────────────────────────────────────────
metrics_html = f"""
<div class="metric-row">
    <div class="metric-card">
        <div class="label">Total Surveys</div>
        <div class="value">{total_surveys:,}</div>
        <div class="sub">{min_date.strftime('%d %b')} → {max_date.strftime('%d %b %Y')}</div>
    </div>
    <div class="metric-card">
        <div class="label">Enumerators</div>
        <div class="value">{total_enums}</div>
        <div class="sub">active in period</div>
    </div>
    <div class="metric-card">
        <div class="label">Field Days</div>
        <div class="value">{total_days}</div>
        <div class="sub">days with submissions</div>
    </div>
    <div class="metric-card">
        <div class="label">Avg / Day</div>
        <div class="value">{avg_per_day:.1f}</div>
        <div class="sub">surveys per day (all enumerators)</div>
    </div>
    {"<div class='metric-card'><div class='label'>Consent Rate</div><div class='value'>{:.1f}%</div><div class='sub'>respondents consented</div></div>".format(consent_pct) if consent_pct is not None else ""}
</div>
""" 
st.markdown(metrics_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DUPLICATE WARNINGS
# ─────────────────────────────────────────────
for w in duplicate_warnings:
    st.markdown(f'<div class="warning-box">{w}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# GROUP / COUNT / PIVOT
# ─────────────────────────────────────────────
group_cols = ["enum"]
if "addr1" in df.columns:         group_cols.append("addr1")
if "addr2" in df.columns:         group_cols.append("addr2")
if "Consent_Status" in df.columns: group_cols.append("Consent_Status")

daily = (
    df.groupby(group_cols + ["date"], dropna=False, observed=True)
    .size()
    .reset_index(name="count")
)

pivot = (
    daily.pivot_table(
        index=group_cols,
        columns="date",
        values="count",
        fill_value=0,
        aggfunc="sum",
        observed=True
    )
    .reset_index()
)

# ─────────────────────────────────────────────
# SAFE COLUMN NAMES
# ─────────────────────────────────────────────
new_cols, seen = [], {}
for col in pivot.columns:
    if isinstance(col, pd.Timestamp):
        base = "d_" + col.strftime("%d%b%Y")
    else:
        base = str(col)
    if base in seen:
        seen[base] += 1
        base = f"{base}_{seen[base]}"
    else:
        seen[base] = 0
    new_cols.append(base)
pivot.columns = new_cols

date_cols = [c for c in pivot.columns if c.startswith("d_")]

# ─────────────────────────────────────────────
# TOTALS & STATS
# ─────────────────────────────────────────────
pivot["Total"]       = pivot[date_cols].sum(axis=1).astype(int)
pivot["Avg/Day"]     = pivot[date_cols].replace(0, np.nan).mean(axis=1).round(1)
pivot["Days Active"] = (pivot[date_cols] > 0).sum(axis=1).astype(int)

# Outlier flags per enumerator
def flag_enum(row):
    vals = row[date_cols]
    active = vals[vals > 0]
    flags = []
    if any(active < outlier_low):
        flags.append(f"Low day (<{outlier_low})")
    if any(active > outlier_high):
        flags.append(f"High day (>{outlier_high})")
    return ", ".join(flags) if flags else "✓ OK"

pivot["QC Flag"] = pivot.apply(flag_enum, axis=1)

# ─────────────────────────────────────────────
# PRETTY HEADERS
# ─────────────────────────────────────────────
pretty = pivot.copy()
rename_pretty, seen_pretty = {}, {}
for col in pretty.columns:
    if col.startswith("d_"):
        raw = col[2:]  # strip "d_"
        try:
            dt = datetime.strptime(raw, "%d%b%Y")
            if header_style.startswith("Pretty"):
                name = dt.strftime("%d %b %Y")
            elif header_style.startswith("Compact"):
                name = dt.strftime("%d%b%Y")
            elif header_style.startswith("ISO"):
                name = dt.strftime("%Y-%m-%d")
            else:
                name = col
        except Exception:
            name = col
        if name in seen_pretty:
            seen_pretty[name] += 1
            name = f"{name}_{seen_pretty[name]}"
        else:
            seen_pretty[name] = 0
        rename_pretty[col] = name

pretty.rename(columns=rename_pretty, inplace=True)
pretty = pretty.loc[:, ~pretty.columns.duplicated()]

# ─────────────────────────────────────────────
# DAILY TOTALS ROW
# ─────────────────────────────────────────────
daily_total_row = {}
for col in pretty.columns:
    if col in group_cols:
        daily_total_row[col] = "── TOTAL ──" if col == "enum" else ""
    elif col in ["Total", "Avg/Day", "Days Active", "QC Flag"]:
        if col == "Total":
            daily_total_row[col] = int(pretty[col].sum())
        elif col == "Days Active":
            daily_total_row[col] = int(pretty[col].sum())
        elif col == "Avg/Day":
            daily_total_row[col] = round(float(pretty[col].mean()), 1)
        else:
            daily_total_row[col] = "──"
    else:
        try:
            daily_total_row[col] = pretty[col].sum()
        except Exception:
            daily_total_row[col] = ""

totals_row = pd.DataFrame([daily_total_row])
pretty_with_totals = pd.concat([pretty, totals_row], ignore_index=True)
# Keep numeric columns properly typed
pretty_with_totals["Avg/Day"] = pd.to_numeric(pretty_with_totals["Avg/Day"], errors="coerce")

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📋 Productivity Table", "📊 Charts", "🚨 QC Report", "📥 Export"])

# ── TAB 1: TABLE ──
with tab1:
    st.markdown('<div class="section-header">Daily Survey Counts by Enumerator</div>', unsafe_allow_html=True)

    # Heatmap color styling on numeric date columns
    date_display_cols = list(rename_pretty.values())

    def heatmap_style(val):
        if not isinstance(val, (int, float)) or pd.isna(val):
            return ""
        if val == 0:
            return "background-color: #1a1a2e; color: #333355;"
        elif val < outlier_low:
            return "background-color: #3d1a0a; color: #f5a623;"
        elif val > outlier_high:
            return "background-color: #0a2a0a; color: #4caf50;"
        else:
            intensity = min(val / outlier_high, 1.0)
            r = int(10 + 20 * intensity)
            g = int(30 + 80 * intensity)
            b = int(60 + 150 * intensity)
            return f"background-color: rgb({r},{g},{b}); color: #e0e6f0;"

    def qc_style(val):
        if val == "✓ OK":
            return "color: #4caf50; font-weight: 600;"
        return "color: #f5a623; font-weight: 600;"

    styled = (
        pretty_with_totals.style
        .map(heatmap_style, subset=[c for c in date_display_cols if c in pretty_with_totals.columns])
        .map(qc_style, subset=["QC Flag"] if "QC Flag" in pretty_with_totals.columns else [])
        .set_properties(**{"font-family": "IBM Plex Mono, monospace", "font-size": "12px"})
    )

    st.dataframe(styled, width="stretch", height=500)

    st.caption(f"🔵 Normal  🟠 Below threshold (<{outlier_low})  🟢 Above threshold (>{outlier_high})  ⚫ Zero submissions")

# ── TAB 2: CHARTS ──
with tab2:
    import plotly.graph_objects as go
    import plotly.express as px

    chart_bg   = "#0d0f14"
    chart_line = "#1e2230"
    chart_text = "#8a9bc4"
    accent     = "#2a6af5"

    def apply_dark_theme(fig):
        fig.update_layout(
            paper_bgcolor=chart_bg,
            plot_bgcolor="#111318",
            font=dict(family="IBM Plex Mono", color=chart_text, size=11),
            xaxis=dict(gridcolor=chart_line, zerolinecolor=chart_line),
            yaxis=dict(gridcolor=chart_line, zerolinecolor=chart_line),
            margin=dict(l=40, r=20, t=40, b=40),
        )
        return fig

    col_a, col_b = st.columns(2)

    # ── Bar: Total per enumerator
    with col_a:
        st.markdown('<div class="section-header">Total Surveys per Enumerator</div>', unsafe_allow_html=True)
        bar_df = pretty[["enum", "Total"]].sort_values("Total", ascending=True).tail(20)
        fig = go.Figure(go.Bar(
            x=bar_df["Total"],
            y=bar_df["enum"],
            orientation="h",
            marker=dict(color=accent, line=dict(width=0)),
        ))
        fig = apply_dark_theme(fig)
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, width="stretch")

    # ── Bar: Avg per day per enumerator
    with col_b:
        st.markdown('<div class="section-header">Average Surveys / Active Day</div>', unsafe_allow_html=True)
        avg_df = pretty[["enum", "Avg/Day"]].sort_values("Avg/Day", ascending=True).tail(20)
        fig2 = go.Figure(go.Bar(
            x=avg_df["Avg/Day"],
            y=avg_df["enum"],
            orientation="h",
            marker=dict(color="#1db954", line=dict(width=0)),
        ))
        fig2 = apply_dark_theme(fig2)
        fig2.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig2, width="stretch")

    # ── Line: Daily totals over time
    st.markdown('<div class="section-header">Daily Submission Volume</div>', unsafe_allow_html=True)
    date_totals = daily.groupby("date")["count"].sum().reset_index()
    date_totals.columns = ["date", "count"]
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=date_totals["date"],
        y=date_totals["count"],
        mode="lines+markers",
        line=dict(color=accent, width=2),
        marker=dict(size=6, color=accent),
        fill="tozeroy",
        fillcolor="rgba(42,106,245,0.08)",
        name="Daily Total"
    ))
    # Rolling average
    if len(date_totals) >= 3:
        date_totals["rolling"] = date_totals["count"].rolling(3, center=True).mean()
        fig3.add_trace(go.Scatter(
            x=date_totals["date"],
            y=date_totals["rolling"],
            mode="lines",
            line=dict(color="#f5a623", width=1.5, dash="dot"),
            name="3-Day Avg"
        ))
    fig3 = apply_dark_theme(fig3)
    fig3.update_layout(height=300, legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig3, width="stretch")

    # ── Heatmap: Enumerator × Day
    st.markdown('<div class="section-header">Enumerator Activity Heatmap</div>', unsafe_allow_html=True)
    heat_data = pivot[["enum"] + date_cols].set_index("enum")
    heat_data.columns = [c[2:] for c in heat_data.columns]  # strip "d_"
    fig4 = go.Figure(go.Heatmap(
        z=heat_data.values,
        x=heat_data.columns.tolist(),
        y=heat_data.index.tolist(),
        colorscale=[[0, "#111318"], [0.001, "#1a2040"], [0.3, "#1a4080"], [1, "#2a6af5"]],
        showscale=True,
        hoverongaps=False,
    ))
    fig4 = apply_dark_theme(fig4)
    fig4.update_layout(height=max(300, len(heat_data) * 22 + 80))
    st.plotly_chart(fig4, width="stretch")

    # ── Consent pie (if available)
    if "Consent_Status" in df.columns:
        st.markdown('<div class="section-header">Consent Breakdown</div>', unsafe_allow_html=True)
        consent_counts = df["Consent_Status"].value_counts()
        fig5 = go.Figure(go.Pie(
            labels=consent_counts.index.tolist(),
            values=consent_counts.values.tolist(),
            hole=0.55,
            marker=dict(colors=["#2a6af5", "#f5a623"], line=dict(color=chart_bg, width=3)),
            textfont=dict(family="IBM Plex Mono", size=11),
        ))
        fig5 = apply_dark_theme(fig5)
        fig5.update_layout(height=320, showlegend=True,
                           legend=dict(orientation="h", yanchor="bottom", y=-0.15))
        st.plotly_chart(fig5, width="stretch")

# ── TAB 3: QC REPORT ──
with tab3:
    st.markdown('<div class="section-header">Quality Control Flags</div>', unsafe_allow_html=True)

    flagged = pretty[pretty["QC Flag"] != "✓ OK"][["enum", "Total", "Avg/Day", "Days Active", "QC Flag"]]

    if flagged.empty:
        st.markdown('<div class="info-box">✓ No QC flags raised. All enumerators within thresholds.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="warning-box">⚠ {len(flagged)} enumerator(s) have QC flags.</div>', unsafe_allow_html=True)
        st.dataframe(flagged, width="stretch")

    st.markdown('<div class="section-header">Enumerator Summary Statistics</div>', unsafe_allow_html=True)
    summary = pretty[["enum", "Total", "Avg/Day", "Days Active", "QC Flag"]].sort_values("Total", ascending=False)
    st.dataframe(summary, width="stretch", height=400)

    if duplicate_warnings:
        st.markdown('<div class="section-header">Duplicate Warnings</div>', unsafe_allow_html=True)
        for w in duplicate_warnings:
            st.markdown(f'<div class="warning-box">{w}</div>', unsafe_allow_html=True)
        if "uid" in df.columns:
            dup_df = df[df.duplicated(subset=["uid"], keep=False)].sort_values("uid")
            show_cols = ["uid", "enum", "date"] + (["addr1"] if "addr1" in df.columns else [])
            st.dataframe(dup_df[show_cols], width="stretch", height=300)

    st.markdown('<div class="section-header">Coverage Gap Analysis</div>', unsafe_allow_html=True)
    all_dates = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    active_dates = df["date"].unique()
    missing_dates = [d for d in all_dates if d not in active_dates]
    if missing_dates:
        missing_str = ", ".join([d.strftime("%d %b") for d in missing_dates])
        st.markdown(f'<div class="warning-box">⚠ No submissions on: {missing_str}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-box">✓ Submissions recorded every day in the date range.</div>', unsafe_allow_html=True)

# ── TAB 4: EXPORT ──
with tab4:
    st.markdown('<div class="section-header">Export Options</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # ── Excel with formatting
    with col1:
        st.markdown("**📊 Formatted Excel**")
        st.caption("Color-coded heatmap, bold headers, frozen panes, summary sheet.")

        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
            pretty_with_totals.to_excel(writer, index=False, sheet_name="Productivity")
            summary.to_excel(writer, index=False, sheet_name="Summary")

            # ── Format Productivity sheet
            ws = writer.sheets["Productivity"]
            header_fill  = PatternFill("solid", fgColor="0D1A3A")
            header_font  = Font(name="Calibri", bold=True, color="FFFFFF", size=10)
            total_fill   = PatternFill("solid", fgColor="1A1A2E")
            total_font   = Font(name="Calibri", bold=True, color="A0B0D0", size=10)
            border_thin  = Border(bottom=Side(style="thin", color="2A6AF5"))

            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = border_thin

            # Color numeric cells
            date_col_indices = [
                i+1 for i, col in enumerate(pretty_with_totals.columns)
                if col in date_display_cols or col in rename_pretty.values()
            ]
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row - 1):
                for cell in row:
                    if cell.column in date_col_indices:
                        val = cell.value
                        if val is None or val == 0:
                            cell.fill = PatternFill("solid", fgColor="1A1A2E")
                            cell.font = Font(color="333355", size=9)
                        elif isinstance(val, (int, float)):
                            if val < outlier_low:
                                cell.fill = PatternFill("solid", fgColor="3D1A0A")
                                cell.font = Font(color="F5A623", bold=True, size=9)
                            elif val > outlier_high:
                                cell.fill = PatternFill("solid", fgColor="0A2A0A")
                                cell.font = Font(color="4CAF50", bold=True, size=9)
                            else:
                                cell.fill = PatternFill("solid", fgColor="0A1830")
                                cell.font = Font(color="5A9AF5", size=9)
                    cell.alignment = Alignment(horizontal="center")

            # Total row formatting
            for cell in ws[ws.max_row]:
                cell.fill = total_fill
                cell.font = total_font
                cell.alignment = Alignment(horizontal="center")

            # Auto column width
            for col_cells in ws.columns:
                max_len = max((len(str(c.value or "")) for c in col_cells), default=0)
                ws.column_dimensions[get_column_letter(col_cells[0].column)].width = min(max_len + 2, 20)

            ws.freeze_panes = "D2"

        st.download_button(
            "⬇ Download Excel",
            output_excel.getvalue(),
            file_name=f"productivity_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ── CSV
    with col2:
        st.markdown("**📄 CSV Export**")
        st.caption("Plain CSV, no formatting. Easy to import into other tools.")
        csv_bytes = pretty_with_totals.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download CSV",
            csv_bytes,
            file_name=f"productivity_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

    st.markdown("---")
    st.markdown('<div class="section-header">QC Report Export</div>', unsafe_allow_html=True)
    qc_report = pretty[["enum", "Total", "Avg/Day", "Days Active", "QC Flag"]].copy()
    qc_csv = qc_report.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download QC Report (CSV)",
        qc_csv,
        file_name=f"qc_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

    st.markdown("---")
    st.caption(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Rows in dataset: {total_surveys:,} | Enumerators: {total_enums} | Period: {min_date} → {max_date}")
