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

# Custom CSS for a cleaner, softer look with Material UI inspiration
def load_css(theme):
    if theme == "Dark":
        css = """
        <style>
        .stApp {
            background-color: #1a1d2e;
            color: #e0e7ff;
        }
        .stSidebar {
            background-color: #252a41;
            padding: 1.5rem;
        }
        .stTitle {
            font-family: 'Roboto', 'Segoe UI', sans-serif;
            font-weight: 500;
            font-size: 2.2rem;
            color: #e0e7ff;
        }
        .stMarkdown {
            font-family: 'Roboto', 'Segoe UI', sans-serif;
            color: #a3bffa;
        }
        .stSelectbox > label, .stTextInput > label, .stFileUploader > label {
            color: #e0e7ff;
            font-weight: 500;
            font-family: 'Roboto', 'Segoe UI', sans-serif;
        }
        .stSelectbox > div > div > div {
            color: #e0e7ff !important;
            background-color: #2d314d;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: box-shadow 0.2s ease;
        }
        .stSelectbox > div > div > div:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .stFileUploader > div > div {
            background-color: #2d314d;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: box-shadow 0.2s ease;
        }
        .stFileUploader > div > div:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .stDataFrame {
            background-color: #252a41;
            color: #e0e7ff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .stDataFrame thead tr th {
            background-color: #2d314d;
            color: #e0e7ff;
            border-bottom: 1px solid #3a4060;
        }
        .stDataFrame tbody tr td {
            background-color: #252a41;
            color: #e0e7ff;
            border-bottom: 1px solid #3a4060;
        }
        .stDownloadButton > button {
            background-color: #1E90FF;
            color: #ffffff;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            font-family: 'Roboto', 'Segoe UI', sans-serif;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: box-shadow 0.2s ease, background-color 0.2s ease;
        }
        .stDownloadButton > button:hover {
            background-color: #187BCD;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .stWarning > div {
            background-color: #3d2b1f;
            color: #f0ad4e;
            border-radius: 8px;
        }
        .stError > div {
            background-color: #3d1a1a;
            color: #d9534f;
            border-radius: 8px;
        }
        .stSuccess > div {
            background-color: #1a3d1a;
            color: #5cb85c;
            border-radius: 8px;
        }
        hr {
            border: 1px solid #3a4060;
            margin: 1.5rem 0;
        }
        .hint-text {
            font-size: 0.8rem;
            color: #a3bffa;
            margin-bottom: 0.5rem;
            font-family: 'Roboto', 'Segoe UI', sans-serif;
        }
        </style>
        """
    else:  # Light theme with white sidebar and soft blue accents
        css = """
        <style>
        .stApp {
            background-color: #f5f7fa;
            color: #2d3748;
        }
        .stSidebar {
            background-color: #ffffff;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .stTitle {
            font-family: 'Roboto', 'Segoe UI', sans-serif;
            font-weight: 500;
            font-size: 2.2rem;
            color: #2d3748;
        }
        .stMarkdown {
            font-family: 'Roboto', 'Segoe UI', sans-serif;
            color: #4a5568;
        }
        .stSelectbox > label, .stTextInput > label, .stFileUploader > label {
            color: #2d3748;
            font-weight: 500;
            font-family: 'Roboto', 'Segoe UI', sans-serif;
        }
        .stSelectbox > div > div > div {
            color: #2d3748 !important;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: box-shadow 0.2s ease;
        }
        .stSelectbox > div > div > div:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .stFileUploader > div > div {
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: box-shadow 0.2s ease;
        }
        .stFileUploader > div > div:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .stDataFrame {
            background-color: #ffffff;
            color: #2d3748;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .stDataFrame thead tr th {
            background-color: #edf2f7;
            color: #2d3748;
            border-bottom: 1px solid #e2e8f0;
        }
        .stDataFrame tbody tr td {
            background-color: #ffffff;
            color: #2d3748;
            border-bottom: 1px solid #e2e8f0;
        }
        .stDownloadButton > button {
            background-color: #1E90FF;
            color: #ffffff;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            font-family: 'Roboto', 'Segoe UI', sans-serif;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: box-shadow 0.2s ease, background-color 0.2s ease;
        }
        .stDownloadButton > button:hover {
            background-color: #187BCD;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .stWarning > div {
            background-color: #fefcbf;
            color: #744210;
            border-radius: 8px;
        }
        .stError > div {
            background-color: #fed7d7;
            color: #742a2a;
            border-radius: 8px;
        }
        .stSuccess > div {
            background-color: #c6f6d5;
            color: #22543d;
            border-radius: 8px;
        }
        hr {
            border: 1px solid #e2e8f0;
            margin: 1.5rem 0;
        }
        .hint-text {
            font-size: 0.8rem;
            color: #718096;
            margin-bottom: 0.5rem;
            font-family: 'Roboto', 'Segoe UI', sans-serif;
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

# Sidebar for controls
st.sidebar.title("Controls")
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"], index=0)
st.sidebar.markdown('<hr>', unsafe_allow_html=True)

# File uploader in sidebar
uploaded_file = st.sidebar.file_uploader("Upload File", type=["dta", "xlsx", "xls"])
st.sidebar.markdown('<hr>', unsafe_allow_html=True)

# Header style in sidebar
header_style = st.sidebar.selectbox(
    "Date Header Style",
    options=["Pretty (e.g., 10 Sep 2025)", "Safe (e.g., d_10Sep2025)", 
             "Compact (e.g., 10Sep2025)", "ISO (e.g., 2025-09-10)"],
    index=0
)
st.sidebar.markdown('<hr>', unsafe_allow_html=True)

# Main content area
st.title("Enumerator Daily Survey Productivity Tool")
st.markdown("Upload your .dta or .xlsx file to generate daily counts by enumerator (and optional grouping like village).")

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
        st.sidebar.success(f"Loaded {len(df)} rows")
    except Exception as e:
        st.sidebar.error(f"File read error: {e}")
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
    st.sidebar.subheader("Column Mapping")
    
    st.sidebar.markdown('<span class="hint-text">Consent</span>', unsafe_allow_html=True)
    consent_col = st.sidebar.selectbox(
        "Column (optional)",
        ['Select a column'] + list(df.columns),
        index=0
    )
    
    st.sidebar.markdown('<span class="hint-text">Enumerator</span>', unsafe_allow_html=True)
    enum_col = st.sidebar.selectbox(
        "Enumerator Column",
        ['Select a column'] + list(df.columns),
        index=1 if 'enum' in df.columns else 0
    )
    
    st.sidebar.markdown('<span class="hint-text">Grouping</span>', unsafe_allow_html=True)
    grouping_var_col = st.sidebar.selectbox(
        "Grouping Column (optional)",
        ['Select a column'] + list(df.columns),
        index=0
    )
    
    st.sidebar.markdown('<span class="hint-text">Date</span>', unsafe_allow_html=True)
    date_col = st.sidebar.selectbox(
        "Date Column",
        ['Select a column'] + list(df.columns),
        index=1 if 'starttime' in df.columns else 0
    )

    if not all([enum_col != 'Select a column', date_col != 'Select a column']):
        st.sidebar.warning("Select Enumerator and Date columns.")
        st.stop()

    # Rename and process
    rename_dict = {enum_col: 'enum'}
    if consent_col != 'Select a column':
        rename_dict[consent_col] = 'consent'
    if grouping_var_col != 'Select a column':
        rename_dict[grouping_var_col] = 'grouping_var'
    df = df.rename(columns=rename_dict)

    # Date handling
    if date_col == 'starttime':
        try:
            df['date'] = pd.to_datetime(df['starttime'], errors='coerce').dt.date
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                st.sidebar.warning(f"{invalid_dates} invalid dates in 'starttime' dropped.")
                df = df.dropna(subset=['date'])
        except Exception as e:
            st.sidebar.error(f"Date conversion error: {e}")
            st.stop()
    else:
        try:
            df['date'] = pd.to_datetime(df[date_col], errors='coerce').dt.date
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                st.sidebar.warning(f"{invalid_dates} invalid dates in '{date_col}' dropped.")
                df = df.dropna(subset=['date'])
        except Exception as e:
            st.sidebar.error(f"Date conversion error: {e}")
            st.stop()

    # Required vars and drops
    required_vars = ['enum', 'date']
    if consent_col != 'Select a column':
        required_vars.append('consent')
    if grouping_var_col != 'Select a column' and 'grouping_var' not in df.columns:
        st.sidebar.error("Grouping column missing.")
        st.stop()
    missing_vars = [var for var in required_vars if var not in df.columns]
    if missing_vars:
        st.sidebar.error(f"Missing: {', '.join(missing_vars)}")
        st.stop()

    required_cols = ['enum', 'date']
    if consent_col != 'Select a column':
        required_cols.append('consent')
    if grouping_var_col != 'Select a column' and 'grouping_var' in df.columns:
        required_cols.append('grouping_var')
    df = df.dropna(subset=required_cols)

    if len(df) == 0:
        st.sidebar.warning("No valid data.")
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
        st.sidebar.error(f"Enum conversion: {e}")
        st.stop()

    if grouping_var_col != 'Select a column' and 'grouping_var' in df.columns:
        try:
            if df['grouping_var'].dtype.name == 'category':
                df['grouping_var'] = df['grouping_var'].astype(str).replace('nan', 'Unknown')
            df['grouping_var'] = df['grouping_var'].map(safe_to_string)
            df['grouping_var'] = df['grouping_var'].fillna('Unknown')
            if df['grouping_var'].apply(lambda x: isinstance(x, (list, dict, tuple))).any():
                st.sidebar.error("Nested data in grouping.")
                st.stop()
        except Exception as e:
            st.sidebar.error(f"Grouping conversion: {e}")
            st.stop()

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    if len(df) == 0:
        st.sidebar.warning("No valid dates.")
        st.stop()

    # Consent categorization
    if consent_col != 'Select a column':
        def categorize_consent(x):
            x_str = str(x).lower().strip()
            if x_str in ['1', 'yes', 'true', 'y']:
                return 'Yes'
            return 'No'
        df['Consent_Status'] = df['consent'].apply(categorize_consent)

    # Grouping and counts
    group_cols = ['enum']
    if consent_col != 'Select a column':
        group_cols.append('Consent_Status')
    if grouping_var_col != 'Select a column' and 'grouping_var' in df.columns:
        group_cols.insert(1, 'grouping_var')

    missing_cols = [col for col in group_cols if col not in df.columns]
    if missing_cols:
        st.sidebar.error(f"Grouping cols missing: {missing_cols}")
        st.stop()

    try:
        daily_counts = (
            df.groupby(group_cols + ['date'])
              .size()
              .reset_index(name='daily_count')
        )
    except Exception as e:
        st.sidebar.error(f"Groupby error: {e}")
        st.stop()

    # Reshape
    index_cols = ['enum']
    if consent_col != 'Select a column':
        index_cols.append('Consent_Status')
    if grouping_var_col != 'Select a column' and 'grouping_var' in df.columns:
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

    st.sidebar.success(f"Processed {len(reshaped)} rows{' (with consent split)' if consent_col != 'Select a column' else ''}.")

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
    st.subheader("Preview")
    st.dataframe(pretty_reshaped, use_container_width=True)

    # Download in main, centered
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pretty_reshaped.to_excel(writer, sheet_name='Daily_survey_by_enum', index=False)
        output.seek(0)
        st.download_button(
            label="Download Excel",
            data=output.getvalue(),
            file_name=f"daily_survey_productivity_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
else:
    st.info("Upload a file in the sidebar to begin!")
