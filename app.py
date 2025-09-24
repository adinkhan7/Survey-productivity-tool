import streamlit as st
import pandas as pd
import pyreadstat
import io
import tempfile
import os
from datetime import datetime

# Page configuration for wide layout
st.set_page_config(
    page_title="Enumerator Daily Survey Productivity Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for minimalistic look, responsive to light/dark theme
st.markdown("""
    <style>
    /* Global minimalistic styles */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .stTitle {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 300;
        color: #1f1f1f;
    }
    .stMarkdown {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
    }
    .stSelectbox > label, .stTextInput > label {
        font-weight: 500;
        color: #333;
    }
    .stButton > button {
        background-color: #0e1117;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #1a1d2e;
    }
    .stDownloadButton > button {
        background-color: #065f46;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stDownloadButton > button:hover {
        background-color: #047857;
    }
    .stWarning > div {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
    }
    .stError > div {
        background-color: #fecaca;
        border-left: 4px solid #dc2626;
    }
    .stSuccess > div {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
    }
    /* Dark theme overrides */
    [data-testid="stAppViewContainer"] {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stTitle {
        color: #fafafa;
    }
    .stMarkdown {
        color: #e2e8f0;
    }
    .stSelectbox > label, .stTextInput > label {
        color: #e2e8f0;
    }
    .stDataFrame {
        background-color: #1a1d2e;
        color: #fafafa;
    }
    .stDataFrame thead tr th {
        background-color: #16213e;
        color: #fafafa;
    }
    .stDataFrame tbody tr td {
        background-color: #1a1d2e;
        color: #fafafa;
        border-bottom: 1px solid #334155;
    }
    /* Light theme (default) */
    @media (prefers-color-scheme: light) {
        [data-testid="stAppViewContainer"] {
            background-color: white;
            color: #1f1f1f;
        }
        .stTitle { color: #1f1f1f; }
        .stMarkdown { color: #374151; }
        .stSelectbox > label, .stTextInput > label { color: #374151; }
        .stDataFrame {
            background-color: white;
            color: #1f1f1f;
        }
        .stDataFrame thead tr th {
            background-color: #f9fafb;
            color: #1f1f1f;
        }
        .stDataFrame tbody tr td {
            background-color: white;
            color: #1f1f1f;
            border-bottom: 1px solid #d1d5db;
        }
    }
    /* Theme toggle in sidebar */
    .theme-toggle {
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar for theme toggle (minimalistic)
with st.sidebar:
    st.markdown("### Theme")
    if st.button("🌙 Dark Mode"):
        st.markdown('<script>localStorage.setItem("theme", "dark"); document.documentElement.setAttribute("data-theme", "dark");</script>', unsafe_allow_html=True)
    if st.button("☀️ Light Mode"):
        st.markdown('<script>localStorage.setItem("theme", "light"); document.documentElement.setAttribute("data-theme", "light");</script>', unsafe_allow_html=True)

# App title and description (wide layout)
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📊 Enumerator Daily Survey Productivity Tool")
with col2:
    st.empty()  # Spacer for balance

st.markdown("""
Upload your .dta or .xlsx file to generate a daily survey count sheet by enumerator and an optional grouping variable (e.g., village, landmark, upazilla).  
If a consent column is selected, counts are split into two rows per enumerator (and grouping variable, if selected): one for consent 'Yes' and one for 'No'.  
If no consent column is selected, counts are provided per enumerator (and grouping variable, if selected) without splitting by consent.
""")

# File uploader (wide)
uploaded_file = st.file_uploader("Choose a .dta or .xlsx file", type=["dta", "xlsx", "xls"], help="Supports Stata (.dta) and Excel (.xlsx/.xls) files.")

# Header style selector
header_style = st.selectbox(
    "Choose date column header style for Excel output",
    options=["Pretty (e.g., 10 Sep 2025)", "Safe (e.g., d_10Sep2025)", 
             "Compact (e.g., 10Sep2025)", "ISO (e.g., 2025-09-10)"],
    index=0
)

if uploaded_file is not None:
    # Read the file (unchanged logic)
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
        st.success(f"Loaded {len(df)} rows successfully!")
    except Exception as e:
        st.error(f"Oops, couldn't read the file: {e}")
        st.stop()

    # Handle MultiIndex and duplicate columns (unchanged)
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

    # Column mapping (wide layout with columns if needed)
    st.subheader("🔧 Map Your Columns")
    col_options = [''] + list(df.columns)
    
    col_map, col_other = st.columns(2)
    with col_map:
        consent_col = st.selectbox(
            "Consent Column (optional)",
            col_options,
            index=0
        )
        enum_col = st.selectbox(
            "Enumerator Column",
            col_options,
            index=col_options.index('enum') if 'enum' in col_options else (col_options.index('enum_lab') if 'enum_lab' in col_options else 0)
        )
    with col_other:
        grouping_var_col = st.selectbox(
            "Grouping Variable (optional)",
            col_options,
            index=0
        )
        date_col = st.selectbox(
            "Date Column",
            col_options,
            index=col_options.index('starttime') if 'starttime' in col_options else (col_options.index('fielddate') if 'fielddate' in col_options else 0)
        )

    if not all([enum_col, date_col]):
        st.warning("Please select columns for Enumerator and Date to proceed.")
        st.stop()

    # Rest of the processing logic remains unchanged...
    # (Rename columns, generate date, checks, conversions, groupby, pivot, reshape, export prep)
    rename_dict = {enum_col: 'enum'}
    if consent_col:
        rename_dict[consent_col] = 'consent'
    if grouping_var_col:
        rename_dict[grouping_var_col] = 'grouping_var'
    df = df.rename(columns=rename_dict)

    if date_col == 'starttime':
        try:
            df['date'] = pd.to_datetime(df['starttime'], errors='coerce').dt.date
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                st.warning(f"{invalid_dates} rows have invalid dates in 'starttime' and will be dropped.")
                df = df.dropna(subset=['date'])
        except Exception as e:
            st.error(f"Failed to convert 'starttime' to date: {e}")
            st.stop()
    else:
        try:
            df['date'] = pd.to_datetime(df[date_col], errors='coerce').dt.date
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                st.warning(f"{invalid_dates} rows have invalid dates in '{date_col}' and will be dropped.")
                df = df.dropna(subset=['date'])
        except Exception as e:
            st.error(f"Failed to convert '{date_col}' to date: {e}")
            st.stop()

    required_vars = ['enum', 'date']
    if consent_col:
        required_vars.append('consent')
    if grouping_var_col and 'grouping_var' not in df.columns:
        st.error("Mapped Address/Location column not found.")
        st.stop()
    missing_vars = [var for var in required_vars if var not in df.columns]
    if missing_vars:
        st.error(f"Missing: {', '.join(missing_vars)}")
        st.stop()

    required_cols = ['enum', 'date']
    if consent_col:
        required_cols.append('consent')
    if grouping_var_col and 'grouping_var' in df.columns:
        required_cols.append('grouping_var')
    df = df.dropna(subset=required_cols)

    if len(df) == 0:
        st.warning("No valid observations.")
        st.stop()

    def safe_to_string(x):
        try:
            if pd.isna(x):
                return 'Unknown'
            return str(x).strip()
        except:
            return 'Unknown'

    df['enum'] = df['enum'].astype(str).map(safe_to_string).fillna('Unknown')

    if grouping_var_col and 'grouping_var' in df.columns:
        df['grouping_var'] = df['grouping_var'].astype(str).map(safe_to_string).fillna('Unknown')

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    if len(df) == 0:
        st.warning("No valid dates.")
        st.stop()

    if consent_col:
        def categorize_consent(x):
            x_str = str(x).lower().strip()
            return 'Yes' if x_str in ['1', 'yes', 'true', 'y'] else 'No'
        df['Consent_Status'] = df['consent'].apply(categorize_consent)

    group_cols = ['enum']
    if consent_col:
        group_cols.append('Consent_Status')
    if grouping_var_col and 'grouping_var' in df.columns:
        group_cols.insert(1, 'grouping_var')

    daily_counts = df.groupby(group_cols + ['date']).size().reset_index(name='daily_count')

    index_cols = ['enum']
    if consent_col:
        index_cols.append('Consent_Status')
    if grouping_var_col and 'grouping_var' in df.columns:
        index_cols.insert(1, 'grouping_var')
    reshaped = daily_counts.pivot_table(index=index_cols, columns='date', values='daily_count', aggfunc='sum', fill_value=0).reset_index()
    date_cols = [c for c in reshaped.columns if c not in index_cols]
    reshaped['Total'] = reshaped[date_cols].sum(axis=1)

    renamed_cols = {}
    for col in reshaped.columns:
        if col not in index_cols + ['Total']:
            date_str = pd.Timestamp(col).strftime('%d%b%Y')
            renamed_cols[col] = f"d_{date_str}"
    reshaped = reshaped.rename(columns=renamed_cols)

    st.success(f"Processed! {len(reshaped)} rows generated.")

    # Prepare pretty headers
    pretty_reshaped = reshaped.copy()
    pretty_renamed = {}
    for col in pretty_reshaped.columns:
        if col.startswith('d_'):
            date_part = col.split('_')[1]
            if header_style == "Pretty (e.g., 10 Sep 2025)":
                pretty_date = datetime.strptime(date_part, '%d%b%Y').strftime('%d %b %Y')
                pretty_renamed[col] = pretty_date
            elif header_style == "Safe (e.g., d_10Sep2025)":
                pretty_renamed[col] = col
            elif header_style == "Compact (e.g., 10Sep2025)":
                pretty_date = datetime.strptime(date_part, '%d%b%Y').strftime('%d%b%Y')
                pretty_renamed[col] = pretty_date
            elif header_style == "ISO (e.g., 2025-09-10)":
                pretty_date = datetime.strptime(date_part, '%d%b%Y').strftime('%Y-%m-%d')
                pretty_renamed[col] = pretty_date
        else:
            pretty_renamed[col] = col
    pretty_reshaped = pretty_reshaped.rename(columns=pretty_renamed)

    # Preview (wide dataframe)
    st.subheader("👀 Preview")
    st.dataframe(pretty_reshaped, use_container_width=True)

    # Download (wide button)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pretty_reshaped.to_excel(writer, sheet_name='Daily_survey_by_enum', index=False)
    output.seek(0)

    st.download_button(
        label="💾 Download Excel Sheet",
        data=output.getvalue(),
        file_name=f"daily_survey_productivity_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
else:
    st.info("👆 Upload a file to get started!")
