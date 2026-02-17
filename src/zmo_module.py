"""
ZMO (Zone Management Officer) Module - Shared Patient Data Management

This module provides a unified, editable patient data management interface
that can be used by both Admin and Onboarding dashboards.

Features:
- Editable patient data table with st.data_editor()
- Column management (show/hide, reorder, search)
- Patient search/filter
- Pagination
- Persistent column configuration
- Save changes to database (patient_panel and patients tables)
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from src import database as db

logger = logging.getLogger(__name__)

# Column to table mapping for save functionality
# Based on actual production.db schema

# patient_panel table columns (from CREATE TABLE statement)
PATIENT_PANEL_COLUMNS = {
    # Core identification
    "patient_id", "first_name", "last_name", "date_of_birth", "phone_primary",
    "current_facility_id", "facility", "status", "created_date",
    # Provider/Coordinator
    "provider_id", "coordinator_id", "provider_name", "coordinator_name",
    "last_visit_date", "last_visit_service_type",
    # Clinical
    "goals_of_care", "goc_value", "code_status", "subjective_risk_level", "service_type",
    # Healthcare utilization
    "er_count_1yr", "hospitalization_count_1yr",
    # Mental health
    "mental_health_concerns", "provider_mh_schizophrenia", "provider_mh_depression",
    "provider_mh_anxiety", "provider_mh_stress", "provider_mh_adhd",
    "provider_mh_bipolar", "provider_mh_suicidal",
    # Functional/Cognitive
    "cognitive_function", "functional_status",
    # Care coordination
    "active_specialists", "active_concerns", "chronic_conditions_provider",
    # Contacts
    "appointment_contact_name", "appointment_contact_phone",
    "medical_contact_name", "medical_contact_phone",
    # Notes
    "labs_notes", "imaging_notes", "general_notes", "next_appointment_date",
    # Display names (computed, stored as text columns)
    "care_provider_name", "care_coordinator_name",
    # Metadata
    "updated_date",
}

# patients table columns (from CREATE TABLE statement)
PATIENTS_TABLE_COLUMNS = {
    # Core identification
    "patient_id", "region_id", "first_name", "last_name", "date_of_birth", "gender",
    "phone_primary", "phone_secondary", "email",
    # Address
    "address_street", "address_city", "address_state", "address_zip",
    # Emergency contact
    "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relationship",
    # Insurance
    "insurance_primary", "insurance_policy_number", "insurance_secondary",
    # Medical records
    "medical_record_number", "enrollment_date", "discharge_date", "notes",
    # Notes
    "labs_notes", "imaging_notes", "general_notes",
    # Metadata
    "created_date", "updated_date", "created_by", "updated_by", "current_facility_id",
    # Flags
    "hypertension", "mental_health_concerns", "dementia",
    # Visit dates
    "last_annual_wellness_visit", "last_first_dob", "last_visit_date",
    # Facility/Coordinator
    "facility", "assigned_coordinator_id",
    # Utilization
    "er_count_1yr", "hospitalization_count_1yr",
    # Clinical
    "clinical_biometric", "chronic_conditions_provider", "cancer_history",
    "subjective_risk_level",
    # Mental health
    "provider_mh_schizophrenia", "provider_mh_depression", "provider_mh_anxiety",
    "provider_mh_stress", "provider_mh_adhd", "provider_mh_bipolar", "provider_mh_suicidal",
    # Specialists/Concerns
    "active_specialists", "code_status", "cognitive_function", "functional_status",
    "goals_of_care", "active_concerns",
    # Initial TV
    "initial_tv_completed_date", "initial_tv_notes",
    # Service/Eligibility
    "service_type", "tv_time", "eligibility_status", "eligibility_notes",
    "eligibility_verified", "emed_chart_created", "chart_id", "facility_confirmed",
    "chart_notes", "intake_call_completed", "intake_notes", "goc_value",
    # Contacts
    "appointment_contact_name", "appointment_contact_phone", "appointment_contact_email",
    "medical_contact_name", "medical_contact_phone", "medical_contact_email",
    # Primary care
    "primary_care_provider", "pcp_last_seen", "active_specialist", "specialist_last_seen",
    # Onboarding
    "chronic_conditions_onboarding",
    # Mental health flags
    "mh_schizophrenia", "mh_depression", "mh_anxiety", "mh_stress",
    "mh_adhd", "mh_bipolar", "mh_suicidal",
    # TV scheduling
    "tv_date", "tv_scheduled", "patient_notified", "initial_tv_provider",
    # Facility nurse
    "facility_nurse_name", "facility_nurse_phone", "facility_nurse_email",
    # Status
    "status",
    # Medical records tracking
    "medical_records_requested", "referral_documents_received",
    "insurance_cards_received", "emed_signature_received",
}

# Columns that should NOT be editable (computed, auto-generated, or special IDs)
READONLY_COLUMNS = {
    # Computed display names (from JOINs or COALESCE) - provider_name and coordinator_name are now editable
    "care_provider_name", "care_coordinator_name",
    # Provider/Coordinator assignment IDs (must use reassignment function)
    "provider_id", "coordinator_id",
    # Auto-timestamps
    "created_date", "updated_date",
    # Primary key that shouldn't be changed
    "patient_id",
    # Other IDs that shouldn't be changed
    "current_facility_id", "chart_id", "assigned_coordinator_id",
}

# Columns that require special cascade updates when edited
CASCADE_NAME_COLUMNS = {
    "provider_name", "coordinator_name"
}

# Columns that require special handling (update patient_assignments table instead)
# NOTE: These are now in READONLY_COLUMNS - assignments must use reassignment function
ASSIGNMENT_COLUMNS = {
    # "provider_id": "provider_id",  # Disabled - use reassignment function instead
    # "coordinator_id": "coordinator_id",  # Disabled - use reassignment function instead
}

# Persistent columns that must always be visible
PERSISTENT_VISIBLE_COLUMNS = {
    col for col in ["patient_id", "first_name", "last_name", "status"]
}

# Configuration file path for column settings
CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "dashboards", "zmo_column_config.json"
)


# ===== Data Fetching Functions =====

@st.cache_data(ttl=300, show_spinner="Loading patient panel data...")
def get_patient_panel_data() -> List[Dict[str, Any]]:
    """Get all patient records from patient_panel table."""
    try:
        return db.get_all_patient_panel() if hasattr(db, "get_all_patient_panel") else []
    except Exception as e:
        logger.error(f"Error loading patient_panel: {e}")
        return []


@st.cache_data(ttl=300, show_spinner="Loading patient data...")
def get_patients_data() -> List[Dict[str, Any]]:
    """Get all patient records from patients table."""
    try:
        return db.get_all_patients() if hasattr(db, "get_all_patients") else []
    except Exception as e:
        logger.error(f"Error loading patients: {e}")
        return []


def fix_dataframe_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix common Streamlit/PyArrow serialization issues in dataframes.
    """
    if df is None or df.empty:
        return df

    df_fixed = df.copy()

    # Fix current_facility_id column to prevent PyArrow conversion errors
    if "current_facility_id" in df_fixed.columns:
        df_fixed["current_facility_id"] = df_fixed["current_facility_id"].astype(str)

    # Convert provider_id and coordinator_id to proper integers
    for col in ["provider_id", "coordinator_id"]:
        if col in df_fixed.columns:
            df_fixed[col] = df_fixed[col].apply(
                lambda x: int(x) if x is not None and not pd.isna(x) else 0
            )

    return df_fixed


