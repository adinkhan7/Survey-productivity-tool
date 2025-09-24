import streamlit as st
import pandas as pd
import pyreadstat
import io
import tempfile
import os
from datetime import datetime

# App title and description
st.title("Enumerator Daily Survey Productivity Tool")
st.markdown("""
Upload your .dta or .xlsx file to generate a daily survey count sheet by enumerator and an optional grouping variable (e.g., village, landmark, upazilla).
If a consent column is selected, counts are split into two rows per enumerator (and grouping variable, if selected): one for consent 'Yes' and one for 'No'.
If no consent column is selected, counts are provided per enumerator (and grouping variable, if selected) without splitting by consent.
Includes a Total column summing counts across dates. Map your columns and choose a date header style.
For .dta files, enumerator labels are applied automatically if available. Use 'enum' for labels or 'enum_lab' for SurveyCTO calculated labels.
If a 'starttime' column is present, the date will be derived from it by default, similar to Stata's 'gen fielddate = dofc(starttime)'.
""")

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
        index= 0 # always default to the empty option
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

    if not all([enum_col, date_col]):
        st.warning("Please select columns for Enumerator and Date to proceed.")
        st.stop()

    # Rename columns to standard names
    rename_dict = {enum_col: 'enum'}
    if consent_col:
        rename_dict[consent_col] = 'consent'
    if grouping_var_col:
        rename_dict[grouping_var_col] = 'grouping_var'
    df = df.rename(columns=rename_dict)

    # Generate date from starttime if selected, otherwise use the selected date column
    if date_col == 'starttime':
        try:
            df['date'] = pd.to_datetime(df['starttime'], errors='coerce').dt.date
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                st.warning(f"{invalid_dates} rows have invalid dates in 'starttime' and will be dropped. Check your 'starttime' column for non-datetime values.")
                if 'starttime' in df.columns:
                    st.write("Sample of invalid 'starttime' values (first 5):")
                    st.write(df[df['date'].isna()][['starttime']].head())
                else:
                    st.write("Error: 'starttime' column not found after mapping.")
            df = df.dropna(subset=['date'])
        except Exception as e:
            st.error(f"Failed to convert 'starttime' to date: {e}")
            if 'starttime' in df.columns:
                st.write("First 5 values of 'starttime' column for debugging:")
                st.write(df['starttime'].head())
                st.write("Unique values in 'starttime':")
                st.write(df['starttime'].unique()[:10])
            st.stop()
    else:
        try:
            df['date'] = pd.to_datetime(df[date_col], errors='coerce').dt.date
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                st.warning(f"{invalid_dates} rows have invalid dates in '{date_col}' and will be dropped. Check your date column for non-date values.")
                if date_col in df.columns:
                    st.write(f"Sample of invalid '{date_col}' values (first 5):")
                    st.write(df[df['date'].isna()][[date_col]].head())
                else:
                    st.write(f"Error: '{date_col}' column not found after mapping.")
            df = df.dropna(subset=['date'])
        except Exception as e:
            st.error(f"Failed to convert '{date_col}' to date: {e}")
            if date_col in df.columns:
                st.write(f"First 5 values of '{date_col}' column for debugging:")
                st.write(df[date_col].head())
                st.write(f"Unique values in '{date_col}':")
                st.write(df[date_col].unique()[:10])
            st.stop()

    # Check required variables
    required_vars = ['enum', 'date']
    if consent_col:
        required_vars.append('consent')
    if grouping_var_col and 'grouping_var' not in df.columns:
        st.error("Mapped Address/Location column not found in data. Skipping.")
        st.stop()
    missing_vars = [var for var in required_vars if var not in df.columns]
    if missing_vars:
        st.error(f"Missing required variables after mapping: {', '.join(missing_vars)}. Skipping.")
        st.stop()

    # Drop missing required columns
    required_cols = ['enum', 'date']
    if consent_col:
        required_cols.append('consent')
    if grouping_var_col and 'grouping_var' in df.columns:
        required_cols.append('grouping_var')
    df = df.dropna(subset=required_cols)

    if len(df) == 0:
        st.warning("No valid observations after filtering. Nothing to process.")
        st.stop()

    # Ensure enum and grouping_var (if present) are strings
    def safe_to_string(x):
        try:
            if x is None or pd.isna(x):
                return 'Unknown'
            if isinstance(x, (list, tuple)):
                return str(x[0]).strip() if x else 'Unknown'  # Take first item if list/tuple
            if isinstance(x, dict):
                return str(list(x.values())[0]).strip() if x else 'Unknown'  # Take first value if dict
            return str(x).strip()
        except:
            return 'Unknown'

    try:
        # Convert enum to string, handling categoricals
        if df['enum'].dtype.name == 'category':
            df['enum'] = df['enum'].astype(str).replace('nan', 'Unknown')
        df['enum'] = df['enum'].map(safe_to_string)
    except Exception as e:
        st.error(f"Failed to convert 'enum' to string: {e}")
        st.write("First 5 values of 'enum' column for debugging:")
        st.write(df['enum'].head())
        st.write("Unique values in 'enum':")
        st.write(df['enum'].unique()[:10])
        st.stop()

    if grouping_var_col and 'grouping_var' in df.columns:
        try:
            # Convert grouping_var to string, handling categoricals
            if df['grouping_var'].dtype.name == 'category':
                df['grouping_var'] = df['grouping_var'].astype(str).replace('nan', 'Unknown')
            df['grouping_var'] = df['grouping_var'].map(safe_to_string)
            df['grouping_var'] = df['grouping_var'].fillna('Unknown')  # Handle NaN
            # Check for nested data
            if df['grouping_var'].apply(lambda x: isinstance(x, (list, dict, tuple))).any():
                st.error("Error: 'grouping_var' column contains nested data (lists/dicts) after conversion.")
                st.write("Sample of 'grouping_var' column:")
                st.write(df['grouping_var'].head(10))
                st.stop()
        except Exception as e:
            st.error(f"Failed to convert 'grouping_var' to string: {e}")
            st.write("First 5 values of 'grouping_var' column for debugging:")
            st.write(df['grouping_var'].head())
            st.stop()

    # Ensure date is in datetime format for grouping
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    if len(df) == 0:
        st.warning("No valid dates after conversion. Nothing to process.")
        st.stop()

    # Categorize consent if provided
    if consent_col:
        def categorize_consent(x):
            x_str = str(x).lower().strip()
            if x_str in ['1', 'yes', 'true', 'y']:
                return 'Yes'
            return 'No'
        df['Consent_Status'] = df['consent'].apply(categorize_consent)

    # Compute daily count
    group_cols = ['enum']
    if consent_col:
        group_cols.append('Consent_Status')
    if grouping_var_col and 'grouping_var' in df.columns:
        group_cols.insert(1, 'grouping_var')

    # Validate group_cols
    missing_cols = [col for col in group_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Error: Grouping columns {missing_cols} not found in DataFrame.")
        st.stop()

    try:
        daily_counts = (
            df.groupby(group_cols + ['date'])
              .size()
              .reset_index(name='daily_count')
        )
    except Exception as e:
        st.error(f"Error in groupby: {e}")
        st.write("Debug: DataFrame info:")
        st.write(df.info())
        st.write("Debug: Sample data:")
        st.write(df.head())
        st.stop()

    # Reshape wide
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

    # Add a total column
    date_cols = [c for c in reshaped.columns if c not in index_cols]
    reshaped['Total'] = reshaped[date_cols].sum(axis=1)

    # Rename columns to safe internal names
    renamed_cols = {}
    for col in reshaped.columns:
        if col not in index_cols + ['Total']:
            date_str = pd.Timestamp(col).strftime('%d%b%Y')
            safe_name = f"d_{date_str}"
            renamed_cols[col] = safe_name
    reshaped = reshaped.rename(columns=renamed_cols)

    st.success(f"Processed! Generated {len(reshaped)} rows with counts{' for \"Yes\" and \"No\" consent' if consent_col else ''}.")

    # Prepare for Excel export based on header style
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

    # Display preview table
    st.subheader("Preview:")
    st.dataframe(pretty_reshaped.head(10))

    # Download button for Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pretty_reshaped.to_excel(writer, sheet_name='Daily_survey_by_enum', index=False)
    output.seek(0)

    st.download_button(
        label="Download Excel Sheet",
        data=output.getvalue(),
        file_name=f"daily_survey_productivity_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Upload a file, map your columns, and choose a header style to get started!")
