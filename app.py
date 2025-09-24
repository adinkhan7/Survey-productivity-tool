import streamlit as st
import pandas as pd
import pyreadstat
import io
import tempfile
import os
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Survey Productivity Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for minimalist modern styling with improved visibility
st.markdown(
    """
    <style>
    /* Reset and base styles */
    .stApp {
        background-color: #f9fafb;
        color: #111827;
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
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 2rem;
    }
    .app-header h1 {
        font-size: 1.75rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.5rem;
    }
    .app-header p {
        font-size: 1rem;
        color: #4b5563;
        max-width: 600px;
    }

    /* File uploader */
    div[data-testid="stFileUploaderDropzone"] {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 1.5rem;
        transition: all 0.2s ease;
    }
    div[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #3b82f6;
        background-color: #f9fafb;
    }

    /* Select boxes */
    div[data-baseweb="select"] > div {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 0.5rem;
        font-size: 0.875rem;
        color: #111827;
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
        color: #111827;
    }

    /* DataFrame */
    .stDataFrame {
        background-color: #ffffff;
        color: #111827;
        border: 1px solid #d1d5db;
        border-radius: 8px;
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

        # Process data if required columns are selected
        if enum_col and date_col:
            try:
                # Copy dataframe
                df_processed = df.copy()

                # Handle consent
                if consent_col:
                    df_processed = df_processed[df_processed[consent_col].isin([1, 'yes', 'Yes', 'YES', True])]

                # Convert date column to datetime
                df_processed[date_col] = pd.to_datetime(df_processed[date_col], errors='coerce')
                
                # Create pivot table
                if grouping_var_col:
                    pivot = pd.pivot_table(
                        df_processed,
                        index=[enum_col, grouping_var_col],
                        columns=date_col,
                        aggfunc='size',
                        fill_value=0
                    )
                else:
                    pivot = pd.pivot_table(
                        df_processed,
                        index=enum_col,
                        columns=date_col,
                        aggfunc='size',
                        fill_value=0
                    )

                # Format column headers based on style
                date_format_map = {
                    "Pretty (10 Sep 2025)": "%d %b %Y",
                    "Safe (d_10Sep2025)": "d_%d%b%Y",
                    "Compact (10Sep2025)": "%d%b%Y",
                    "ISO (2025-09-10)": "%Y-%m-%d"
                }
                date_format = date_format_map[header_style]
                pivot.columns = [col.strftime(date_format) for col in pivot.columns]

                # Reset index for cleaner display
                pivot = pivot.reset_index()
                
                # Add total column
                pivot['Total'] = pivot.iloc[:, 1:].sum(axis=1)

                # Display preview
                st.subheader("Preview")
                st.dataframe(pivot, use_container_width=True)

                # Download button
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    pivot.to_excel(writer, index=False, sheet_name='Survey_Counts')
                output.seek(0)
                
                st.download_button(
                    label="Download Excel",
                    data=output,
                    file_name=f"survey_counts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"Error processing data: {e}")
        else:
            st.info("Please select at least Enumerator and Date columns to generate the report.")
    else:
        st.info("Upload a file to begin analyzing survey data.")
