import streamlit as st
import pandas as pd
import pyreadstat
import io
import tempfile
import os
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    layout="wide",
    page_title="Enumerator Daily Survey Productivity Tool",
    page_icon="📊"
)

# ---------------- THEME ----------------
st.markdown("""
<style>
.stApp {background-color: #000000; color: #ffffff;}
.stDownloadButton > button {
    background-color: #0288d1;
    color: white;
    border-radius: 8px;
    padding: 0.6rem 1.2rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
with st.sidebar:

    st.title("Controls")

    uploaded_file = st.file_uploader(
        "Upload File",
        type=["dta", "xlsx", "xls"]
    )

    header_style = st.selectbox(
        "Date Header Style",
        [
            "Pretty (e.g., 10 Sep 2025)",
            "Safe (e.g., d_10Sep2025)",
            "Compact (e.g., 10Sep2025)",
            "ISO (e.g., 2025-09-10)"
        ]
    )

# ---------------- TITLE ----------------
st.title("Enumerator Daily Survey Productivity Tool")

if uploaded_file is None:
    st.info("Upload a file from sidebar.")
    st.stop()

# ---------------- READ FILE ----------------
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

    st.sidebar.success(f"{len(df)} rows loaded")

except Exception as e:

    st.error(e)
    st.stop()

# ---------------- FIX COLUMN NAMES ----------------
if isinstance(df.columns, pd.MultiIndex):
    df.columns = ["_".join(map(str, col)) for col in df.columns]

df.columns = [str(c).strip() for c in df.columns]

# ---------------- COLUMN SELECT ----------------
col_options = ["Select a column"] + list(df.columns)

enum_col = st.sidebar.selectbox(
    "Enumerator Column",
    col_options,
    index=col_options.index("enum") if "enum" in col_options else 0
)

date_col = st.sidebar.selectbox(
    "Date Column",
    col_options,
    index=col_options.index("starttime") if "starttime" in col_options else 0
)

consent_col = st.sidebar.selectbox(
    "Consent Column (optional)",
    col_options
)

addr1_col = st.sidebar.selectbox(
    "Address Column 1 (optional)",
    col_options
)

addr2_col = st.sidebar.selectbox(
    "Address Column 2 (optional)",
    col_options
)

if enum_col == "Select a column" or date_col == "Select a column":
    st.warning("Enumerator and Date required")
    st.stop()

# ---------------- RENAME ----------------
rename_map = {
    enum_col: "enum",
    date_col: "date"
}

if consent_col != "Select a column":
    rename_map[consent_col] = "consent"

if addr1_col != "Select a column":
    rename_map[addr1_col] = "addr1"

if addr2_col != "Select a column":
    rename_map[addr2_col] = "addr2"

df = df.rename(columns=rename_map)

# ---------------- DATE CLEAN ----------------
df["date"] = pd.to_datetime(df["date"], errors="coerce")

df = df.dropna(subset=["date"])

df["date"] = df["date"].dt.normalize()

# ---------------- CLEAN STRING FIELDS ----------------
def clean(x):
    if pd.isna(x):
        return "Unknown"
    return str(x).strip()

df["enum"] = df["enum"].apply(clean)

if "addr1" in df.columns:
    df["addr1"] = df["addr1"].apply(clean)

if "addr2" in df.columns:
    df["addr2"] = df["addr2"].apply(clean)

# ---------------- CONSENT ----------------
if "consent" in df.columns:

    def map_consent(x):

        x = str(x).lower().strip()

        if x in ["yes", "1", "true", "y"]:
            return "Yes"

        return "No"

    df["Consent_Status"] = df["consent"].apply(map_consent)

# ---------------- GROUP COLS ----------------
group_cols = ["enum"]

if "addr1" in df.columns:
    group_cols.append("addr1")

if "addr2" in df.columns:
    group_cols.append("addr2")

if "Consent_Status" in df.columns:
    group_cols.append("Consent_Status")

# ---------------- COUNT ----------------
daily = (
    df.groupby(group_cols + ["date"], dropna=False)
    .size()
    .reset_index(name="count")
)

# ---------------- PIVOT ----------------
pivot = (
    daily.pivot_table(
        index=group_cols,
        columns="date",
        values="count",
        fill_value=0,
        aggfunc="sum"
    )
    .reset_index()
)

# ---------------- SAFE UNIQUE COLUMN NAMES ----------------
new_cols = []
seen = {}

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

# ---------------- TOTAL ----------------
date_cols = [c for c in pivot.columns if c.startswith("d_")]

pivot["Total"] = pivot[date_cols].sum(axis=1)

# ---------------- PRETTY HEADERS ----------------
pretty = pivot.copy()

rename_pretty = {}
seen_pretty = {}

for col in pretty.columns:

    if col.startswith("d_"):

        raw = col.split("_")[1]

        dt = datetime.strptime(raw, "%d%b%Y")

        if header_style.startswith("Pretty"):
            name = dt.strftime("%d %b %Y")

        elif header_style.startswith("Compact"):
            name = dt.strftime("%d%b%Y")

        elif header_style.startswith("ISO"):
            name = dt.strftime("%Y-%m-%d")

        else:
            name = col

        if name in seen_pretty:
            seen_pretty[name] += 1
            name = f"{name}_{seen_pretty[name]}"
        else:
            seen_pretty[name] = 0

        rename_pretty[col] = name

pretty.rename(columns=rename_pretty, inplace=True)

# ---------------- FINAL SAFETY ----------------
pretty = pretty.loc[:, ~pretty.columns.duplicated()]

# ---------------- SHOW ----------------
st.subheader("Preview")

st.dataframe(pretty, use_container_width=True)

# ---------------- DOWNLOAD ----------------
output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    pretty.to_excel(writer, index=False)

st.download_button(
    "Download Excel",
    output.getvalue(),
    file_name=f"productivity_{datetime.now().strftime('%Y%m%d')}.xlsx"
)
