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
from src.dashboards.coordinator_task_review_component import show as show_coordinator_task_review
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
                ws.deliverable as current_deliverable
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
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Patient ID:**")
                    st.write(wf['patient_id'])

                with col2:
                    st.write("**Current Step:**")
                    st.write(f"Step {wf['current_step']}: {wf['current_task']}")

                st.write("**Deliverable:**")
                st.write(wf['current_deliverable'])

                # Action buttons with time tracking
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Time Spent (minutes):**")
                    duration = st.number_input(
                        "Minutes",
                        min_value=1,
                        max_value=480,
                        value=15,
                        step=5,
                        key=f"duration_{wf['instance_id']}",
                        help="Enter time spent on this review"
                    )

                with col2:
                    if st.button(f"Complete Review", key=f"complete_{wf['instance_id']}", type="primary"):
                        complete_rr_workflow(
                            instance_id=wf['instance_id'],
                            template_id=wf['template_id'],
                            user_id=user_id,
                            duration_minutes=duration,
                            patient_id=wf['patient_id'],
                            patient_name=wf['patient_name']
                        )
                        st.success("Workflow completed successfully!")
                        time.sleep(1)
                        st.rerun()

    except Exception as e:
        st.error(f"Error loading workflows: {e}")
    finally:
        conn.close()


def complete_rr_workflow(instance_id: int, template_id: int, user_id: int,
                         duration_minutes: int, patient_id: str, patient_name: str):
    """
    Complete the RR workflow step and the entire workflow

    For RR workflows, completing the final step also completes the entire workflow.
    Also creates a coordinator task entry for billing purposes.

    Args:
        instance_id: Workflow instance ID
        template_id: Workflow template ID (determines task type)
        user_id: RR user ID
        duration_minutes: Time spent on review
        patient_id: Patient ID
        patient_name: Patient name
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

        # Get RR user info
        user = conn.execute(
            "SELECT user_id, username, full_name FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        if not user:
            st.error("User not found")
            return

        # Determine task type based on template
        if template_id in [1, 2, 3]:
            task_type = "Results Review - LAB"
        elif template_id in [4, 5, 6]:
            task_type = "Results Review - IMAGING"
        else:
            task_type = "Results Review"

        # Get current month table name
        from datetime import datetime
        current_month_table = f"coordinator_tasks_{datetime.now().strftime('%Y_%m')}"

        # Ensure monthly table exists
        database.ensure_monthly_coordinator_tasks_table()

        # Determine step number and columns based on template
        if template_id in [1, 2, 3]:  # LAB workflows
            step_number = 5
            step_col = "step5_complete"
            notes_col = "step5_notes"
            date_col = "step5_date"
            duration_col = "step5_duration_minutes"
        else:  # IMAGING workflows
            step_number = 4
            step_col = "step4_complete"
            notes_col = "step4_notes"
            date_col = "step4_date"
            duration_col = "step4_duration_minutes"

        # Get existing notes and duration for appending
        existing = conn.execute(
            f"SELECT {notes_col}, {duration_col} FROM workflow_instances WHERE instance_id = ?",
            (instance_id,)
        ).fetchone()

        existing_notes = existing[notes_col] if existing and existing[notes_col] else ""
        existing_duration = existing[duration_col] if existing and existing[duration_col] else 0

        # Append new notes with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        completion_note = f"Results review completed by {user['full_name'] or user['username']} ({duration_minutes} min)"
        new_notes = f"{timestamp}: {completion_note}" if not existing_notes else f"{existing_notes}\n\n{timestamp}: {completion_note}"
        new_duration = existing_duration + duration_minutes

        # Insert into coordinator_tasks for billing
        conn.execute(f"""
            INSERT INTO {current_month_table} (
                coordinator_id,
                patient_id,
                task_date,
                duration_minutes,
                task_type,
                notes,
                source_system,
                created_at_pst
            ) VALUES (?, ?, date('now'), ?, ?, ?, 'DASHBOARD', datetime('now', 'localtime'))
        """, (
            user['user_id'],
            patient_id,
            duration_minutes,
            task_type,
            new_notes
        ))

        # Mark the step and workflow as completed
        conn.execute(f"""
            UPDATE workflow_instances
            SET {step_col} = 1,
                {notes_col} = ?,
                {date_col} = date('now'),
                {duration_col} = ?,
                workflow_status = 'Completed'
            WHERE instance_id = ?
        """, (new_notes, new_duration, instance_id))

        conn.commit()
        st.success(f"Workflow {instance_id} completed and billed ({duration_minutes} minutes)!")
    finally:
        conn.close()


def render_phone_review_tab(user_id: int, user_role_ids: list):
    """Render Phone Review tab - reuse existing component"""
    st.subheader("Phone Reviews")
    show_phone_review_entry(mode='rr', user_id=user_id)


def render_task_review_tab(user_id: int, user_role_ids: list):
    """Render Task Review tab - use coordinator task review component for RR"""
    st.subheader("Task Review")

    # RR users use the coordinator task review component
    # This shows coordinator_tasks_YYYY_MM tables filtered by coordinator_id
    show_coordinator_task_review(user_id=user_id)


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
