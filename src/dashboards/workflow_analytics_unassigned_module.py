"""
Workflow Analytics & Unassigned Patient Management Module

This module provides two main features for dashboards:
1. Workflow Analytics & Monitoring (FR-2.x)
   - Step-level metrics (completion time, throughput)
   - Delay/Late tracking
   - Stagnation alerts

2. Unassigned Patient Management (FR-3.x)
   - Andrew's View (custom filtered view)
   - Jan's View (custom filtered view)
   - Filter for unassigned active patients

Compatible with: Admin Dashboard, Care Coordinator Dashboard, Coordinator Manager Dashboard
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sqlite3

# Import database and utilities
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import get_db_connection
from config.ui_style_config import get_section_title, get_metric_label, TextStyle


# =============================================================================
# DATABASE QUERY FUNCTIONS - WORKFLOW ANALYTICS
# =============================================================================

@st.cache_data(ttl=300)
def get_workflow_step_analytics() -> pd.DataFrame:
    """
    FR-2.1: Get step-level metrics for all workflow steps.
    Returns completion time and throughput for each step.
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT
            ws.step_id,
            ws.template_id,
            wt.template_name,
            ws.step_order,
            ws.task_name,
            ws.owner,
            ws.deliverable,
            ws.cycle_time as expected_cycle_time,
            COUNT(DISTINCT wi.instance_id) as total_instances,
            COUNT(DISTINCT CASE WHEN wi.step1_complete THEN wi.instance_id END) as step1_completions,
            COUNT(DISTINCT CASE WHEN wi.step2_complete THEN wi.instance_id END) as step2_completions,
            COUNT(DISTINCT CASE WHEN wi.step3_complete THEN wi.instance_id END) as step3_completions,
            COUNT(DISTINCT CASE WHEN wi.step4_complete THEN wi.instance_id END) as step4_completions,
            COUNT(DISTINCT CASE WHEN wi.step5_complete THEN wi.instance_id END) as step5_completions,
            COUNT(DISTINCT CASE WHEN wi.step6_complete THEN wi.instance_id END) as step6_completions,
            AVG(CASE
                WHEN wi.workflow_status = 'Completed' AND wi.completed_at IS NOT NULL
                THEN julianday(wi.completed_at) - julianday(wi.created_at)
                ELSE NULL
            END) as avg_completion_days
        FROM workflow_steps ws
        JOIN workflow_templates wt ON ws.template_id = wt.template_id
        LEFT JOIN workflow_instances wi ON wt.template_id = wi.template_id
        GROUP BY ws.step_id, wt.template_name, ws.step_order, ws.task_name, ws.owner, ws.deliverable, ws.cycle_time
        ORDER BY wt.template_name, ws.step_order
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=300)
def get_workflow_delay_tracking() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    FR-2.2: Identify delayed and late workflows.
    - Delayed: Exceeds internal benchmarks (cycle_time * 1.5)
    - Late: Exceeds hard deadlines (cycle_time * 2.0)

    Returns:
        - delayed_df: Workflows exceeding internal benchmarks
        - late_df: Workflows exceeding hard deadlines
    """
    conn = get_db_connection()
    try:
        # Get active workflows with time tracking
        query = """
        SELECT
            wi.instance_id,
            wt.template_name,
            wi.patient_id,
            wi.patient_name,
            wi.coordinator_id,
            wi.coordinator_name,
            wi.current_step,
            wi.workflow_status,
            wi.created_at,
            wi.updated_at,
            ws.cycle_time as expected_cycle_time_days,
            CAST(julianday('now') - julianday(wi.created_at) AS INTEGER) as days_in_workflow,
            CAST(julianday('now') - julianday(wi.updated_at) AS INTEGER) as days_since_update
        FROM workflow_instances wi
        JOIN workflow_templates wt ON wi.template_id = wt.template_id
        LEFT JOIN workflow_steps ws ON wt.template_id = ws.template_id AND wi.current_step = ws.step_order
        WHERE wi.workflow_status = 'Active'
        ORDER BY wi.created_at DESC
        """
        df = pd.read_sql_query(query, conn)

        # Calculate delayed and late
        if not df.empty:
            # Convert to numeric, handling any string values
            df['expected_cycle_time_days'] = pd.to_numeric(df['expected_cycle_time_days'], errors='coerce')
            df['days_in_workflow'] = pd.to_numeric(df['days_in_workflow'], errors='coerce')

            # Fill NULL values with a default (7 days if cycle_time is NULL)
            df['expected_cycle_time_days'] = df['expected_cycle_time_days'].fillna(7.0)

            # Delayed: Exceeds 150% of expected cycle time
            df['is_delayed'] = df['days_in_workflow'] > (df['expected_cycle_time_days'] * 1.5)

            # Late: Exceeds 200% of expected cycle time
            df['is_late'] = df['days_in_workflow'] > (df['expected_cycle_time_days'] * 2.0)

            delayed_df = df[df['is_delayed'] == True].copy()
            late_df = df[df['is_late'] == True].copy()
        else:
            delayed_df = pd.DataFrame()
            late_df = pd.DataFrame()

        return delayed_df, late_df
    finally:
        conn.close()


@st.cache_data(ttl=300)
def get_stagnant_workflows(hours_threshold: int = 48) -> pd.DataFrame:
    """
    FR-2.3: Identify workflows that haven't been touched within threshold.

    Args:
        hours_threshold: Hours since last update (default: 48)

    Returns:
        DataFrame of stagnant workflows with hours since last update
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT
            wi.instance_id,
            wt.template_name,
            wi.patient_id,
            wi.patient_name,
            wi.coordinator_id,
            wi.coordinator_name,
            wi.current_step,
            wi.workflow_status,
            wi.created_at,
            wi.updated_at,
            CAST(julianday('now') - julianday(wi.updated_at) * 24 AS REAL) as hours_since_update
        FROM workflow_instances wi
        JOIN workflow_templates wt ON wi.template_id = wt.template_id
        WHERE wi.workflow_status = 'Active'
        ORDER BY wi.updated_at ASC
        """
        df = pd.read_sql_query(query, conn)

        if not df.empty:
            # Filter by threshold
            stagnant_df = df[df['hours_since_update'] >= hours_threshold].copy()
            stagnant_df = stagnant_df.sort_values('hours_since_update', ascending=False)
        else:
            stagnant_df = pd.DataFrame()

        return stagnant_df
    finally:
        conn.close()


def get_workflow_summary_metrics() -> Dict:
    """Get overall workflow summary metrics for display."""
    conn = get_db_connection()
    try:
        # Get overall metrics
        query = """
        SELECT
            COUNT(CASE WHEN workflow_status = 'Active' THEN 1 END) as active_workflows,
            COUNT(CASE WHEN workflow_status = 'Completed' THEN 1 END) as completed_workflows,
            COUNT(CASE WHEN workflow_status = 'Active' AND date(updated_at) >= date('now', '-7 days') THEN 1 END) as active_this_week,
            COUNT(CASE WHEN workflow_status = 'Completed' AND date(completed_at) >= date('now', '-7 days') THEN 1 END) as completed_this_week
        FROM workflow_instances
        WHERE created_at >= date('now', '-30 days')
        """
        cursor = conn.execute(query)
        row = cursor.fetchone()

        return {
            'active_workflows': row[0] if row else 0,
            'completed_workflows': row[1] if row else 0,
            'active_this_week': row[2] if row else 0,
            'completed_this_week': row[3] if row else 0
        }
    finally:
        conn.close()


# =============================================================================
# DATABASE QUERY FUNCTIONS - UNASSIGNED PATIENTS
# =============================================================================

@st.cache_data(ttl=300)
def get_unassigned_active_patients() -> pd.DataFrame:
    """
    FR-3.2: Get patients where coordinator_id IS NULL OR provider_id IS NULL
    and status = 'Active'.

    Returns:
        DataFrame of unassigned active patients
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT
            p.patient_id,
            p.first_name,
            p.last_name,
            p.first_name || ' ' || p.last_name as full_name,
            p.status,
            p.facility,
            pa.provider_id,
            pa.coordinator_id,
            up.provider_name,
            up.coordinator_name,
            p.last_visit_date,
            p.next_appointment_date,
            p.general_notes
        FROM patients p
        LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id AND pa.status = 'active'
        LEFT JOIN patient_panel up ON p.patient_id = up.patient_id
        WHERE p.status = 'Active'
          AND (pa.provider_id IS NULL OR pa.coordinator_id IS NULL)
        ORDER BY p.last_name, p.first_name
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


