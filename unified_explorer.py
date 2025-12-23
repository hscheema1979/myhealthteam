"""
Unified Data Explorer with PyGWalker
A simple tool to explore unified task data with pre-built views for common metrics.
"""

import sqlite3
import warnings
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

warnings.filterwarnings("ignore")

# Check for PyGWalker
try:
    import pygwalker as pyg
    HAS_PYGWALKER = True
except ImportError:
    HAS_PYGWALKER = False

# Page configuration
st.set_page_config(
    page_title="Unified Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_resource
def get_db_connection():
    """Get SQLite database connection"""
    return sqlite3.connect("production.db", check_same_thread=False)

def create_unified_views():
    """Create the unified views if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if unified_tasks view exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='unified_tasks'")
    if not cursor.fetchone():
        st.info("Creating unified views...")

        # Create unified_tasks view
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS unified_tasks AS
        -- Coordinator tasks
        SELECT
            'coordinator' AS task_type,
            coordinator_task_id AS task_id,
            coordinator_id AS staff_id,
            coordinator_name AS staff_name,
            patient_id,
            NULL AS patient_name,
            task_date,
            duration_minutes AS minutes,
            task_type AS activity_type,
            notes,
            NULL AS task_description,
            NULL AS billing_code,
            NULL AS billing_code_description,
            source_system,
            imported_at,
            NULL AS status,
            NULL AS is_deleted,
            NULL AS provider_paid,
            NULL AS provider_paid_date
        FROM coordinator_tasks

        UNION ALL

        -- Provider tasks
        SELECT
            'provider' AS task_type,
            provider_task_id AS task_id,
            provider_id AS staff_id,
            provider_name AS staff_name,
            patient_id,
            patient_name,
            task_date,
            minutes_of_service AS minutes,
            NULL AS activity_type,
            notes,
            task_description,
            billing_code,
            billing_code_description,
            source_system,
            imported_at,
            status,
            is_deleted,
            provider_paid,
            provider_paid_date
        FROM provider_tasks
        """)

        # Create unified_tasks_with_facilities view
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS unified_tasks_with_facilities AS
        SELECT
            ut.*,
            p.current_facility_id,
            f.facility_name
        FROM unified_tasks ut
        LEFT JOIN patients p ON ut.patient_id = p.patient_id
        LEFT JOIN facilities f ON p.current_facility_id = f.facility_id
        """)

        conn.commit()
        st.success("Created unified views!")

    conn.close()

def get_available_views():
    """Get all available views for exploration"""
    return {
        "unified_tasks": "All tasks combined (coordinator + provider)",
        "unified_tasks_with_facilities": "All tasks with facility information",
        "coordinator_tasks": "Coordinator tasks only (original view)",
        "provider_tasks": "Provider tasks only (original view)",
        "patients": "Patient information",
        "facilities": "Facility information",
        "patient_panel": "Patient panel data",
    }

def get_prebuilt_queries():
    """Get pre-built queries for common metrics"""
    return {
        "Select a pre-built query...": "",
        "Minutes per coordinator per month, per facility": """
SELECT
    COALESCE(facility_name, 'Unknown Facility') as facility_name,
    staff_name as coordinator_name,
    strftime('%Y-%m', task_date) as month,
    SUM(minutes) as total_minutes,
    COUNT(*) as task_count,
    COUNT(DISTINCT patient_id) as unique_patients,
    ROUND(AVG(minutes), 2) as avg_minutes_per_task
FROM unified_tasks_with_facilities
WHERE task_type = 'coordinator'
  AND task_date >= date('now', '-12 months')
GROUP BY facility_name, staff_name, month
ORDER BY facility_name, coordinator_name, month DESC
        """,
        "Tasks per provider per month, per facility": """
SELECT
    COALESCE(facility_name, 'Unknown Facility') as facility_name,
    staff_name as provider_name,
    strftime('%Y-%m', task_date) as month,
    COUNT(*) as task_count,
    SUM(minutes) as total_minutes,
    COUNT(DISTINCT patient_id) as unique_patients,
    ROUND(AVG(minutes), 2) as avg_minutes_per_task,
    GROUP_CONCAT(DISTINCT billing_code) as billing_codes_used
FROM unified_tasks_with_facilities
WHERE task_type = 'provider'
  AND task_date >= date('now', '-12 months')
GROUP BY facility_name, staff_name, month
ORDER BY facility_name, provider_name, month DESC
        """,
        "General minutes per month per facility": """
SELECT
    COALESCE(facility_name, 'Unknown Facility') as facility_name,
    strftime('%Y-%m', task_date) as month,
    SUM(CASE WHEN task_type = 'coordinator' THEN minutes ELSE 0 END) as coordinator_minutes,
    SUM(CASE WHEN task_type = 'provider' THEN minutes ELSE 0 END) as provider_minutes,
    SUM(minutes) as total_minutes,
    COUNT(CASE WHEN task_type = 'coordinator' THEN 1 END) as coordinator_tasks,
    COUNT(CASE WHEN task_type = 'provider' THEN 1 END) as provider_tasks,
    COUNT(*) as total_tasks,
    COUNT(DISTINCT patient_id) as unique_patients
FROM unified_tasks_with_facilities
WHERE task_date >= date('now', '-12 months')
GROUP BY facility_name, month
ORDER BY facility_name, month DESC
        """,
        "Tasks per month per facility": """
SELECT
    COALESCE(facility_name
