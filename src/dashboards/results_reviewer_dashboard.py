"""
Results Reviewer Dashboard

This dashboard is for users with the Results Reviewer (RR) role (role_id 43).
RR users review lab and imaging results and coordinate with providers and patients.

Workflow Integration:
- RR sees workflows that have reached the final RR step
- For LAB workflows (templates 1-3): Step 5 is the RR step
- For IMAGING workflows (templates 4-6): Step 4 is the RR step
- Completing the RR step also completes the entire workflow
"""

import time
from datetime import datetime, timedelta, date
from typing import Optional

import pandas as pd
import streamlit as st

from src import database
from src.core_utils import get_user_role_ids
from src.dashboards.phone_review import show_phone_review_entry
from src.dashboards.coordinator_task_review_component import show as show_monthly_task_review
from src.zmo_module import render_zmo_tab


def render_results_review_tab(user_id: int, user_role_ids: list):
    """
    Render the Results Review tab - shows workflows at RR step

    RR users see workflows where:
    - Template is LAB (1-3) and current_step = 5
    - Template is IMAGING (4-6) and current_step = 4
    """
    st.subheader("Results Review Workflows")

    # Get RR workflows
    conn = database.get_db_connection()
    try:
        # Query for workflows at RR step
        rr_workflows = conn.execute("""
            SELECT
                wi.instance_id,
                wi.patient_id,
                wi.patient_name,
                wi.template_id,
                wt.template_name,
                wi.current_step,
                wi.workflow_status,
                wi.created_at,
                ws.task_name as current_task,
                ws.deliverable as current_deliverable,
                wi.notes
            FROM workflow_instances wi
            JOIN workflow_templates wt ON wi.template_id = wt.template_id
            LEFT JOIN workflow_steps ws ON wi.template_id = ws.template_id AND wi.current_step = ws.step_order
            WHERE wi.template_id IN (1, 2, 3, 4, 5, 6)
              AND (
                  (wi.template_id IN (1, 2, 3) AND wi.current_step = 5) OR
                  (wi.template_id IN (4, 5, 6) AND wi.current_step = 4)
              )
              AND wi.workflow_status = 'Active'
            ORDER BY wi.created_at DESC
        """).fetchall()

        if not rr_workflows:
            st.info("No workflows currently awaiting results review.")
            return

        # Display workflows
        st.write(f"**{len(rr_workflows)} workflow(s) awaiting review**")

        for wf in rr_workflows:
            with st.expander(
                f"{wf['template_name']} - {wf['patient_name']} "
                f"(Created: {wf['created_at'][:10]})"
            ):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write("**Patient ID:**")
                    st.write(wf['patient_id'])

                with col2:
                    st.write("**Current Step:**")
                    st.write(f"Step {wf['current_step']}: {wf['current_task']}")

                with col3:
                    st.write("**Status:**")
                    st.write(wf['workflow_status'])

                st.write("**Deliverable:**")
                st.write(wf['current_deliverable'])

                if wf['notes']:
                    st.write("**Existing Notes:**")
                    st.info(wf['notes'])

                # Action buttons
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button(f"Complete Review", key=f"complete_{wf['instance_id']}"):
                        complete_rr_workflow(wf['instance_id'], wf['template_id'])
                        st.success("Workflow completed successfully!")
                        time.sleep(1)
                        st.rerun()

                with col2:
                    if st.button(f"Add Note", key=f"note_{wf['instance_id']}"):
                        add_workflow_note(wf['instance_id'])

                with col3:
                    if st.button(f"View Details", key=f"view_{wf['instance_id']}"):
                        view_workflow_details(wf['instance_id'])

    finally:
        conn.close()


def complete_rr_workflow(instance_id: int, template_id: int):
    """
    Complete the RR workflow step and the entire workflow

    For RR workflows, completing the final step also completes the entire workflow
    """
    conn = database.get_db_connection()
    try:
        # Get workflow info
        workflow = conn.execute(
            "SELECT * FROM workflow_instances WHERE instance_id = ?",
            (instance_id,)
        ).fetchone()

        if not workflow:
            st.error("Workflow not found")
            return

        # Mark the current step as completed
        conn.execute(
            "UPDATE workflow_instances SET workflow_status = 'Completed' WHERE instance_id = ?",
            (instance_id,)
        )

        # Log completion
        conn.execute(
            """INSERT INTO workflow_progress_log
               (instance_id, step_number, completed_at, completed_by, notes)
               VALUES (?, ?, datetime('now'), 'RR', 'Workflow completed by Results Reviewer')""",
            (instance_id, workflow['current_step'])
        )

        conn.commit()
        st.success(f"Workflow {instance_id} marked as complete!")
    finally:
        conn.close()


def add_workflow_note(instance_id: int):
    """Add a note to the workflow"""
    note = st.text_area("Enter note:", key=f"note_input_{instance_id}")

    if st.button("Save Note", key=f"save_note_{instance_id}"):
        if note:
            conn = database.get_db_connection()
            try:
                # Append note to existing notes
                conn.execute(
                    """UPDATE workflow_instances
                       SET notes = CASE
                           WHEN notes IS NULL THEN ?
                           ELSE notes || '\n\n' || ?
                       END
                       WHERE instance_id = ?""",
                    (note, note, instance_id)
                )
                conn.commit()
                st.success("Note added successfully!")
                time.sleep(1)
                st.rerun()
            finally:
                conn.close()