def get_andrews_view(df: pd.DataFrame) -> pd.DataFrame:
    """
    FR-3.1: Andrew's View - Custom filtered view of unassigned patients.

    Filters for:
    - Patients without coordinator assignment
    - Sorted by facility and last name
    """
    if df.empty:
        return pd.DataFrame()

    # Filter for patients without coordinator
    andrews_df = df[df['coordinator_id'].isna() | (df['coordinator_id'] == 0)].copy()

    # Sort by facility, then last name
    andrews_df = andrews_df.sort_values(['facility', 'last_name'])

    # Add priority indicator
    def assign_priority(row):
        if pd.isna(row['last_visit_date']) or row['last_visit_date'] == '':
            return f"{TextStyle.HIGH_PRIORITY}"
        else:
            try:
                last_visit = pd.to_datetime(row['last_visit_date'])
                days_since = (pd.Timestamp.now() - last_visit).days
                if days_since > 60:
                    return f"{TextStyle.HIGH_PRIORITY}"
                elif days_since > 30:
                    return f"{TextStyle.MEDIUM_PRIORITY}"
                else:
                    return f"{TextStyle.LOW_PRIORITY}"
            except:
                return f"{TextStyle.LOW_PRIORITY}"

    andrews_df['priority'] = andrews_df.apply(assign_priority, axis=1)

    return andrews_df


