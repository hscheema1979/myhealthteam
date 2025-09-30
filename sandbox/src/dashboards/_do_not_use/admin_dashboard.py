
import streamlit as st
import pandas as pd
import numpy as np
import time
from src import database as db
try:
    # reuse the unfiltered patient summary helper from provider dashboard for consistency
    from src.dashboards.care_provider_dashboard_enhanced import show_unfiltered_patient_summary
except Exception:
    show_unfiltered_patient_summary = None
from datetime import datetime, timedelta
# Mito Sheet import
try:
    from mitosheet.streamlit.v1 import spreadsheet
    MITO_AVAILABLE = True
except ImportError:
    MITO_AVAILABLE = False
def show():
    from src.config.ui_style_config import TextStyle
    st.title("Admin Dashboard")
    user_id = st.session_state.get('user_id', None)

    # New tab order: User Role Management, User Management, Staff Onboarding, Coordinator Tasks, Provider Tasks, Patient Info
    tab_role, tab1, tab_onboard, tab_coord_tasks, tab_prov_tasks, tab3 = st.tabs([
        "User Role Management",
        "User Management", 
        "Staff Onboarding",
        "Coordinator Tasks",
        "Provider Tasks",
        "Patient Info"
    ])
    # --- TAB: Coordinator Tasks ---
    with tab_coord_tasks:
        
        # --- Patient and Coordinator Monthly Summary Tables Side-by-Side ---
        st.divider()
        col_patient, col_coord = st.columns(2)
        with col_patient:
            st.subheader("Patient Monthly Summary (Current Month)")
            try:
                import sqlite3
                import pandas as pd
                conn = db.get_db_connection()
                now = pd.Timestamp.now()
                year = now.year
                month = now.month
                table_name = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
                table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
                if not table_exists:
                    st.info(f"No coordinator tasks table found for current month ({table_name}).")
                else:
                        # Read full table so we can use any patient name columns that may already be present
                        tasks_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                        conn.close()
                        if 'duration_minutes' not in tasks_df.columns or tasks_df['duration_minutes'].dropna().eq(0).all():
                            st.info("No patient summary data available for the current month.")
                        else:
                            df_tasks = tasks_df[['patient_id', 'duration_minutes']].copy()
                            df_tasks = df_tasks[df_tasks['duration_minutes'].notna() & (df_tasks['duration_minutes'] > 0)]
                            patient_summary = df_tasks.groupby('patient_id', dropna=False).agg({'duration_minutes':'sum'}).reset_index()
                            patient_summary = patient_summary.rename(columns={'patient_id':'Patient ID','duration_minutes':'Sum of Minutes'})

                            # Build ID -> name mapping. Prefer names present in the tasks table itself (many task tables include patient names).
                            id_to_name = {}
                            def _safe_key(val):
                                try:
                                    if pd.isna(val):
                                        return None
                                    return str(int(val))
                                except Exception:
                                    return str(val)

                            # Try common name columns in the tasks table
                            if 'patient_name' in tasks_df.columns:
                                mapping = tasks_df[['patient_id', 'patient_name']].dropna().drop_duplicates('patient_id')
                                for _, row in mapping.iterrows():
                                    key = _safe_key(row['patient_id'])
                                    if key:
                                        id_to_name[key] = row['patient_name']
                            elif 'patient_full_name' in tasks_df.columns:
                                mapping = tasks_df[['patient_id', 'patient_full_name']].dropna().drop_duplicates('patient_id')
                                for _, row in mapping.iterrows():
                                    key = _safe_key(row['patient_id'])
                                    if key:
                                        id_to_name[key] = row['patient_full_name']
                            elif 'first_name' in tasks_df.columns and 'last_name' in tasks_df.columns:
                                mapping = tasks_df[['patient_id', 'first_name', 'last_name']].drop_duplicates('patient_id')
                                for _, row in mapping.iterrows():
                                    key = _safe_key(row['patient_id'])
                                    if key:
                                        id_to_name[key] = f"{row.get('first_name','') or ''} {row.get('last_name','') or ''}".strip()

                            # Fallback to patients table if we still don't have names
                            if not id_to_name:
                                patients = db.get_all_patients() if hasattr(db, 'get_all_patients') else []
                                for p in patients:
                                    pid = p.get('patient_id')
                                    if pid is None:
                                        continue
                                    id_to_name[_safe_key(pid)] = f"{p.get('first_name','') or ''} {p.get('last_name','') or ''}".strip()

                            # Normalize patient id column to string keys for mapping
                            patient_summary['Patient ID'] = patient_summary['Patient ID'].apply(lambda x: _safe_key(x) if pd.notna(x) else None)
                            patient_summary['Patient'] = patient_summary['Patient ID'].map(id_to_name).fillna(patient_summary['Patient ID'])
                            patient_summary = patient_summary[['Patient', 'Sum of Minutes']]
                            patient_summary = patient_summary.sort_values('Sum of Minutes', ascending=True)
                            st.write("Sorted by Sum of Minutes (lowest → highest):")
                            try:
                                # Ensure Sum of Minutes is numeric
                                patient_summary['Sum of Minutes'] = pd.to_numeric(patient_summary['Sum of Minutes'], errors='coerce').fillna(0)

                                # Partition into sections to reduce scrolling: red (<40), yellow (40-89), green/blue (>=90)
                                red_df = patient_summary[patient_summary['Sum of Minutes'] < 40].copy()
                                yellow_df = patient_summary[(patient_summary['Sum of Minutes'] >= 40) & (patient_summary['Sum of Minutes'] < 90)].copy()
                                greenblue_df = patient_summary[patient_summary['Sum of Minutes'] >= 90].copy()

                                # Color mapping function used for all sections
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

                                # Display sections inside expanders (collapsed by default to reduce scrolling)
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
                            except Exception:
                                # Fallback if anything goes wrong while splitting or styling
                                st.dataframe(patient_summary, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading patient monthly summary: {e}")
        with col_coord:
            st.subheader("Coordinator Monthly Summary (Current Month)")
            try:
                # Use live aggregation from database helper
                summary_rows = db.get_coordinator_monthly_minutes_live()
                if not summary_rows:
                    st.info("No coordinator summary data available for the current month.")
                else:
                    import pandas as pd
                    df_summary = pd.DataFrame(summary_rows)

                    # Try to get coordinator names from the tasks table first (some tables include coordinator_name)
                    conn = db.get_db_connection()
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
                        coordinators = db.get_users_by_role(36)
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
            conn = db.get_db_connection()
            # List all tables matching coordinator_task_YYYY_MM
            table_query = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'coordinator_task_%' ORDER BY name DESC"
            table_names = [row[0] for row in conn.execute(table_query).fetchall()]
            conn.close()
            if not table_names:
                st.info("No coordinator task tables found.")
            else:
                selected_table = st.selectbox("Select Coordinator Task Table (by month)", table_names)
                if selected_table:
                    conn = db.get_db_connection()
                    df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
                    # If patient_id is present, join with patients table for patient info
                    if 'patient_id' in df.columns:
                        try:
                            patients = db.get_all_patients() if hasattr(db, 'get_all_patients') else []
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
                    if not df.empty:
                        filter_cols = [col for col in ['coordinator_name', 'status', 'task_type'] if col in df.columns]
                        filters = {}
                        for col in filter_cols:
                            options = sorted(df[col].dropna().unique())
                            selected = st.multiselect(f"Filter by {col.replace('_', ' ').title()}", options, default=options)
                            filters[col] = selected
                        filtered_df = df.copy()
                        for col, selected in filters.items():
                            filtered_df = filtered_df[filtered_df[col].isin(selected)]
                        st.data_editor(filtered_df, use_container_width=True, num_rows="dynamic", height=700)
                    else:
                        st.info(f"No data in table {selected_table}.")
        except Exception as e:
            st.error(f"Error loading coordinator tasks: {e}")

    # --- TAB: Provider Tasks ---
    with tab_prov_tasks:
        st.subheader("Provider Tasks Table (Editable, Filterable, Sortable)")
        try:
            # Attempt to get provider tasks from db
            tasks = db.get_provider_tasks() if hasattr(db, 'get_provider_tasks') else []
            tasks_df = pd.DataFrame(tasks)
            if not tasks_df.empty:
                # Filtering widgets
                filter_cols = [col for col in ['provider_name', 'status', 'task_type'] if col in tasks_df.columns]
                filters = {}
                for col in filter_cols:
                    options = sorted(tasks_df[col].dropna().unique())
                    selected = st.multiselect(f"Filter by {col.replace('_', ' ').title()}", options, default=options)
                    filters[col] = selected
                filtered_df = tasks_df.copy()
                for col, selected in filters.items():
                    filtered_df = filtered_df[filtered_df[col].isin(selected)]
                st.data_editor(filtered_df, use_container_width=True, num_rows="dynamic", height=700)
            else:
                st.info("No provider tasks found.")
        except Exception as e:
            st.error(f"Error loading provider tasks: {e}")

        # --- Provider Monthly Summary Table ---
        st.divider()
        st.subheader("Provider Monthly Summary (Current Month)")
        try:
            providers = db.get_users_by_role(33)
            summary_rows = []
            for provider in providers:
                provider_id = provider.get('user_id')
                provider_name = provider.get('full_name', provider.get('username', 'Unknown'))
                # Use get_provider_performance_metrics for monthly data
                monthly_data = db.get_provider_performance_metrics()
                # Find the row for this provider
                provider_row = next((row for row in monthly_data if row.get('full_name') == provider_name), None)
                patients_visited = provider_row.get('patients_visited_this_month', 0) if provider_row else 0
                remaining_visits = provider_row.get('remaining_visits', 0) if provider_row else 0
                summary_rows.append({
                    'Provider': provider_name,
                    'Patients Visited (This Month)': patients_visited,
                    'Remaining Visits': remaining_visits
                })
            if summary_rows:
                df_summary = pd.DataFrame(summary_rows)
                df_summary = df_summary.sort_values('Patients Visited (This Month)', ascending=False)
                st.write("Sorted by Patients Visited (descending):")
                st.dataframe(df_summary, use_container_width=True)
            else:
                st.info("No provider summary data available for the current month.")
        except Exception as e:
            st.error(f"Error loading provider monthly summary: {e}")

    # --- TAB: User Role Management ---
    with tab_role:
        st.subheader(TextStyle.INFO_INDICATOR + " User Role Management")
        st.markdown("### Assign and Remove User Roles")
        users = db.get_all_users() or []
        roles = db.get_all_roles() or []
        roles = [role for role in roles if role['role_name'] != 'Provider']
        role_names = [role['role_name'] for role in roles]
        role_id_map = {role['role_name']: role['role_id'] for role in roles}
        data = []
        for user in users:
            user_id = user['user_id']
            user_roles = db.get_user_roles_by_user_id(user_id)
            user_role_names = [r['role_name'] for r in user_roles]
            row = {
                'user_id': user_id,
                'full_name': user['full_name'],
                'email': user['email'] or '',
                'status': user['status'] or 'Active',
            }
            for role_name in role_names:
                row[f'role_{role_name}'] = role_name in user_role_names
            data.append(row)
        df = pd.DataFrame(data)
        column_config = {
            "user_id": None,
            "full_name": st.column_config.TextColumn("Full Name"),
            "email": st.column_config.TextColumn("Email"),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["Active", "Inactive", "Pending", "Suspended"],
                required=True
            )
        }
        for role_name in role_names:
            column_config[f'role_{role_name}'] = st.column_config.CheckboxColumn(role_name)
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            hide_index=True,
            key="user_role_editor",
            use_container_width=True
        )
        if st.session_state.get("user_role_editor"):
            changes = st.session_state["user_role_editor"]
            if "edited_rows" in changes and changes["edited_rows"]:
                for row_index, changed_cells in changes["edited_rows"].items():
                    user_id = df.iloc[row_index]['user_id']
                    full_name = df.iloc[row_index]['full_name']
                    for col_name, new_value in changed_cells.items():
                        try:
                            if col_name.startswith('role_'):
                                role_name = col_name.replace('role_', '')
                                role_id = role_id_map[role_name]
                                if new_value:
                                    db.add_user_role(user_id, role_id)
                                    st.info(f"{TextStyle.INFO_INDICATOR} Added {role_name} role to {full_name}")
                                else:
                                    db.remove_user_role(user_id, role_id)
                                    st.info(f"{TextStyle.INFO_INDICATOR} Removed {role_name} role from {full_name}")
                            elif col_name == 'status':
                                conn = db.get_db_connection()
                                conn.execute("""
                                    UPDATE users 
                                    SET status = ? 
                                    WHERE user_id = ?
                                """, (new_value, user_id))
                                conn.commit()
                                conn.close()
                                st.info(f"{TextStyle.INFO_INDICATOR} Updated status to {new_value} for {full_name}")
                            elif col_name in ['full_name', 'email']:
                                conn = db.get_db_connection()
                                if col_name == 'full_name':
                                    conn.execute("""
                                        UPDATE users 
                                        SET full_name = ? 
                                        WHERE user_id = ?
                                    """, (new_value, user_id))
                                elif col_name == 'email':
                                    conn.execute("""
                                        UPDATE users 
                                        SET email = ? 
                                        WHERE user_id = ?
                                    """, (new_value, user_id))
                                conn.commit()
                                conn.close()
                                st.info(f"{TextStyle.INFO_INDICATOR} Updated {col_name.replace('_', ' ').title()} for {full_name}")
                        except Exception as e:
                            st.error(f"{TextStyle.INFO_INDICATOR} Error updating {col_name} for {full_name}: {e}")
                time.sleep(1)
                st.rerun()
        st.divider()
        st.markdown("#### Quick Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Refresh User Data"):
                st.rerun()
        with col2:
            if st.button("Export User List"):
                st.info("Export functionality would be implemented here")
        with col3:
            if st.button("Send Status Updates"):
                st.info("Email notification functionality would be implemented here")

    # --- TAB 1: User Management ---
    with tab1:
        st.subheader("User Management Table (All Users and Roles)")
        try:
            users = db.get_all_users()
            users_df = pd.DataFrame(users)
            st.data_editor(users_df, use_container_width=True, num_rows="dynamic")
        except Exception as e:
            st.error(f"Error loading user data: {e}")

    # --- TAB: Staff Onboarding ---
    with tab_onboard:
        st.subheader(TextStyle.INFO_INDICATOR + " Staff Onboarding Management")
        st.info("**Admin Only**: Staff onboarding and user registration is restricted to administrators")
        st.markdown("### New User Registration")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("Create new users and assign roles (Providers, Coordinators, etc.)")
            with st.form("new_user_form"):
                st.markdown("##### User Information")
                first_name = st.text_input("First Name*", key="new_first_name")
                last_name = st.text_input("Last Name*", key="new_last_name")
                email = st.text_input("Email*", key="new_email")
                username = st.text_input("Username*", key="new_username")
                password = st.text_input("Password*", type="password", key="new_password")
                st.markdown("##### Role Assignment")
                try:
                    roles = db.get_user_roles()
                    role_options = [role['role_name'] for role in roles if role['role_name'] not in ['LC', 'CPM', 'CM']]
                    selected_role = st.selectbox("Primary Role*", role_options, key="new_role")
                    role_descriptions = {
                        'CP': 'Care Provider - Delivers direct patient care',
                        'CC': 'Care Coordinator - Coordinates patient care plans',
                        'ADMIN': 'Administrator - System administration and management',
                        'OT': 'Onboarding Team - Patient intake and onboarding',
                        'DATA ENTRY': 'Data Entry - Data entry and documentation'
                    }
                    if selected_role and selected_role in role_descriptions:
                        st.info(role_descriptions[selected_role])
                except Exception as e:
                    st.error(f"Error loading roles: {e}")
                    selected_role = None
                submitted = st.form_submit_button("Create New User", use_container_width=True)
                if submitted:
                    if all([first_name, last_name, email, username, password, selected_role]):
                        try:
                            db.add_user(username, password, first_name, last_name, email, selected_role)
                            st.success(f"Successfully created user: {first_name} {last_name} ({selected_role})")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating user: {e}")
                    else:
                        st.error("Please fill in all required fields")

    # --- TAB 2: Patient Assignments ---
    # with tab2:
    #     st.subheader("Patient Assignments Table (All Assignments)")
    #     try:
    #         assignments = db.get_all_patient_assignments()
    #         assignments_df = pd.DataFrame(assignments)
    #         table_height = 900  # Large value to fill most browser windows
    #         if not assignments_df.empty and 'patient_id' in assignments_df.columns:
    #             patients = db.get_all_patients() if hasattr(db, 'get_all_patients') else []
    #             patients_df = pd.DataFrame(patients)
    #             required_cols = {'patient_id', 'first_name', 'last_name', 'dob'}
    #             if not patients_df.empty and required_cols.issubset(patients_df.columns):
    #                 merged_df = assignments_df.merge(
    #                     patients_df[['patient_id', 'first_name', 'last_name', 'dob']],
    #                     on='patient_id', how='left'
    #                 )
    #                 # Add Patient Name column
    #                 if all(col in merged_df.columns for col in ['first_name', 'last_name']):
    #                     merged_df['Patient Name'] = merged_df['first_name'].fillna('') + ' ' + merged_df['last_name'].fillna('')
    #                 # Order columns: last_name, first_name, dob, Patient Name, then others
    #                 first_cols = [col for col in ['last_name', 'first_name', 'dob', 'Patient Name'] if col in merged_df.columns]
    #                 other_cols = [c for c in merged_df.columns if c not in first_cols]
    #                 merged_df = merged_df[first_cols + other_cols]
    #                 st.data_editor(merged_df, use_container_width=True, num_rows="dynamic", height=table_height)
    #             else:
    #                 st.data_editor(assignments_df, use_container_width=True, num_rows="dynamic", height=table_height)
    #         else:
    #             st.data_editor(assignments_df, use_container_width=True, num_rows="dynamic", height=table_height)
    #     except Exception as e:
    #         st.error(f"Error loading assignment data: {e}")

    # --- TAB 3: Patient Info ---
    with tab3:
        st.subheader("Patient Info Table (All Patient Data, Assignments)")
        try:
            # Provide a quick unfiltered patient summary (from patient_panel) for admins
            # Render the full patient_panel (no columns filtered) and add last-visit based
            # color-coding for patient name columns similar to the provider view.
            try:
                patients = db.get_all_patient_panel() if hasattr(db, 'get_all_patient_panel') else []
                patients_df = pd.DataFrame(patients)
                if patients_df.empty:
                    st.info("No patients found in patient_panel.")
                else:
                    # Prefer sorting by last_name then first_name when available
                    sort_cols = [c for c in ['last_name', 'first_name'] if c in patients_df.columns]
                    if sort_cols:
                        patients_df = patients_df.sort_values(by=sort_cols, na_position='last')

                    # Normalize last-visit column to a consistent 'Last Visit Date' string column
                    possible_last_visit_cols = ['last_visit_date', 'last_visit', 'last_visit_dt', 'last_visit_at', 'last_visit_timestamp', 'most_recent_visit', 'last_visit_date_iso']
                    found_last = None
                    for c in possible_last_visit_cols:
                        if c in patients_df.columns:
                            found_last = c
                            break

                    def _format_date(val):
                        try:
                            ts = pd.to_datetime(val, errors='coerce')
                            return ts.strftime('%Y-%m-%d') if not pd.isna(ts) else None
                        except Exception:
                            return None

                    if found_last:
                        patients_df['Last Visit Date'] = patients_df[found_last].apply(_format_date)
                    else:
                        # If no last-visit column exists, create an empty Last Visit Date column
                        patients_df['Last Visit Date'] = None

                    import datetime as _dt

                    def color_patient_name(row):
                        color = ''
                        last_visit = row.get('Last Visit Date')
                        today = _dt.datetime.now().date()
                        if last_visit:
                            try:
                                last_visit_dt = pd.to_datetime(last_visit, errors='coerce')
                                if not pd.isna(last_visit_dt):
                                    last_visit_dt = last_visit_dt.date()
                                    delta = (today - last_visit_dt).days
                                    if delta > 60:
                                        color = 'background-color: #ffcccc; color: #a00;'
                                    elif 30 < delta <= 60:
                                        color = 'background-color: #fff3cd; color: #a67c00;'
                                    elif 0 <= delta <= 30:
                                        color = 'background-color: #d4edda; color: #155724;'
                            except Exception:
                                pass
                        return color

                    # Decide which name columns to style (support both lowercase and title-case names)
                    name_cols = []
                    for cand in ['First Name', 'Last Name', 'first_name', 'last_name', 'patient_first_name', 'patient_last_name']:
                        if cand in patients_df.columns:
                            name_cols.append(cand)

                    def style_names(df):
                        # apply returns a DataFrame of same shape with CSS for each cell
                        def _row_style(row):
                            styles = []
                            # compute the style for the row once
                            row_style = color_patient_name(row)
                            for col in df.columns:
                                if col in name_cols:
                                    styles.append(row_style)
                                else:
                                    styles.append('')
                            return styles
                        return df.style.apply(lambda r: _row_style(r), axis=1)

                    # Display full table with coloring applied to name columns
                    try:
                        styled = style_names(patients_df)
                        st.dataframe(styled, height=900, use_container_width=True)
                    except Exception:
                        # If styling fails for very wide DF or other reasons, fall back to plain display
                        st.dataframe(patients_df, height=900, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading patient_panel: {e}")

        #     merged_df = pd.DataFrame(merged)
        #     table_height = 600  # Large value to fill most browser windows
        #     # Reorder columns: after 'facility', show 'provider_name', 'coordinator_name', then the rest
        #     if not merged_df.empty:
        #         cols = list(merged_df.columns)
        #         # Find indices
        #         fac_idx = cols.index('facility') if 'facility' in cols else -1
        #         prov_idx = cols.index('provider_name') if 'provider_name' in cols else -1
        #         coord_idx = cols.index('coordinator_name') if 'coordinator_name' in cols else -1
        #         # Remove provider/coordinator if present
        #         for c in ['provider_name', 'coordinator_name']:
        #             if c in cols:
        #                 cols.remove(c)
        #         # Insert after facility
        #         insert_at = fac_idx + 1 if fac_idx != -1 else 0
        #         for c in ['coordinator_name', 'provider_name'][::-1]:
        #             if c in merged_df.columns:
        #                 cols.insert(insert_at, c)
        #         merged_df = merged_df[cols]
        #     st.data_editor(merged_df, use_container_width=True, num_rows="dynamic", height=table_height)
        except Exception as e:
            st.error(f"Error loading patient data: {e}")

    # ...existing code...
