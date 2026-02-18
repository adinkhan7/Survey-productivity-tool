import streamlit as st
import pandas as pd
import pyreadstat
import io
import tempfile
import os
from datetime import datetime

st.set_page_config(layout="wide")

st.title("Enumerator Daily Survey Productivity Tool")

# File uploader FIRST
uploaded_file = st.sidebar.file_uploader(
    "Upload File",
    type=["dta", "xlsx", "xls"]
)

# STOP if no file
if uploaded_file is None:
    st.info("Upload a file to begin.")
    st.stop()

# READ FILE INTO df
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
        df = pd.read_excel(io.BytesIO(file_bytes))

except Exception as e:
    st.sidebar.error(f"File read error: {e}")
    st.stop()

# NOW df EXISTS — Column mapping can safely run
with st.sidebar.expander("Column Mapping", expanded=True):

    col_options = ['Select a column'] + list(df.columns)

    consent_col = st.selectbox(
        "Consent Column (optional)",
        col_options,
        index=0
    )

    enum_col = st.selectbox(
        "Enumerator Column",
        col_options,
        index=col_options.index('enum') if 'enum' in col_options else 0
    )

    grouping_var_col = st.selectbox(
        "Address (Optional)",
        col_options,
        index=0
    )

    grouping_var2_col = st.selectbox(
        "Second Address / Grouping (Optional)",
        col_options,
        index=0
    )

    date_col = st.selectbox(
        "Date Column",
        col_options,
        index=col_options.index('starttime') if 'starttime' in col_options else 0
    )

# VALIDATION
if enum_col == 'Select a column' or date_col == 'Select a column':
    st.warning("Please select Enumerator and Date columns.")
    st.stop()

# SAFE STRING FUNCTION
def safe_to_string(x):

    if pd.isna(x):
        return "Unknown"

    return str(x).strip()

# RENAME
rename_dict = {enum_col: 'enum'}

if consent_col != 'Select a column':
    rename_dict[consent_col] = 'consent'

if grouping_var_col != 'Select a column':
    rename_dict[grouping_var_col] = 'grouping_var'

if grouping_var2_col != 'Select a column':
    rename_dict[grouping_var2_col] = 'grouping_var2'

if date_col != 'date':
    rename_dict[date_col] = 'date'

df = df.rename(columns=rename_dict)

# DATE CONVERSION
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df = df.dropna(subset=['date'])

# CLEAN STRINGS
df['enum'] = df['enum'].map(safe_to_string)

if 'grouping_var' in df.columns:
    df['grouping_var'] = df['grouping_var'].map(safe_to_string)

if 'grouping_var2' in df.columns:
    df['grouping_var2'] = df['grouping_var2'].map(safe_to_string)

# CONSENT
if 'consent' in df.columns:

    def categorize(x):
        x = str(x).lower()
        return "Yes" if x in ["1","yes","true"] else "No"

    df["Consent_Status"] = df["consent"].apply(categorize)

# BUILD GROUP COLS
group_cols = ['enum']

if 'grouping_var' in df.columns:
    group_cols.append('grouping_var')

if 'grouping_var2' in df.columns:
    group_cols.append('grouping_var2')

if 'Consent_Status' in df.columns:
    group_cols.append('Consent_Status')

# GROUP
daily_counts = (
    df.groupby(group_cols + ['date'])
    .size()
    .reset_index(name='daily_count')
)

# PIVOT
reshaped = daily_counts.pivot_table(
    index=group_cols,
    columns='date',
    values='daily_count',
    fill_value=0
).reset_index()

# TOTAL
date_cols = [c for c in reshaped.columns if c not in group_cols]

reshaped['Total'] = reshaped[date_cols].sum(axis=1)

# DISPLAY
st.dataframe(reshaped, use_container_width=True)

# DOWNLOAD
output = io.BytesIO()

with pd.ExcelWriter(output, engine='openpyxl') as writer:
    reshaped.to_excel(writer, index=False)

st.download_button(
    "Download Excel",
    data=output.getvalue(),
    file_name="daily_productivity.xlsx"
)
