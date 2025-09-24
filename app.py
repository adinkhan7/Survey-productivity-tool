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

# Custom CSS for modern minimalistic look
def load_css(theme):
    if theme == "Dark":
        css = """
        <style>
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        .stTitle {
            font-family: 'Segoe UI', sans-serif;
            font-weight: 300;
            color: #fafafa;
        }
        .stMarkdown {
            font-family: 'Segoe UI', sans-serif;
            color: #e1e5e9;
        }
        .stSelectbox > label, .stTextInput > label, .stFileUploader > label {
            color: #fafafa;
            font-weight: 500;
        }
        .stDataFrame {
            background-color: #1e1e1e;
            color: #fafafa;
        }
        .stDataFrame thead tr th {
            background-color: #2a2a2a;
            color: #fafafa;
            border-bottom: 1px solid #444;
        }
        .stDataFrame tbody tr td {
            background-color: #1e1e1e;
            color: #fafafa;
            border-bottom: 1px solid #444;
        }
        .stDownloadButton > button {
            background-color: #1f77b4;
            color: #fafafa;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        .stDownloadButton > button:hover {
            background-color: #155a8a;
        }
        .stWarning > div {
            background-color: #3d2b1f;
            color: #f0ad4e;
        }
        .stError > div {
            background-color: #3d1a1a;
            color: #d9534f;
        }
        .stSuccess > div {
            background-color: #1a3d1a;
            color: #5cb85c;
        }
        hr {
            border: 1px solid #333;
        }
        </style>
        """
    else:  # Light theme
        css = """
        <style>
        .stApp {
            background-color: #ffffff;
            color: #212529;
        }
        .stTitle {
            font-family: 'Segoe UI', sans-serif;
            font-weight: 300;
            color: #212529;
        }
        .stMarkdown {
            font-family: 'Segoe UI', sans-serif;
            color: #495057;
        }
        .stSelectbox > label, .stTextInput > label, .stFileUploader > label {
            color: #212529;
            font-weight: 500;
        }
        .stDataFrame {
            background-color: #ffffff;
            color: #212529;
        }
        .stDataFrame thead tr th {
            background-color: #f8f9fa;
            color: #212529;
            border-bottom: 1px solid #dee2e6;
        }
        .stDataFrame tbody tr td {
            background-color: #ffffff;
            color: #212529;
            border-bottom: 1px solid #dee2e6;
        }
        .stDownloadButton > button {
            background-color: #007bff;
            color: #ffffff;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        .stDownloadButton > button:hover {
            background-color: #0056b3;
        }
        .stWarning > div {
            background-color: #fff3cd;
            color: #856404;
        }
        .stError > div {
            background-color: #f8d7da;
            color: #721c24;
        }
        .stSuccess > div {
            background-color: #d4edda;
            color: #155724;
        }
        hr {
            border: 1px solid #dee2e6;
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

# Sidebar for controls
st.sidebar.title("⚙️ Controls")
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"], index=0)
load_css(theme)

# File uploader in sidebar
uploaded_file = st.sidebar.file_uploader("📁 Upload File", type=["dta", "xlsx", "xls"], help="Upload a .dta (Stata) or .xlsx/.xls (Excel) file containing survey data.")

# Header style in sidebar
header_style = st.sidebar.selectbox(
    "📅 Date Header Style",
    options=["Pretty (e.g., 10 Sep 2025)", "Safe (e.g., d_10Sep2025)", 
             "Compact (e.g., 10Sep2025)", "ISO (e.g., 2025-09-10)"],
    index=0,
    help="Select how date columns will appear in the output Excel file."
)

# Main content area
col1, col2 = st.columns([2, 1])  # Uneven columns for title and info
with col1:
    st.title("📊 Enumerator Daily Survey Productivity Tool")
with col2:
    st.markdown("**Upload your .dta or .xlsx file to generate daily counts by enumerator (and optional grouping like village).**")

# Process file if uploaded
if uploaded_file is not None:
    # Read the file
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
        st.sidebar.success(f"✅ Loaded {len(df)} rows")
    except Exception as e:
        st.sidebar.error(f"❌ File read error: {e}")
        st.stop()

    # Handle MultiIndex and duplicates
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

    # Column mappings in sidebar
    st.sidebar.subheader("🔧 Column Mapping")
    col_options = [''] + list(df.columns)
    consent_col = st.sidebar.selectbox(
        "Consent Column (optional)",
        col_options,
        index=0,
        help="Select the column indicating consent status (e.g., 'yes/no', '1/0'). Leave blank if not applicable."
    )
    enum_col = st.sidebar.selectbox(
        "Enumerator Column",
        col_options,
        index=0,
        help="Select the column containing enumerator IDs or names (e.g., 'enum', 'enum_lab')."
    )
    grouping_var_col = st.sidebar.selectbox(
        "Grouping Column (optional)",
        col_options,
        index=0,
        help="Select a column for grouping counts (e.g., 'village', 'landmark', 'upazilla'). Leave blank if not needed."
    )
    date_col = st.sidebar.selectbox(
        "Date Column",
        col_options,
        index=0,
        help="Select the column containing survey dates (e.g., 'fielddate', 'starttime', 'survey_date')."
    )

    if not all([enum_col, date_col]):
        st.sidebar.warning("⚠️ Select Enumerator and Date columns.")
        st.stop()

    # Rename and process
    rename_dict = {enum_col: 'enum'}
    if consent_col:
        rename_dict[consent_col] = 'consent'
    if grouping_var_col:
        rename_dict[grouping_var_col] = 'grouping_var'
    df = df.rename(columns=rename_dict)

    # Date handling
    if date_col == 'starttime':
        try:
            df['date'] = pd.to_datetime(df['starttime'], errors='coerce').dt.date
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                st.sidebar.warning(f"⚠️ {invalid_dates} invalid dates in 'starttime' dropped.")
                df = df.dropna(subset=['date'])
        except Exception as e:
            st.sidebar.error(f"❌ Date conversion error: {e}")
            st.stop()
    else:
        try:
            df['date'] = pd.to_datetime(df[date_col], errors='coerce').dt.date
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                st.sidebar.warning(f"⚠️ {invalid_dates} invalid dates in '{date_col}' dropped.")
                df = df.dropna(subset=['date'])
        except Exception as e:
            st.sidebar.error(f"❌ Date conversion error: {e}")
            st.stop()

    # Required vars and drops
    required_vars = ['enum', 'date']
    if consent_col:
        required_vars.append('consent')
    if grouping_var_col and 'grouping_var' not in df.columns:
        st.sidebar.error("❌ Grouping column missing.")
        st.stop()
    missing_vars = [var for var in required_vars if var not in df.columns]
    if missing_vars:
        st.sidebar.error(f"❌ Missing: {', '.join(missing_vars)}")
        st.stop()

    required_cols = ['enum', 'date']
    if consent_col:
        required_cols.append('consent')
    if grouping_var_col and 'grouping_var' in df.columns:
        required_cols.append('grouping_var')
    df = df.dropna(subset=required_cols)

    if len(df) == 0:
        st.sidebar.warning("⚠️ No valid data.")
        st.stop()

    # String conversions
    def safe_to_string(x):
        try:
            if x is None or pd.isna(x):
                return 'Unknown'
            if isinstance(x, (list, tuple)):
                return str(x[0]).strip() if x else 'Unknown'
            if isinstance(x, dict):
                return str(list(x.values())[0]).strip() if x else 'Unknown'
            return str(x).strip()
        except:
            return 'Unknown'

    try:
        if df['enum'].dtype.name == 'category':
            df['enum'] = df['enum'].astype(str).replace('nan', 'Unknown')
        df['enum'] = df['enum'].map(safe_to_string)
    except Exception as e:
        st.sidebar.error(f"❌ Enum conversion: {e}")
        st.stop()

    if grouping_var_col and 'grouping_var' in df.columns:
        try:
            if df['grouping_var'].dtype.name == 'category':
                df['grouping_var'] = df['grouping_var'].astype(str).replace('nan', 'Unknown')
            df['grouping_var'] = df['grouping_var'].map(safe_to_string)
            df['grouping_var'] = df['grouping_var'].fillna('Unknown')
            if df['grouping_var'].apply(lambda x: isinstance(x, (list, dict, tuple))).any():
                st.sidebar.error("❌ Nested data in grouping.")
                st.stop()
        except Exception as e:
            st.sidebar.error(f"❌ Grouping conversion: {e}")
            st.stop()

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    if len(df) == 0:
        st.sidebar.warning("⚠️ No valid dates.")
        st.stop()

    # Consent categorization
    if consent_col:
        def categorize_consent(x):
            x_str = str(x).lower().strip()
            if x_str in ['1', 'yes', 'true', 'y']:
                return 'Yes'
            return 'No'
        df['Consent_Status'] = df['consent'].apply(categorize_consent)

    # Grouping and counts
    group_cols = ['enum']
    if consent_col:
        group_cols.append('Consent_Status')
    if grouping_var_col and 'grouping_var' in df.columns:
        group_cols.insert(1, 'grouping_var')

    missing_cols = [col for col in group_cols if col not in df.columns]
    if missing_cols:
        st.sidebar.error(f"❌ Grouping cols missing: {missing_cols}")
        st.stop()

    try:
        daily_counts = (
            df.groupby(group_cols + ['date'])
              .size()
              .reset_index(name='daily_count')
        )
    except Exception as e:
        st.sidebar.error(f"❌ Groupby error: {e}")
        st.stop()

    # Reshape
    index_cols = ['enum']
    if consent_col:
        index_cols.append('Consent_Status')
    if grouping_var_col and 'grouping_var' in df.columns:
        index_cols.insert(1, 'grouping_var')
    reshaped = (
        daily_counts.pivot_table(
            index=index_cols,
            columns='date',
            values='daily_count',
            aggfunc='sum',
            fill_value=0
        )
        .reset_index()
    )

    date_cols = [c for c in reshaped.columns if c not in index_cols]
    reshaped['Total'] = reshaped[date_cols].sum(axis=1)

    # Rename for safety
    renamed_cols = {}
    for col in reshaped.columns:
        if col not in index_cols + ['Total']:
            date_str = pd.Timestamp(col).strftime('%d%b%Y')
            safe_name = f"d_{date_str}"
            renamed_cols[col] = safe_name
    reshaped = reshaped.rename(columns=renamed_cols)

    st.sidebar.success(f"✅ Processed {len(reshaped)} rows{' (with consent split)' if consent_col else ''}.")

    # Pretty rename based on style
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

    # Main preview
    st.subheader("👀 Preview")
    st.dataframe(pretty_reshaped, use_container_width=True)

    # Download in main, centered
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pretty_reshaped.to
