"""
Coordinator Manager Dashboard
Purpose: Dedicated interface for Coordinator Managers (role 40) to manage:
  1. Coordinator Tasks - View all coordinator tasks across all coordinators
  2. Patient Reassignment - Reassign patients BETWEEN COORDINATORS ONLY (not providers)
  3. Workflow Assignment - Continue existing workflow assignment capability

Author: AI Agent
Date: December 2025
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from typing import Optional, Tuple

from src import database as db
from src.core_utils import get_user_role_ids

# Role constants
ROLE_ADMIN = 34
ROLE_CARE_PROVIDER = 33
ROLE_CARE_COORDINATOR = 36
ROLE_COORDINATOR_MANAGER = 40


def _execute_coordinator_patient_reassignment(
    patient_id: str, 
    old_coordinator_id, 
    new_coordinator_id, 
    user_id,
    notes: str = ""
) -> bool:
    """
    Execute patient reassignment between coordinators only
    RESTRICTION: Cannot reassign provider assignments, only coordinator assignments
    
    Args:
        patient_id: Patient to reassign
        old_coordinator_id: Current coordinator ID
        new_coordinator_id: New coordinator ID
        user_id: Admin user executing the reassignment
        notes: Optional notes about the reassignment
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not all([patient_id, new_coordinator_id]):
        st.error("Missing required parameters for reassignment")
        return False
    
    try:
        import datetime as dt
        conn = db.get_db_connection()
        
        # Get current assignment info for audit
        audit_timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if assignment exists
        existing_assignment = conn.execute(
            "SELECT id FROM patient_assignments WHERE patient_id = ?",
            (patient_id,)
        ).fetchone()
        
        if existing_assignment:
            # Update existing assignment
            conn.execute(
                "UPDATE patient_assignments SET coordinator_id = ?, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
                (new_coordinator_id, patient_id)
            )
        else:
            # Create new assignment record (keep provider_id if it exists)
            conn.execute(
                "INSERT INTO patient_assignments (patient_id, coordinator_id, created_date, updated_date) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (patient_id, new_coordinator_id)
            )
        
        # Log audit trail
        description = f"Patient {patient_id} reassigned from Coordinator {old_coordinator_id} to Coordinator {new_coordinator_id}"
        if notes:
            description += f" | Notes: {notes}"
        
        conn.execute(
            """INSERT INTO audit_log (action_type, table_name, record_id, old_value, new_value, user_id, timestamp, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "COORDINATOR_REASSIGNMENT",
                "patient_assignments",
                patient_id,
                f"coordinator_id: {old_coordinator_id}",
                f"coordinator_id: {new_coordinator_id}",
                user_id,
                audit_timestamp,
                description
            )
        )
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Error reassigning patient: {str(e)}")
        return False


def show_coordinator_tasks_tab(selected_year: int, selected_month: int):
    """Display all coordinator tasks for selected month - read-only view"""
    
    table_name = f"coordinator_tasks_{selected_year}_{selected_month:02d}"
    
    # Check if table exists
    conn = db.get_db_connection()
    table_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()
    
    if not table_exists:
        st.warning(f"No coordinator tasks data available for {calendar.month_name[selected_month]} {selected_year}")
        conn.close()
        return
    
    # Get total minutes
    total_result = conn.execute(
        f"SELECT SUM(duration_minutes) as total FROM {table_name} WHERE duration_minutes IS NOT NULL"
    ).fetchone()
    total_minutes = int(total_result[0]) if total_result and total_result[0] else 0
    
    st.markdown(f"### Total Coordinator Minutes {calendar.month_name[selected_month]} {selected_year}: **{total_minutes:,}**")
    
    # Load data
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    
    # Join with patients table if available
    if 'patient_id' in df.columns:
        try:
            patients = db.get_all_patients() if hasattr(db, 'get_all_patients') else []
            if patients:
                patients_df = pd.DataFrame(patients)
                required_cols = {'patient_id', 'first_name', 'last_name', 'dob'}
                if not patients_df.empty and required_cols.issubset(patients_df.columns):
                    df = df.merge(
                        patients_df[['patient_id', 'first_name', 'last_name', 'dob']],
                        on='patient_id',
                        how='left'
                    )
        except Exception as e:
            st.warning(f"Could not join patient info: {e}")
    
    conn.close()
    
    # Build coordinator name mapping
    if 'coordinator_name' not in df.columns and 'coordinator_id' in df.columns:
        id_to_name = {}
        coordinators = db.get_users_by_role(ROLE_CARE_COORDINATOR) or []
        for c in coordinators:
            uid = c.get('user_id')
            if uid:
                id_to_name[str(uid)] = c.get('full_name', c.get('username', 'Unknown'))
        
        df['coordinator_name'] = df['coordinator_id'].apply(
            lambda x: id_to_name.get(str(x), str(x)) if pd.notna(x) else None
        )
    
    # Display Coordinator Summary
    st.subheader("Coordinator Monthly Summary")
    
    try:
        if 'coordinator_id' in df.columns:
            coord_summary = df.groupby('coordinator_id').agg({
                'duration_minutes': 'sum',
                'coordinator_name': 'first'
            }).reset_index()
            coord_summary.columns = ['coordinator_id', 'total_minutes', 'Coordinator']
            coord_summary = coord_summary.sort_values('total_minutes', ascending=True)
            
            st.dataframe(coord_summary[['Coordinator', 'total_minutes']], use_container_width=True)
    except Exception as e:
        st.warning(f"Could not display coordinator summary: {e}")
    
    # Display Tasks Table
    st.subheader(f"Coordinator Tasks - {calendar.month_name[selected_month]} {selected_year}")
    
    # Filters
    filter_cols = st.columns(2)
    
    with filter_cols[0]:
        st.markdown("**Coordinator**")
        coord_names = sorted(df['coordinator_name'].dropna().unique()) if 'coordinator_name' in df.columns else []
        selected_coord = st.selectbox("Filter by Coordinator", ["All"] + coord_names, key="cm_coord_filter")
    
    with filter_cols[1]:
        st.markdown("**Patient**")
        if 'patient_name' in df.columns:
            patient_options = [f"{row['patient_name']} ({row['patient_id']})" 
                             for _, row in df[['patient_id', 'patient_name']].drop_duplicates().dropna().iterrows()]
            patient_map = {f"{row['patient_name']} ({row['patient_id']})": row['patient_id']
                          for _, row in df[['patient_id', 'patient_name']].drop_duplicates().dropna().iterrows()}
        else:
            patient_options = [str(pid) for pid in sorted(df['patient_id'].dropna().unique())]
            patient_map = {str(pid): pid for pid in patient_options}
        
        selected_patient = st.selectbox("Filter by Patient", ["All"] + patient_options, key="cm_patient_filter")
    
    # Apply filters
    filtered_df = df.copy()
    if selected_coord != "All":
        filtered_df = filtered_df[filtered_df['coordinator_name'] == selected_coord]
    if selected_patient != "All":
        filtered_df = filtered_df[filtered_df['patient_id'] == patient_map[selected_patient]]
    
    if not filtered_df.empty:
        # Display columns
        preferred_order = [
            'coordinator_name', 'status', 'patient_id', 'patient_name', 'first_name', 'last_name', 'dob',
            'task_type', 'duration_minutes', 'date', 'notes'
        ]
        show_cols = [col for col in preferred_order if col in filtered_df.columns]
        
        st.data_editor(
            filtered_df[show_cols],
            use_container_width=True,
            num_rows="dynamic",
            height=600,
            key="cm_coordinator_tasks_editor"
        )
    else:
        st.info("No tasks found for the selected filters.")


def show_patient_reassignment_tab(user_id: int):
    """
    Display patient reassignment interface
    RESTRICTION: Can ONLY reassign patients between coordinators, not providers
    """
    
    st.subheader("🔄 Patient Reassignment (Coordinator-to-Coordinator)")
    st.markdown("Reassign patients between coordinators to balance workload and manage team capacity.")
    
    # Get all coordinators
    try:
        coordinators = db.get_users_by_role(ROLE_CARE_COORDINATOR) or []
        coordinator_map = {c['full_name']: c['user_id'] for c in coordinators}
    except Exception as e:
        st.error(f"Error loading coordinators: {e}")
        return
    
    # Reassignment Method
    reassignment_method = st.radio(
        "Reassignment Method",
        ["Individual Patient", "Bulk Reassignment"],
        key="cm_reassignment_method",
        horizontal=True
    )
    
    if reassignment_method == "Individual Patient":
        st.markdown("#### Reassign Single Patient")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Search for patient
            patient_search = st.text_input(
                "Search Patient by Name or ID",
                key="cm_patient_search",
                placeholder="Enter patient name or ID..."
            )
            
            if patient_search:
                try:
                    all_patients = db.get_all_patient_panel() if hasattr(db, 'get_all_patient_panel') else []
                    patients_df = pd.DataFrame(all_patients)
                    
                    if not patients_df.empty:
                        search_lower = patient_search.lower()
                        mask = pd.Series(False, index=patients_df.index)
                        
                        if 'first_name' in patients_df.columns:
                            mask |= patients_df['first_name'].fillna('').astype(str).str.lower().str.contains(search_lower)
                        if 'last_name' in patients_df.columns:
                            mask |= patients_df['last_name'].fillna('').astype(str).str.lower().str.contains(search_lower)
                        if 'patient_id' in patients_df.columns:
                            mask |= patients_df['patient_id'].fillna('').astype(str).str.lower().str.contains(search_lower)
                        
                        filtered_patients = patients_df[mask]
                        
                        if not filtered_patients.empty:
                            patient_options = [
                                f"{row.get('last_name', '')} {row.get('first_name', '')} ({row.get('patient_id', '')})"
                                for _, row in filtered_patients.head(10).iterrows()
                            ]
                            
                            selected_patient_display = st.selectbox(
                                "Select Patient",
                                patient_options,
                                key="cm_selected_patient"
                            )
                            
                            # Extract patient_id
                            selected_patient_id = selected_patient_display.split('(')[-1].rstrip(')')
                            
                            # Get current coordinator
                            try:
                                patient_data = filtered_patients[
                                    filtered_patients['patient_id'] == selected_patient_id
                                ].iloc[0]
                                
                                current_coord_id = patient_data.get('assigned_coordinator_id')
                                current_coord_name = patient_data.get('care_coordinator_name', 'Unassigned')
                                
                                st.info(f"**Current Coordinator:** {current_coord_name}")
                                
                            except Exception as e:
                                st.warning("Could not determine current coordinator")
                                current_coord_id = None
                        else:
                            st.warning(f"No patients found matching '{patient_search}'")
                            selected_patient_id = None
                
                except Exception as e:
                    st.error(f"Error searching patients: {e}")
                    selected_patient_id = None
        
        with col2:
            # Select new coordinator
            st.markdown("**New Coordinator**")
            
            if patient_search and selected_patient_id:
                new_coord_name = st.selectbox(
                    "Assign to Coordinator",
                    sorted(coordinator_map.keys()),
                    key="cm_new_coordinator"
                )
                new_coordinator_id = coordinator_map[new_coord_name]
                
                # Reassign button
                st.markdown("")
                if st.button("🔄 Reassign Patient", key="cm_execute_individual", type="primary"):
                    if _execute_coordinator_patient_reassignment(
                        selected_patient_id,
                        current_coord_id,
                        new_coordinator_id,
                        user_id
                    ):
                        st.success(f"Patient {selected_patient_id} reassigned to {new_coord_name}")
                        st.rerun()
            else:
                st.info("Search for a patient to select a new coordinator")
    
    else:  # Bulk Reassignment
        st.markdown("#### Bulk Patient Reassignment")
        st.info("Select multiple patients or all patients from a coordinator and reassign them to a new coordinator.")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**From Coordinator**")
            from_coord_name = st.selectbox(
                "Select source coordinator",
                sorted(coordinator_map.keys()),
                key="cm_from_coordinator"
            )
            from_coordinator_id = coordinator_map[from_coord_name]
            
            # Get all patients for this coordinator
            try:
                all_patients = db.get_all_patient_panel() if hasattr(db, 'get_all_patient_panel') else []
                if all_patients:
                    patients_df = pd.DataFrame(all_patients)
                    coord_patients = patients_df[
                        patients_df['assigned_coordinator_id'] == from_coordinator_id
                    ].copy()
                    
                    st.metric("Patients to Reassign", len(coord_patients))
                    
                    # Show list
                    with st.expander(f"View {len(coord_patients)} patients from {from_coord_name}"):
                        if not coord_patients.empty:
                            display_cols = ['patient_id', 'first_name', 'last_name', 'status']
                            show_cols = [c for c in display_cols if c in coord_patients.columns]
                            st.dataframe(
                                coord_patients[show_cols],
                                use_container_width=True,
                                height=300
                            )
                        else:
                            st.info(f"No patients assigned to {from_coord_name}")
                
            except Exception as e:
                st.error(f"Error loading coordinator patients: {e}")
                coord_patients = pd.DataFrame()
        
        with col2:
            st.markdown("**To Coordinator(s)**")
            
            # Option to split or send to single coordinator
            distribute_method = st.radio(
                "Distribution Method",
                ["Send All to One", "Split Between Multiple"],
                key="cm_distribute_method",
                horizontal=True
            )
            
            if distribute_method == "Send All to One":
                to_coord_name = st.selectbox(
                    "Select destination coordinator",
                    [name for name in sorted(coordinator_map.keys()) if name != from_coord_name],
                    key="cm_to_coordinator_single"
                )
                to_coordinator_ids = [coordinator_map[to_coord_name]]
                
                # Execute bulk reassignment
                if not coord_patients.empty and st.button("🔄 Reassign All Patients", key="cm_execute_bulk_single", type="primary"):
                    success_count = 0
                    for _, patient in coord_patients.iterrows():
                        if _execute_coordinator_patient_reassignment(
                            patient['patient_id'],
                            from_coordinator_id,
                            to_coordinator_ids[0],
                            user_id,
                            notes=f"Bulk reassignment from {from_coord_name} to {to_coord_name}"
                        ):
                            success_count += 1
                    
                    st.success(f"Successfully reassigned {success_count} of {len(coord_patients)} patients to {to_coord_name}")
                    st.rerun()
            
            else:  # Split between multiple
                # Multi-select for destination coordinators
                dest_coords = [name for name in sorted(coordinator_map.keys()) if name != from_coord_name]
                selected_dest_coords = st.multiselect(
                    "Select destination coordinators",
                    dest_coords,
                    key="cm_to_coordinators_split",
                    help="Select 2+ coordinators to split the workload"
                )
                
                if selected_dest_coords and not coord_patients.empty:
                    # Show split preview
                    st.markdown(f"**Split Preview:** {len(coord_patients)} patients → {len(selected_dest_coords)} coordinators")
                    
                    patients_per_coord = len(coord_patients) // len(selected_dest_coords)
                    remainder = len(coord_patients) % len(selected_dest_coords)
                    
                    for i, coord_name in enumerate(selected_dest_coords):
                        num_patients = patients_per_coord + (1 if i < remainder else 0)
                        st.caption(f"{coord_name}: {num_patients} patients")
                    
                    if st.button("🔄 Execute Split Reassignment", key="cm_execute_bulk_split", type="primary"):
                        # Distribute patients
                        coord_list = [coordinator_map[name] for name in selected_dest_coords]
                        patient_list = coord_patients['patient_id'].tolist()
                        
                        success_count = 0
                        for idx, patient_id in enumerate(patient_list):
                            # Round-robin distribution
                            target_coord_id = coord_list[idx % len(coord_list)]
                            target_coord_name = [name for name, uid in coordinator_map.items() if uid == target_coord_id][0]
                            
                            if _execute_coordinator_patient_reassignment(
                                patient_id,
                                from_coordinator_id,
                                target_coord_id,
                                user_id,
                                notes=f"Split reassignment from {from_coord_name} to {target_coord_name}"
                            ):
                                success_count += 1
                        
                        st.success(f"Successfully split {success_count} of {len(patient_list)} patients")
                        st.rerun()


def show_workflow_assignment_tab(user_id: int):
    """Display workflow assignment interface - delegate to existing module"""
    
    st.subheader("📋 Workflow Assignment for Coordinators")
    st.markdown("Assign new workflows to coordinators and manage workflow queue distribution.")
    
    try:
        from src.dashboards.workflow_module import show_workflow_management
        
        # Get all coordinators for workflow assignment
        coordinators = db.get_users_by_role(ROLE_CARE_COORDINATOR) or []
        
        # Get coordinator IDs for filtering
        coordinator_ids = [c['user_id'] for c in coordinators]
        
        # For workflow management, we pass coordinator_id as user_id context
        show_workflow_management(
            user_id=user_id,
            coordinator_id=user_id,  # Coordinator Manager's ID
            active_patients=[],  # Not filtering by specific coordinator's patients
            filtered_patients=[],
            user_role_ids=[ROLE_COORDINATOR_MANAGER]
        )
        
    except ImportError as e:
        st.error(f"Workflow module not found: {e}")
    except Exception as e:
        st.error(f"Error in workflow assignment: {e}")


def show(user_id: int, user_role_ids=None):
    """Main Coordinator Manager Dashboard"""
    
    if user_role_ids is None:
        user_role_ids = []
    
    # Check coordinator manager role
    has_cm_role = ROLE_COORDINATOR_MANAGER in user_role_ids
    
    if not has_cm_role:
        st.warning("⚠️ **Access Restricted**")
        st.info("This dashboard is only available to Coordinator Managers (role 40).")
        st.markdown("If you believe you should have access, please contact your administrator.")
        return
    
    st.title("👥 Coordinator Manager Dashboard")
    st.markdown("Manage coordinator team workload, patient assignments, and workflow distribution.")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "Coordinator Tasks",
        "Patient Reassignment",
        "Workflow Assignment"
    ])
    
    # Month selection for coordinator tasks tab
    import datetime as dt
    now = dt.datetime.now()
    current_year = now.year
    current_month = now.month
    
    # Get available months
    conn = db.get_db_connection()
    available_tables = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'coordinator_tasks_20%'
        ORDER BY name DESC
    """).fetchall()
    conn.close()
    
    available_months = []
    for table in available_tables:
        try:
            parts = table[0].split('_')
            if len(parts) >= 3:
                year = int(parts[2])
                month = int(parts[3])
                available_months.append((year, month))
        except:
            continue
    
    available_months = sorted(set(available_months), reverse=True)
    
    # --- TAB 1: Coordinator Tasks ---
    with tab1:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if available_months:
                month_options = [f"{calendar.month_name[m]} {y}" for y, m in available_months]
                month_values = available_months
                
                default_idx = 0
                for i, (y, m) in enumerate(month_values):
                    if y == current_year and m == current_month:
                        default_idx = i
                        break
                
                selected_month_text = st.selectbox(
                    "Select Month",
                    month_options,
                    index=default_idx,
                    key="cm_month_select"
                )
                selected_year, selected_month = month_values[month_options.index(selected_month_text)]
            else:
                st.warning("No coordinator tasks data available")
                selected_year, selected_month = current_year, current_month
        
        with col2:
            st.markdown(f"### Coordinator Tasks - {calendar.month_name[selected_month]} {selected_year}")
        
        show_coordinator_tasks_tab(selected_year, selected_month)
    
    # --- TAB 2: Patient Reassignment ---
    with tab2:
        show_patient_reassignment_tab(user_id)
    
    # --- TAB 3: Workflow Assignment ---
    with tab3:
        show_workflow_assignment_tab(user_id)
