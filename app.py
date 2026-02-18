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

    # SECOND GROUPING VAR (NEW)
    grouping_var2_col = st.selectbox(
        "Second Address / Grouping (Optional)",
        col_options,
        index=0,
        help="Select second grouping column (e.g., 'district', 'union')."
    )

    date_col = st.selectbox(
        "Date Column",
        col_options,
        index=col_options.index('starttime') if 'starttime' in col_options else 0,
        help="Select column with survey dates."
    )


# Rename and process
rename_dict = {enum_col: 'enum'}

if consent_col != 'Select a column':
    rename_dict[consent_col] = 'consent'

if grouping_var_col != 'Select a column':
    rename_dict[grouping_var_col] = 'grouping_var'

# SECOND GROUPING VAR (NEW)
if grouping_var2_col != 'Select a column':
    rename_dict[grouping_var2_col] = 'grouping_var2'

df = df.rename(columns=rename_dict)


# Required vars and drops
required_vars = ['enum', 'date']

if consent_col != 'Select a column':
    required_vars.append('consent')

if grouping_var_col != 'Select a column' and 'grouping_var' not in df.columns:
    st.sidebar.error("Grouping column missing.")
    st.stop()

# SECOND GROUPING VAR VALIDATION (NEW)
if grouping_var2_col != 'Select a column' and 'grouping_var2' not in df.columns:
    st.sidebar.error("Second grouping column missing.")
    st.stop()


required_cols = ['enum', 'date']

if consent_col != 'Select a column':
    required_cols.append('consent')

if grouping_var_col != 'Select a column' and 'grouping_var' in df.columns:
    required_cols.append('grouping_var')

# SECOND GROUPING VAR REQUIRED COL (NEW)
if grouping_var2_col != 'Select a column' and 'grouping_var2' in df.columns:
    required_cols.append('grouping_var2')

df = df.dropna(subset=required_cols)


# Convert grouping_var safely
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


# SECOND GROUPING VAR SAFE CONVERSION (NEW)
if grouping_var2_col != 'Select a column' and 'grouping_var2' in df.columns:
    try:
        if df['grouping_var2'].dtype.name == 'category':
            df['grouping_var2'] = df['grouping_var2'].astype(str).replace('nan', 'Unknown')

        df['grouping_var2'] = df['grouping_var2'].map(safe_to_string)
        df['grouping_var2'] = df['grouping_var2'].fillna('Unknown')

        if df['grouping_var2'].apply(lambda x: isinstance(x, (list, dict, tuple))).any():
            st.sidebar.error("Nested data in second grouping.")
            st.stop()

    except Exception as e:
        st.sidebar.error(f"Second grouping conversion: {e}")
        st.stop()


# Grouping and counts
group_cols = ['enum']

if consent_col != 'Select a column':
    group_cols.append('Consent_Status')

if grouping_var_col != 'Select a column' and 'grouping_var' in df.columns:
    group_cols.insert(1, 'grouping_var')

# SECOND GROUPING VAR IN GROUP_COLS (NEW)
if grouping_var2_col != 'Select a column' and 'grouping_var2' in df.columns:
    group_cols.insert(2, 'grouping_var2')


# Reshape index_cols
index_cols = ['enum']

if consent_col != 'Select a column':
    index_cols.append('Consent_Status')

if grouping_var_col != 'Select a column' and 'grouping_var' in df.columns:
    index_cols.insert(1, 'grouping_var')

# SECOND GROUPING VAR IN INDEX_COLS (NEW)
if grouping_var2_col != 'Select a column' and 'grouping_var2' in df.columns:
    index_cols.insert(2, 'grouping_var2')