def merge_patient_data(panel_df: pd.DataFrame, patients_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge patient_panel and patients dataframes.

    Args:
        panel_df: DataFrame from patient_panel table
        patients_df: DataFrame from patients table

    Returns:
        Merged DataFrame with combined patient data
    """
    if panel_df.empty or patients_df.empty:
        return panel_df if not panel_df.empty else patients_df

    panel_cols = set(panel_df.columns)
    patients_extra_cols = [
        col for col in patients_df.columns
        if col not in panel_cols and col != "patient_id"
    ]

    if patients_extra_cols:
        merged = panel_df.merge(
            patients_df[["patient_id"] + patients_extra_cols],
            how="left",
            on="patient_id",
            suffixes=("", "_patients"),
        )
    else:
        merged = panel_df.copy()

    # Ensure extra columns exist
    for col in patients_extra_cols:
        if col not in merged.columns:
            merged[col] = pd.NA

    return merged


# ===== Column Configuration Functions =====

def load_column_config(all_cols: List[str]) -> Tuple[List[str], List[str]]:
    """
    Load column configuration from JSON file.

    Args:
        all_cols: List of all available column names

    Returns:
        Tuple of (visible_cols, col_order)
    """
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            visible_cols = config.get("visible_cols", all_cols)
            col_order = config.get("col_order", all_cols)
            # Remove any columns that no longer exist
            visible_cols = [c for c in visible_cols if c in all_cols]
            col_order = [c for c in col_order if c in all_cols]
            return visible_cols, col_order
    except Exception as e:
        logger.warning(f"Could not load column config: {e}")
    return all_cols, all_cols


def save_column_config(visible_cols: List[str], col_order: List[str]) -> None:
    """
    Save column configuration to JSON file.

    Args:
        visible_cols: List of visible column names
        col_order: List of column names in order
    """
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(
                {"visible_cols": visible_cols, "col_order": col_order},
                f,
                indent=2,
            )
    except Exception as e:
        logger.warning(f"Could not save column config: {e}")


def format_column_name(col: str) -> str:
    """
    Format column name for display (friendly names).

    Args:
        col: Column name to format

    Returns:
        Formatted display name
    """
    name = col.replace("_", " ").title()
    overrides = {
        "dob": "Date of Birth",
        "patient_id": "Patient ID",
        "status_name": "Status",
        "provider_id": "Provider ID",
        "coordinator_id": "Coordinator ID",
        "goc_value": "GoC Value",
        "hhc": "HHC",
        "soc": "SOC",
        "dme": "DME",
        "polst": "POLST",
        "labs_notes": "Labs Notes",
        "imaging_notes": "Imaging Notes",
        "general_notes": "General Notes",
        "next_appointment_date": "Next Appointment Date",
    }
    return overrides.get(col, name)


# ===== Save Functions =====

def _update_patient_assignment(
    conn, patient_id: str, column: str, new_value: Any, user_id: Optional[int]
) -> bool:
    """
    Update provider or coordinator assignment in patient_assignments table.

    Args:
        conn: Database connection
        patient_id: Patient ID
        column: Column name (provider_id or coordinator_id)
        new_value: New assignment value
        user_id: User ID for audit

    Returns:
        True if update was successful
    """
    try:
        # Get current assignment for audit
        current_assignment = conn.execute(
            f"SELECT {column} FROM patient_assignments WHERE patient_id = ?",
            (patient_id,)
        ).fetchone()

        current_value = current_assignment[0] if current_assignment else None

        # Handle None/0 values for new assignments
        if pd.isna(new_value) or new_value == 0 or new_value == "":
            new_value = None

        # Check if value actually changed
        if current_value == new_value:
            return False

        # Check if assignment exists
        existing = conn.execute(
            "SELECT assignment_id FROM patient_assignments WHERE patient_id = ?",
            (patient_id,)
        ).fetchone()

        audit_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if existing:
            # Update existing assignment
            conn.execute(
                f"UPDATE patient_assignments SET {column} = ?, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
                (new_value, patient_id),
            )
        else:
            # Create new assignment record
            conn.execute(
                f"INSERT INTO patient_assignments (patient_id, {column}, created_date, updated_date) VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (patient_id,) if new_value is None else (patient_id, new_value),
            )

        # Log audit trail
        role_type = "Provider" if column == "provider_id" else "Coordinator"
        conn.execute(
            """INSERT INTO audit_log (action_type, table_name, record_id, old_value, new_value, user_id, timestamp, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "REASSIGNMENT",
                "patient_assignments",
                patient_id,
                f"{role_type}_ID: {current_value}",
                f"{role_type}_ID: {new_value}",
                user_id,
                audit_timestamp,
                f"Patient {patient_id} {column} updated from {current_value} to {new_value} via ZMO",
            ),
        )

        return True

    except Exception as e:
        logger.error(f"Error updating patient assignment: {e}")
        raise