def get_jans_view(df: pd.DataFrame) -> pd.DataFrame:
    """
    FR-3.1: Jan's View - Custom filtered view of unassigned patients.

    Filters for:
    - Patients without provider assignment
    - Sorted by last visit date (oldest first)
    """
    if df.empty:
        return pd.DataFrame()

    # Filter for patients without provider
    jans_df = df[df['provider_id'].isna() | (df['provider_id'] == 0)].copy()

    # Convert last_visit_date to datetime for sorting
    try:
        jans_df['last_visit_date_sorted'] = pd.to_datetime(jans_df['last_visit_date'], errors='coerce')
        jans_df = jans_df.sort_values('last_visit_date_sorted', na_position='first')
        jans_df = jans_df.drop(columns=['last_visit_date_sorted'])
    except:
        jans_df = jans_df.sort_values('last_name', na_position='first')

    # Add urgency indicator based on days since last visit
    def assign_urgency(row):
        if pd.isna(row['last_visit_date']) or row['last_visit_date'] == '':
            return "NEVER VISITED"
        else:
            try:
                last_visit = pd.to_datetime(row['last_visit_date'])
                days_since = (pd.Timestamp.now() - last_visit).days
                if days_since > 90:
                    return f"URGENT ({days_since} days)"
                elif days_since > 60:
                    return f"HIGH ({days_since} days)"
                elif days_since > 30:
                    return f"MEDIUM ({days_since} days)"
                else:
                    return f"LOW ({days_since} days)"
            except:
                return "UNKNOWN"

    jans_df['urgency'] = jans_df.apply(assign_urgency, axis=1)

    return jans_df


# =============================================================================
# UI COMPONENTS - WORKFLOW ANALYTICS
# =============================================================================

