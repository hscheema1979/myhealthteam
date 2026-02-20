"""
Patient Assignment Utilities for ZMO Module

Provides user-friendly dropdowns for reassigning patients to coordinators and providers.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional

from src import database


def _row_to_dict(row) -> dict:
    """Safely convert SQLite Row object to dict."""
    if hasattr(row, 'keys'):
        return {k: row[k] for k in row.keys()}
    return dict(row)


def get_coordinator_options() -> List[Dict]:
    """
    Get list of coordinators for dropdown.

    Returns:
        List of dicts with user_id, username, full_name
    """
    conn = database.get_db_connection()
    try:
        # Get Care Coordinators (role 36)
        coordinators = conn.execute("""
            SELECT DISTINCT
                u.user_id,
                u.username,
                u.full_name,
                CASE
                    WHEN u.full_name IS NOT NULL AND u.full_name != '' THEN u.full_name
                    ELSE u.username
                END as display_name
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            WHERE ur.role_id = 36
            ORDER BY u.full_name, u.username
        """).fetchall()

        # Convert Row objects to dicts
        return [{k: c[k] for k in c.keys()} for c in coordinators]
    finally:
        conn.close()


def get_provider_options() -> List[Dict]:
    """
    Get list of providers for dropdown.

    Returns:
        List of dicts with user_id, username, full_name
    """
    conn = database.get_db_connection()
    try:
        # Get Care Providers (role 33)
        providers = conn.execute("""
            SELECT DISTINCT
                u.user_id,
                u.username,
                u.full_name,
                CASE
                    WHEN u.full_name IS NOT NULL AND u.full_name != '' THEN u.full_name
                    ELSE u.username
                END as display_name
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            WHERE ur.role_id = 33
            ORDER BY u.full_name, u.username
        """).fetchall()

        # Convert Row objects to dicts
        return [{k: p[k] for k in p.keys()} for p in providers]
    finally:
        conn.close()


def render_assignment_tab():
    """
    Render the Patient Assignments tab in ZMO module.

    Provides user-friendly interface for reassigning patients to coordinators and providers.
    """
    st.subheader("Patient Assignments")

    # Get current assignments
    conn = database.get_db_connection()
    try:
        # Get patients with their current assignments
        patients = conn.execute("""
            SELECT
                p.patient_id,
                p.first_name,
                p.last_name,
                p.coordinator_id,
                p.coordinator_name,
                p.provider_id,
                p.provider_name
            FROM patient_panel p
            WHERE p.status = 'Active'
            ORDER BY p.last_name, p.first_name
        """).fetchall()

        if not patients:
            st.info("No active patients found.")
            return

        # Get coordinator and provider options
        coordinator_options = get_coordinator_options()
        provider_options = get_provider_options()

        # Create mapping dictionaries
        coordinator_map = {c['user_id']: c['display_name'] for c in coordinator_options}
        provider_map = {p['user_id']: p['display_name'] for p in provider_options}

        # Show assignment editor
        st.write(f"**{len(patients)} active patients**")
        st.info("💡 Tip: Use the dropdowns to change coordinator or provider assignments. Changes are saved immediately.")

        # Add filters
        col1, col2, col3 = st.columns(3)

        with col1:
            search_name = st.text_input("Search by name", key="assign_search_name")

        with col2:
            filter_coordinator = st.selectbox(
                "Filter by coordinator",
                options=["All"] + [c['display_name'] for c in coordinator_options],
                key="assign_filter_coord"
            )

        with col3:
            filter_provider = st.selectbox(
                "Filter by provider",
                options=["All"] + [p['display_name'] for p in provider_options],
                key="assign_filter_prov"
            )

        # Filter patients
        filtered_patients = []
        for p in patients:
            p_dict = dict(p)

            # Name filter
            if search_name:
                search_lower = search_name.lower()
                name_match = (
                    search_lower in p_dict.get('first_name', '').lower() or
                    search_lower in p_dict.get('last_name', '').lower() or
                    search_lower in p_dict.get('patient_id', '').lower()
                )
                if not name_match:
                    continue

            # Coordinator filter
            if filter_coordinator != "All":
                if p_dict.get('coordinator_name', '') != filter_coordinator:
                    continue

            # Provider filter
            if filter_provider != "All":
                if p_dict.get('provider_name', '') != filter_provider:
                    continue

            filtered_patients.append(p_dict)

        if not filtered_patients:
            st.info("No patients match the current filters.")
            return

        st.write(f"**Showing {len(filtered_patients)} patient(s)**")

        # Edit assignments
        for patient in filtered_patients:
            with st.expander(
                f"{patient['last_name']}, {patient['first_name']} "
                f"(ID: {patient['patient_id']})"
            ):
                col1, col2 = st.columns(2)

                # Current assignments
                with col1:
                    st.write("**Current Coordinator:**")
                    st.write(f"{patient.get('coordinator_name', 'Unassigned')} (ID: {patient.get('coordinator_id', 'N/A')})")

                    # Coordinator dropdown
                    current_coord_id = patient.get('coordinator_id')
                    if current_coord_id:
                        try:
                            current_coord_id = int(current_coord_id)
                        except (ValueError, TypeError):
                            current_coord_id = None

                    new_coordinator = st.selectbox(
                        "Change Coordinator",
                        options=[{"user_id": None, "display_name": "Unassigned"}] + coordinator_options,
                        format_func=lambda x: x['display_name'] if x else "Unassigned",
                        index=next((
                            i for i, c in enumerate([{"user_id": None, "display_name": "Unassigned"}] + coordinator_options)
                            if c and c['user_id'] == current_coord_id
                        ), 0),
                        key=f"coord_{patient['patient_id']}"
                    )

                with col2:
                    st.write("**Current Provider:**")
                    st.write(f"{patient.get('provider_name', 'Unassigned')} (ID: {patient.get('provider_id', 'N/A')})")

                    # Provider dropdown
                    current_prov_id = patient.get('provider_id')
                    if current_prov_id:
                        try:
                            current_prov_id = int(current_prov_id)
                        except (ValueError, TypeError):
                            current_prov_id = None

                    new_provider = st.selectbox(
                        "Change Provider",
                        options=[{"user_id": None, "display_name": "Unassigned"}] + provider_options,
                        format_func=lambda x: x['display_name'] if x else "Unassigned",
                        index=next((
                            i for i, p in enumerate([{"user_id": None, "display_name": "Unassigned"}] + provider_options)
                            if p and p['user_id'] == current_prov_id
                        ), 0),
                        key=f"prov_{patient['patient_id']}"
                    )

                # Save button
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("Save Changes", key=f"save_assign_{patient['patient_id']}"):
                        save_assignment_changes(
                            patient['patient_id'],
                            patient.get('coordinator_id'),
                            patient.get('provider_id'),
                            new_coordinator['user_id'] if new_coordinator else None,
                            new_provider['user_id'] if new_provider else None
                        )
                        st.success("Assignments updated!")
                        st.rerun()

                with col2:
                    if st.button("View History", key=f"history_{patient['patient_id']}"):
                        view_assignment_history(patient['patient_id'])

    finally:
        conn.close()


def save_assignment_changes(patient_id: str, old_coordinator_id, old_provider_id,
                           new_coordinator_id, new_provider_id):
    """
    Save coordinator and provider assignment changes.

    Simplified logic: Updates patient_assignments (source of truth) and patient_panel (display).
    Does NOT update patients table (wrong table for assignment data).

    Args:
        patient_id: Patient ID
        old_coordinator_id: Previous coordinator ID
        old_provider_id: Previous provider ID
        new_coordinator_id: New coordinator ID (None to unassign)
        new_provider_id: New provider ID (None to unassign)
    """
    conn = database.get_db_connection()
    try:
        changes = []

        # Handle coordinator change
        if old_coordinator_id != new_coordinator_id:
            # Deactivate old coordinator assignments
            if old_coordinator_id:
                conn.execute(
                    "UPDATE patient_assignments SET status = 'inactive' WHERE patient_id = ? AND coordinator_id = ? AND status = 'active'",
                    (patient_id, old_coordinator_id)
                )

            # Create new coordinator assignment if provided
            if new_coordinator_id:
                # Get coordinator name for display
                coord = conn.execute(
                    "SELECT full_name, username FROM users WHERE user_id = ?",
                    (new_coordinator_id,)
                ).fetchone()
                coord_name = coord['full_name'] or coord['username'] if coord else None

                # Create new assignment
                conn.execute(
                    "INSERT INTO patient_assignments (patient_id, coordinator_id, status) VALUES (?, ?, 'active')",
                    (patient_id, new_coordinator_id)
                )

                # Update patient_panel for display
                conn.execute(
                    "UPDATE patient_panel SET coordinator_id = ?, coordinator_name = ?, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
                    (new_coordinator_id, coord_name, patient_id)
                )

            changes.append(f"Coordinator: {old_coordinator_id} → {new_coordinator_id}")

        # Handle provider change
        if old_provider_id != new_provider_id:
            # Deactivate old provider assignments
            if old_provider_id:
                conn.execute(
                    "UPDATE patient_assignments SET status = 'inactive' WHERE patient_id = ? AND provider_id = ? AND status = 'active'",
                    (patient_id, old_provider_id)
                )

            # Create new provider assignment if provided
            if new_provider_id:
                # Get provider name for display
                prov = conn.execute(
                    "SELECT full_name, username FROM users WHERE user_id = ?",
                    (new_provider_id,)
                ).fetchone()
                prov_name = prov['full_name'] or prov['username'] if prov else None

                # Create new assignment
                conn.execute(
                    "INSERT INTO patient_assignments (patient_id, provider_id, status) VALUES (?, ?, 'active')",
                    (patient_id, new_provider_id)
                )

                # Update patient_panel for display
                conn.execute(
                    "UPDATE patient_panel SET provider_id = ?, provider_name = ?, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
                    (new_provider_id, prov_name, patient_id)
                )

            changes.append(f"Provider: {old_provider_id} → {new_provider_id}")

        # Log to patient_assignment_history table
        if changes:
            conn.execute(
                """INSERT INTO patient_assignment_history
                   (patient_id, old_coordinator_id, new_coordinator_id, old_provider_id,
                    new_provider_id, changed_by_user_id, changed_date, change_notes)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)""",
                (patient_id,
                 str(old_coordinator_id) if old_coordinator_id else None,
                 str(new_coordinator_id) if new_coordinator_id else None,
                 str(old_provider_id) if old_provider_id else None,
                 str(new_provider_id) if new_provider_id else None,
                 st.session_state.get("user_id"),
                 '; '.join(changes))
            )

        conn.commit()

        if changes:
            st.success(f"Changes saved: {'; '.join(changes)}")
        else:
            st.info("No changes to save.")

    except Exception as e:
        conn.rollback()
        st.error(f"Error saving changes: {str(e)}")
    finally:
        conn.close()


def view_assignment_history(patient_id: str):
    """View assignment history for a patient."""
    conn = database.get_db_connection()
    try:
        history = conn.execute("""
            SELECT
                pah.changed_date,
                pah.old_coordinator_id,
                pah.new_coordinator_id,
                pah.old_provider_id,
                pah.new_provider_id,
                pah.change_notes,
                u.username as changed_by
            FROM patient_assignment_history pah
            LEFT JOIN users u ON pah.changed_by_user_id = u.user_id
            WHERE pah.patient_id = ?
            ORDER BY pah.changed_date DESC
            LIMIT 10
        """, (patient_id,)).fetchall()

        if not history:
            st.info("No assignment history found.")
            return

        st.write("**Assignment History:**")
        for h in history:
            with st.expander(f"{h['changed_date']} - Changed by {h.get('changed_by', 'System')}"):
                if h['old_coordinator_id'] or h['new_coordinator_id']:
                    st.write(f"Coordinator: {h['old_coordinator_id']} → {h['new_coordinator_id']}")
                if h['old_provider_id'] or h['new_provider_id']:
                    st.write(f"Provider: {h['old_provider_id']} → {h['new_provider_id']}")
                if h['change_notes']:
                    st.write(f"Notes: {h['change_notes']}")

    finally:
        conn.close()


def get_all_users_map() -> Dict[str, str]:
    """
    Get mapping of all users (coordinators + providers) for reference.

    Returns:
        Dict mapping user_id to display_name
    """
    conn = database.get_db_connection()
    try:
        users = conn.execute("""
            SELECT DISTINCT
                u.user_id,
                CASE
                    WHEN u.full_name IS NOT NULL AND u.full_name != '' THEN u.full_name
                    ELSE u.username
                END as display_name,
                ur.role_id
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            WHERE ur.role_id IN (33, 36)
            ORDER BY u.full_name, u.username
        """).fetchall()

        # Convert Row objects to dicts
        return {str(u['user_id']): f"{u['display_name']} (ID: {u['user_id']})" for u in users}
    finally:
        conn.close()