def save_edits_to_database(
    original_df: pd.DataFrame,
    edited_df: pd.DataFrame,
    user_id: Optional[int] = None
) -> Tuple[int, List[str]]:
    """
    Save edited data back to the database.

    Compares original and edited DataFrames to identify changes,
    then updates the appropriate tables:
    - patient_panel table for most columns
    - patients table for core patient data
    - patient_assignments table for provider_id/coordinator_id changes

    Args:
        original_df: DataFrame before edits
        edited_df: DataFrame after edits
        user_id: ID of user making changes (for audit)

    Returns:
        Tuple of (rows_updated, list of change summaries)
    """
    if original_df.empty or edited_df.empty:
        return 0, []

    if original_df.shape != edited_df.shape:
        logger.warning("DataFrame shape mismatch - cannot save changes")
        return 0, []

    conn = db.get_db_connection()
    rows_updated = 0
    change_summaries = []

    try:
        # Find rows with changes
        for idx in edited_df.index:
            original_row = original_df.loc[idx]
            edited_row = edited_df.loc[idx]

            patient_id = edited_row.get("patient_id")
            if not patient_id:
                continue

            panel_updates = {}
            patients_updates = {}
            assignment_updates = {}

            # Check each column for changes
            for col in edited_df.columns:
                if col in READONLY_COLUMNS:
                    continue  # Skip readonly columns

                original_val = original_row.get(col)
                edited_val = edited_row.get(col)

                # Handle NaN/None comparisons
                if pd.isna(original_val) and pd.isna(edited_val):
                    continue
                if pd.isna(original_val) != pd.isna(edited_val):
                    changed = True
                else:
                    changed = original_val != edited_val

                if changed:
                    # Handle assignment columns separately
                    if col in ASSIGNMENT_COLUMNS:
                        assignment_updates[col] = edited_val
                    # Handle cascade name columns (provider_name, coordinator_name)
                    elif col in CASCADE_NAME_COLUMNS:
                        # This will be handled separately with cascade update
                        if col not in panel_updates:
                            panel_updates[col] = edited_val
                    # Determine which table this column belongs to
                    elif col in PATIENT_PANEL_COLUMNS:
                        panel_updates[col] = edited_val
                    elif col in PATIENTS_TABLE_COLUMNS:
                        patients_updates[col] = edited_val

            # Apply assignment updates to patient_assignments table
            for col, new_val in assignment_updates.items():
                if _update_patient_assignment(conn, patient_id, col, new_val, user_id):
                    change_summaries.append(
                        f"Patient {patient_id}: Reassigned {col} to {new_val}"
                    )
                    rows_updated += 1

            # Apply updates to patient_panel table
            if panel_updates:
                # Separate cascade updates from regular panel updates
                cascade_updates = {k: v for k, v in panel_updates.items() if k in CASCADE_NAME_COLUMNS}
                regular_panel_updates = {k: v for k, v in panel_updates.items() if k not in CASCADE_NAME_COLUMNS}

                # Handle cascade name updates (provider_name, coordinator_name)
                if cascade_updates:
                    for col, new_name in cascade_updates.items():
                        # Get the user_id for this provider/coordinator
                        user_id_col = "provider_id" if col == "provider_name" else "coordinator_id"
                        user_id_val = edited_row.get(user_id_col)

                        if user_id_val and user_id_val != 0 and user_id_val != "UNASSIGNED":
                            try:
                                # Update the users table
                                conn.execute(
                                    "UPDATE users SET full_name = ? WHERE user_id = ?",
                                    (new_name, user_id_val)
                                )

                                # Cascade to all patient_panel records with this user
                                conn.execute(
                                    f"UPDATE patient_panel SET {col} = ?, updated_date = CURRENT_TIMESTAMP WHERE {user_id_col} = ?",
                                    (new_name, user_id_val)
                                )

                                # Also update care_provider_name or care_coordinator_name columns
                                if col == "provider_name":
                                    conn.execute(
                                        "UPDATE patient_panel SET care_provider_name = ?, updated_date = CURRENT_TIMESTAMP WHERE provider_id = ?",
                                        (new_name, user_id_val)
                                    )
                                elif col == "coordinator_name":
                                    conn.execute(
                                        "UPDATE patient_panel SET care_coordinator_name = ?, updated_date = CURRENT_TIMESTAMP WHERE coordinator_id = ?",
                                        (new_name, user_id_val)
                                    )

                                # Update provider_tasks_YYYY_MM tables (provider_name column)
                                if col == "provider_name":
                                    conn.execute(
                                        "UPDATE provider_tasks SET provider_name = ? WHERE provider_id = ?",
                                        (new_name, user_id_val)
                                    )

                                # Update coordinator_tasks_YYYY_MM tables (coordinator_name column if exists)
                                # Note: coordinator_tasks tables don't typically have coordinator_name, but some might

                                # Update workflow_instances table
                                if col == "coordinator_name":
                                    conn.execute(
                                        "UPDATE workflow_instances SET coordinator_name = ? WHERE coordinator_id = ?",
                                        (new_name, user_id_val)
                                    )

                                # Update provider_monthly_summary table
                                if col == "provider_name":
                                    conn.execute(
                                        "UPDATE provider_monthly_summary SET provider_name = ? WHERE provider_id = ?",
                                        (new_name, user_id_val)
                                    )

                                change_summaries.append(
                                    f"Patient {patient_id}: Updated {col} to '{new_name}' (cascaded to all records for user {user_id_val})"
                                )
                                rows_updated += 1
                            except Exception as e:
                                logger.error(f"Error cascading {col} update: {e}")
                                change_summaries.append(
                                    f"Patient {patient_id}: Failed to cascade {col} update - {e}"
                                )

                # Handle regular panel updates
                if regular_panel_updates:
                    set_clause = ", ".join([f"{col} = ?" for col in regular_panel_updates.keys()])
                    values = list(regular_panel_updates.values()) + [patient_id]

                    conn.execute(
                        f"UPDATE patient_panel SET {set_clause}, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
                        values,
                    )
                    if not cascade_updates:  # Only add summary if not already added from cascade
                        change_summaries.append(
                            f"Patient {patient_id}: Updated {', '.join(regular_panel_updates.keys())}"
                        )
                    rows_updated += 1

            # Apply updates to patients table
            if patients_updates:
                set_clause = ", ".join([f"{col} = ?" for col in patients_updates.keys()])
                values = list(patients_updates.values()) + [patient_id]

                conn.execute(
                    f"UPDATE patients SET {set_clause}, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
                    values,
                )
                if not panel_updates and not assignment_updates:  # Only add summary if not already counted
                    change_summaries.append(
                        f"Patient {patient_id}: Updated {', '.join(patients_updates.keys())}"
                    )
                    rows_updated += 1

        conn.commit()
        if user_id and change_summaries:
            logger.info(f"User {user_id} made {rows_updated} patient data updates")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving edits to database: {e}")
        raise
    finally:
        conn.close()

    return rows_updated, change_summaries


