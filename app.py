import streamlit as st
import pandas as pd
import pyreadstat
import io
import tempfile
import os

# Page config
st.set_page_config(
    page_title="Survey Productivity Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for minimalist modern styling
st.markdown(
    """
    <style>
    /* Reset and base styles */
    .stApp {
        background-color: #f8fafc;
        color: #1e293b;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        line-height: 1.5;
    }

    /* Header */
    .app-header {
        position: sticky;
        top: 0;
        z-index: 1000;
        background-color: #ffffff;
        padding: 1.5rem 2rem;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 2rem;
    }
    .app-header h1 {
        font-size: 1.75rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 0.5rem;
    }
    .app-header p {
        font-size: 1rem;
        color: #64748b;
        max-width: 600px;
    }

    /* File uploader */
    div[data-testid="stFileUploaderDropzone"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        transition: all 0.2s ease;
    }
    div[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #3b82f6;
        background-color: #f8fafc;
    }

    /* Select boxes */
    div[data-baseweb="select"] > div {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.5rem;
        font-size: 0.875rem;
    }
    div[data-baseweb="select"]:hover > div {
        border-color: #3b82f6;
    }

    /* Buttons */
    button[kind="primary"] {
        background-color: #3b82f6;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }
    button[kind="primary"]:hover {
        background-color: #2563eb;
    }

    /* Alerts and info boxes */
    .stAlert {
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header
st.markdown(
    """
    <div class="app-header">
        <h1>Survey Productivity Dashboard</h1>
        <p>Upload a .dta or .xlsx file to generate daily survey counts by enumerator and optional grouping.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Main container
with st.container():
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload .dta or .xlsx file",
        type=["dta", "xlsx", "xls"],
        help="Select a data file to analyze"
    )

    # Header style selector
    header_style = st.selectbox(
        "Date column header style",
        options=["Pretty (10 Sep 2025)", "Safe (d_10Sep2025)", "Compact (10Sep2025)", "ISO (2025-09-10)"],
        help="Choose how dates appear in the output",
        index=0
    )

    if uploaded_file is not None:
        # Read file
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
            st.success(f"Successfully loaded {len(df)} rows")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

        # Handle MultiIndex and duplicates
        if isinstance(df.columns, pd.MultiIndex):
            st.warning("MultiIndex columns detected. Converting to single-level names.")
            df.columns = ['_'.join(map(str, col)).strip() for col in df.columns]
        if df.columns.duplicated().any():
            st.warning("Duplicate columns found. Renaming to avoid conflicts.")
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
            with st.expander("View column names"):
                st.write(df.columns.tolist())

        # Column mapping
        st.subheader("Column Mapping")
        col_options = [''] + list(df.columns)
        col1, col2 = st.columns(2)
        with col1:
            consent_col = st.selectbox(
                "Consent column (optional)",
                col_options,
                help="Select column with consent data (e.g., 1/0, yes/no)"
            )
            enum_col = st.selectbox(
                "Enumerator column",
                col_options,
                index=col_options.index('enum') if 'enum' in col_options else (col_options.index('enum_lab') if 'enum_lab' in col_options else 0),
                help="Select column with enumerator IDs or names"
            )
        with col2:
            grouping_var_col = st.selectbox(
                "Location column (optional)",
                col_options,
                help="Select column for grouping (e.g., village, landmark)"
            )
            date_col = st.selectbox(
                "Date column",
                col_options,
                index=col_options.index('starttime') if 'starttime' in col_options else (col_options.index('fielddate') if 'fielddate' in col_options else 0),
                help="Select column with survey dates"
            )
    else:
        st.info("Upload a file to begin analyzing survey data.")
