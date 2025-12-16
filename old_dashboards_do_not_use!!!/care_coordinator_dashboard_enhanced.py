
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional
import time

# Import database and other dependencies
from src import database
from src.core_utils import get_user_role_ids
import streamlit.components.v1 as components
from src.dashboards.workflow_module import show_workflow_management
from src.dashboards.phone_review import show_phone_review_entry
from src.dashboards import coordinator_task_review_component

def _has_admin_role(user_id):
    """Check if user has admin role (role_id 34) for edit permissions"""
    try:
        user_roles = database.get_user_roles_by_user_id(user_id)
        user_role_ids = [r['role_id'] for r in user_roles]
        return 34 in user_role_ids
    except Exception:
        return False

def _apply_patient_info_edits(edited_df, original_df):
    """Apply edits to patient information in database"""
    import pandas as pd
    if edited_df is None or original_df is None:
        return
    if "patient_id" not in edited_df.columns:
        return
    original_by_id = {str(r["patient_id"]): r for _, r in original_df.iterrows() if pd.notna(r.get("patient_id"))}
    conn = database.get_db_connection()
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
        tab1, tab2, tab3, tab_patient_info, tab4 = st.tabs(["My Patients", "Phone Reviews", "Team Management", "Patient Info", "Help"])
        with tab4:
            st.header("Help")
            st.markdown("This help uses real UI elements to explain coordinator views.")
            st.subheader("Color Legend (Minutes This Month)")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.error("Red: <40 minutes (triage now)")
            with col2:
                st.warning("Yellow: 40–89 minutes")
            with col3:
                st.success("Green: 90–199 minutes")
            with col4:
                st.info("Blue: ≥200 minutes")
            st.subheader("Sections")
            st.markdown(
                "- My Patients: coordinator panel and actions.\n"
                "- Phone Reviews: use 'cm' mode for coordinator reviews.\n"
                "- Team Management: monthly/weekly summaries and task creation."
            )
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
                                        styled = red_df.style.map(_color_minutes, subset=['Sum of Minutes'])
                                        st.dataframe(styled, use_container_width=True)
                                    except Exception:
                                        st.dataframe(red_df, use_container_width=True)

                            with st.expander(f"Yellow (40–89 minutes) — {len(yellow_df)} patients", expanded=(len(yellow_df) > 0 and len(yellow_df) <= 10)):
                                if yellow_df.empty:
                                    st.info("No patients in this category.")
                                else:
                                    try:
                                        styled = yellow_df.style.map(_color_minutes, subset=['Sum of Minutes'])
                                        st.dataframe(styled, use_container_width=True)
                                    except Exception:
                                        st.dataframe(yellow_df, use_container_width=True)

                            with st.expander(f"Green / Blue (≥90 minutes) — {len(greenblue_df)} patients", expanded=(len(greenblue_df) > 0 and len(greenblue_df) <= 10)):
                                if greenblue_df.empty:
                                    st.info("No patients in this category.")
                                else:
                                    try:
                                        styled = greenblue_df.style.map(_color_minutes, subset=['Sum of Minutes'])
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
                            st.data_editor(filtered_df[show_cols], use_container_width=True, num_rows="dynamic", height=700)
                        else:
                            st.info(f"No data in table {selected_table} after filtering.")
            except Exception as e:
                st.error(f"Error loading coordinator tasks: {e}")
        with tab_patient_info:
            show_patient_info_tab_coordinator(user_id)
    else:
        # Non-management coordinator view: provide My Patients + Help tabs (no Team Management)
        tab1, tab_task_review, tab_patient_info, tab2 = st.tabs(["My Patients", "Task Review", "Patient Info", "Help"])
        with tab1:
            show_coordinator_patient_list(user_id, context="tab1")
        with tab_task_review:
            coordinator_task_review_component.show(user_id)
        with tab_patient_info:
            show_patient_info_tab_coordinator(user_id)
        with tab2:
            st.header("Help")
            help_html = """
            <style>
              .legend { display: flex; gap: 12px; margin: 6px 0 18px 0; }
              .badge { padding: 6px 10px; border-radius: 6px; color: #fff; font-weight: 600; font-size: 13px; }
              .red { background: #d9534f; }
              .yellow { background: #f0ad4e; }
              .green { background: #5cb85c; }
              .blue { background: #5bc0de; }
              .section { margin: 10px 0 18px 0; }
              .section h3 { margin: 12px 0 8px 0; }
              .desc { color: #444; font-size: 14px; }
              table.help { width: 100%; border-collapse: collapse; margin-top: 8px; }
              table.help th, table.help td { border: 1px solid #ddd; padding: 8px; font-size: 13px; }
              table.help th { background: #f7f7f7; text-align: left; }
              .small { color: #777; font-size: 12px; }
            </style>

            <div class="section">
              <div class="legend">
                <span class="badge red">&lt;40 min</span>
                <span class="badge yellow">40–89 min</span>
                <span class="badge green">90–199 min</span>
                <span class="badge blue">≥200 min</span>
              </div>
              <div class="small">Legend applies to the <strong>Mins</strong> column: total minutes logged this month.</div>
            </div>

            <div class="section">
              <h3>Patient Panel — Columns and Meaning</h3>
              <div class="desc">This table lists patients assigned to you and key details you use to coordinate care.</div>
              <table class="help">
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>What it means</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Status</td>
                    <td>Patient’s enrollment status. Active variants include <em>Active</em>, <em>Active-Geri</em>, <em>Active-PCP</em>. Filters and metrics use “Active*”.</td>
                  </tr>
                  <tr>
                    <td>First Name / Last Name</td>
                    <td>Patient’s name. Rows are sorted by Last Name, then First Name.</td>
                  </tr>
                  <tr>
                    <td>Facility</td>
                    <td>Mapped facility name (from <code>current_facility_id</code> or fallback text). “Unknown” if not mapped.</td>
                  </tr>
                  <tr>
                    <td>Provider Name</td>
                    <td>Assigned provider mapped from provider IDs. Shows “Unassigned” if no match.</td>
                  </tr>
                  <tr>
                    <td>Provider’s Last Visit Date</td>
                    <td>Last recorded provider visit date for this patient.</td>
                  </tr>
                  <tr>
                    <td>Service Type</td>
                    <td>Service category for the patient (e.g., routine, geriatric, PCP lines as defined in data).</td>
                  </tr>
                  <tr>
                    <td>Phone Number</td>
                    <td>Primary phone on record.</td>
                  </tr>
                  <tr>
                    <td>POC-A (Appt Contact)</td>
                    <td>Point-of-contact for scheduling/appointments.</td>
                  </tr>
                  <tr>
                    <td>POC-M (Medical Contact)</td>
                    <td>Point-of-contact for medical information/coordination.</td>
                  </tr>
                  <tr>
                    <td>Mins</td>
                    <td>Total minutes logged this month for this patient by the coordinator; used for triage and coverage checks.</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="section">
              <h3>Workflow Manager — Overview and Table Columns</h3>
              <div class="desc">Create new workflows and track ongoing work. Quick Start lets you pick <strong>Patient</strong>, <strong>Workflow Type</strong>, <strong>Priority</strong>, and <strong>Task Notes</strong>. Ongoing Workflows shows active items with progress.</div>
              <table class="help">
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>What it means</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Workflow Instance ID</td>
                    <td>Unique ID for the workflow instance.</td>
                  </tr>
                  <tr>
                    <td>Patient</td>
                    <td>Patient name tied to the workflow.</td>
                  </tr>
                  <tr>
                    <td>Workflow Type</td>
                    <td>The template name (e.g., “IMAGING URGENT”, “MEDICATION REFILL”).</td>
                  </tr>
                  <tr>
                    <td>Coordinator ID / Coordinator Name</td>
                    <td>Assigned coordinator identifiers for the workflow.</td>
                  </tr>
                  <tr>
                    <td>Current Owner User ID / Current Owner Name</td>
                    <td>User currently responsible for the next step.</td>
                  </tr>
                  <tr>
                    <td>Current Step / Total Steps</td>
                    <td>Numeric progress (e.g., Step 2 of 5). Also shown as “Step Progress”.</td>
                  </tr>
                  <tr>
                    <td>Priority</td>
                    <td>Priority level chosen at kickoff (Low/Medium/High/Urgent).</td>
                  </tr>
                  <tr>
                    <td>Created</td>
                    <td>Date the workflow was started.</td>
                  </tr>
                  <tr>
                    <td>Status</td>
                    <td>Workflow state (e.g., Active). Changes when completed.</td>
                  </tr>
                </tbody>
              </table>
              <div class="small">Actions available: <strong>Resume Workflow</strong> (open steps), <strong>Complete Next Step</strong> (advance), <strong>Add Note</strong> (append timestamped note), and <strong>Complete Workflow</strong>.</div>
            </div>

            <div class="section">
              <h3>Task Entry — Fields and Usage</h3>
              <table class="help">
                <thead>
                  <tr>
                    <th>Field</th>
                    <th>What it does</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Date</td>
                    <td>When the task occurred. Defaults to today.</td>
                  </tr>
                  <tr>
                    <td>Patient Name</td>
                    <td>Dropdown listing your currently assigned, active patients. If none, you’ll see a notice.</td>
                  </tr>
                  <tr>
                    <td>Task Type</td>
                    <td>Category for the activity (Phone Call, Care Coordination, Documentation, Patient Follow-up, Provider Communication, Other).</td>
                  </tr>
                  <tr>
                    <td>Duration (min)</td>
                    <td>Manual entry; contributes to monthly minutes.</td>
                  </tr>
                  <tr>
                    <td>Notes</td>
                    <td>Free text describing the activity.</td>
                  </tr>
                  <tr>
                    <td>Log Task</td>
                    <td>Validates required fields (patient, type, duration) and records the entry.</td>
                  </tr>
                </tbody>
              </table>
            </div>
            """
            # Add visual mockups for the elements described above so users can see what to look for
            help_html += """
            <div class="example">
                <h3>Visual Examples</h3>
                <p class="note">These are static examples to help you visually match the UI. They do not perform actions.</p>

                <h4>Patient Panel (example snippet)</h4>
                <table class="help">
                    <thead>
                        <tr>
                            <th>Status</th>
                            <th>First Name</th>
                            <th>Last Name</th>
                            <th>Facility</th>
                            <th>Provider Name</th>
                            <th>Provider's Last Visit Date</th>
                            <th>Service Type</th>
                            <th>POC-A (Appt Contact)</th>
                            <th>POC-M (Medical Contact)</th>
                            <th>Mins (This Month)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><span class="badge" style="background:#e0f7fa;color:#006064">Active</span></td>
                            <td>Alice</td>
                            <td>Nguyen</td>
                            <td>Sunrise Manor</td>
                            <td>Dr. Patel</td>
                            <td>2025-11-02</td>
                            <td>Initial TV</td>
                            <td>(702) 555-0142</td>
                            <td>(702) 555-0199</td>
                            <td><strong>57</strong></td>
                        </tr>
                    </tbody>
                </table>

                <h4>Workflow Manager (example controls)</h4>
                <div class="form-row">
                    <div class="field">
                        <label>Workflow Template</label>
                        <div class="select disabled">Home Visit</div>
                    </div>
                    <div class="field">
                        <label>Start Date</label>
                        <div class="input disabled">2025-11-19</div>
                    </div>
                    <div class="field">
                        <label>Patient</label>
                        <div class="select disabled">Alice Nguyen</div>
                    </div>
                    <div class="field">
                        <label>Coordinator</label>
                        <div class="select disabled">Your Name</div>
                    </div>
                </div>
                <div class="actions">
                    <button class="btn" disabled>Start Workflow</button>
                </div>
                <p class="note">In the real UI these are Streamlit controls. Here they are static so you can see layout and labels.</p>

                <h4>Ongoing Workflows (example snippet)</h4>
                <table class="help">
                    <thead>
                        <tr>
                            <th>Workflow</th>
                            <th>Patient</th>
                            <th>Coordinator</th>
                            <th>Started</th>
                            <th>Completed Steps</th>
                            <th>Total Steps</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Home Visit</td>
                            <td>Alice Nguyen</td>
                            <td>Your Name</td>
                            <td>2025-11-19</td>
                            <td>1</td>
                            <td>4</td>
                            <td>
                                <span class="btn small" disabled>Open</span>
                                <span class="btn small" disabled>Save Progress</span>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <h4>Task Entry (example layout)</h4>
                <div class="form-row">
                    <div class="field">
                        <label>Date</label>
                        <div class="input disabled">2025-11-19</div>
                    </div>
                    <div class="field">
                        <label>Patient</label>
                        <div class="select disabled">Alice Nguyen</div>
                    </div>
                    <div class="field">
                        <label>Task Type</label>
                        <div class="select disabled">Phone Call</div>
                    </div>
                    <div class="field">
                        <label>Duration (mins)</label>
                        <div class="input disabled">15</div>
                    </div>
                </div>
                <div class="field" style="max-width: 720px;">
                    <label>Notes</label>
                    <div class="textarea disabled">Spoke with POC-A to confirm appointment for next week.</div>
                </div>
                <div class="actions">
                    <button class="btn" disabled>Log Task</button>
                </div>

                <style>
                    .example { margin-top: 24px; }
                    .note { color: #555; font-size: 13px; margin: 8px 0 16px; }
                    .form-row { display: flex; gap: 16px; flex-wrap: wrap; }
                    .field { display: flex; flex-direction: column; gap: 6px; min-width: 180px; }
                    .input, .select, .textarea { border: 1px solid #ddd; border-radius: 6px; padding: 8px 10px; background: #fafafa; color: #666; }
                    .textarea { min-height: 72px; }
                    .disabled { opacity: 0.7; }
                    .btn { display: inline-block; padding: 8px 12px; background: #f0f0f0; color: #333; border: 1px solid #ddd; border-radius: 6px; cursor: not-allowed; }
                    .btn.small { padding: 6px 10px; font-size: 12px; }
                </style>
            </div>
            """

            components.html(help_html, height=1100, scrolling=True)

            # Interactive Examples (real Streamlit widgets, read-only)
            st.markdown("### Interactive Examples (Live Streamlit widgets, read-only)")

            # Patient Panel — Live Example
            with st.expander("Patient Panel — Live Example (Read-only)", expanded=True):
                import pandas as pd
                sample_df = pd.DataFrame([
                    {
                        "Status": "Active",
                        "First Name": "Alice",
                        "Last Name": "Nguyen",
                        "Facility": "Sunrise Manor",
                        "Provider Name": "Dr. Patel",
                        "Provider's Last Visit Date": "2025-11-02",
                        "Service Type": "Initial TV",
                        "POC-A (Appt Contact)": "(702) 555-0142",
                        "POC-M (Medical Contact)": "(702) 555-0199",
                        "Mins": 57,
                    }
                ])
                st.dataframe(sample_df, use_container_width=True)
                st.caption("What it shows: the real panel columns and a sample row. How to use: sort/filter columns as needed in the actual panel; minutes are monthly and color-coded in the real view.")

            # Workflow Manager — Quick Start (fields)
            with st.expander("Workflow Manager — Quick Start (Read-only)", expanded=True):
                import datetime
                st.selectbox("Workflow Template", ["Home Visit", "Initial TV", "Follow-up"], index=0, disabled=True)
                st.date_input("Start Date", datetime.date.today(), disabled=True)
                st.selectbox("Patient", ["Alice Nguyen"], index=0, disabled=True, key="workflow_patient_selectbox")
                st.selectbox("Coordinator", ["Your Name"], index=0, disabled=True)
                st.button("Start Workflow", disabled=True)
                st.caption("What it does: creates a workflow instance tied to a patient/coordinator with tracked steps. How to use: choose a template, confirm date/patient, then Start; progress appears in Ongoing Workflows.")

            # Ongoing Workflows — Status Table
            with st.expander("Ongoing Workflows — Status Table (Read-only)", expanded=False):
                import pandas as pd
                wf_df = pd.DataFrame([
                    {
                        "Workflow": "Home Visit",
                        "Patient": "Alice Nguyen",
                        "Coordinator": "Your Name",
                        "Started": "2025-11-19",
                        "Completed Steps": 1,
                        "Total Steps": 4,
                    }
                ])
                st.dataframe(wf_df, use_container_width=True)
                st.caption("Actions in the real UI: Open (view and complete steps), Save Progress (log notes/minutes). Use to track progress and capture time.")

            # Task Entry — Logging
            with st.expander("Task Entry — Logging (Read-only)", expanded=False):
                import datetime
                st.date_input("Date", datetime.date.today(), disabled=True)
                st.selectbox("Patient", ["Alice Nguyen"], index=0, disabled=True, key="task_entry_patient_selectbox")
                st.selectbox("Task Type", ["Phone Call", "Chart Review", "Care Coordination"], index=0, disabled=True)
                st.number_input("Duration (mins)", min_value=0, step=5, value=15, disabled=True)
                st.text_area("Notes", "Spoke with POC-A to confirm appointment for next week.", disabled=True)
                st.button("Log Task", disabled=True)
                st.caption("What it does: records the activity to monthly summaries and minutes. How to use: pick date/patient/type, enter duration and notes, then Log Task in the real view.")
        # REMOVED: Onboarding queue statistics and onboarding tasks are not shown in care coordinator dashboard

