
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
Upload your .dta or .xlsx file to generate a daily survey count sheet by enumerator and optional village.
Counts are split into two rows per enumerator (and village, if selected): one for consent 'Yes' and one for 'No'.
Includes a Total column summing counts across dates. Map your columns and choose a date header style.
For .dta files, enumerator labels are applied automatically if available. Use 'enum' for labels or 'enum_lab' for SurveyCTO calculated labels.
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

    # Handle duplicate columns
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
    consent_col = st.selectbox("Select column for Consent (e.g., 1/0, yes/no)", col_options, index=col_options.index('consent') if 'consent' in col_options else 0)
    enum_col = st.selectbox("Select column for Enumerator (e.g., enum or enum_lab)", col_options, index=col_options.index('enum') if 'enum' in col_options else 0)
    village_col = st.selectbox("Select column for Village (optional)", col_options, index=0)
    fielddate_col = st.selectbox("Select column for Field Date (e.g., int_date)", col_options, index=col_options.index('int_date') if 'int_date' in col_options else 0)

    if not all([consent_col, enum_col, fielddate_col]):
        st.warning("Please select columns for Consent, Enumerator, and Field Date to proceed.")
        st.stop()

    # Rename columns to standard names
    rename_dict = {
        consent_col: 'consent',
        enum_col: 'enum',
        fielddate_col: 'fielddate'
    }
    if village_col:
        rename_dict[village_col] = 'village'
    df = df.rename(columns=rename_dict)

    # Check required variables
    required_vars = ['consent', 'enum', 'fielddate']
    if village_col and 'village' not in df.columns:
        st.error("Mapped village column not found in data. Skipping.")
        st.stop()
    missing_vars = [var for var in required_vars if var not in df.columns]
    if missing_vars:
        st.error(f"Missing required variables after mapping: {', '.join(missing_vars)}. Skipping.")
        st.stop()

    # Drop missing required columns
    required_cols = ['enum', 'fielddate']
    if village_col and 'village' in df.columns:
        required_cols.append('village')
    df = df.dropna(subset=required_cols)

    if len(df) == 0:
        st.warning("No valid observations after filtering. Nothing to process.")
        st.stop()

    # Ensure enum and village (if present) are strings
    def safe_to_string(x):
        try:
            return str(x).strip() if x is not None else ''
        except:
            return ''
    try:
        df['enum'] = df['enum'].map(safe_to_string)
    except Exception as e:
        st.error(f"Failed to convert 'enum' to string: {e}")
        st.write("First 5 values of 'enum' column for debugging:")
        st.write(df['enum'].head())
        st.write("Unique values in 'enum':")
        st.write(df['enum'].unique()[:10])
        st.stop()
    if village_col and 'village' in df.columns:
        try:
            df['village'] = df['village'].map(safe_to_string)
        except Exception as e:
            st.error(f"Failed to convert 'village' to string: {e}")
            st.write("First 5 values of 'village' column for debugging:")
            st.write(df['village'].head())
            st.stop()

    # Convert fielddate to datetime
    df['fielddate'] = pd.to_datetime(df['fielddate'], errors='coerce')
    df = df.dropna(subset=['fielddate'])

    if len(df) == 0:
        st.warning("No valid dates after conversion. Nothing to process.")
        st.stop()

    # Categorize consent
    def categorize_consent(x):
        x_str = str(x).lower().strip()
        if x_str in ['1', 'yes', 'true', 'y']:
            return 'Yes'
        return 'No'
    df['Consent_Status'] = df['consent'].apply(categorize_consent)

    # Compute daily count
    group_cols = ['enum', 'Consent_Status']
    if village_col and 'village' in df.columns:
        group_cols.insert(1, 'village')
    daily_counts = (
        df.groupby(group_cols + ['fielddate'])
          .size()
          .reset_index(name='daily_count')
    )

    # Reshape wide
    index_cols = ['enum', 'Consent_Status']
    if village_col and 'village' in df.columns:
        index_cols.insert(1, 'village')
    reshaped = (
        daily_counts.pivot_table(
            index=index_cols,
            columns='fielddate',
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

    st.success(f"Processed! Generated {len(reshaped)} rows with counts for 'Yes' and 'No' consent.")

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