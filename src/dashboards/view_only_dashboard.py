"""
View-Only Dashboards for external service roles.

Each role sees a filtered, read-only patient list with specific columns.
Roles:
  44 - Live Answering Service
  45 - Special Teams
  46 - Clinical Pharmacy
  47 - SMS ChatBot
"""

import pandas as pd
import streamlit as st

from src import database

# ---------------------------------------------------------------------------
# Role definitions
# ---------------------------------------------------------------------------
ROLE_LIVE_ANSWERING = 44
ROLE_SPECIAL_TEAMS = 45
ROLE_CLINICAL_PHARMACY = 46
ROLE_SMS_CHATBOT = 47

# ---------------------------------------------------------------------------
# Per-role configuration
# ---------------------------------------------------------------------------
VIEW_CONFIGS = {
    ROLE_LIVE_ANSWERING: {
        "title": "Live Answering Service",
        "subtitle": "Active & Hospice patients — contact information",
        "columns": [
            ("patient_id", "Patient"),
            ("coordinator_name", "Assigned Coordinator"),
            ("provider_name", "Assigned Provider"),
        ],
    },
    ROLE_SPECIAL_TEAMS: {
        "title": "Special Teams Dashboard",
        "subtitle": "Active & Hospice patients — BH / Cognitive / RPM teams",
        "columns": [
            ("patient_id", "Patient"),
            ("bh_team", "BH Team"),
            ("cog_team", "Cog Team"),
            ("rpm_team", "RPM Team"),
        ],
    },
    ROLE_CLINICAL_PHARMACY: {
        "title": "Clinical Pharmacy",
        "subtitle": "Active & Hospice patients — medication list",
        "columns": [
            ("patient_id", "Patient"),
            ("medlist_date", "MedList Date"),
        ],
    },
    ROLE_SMS_CHATBOT: {
        "title": "SMS ChatBot",
        "subtitle": "Active & Hospice patients — contact points",
        "columns": [
            ("patient_id", "Patient"),
            ("medical_contact_name", "Med POC"),
            ("appointment_contact_name", "Appt POC"),
        ],
    },
}

ALL_VIEW_ONLY_ROLES = set(VIEW_CONFIGS.keys())


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------
def _get_active_hospice_patients() -> pd.DataFrame:
    """Return patient_panel rows where status is Active or Hospice."""
    conn = database.get_db_connection()
    try:
        query = """
            SELECT *
            FROM patient_panel
            WHERE LOWER(status) IN ('active', 'hospice')
            ORDER BY patient_id
        """
        df = pd.read_sql_query(query, conn)
        df = df.where(pd.notnull(df), None)
        return df
    except Exception as e:
        st.error(f"Error loading patient data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def show(user_id: int, user_role_ids: list):
    """Render the appropriate view-only dashboard based on the user's role."""

    # Determine which view-only role this user has
    matching_roles = ALL_VIEW_ONLY_ROLES.intersection(set(user_role_ids))
    if not matching_roles:
        st.error("You do not have permission to access this dashboard.")
        return

    role_id = matching_roles.pop()
    config = VIEW_CONFIGS[role_id]

    # Header
    st.markdown(f"# {config['title']}")
    st.caption(config["subtitle"])
    st.divider()

    # Load data
    df = _get_active_hospice_patients()
    if df.empty:
        st.info("No active or hospice patients found.")
        return

    # Select only the configured columns
    db_cols = [col for col, _ in config["columns"]]
    display_names = [name for _, name in config["columns"]]

    # Ensure columns exist
    for col in db_cols:
        if col not in df.columns:
            df[col] = None

    display_df = df[db_cols].copy()
    display_df.columns = display_names

    # Summary metrics
    col1, col2 = st.columns(2)
    active_count = len(df[df["status"].str.lower() == "active"]) if "status" in df.columns else 0
    hospice_count = len(df[df["status"].str.lower() == "hospice"]) if "status" in df.columns else 0
    col1.metric("Active Patients", active_count)
    col2.metric("Hospice Patients", hospice_count)

    st.divider()

    # Search
    search = st.text_input(
        "Search patients",
        placeholder="Type patient name or ID...",
        key=f"view_only_search_{role_id}",
    )

    if search:
        search_lower = search.lower()
        mask = display_df.apply(
            lambda row: any(
                search_lower in str(val).lower()
                for val in row
                if val is not None
            ),
            axis=1,
        )
        display_df = display_df[mask]

    st.caption(f"Showing {len(display_df)} patients")

    # Display read-only table
    column_config = {}
    for col_name in display_names:
        column_config[col_name] = st.column_config.TextColumn(col_name, disabled=True)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        height=min(len(display_df) * 35 + 38, 800),
    )