def show_coordinator_patient_list(user_id, context="default"):
    # Ensure daily_tasks_data is initialized in session state
    if "daily_tasks_data" not in st.session_state:
        st.session_state.daily_tasks_data = [{}]

    # Also get user role ids so management roles can see all workflows
    try:
        user_role_ids = get_user_role_ids(user_id) or []
    except Exception:
        user_role_ids = []

    # Get all patient data with coordinator assignments
    try:
        # First, get all coordinator IDs to fetch their patients
        all_coordinators = database.get_users_by_role(36)  # 36 = Care Coordinator role
        coordinator_ids = [str(coord.get('user_id')) for coord in all_coordinators if coord.get('user_id')]
        
        # Fetch patients for all coordinators
        all_patient_data = []
        for coord_id in coordinator_ids:
            coordinator_patients = database.get_coordinator_patient_panel_enhanced(int(coord_id))
            all_patient_data.extend(coordinator_patients)
        
        # Remove duplicates based on patient_id
        seen_patient_ids = set()
        patient_data_list = []
        for patient in all_patient_data:
            patient_id = patient.get('patient_id')
            if patient_id and patient_id not in seen_patient_ids:
                seen_patient_ids.add(patient_id)
                patient_data_list.append(patient)
                
    except Exception as e:
        st.error(f"Error fetching patient panel data: {e}")
        patient_data_list = []

    # Initialize coordinator map for filtering
    coordinator_map = {}
    try:
        all_coordinators = database.get_users_by_role(36)
        for coord in all_coordinators:
            coord_name = f"{coord.get('full_name', coord.get('username', 'Unknown'))}"
            coord_id = coord.get('user_id')
            coordinator_map[coord_name] = coord_id
    except:
        pass

    # --- Add Search and Filter UI at the top ---
    st.markdown("#### Search and Filter Patients")
    
    # Create filter columns
    col_search, col_filter = st.columns([2, 1])
    
    with col_search:
        search_query = st.text_input(
            "Search by patient name or ID",
            key="coordinator_patient_search",
            placeholder="Enter patient name or ID..."
        )
    
    with col_filter:
        # Get all coordinators for the filter dropdown
        try:
            all_coordinators = database.get_users_by_role(36)  # 36 = Care Coordinator role
            coordinator_options = ["All Coordinators"]
            
            for coord in all_coordinators:
                coord_name = f"{coord.get('full_name', coord.get('username', 'Unknown'))}"
                coordinator_options.append(coord_name)
            
            # Default to showing only the logged-in user's patients
            current_user_name = None
            try:
                current_user = database.get_user_by_id(user_id)
                if current_user:
                    # Handle sqlite3.Row object by accessing directly like a dictionary
                    try:
                        full_name = current_user['full_name']
                        username = current_user['username']
                    except (KeyError, TypeError):
                        # Fallback if direct access fails
                        full_name = None
                        username = None
                    
                    current_user_name = full_name if full_name else username if username else "Unknown User"
            except Exception:
                pass
            
            # Set default selection - only current user if found, otherwise "All Coordinators"
            default_selection = [current_user_name] if current_user_name and current_user_name in coordinator_options else ["All Coordinators"]
            
            selected_coordinators = st.multiselect(
                "Filter by Coordinator(s)",
                coordinator_options,
                key="coordinator_filter",
                default=default_selection,
                help="Select one or more coordinators to view their patients. Default shows your patients."
            )
        except Exception as e:
            st.warning(f"Could not load coordinator list: {e}")
            selected_coordinators = ["All Coordinators"]

    # Apply filtering
    filtered_patients = patient_data_list
    
    # Filter by search query
    if search_query.strip():
        q = search_query.lower().strip()
        filtered_patients = [
            p for p in filtered_patients
            if (q in str(p.get('patient_id', '')).lower() or 
                q in f"{p.get('first_name', '')} {p.get('last_name', '')}".lower())
        ]
    
    # Filter by coordinator(s)
    if selected_coordinators and "All Coordinators" not in selected_coordinators:
        # Get selected coordinator IDs
        selected_coord_ids = []
        for coord_name in selected_coordinators:
            coord_id = coordinator_map.get(coord_name)
            if coord_id:
                selected_coord_ids.append(str(coord_id))
        
        if selected_coord_ids:
            filtered_patients = [
                p for p in filtered_patients
                if str(p.get('assigned_coordinator_id', '')) in selected_coord_ids
            ]

    # Use filtered results
    patient_data_list = filtered_patients

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
    # Use the patient_data_list which now contains the filtered results
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

        if 'current_facility_id' in patients_df.columns:
            patients_df['current_facility_id'] = patients_df['current_facility_id'].astype(str)
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
        coordinator_id=user_id,  # Pass user_id as coordinator_id for workflow compatibility
        active_patients=active_patient_names,
        filtered_patients=patient_data_list,  # Pass filtered patient data for workflow filtering
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
    # Moved to workflow_utils.py - wrapper maintains old signature for compatibility
    # Note: coordinator_id here is actually user_id in the old calling convention
    from src.utils.workflow_utils import create_workflow_task as _create_workflow_task
    return _create_workflow_task(
        user_id=coordinator_id,  # coordinator_id parameter is actually user_id
        patient_name=patient_name,
        workflow_type=workflow_type,
        priority=priority,
        notes=notes,
        estimated_duration=estimated_duration
    )

