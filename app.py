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
        enum_col = st.selectbox("Enumerator Column", col_options, 
                               index=col_options.index('enum') if 'enum' in col_options else 0)
        grouping_var_col = st.selectbox("Address (Optional)", col_options, index=0)
        grouping_var_col_2 = st.selectbox("Additional Grouping (Optional)", col_options, index=0)
        date_col = st.selectbox("Date Column", col_options, 
                               index=col_options.index('starttime') if 'starttime' in col_options else 0)

    if not all([enum_col != 'Select a column', date_col != 'Select a column']):
        st.sidebar.warning("Select Enumerator and Date columns.")
        st.stop()

    # Create local names for processing
    rename_dict = {enum_col: 'enum_internal'}
    if consent_col != 'Select a column':
        rename_dict[consent_col] = 'consent_internal'
    if grouping_var_col != 'Select a column':
        rename_dict[grouping_var_col] = 'group1_internal'
    if grouping_var_col_2 != 'Select a column':
        rename_dict[grouping_var_col_2] = 'group2_internal'
    
    df_proc = df.rename(columns=rename_dict)

    try:
        df_proc['date_internal'] = pd.to_datetime(df_proc[date_col], errors='coerce').dt.date
        df_proc = df_proc.dropna(subset=['date_internal'])
    except Exception as e:
        st.sidebar.error(f"Date conversion error: {e}")
        st.stop()

    def safe_to_string(x):
        try:
            if x is None or pd.isna(x): return 'Unknown'
            return str(x).strip()
        except: return 'Unknown'

    df_proc['enum_internal'] = df_proc['enum_internal'].map(safe_to_string)
    
    group_cols = ['enum_internal']
    
    if 'group1_internal' in df_proc.columns:
        df_proc['group1_internal'] = df_proc['group1_internal'].map(safe_to_string)
        group_cols.append('group1_internal')
    
    if 'group2_internal' in df_proc.columns:
        df_proc['group2_internal'] = df_proc['group2_internal'].map(safe_to_string)
        group_cols.append('group2_internal')

    if 'consent_internal' in df_proc.columns:
        def categorize_consent(x):
            x_str = str(x).lower().strip()
            return 'Yes' if x_str in ['1', 'yes', 'true', 'y'] else 'No'
        df_proc['Consent_Status'] = df_proc['consent_internal'].apply(categorize_consent)
        group_cols.append('Consent_Status')

    daily_counts = df_proc.groupby(group_cols + ['date_internal']).size().reset_index(name='daily_count')
    
    reshaped = daily_counts.pivot_table(
        index=group_cols,
        columns='date_internal',
        values='daily_count',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Final label cleaning for display
    final_rename = {'enum_internal': enum_col}
    if grouping_var_col != 'Select a column': final_rename['group1_internal'] = grouping_var_col
    if grouping_var_col_2 != 'Select a column': final_rename['group2_internal'] = grouping_var_col_2
    
    reshaped = reshaped.rename(columns=final_rename)
    
    # Identify non-date columns for Total calculation
    id_vars = [v for v in reshaped.columns if not isinstance(v, (datetime, pd.Timestamp, datetime.date))]
    date_vars = [v for v in reshaped.columns if v not in id_vars]
    
    reshaped['Total'] = reshaped[date_vars].sum(axis=1)

    # Format Date Headers
    pretty_renamed = {}
    for col in reshaped.columns:
        if isinstance(col, (datetime, pd.Timestamp, datetime.date)):
            if header_style == "Pretty (e.g., 10 Sep 2025)":
                pretty_renamed[col] = col.strftime('%d %b %Y')
            elif header_style == "Compact (e.g., 10Sep2025)":
                pretty_renamed[col] = col.strftime('%d%b%Y')
            elif header_style == "ISO (e.g., 2025-09-10)":
                pretty_renamed[col] = col.strftime('%Y-%m-%d')
            else:
                pretty_renamed[col] = col.strftime('d_%d%b%Y')
    
    reshaped = reshaped.rename(columns=pretty_renamed)

    st.subheader("Preview")
    st.dataframe(reshaped, use_container_width=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            reshaped.to_excel(writer, sheet_name='Daily_survey_by_enum', index=False)
        output.seek(0)
        st.download_button(
            label="Download Excel",
            data=output.getvalue(),
            file_name=f"productivity_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
else:
    st.info("Upload a file in the sidebar to begin!")
