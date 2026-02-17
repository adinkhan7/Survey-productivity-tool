import streamlit as st
import pandas as pd
import pyreadstat
import io
import tempfile
import os
from datetime import datetime

# Page configuration for full width
st.set_page_config(
    layout="wide",
    page_title="Enumerator Daily Survey Productivity Tool",
    page_icon="📊"
)

# Custom CSS for AMOLED black theme with depth effect
st.markdown("""
<style>
.stApp {
    background-color: #000000;
    color: #ffffff;
}
.stTitle {
    font-family: 'Segoe UI', sans-serif;
    font-weight: 300;
    color: #ffffff;
}
.stMarkdown {
    font-family: 'Segoe UI', sans-serif;
    color: #b0b0b0;
}
.stSelectbox > label, .stTextInput > label, .stFileUploader > label {
    color: #ffffff;
    font-weight: 500;
}
.stDataFrame {
    background-color: #1a1a1a;
    color: #ffffff;
}
.stDataFrame thead tr th {
    background-color: #2c2c2c;
    color: #ffffff;
    border-bottom: 1px solid #444444;
}
.stDataFrame tbody tr td {
    background-color: #1a1a1a;
    color: #ffffff;
    border-bottom: 1px solid #444444;
}
.stDownloadButton > button {
    background-color: #0288d1;
    color: #ffffff;
    border-radius: 8px;
    padding: 0.6rem 1.2rem;
    font-weight: 500;
}
.stDownloadButton > button:hover {
    background-color: #01579b;
}
.stWarning > div {
    background-color: #4a2e00;
    color: #ffb300;
}
.stError > div {
    background-color: #5c1c1c;
    color: #ff6b6b;
}
.stSuccess > div {
    background-color: #1c4a1c;
    color: #4caf50;
}
hr {
    border: 1px solid #333333;
}
.stSelectbox [data-baseweb="select"] > div {
    color: #ffffff !important;
    background-color: #1a1a1a;
}
.stSelectbox [data-baseweb="select"] > div > div {
    opacity: 0.6;
}
.stSidebar [data-baseweb="accordion"] {
    background-color: #1a1a1a;
    border: 1px solid #2c2c2c;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    padding: 10px;
}
.stSidebar .stSelectbox, .stSidebar .stFileUploader {
    background-color: #000000;
    border-radius: 6px;
    padding: 8px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar for controls with depth effect
with st.sidebar:
    st.title("Controls")
    with st.expander("Configuration", expanded=True):
        uploaded_file = st.file_uploader("Upload File", type=["dta", "xlsx", "xls"], help="Upload a .dta (Stata) or .xlsx/.xls (Excel) file.")
        
        header_style = st.selectbox(
            "Date Header Style",
            options=["Pretty (e.g., 10 Sep 2025)", "Safe (e.g., d_10Sep2025)", 
                     "Compact (e.g., 10Sep2025)", "ISO (e.g., 2025-09-10)"],
            index=0,
            help="Select how date columns will appear in the output Excel file."
        )

# Main content area
st.title("Enumerator Daily Survey Productivity Tool")
st.markdown("**Upload your .dta or .xlsx file to generate daily counts by enumerator.**")

# Process file if uploaded
if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.read()
        if uploaded_file.name.lower().endswith('.dta'):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dta') as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            try:
                df, meta = pyreadstat.read_dta(tmp_path, apply_value_formats=True)
            finally:
                os.unlink(tmp_path)
        else:
            file_buffer = io.BytesIO(file_bytes)
            df = pd.read_excel(file_buffer)
        st.sidebar.success(f"Loaded {len(df)} rows")
    except Exception as e:
        st.sidebar.error(f"File read error: {e}")
        st.stop()

    if isinstance(df.columns, pd.MultiIndex):
        st.sidebar.warning("MultiIndex detected. Flattening columns.")
        df.columns = ['_'.join(map(str, col)).strip() for col in df.columns]
    if df.columns.duplicated().any():
        st.sidebar.warning("Duplicates detected. Renaming.")
        new_columns = []
        seen = {}
        for col in df.columns:
            if col in seen:
                seen[col] += 1
                new_columns.append(f"{col}_dup{seen[col]}")
            else:
                seen[col] = 0
                new_columns.append(col)
        df.columns = new_columns

    with st.sidebar.expander("Column Mapping", expanded=True):
        col_options = ['Select a column'] + list(df.columns)
        consent_col = st.selectbox("Consent Column (optional)", col_options, index=0)
        enum_
