import streamlit as st
from src.dashboards.dashboard_display_config import ST_DF_AUTOSIZE_COLUMNS
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

def _apply_patient_info_edits_admin(edited_df, original_df):
    """Apply patient info edits to database"""
    import pandas as pd
    from src import database as _db
    if edited_df is None or original_df is None:
        return
    if "patient_id" not in edited_df.columns:
        return
    original_by_id = {str(r["patient_id"]): r for _, r in original_df.iterrows() if pd.notna(r.get("patient_id"))}
    conn = _db.get_db_connection()
    try:
        for _, row in edited_df.iterrows():
            pid = str(row.get("patient_id"))
            if not pid or pid not in original_by_id:
                continue
            orig = original_by_id[pid]
            changed = {}
            for col in edited_df.columns:
                if col == "patient_id":
                    continue
                if str(row.get(col)) != str(orig.get(col)):
                    changed[col] = row.get(col)
            if not changed:
                continue
            patient_cols = [c[1] for c in conn.execute("PRAGMA table_info('patients')").fetchall()]
            set_parts = []
            params = []
            for k, v in changed.items():
                if k in patient_cols:
                    set_parts.append(f"{k} = ?")
                    params.append(v)
            if set_parts:
                params.append(pid)
                conn.execute(f"UPDATE patients SET {', '.join(set_parts)}, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?", tuple(params))
            panel_cols = [c[1] for c in conn.execute("PRAGMA table_info('patient_panel')").fetchall()]
            set_parts = []
            params = []
            for k, v in changed.items():
                if k in panel_cols:
                    set_parts.append(f"{k} = ?")
                    params.append(v)
            if set_parts:
                params.append(pid)
                conn.execute(f"UPDATE patient_panel SET {', '.join(set_parts)}, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?", tuple(params))
        conn.commit()
    finally:
        conn.close()

