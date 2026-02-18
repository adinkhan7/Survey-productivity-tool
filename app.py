import streamlit as st
import pandas as pd
import pyreadstat
import io
import tempfile
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    layout="wide",
    page_title="Enumerator Daily Survey Productivity Tool",
    page_icon="📊"
)

# AMOLED Theme CSS
st.markdown("""
<style>
.stApp {background-color: #000000; color: #ffffff;}
.stTitle {font-family: 'Segoe UI'; font-weight: 300; color: #ffffff;}
.stMarkdown {color: #b0b0b0;}
.stSelectbox > label, .stFileUploader > label {color: #ffffff; font-weight: 500;}
.stDataFrame {background-color: #1a1a1a; color: #ffffff;}
.stDownloadButton > button {
    background-color: #0288d1;
    color: white;
    border-radius: 8px;
    padding: 0.6rem 1.2rem;
}
.stDownloadButton > button:hover {background-color: #01579b;}
hr {border: 1px solid #333333;}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Controls")

    uploaded_file = st.file_uploader(
        "Upload File",
        type=["dta", "xlsx", "xls"]
    )

    header_style = st.selectbox(
        "Date Header Style",
        options=[
            "Pretty (e.g., 10 Sep 2025)",
            "Safe (e.g., d_10Sep2025)",
            "Compact (e.g., 10Sep2025)",
            "ISO (e.g., 2025-09-10)"
        ],
        index=0
    )

st.title("Enumerator Daily Survey Productivity Tool")
st.markdown("Upload your file to generate daily productivity counts.")

if uploaded_file is not None:

    # Read file
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

        st.sidebar.success(f"Loaded {len(df)} rows")

    except Exception as e:
        st.sidebar.error(f"File read error: {e}")
        st.stop()

    # Flatten MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(map(str, col)).strip() for col in df.columns]

    # Fix duplicate columns
    if df.columns.duplicated().any():
        seen = {}
        new_cols = []
        for col in df.columns:
            if col in seen:
                seen[col] += 1
                new_cols.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                new_cols.append(col)
        df.columns = new_cols

    # Column Mapping
    with st.sidebar:

        col_options = ["Select a column"] + list(df.columns)

        consent_col = st.selectbox("Consent Column (optional)", col_options)

        enum_col = st.selectbox(
            "Enumerator Column",
            col_options,
            index=col_options.index("enum") if "enum" in col_options else 0
        )

        grouping_var_col = st.selectbox(
            "Address Column 1 (optional)",
            col_options
        )

        grouping_var2_col = st.selectbox(
            "Address Column 2 (optional)",
            col_options
        )

        date_col = st.selectbox(
            "Date Column",
            col_options,
            index=col_options.index("starttime") if "starttime" in col_options else 0
        )

    if enum_col == "Select a column" or date_col == "Select a column":
        st.warning("Select Enumerator and Date columns")
        st.stop()

    # Rename columns
    rename_dict = {enum_col: "enum"}

    if consent_col != "Select a column":
        rename_dict[consent_col] = "consent"

    if grouping_var_col != "Select a column":
        rename_dict[grouping_var_col] = "grouping_var"

    if grouping_var2_col != "Select a column":
        rename_dict[grouping_var2_col] = "grouping_var2"

    df = df.rename(columns=rename_dict)

    # Date conversion
    df["date"] = pd.to_datetime(df[date_col], errors="coerce").dt.date
    df = df.dropna(subset=["date"])

    # Clean string safely
    def safe_to_string(x):
        if pd.isna(x):
            return "Unknown"
        return str(x).strip()

    df["enum"] = df["enum"].map(safe_to_string)

    if "grouping_var" in df.columns:
        df["grouping_var"] = df["grouping_var"].map(safe_to_string)

    if "grouping_var2" in df.columns:
        df["grouping_var2"] = df["grouping_var2"].map(safe_to_string)

    # Consent processing
    if "consent" in df.columns:

        def consent_map(x):
            x = str(x).lower().strip()
            if x in ["yes", "1", "true", "y"]:
                return "Yes"
            return "No"

        df["Consent_Status"] = df["consent"].apply(consent_map)

    # Group columns dynamically
    group_cols = ["enum"]

    if "grouping_var" in df.columns:
        group_cols.append("grouping_var")

    if "grouping_var2" in df.columns:
        group_cols.append("grouping_var2")

    if "Consent_Status" in df.columns:
        group_cols.append("Consent_Status")

    # Count daily
    daily_counts = (
        df.groupby(group_cols + ["date"])
        .size()
        .reset_index(name="daily_count")
    )

    # Pivot
    reshaped = (
        daily_counts
        .pivot_table(
            index=group_cols,
            columns="date",
            values="daily_count",
            fill_value=0
        )
        .reset_index()
    )

    # Add total
    date_cols = [c for c in reshaped.columns if c not in group_cols]
    reshaped["Total"] = reshaped[date_cols].sum(axis=1)

    # Safe rename dates
    renamed_cols = {}

    for col in reshaped.columns:

        if isinstance(col, datetime) or isinstance(col, pd.Timestamp):

            safe = "d_" + pd.Timestamp(col).strftime("%d%b%Y")
            renamed_cols[col] = safe

    reshaped = reshaped.rename(columns=renamed_cols)

    # Pretty headers
    pretty = reshaped.copy()
    pretty_rename = {}

    for col in pretty.columns:

        if col.startswith("d_"):

            raw = col[2:]
            dt = datetime.strptime(raw, "%d%b%Y")

            if header_style.startswith("Pretty"):
                pretty_rename[col] = dt.strftime("%d %b %Y")

            elif header_style.startswith("Compact"):
                pretty_rename[col] = dt.strftime("%d%b%Y")

            elif header_style.startswith("ISO"):
                pretty_rename[col] = dt.strftime("%Y-%m-%d")

            else:
                pretty_rename[col] = col

    pretty = pretty.rename(columns=pretty_rename)

    # Preview
    st.subheader("Preview")
    st.dataframe(pretty, use_container_width=True)

    # Download
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pretty.to_excel(writer, index=False)

    output.seek(0)

    st.download_button(
        "Download Excel",
        data=output,
        file_name=f"daily_productivity_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Upload a file from the sidebar to begin.")