# ===== Main ZMO Tab Renderer =====

def render_zmo_tab(
    rows_per_page: int = 50,
    enable_editing: bool = True,
    show_save_button: bool = True,
    user_id: Optional[int] = None
) -> None:
    """
    Render the complete ZMO (Patient Data Management) tab interface.

    This is the main entry point for displaying the ZMO tab in dashboards.
    It provides:
    - Search and filter functionality
    - Column management (show/hide, reorder, search)
    - Editable data table with pagination
    - Save to database functionality

    Args:
        rows_per_page: Number of rows to display per page (default: 50)
        enable_editing: Whether to enable inline editing (default: True)
        show_save_button: Whether to show the save button (default: True)
        user_id: User ID for audit trail (optional)
    """
    st.subheader("ZMO: Patient Data Management")

    try:
        # Fetch data
        panel_rows = get_patient_panel_data()
        patients_rows = get_patients_data()
        panel_df = fix_dataframe_for_streamlit(pd.DataFrame(panel_rows))
        patients_df = fix_dataframe_for_streamlit(pd.DataFrame(patients_rows))

        if panel_df.empty and patients_df.empty:
            st.info("No patient data available.")
            return

        # Merge data
        merged = merge_patient_data(panel_df, patients_df)

        # Store original for comparison
        if "zmo_original_data" not in st.session_state:
            st.session_state.zmo_original_data = merged.copy()

        # ===== Search & Filter Section =====
        st.markdown("### Search & Filter")
        search_col1, search_col2 = st.columns([3, 1])

        with search_col1:
            patient_search = st.text_input(
                "Search patients by name or ID",
                placeholder="Enter patient name, ID, or MRN...",
                help="Search across patient_id, name, and other identifiers",
                key="zmo_search_input",
            )

        with search_col2:
            if st.button("Clear search", key="zmo_clear_search"):
                st.session_state["zmo_search_input"] = ""
                st.rerun()

        # Filter merged data based on patient search
        if patient_search:
            search_lower = patient_search.lower()
            search_mask = merged.astype(str).apply(
                lambda row: any(
                    search_lower in str(val).lower() for val in row
                ),
                axis=1,
            )
            merged = merged[search_mask]
            st.success(f"✓ Found {len(merged)} patients matching '{patient_search}'")
        else:
            st.caption(f"Showing all {len(merged)} patients")

        # ===== Column Management Section =====
        st.markdown("### Column Management")

        all_cols = list(merged.columns)
        visible_cols, col_order = load_column_config(all_cols)

        # Column search and filter controls
        col_controls = st.columns([3, 1.2, 1.2, 1.2])

        with col_controls[0]:
            col_search_term = st.text_input(
                "Search columns",
                placeholder="Type to filter column names...",
                help="Search by column name",
                key="zmo_col_search",
            )

        with col_controls[1]:
            st.write("")  # Vertical spacer
            show_only = st.checkbox(
                "Show Only",
                help="Show ONLY columns matching search (hide all others)",
                key="zmo_show_only",
            )

        with col_controls[2]:
            st.write("")  # Vertical spacer
            if st.button("Clear Results", key="zmo_clear_results", use_container_width=True):
                st.session_state["zmo_search_input"] = ""
                st.session_state["zmo_col_search"] = ""
                st.session_state["zmo_show_only"] = False
                st.rerun()

        with col_controls[3]:
            st.write("")  # Vertical spacer
            if st.button("Reset Columns", key="zmo_reset_cols", use_container_width=True):
                save_column_config(all_cols, all_cols)
                st.session_state["zmo_col_search"] = ""
                st.session_state["zmo_show_only"] = False
                st.session_state["zmo_search_input"] = ""
                st.rerun()

        # Filter columns based on search term
        filtered_cols = all_cols
        if col_search_term:
            search_lower = col_search_term.lower()
            filtered_cols = [col for col in all_cols if search_lower in col.lower()]

        # Persistent columns that must always be visible
        persistent_cols = [
            col for col in all_cols
            if any(name in col.lower() for name in ["patient_id", "first_name", "last_name", "status"])
        ]

        # Show/hide columns with checkboxes
        with st.expander("Show/Hide Columns", expanded=False):
            col_checks = {col: (col in visible_cols) for col in all_cols}
            checked_cols = []

            if not filtered_cols:
                st.warning("No columns match your search. Try a different search term.")
            else:
                n_cols = 3  # Number of columns in the expander
                col_chunks = [filtered_cols[i::n_cols] for i in range(n_cols)]
                cols = st.columns(n_cols)
                for idx, chunk in enumerate(col_chunks):
                    with cols[idx]:
                        for col in chunk:
                            checked = st.checkbox(
                                col,
                                value=col_checks[col],
                                key=f"zmo_col_check_{col}",
                            )
                            col_checks[col] = checked
                            if checked:
                                checked_cols.append(col)

            # If Show Only is checked and search has results, auto-select all matching columns
            if show_only and col_search_term and filtered_cols:
                checked_cols = filtered_cols
                st.caption(f"✓ Show Only enabled: Displaying {len(filtered_cols)} matching columns")
            elif show_only and not col_search_term:
                st.warning("⚠️ 'Show Only' requires a search term to work")

            # Show count of hidden columns
            if checked_cols:
                hidden_count = len(all_cols) - len(checked_cols)
                if hidden_count > 0:
                    st.caption(f"Showing {len(checked_cols)} columns (hiding {hidden_count} others)")

        # Always ensure persistent columns are included
        checked_cols_with_persistent = list(set(checked_cols + persistent_cols))

        # Preserve order from config, add any new checked columns at the end
        col_order = [
            col for col in col_order if col in checked_cols_with_persistent
        ] + [
            col for col in checked_cols_with_persistent if col not in col_order
        ]

        # Save config if changed
        if set(checked_cols_with_persistent) != set(visible_cols) or col_order != visible_cols:
            save_column_config(checked_cols_with_persistent, col_order)
            visible_cols, col_order = checked_cols_with_persistent, col_order

        # Filter and reorder DataFrame
        filtered = merged[col_order] if col_order else merged

        # ===== Data Table Section =====
        st.markdown("### Data Table")

        # Initialize pagination in session state
        if "zmo_page" not in st.session_state:
            st.session_state.zmo_page = 0

        total_rows = len(filtered)
        total_pages = (total_rows + rows_per_page - 1) // rows_per_page

        # Pagination controls
        col_page1, col_page2, col_page3 = st.columns([1, 3, 1])

        with col_page1:
            if st.button("← Previous", key="zmo_prev_page",
                        disabled=st.session_state.zmo_page == 0):
                st.session_state.zmo_page -= 1
                st.rerun()

        with col_page2:
            st.caption(
                f"Page {st.session_state.zmo_page + 1} of {max(1, total_pages)} | "
                f"Showing {len(filtered)} of {len(merged)} total patients | "
                f"{len(filtered.columns)} columns"
            )

        with col_page3:
            if st.button("Next →", key="zmo_next_page",
                        disabled=st.session_state.zmo_page >= total_pages - 1):
                st.session_state.zmo_page += 1
                st.rerun()

        # Clamp page number
        st.session_state.zmo_page = max(0, min(st.session_state.zmo_page, total_pages - 1))

        # Calculate slice for current page
        start_idx = st.session_state.zmo_page * rows_per_page
        end_idx = start_idx + rows_per_page
        page_data = filtered.iloc[start_idx:end_idx].copy()

        # Build column configuration
        col_config = {}
        for col in page_data.columns:
            dtype = page_data[col].dtype
            display_name = format_column_name(col)

            if col in READONLY_COLUMNS:
                # Skip readonly columns - they'll use default config
                # (changes won't be saved due to save function filtering)
                continue
            elif col in ["labs_notes", "imaging_notes", "general_notes", "next_appointment_date"]:
                # Notes columns - use wider text column
                col_config[col] = st.column_config.TextColumn(
                    display_name, width="large"
                )
            elif pd.api.types.is_float_dtype(dtype) or pd.api.types.is_integer_dtype(dtype):
                col_config[col] = st.column_config.NumberColumn(
                    display_name, width="medium"
                )
            elif pd.api.types.is_object_dtype(dtype):
                col_config[col] = st.column_config.TextColumn(
                    display_name, width="medium"
                )

        # Store current page data for comparison
        st.session_state[f"zmo_current_page_{st.session_state.zmo_page}"] = page_data.copy()

        # ===== Display Table =====
        if enable_editing:
            # Determine which columns to disable (readonly columns that exist in page_data)
            disabled_columns = [col for col in READONLY_COLUMNS if col in page_data.columns]
            edited_data = st.data_editor(
                page_data,
                use_container_width=True,
                height=600,
                column_config=col_config,
                key=f"zmo_editor_{st.session_state.zmo_page}",
                hide_index=True,
                disabled=disabled_columns if disabled_columns else None,
            )
        else:
            st.dataframe(
                page_data,
                use_container_width=True,
                height=600,
                column_config=col_config,
            )

        # ===== Save Button =====
        if show_save_button and enable_editing:
            st.markdown("---")

            save_col1, save_col2, save_col3 = st.columns([2, 1, 1])

            with save_col1:
                if st.button("💾 Save Changes to Database", key="zmo_save_changes",
                           type="primary", use_container_width=True):
                    with st.spinner("Saving changes..."):
                        # Get original data for comparison
                        original_data = st.session_state.zmo_original_data

                        # Filter original data to match current filtered view
                        if patient_search:
                            search_lower = patient_search.lower()
                            search_mask = original_data.astype(str).apply(
                                lambda row: any(search_lower in str(val).lower() for val in row),
                                axis=1,
                            )
                            original_filtered = original_data[search_mask]
                        else:
                            original_filtered = original_data

                        # Apply column filter
                        original_filtered = original_filtered[col_order] if col_order else original_filtered

                        # Get current page of original data
                        original_page = original_filtered.iloc[start_idx:end_idx].copy()

                        rows_updated, changes = save_edits_to_database(
                            original_page,
                            edited_data,
                            user_id
                        )

                        if rows_updated > 0:
                            st.success(f"✓ Saved {rows_updated} patient update(s) to database")

                            # Show change details in expander
                            with st.expander("View change details"):
                                for change in changes:
                                    st.text(change)

                            # Clear cache to refresh data
                            get_patient_panel_data.clear()
                            get_patients_data.clear()

                            # Update original data
                            st.session_state.zmo_original_data = merged.copy()

                            # Rerun after short delay
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.info("No changes detected to save.")

            with save_col2:
                if st.button("🔄 Refresh Data", key="zmo_refresh", use_container_width=True):
                    # Clear cache and rerun
                    get_patient_panel_data.clear()
                    get_patients_data.clear()
                    st.rerun()

            with save_col3:
                if st.button("↩️ Reset All", key="zmo_reset", use_container_width=True):
                    # Reset column config and clear cache
                    save_column_config(all_cols, all_cols)
                    get_patient_panel_data.clear()
                    get_patients_data.clear()
                    for key in list(st.session_state.keys()):
                        if key.startswith("zmo_"):
                            del st.session_state[key]
                    st.rerun()

        elif not enable_editing:
            st.caption("💡 Edit mode is disabled for this view")

    except Exception as e:
        st.error(f"Error in ZMO tab: {e}")
        logger.error(f"ZMO tab error: {e}", exc_info=True)