def show():
    global pd  # Explicitly declare pd as global to prevent UnboundLocalError
    from src.config.ui_style_config import TextStyle
    st.title("Admin Dashboard")
    user_id = st.session_state.get('user_id', None)

    # New tab order: User Role Management, User Management, Staff Onboarding, Coordinator Tasks, Provider Tasks, Patient Info, Billing Report, For Testing
    tab_role, tab1, tab_onboard, tab_coord_tasks, tab_prov_tasks, tab3, tab_billing, tab_test = st.tabs([
        "User Role Management",
        "User Management", 
        "Staff Onboarding",
        "Coordinator Tasks",
        "Provider Tasks",
        "Patient Info",
        "Billing Report",
        "For Testing"
    ])

    # --- TAB: User Role Management ---
    with tab_role:
        st.subheader(TextStyle.INFO_INDICATOR + " User Role Management")
        st.markdown("### Assign and Remove User Roles")
        users = db.get_all_users() or []
        roles = db.get_all_roles() or []
        # Filter out roles that are no longer used as separate roles
        roles = [role for role in roles if role['role_name'] not in ['Provider', 'INITIAL_TV_PROVIDER']]
        role_names = [role['role_name'] for role in roles]
        role_id_map = {role['role_name']: role['role_id'] for role in roles}
        data = []
        for user in users:
            user_id = user['user_id']
            user_roles = db.get_user_roles_by_user_id(user_id)
            user_role_names = [r['role_name'] for r in user_roles]
            user_role_ids = [r['role_id'] for r in user_roles]
            row = {
                'user_id': user_id,
                'full_name': user['full_name'],
                'email': user['email'] or '',
                'status': user['status'] or 'Active',
                'can_edit_patient_info': 34 in user_role_ids,  # Admin role (34) can edit patient info
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
            ),
            "can_edit_patient_info": st.column_config.CheckboxColumn("🔧 Edit Patient Info", help="Allow user to edit patient information - Grant admin role automatically")
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
                            elif col_name == 'can_edit_patient_info':
                                if new_value:
                                    # Grant admin access (role ID 34)
                                    db.add_user_role(user_id, 34)
                                    st.info(f"{TextStyle.INFO_INDICATOR} Granted edit patient info access to {full_name}")
                                else:
                                    # Remove admin access (role ID 34)
                                    existing_roles = db.get_user_roles_by_user_id(user_id)
                                    if len(existing_roles) > 1 or (len(existing_roles) == 1 and existing_roles[0]['role_name'] != 'ADMIN'):
                                        db.remove_user_role(user_id, 34)
                                        st.info(f"{TextStyle.INFO_INDICATOR} Removed edit patient info access from {full_name}")
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
            if st.button("🔄 Refresh User Data"):
                st.rerun()
        with col2:
            if st.button("📊 Export User List"):
                st.info("Export functionality would be implemented here")
        with col3:
            if st.button("📧 Send Status Updates"):
                st.info("Email notification functionality would be implemented here")

    # --- TAB 1: User Management ---
    with tab1:
        st.subheader("User Management Table (All Users and Roles)")
        try:
            users = db.get_all_users()
            users_df = pd.DataFrame(users)
            
            # Configure columns for the user management table
            column_config = {
                "user_id": None,
                "username": st.column_config.TextColumn("Username"),
                "full_name": st.column_config.TextColumn("Full Name"),
                "email": st.column_config.TextColumn("Email"),
                "status": st.column_config.SelectboxColumn("Status", options=["active", "inactive", "pending"], required=True),
                "hire_date": st.column_config.DateColumn("Hire Date")
            }
            
            edited_df = st.data_editor(
                users_df, 
                column_config=column_config,
                use_container_width=True, 
                num_rows="dynamic",
                key="user_management_editor"
            )
                        
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

    # --- TAB: Coordinator Tasks ---
    with tab_coord_tasks:
        
        # --- Month Selection ---
        import calendar
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Get current date
            now = pd.Timestamp.now()
            current_year = int(now.year)
            current_month = int(now.month)
            
            # Get available months from coordinator_tasks tables
            conn = db.get_db_connection()
            available_tables = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'coordinator_tasks_20%'
                ORDER BY name DESC
            """).fetchall()
            conn.close()
            
            available_months = []
            for table in available_tables:
                table_name = table[0]
                try:
                    # Extract year and month from table name (coordinator_tasks_YYYY_MM)
                    parts = table_name.split('_')
                    if len(parts) >= 3:
                        year = int(parts[2])
                        month = int(parts[3])
                        available_months.append((year, month))
                except:
                    continue
            
            # Sort by year, month descending (most recent first)
            available_months.sort(reverse=True)
            
            # Create month options for selectbox
            month_options = []
            month_values = []
            for year, month in available_months:
                month_name = calendar.month_name[month]
                option_text = f"{month_name} {year}"
                month_options.append(option_text)
                month_values.append((year, month))
            
            # Default to current month if available, otherwise first available
            default_index = 0
            for i, (year, month) in enumerate(month_values):
                if year == current_year and month == current_month:
                    default_index = i
                    break
            
            if month_options:
                selected_month_text = st.selectbox(
                    "Select Month:",
                    options=month_options,
                    index=default_index
                )
                selected_year, selected_month = month_values[month_options.index(selected_month_text)]
            else:
                st.warning("No coordinator tasks data available")
                selected_year, selected_month = current_year, current_month
        
        with col2:
            st.markdown(f"### Coordinator Tasks - {calendar.month_name[selected_month]} {selected_year}")
        
        # --- Coordinator Tasks: Total Minutes Selected Month Header ---
        table_name = f"coordinator_tasks_{selected_year}_{selected_month:02d}"
        conn = db.get_db_connection()
        table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
        
        if table_exists:
            total_minutes_query = f"SELECT SUM(duration_minutes) as total FROM {table_name} WHERE duration_minutes IS NOT NULL"
            total_result = conn.execute(total_minutes_query).fetchone()
            total_minutes = total_result[0] if total_result and total_result[0] else 0
            st.markdown(f"### Total Minutes {calendar.month_name[selected_month]} {selected_year}: **{int(total_minutes):,}**")
        else:
            st.markdown(f"### Total Minutes {calendar.month_name[selected_month]} {selected_year}: _No data available_")
        
        conn.close()
        # --- Patient and Coordinator Monthly Summary Tables Side-by-Side ---
        st.divider()
        col_patient, col_coord = st.columns(2)
        with col_patient:
            st.subheader(f"Patient Monthly Summary ({calendar.month_name[selected_month]} {selected_year})")
            try:
                if table_exists:
                    conn = db.get_db_connection()
                    
                    # Get patient data with billing codes for selected month
                    patient_query = f"""
                    SELECT 
                        p.patient_id,
                        (p.first_name || ' ' || p.last_name) as patient_name,
                        ct.task_type as billing_code,
                        SUM(ct.duration_minutes) as total_minutes
                    FROM {table_name} ct
                    JOIN patients p ON ct.patient_id = p.patient_id
                    WHERE ct.duration_minutes IS NOT NULL
                    GROUP BY p.patient_id, p.first_name, p.last_name, ct.task_type
                    ORDER BY p.patient_id, ct.task_type
                    """
                    
                    patient_rows = conn.execute(patient_query).fetchall()
                    conn.close()
                    
                    if patient_rows:
                        df_patients = pd.DataFrame(patient_rows, columns=[
                            'patient_id', 'patient_name', 'billing_code', 'total_minutes'
                        ])
                        
                        # Ensure total_minutes is numeric
                        df_patients['total_minutes'] = pd.to_numeric(df_patients['total_minutes'], errors='coerce').fillna(0)
                        
                        # Create patient totals (sum across all billing codes)
                        patient_totals = df_patients.groupby(['patient_id', 'patient_name'])['total_minutes'].sum().reset_index()
                        patient_totals = patient_totals.sort_values('total_minutes', ascending=True)  # lowest to highest
                        patient_totals.rename(columns={'total_minutes': 'Sum of Minutes'}, inplace=True)
                        
                        # Color coding function
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
                        
                        # Partition into sections
                        red_df = patient_totals[patient_totals['Sum of Minutes'] < 40].copy()
                        yellow_df = patient_totals[(patient_totals['Sum of Minutes'] >= 40) & (patient_totals['Sum of Minutes'] < 90)].copy()
                        greenblue_df = patient_totals[patient_totals['Sum of Minutes'] >= 90].copy()
                        
                        st.write("Sorted by Sum of Minutes (lowest → highest):")
                        
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
                        
                        # Add billing code breakdown section
                        st.markdown("---")
                        st.markdown("**Billing Code Breakdown:**")
                        
                        # Show detailed breakdown by billing code
                        df_billing_display = df_patients[['patient_name', 'billing_code', 'total_minutes']].copy()
                        df_billing_display.rename(columns={
                            'patient_name': 'Patient Name',
                            'billing_code': 'Billing Code',
                            'total_minutes': 'Total Minutes'
                        }, inplace=True)
                        
                        st.dataframe(df_billing_display, use_container_width=True)
                        
                    else:
                        st.info("No patient data available for this month.")
            except Exception as e:
                st.error(f"Error loading patient monthly summary: {e}")
        with col_coord:
            st.subheader(f"Coordinator Monthly Summary ({calendar.month_name[selected_month]} {selected_year})")
            try:
                if table_exists:
                    conn = db.get_db_connection()
                    
                    # Get coordinator summary for selected month
                    coordinator_query = f"""
                    SELECT 
                        ct.coordinator_id,
                        SUM(ct.duration_minutes) as total_minutes
                    FROM {table_name} ct
                    WHERE ct.duration_minutes IS NOT NULL
                    GROUP BY ct.coordinator_id
                    ORDER BY total_minutes ASC
                    """
                    
                    coordinator_rows = conn.execute(coordinator_query).fetchall()
                    
                    if coordinator_rows:
                        df_summary = pd.DataFrame(coordinator_rows, columns=['coordinator_id', 'total_minutes'])
                        
                        # Get coordinator names
                        id_to_name = {}
                        def _safe_key(val):
                            try:
                                if pd.isna(val):
                                    return None
                                return str(int(val))
                            except Exception:
                                return str(val)

                        # Try to get coordinator names from the tasks table first
                        try:
                            tasks_df = pd.read_sql_query(f"SELECT coordinator_id, coordinator_name FROM {table_name} WHERE coordinator_name IS NOT NULL", conn)
                            if not tasks_df.empty:
                                mapping = tasks_df.drop_duplicates('coordinator_id')
                                for _, row in mapping.iterrows():
                                    key = _safe_key(row['coordinator_id'])
                                    if key:
                                        id_to_name[key] = row['coordinator_name']
                        except Exception:
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

                        # Map coordinator names
                        df_summary['coord_key'] = df_summary['coordinator_id'].apply(lambda x: _safe_key(x) if pd.notna(x) else None)
                        df_summary['Coordinator'] = df_summary['coord_key'].map(id_to_name).fillna(df_summary['coord_key'])
                        df_summary = df_summary[['Coordinator', 'total_minutes']]
                        df_summary = df_summary.rename(columns={'total_minutes': 'Sum of Minutes'})
                        df_summary = df_summary.sort_values('Sum of Minutes', ascending=True)
                        st.write("Sorted by Sum of Minutes (lowest → highest):")
                        st.dataframe(df_summary, use_container_width=True)
                    else:
                        st.info("No coordinator summary data available for this month.")
                else:
                    st.info("No coordinator summary data available for this month.")
            except Exception as e:
                st.error(f"Error loading coordinator monthly summary: {e}")
            st.subheader(f"Coordinator Tasks Table - {calendar.month_name[selected_month]} {selected_year} (Editable, Filterable, Sortable)")
        try:
            # Use the selected month from above
            selected_table = table_name  # This is already defined from the month selection above
            
            if table_exists:
                # Load the selected table for filtering and display
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
                            coordinators = db.get_users_by_role(36) if hasattr(db, 'get_users_by_role') else []
                            for c in coordinators:
                                uid = c.get('user_id')
                                name = c.get('full_name', c.get('username', 'Unknown'))
                                if uid is not None:
                                    id_to_name[str(uid)] = name
                        # Add coordinator_name column
                        df['coordinator_name'] = df['coordinator_id'].apply(lambda x: id_to_name.get(str(x), str(x)) if pd.notna(x) else None)

                # Create filter columns
                filter_cols = st.columns(3)
                
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

        # --- Provider Patient Visit Breakdown ---
        st.divider()
        st.subheader("Provider Patient Visit Breakdown")
        try:
            # Get patient data for visit breakdown analysis
            patients = db.get_all_patient_panel() if hasattr(db, 'get_all_patient_panel') else []
            patients_df = pd.DataFrame(patients)
            
            if not patients_df.empty:
                # Use the same robust date processing logic as Patient Info tab
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
                    patients_df['Last Visit Date'] = None

                # If many rows are missing Last Visit Date, try to infer from task tables
                def _fill_missing_last_visit_from_tasks(df, db):
                    try:
                        # Collect patient ids that are missing a last visit
                        pids = df.loc[df['Last Visit Date'].isna(), 'patient_id'].dropna().unique().tolist()
                        if not pids:
                            return {}

                        # Prepare placeholders for IN clause
                        placeholders = ','.join(['?'] * len(pids))

                        # Candidate queries from coordinator_tasks and provider_tasks using common date columns
                        select_templates = [
                            f"SELECT patient_id, date(task_date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(activity_date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(service_date) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(date) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(dos) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})"
                        ]

                        union_sql = '\nUNION ALL\n'.join(select_templates)
                        final_sql = f"WITH dates AS ({union_sql}) SELECT patient_id, MAX(dt) as last_visit FROM dates WHERE dt IS NOT NULL GROUP BY patient_id"

                        # params need to be repeated for each select template
                        params = pids * len(select_templates)

                        conn = db.get_db_connection()
                        try:
                            rows = conn.execute(final_sql, params).fetchall()
                        finally:
                            conn.close()

                        result = {}
                        for r in rows:
                            try:
                                # r[0] = patient_id, r[1] = last_visit (YYYY-MM-DD or None)
                                if r[1]:
                                    result[r[0]] = str(r[1])
                            except Exception:
                                continue
                        return result
                    except Exception:
                        return {}

                # Attempt to enrich missing Last Visit Dates from task tables
                try:
                    inferred = _fill_missing_last_visit_from_tasks(patients_df, db)
                    if inferred:
                        def _maybe_fill(row):
                            if row.get('Last Visit Date'):
                                return row.get('Last Visit Date')
                            pid = row.get('patient_id')
                            if pid in inferred:
                                return inferred[pid]
                            return None
                        patients_df['Last Visit Date'] = patients_df.apply(_maybe_fill, axis=1)
                except Exception:
                    pass

                import datetime as _dt
                today = _dt.datetime.now().date()

                def get_delta(row):
                    last_visit = row.get('Last Visit Date')
                    if last_visit:
                        try:
                            last_visit_dt = pd.to_datetime(last_visit, errors='coerce')
                            if not pd.isna(last_visit_dt):
                                last_visit_dt = last_visit_dt.date()
                                return (today - last_visit_dt).days
                        except Exception:
                            return None
                    return None

                patients_df['days_since_last_visit'] = patients_df.apply(get_delta, axis=1)
                
                # Create visit category dataframes
                seen_30 = patients_df[(patients_df['days_since_last_visit'] >= 0) & (patients_df['days_since_last_visit'] <= 30)].copy()
                seen_31_60 = patients_df[(patients_df['days_since_last_visit'] > 30) & (patients_df['days_since_last_visit'] <= 60)].copy()
                not_seen_60 = patients_df[(patients_df['days_since_last_visit'] > 60) | (patients_df['days_since_last_visit'].isna())].copy()

                # Columns to show in breakdown tables
                breakdown_cols = [col for col in ['status', 'patient_id', 'first_name', 'last_name', 'dob', 'provider_name', 'coordinator_name', 'goc', 'code', 'Last Visit Date', 'last_visit_service_type'] if col in patients_df.columns]

                def show_styled_table(df, height):
                    try:
                        # Use the same color mapping logic as Patient Info tab
                        def color_patient_name(row):
                            color = ''
                            delta = row.get('days_since_last_visit')
                            if delta is not None:
                                if delta > 60:
                                    color = 'background-color: #ffcccc; color: #a00;'
                                elif 30 < delta <= 60:
                                    color = 'background-color: #fff3cd; color: #a67c00;'
                                elif 0 <= delta <= 30:
                                    color = 'background-color: #d4edda; color: #155724;'
                            return color

                        # Decide which name columns to style (support both lowercase and title-case names)
                        name_cols = []
                        for cand in ['First Name', 'Last Name', 'first_name', 'last_name', 'patient_first_name', 'patient_last_name']:
                            if cand in df.columns:
                                name_cols.append(cand)

                        def style_names(df):
                            def _row_style(row):
                                styles = []
                                row_style = color_patient_name(row)
                                for col in df.columns:
                                    if col in name_cols:
                                        styles.append(row_style)
                                    else:
                                        styles.append('')
                                return styles
                            return df.style.apply(lambda r: _row_style(r), axis=1)
                        
                        styled = style_names(df[breakdown_cols])
                        st.dataframe(styled, height=height, use_container_width=True)
                    except Exception:
                        st.dataframe(df[breakdown_cols], height=height, use_container_width=True)

                provider_col = 'provider_name' if 'provider_name' in patients_df.columns else None
                if provider_col:
                    # Create provider statistics summary table
                    st.markdown("##### Provider Statistics Summary")
                    
                    # Calculate stats for each provider across all categories
                    provider_stats = []
                    all_providers = set()
                    
                    # Collect all unique providers (filter out None/NaN values)
                    for _, df_cat in [("seen_30", seen_30), ("seen_31_60", seen_31_60), ("not_seen_60", not_seen_60)]:
                        if not df_cat.empty and provider_col in df_cat.columns:
                            # Filter out None and NaN values
                            valid_providers = df_cat[provider_col].dropna().unique()
                            valid_providers = [p for p in valid_providers if p is not None and str(p).strip() != '']
                            all_providers.update(valid_providers)
                    
                    # Calculate counts for each provider
                    for provider in sorted(all_providers):
                        # Use safe filtering that handles None values
                        seen_30_count = len(seen_30[seen_30[provider_col].fillna('') == provider]) if not seen_30.empty and provider_col in seen_30.columns else 0
                        seen_31_60_count = len(seen_31_60[seen_31_60[provider_col].fillna('') == provider]) if not seen_31_60.empty and provider_col in seen_31_60.columns else 0
                        not_seen_60_count = len(not_seen_60[not_seen_60[provider_col].fillna('') == provider]) if not not_seen_60.empty and provider_col in not_seen_60.columns else 0
                        total_count = seen_30_count + seen_31_60_count + not_seen_60_count
                        
                        provider_stats.append({
                            'Provider': provider,
                            '🟢 Seen ≤30 days': seen_30_count,
                            '🟡 Seen 31-60 days': seen_31_60_count,
                            '🔴 Not seen >60 days': not_seen_60_count,
                            'Total Patients': total_count
                        })
                    
                    if provider_stats:
                        stats_df = pd.DataFrame(provider_stats)
                        st.dataframe(stats_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No provider data available.")
                    
                    st.markdown("---")
                    for label, df_cat in [
                        ("Patients seen in the last 30 days", seen_30),
                        ("Patients seen 1mo <> 2mo", seen_31_60),
                        ("Patients NOT seen by Regional Provider in 2mo", not_seen_60)
                    ]:
                        # Use expandable sections with color-coded titles
                        if "last 30 days" in label:
                            # Green for recent visits (good)
                            expander_title = f"🟢 {label} by Provider"
                            color_style = "background-color: #d4edda; color: #155724;"
                        elif "1mo <> 2mo" in label:
                            # Yellow for moderate delay
                            expander_title = f"🟡 {label} by Provider"
                            color_style = "background-color: #fff3cd; color: #a67c00;"
                        else:
                            # Red for long delays (concerning)
                            expander_title = f"🔴 {label} by Provider"
                            color_style = "background-color: #ffcccc; color: #a00;"
                        
                        with st.expander(expander_title, expanded=False):
                            grouped = df_cat.groupby(provider_col)
                            if grouped.ngroups == 0:
                                st.info(f"No providers have patients in this category.")
                            else:
                                for prov, prov_df in grouped:
                                    # Use subheader instead of nested expander
                                    st.markdown(f"**Provider: {prov}** ({len(prov_df)} patients)")
                                    if prov_df.empty:
                                        st.info("No patients for this provider in this category.")
                                    else:
                                        show_styled_table(prov_df, 300)
                                    st.markdown("---")  # Add separator between providers
                else:
                    st.info("Provider information not available in patient data.")
            else:
                st.info("No patient data available for visit breakdown analysis.")
        except Exception as e:
            st.error(f"Error loading provider patient visit breakdown: {e}")

    # --- TAB 3: Patient Info ---
    with tab3:
        st.subheader("Patient Info Table (All Patient Data, Assignments)")
        
        # --- Search Filter (at the top) ---
        st.markdown("### Search Patients")
        search_term = st.text_input("Search by Name or ID", key="patient_info_search_input")
        
        # --- Enable Editing Control ---
        editable_admin = st.checkbox("Enable editing", value=False, key="admin_patient_info_editable")
        
        # Apply search filter immediately after data loading
        try:
            patients = db.get_all_patient_panel() if hasattr(db, 'get_all_patient_panel') else []
            patients_df = pd.DataFrame(patients)
            if patients_df.empty:
                st.info("No patients found in patient_panel.")
            else:
                # Apply search filter
                if search_term:
                    search_term_lower = search_term.lower()
                    # Filter by first_name, last_name, or patient_id
                    mask = pd.Series(False, index=patients_df.index)
                    
                    if 'first_name' in patients_df.columns:
                        mask |= patients_df['first_name'].fillna('').astype(str).str.lower().str.contains(search_term_lower)
                    if 'last_name' in patients_df.columns:
                        mask |= patients_df['last_name'].fillna('').astype(str).str.lower().str.contains(search_term_lower)
                    if 'patient_id' in patients_df.columns:
                        mask |= patients_df['patient_id'].fillna('').astype(str).str.lower().str.contains(search_term_lower)
                    
                    patients_df = patients_df[mask]
                    
                    if patients_df.empty:
                        st.warning(f"No patients found matching '{search_term}'")
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
                    patients_df['Last Visit Date'] = None

                # If many rows are missing Last Visit Date, try to infer from task tables
                def _fill_missing_last_visit_from_tasks(df, db):
                    try:
                        # Collect patient ids that are missing a last visit
                        pids = df.loc[df['Last Visit Date'].isna(), 'patient_id'].dropna().unique().tolist()
                        if not pids:
                            return {}

                        # Prepare placeholders for IN clause
                        placeholders = ','.join(['?'] * len(pids))

                        # Candidate queries from coordinator_tasks and provider_tasks using common date columns
                        union_selects = []
                        select_templates = [
                            f"SELECT patient_id, date(task_date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(activity_date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(service_date) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(date) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(dos) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})"
                        ]

                        union_sql = '\nUNION ALL\n'.join(select_templates)
                        final_sql = f"WITH dates AS ({union_sql}) SELECT patient_id, MAX(dt) as last_visit FROM dates WHERE dt IS NOT NULL GROUP BY patient_id"

                        # params need to be repeated for each select template
                        params = pids * len(select_templates)

                        conn = db.get_db_connection()
                        try:
                            rows = conn.execute(final_sql, params).fetchall()
                        finally:
                            conn.close()

                        result = {}
                        for r in rows:
                            try:
                                # r[0] = patient_id, r[1] = last_visit (YYYY-MM-DD or None)
                                if r[1]:
                                    result[r[0]] = str(r[1])
                            except Exception:
                                continue
                        return result
                    except Exception:
                        return {}

                # Attempt to enrich missing Last Visit Dates from task tables
                try:
                    inferred = _fill_missing_last_visit_from_tasks(patients_df, db)
                    if inferred:
                        def _maybe_fill(row):
                            if row.get('Last Visit Date'):
                                return row.get('Last Visit Date')
                            pid = row.get('patient_id')
                            if pid in inferred:
                                return inferred[pid]
                            return None
                        patients_df['Last Visit Date'] = patients_df.apply(_maybe_fill, axis=1)
                except Exception:
                    pass

                import datetime as _dt
                today = _dt.datetime.now().date()

                def get_delta(row):
                    last_visit = row.get('Last Visit Date')
                    if last_visit:
                        try:
                            last_visit_dt = pd.to_datetime(last_visit, errors='coerce')
                            if not pd.isna(last_visit_dt):
                                last_visit_dt = last_visit_dt.date()
                                return (today - last_visit_dt).days
                        except Exception:
                            return None
                    return None

                patients_df['days_since_last_visit'] = patients_df.apply(get_delta, axis=1)

                # Color mapping for patient name columns
                def color_patient_name(row):
                    color = ''
                    delta = row.get('days_since_last_visit')
                    if delta is not None:
                        if delta > 60:
                            color = 'background-color: #ffcccc; color: #a00;'
                        elif 30 < delta <= 60:
                            color = 'background-color: #fff3cd; color: #a67c00;'
                        elif 0 <= delta <= 30:
                            color = 'background-color: #d4edda; color: #155724;'
                    return color

                # Decide which name columns to style (support both lowercase and title-case names)
                name_cols = []
                for cand in ['First Name', 'Last Name', 'first_name', 'last_name', 'patient_first_name', 'patient_last_name']:
                    if cand in patients_df.columns:
                        name_cols.append(cand)

                def style_names(df):
                    def _row_style(row):
                        styles = []
                        row_style = color_patient_name(row)
                        for col in df.columns:
                            if col in name_cols:
                                styles.append(row_style)
                            else:
                                styles.append('')
                        return styles
                    return df.style.apply(lambda r: _row_style(r), axis=1)

                # --- Patient Visit Breakdown (move above main table) ---
                seen_30 = patients_df[(patients_df['days_since_last_visit'] >= 0) & (patients_df['days_since_last_visit'] <= 30)].copy()
                seen_31_60 = patients_df[(patients_df['days_since_last_visit'] > 30) & (patients_df['days_since_last_visit'] <= 60)].copy()
                not_seen_60 = patients_df[(patients_df['days_since_last_visit'] > 60) | (patients_df['days_since_last_visit'].isna())].copy()

                st.markdown("#### Patient Visit Breakdown")

                # Columns to show in breakdown tables
                breakdown_cols = [col for col in ['status', 'patient_id', 'first_name', 'last_name', 'dob', 'provider_name', 'coordinator_name', 'goc', 'code', 'Last Visit Date', 'service_type'] if col in patients_df.columns]

                def show_styled_table(df, height):
                    try:
                        styled = style_names(df[breakdown_cols])
                        st.dataframe(styled, height=height, use_container_width=True)
                    except Exception:
                        st.dataframe(df[breakdown_cols], height=height, use_container_width=True)

                with st.expander(f"Patients seen in the last 30 days ({len(seen_30)})", expanded=(len(seen_30) > 0 and len(seen_30) <= 10)):
                    if seen_30.empty:
                        st.info("No patients seen in the last 30 days.")
                    else:
                        show_styled_table(seen_30, 400)

                with st.expander(f"Patients seen 1mo <> 2mo ({len(seen_31_60)})", expanded=(len(seen_31_60) > 0 and len(seen_31_60) <= 10)):
                    if seen_31_60.empty:
                        st.info("No patients seen between 1 and 2 months ago.")
                    else:
                        show_styled_table(seen_31_60, 400)

                with st.expander(f"Patients NOT seen by Regional Provider in 2mo ({len(not_seen_60)})", expanded=(len(not_seen_60) > 0 and len(not_seen_60) <= 10)):
                    if not_seen_60.empty:
                        st.info("No patients not seen in over 2 months.")
                    else:
                        show_styled_table(not_seen_60, 400)

                st.markdown("---")

                # Split patients into active and inactive
                active_statuses = ['Active', 'Active-Geri', 'Active-PCP']
                if 'status' in patients_df.columns:
                    # Active patients: status starts with 'Active'
                    active_patients = patients_df[
                        patients_df['status'].fillna('').astype(str).str.strip().isin(active_statuses) |
                        patients_df['status'].fillna('').astype(str).str.strip().str.startswith('Active')
                    ].copy()
                    
                    # Inactive patients: everything else
                    inactive_patients = patients_df[
                        ~(patients_df['status'].fillna('').astype(str).str.strip().isin(active_statuses) |
                          patients_df['status'].fillna('').astype(str).str.strip().str.startswith('Active'))
                    ].copy()
                else:
                    # If no status column, treat all as active
                    active_patients = patients_df.copy()
                    inactive_patients = pd.DataFrame()

                if not editable_admin:
                    st.markdown(f"#### 🟢 Active Patients ({len(active_patients)})")
                    if not active_patients.empty:
                        try:
                            styled_active = style_names(active_patients)
                            st.dataframe(styled_active, height=600, use_container_width=True)
                        except Exception:
                            st.dataframe(active_patients, height=600, use_container_width=True)
                    else:
                        st.info("No active patients found.")
                else:
                    display_cols = [
                        'patient_id', 'status', 'first_name', 'last_name', 'facility', 'Last Visit Date', 'service_type', 'phone_primary'
                    ]
                    existing_cols = [c for c in display_cols if c in active_patients.columns]
                    df_display = active_patients[existing_cols].copy()
                    col_config = {}
                    if 'patient_id' in df_display.columns:
                        col_config['patient_id'] = st.column_config.TextColumn('patient_id', disabled=True)
                    edited = st.data_editor(
                        df_display,
                        use_container_width=True,
                        num_rows="dynamic",
                        height=600,
                        column_config=col_config,
                        key="admin_patient_info_editor"
                    )
                    if st.button("Save changes", key="admin_patient_info_save"):
                        try:
                            _apply_patient_info_edits_admin(edited, df_display)
                            st.success("Patient records updated.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving changes: {e}")

                # --- Inactive Patients Section (Expandable) ---
                with st.expander(f"🔴 Inactive Patients ({len(inactive_patients)})", expanded=False):
                    if not inactive_patients.empty:
                        if not editable_admin:
                            try:
                                styled_inactive = style_names(inactive_patients)
                                st.dataframe(styled_inactive, height=400, use_container_width=True)
                            except Exception:
                                st.dataframe(inactive_patients, height=400, use_container_width=True)
                        else:
                            display_cols = [
                                'patient_id', 'status', 'first_name', 'last_name', 'facility', 'Last Visit Date', 'service_type', 'phone_primary'
                            ]
                            existing_cols = [c for c in display_cols if c in inactive_patients.columns]
                            df_display = inactive_patients[existing_cols].copy()
                            col_config = {}
                            if 'patient_id' in df_display.columns:
                                col_config['patient_id'] = st.column_config.TextColumn('patient_id', disabled=True)
                            edited_inactive = st.data_editor(
                                df_display,
                                use_container_width=True,
                                num_rows="dynamic",
                                height=400,
                                column_config=col_config,
                                key="admin_patient_info_editor_inactive"
                            )
                            if st.button("Save changes (Inactive)", key="admin_patient_info_save_inactive"):
                                try:
                                    _apply_patient_info_edits_admin(edited_inactive, df_display)
                                    st.success("Patient records updated.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error saving changes: {e}")
                    else:
                        st.info("No inactive patients found.")

        except Exception as e:
            st.error(f"Error loading patient data: {e}")

    # --- TAB: Billing Report ---
    with tab_billing:
        # Check if user has access to billing dashboard (only admin@ and harpreet@ users)
        current_user = st.session_state.get('authenticated_user')
        user_email = current_user.get('email', '') if current_user else ''
        
        # Allow access only to admin@ and harpreet@ email addresses
        if user_email.startswith('admin@') or user_email.startswith('harpreet@'):
            # Create sub-tabs for different billing views
            billing_tab1, billing_tab2 = st.tabs(["Monthly Billing (Coordinators)", "Weekly Billing (Providers)"])
            
            with billing_tab1:
                st.subheader("Monthly Coordinator Billing")
                st.markdown("Track coordinator billing by month using patient minutes and billing codes")
                try:
                    from src.dashboards.monthly_coordinator_billing_dashboard import display_monthly_coordinator_billing_dashboard
                    display_monthly_coordinator_billing_dashboard()
                except Exception as e:
                    st.error(f"Error loading monthly coordinator billing dashboard: {e}")
                    st.info("Please ensure the monthly coordinator billing dashboard module is properly configured.")
            
            with billing_tab2:
                st.subheader("Weekly Provider Billing (P00)")
                st.markdown("Track provider billing by week using provider tasks and billing status")
                try:
                    from src.dashboards.weekly_billing_dashboard import display_weekly_billing_dashboard
                    display_weekly_billing_dashboard()
                except Exception as e:
                    st.error(f"Error loading weekly provider billing dashboard: {e}")
                    st.info("Please ensure the weekly provider billing dashboard module is properly configured.")
        else:
            st.warning("Access Restricted")
            st.info("Billing dashboard access is restricted to authorized users only.")
            st.markdown("---")
            st.markdown("**Contact Information:**")
            st.markdown("- For billing access requests, please contact your system administrator")
            st.markdown("- Current user email: `{}`".format(user_email if user_email else "Not available"))

    # --- TAB: For Testing ---
    with tab_test:
        st.subheader("For Testing: Combined patient_panel and patients table (all columns)")
        import os, json
        try:
            # Always use patient_panel as base
            panel_rows = db.get_all_patient_panel() if hasattr(db, 'get_all_patient_panel') else []
            patients_rows = db.get_all_patients() if hasattr(db, 'get_all_patients') else []
            panel_df = pd.DataFrame(panel_rows)
            patients_df = pd.DataFrame(patients_rows)

            if panel_df.empty or patients_df.empty:
                st.info("No rows found for patient_panel or patients table.")
            else:
                # Only join columns from patients that are not already in patient_panel
                panel_cols = set(panel_df.columns)
                patients_extra_cols = [col for col in patients_df.columns if col not in panel_cols and col != 'patient_id']
                # If there are extra columns, join them in
                if patients_extra_cols:
                    merged = panel_df.merge(
                        patients_df[['patient_id'] + patients_extra_cols],
                        how='left', on='patient_id', suffixes=('', '_patients')
                    )
                else:
                    merged = panel_df.copy()
                # Ensure all extra columns are present in merged, even if missing after merge
                for col in patients_extra_cols:
                    if col not in merged.columns:
                        merged[col] = pd.NA
                st.markdown("### Combined patient_panel + patients (no duplicate columns, editable)")

                # --- Persistent column selection and ordering via external JSON ---
                CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'for_testing_col_config.json')
                CONFIG_PATH = os.path.abspath(CONFIG_PATH)

                def load_col_config(all_cols):
                    try:
                        if os.path.exists(CONFIG_PATH):
                            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                            visible_cols = config.get('visible_cols', all_cols)
                            col_order = config.get('col_order', all_cols)
                            # Remove any columns that no longer exist
                            visible_cols = [c for c in visible_cols if c in all_cols]
                            col_order = [c for c in col_order if c in all_cols]
                            return visible_cols, col_order
                    except Exception as e:
                        st.warning(f"Could not load column config: {e}")
                    return all_cols, all_cols

                def save_col_config(visible_cols, col_order):
                    try:
                        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                            json.dump({'visible_cols': visible_cols, 'col_order': col_order}, f, indent=2)
                    except Exception as e:
                        st.warning(f"Could not save column config: {e}")

                all_cols = list(merged.columns)
                visible_cols, col_order = load_col_config(all_cols)

                # --- Dropdown with checkboxes for column selection ---
                with st.expander("Show/Hide Columns", expanded=False):
                    # Use a local dict for checkbox state
                    col_checks = {col: (col in visible_cols) for col in all_cols}
                    checked_cols = []
                    n_cols = 3  # Number of columns in the expander
                    col_chunks = [all_cols[i::n_cols] for i in range(n_cols)]
                    cols = st.columns(n_cols)
                    for idx, chunk in enumerate(col_chunks):
                        with cols[idx]:
                            for col in chunk:
                                checked = st.checkbox(col, value=col_checks[col], key=f"for_testing_col_check_{col}")
                                col_checks[col] = checked
                                if checked:
                                    checked_cols.append(col)

                # Preserve order from config, add any new checked columns at the end
                col_order = [col for col in col_order if col in checked_cols] + [col for col in checked_cols if col not in col_order]

                # Save config if changed
                if set(checked_cols) != set(visible_cols) or col_order != visible_cols:
                    save_col_config(checked_cols, col_order)
                    visible_cols, col_order = checked_cols, col_order

                # Reset button to restore all columns
                if st.button("Reset columns to default"):
                    save_col_config(all_cols, all_cols)
                    st.rerun()

                # Filter and reorder DataFrame
                filtered = merged[col_order] if col_order else merged

                # Dynamically set column type and human-readable names for editor compatibility
                def format_col_name(col):
                    # Auto-format: snake_case to Title Case
                    name = col.replace('_', ' ').title()
                    # Apply overrides for special cases
                    overrides = {
                        'dob': 'Date of Birth',
                        'patient_id': 'Patient ID',
                        'status_name': 'Status',
                        'provider_id': 'Provider ID',
                        'coordinator_id': 'Coordinator ID',
                        # Add more as needed
                    }
                    return overrides.get(col, name)

                col_config = {}
                for col in filtered.columns:
                    dtype = filtered[col].dtype
                    display_name = format_col_name(col)
                    if pd.api.types.is_float_dtype(dtype) or pd.api.types.is_integer_dtype(dtype):
                        col_config[col] = st.column_config.NumberColumn(display_name, width="medium")
                    elif pd.api.types.is_object_dtype(dtype):
                        col_config[col] = st.column_config.TextColumn(display_name, width="medium")
                    else:
                        col_config[col] = st.column_config.DisabledColumn(display_name)
                st.data_editor(
                    filtered.head(200),
                    use_container_width=True,
                    num_rows="dynamic",
                    height=900,
                    column_config=col_config
                )
        except Exception as e:
            st.error(f"Error in For Testing tab: {e}")

    # ... Rest of the coordinator tasks and provider tasks tabs would go here ...
