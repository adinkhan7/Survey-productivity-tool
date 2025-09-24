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
        # File uploader in sidebar
        uploaded_file = st.file_uploader("Upload File", type=["dta", "xlsx", "xls"], help="Upload a .dta (Stata) or .xlsx/.xls (Excel) file.")
        
        # Header style in sidebar
        header_style = st.selectbox(
            "Date Header Style",
            options=["Pretty (e.g., 10 Sep 2025)", "Safe (e.g., d_10Sep2025)", 
                     "Compact (e.g., 10Sep2025)", "ISO (e.g., 2025-09-10)"],
            index=0,
            help="Select how date columns will appear in the output Excel file."
        )

# Main content area
st.title("Enumerator Daily Survey Productivity Tool")
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
    with st.sidebar.expander("Column Mapping", expanded=True):
        col_options = ['Select a column'] + list(df.columns)
        consent_col = st.selectbox(
            "Consent Column (optional)",
            col_options,
            index=0,
            help="Select column with consent status (e.g., 'yes/no', '1/0')."
        )
        enum_col = st.selectbox(
            "Enumerator Column",
            col_options,
            index=col_options.index('enum') if 'enum' in col_options else 0,
            help="Select column with enumerator IDs or names."
        )
        grouping_var_col = st.selectbox(
            "Address (Optional)",
            col_options,
            index=0,
            help="Select column for grouping (e.g., 'village', 'upazilla')."
        )
        date_col = st.selectbox(
            "Date Column",
            col_options,
            index=col_options.index('starttime') if 'starttime' in col_options else 0,
            help="Select column with survey dates."
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