def view_workflow_details(instance_id: int):
    """View detailed workflow information"""
    conn = database.get_db_connection()
    try:
        # Get workflow instance details
        workflow = conn.execute(
            """SELECT wi.*, wt.template_name
               FROM workflow_instances wi
               JOIN workflow_templates wt ON wi.template_id = wt.template_id
               WHERE wi.instance_id = ?""",
            (instance_id,)
        ).fetchone()

        if workflow:
            st.json(dict(workflow))

        # Get workflow progress
        progress = conn.execute(
            """SELECT wpl.*, ws.task_name
               FROM workflow_progress_log wpl
               LEFT JOIN workflow_steps ws ON wpl.step_number = ws.step_order AND wpl.instance_id IN (
                   SELECT instance_id FROM workflow_instances WHERE template_id IN (1,2,3,4,5,6)
               )
               WHERE wpl.instance_id = ?
               ORDER BY wpl.completed_at DESC""",
            (instance_id,)
        ).fetchall()

        if progress:
            st.write("**Progress History:**")
            for p in progress:
                st.write(f"- Step {p['step_number']}: {p['task_name']} - {p['completed_at']}")

    finally:
        conn.close()


def render_phone_review_tab(user_id: int, user_role_ids: list):
    """Render Phone Review tab - reuse existing component"""
    st.subheader("Phone Reviews")
    show_phone_review_entry(mode='rr', user_id=user_id)


def render_task_review_tab(user_id: int, user_role_ids: list):
    """Render Task Review tab - reuse existing component"""
    st.subheader("Task Review")

    # Get RR role info for filtering
    conn = database.get_db_connection()
    try:
        # Get tasks assigned to RR user
        show_monthly_task_review(user_id=user_id)
    finally:
        conn.close()


def render_help_tab():
    """Render Help tab"""
    st.subheader("Results Reviewer Dashboard Help")

    st.write("""
    ### Dashboard Overview

    Welcome to the Results Reviewer (RR) Dashboard. As a Results Reviewer, you are responsible for:

    1. **Results Review** - Reviewing lab and imaging results and coordinating with providers and patients
    2. **Phone Reviews** - Handling phone inquiries from patients
    3. **Task Management** - Tracking and completing assigned tasks
    4. **Patient Data** - Accessing patient information through the ZMO module

    ### Results Review Workflow

    Results Review workflows are assigned when:
    - **LAB workflows** (Routine, Urgent, Future) reach Step 5
    - **IMAGING workflows** (Routine, Urgent, Future) reach Step 4

    At this point:
    - Care Coordinators have completed all initial steps (ordering, confirming collection/receipt)
    - Results have been received and are ready for review
    - You need to review the results and coordinate with the provider and patient

    ### Completing a Workflow

    When you complete a review:
    1. Review the patient's results
    2. Coordinate with the Care Provider (CP)
    3. Inform the patient of the results
    4. Click **"Complete Review"** to finish the workflow

    **Note:** Completing the RR step also completes the entire workflow. The workflow will
    be marked as "Completed" and will no longer appear on any dashboard.

    ### Workflow Steps

    **LAB Workflows (5 steps):**
    1. Send lab order, confirm receipt (CC)
    2. Confirm labs were collected/drawn (CC)
    3. Confirm received results (CC)
    4. Care Coordinator confirms results received (CC)
    5. **Review Patient Results and inform patient/provider (RR)** ← You are here

    **IMAGING Workflows (4 steps):**
    1. Send imaging order, confirm receipt (CC)
    2. Confirm received results (CC)
    3. Care Coordinator confirms results received (CC)
    4. **Review Patient Results and inform patient/provider (RR)** ← You are here

    ### Need Help?

    Contact your system administrator for assistance.
    """)


def show_results_reviewer_dashboard(user_id: int):
    """
    Main entry point for Results Reviewer dashboard

    Args:
        user_id: The user_id of the logged-in RR user
    """
    # Get user roles
    user_role_ids = get_user_role_ids(user_id)

    # Verify user has RR role
    ROLE_RESULTS_REVIEWER = 43  # RR role ID
    if ROLE_RESULTS_REVIEWER not in user_role_ids:
        st.error("You do not have permission to access the Results Reviewer Dashboard")
        st.stop()

    # Page title
    st.title("Results Reviewer Dashboard")

    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Results Review",
        "Phone Reviews",
        "Task Review",
        "ZMO (Patient Data)",
        "Help"
    ])

    with tab1:
        render_results_review_tab(user_id, user_role_ids)

    with tab2:
        render_phone_review_tab(user_id, user_role_ids)

    with tab3:
        render_task_review_tab(user_id, user_role_ids)

    with tab4:
        render_zmo_tab(user_id=user_id)

    with tab5:
        render_help_tab()


if __name__ == "__main__":
    # For testing purposes
    show_results_reviewer_dashboard(user_id=1)
