import streamlit as st
import pandas as pd
import pyreadstat
import io
import tempfile
import os
from datetime import datetime

# ----------------------------------------
# Page config
# ----------------------------------------
st.set_page_config(
    page_title="Enumerator Daily Survey Productivity Tool",
    layout="wide"
)

# ----------------------------------------
# Custom CSS for styling + sticky header
# ----------------------------------------
st.markdown(
    """
    <style>
    /* Global white/black theme */
    .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: "Segoe UI", sans-serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* Titles and text */
    .stMarkdown, .stText, .stSubheader, .stHeader, .stTitle {
        color: #000000 !important;
    }

    /* DataFrames */
    .stDataFrame {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* Input widgets (selectbox, text input, file uploader) */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ccc !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="input"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ccc !important;
        border-radius: 6px !important;
    }
    section[data-testid="stFileUploaderDropzone"] {
        background-color: #ffffff !important;
        border: 2px dashed #ccc !important;
        color: #000000 !important;
    }

    /* Buttons */
    button[kind="primary"], button[data-baseweb="button"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #000000 !important;
        border-radius: 8px !important;
        padding: 0.4rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease-in-out;
    }
    button[kind="primary"]:hover, button[data-baseweb="button"]:hover {
        background-color: #000000 !important;
        color: #ffffff !important;
    }

    /* Sticky header */
    .app-header {
        position: sticky;
        top: 0;
        z-index: 999;
        background-color: #ffffff;
        padding: 1rem;
        border-bottom: 1px solid #ccc;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------------------
# Sticky header (title + description)
# ----------------------------------------
st.markdown(
    """
    <div class="app-header">
        <h1>Enumerator Daily Survey Productivity Tool</h1>
        <p>
            Upload your <b>.dta</b> or <b>.xlsx</b> file to generate a daily survey count 
            sheet by enumerator and optional grouping variable.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------------------
# Main App Logic
# ----------------------------------------

# File uploader
uploaded_file = st.file_uploader("Choose a .dta or .xlsx file", type=["dta", "xlsx", "xls"])

# Header style selector
header_style = st.selectbox(
    "Choose date column header style for Excel output",
    options=["Pretty (e.g., 10 Sep 2025)", "Safe (e.g., d_10Sep2025)", 
             "Compact (e.g., 10Sep2025)", "ISO (e.g., 2025-09-10)"],
    index=0
)

if uploaded_file is not None:
    # Read the file
    try:
        file_bytes = uploaded_file.read()
        if uploaded_file.name.lower().endswith('.dta'):
            # Write bytes to a temporary file for .dta
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dta') as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            try:
                # Apply value labels for .dta to get enum labels
                df, meta = pyreadstat.read_dta(tmp_path, apply_value_formats=True)
            finally:
                os.unlink(tmp_path)  # Clean up temp file
        else:
            # Use BytesIO for .xlsx
            file_buffer = io.BytesIO(file_bytes)
            df = pd.read_excel(file_buffer)
        st.success(f"Loaded {len(df)} rows successfully!")
    except Exception as e:
        st.error(f"Oops, couldn't read the file: {e}")
        st.stop()

    # Handle MultiIndex and duplicate columns
    if isinstance(df.columns, pd.MultiIndex):
        st.warning("MultiIndex columns detected. Flattening to single-level column names.")
        df.columns = ['_'.join(map(str, col)).strip() for col in df.columns]
    if df.columns.duplicated().any():
        st.warning("Duplicate column names detected. Renaming duplicates to avoid conflicts.")
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
        st.write("New column names after resolving duplicates:")
        st.write(df.columns.tolist())

    # Column mapping
    st.subheader("Map Your Columns")
    col_options = [''] + list(df.columns)
    consent_col = st.selectbox(
        "Select column for Consent (e.g., 1/0, yes/no, optional)",
        col_options,
        index=0 # always default to empty
    )
    enum_col = st.selectbox(
        "Select column for Enumerator (e.g., enum or enum_lab)",
        col_options,
        index=col_options.index('enum') if 'enum' in col_options else (col_options.index('enum_lab') if 'enum_lab' in col_options else 0)
    )
    grouping_var_col = st.selectbox(
        "Select column for Address/Location (e.g., village, landmark, upazilla, optional)",
        col_options,
        index=0
    )
    date_col = st.selectbox(
        "Select column for Date (e.g., fielddate, survey_date, collection_date, starttime)",
        col_options,
        index=col_options.index('starttime') if 'starttime' in col_options else (col_options.index('fielddate') if 'fielddate' in col_options else 0)
    )

    # ---- (rest of your original logic remains unchanged) ----
    # Your processing, grouping, reshaping, preview, and download button code continues here...
else:
    st.info("Upload a file, map your columns, and choose a header style to get started!")