def display_workflow_metrics_summary():
    """Display summary metrics for workflow analytics."""
    st.subheader(get_section_title("Workflow Summary Metrics"))

    metrics = get_workflow_summary_metrics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            get_metric_label("Active Workflows", is_current_month=True),
            metrics['active_workflows']
        )

    with col2:
        st.metric(
            get_metric_label("Completed This Week", is_current_month=False),
            metrics['completed_this_week']
        )

    with col3:
        avg_completion = get_average_completion_time()
        st.metric(
            get_metric_label("Avg Completion Time", is_current_month=False),
            f"{avg_completion:.1f} days"
        )

    with col4:
        delayed, late = get_workflow_delay_tracking()
        st.metric(
            get_metric_label("Delayed/Late", is_current_month=False),
            f"{len(delayed)}/{len(late)}",
            help="Delayed: Exceeds benchmark | Late: Exceeds deadline"
        )


def get_average_completion_time() -> float:
    """Calculate average completion time in days."""
    conn = get_db_connection()
    try:
        query = """
        SELECT AVG(julianday(completed_at) - julianday(created_at)) as avg_days
        FROM workflow_instances
        WHERE workflow_status = 'Completed'
          AND completed_at IS NOT NULL
          AND created_at >= date('now', '-90 days')
        """
        cursor = conn.execute(query)
        row = cursor.fetchone()
        return row[0] if row and row[0] else 0.0
    finally:
        conn.close()


