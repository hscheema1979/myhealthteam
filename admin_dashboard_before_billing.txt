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
def show():
    from src.config.ui_style_config import TextStyle
    st.title("Admin Dashboard")
    user_id = st.session_state.get('user_id', None)

    # New tab order: User Role Management, User Management, Staff Onboarding, Coordinator Tasks, Provider Tasks, Patient Info
    tab_role, tab1, tab_onboard, tab_coord_tasks, tab_prov_tasks, tab3, tab_test = st.tabs([
        "User Role Management",
        "User Management", 
        "Staff Onboarding",
        "Coordinator Tasks",
        "Provider Tasks",
        "Patient Info",
        "For Testing"
    ])
    # --- TAB: Coordinator Tasks ---
    with tab_coord_tasks:
        
        # --- Coordinator Tasks: Total Minutes This Month Header ---
        # We'll calculate the total from the Coordinator Monthly Summary DataFrame (df_summary)
        # This is more robust and avoids local variable errors
        summary_rows = db.get_coordinator_monthly_minutes_live()
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
                conn = db.get_db_connection()
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
                        summary_df = prepare_patient_summary_with_facility_mapping(aggregated_df, db)
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
            import datetime
            conn = db.get_db_connection()
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

                # --- Split patient data into active and inactive sections ---
                # Define active status patterns
                active_statuses = ['Active', 'Active-Geri', 'Active-PCP']
                
                # Split patients into active and inactive
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

                # --- Active Patients Section ---
                st.markdown(f"#### 🟢 Active Patients ({len(active_patients)})")
                if not active_patients.empty:
                    try:
                        styled_active = style_names(active_patients)
                        st.dataframe(styled_active, height=600, use_container_width=True)
                    except Exception:
                        st.dataframe(active_patients, height=600, use_container_width=True)
                else:
                    st.info("No active patients found.")

                # --- Inactive Patients Section (Expandable) ---
                with st.expander(f"🔴 Inactive Patients ({len(inactive_patients)})", expanded=False):
                    if not inactive_patients.empty:
                        try:
                            styled_inactive = style_names(inactive_patients)
                            st.dataframe(styled_inactive, height=400, use_container_width=True)
                        except Exception:
                            st.dataframe(inactive_patients, height=400, use_container_width=True)
                    else:
                        st.info("No inactive patients found.")
        except Exception as e:
            st.error(f"Error loading patient data: {e}")

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

    # ...existing code...