def get_ongoing_workflows(user_id, user_role_ids=None):
    # Moved to workflow_utils.py
    from src.utils.workflow_utils import get_ongoing_workflows as _get_ongoing_workflows
    return _get_ongoing_workflows(user_id, user_role_ids)

def show_patient_info_tab_coordinator(user_id):
    try:
        search_query = st.text_input("Search by name or ID", key="cc_patient_info_search")

        # Check if user has admin role for edit access
        has_admin_access = _has_admin_role(user_id)

        if has_admin_access:
            edit_mode = st.checkbox("Enable editing", key="cc_patient_edit_mode")
        else:
            edit_mode = False
            st.info("🔒 **View-Only Mode**: Patient info editing is restricted to administrators")

        # Always use the full patient panel (admin-equivalent view)
        patient_data_list = database.get_all_patient_panel() if hasattr(database, "get_all_patient_panel") else []

        import pandas as pd
        df = pd.DataFrame(patient_data_list)

        if df.empty:
            st.info("No patient data available.")
            return

        if "patient_id" not in df.columns:
            df["patient_id"] = None

        df["full_name"] = (df.get("first_name", "").fillna("") + " " + df.get("last_name", "").fillna("")).str.strip()

        if search_query:
            q = str(search_query).lower().strip()
            df = df[df.apply(lambda r: q in str(r.get("patient_id", "")).lower() or q in str(r.get("full_name", "")).lower(), axis=1)]

        from datetime import datetime
        def _days_since(date_val):
            try:
                if pd.isna(date_val) or not str(date_val).strip():
                    return None
                return (datetime.now() - pd.to_datetime(date_val)).days
            except Exception:
                return None

        possible_last_visit_cols = ['last_visit_date', 'last_visit', 'last_visit_dt', 'last_visit_at', 'last_visit_timestamp', 'most_recent_visit', 'last_visit_date_iso']
        found_last = None
        for c in possible_last_visit_cols:
            if c in df.columns:
                found_last = c
                break
        df["Last Visit Date"] = df[found_last] if found_last else None
        df["days_since_last_visit"] = df.get("Last Visit Date").apply(_days_since)

        display_cols = [
            "patient_id",
            "status",
            "first_name",
            "last_name",
            "facility",
            "Last Visit Date",
            "service_type",
            "phone_primary",
        ]
        existing_cols = [c for c in display_cols if c in df.columns]
        df_display = df[existing_cols].copy()


        def _color_last_visit(val):
            try:
                d = _days_since(val)
                if d is None:
                    return ""
                if d <= 30:
                    return "background-color: #90be6d; color: black"
                if d <= 60:
                    return "background-color: #f9c74f; color: black"
                return "background-color: #f94144; color: white"
            except Exception:
                return ""

        # Display based on edit permissions
        if edit_mode and has_admin_access:
            # Show editable dataframe for admin users
            edited_df = st.data_editor(df_display, use_container_width=True, hide_index=True, num_rows="dynamic", key="cc_patient_info_editor")
            if edited_df is not None and not edited_df.equals(df_display):
                _apply_patient_info_edits(edited_df, df_display)
                st.success("Patient information updated successfully!")
                st.rerun()
        else:
            # Show read-only dataframe for non-admin users
            try:
                styled = df_display.style.map(_color_last_visit, subset=["Last Visit Date"]) if "Last Visit Date" in df_display.columns else df_display.style
                st.dataframe(styled, use_container_width=True)
            except Exception:
                st.dataframe(df_display, use_container_width=True)

    except Exception as e:
        st.error(f"Error in Patient Info tab: {e}")


