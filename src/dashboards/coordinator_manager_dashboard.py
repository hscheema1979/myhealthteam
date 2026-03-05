"""
Coordinator Manager Dashboard
Purpose: Dedicated interface for Coordinator Managers (role 40) to manage:
  1. Coordinator Tasks - View all coordinator tasks across all coordinators
  2. Patient Reassignment - Reassign patients BETWEEN COORDINATORS ONLY (not providers)
  3. Workflow Assignment - Continue existing workflow assignment capability
  4. Workflow Analytics & Unassigned - Monitor workflow performance and assign unassigned patients

Author: AI Agent
Date: December 2025
Updated: March 2026 - Added Workflow Analytics & Unassigned tab
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from typing import Optional, Tuple

from src import database as db
from src.core_utils import get_user_role_ids

# Import the centralized coordinator tasks module for consistent views across dashboards
from src.dashboards.coordinator_tasks_module import show_coordinator_tasks_tab as show_unified_coordinator_tasks_tab

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

        # Also update the patients table for consistency
        conn.execute(
            "UPDATE patients SET coordinator_id = ? WHERE patient_id = ?",
            (new_coordinator_id, patient_id)
        )

        conn.commit()
        conn.close()

        st.success(f"✓ Patient {patient_id} successfully reassigned to Coordinator {new_coordinator_id}")
        return True

    except Exception as e:
        st.error(f"Error reassigning patient: {e}")
        return False


def show_patient_reassignment_tab(user_id: int):
    """Show patient reassignment tab for coordinator-to-coordinator reassignment"""

    st.subheader("Patient Reassignment (Coordinator-to-Coordinator Only)")
    st.info("ℹ️ **Coordinator Managers can reassign patients between coordinators**. Provider assignments remain unchanged.")

    # Get all active patients with coordinator assignments
    conn = db.get_db_connection()
    try:
        patients_df = pd.read_sql_query("""
            SELECT
                p.patient_id,
                p.full_name,
                p.facility,
                p.coordinator_id,
                u.full_name as coordinator_name,
                p.provider_id,
                p.status
            FROM patients p
            LEFT JOIN users u ON p.coordinator_id = u.user_id
            WHERE p.status = 'Active'
            ORDER BY p.last_name, p.first_name
        """, conn)
    finally:
        conn.close()

    if patients_df.empty:
        st.info("No active patients found.")
        return

    # Add selection column
    patients_df['Select'] = False

    # Display patient list with selection
    st.markdown("#### Step 1: Select Patient(s) to Reassign")
    edited_df = st.data_editor(
        patients_df[['patient_id', 'Select', 'full_name', 'facility', 'coordinator_name', 'status']],
        column_config={
            'Select': st.column_config.CheckboxColumn("Select for Reassignment"),
            'patient_id': 'Patient ID',
            'full_name': 'Patient Name',
            'facility': 'Facility',
            'coordinator_name': 'Current Coordinator',
            'status': 'Status'
        },
        use_container_width=True,
        hide_index=True
    )

    # Get selected patients
    selected_patients = edited_df[edited_df['Select'] == True]

    if selected_patients.empty:
        st.info("Select one or more patients above to reassign.")
        return

    # Get available coordinators
    coordinators = db.get_users_by_role(ROLE_CARE_COORDINATOR)

    if not coordinators:
        st.warning("No coordinators available for reassignment.")
        return

    coordinator_options = {f"{c['full_name']} (ID: {c['user_id']})": c['user_id'] for c in coordinators}

    st.markdown("#### Step 2: Select New Coordinator")
    new_coordinator = st.selectbox(
        "Assign to Coordinator",
        options=list(coordinator_options.keys()),
        key="cm_new_coordinator"
    )

    new_coordinator_id = coordinator_options[new_coordinator]

    # Notes
    notes = st.text_area("Reassignment Notes (Optional)", key="cm_reassign_notes")

    # Execute reassignment
    if st.button("Execute Reassignment", type="primary", key="cm_execute_reassign"):
        success_count = 0
        for _, patient in selected_patients.iterrows():
            patient_id = patient['patient_id']
            old_coordinator_id = patient['coordinator_id']

            if old_coordinator_id == new_coordinator_id:
                st.warning(f"Patient {patient_id} is already assigned to this coordinator.")
                continue

            if _execute_coordinator_patient_reassignment(
                patient_id, old_coordinator_id, new_coordinator_id, user_id, notes
            ):
                success_count += 1

        if success_count > 0:
            st.success(f"Successfully reassigned {success_count} patient(s)")
            st.rerun()


def show_workflow_assignment_tab(user_id: int):
    """Show workflow assignment tab for coordinators"""

    st.subheader("Workflow Assignment")
    st.info("ℹ️ Assign workflow templates to new patients and track their progress through the workflow.")

    # Get available workflow templates
    templates = db.get_available_workflows()

    if not templates:
        st.warning("No workflow templates available.")
        return

    # Get unassigned active patients (patients without workflows)
    conn = db.get_db_connection()
    try:
        unassigned_patients = pd.read_sql_query("""
            SELECT
                p.patient_id,
                p.full_name,
                p.facility,
                p.status,
                p.coordinator_id,
                u.full_name as coordinator_name
            FROM patients p
            LEFT JOIN users u ON p.coordinator_id = u.user_id
            WHERE p.status = 'Active'
              AND NOT EXISTS (
                  SELECT 1 FROM workflow_instances wi
                  WHERE wi.patient_id = p.patient_id
                    AND wi.workflow_status = 'Active'
              )
            ORDER BY p.last_name, p.first_name
            LIMIT 50
        """, conn)
    finally:
        conn.close()

    if unassigned_patients.empty:
        st.info("All active patients have active workflows.")
        return

    # Workflow assignment form
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Step 1: Select Workflow Template")
        template_options = {t['template_name']: t['template_id'] for t in templates}
        selected_template = st.selectbox("Workflow Template", options=list(template_options.keys()))

    with col2:
        st.markdown("#### Step 2: Select Patient")
        patient_options = {f"{p['full_name']} (ID: {p['patient_id']})": p['patient_id']
                          for _, p in unassigned_patients.iterrows()}
        selected_patient = st.selectbox("Patient", options=list(patient_options.keys()))

    # Notes
    notes = st.text_area("Assignment Notes (Optional)", key="cm_workflow_notes")

    # Show template details
    template_id = template_options[selected_template]
    template_details = next((t for t in templates if t['template_id'] == template_id), None)

    if template_details:
        with st.expander("📋 Workflow Template Details", expanded=False):
            st.markdown(f"**Template**: {template_details['template_name']}")
            # You could add more details here if needed

    # Execute assignment
    if st.button("Assign Workflow", type="primary", key="cm_assign_workflow"):
        patient_id = patient_options[selected_patient]

        try:
            from src.utils.workflow_utils import create_workflow_instance

            instance_id = create_workflow_instance(
                template_id=template_id,
                patient_id=patient_id,
                coordinator_id=unassigned_patients[unassigned_patients['patient_id'] == patient_id]['coordinator_id'].values[0],
                notes=notes
            )

            if instance_id:
                st.success(f"✓ Workflow instance created successfully (ID: {instance_id})")
                st.rerun()
            else:
                st.error("Failed to create workflow instance")

        except Exception as e:
            st.error(f"Error in workflow assignment: {e}")


def show(user_id: int, user_role_ids=None):
    """Main Coordinator Manager Dashboard"""

    if user_role_ids is None:
        user_role_ids = []

    # Check coordinator manager role
    has_cm_role = ROLE_COORDINATOR_MANAGER in user_role_ids

    if not has_cm_role:
        st.warning("**Access Restricted**")
        st.info("This dashboard is only available to Coordinator Managers (role 40).")
        st.markdown("If you believe you should have access, please contact your administrator.")
        return

    st.title("Coordinator Manager Dashboard")
    st.markdown("Manage coordinator team workload, patient assignments, and workflow distribution.")

    # Create tabs
    tab1, tab2, tab3, tab_zmo, tab_analytics = st.tabs([
        "Coordinator Tasks",
        "Patient Reassignment",
        "Workflow Assignment",
        "ZMO (Patient Data)",
        "Analytics & Unassigned"
    ])

    # --- TAB 1: Coordinator Tasks ---
    # Use the centralized coordinator_tasks_module for consistent view with admin dashboard
    with tab1:
        # Call the unified coordinator tasks tab from the centralized module
        # This ensures CM/CC users see the same Patient Monthly Summary and
        # Coordinator Monthly Summary as the admin dashboard
        show_unified_coordinator_tasks_tab(
            user_id=user_id,
            user_role_ids=user_role_ids,
            show_all_coordinators=True,  # Coordinator Managers can see all coordinators
            filter_by_coordinator=False
        )

    # --- TAB 2: Patient Reassignment ---
    with tab2:
        show_patient_reassignment_tab(user_id)

    # --- TAB 3: Workflow Assignment ---
    with tab3:
        show_workflow_assignment_tab(user_id)

    # --- TAB 4: ZMO (Patient Data) ---
    with tab_zmo:
        from src.zmo_module import render_zmo_tab
        render_zmo_tab(user_id=user_id)

    # --- TAB 5: Workflow Analytics & Unassigned Patients ---
    with tab_analytics:
        # Import the new workflow analytics and unassigned patients module
        from src.dashboards.workflow_analytics_unassigned_module import show_workflow_analytics_unassigned_tab

        # Show the workflow analytics and unassigned patients tab
        show_workflow_analytics_unassigned_tab(
            user_id=user_id,
            user_role_ids=user_role_ids
        )
