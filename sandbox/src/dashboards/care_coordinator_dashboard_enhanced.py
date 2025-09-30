
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional

# Import database and other dependencies
from src import database
from src.core_utils import get_user_role_ids
import streamlit.components.v1 as components
from src.dashboards.workflow_module import show_workflow_management
from src.dashboards.phone_review import show_phone_review_entry

def show(user_id, user_role_ids=None):
    if user_role_ids is None:
        user_role_ids = []
    
    # Check if user has Lead Coordinator (37) or Coordinator Manager (40) roles
    has_lc_role = 37 in user_role_ids
    has_cm_role = 40 in user_role_ids
    
    st.title("Care Coordinator Dashboard")
    
    # Show onboarding queue statistics only for management roles
    has_management_role = has_lc_role or has_cm_role
    if has_management_role:
        role_text = []
        if has_lc_role:
            role_text.append("Lead Coordinator")
        if has_cm_role:
            role_text.append("Coordinator Manager")
        st.info(f"**Management Access**: You have {' & '.join(role_text)} privileges with additional tabs available")
        tab1, tab2, tab3 = st.tabs(["My Patients", "Phone Reviews", "Team Management"])
        with tab1:
            show_coordinator_patient_list(user_id, context="tab1")
        with tab2:
            from src.dashboards.phone_review import show_phone_review_entry
            show_phone_review_entry(mode="cm", user_id=user_id)
        with tab3:
            # --- Coordinator Tasks: Total Minutes This Month Header ---
            # We'll calculate the total from the Coordinator Monthly Summary DataFrame (df_summary)
            # This is more robust and avoids local variable errors
            summary_rows = database.get_coordinator_monthly_minutes_live()
            total_minutes = None
            if summary_rows:
                try:
                    import pandas as pd
                    df_summary = pd.DataFrame(summary_rows)
                    if not df_summary.empty and 'total_minutes' in df_summary.columns:
                        total_minutes = pd.to_numeric(df_summary['total_minutes'], errors='coerce').fillna(0).sum()
                except Exception as e:
                    st.markdown(f"### Total Minutes This Month: _Error loading summary ({e})_")
            if total_minutes is not None:
                st.markdown(f"### Total Minutes This Month: **{int(total_minutes):,}**")
            else:
                st.markdown("### Total Minutes This Month: _No data available_")
            
            # --- Patient and Coordinator Monthly Summary Tables Side-by-Side ---
            st.divider()
            col_patient, col_coord = st.columns(2)
            
            with col_patient:
                st.subheader("Patient Monthly Summary (Current Month)")
                try:
                    import sqlite3
                    import pandas as pd
                    conn = database.get_db_connection()
                    now = pd.Timestamp.now()
                    year = int(now.year)
                    month = int(now.month)
                    table_name = f"coordinator_monthly_summary_{year}_{str(month).zfill(2)}"
                    table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
                    if not table_exists:
                        st.info(f"No coordinator monthly summary table found for current month ({table_name}).")
                    else:
                        summary_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                        conn.close()
                        if summary_df.empty or 'patient_id' not in summary_df.columns or 'total_minutes' not in summary_df.columns:
                            st.info("No patient summary data available for the current month.")
                        else:
                            # Use centralized patient data aggregation functions
                            from src.core_utils import aggregate_patient_data_by_patient_id, prepare_patient_summary_with_facility_mapping
                            
                            # Aggregate patient data by patient_id to avoid coordinator-patient duplicates
                            aggregated_df = aggregate_patient_data_by_patient_id(summary_df)
                            
                            # Prepare summary DataFrame with patient names and facility mapping
                            summary_df = prepare_patient_summary_with_facility_mapping(aggregated_df, database)
                            st.write("Sorted by Sum of Minutes (lowest → highest):")

                            # Partition into sections to reduce scrolling: red (<40), yellow (40-89), green/blue (>=90)
                            red_df = summary_df[summary_df['Sum of Minutes'] < 40].copy()
                            yellow_df = summary_df[(summary_df['Sum of Minutes'] >= 40) & (summary_df['Sum of Minutes'] < 90)].copy()
                            greenblue_df = summary_df[summary_df['Sum of Minutes'] >= 90].copy()

                            def _color_minutes(val):
                                try:
                                    v = float(val)
                                except Exception:
                                    return ''
                                if v < 40:
                                    return 'background-color: #f94144; color: white'
                                elif v < 90:
                                    return 'background-color: #f9c74f; color: black'
                                elif v < 200:
                                    return 'background-color: #90be6d; color: black'
                                else:
                                    return 'background-color: #89C2E0; color: black'

                            with st.expander(f"Red (<40 minutes) — {len(red_df)} patients", expanded=(len(red_df) > 0 and len(red_df) <= 10)):
                                if red_df.empty:
                                    st.info("No patients in this category.")
                                else:
                                    try:
                                        styled = red_df.style.applymap(_color_minutes, subset=['Sum of Minutes'])
                                        st.dataframe(styled, use_container_width=True)
                                    except Exception:
                                        st.dataframe(red_df, use_container_width=True)

                            with st.expander(f"Yellow (40–89 minutes) — {len(yellow_df)} patients", expanded=(len(yellow_df) > 0 and len(yellow_df) <= 10)):
                                if yellow_df.empty:
                                    st.info("No patients in this category.")
                                else:
                                    try:
                                        styled = yellow_df.style.applymap(_color_minutes, subset=['Sum of Minutes'])
                                        st.dataframe(styled, use_container_width=True)
                                    except Exception:
                                        st.dataframe(yellow_df, use_container_width=True)

                            with st.expander(f"Green / Blue (≥90 minutes) — {len(greenblue_df)} patients", expanded=(len(greenblue_df) > 0 and len(greenblue_df) <= 10)):
                                if greenblue_df.empty:
                                    st.info("No patients in this category.")
                                else:
                                    try:
                                        styled = greenblue_df.style.applymap(_color_minutes, subset=['Sum of Minutes'])
                                        st.dataframe(styled, use_container_width=True)
                                    except Exception:
                                        st.dataframe(greenblue_df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading patient monthly summary: {e}")
            
            with col_coord:
                st.subheader("Coordinator Monthly Summary (Current Month)")
                try:
                    # Use live aggregation from database helper
                    summary_rows = database.get_coordinator_monthly_minutes_live()
                    if not summary_rows:
                        st.info("No coordinator summary data available for the current month.")
                    else:
                        import pandas as pd
                        df_summary = pd.DataFrame(summary_rows)

                        # Try to get coordinator names from the tasks table first (some tables include coordinator_name)
                        conn = database.get_db_connection()
                        now = pd.Timestamp.now()
                        year = now.year
                        month = now.month
                        table_name = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
                        table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
                        id_to_name = {}
                        def _safe_key(val):
                            try:
                                if pd.isna(val):
                                    return None
                                return str(int(val))
                            except Exception:
                                return str(val)

                        if table_exists:
                            try:
                                tasks_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                                if 'coordinator_name' in tasks_df.columns:
                                    mapping = tasks_df[['coordinator_id', 'coordinator_name']].dropna().drop_duplicates('coordinator_id')
                                    for _, row in mapping.iterrows():
                                        key = _safe_key(row['coordinator_id'])
                                        if key:
                                            id_to_name[key] = row['coordinator_name']
                            except Exception:
                                # ignore and fallback to users table
                                pass
                        conn.close()

                        # Fallback to users table for coordinators
                        if not id_to_name:
                            coordinators = database.get_users_by_role(36)
                            for c in coordinators:
                                uid = c.get('user_id')
                                if uid is None:
                                    continue
                                id_to_name[_safe_key(uid)] = c.get('full_name', c.get('username', 'Unknown'))

                        # Normalize coordinator id keys and map
                        df_summary['coord_key'] = df_summary['coordinator_id'].apply(lambda x: _safe_key(x) if pd.notna(x) else None)
                        df_summary['Coordinator'] = df_summary['coord_key'].map(id_to_name).fillna(df_summary['coord_key'])
                        df_summary = df_summary[['Coordinator', 'total_minutes']]
                        df_summary = df_summary.rename(columns={'total_minutes': 'Sum of Minutes'})
                        df_summary = df_summary.sort_values('Sum of Minutes', ascending=True)
                        st.write("Sorted by Sum of Minutes (lowest → highest):")
                        st.dataframe(df_summary, use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading coordinator monthly summary: {e}")
            
            st.subheader("Coordinator Tasks Table (Editable, Filterable, Sortable)")
            try:
                import datetime
                conn = database.get_db_connection()
                # List all tables matching coordinator_task_YYYY_MM
                table_query = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'coordinator_task_%' ORDER BY name DESC"
                all_table_names = [row[0] for row in conn.execute(table_query).fetchall()]
                conn.close()

                # Compute current, last, and month before last table names
                today = datetime.date.today()
                months = []
                for i in range(3):
                    year = today.year
                    month = today.month - i
                    while month <= 0:
                        month += 12
                        year -= 1
                    months.append((year, month))
                valid_table_names = [f"coordinator_tasks_{y}_{str(m).zfill(2)}" for y, m in months]
                # Only show tables that exist and are in the valid set
                table_names = [t for t in valid_table_names if t in all_table_names]

                if not table_names:
                    st.info("No coordinator task tables found for the last three months.")
                else:
                    # --- FILTERS: Side-by-side layout (table selection integrated here) ---
                    filter_cols = st.columns(3)
                    with filter_cols[0]:
                        st.markdown("**Monthly File**")
                        selected_table = st.selectbox("Select Monthly File", table_names, key="monthly_file_selector")
                    # Load the selected table for filtering and display
                    if selected_table:
                        conn = database.get_db_connection()
                        df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
                        # If patient_id is present, join with patients table for patient info
                        if 'patient_id' in df.columns:
                            try:
                                patients = database.get_all_patients() if hasattr(database, 'get_all_patients') else []
                                patients_df = pd.DataFrame(patients)
                                required_cols = {'patient_id', 'first_name', 'last_name', 'dob'}
                                if not patients_df.empty and required_cols.issubset(patients_df.columns):
                                    df = df.merge(
                                        patients_df[['patient_id', 'first_name', 'last_name', 'dob']],
                                        on='patient_id', how='left'
                                    )
                                    # Move patient info columns to front
                                    first_cols = [col for col in ['last_name', 'first_name', 'dob'] if col in df.columns]
                                    other_cols = [c for c in df.columns if c not in first_cols]
                                    df = df[first_cols + other_cols]
                            except Exception as e:
                                st.warning(f"Could not join patient info: {e}")
                        conn.close()
                        # Ensure coordinator_name is present
                        if 'coordinator_name' not in df.columns:
                            # Try to build mapping from coordinator_id to name
                            id_to_name = {}
                            # First, try from the tasks table itself
                            if 'coordinator_id' in df.columns:
                                # If coordinator_name is present in any row, use it
                                if 'coordinator_name' in df.columns:
                                    mapping = df[['coordinator_id', 'coordinator_name']].dropna().drop_duplicates('coordinator_id')
                                    for _, row in mapping.iterrows():
                                        key = str(row['coordinator_id'])
                                        id_to_name[key] = row['coordinator_name']
                                # Otherwise, fallback to users table
                                if not id_to_name:
                                    coordinators = database.get_users_by_role(36) if hasattr(database, 'get_users_by_role') else []
                                    for c in coordinators:
                                        uid = c.get('user_id')
                                        name = c.get('full_name', c.get('username', 'Unknown'))
                                        if uid is not None:
                                            id_to_name[str(uid)] = name
                                # Add coordinator_name column
                                df['coordinator_name'] = df['coordinator_id'].apply(lambda x: id_to_name.get(str(x), str(x)) if pd.notna(x) else None)

                        with filter_cols[1]:
                            st.markdown("**Coordinator Name**")
                            coord_names = sorted(df['coordinator_name'].dropna().unique()) if 'coordinator_name' in df.columns else []
                            selected_coord = st.selectbox("", ["All"] + coord_names, key="coord_name_selector")
                        with filter_cols[2]:
                            st.markdown("**Patient**")
                            if 'Patient Name' in df.columns:
                                patient_display = df[['patient_id', 'Patient Name']].drop_duplicates().dropna()
                                patient_options = [f"{row['Patient Name']} ({row['patient_id']})" for _, row in patient_display.iterrows()]
                                patient_map = {f"{row['Patient Name']} ({row['patient_id']})": row['patient_id'] for _, row in patient_display.iterrows()}
                            elif 'patient_name' in df.columns:
                                patient_display = df[['patient_id', 'patient_name']].drop_duplicates().dropna()
                                patient_options = [f"{row['patient_name']} ({row['patient_id']})" for _, row in patient_display.iterrows()]
                                patient_map = {f"{row['patient_name']} ({row['patient_id']})": row['patient_id'] for _, row in patient_display.iterrows()}
                            else:
                                patient_options = [str(pid) for pid in sorted(df['patient_id'].dropna().unique())] if 'patient_id' in df.columns else []
                                patient_map = {str(pid): pid for pid in patient_options}
                            selected_patient = st.selectbox("", ["All"] + patient_options, key="patient_selector")

                        # Apply filters
                        filtered_df = df.copy()
                        if selected_coord != "All":
                            filtered_df = filtered_df[filtered_df['coordinator_name'] == selected_coord]
                        if selected_patient != "All":
                            filtered_df = filtered_df[filtered_df['patient_id'] == patient_map[selected_patient]]

                        if not filtered_df.empty:
                            # Only show a fixed set of columns, no dropdown for selection
                            # Move coordinator_name to the leftmost column
                            preferred_order = [
                                'coordinator_name', 'status', 'patient_id', 'patient_name', 'patient_full_name', 'first_name', 'last_name', 'dob',
                                'task_type', 'duration_minutes', 'date', 'notes', 'Patient Name'
                            ]
                            show_cols = [col for col in preferred_order if col in filtered_df.columns]
                            # Prefer patient_name/full_name, else first_name + last_name
                            if 'patient_name' in show_cols:
                                pass
                            elif 'patient_full_name' in show_cols:
                                pass
                            elif 'first_name' in show_cols and 'last_name' in show_cols:
                                # Combine first_name and last_name into a single column
                                filtered_df['Patient Name'] = filtered_df['first_name'].fillna('') + ' ' + filtered_df['last_name'].fillna('')
                                show_cols.append('Patient Name')
                            st.data_editor(filtered_df[show_cols], use_container_width=True, num_rows="dynamic", height=700)
                        else:
                            st.info(f"No data in table {selected_table} after filtering.")
            except Exception as e:
                st.error(f"Error loading coordinator tasks: {e}")
    else:
        show_coordinator_patient_list(user_id, context="default")
        # REMOVED: Onboarding queue statistics and onboarding tasks are not shown in care coordinator dashboard

def show_coordinator_patient_list(user_id, context="default"):
    # Ensure daily_tasks_data is initialized in session state
    if "daily_tasks_data" not in st.session_state:
        st.session_state.daily_tasks_data = [{}]

    # No mapping needed: user_id is coordinator_id

    # Use user_id directly as coordinator_id for all downstream logic
    coordinator_id = user_id
    st.caption(f"[DEBUG] user_id: {user_id} (used as coordinator_id)")

    # Also get user role ids so management roles can see all workflows
    try:
        user_role_ids = get_user_role_ids(user_id) or []
    except Exception:
        user_role_ids = []

    # Use patient_panel via database.get_coordinator_patient_panel_enhanced
    try:
        # Pass user_id directly
        patient_data_list = database.get_coordinator_patient_panel_enhanced(user_id)
    except Exception as e:
        st.error(f"Error fetching patient panel data: {e}")
        patient_data_list = []

    # --- Get patient-wise minutes for this coordinator for the current month from the summary table ---
    import pandas as pd
    from datetime import datetime
    now = datetime.now()
    year = now.year
    month = now.month
    # Try to read the monthly summary table for this coordinator
    try:
        conn = database.get_db_connection()
        table_name = f"coordinator_monthly_summary_{year}_{str(month).zfill(2)}"
        table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
        patient_minutes = {}
        
        if table_exists:
            summary_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            
            if not summary_df.empty and 'patient_id' in summary_df.columns and 'total_minutes' in summary_df.columns:
                for _, row in summary_df.iterrows():
                    pid = row['patient_id']
                    # Normalize patient ID by removing comma for matching
                    normalized_pid = str(pid).replace(', ', ' ')
                    patient_minutes[normalized_pid] = row['total_minutes']
        conn.close()
    except Exception as e:
        st.warning(f"Could not fetch patient minutes from summary table: {e}")
        patient_minutes = {}

    # Attach 'Mins' to each patient in patient_data_list
    for p in patient_data_list:
        pid = p.get('patient_id')
        # Patient IDs are now normalized at the database level
        mins = patient_minutes.get(str(pid) if pid else '')
        p['Mins'] = mins if mins is not None else 0

    # --- Map facility_id to facility_name using modular utility ---
    from src.core_utils import get_facility_id_to_name_map
    facility_id_to_name = get_facility_id_to_name_map(database)
    from src.core_utils import map_facility_id_to_name
    unmapped_facilities = set()
    for p in patient_data_list:
        fid = p.get('current_facility_id')
        facility_name = map_facility_id_to_name(fid, facility_id_to_name)
        # Fallback: if no id or not mapped, try the text field
        if not facility_name:
            fallback_name = p.get('facility')
            if fallback_name and fallback_name not in facility_id_to_name.values():
                unmapped_facilities.add(fallback_name)
            facility_name = fallback_name or 'Unknown'
        p['facility'] = facility_name
    if unmapped_facilities:
        st.warning(f"Unmapped facilities found in patient data: {sorted(unmapped_facilities)}")

    # Always show patient panel, even if empty
    rename_map = {
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'status': 'Status',
        'facility': 'Facility',
        'phone_primary': 'Phone Number',
        'last_visit_date': "Provider's Last Visit Date",
        'provider_name': 'Provider Name',
        'service_type': 'Service Type',
        'POC-A': 'POC-A (Appt Contact)',
        'POC-M': 'POC-M (Medical Contact)',
    }
    required_columns = [
        'Status',
        'First Name',
        'Last Name',
        'Facility',
        'Provider Name',
        "Provider's Last Visit Date",
        'Service Type',
        'Phone Number',
        'POC-A (Appt Contact)',
        'POC-M (Medical Contact)',
        'Mins',
    ]
    # Metrics for active patient counts (show only once, no dropdown)
    allowed_statuses = ['Active', 'Active-Geri', 'Active-PCP']
    total_active = len([p for p in patient_data_list if (p.get('status', '') or '').strip() in allowed_statuses])
    count_geri = len([p for p in patient_data_list if (p.get('status', '') or '').strip() == 'Active-Geri'])
    count_pcp = len([p for p in patient_data_list if (p.get('status', '') or '').strip() == 'Active-PCP'])
    col1, col2, col3 = st.columns(3)
    col1.metric("All Active Patients", total_active)
    col2.metric("Active-Geri Patients", count_geri)
    col3.metric("Active-PCP Patients", count_pcp)

    # Ensure active_patients is defined for downstream workflow and task UI
    active_patients = [p for p in patient_data_list if p.get('status') and str(p.get('status')).strip().startswith('Active')]
    # Prepare patient name list for workflow UI
    active_patient_names = [
        f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        for p in active_patients
    ]

    if patient_data_list:
        # Sort patient_data_list by last_name, then first_name
        patient_data_list = sorted(
            patient_data_list,
            key=lambda p: (str(p.get('last_name', '')).lower(), str(p.get('first_name', '')).lower())
        )
        patients_df = pd.DataFrame(patient_data_list)
        # Ensure rename_map keys exist
        for col in rename_map:
            if col not in patients_df.columns:
                patients_df[col] = ''

        # --- Provider mapping logic ---
        # Map assigned_provider_id to provider name for display
        try:
            providers = database.get_users_by_role(33) or []  # 33 = Care Provider
            provider_map = {p['user_id']: p.get('full_name') or p.get('username') for p in providers}
            provider_map.update({str(k): v for k, v in list(provider_map.items())})
        except Exception:
            provider_map = {}
        provider_id_fields = ['assigned_provider_id', 'provider_user_id', 'assigned_provider_user_id', 'provider_id']
        mapped = False
        for fld in provider_id_fields:
            if fld in patients_df.columns:
                patients_df['provider_name'] = patients_df[fld].map(lambda x: provider_map.get(x) if x in provider_map else provider_map.get(str(x)) if pd.notna(x) else 'Unassigned')
                mapped = True
                break
        if not mapped and 'provider_name' not in patients_df.columns:
            patients_df['provider_name'] = None

        # 'Mins' is now set directly in patient_data_list above

        patients_df = patients_df.rename(columns=rename_map)

        # Make sure all required columns exist and in the right order
        for c in required_columns:
            if c not in patients_df.columns:
                patients_df[c] = '' if c != 'Mins' else 0

        display_df = patients_df[required_columns].copy()
    else:
        # Create empty DataFrame with required columns
        display_df = pd.DataFrame(columns=required_columns)

    st.subheader("Patient Panel")
    st.caption("Columns: Status, First Name, Last Name, Facility, Provider Name, Provider's Last Visit Date, Service Type, Phone Number, POC-A (Appt Contact), POC-M (Medical Contact), Mins")

    st.dataframe(
        display_df,
        height=400,
        use_container_width=True,
        column_config={
            "Status": st.column_config.TextColumn("Status"),
            "First Name": st.column_config.TextColumn("First Name"),
            "Last Name": st.column_config.TextColumn("Last Name"),
            "Facility": st.column_config.TextColumn("Facility"),
            "Provider Name": st.column_config.TextColumn("Provider Name"),
            "Provider's Last Visit Date": st.column_config.DateColumn("Provider's Last Visit Date"),
            "Service Type": st.column_config.TextColumn("Service Type"),
            "POC-A (Appt Contact)": st.column_config.TextColumn("POC-A (Appt Contact)"),
            "POC-M (Medical Contact)": st.column_config.TextColumn("POC-M (Medical Contact)"),
        }
    )

    # --- Restore Workflow Management UI ---
    from src.dashboards.workflow_module import show_workflow_management
    show_workflow_management(
        user_id=user_id,
        coordinator_id=coordinator_id,
        active_patients=active_patient_names,
        user_role_ids=user_role_ids
    )

    # Define available task types for the task entry UI
    task_options = [
        "Phone Call",
        "Care Coordination",
        "Documentation",
        "Patient Follow-up",
        "Provider Communication",
        "Other"
    ]

    # Create task entries (removed timer and orphaned logic, now handled in workflow module)
    for i, task_entry in enumerate(st.session_state.daily_tasks_data):
        st.markdown(f"#### Task Entry {i+1}")
        col1, col2, col3, col4 = st.columns([1, 1.2, 2.2, 1])
        with col1:
            task_entry['date'] = st.date_input(f"Date {i+1}", value=task_entry.get('date', pd.to_datetime('today')), key=f"date_{i}")
        with col2:
            active_patients = [
                p for p in patient_data_list
                if p.get('status') and str(p.get('status')).strip().startswith('Active')
                and str(p.get('coordinator_id', '')) == str(coordinator_id)
            ]
            active_patients = sorted(
                active_patients,
                key=lambda p: (str(p.get('last_name', '')).lower(), str(p.get('first_name', '')).lower())
            )
            patient_names = [
                f"{p.get('first_name', '')} {p.get('last_name', '')} ({p.get('username', '')})".strip()
                for p in active_patients
            ]
            if not patient_names:
                patient_names = ["No active patients assigned to you"]
            task_entry['patient_name'] = st.selectbox(
                f"Patient Name {i+1}",
                patient_names,
                key=f"patient_name_{i}",
                help="Select the patient assigned to you for this task entry"
            )
        with col3:
            task_entry['task_type'] = st.selectbox(f"Task Type {i+1}", task_options, key=f"task_type_{i}", index=0 if task_options else -1)
        with col4:
            task_entry['duration'] = st.number_input(
                "Duration (min)", 
                min_value=1, 
                value=30, 
                key=f"duration_{i}",
                help="Enter duration manually"
            )
        task_entry['notes'] = st.text_area(f"Notes {i+1}", value=task_entry.get('notes', ''), key=f"notes_{i}")
        if st.button(f"Log Task {i+1}", key=f"log_task_{i}"):
            if not (task_entry.get('patient_name') and task_entry.get('task_type') and task_entry.get('duration')):
                st.warning("Please fill in all fields for the task entry.")
        st.markdown("---")
    # (Workflow management UI removed; now handled in workflow_module.py)

def create_workflow_task(coordinator_id, patient_name, workflow_type, priority, notes, estimated_duration):
    # Moved to workflow_utils.py
    from src.utils.workflow_utils import create_workflow_task as _create_workflow_task
    return _create_workflow_task(coordinator_id, patient_name, workflow_type, priority, notes, estimated_duration)

def get_ongoing_workflows(user_id, user_role_ids=None):
    # Moved to workflow_utils.py
    from src.utils.workflow_utils import get_ongoing_workflows as _get_ongoing_workflows
    return _get_ongoing_workflows(user_id, user_role_ids)