def show_daily_task_log(user_id, role="coordinator"):
    """Display Daily Task Log with today's tasks, metrics, and submission functionality"""
    try:
        st.subheader("Daily Task Log")

        # Get today's tasks
        todays_tasks = database.get_todays_tasks(user_id, role)

        if not todays_tasks:
            st.info("No tasks found for today.")
            # Still show metrics (all zero)
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Tasks Today", 0)
            col2.metric("Unique Patients", 0)
            col3.metric("Total Minutes", 0)
            return

        # Convert to DataFrame for display
        tasks_df = pd.DataFrame(todays_tasks)

        # Calculate metrics
        total_tasks = len(tasks_df)
        unique_patients = tasks_df['patient_name'].nunique() if 'patient_name' in tasks_df.columns else 0
        total_minutes = tasks_df['duration_minutes'].sum() if 'duration_minutes' in tasks_df.columns else 0

        # Display metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks Today", total_tasks)
        col2.metric("Unique Patients", unique_patients)
        col3.metric("Total Minutes", total_minutes)

        # Prepare display columns
        display_columns = []
        if 'task_date' in tasks_df.columns:
            display_columns.append('Time')
        if 'patient_name' in tasks_df.columns:
            display_columns.append('Patient ID / Name')
        if 'task_type' in tasks_df.columns:
            display_columns.append('Task Type')
        if 'duration_minutes' in tasks_df.columns:
            display_columns.append('Minutes Spent')
        if 'notes' in tasks_df.columns:
            display_columns.append('Notes')

        # Rename columns for display
        column_mapping = {
            'task_date': 'Time',
            'patient_name': 'Patient ID / Name',
            'task_type': 'Task Type',
            'duration_minutes': 'Minutes Spent',
            'notes': 'Notes'
        }

        display_df = tasks_df.rename(columns=column_mapping)

        # Format time column
        if 'Time' in display_df.columns:
            display_df['Time'] = pd.to_datetime(display_df['Time']).dt.strftime('%H:%M')

        # Show editable table
        st.markdown("#### Today's Tasks")
        st.markdown("*Edit minutes, task type, or notes if corrections are needed*")

        # Check if tasks are already submitted
        is_submitted = tasks_df['submission_status'].iloc[0] == 'submitted' if 'submission_status' in tasks_df.columns and not tasks_df.empty else False

        if is_submitted:
            st.info("📋 Today's tasks have been submitted and are read-only.")
            # Show read-only table
            st.dataframe(display_df[display_columns], use_container_width=True, hide_index=True)
        else:
            # Show editable table
            edited_df = st.data_editor(
                display_df[display_columns],
                use_container_width=True,
                hide_index=True,
                key=f"daily_tasks_{user_id}_{role}",
                num_rows="fixed"
            )

            # Handle edits
            if edited_df is not None and not edited_df.equals(display_df[display_columns]):
                st.info("💾 Changes saved automatically.")

            # Submit button
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                if st.button("📤 Submit Day", type="primary", use_container_width=True):
                    # Show confirmation dialog
                    confirm_submit = st.checkbox("I confirm that today's task log is accurate and complete.", key=f"confirm_submit_{user_id}")

                    if confirm_submit:
                        # Submit the day's tasks
                        success = database.submit_daily_tasks(user_id, role)
                        if success:
                            st.success("✅ Daily task log submitted successfully! Today's entries are now read-only.")
                            st.balloons()
                            time.sleep(2)  # Give user time to see success message
                            st.rerun()  # Refresh to show read-only state
                        else:
                            st.error("❌ Failed to submit daily tasks. Please try again.")
                    else:
                        st.warning("Please confirm submission by checking the box above.")

    except Exception as e:
        st.error(f"Error loading daily task log: {e}")
        print(f"Daily task log error: {e}")
