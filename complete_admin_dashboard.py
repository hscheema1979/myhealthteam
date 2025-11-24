#!/usr/bin/env python3

# Read the current file (without the placeholder)
with open('src/dashboards/admin_dashboard.py', 'r') as f:
    content = f.read()

# Find where to insert the missing sections (before the placeholder)
placeholder = "# ... Rest of the coordinator tasks and provider tasks tabs would go here ..."
insert_point = content.find(placeholder)

if insert_point == -1:
    print("Placeholder not found!")
    exit(1)

# Take everything before the placeholder
before_placeholder = content[:insert_point]

# Add the missing coordinator and provider tasks sections
missing_sections = """

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
            available_tables = conn.execute(\"\"\"
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'coordinator_tasks_20%'
                ORDER BY name DESC
            \"\"\").fetchall()
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
                    patient_query = f\"\"\"
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
                    \"\"\"
                    
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
                                    red_df = red_df.copy()
                                    styled = red_df.style.map(_color_minutes, subset=['Sum of Minutes'])
                                    st.dataframe(styled, use_container_width=True)
                                except Exception:
                                    st.dataframe(red_df, use_container_width=True)

                        with st.expander(f"Yellow (40–89 minutes) — {len(yellow_df)} patients", expanded=(len(yellow_df) > 0 and len(yellow_df) <= 10)):
                            if yellow_df.empty:
                                st.info("No patients in this category.")
                            else:
                                try:
                                    yellow_df = yellow_df.copy()
                                    styled = yellow_df.style.map(_color_minutes, subset=['Sum of Minutes'])
                                    st.dataframe(styled, use_container_width=True)
                                except Exception:
                                    st.dataframe(yellow_df, use_container_width=True)

                        with st.expander(f"Green / Blue (≥90 minutes) — {len(greenblue_df)} patients", expanded=(len(greenblue_df) > 0 and len(greenblue_df) <= 10)):
                            if greenblue_df.empty:
                                st.info("No patients in this category.")
                            else:
                                try:
                                    greenblue_df = greenblue_df.copy()
                                    styled = greenblue_df.style.map(_color_minutes, subset=['Sum of Minutes'])
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
                        
                        df_billing_display = df_billing_display.copy()
                        if 'current_facility_id' in df_billing_display.columns:
                            df_billing_display['current_facility_id'] = df_billing_display['current_facility_id'].astype(str)
                        st.dataframe(df_billing_display, use_container_width=True)
                        
                    else:
                        st.info("No patient data available for this month.")
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
                    coordinator_query = f\"\"\"
                    SELECT 
                        ct.coordinator_id,
                        SUM(ct.duration_minutes) as total_minutes
                    FROM {table_name} ct
                    WHERE ct.duration_minutes IS NOT NULL
                    GROUP BY ct.coordinator_id
                    ORDER BY total_minutes ASC
                    \"\"\"
                    
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

                        # Enhance mapping: resolve staff codes via staff_code_mapping and users
                        try:
                            conn2 = db.get_db_connection()
                            # Build user_id -> name map from users table
                            users_df = pd.read_sql_query("SELECT user_id, COALESCE(full_name, username) AS name FROM users", conn2)
                            user_map = {str(int(row['user_id'])): row['name'] for _, row in users_df.iterrows() if pd.notna(row['user_id'])}
                            # Map staff_code -> name via staff_code_mapping
                            try:
                                scm_df = pd.read_sql_query("SELECT staff_code, user_id FROM staff_code_mapping", conn2)
                                for _, r in scm_df.iterrows():
                                    code_key = _safe_key(r['staff_code'])
                                    # Prefer mapped user name if exists
                                    if pd.notna(r['user_id']):
                                        uid_key = _safe_key(r['user_id'])
                                        mapped_name = user_map.get(uid_key)
                                        if code_key and mapped_name:
                                            id_to_name[code_key] = mapped_name
                                    # Also add direct user_id -> name entries
                                    if pd.notna(r['user_id']):
                                        uid_key = _safe_key(r['user_id'])
                                        if uid_key and uid_key in user_map:
                                            id_to_name.setdefault(uid_key, user_map[uid_key])
                            except Exception:
                                pass
                        except Exception:
                            pass
                        finally:
                            try:
                                conn2.close()
                            except Exception:
                                pass

                        # Fallback to users table for coordinators (roles 36/37)
                        if not id_to_name:
                            coordinators = []
                            try:
                                coordinators.extend(db.get_users_by_role(36))
                            except Exception:
                                pass
                            try:
                                coordinators.extend(db.get_users_by_role(37))
                            except Exception:
                                pass
                            for c in coordinators:
                                uid = c.get('user_id')
                                if uid is None:
                                    continue
                                id_to_name[_safe_key(uid)] = c.get('full_name', c.get('username', 'Unknown'))

                        # Map coordinator names
                        df_summary['coord_key'] = df_summary['coordinator_id'].apply(lambda x: _safe_key(x) if pd.notna(x) else None)
                        df_summary['Coordinator'] = df_summary['coord_key'].apply(lambda k: id_to_name.get(k, f"Unknown (ID {k})") if k else None)
                        df_summary = df_summary[['Coordinator', 'total_minutes']]
                        df_summary = df_summary.rename(columns={'total_minutes': 'Sum of Minutes'})
                        df_summary = df_summary.sort_values('Sum of Minutes', ascending=True)
                        st.write("Sorted by Sum of Minutes (lowest → highest):")
                        df_summary = df_summary.copy()
                        if 'current_facility_id' in df_summary.columns:
                            df_summary['current_facility_id'] = df_summary['current_facility_id'].astype(str)
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
                
                # Ensure coordinator_name is present (fill blanks even if the column exists)
                # Build a robust mapping from coordinator_id (user_id or staff_code) to display name
                id_to_name = {}
                def _safe_key(val):
                    try:
                        if pd.isna(val):
                            return None
                        return str(int(val))
                    except Exception:
                        return str(val) if val is not None else None

                if 'coordinator_id' in df.columns:
                    # 1) Prefer names already present in tasks rows
                    if 'coordinator_name' in df.columns:
                        try:
                            mapping = df[['coordinator_id', 'coordinator_name']].dropna().drop_duplicates('coordinator_id')
                            for _, row in mapping.iterrows():
                                key = _safe_key(row['coordinator_id'])
                                name = row['coordinator_name']
                                if key and pd.notna(name) and str(name).strip() != '':
                                    id_to_name[key] = name
                        except Exception:
                            pass

                    # 2) Enhance mapping using staff_code_mapping and users
                    try:
                        conn3 = db.get_db_connection()
                        users_df = pd.read_sql_query("SELECT user_id, COALESCE(full_name, username) AS name FROM users", conn3)
                        user_map = {str(int(row['user_id'])): row['name'] for _, row in users_df.iterrows() if pd.notna(row['user_id'])}
                        try:
                            scm_df = pd.read_sql_query("SELECT staff_code, user_id FROM staff_code_mapping", conn3)
                            for _, r in scm_df.iterrows():
                                code_key = _safe_key(r.get('staff_code'))
                                uid_key = _safe_key(r.get('user_id'))
                                mapped_name = user_map.get(uid_key) if uid_key else None
                                if code_key and mapped_name:
                                    id_to_name.setdefault(code_key, mapped_name)
                                if uid_key and mapped_name:
                                    id_to_name.setdefault(uid_key, mapped_name)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    finally:
                        try:
                            conn3.close()
                        except Exception:
                            pass

                    # 3) Fallback to coordinator roles (include CC=36 and LC=37)
                    try:
                        coordinators = []
                        try:
                            coordinators.extend(db.get_users_by_role(36))
                        except Exception:
                            pass
                        try:
                            coordinators.extend(db.get_users_by_role(37))
                        except Exception:
                            pass
                        for c in coordinators:
                            uid_key = _safe_key(c.get('user_id'))
                            name = c.get('full_name', c.get('username', 'Unknown'))
                            if uid_key and name:
                                id_to_name.setdefault(uid_key, name)
                    except Exception:
                        pass

                    # 4) Ensure coordinator_name column exists and fill using mapping
                    if 'coordinator_name' in df.columns:
                        def _resolve_name(row):
                            existing = row.get('coordinator_name')
                            if pd.notna(existing) and str(existing).strip() != '':
                                return existing
                            key = _safe_key(row.get('coordinator_id'))
                            if key:
                                return id_to_name.get(key, f"Unknown (ID {row.get('coordinator_id')})")
                            return None
                        df['coordinator_name'] = df.apply(_resolve_name, axis=1)
                    else:
                        df['coordinator_name'] = df['coordinator_id'].apply(lambda x: id_to_name.get(_safe_key(x), f"Unknown (ID {x})") if pd.notna(x) else None)

                # Create filter columns
                filter_cols = st.columns(3)
                
                with filter_cols[1]:
                    st.markdown("**Coordinator Name**")
                    coord_names = sorted(df['coordinator_name'].dropna().unique()) if 'coordinator_name' in df.columns else []
                    selected_coord = st.selectbox("Coordinator Name", ["All"] + coord_names, key="coord_name_selector", label_visibility="collapsed")
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
                    selected_patient = st.selectbox("Patient", ["All"] + patient_options, key="patient_selector", label_visibility="collapsed")

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
                    df_ed = filtered_df[show_cols].copy()
                    if 'current_facility_id' in df_ed.columns:
                        df_ed['current_facility_id'] = df_ed['current_facility_id'].astype(str)
                    st.data_editor(df_ed, use_container_width=True, num_rows="dynamic", height=700)
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
                df_summary = df_summary.copy()
                if 'current_facility_id' in df_summary.columns:
                    df_summary['current_facility_id'] = df_summary['current_facility_id'].astype(str)
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

                if 'current_facility_id' in patients_df.columns:
                    patients_df['current_facility_id'] = patients_df['current_facility_id'].astype(str)

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

                        union_sql = '\\nUNION ALL\\n'.join(select_templates)
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
                        df_show = df[breakdown_cols].copy()
                        if 'current_facility_id' in df_show.columns:
                            df_show['current_facility_id'] = df_show['current_facility_id'].astype(str)
                        st.dataframe(df_show, height=height, use_container_width=True)

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

"""

# Write the complete file
with open('src/dashboards/admin_dashboard.py', 'w') as f:
    f.write(before_placeholder + missing_sections)

print("Complete admin dashboard file created successfully!")
