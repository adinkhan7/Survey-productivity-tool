import streamlit as st
import pandas as pd
import pyreadstat
import io
import gc
from datetime import datetime

st.set_page_config(layout="wide", page_title="Memory-Efficient Tool")

# Minimal AMOLED Style
st.markdown("<style>.stApp{background-color:#000;color:#fff;}</style>", unsafe_allow_html=True)

with st.sidebar:
    st.title("Settings")
    uploaded_file = st.file_uploader("Upload File", type=["dta", "xlsx", "xls"])
    header_style = st.selectbox("Date Style", ["Pretty", "Safe", "Compact", "ISO"])

st.title("Enumerator Daily Productivity Tool")

if uploaded_file is not None:
    try:
        # Step 1: Efficient Loading
        if uploaded_file.name.endswith('.dta'):
            # For Stata files, we read metadata first to avoid loading everything
            # Memory-lean: Only load specific columns if possible (requires user input first)
            # For now, we load normally but clear memory immediately after
            df, meta = pyreadstat.read_dta(io.BytesIO(uploaded_file.getvalue()), apply_value_formats=True)
        else:
            # Excel files: read directly from buffer
            df = pd.read_excel(uploaded_file)

        # Step 2: User Configuration
        with st.sidebar.expander("Column Mapping", expanded=True):
            cols = ["Select a column"] + list(df.columns)
            c_enum = st.selectbox("Enumerator", cols)
            c_date = st.selectbox("Date", cols)
            c_group1 = st.selectbox("Address (Optional)", cols)
            c_group2 = st.selectbox("Additional Grouping (Optional)", cols)
            c_consent = st.selectbox("Consent (Optional)", cols)

        if c_enum != "Select a column" and c_date != "Select a column":
            # Step 3: Minimal Data Extraction (Keep only needed columns)
            keep_cols = [c_enum, c_date]
            if c_group1 != "Select a column": keep_cols.append(c_group1)
            if c_group2 != "Select a column": keep_cols.append(c_group2)
            if c_consent != "Select a column": keep_cols.append(c_consent)
            
            # Filter and Drop the rest immediately
            df = df[keep_cols].copy()
            gc.collect() # Force clear memory

            # Step 4: Logic
            df['Date_Processed'] = pd.to_datetime(df[c_date], errors='coerce').dt.date
            df = df.dropna(subset=['Date_Processed'])

            group_list = [c_enum]
            if c_group1 != "Select a column": group_list.append(c_group1)
            if c_group2 != "Select a column": group_list.append(c_group2)
            
            if c_consent != "Select a column":
                df['Consent_Status'] = df[c_consent].astype(str).str.lower().map(
                    lambda x: "Yes" if x in ['1', 'yes', 'true', 'y'] else "No"
                )
                group_list.append('Consent_Status')

            for col in group_list:
                df[col] = df[col].astype(str).replace('nan', 'Unknown')

            # Create Pivot
            pivot = df.groupby(group_list + ['Date_Processed']).size().unstack(fill_value=0).reset_index()
            
            # Clean up raw data to save memory
            del df
            gc.collect()

            # Step 5: Formatting & Download
            date_cols = [c for c in pivot.columns if isinstance(c, datetime.date)]
            pivot['Total'] = pivot[date_cols].sum(axis=1)

            # Date Header Formatting logic
            date_map = {}
            for d in date_cols:
                if header_style == "Pretty": date_map[d] = d.strftime('%d %b %Y')
                elif header_style == "Compact": date_map[d] = d.strftime('%d%b%Y')
                elif header_style == "ISO": date_map[d] = d.strftime('%Y-%m-%d')
                else: date_map[d] = f"d_{d.strftime('%d%b%Y')}"
            
            pivot = pivot.rename(columns=date_map)
            st.dataframe(pivot, use_container_width=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                pivot.to_excel(writer, index=False, sheet_name='Productivity')
            st.download_button("Download Excel", output.getvalue(), "productivity.xlsx", use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Upload a file to begin.")
