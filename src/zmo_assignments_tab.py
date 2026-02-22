"""
Patient Assignments Tab for ZMO Module - Enhanced Version

This file contains the Patient Assignments tab functionality with support for viewing inactive patients.
It will be imported and used by the main ZMO module.
"""

from typing import Optional
from datetime import datetime

import streamlit as st

from src import database as db
from src.utils.patient_assignments import (
    _row_to_dict,
    get_coordinator_options,
    get_provider_options,
    get_all_users_map
)


def _render_patient_assignments_tab(user_id: Optional[int] = None) -> None:
    """
    Render the Patient Assignments tab with user-friendly dropdowns.

    Provides easy coordinator/provider reassignment with name-based dropdowns
    instead of requiring users to know IDs.

    Enhanced to support viewing inactive patients for reactivation workflow.
    Uses flexible multi-select status filtering like the admin dashboard.
    """
    st.subheader("Patient Assignments")
    st.info("💡 Tip: Use dropdowns to change coordinator/provider assignments. Changes cascade to all tables automatically.")

    # Get reference data
    coordinator_options = get_coordinator_options()
    provider_options = get_provider_options()
    users_map = get_all_users_map()

    # Create display-friendly mappings
    coord_map = {c['user_id']: c['display_name'] for c in coordinator_options}
    prov_map = {p['user_id']: p['display_name'] for p in provider_options}

    # Get all patients from patient_panel
    conn = db.get_db_connection()
    try:
        # ===== Status Filter Section =====
        st.markdown("### Patient Status Filter")

        # Get all available statuses from the database
        all_statuses = conn.execute("""
            SELECT DISTINCT status
            FROM patient_panel
            WHERE status IS NOT NULL
            ORDER BY status
        """).fetchall()
        all_statuses = [s[0] for s in all_statuses]

        # Default to Active statuses and Hospice (same as admin dashboard)
        default_statuses = [s for s in all_statuses if s.startswith("Active") or s.upper() == "HOSPICE"]

        # Add columns for status filter and search
        col_status, col_search, col_coord, col_prov = st.columns([2, 2, 2, 2])

        with col_status:
            selected_statuses = st.multiselect(
                "Filter by Patient Status",
                options=all_statuses,
                default=default_statuses,
                key="assign_status_filter",
                help="Select which patient statuses to display. Default shows Active and Hospice."
            )

        with col_search:
            search_name = st.text_input(
                "Search by name or ID",
                key="assign_search_name",
                help="Filter patients by name or patient ID"
            )

        with col_coord:
            filter_coord = st.selectbox(
                "Filter by coordinator",
                options=["All"] + [c['display_name'] for c in coordinator_options],
                key="assign_filter_coord",
                help="Show only patients assigned to this coordinator"
            )

        with col_prov:
            filter_prov = st.selectbox(
                "Filter by provider",
                options=["All"] + [p['display_name'] for p in provider_options],
                key="assign_filter_prov",
                help="Show only patients assigned to this provider"
            )

        # Fetch all patients - we'll filter for statuses in Python for consistency
        patients = conn.execute("""
            SELECT
                p.patient_id,
                p.first_name,
                p.last_name,
                p.status,
                p.coordinator_id,
                p.coordinator_name,
                p.provider_id,
                p.provider_name
            FROM patient_panel p
            ORDER BY p.last_name, p.first_name
        """).fetchall()

        if not patients:
            st.info("No patients found.")
            return

        # First pass: Filter by selected statuses
        status_filtered = []
        for p in patients:
            p_dict = _row_to_dict(p)
            status = p_dict.get('status', '').strip() if p_dict.get('status') else ''

            # Apply status filter based on user selection
            if selected_statuses and status not in selected_statuses:
                continue

            status_filtered.append(p_dict)

        if not status_filtered:
            st.info(f"No patients found matching the selected statuses: {', '.join(selected_statuses)}")
            return

        # Second pass: Apply search/coordinator/provider filters
        filtered_patients = []
        for p_dict in status_filtered:
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
            if filter_coord != "All":
                if p_dict.get('coordinator_name', '') != filter_coord:
                    continue

            # Provider filter
            if filter_prov != "All":
                if p_dict.get('provider_name', '') != filter_prov:
                    continue

            filtered_patients.append(p_dict)

        if not filtered_patients:
            st.info("No patients match the current filters.")
            return

        # Show patient count with status breakdown
        st.write(f"**{len(filtered_patients)} patient(s)**")
        if len(selected_statuses) < len(all_statuses):
            st.caption(f"Showing: {', '.join(selected_statuses)}")
        else:
            st.caption("Showing: All statuses")

        # ===== Pagination =====
        patients_per_page = 50
        total_pages = max(1, (len(filtered_patients) + patients_per_page - 1) // patients_per_page)

        # Initialize pagination in session state
        if "assign_page" not in st.session_state:
            st.session_state.assign_page = 0

        # Pagination controls
        col_page1, col_page2, col_page3 = st.columns([2, 2, 2])

        with col_page1:
            if st.button("← Previous", key="assign_prev", disabled=(st.session_state.assign_page == 0)):
                st.session_state.assign_page -= 1
                st.rerun()

        with col_page2:
            st.caption(
                f"Page {st.session_state.assign_page + 1} of {total_pages} | "
                f"{len(filtered_patients)} total patients"
            )

        with col_page3:
            if st.button("Next →", key="assign_next", disabled=(st.session_state.assign_page >= total_pages - 1)):
                st.session_state.assign_page += 1
                st.rerun()

        # Calculate page boundaries
        start_idx = st.session_state.assign_page * patients_per_page
        end_idx = start_idx + patients_per_page
        paginated_patients = filtered_patients[start_idx:end_idx]

        # Determine which patients are inactive (not Active/Hospice) for special handling
        active_statuses = ["Active", "Active-Geri", "Active-PCP", "Hospice", "HOSPICE"]

        # Show assignments with edit controls
        for patient in paginated_patients:
            patient_status = patient.get('status', 'Unknown')
            is_inactive = patient_status not in active_statuses and not (
                patient_status.startswith('Active') or patient_status.upper() == 'HOSPICE'
            )
            status_emoji = "🔴" if is_inactive else "🟢"

            with st.expander(
                f"{status_emoji} {patient['last_name']}, {patient['first_name']} "
                f"(ID: {patient['patient_id']}) - Status: **{patient_status}**"
            ):
                col1, col2 = st.columns(2)

                # Coordinator assignment
                with col1:
                    st.write("**Coordinator:**")
                    current_coord_id = patient.get('coordinator_id')
                    if current_coord_id:
                        try:
                            current_coord_id = int(current_coord_id)
                        except (ValueError, TypeError):
                            current_coord_id = None

                    # Show last assignment info for inactive patients
                    if is_inactive and current_coord_id:
                        st.caption(f"Last assigned: {patient.get('coordinator_name', 'Unknown')} (ID: {current_coord_id})")
                        if current_coord_id in users_map:
                            st.caption(f"Reference: {users_map[current_coord_id]}")

                    new_coordinator = st.selectbox(
                        "Change to:",
                        options=[None] + coordinator_options,
                        format_func=lambda x: x['display_name'] if x else "Unassigned",
                        index=next((
                            i for i, c in enumerate([None] + coordinator_options)
                            if c and c['user_id'] == current_coord_id
                        ), 0),
                        key=f"coord_{patient['patient_id']}"
                    )

                # Provider assignment
                with col2:
                    st.write("**Provider:**")
                    current_prov_id = patient.get('provider_id')
                    if current_prov_id:
                        try:
                            current_prov_id = int(current_prov_id)
                        except (ValueError, TypeError):
                            current_prov_id = None

                    # Show last assignment info for inactive patients
                    if is_inactive and current_prov_id:
                        st.caption(f"Last assigned: {patient.get('provider_name', 'Unknown')} (ID: {current_prov_id})")
                        if current_prov_id in users_map:
                            st.caption(f"Reference: {users_map[current_prov_id]}")

                    new_provider = st.selectbox(
                        "Change to:",
                        options=[None] + provider_options,
                        format_func=lambda x: x['display_name'] if x else "Unassigned",
                        index=next((
                            i for i, p in enumerate([None] + provider_options)
                            if p and p['user_id'] == current_prov_id
                        ), 0),
                        key=f"prov_{patient['patient_id']}"
                    )

                # Action buttons
                col1, col2, col3 = st.columns(3)

                with col1:
                    # Check if changes were made
                    coord_changed = (
                        (new_coordinator and new_coordinator['user_id'] != current_coord_id) or
                        (not new_coordinator and current_coord_id)
                    )
                    prov_changed = (
                        (new_provider and new_provider['user_id'] != current_prov_id) or
                        (not new_provider and current_prov_id)
                    )

                    if coord_changed or prov_changed:
                        # For inactive patients, remind about reactivation
                        if is_inactive:
                            st.info("💡 Don't forget to update patient status to 'Active' in Patient Info tab when reactivating.")

                        if st.button("Save Changes", key=f"save_assign_{patient['patient_id']}", type="primary"):
                            # Update using the assignment utility function
                            from src.utils.patient_assignments import save_assignment_changes

                            save_assignment_changes(
                                patient['patient_id'],
                                patient.get('coordinator_id'),
                                patient.get('provider_id'),
                                new_coordinator['user_id'] if new_coordinator else None,
                                new_provider['user_id'] if new_provider else None
                            )

                            st.success("Assignments updated successfully!")
                            if is_inactive:
                                st.info("💡 Reminder: Update patient status to 'Active' in the Patient Info tab when reactivating.")
                            st.rerun()
                    else:
                        st.write("No changes to save")

                with col2:
                    if st.button("View Assignment History", key=f"history_{patient['patient_id']}"):
                        _view_assignment_history(patient['patient_id'])

                with col3:
                    if st.button("View Patient Details", key=f"details_{patient['patient_id']}"):
                        st.json(patient)

    except Exception as e:
        st.error(f"Error loading assignments: {e}")
    finally:
        conn.close()


def _view_assignment_history(patient_id: str) -> None:
    """Display assignment history for a patient."""
    conn = db.get_db_connection()
    try:
        # Check if history table exists
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='patient_assignment_history'"
        ).fetchone()

        if not table_exists:
            st.info("Assignment history tracking is not enabled in this database.")
            return

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
            st.info("No assignment history found for this patient.")
            return

        st.write("**Assignment History (last 10 changes):**")
        for h in history:
            with st.expander(f"{h['changed_date']} - {h.get('changed_by', 'System')}"):
                if h['old_coordinator_id'] or h['new_coordinator_id']:
                    old_c = h.get('old_coordinator_id') or "Unassigned"
                    new_c = h.get('new_coordinator_id') or "Unassigned"
                    st.write(f"Coordinator: {old_c} → {new_c}")

                if h['old_provider_id'] or h['new_provider_id']:
                    old_p = h.get('old_provider_id') or "Unassigned"
                    new_p = h.get('new_provider_id') or "Unassigned"
                    st.write(f"Provider: {old_p} → {new_p}")

                if h['change_notes']:
                    st.write(f"Notes: {h['change_notes']}")

    finally:
        conn.close()