def display_step_level_metrics():
    """FR-2.1: Display step-level performance metrics."""
    st.subheader(get_section_title("Step-Level Performance Metrics"))

    df = get_workflow_step_analytics()

    if df.empty:
        st.info("No workflow step data available.")
        return

    # Calculate throughput metrics
    df['throughput'] = df['total_instances'] / df['total_instances'].max() if df['total_instances'].max() > 0 else 0

    # Format for display
    display_df = df[[
        'template_name', 'step_order', 'task_name', 'owner',
        'expected_cycle_time', 'total_instances', 'avg_completion_days'
    ]].copy()

    display_df.columns = [
        'Template', 'Step', 'Task', 'Owner',
        'Expected Days', 'Total Instances', 'Avg Completion Days'
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


def display_delay_tracking():
    """FR-2.2: Display delayed and late workflow tracking."""
    st.subheader(get_section_title("Delay & Late Tracking"))

    delayed_df, late_df = get_workflow_delay_tracking()

    if delayed_df.empty and late_df.empty:
        st.success(f"{TextStyle.SUCCESS_INDICATOR}: No delayed or late workflows!")
        return

    # Delayed Workflows
    if not delayed_df.empty:
        st.warning(f"⚠️ {len(delayed_df)} workflows exceeding internal benchmarks")

        delayed_display = delayed_df[[
            'instance_id', 'template_name', 'patient_name',
            'current_step', 'days_in_workflow', 'expected_cycle_time_days'
        ]].copy()

        delayed_display.columns = [
            'Instance ID', 'Template', 'Patient',
            'Current Step', 'Days in Workflow', 'Expected Days'
        ]

        st.dataframe(delayed_display, use_container_width=True, hide_index=True)

    # Late Workflows
    if not late_df.empty:
        st.error(f"🚨 {len(late_df)} workflows exceeding hard deadlines")

        late_display = late_df[[
            'instance_id', 'template_name', 'patient_name',
            'coordinator_name', 'current_step', 'days_in_workflow'
        ]].copy()

        late_display.columns = [
            'Instance ID', 'Template', 'Patient',
            'Coordinator', 'Current Step', 'Days Late'
        ]

        st.dataframe(late_display, use_container_width=True, hide_index=True)


def display_stagnation_alerts(hours_threshold: int = 48):
    """FR-2.3: Display stagnation alerts for inactive workflows."""
    st.subheader(get_section_title("Stagnation Alerts"))

    col1, col2 = st.columns(2)
    with col1:
        hours_threshold = st.slider(
            "Alert Threshold (hours)",
            min_value=24,
            max_value=120,
            value=48,
            step=12,
            help="Alert if no activity within this many hours"
        )

    stagnant_df = get_stagnant_workflows(hours_threshold)

    if stagnant_df.empty:
        st.success(f"{TextStyle.SUCCESS_INDICATOR}: No stagnant workflows (threshold: {hours_threshold} hours)")
        return

    st.error(f"🚨 {len(stagnant_df)} workflows with no activity in {hours_threshold}+ hours")

    # Display most stagnant first
    stagnant_display = stagnant_df[[
        'instance_id', 'template_name', 'patient_name',
        'coordinator_name', 'current_step', 'hours_since_update', 'updated_at'
    ]].head(20).copy()

    stagnant_display.columns = [
        'Instance ID', 'Template', 'Patient',
        'Coordinator', 'Current Step', 'Hours Since Update', 'Last Updated'
    ]

    st.dataframe(stagnant_display, use_container_width=True, hide_index=True)


# =============================================================================
# UI COMPONENTS - UNASSIGNED PATIENTS
# =============================================================================

def display_unassigned_patients_management():
    """Display unassigned patient management with Andrew's and Jan's views."""
    st.subheader(get_section_title("Unassigned Patient Management"))

    # Get base data
    unassigned_df = get_unassigned_active_patients()

    if unassigned_df.empty:
        st.info(f"{TextStyle.INFO_INDICATOR}: No unassigned active patients found.")
        return

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        no_coordinator = unassigned_df[unassigned_df['coordinator_id'].isna() | (unassigned_df['coordinator_id'] == 0)]
        st.metric(get_metric_label("No Coordinator", is_current_month=True), len(no_coordinator))

    with col2:
        no_provider = unassigned_df[unassigned_df['provider_id'].isna() | (unassigned_df['provider_id'] == 0)]
        st.metric(get_metric_label("No Provider", is_current_month=True), len(no_provider))

    with col3:
        st.metric(get_metric_label("Total Unassigned", is_current_month=True), len(unassigned_df))

    # Tab system for views
    tab_andrew, tab_jan = st.tabs(["Andrew's View", "Jan's View"])

    with tab_andrew:
        display_andrews_view(no_coordinator)

    with tab_jan:
        display_jans_view(no_provider)


def display_andrews_view(df: pd.DataFrame):
    """FR-3.1: Display Andrew's View - Coordinator-focused unassigned patients."""
    st.info(f"{TextStyle.INFO_INDICATOR}: Andrew's View - Patients without coordinator assignment")

    if df.empty:
        st.info("No patients without coordinator assignment.")
        return

    # Apply Andrew's view filters
    andrews_df = get_andrews_view(df)

    # Add selection column for assignment
    andrews_df['Select'] = False

    # Display
    edited_df = st.data_editor(
        andrews_df[[
            'Select', 'patient_id', 'full_name', 'facility',
            'last_visit_date', 'priority', 'general_notes'
        ]],
        column_config={
            'Select': st.column_config.CheckboxColumn(
                "Select for Assignment",
                help="Select patients to assign to a coordinator"
            ),
            'patient_id': st.column_config.TextColumn("Patient ID"),
            'full_name': st.column_config.TextColumn("Patient Name"),
            'facility': st.column_config.TextColumn("Facility"),
            'last_visit_date': st.column_config.DateColumn("Last Visit"),
            'priority': st.column_config.TextColumn("Priority"),
            'general_notes': st.column_config.TextColumn("Notes")
        },
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Assignment action
    if st.button("Assign Selected Patients", key="andrew_assign"):
        selected = edited_df[edited_df['Select'] == True]
        if not selected.empty:
            st.success(f"Ready to assign {len(selected)} patients to coordinator")
        else:
            st.warning("No patients selected")


def display_jans_view(df: pd.DataFrame):
    """FR-3.1: Display Jan's View - Provider-focused unassigned patients."""
    st.info(f"{TextStyle.INFO_INDICATOR}: Jan's View - Patients without provider assignment")

    if df.empty:
        st.info("No patients without provider assignment.")
        return

    # Apply Jan's view filters
    jans_df = get_jans_view(df)

    # Add selection column for assignment
    jans_df['Select'] = False

    # Display
    edited_df = st.data_editor(
        jans_df[[
            'Select', 'patient_id', 'full_name', 'facility',
            'last_visit_date', 'urgency', 'general_notes'
        ]],
        column_config={
            'Select': st.column_config.CheckboxColumn(
                "Select for Assignment",
                help="Select patients to assign to a provider"
            ),
            'patient_id': st.column_config.TextColumn("Patient ID"),
            'full_name': st.column_config.TextColumn("Patient Name"),
            'facility': st.column_config.TextColumn("Facility"),
            'last_visit_date': st.column_config.DateColumn("Last Visit"),
            'urgency': st.column_config.TextColumn("Urgency"),
            'general_notes': st.column_config.TextColumn("Notes")
        },
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Assignment action
    if st.button("Assign Selected Patients", key="jan_assign"):
        selected = edited_df[edited_df['Select'] == True]
        if not selected.empty:
            st.success(f"Ready to assign {len(selected)} patients to provider")
        else:
            st.warning("No patients selected")


# =============================================================================
# MAIN TAB COMPONENT
# =============================================================================

def show_workflow_analytics_unassigned_tab(user_id: int, user_role_ids: List[int]):
    """
    Main entry point for Workflow Analytics & Unassigned Patients tab.

    This function should be called from the dashboard's tab system.

    Args:
        user_id: Current user ID
        user_role_ids: List of user's role IDs

    Usage in dashboard:
        with tab_workflow_analytics:
            show_workflow_analytics_unassigned_tab(user_id, user_role_ids)
    """
    # Apply professional styling
    from src.config.ui_style_config import apply_custom_css
    apply_custom_css()

    st.header("Workflow Analytics & Unassigned Patients")

    # Create sub-tabs
    tab_analytics, tab_unassigned = st.tabs([
        "📊 Workflow Analytics",
        "👥 Unassigned Patients"
    ])

    # Tab 1: Workflow Analytics
    with tab_analytics:
        st.markdown("### Performance Monitoring")

        # Summary metrics
        display_workflow_metrics_summary()

        st.markdown("---")

        # Detailed analytics
        col1, col2 = st.columns(2)

        with col1:
            display_step_level_metrics()

        with col2:
            display_delay_tracking()

        st.markdown("---")

        # Stagnation alerts (full width)
        display_stagnation_alerts()

    # Tab 2: Unassigned Patients
    with tab_unassigned:
        st.markdown("### Patient Assignment Management")
        display_unassigned_patients_management()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def export_workflow_analytics_report() -> pd.DataFrame:
    """Export complete workflow analytics report for download."""
    step_df = get_workflow_step_analytics()
    delayed_df, late_df = get_workflow_delay_tracking()
    stagnant_df = get_stagnant_workflows()

    return {
        'step_metrics': step_df,
        'delayed_workflows': delayed_df,
        'late_workflows': late_df,
        'stagnant_workflows': stagnant_df
    }


def export_unassigned_patients_report(view_type: str = 'both') -> pd.DataFrame:
    """
    Export unassigned patients report.

    Args:
        view_type: 'andrew', 'jan', or 'both'
    """
    unassigned_df = get_unassigned_active_patients()

    if view_type == 'andrew':
        return get_andrews_view(unassigned_df)
    elif view_type == 'jan':
        return get_jans_view(unassigned_df)
    else:
        return {
            'andrews_view': get_andrews_view(unassigned_df),
            'jans_view': get_jans_view(unassigned_df)
        }
