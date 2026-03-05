import streamlit as st

st.write("Admin Dashboard Loaded")
import logging
import time

# try:
#     # reuse the unfiltered patient summary helper from provider dashboard for consistency
#     from src.dashboards.care_provider_dashboard_enhanced import show_unfiltered_patient_summary
#   except Exception:
#     show_unfiltered_patient_summary = None
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Setup logger
logger = logging.getLogger(__name__)

from src import database as db
from src.dashboards.dashboard_display_config import ST_DF_AUTOSIZE_COLUMNS
from src.utils.write_ahead_logger import log_write_ahead, mark_log_completed, mark_log_failed


# ===== PERFORMANCE OPTIMIZATION: Add caching for expensive database queries =====
@st.cache_data(ttl=300, show_spinner="Loading patient data...")
def _cached_get_all_patient_panel():
    """Cached version of get_all_patient_panel - refreshes every 5 minutes"""
    try:
        return (
            db.get_all_patient_panel() if hasattr(db, "get_all_patient_panel") else []
        )
    except Exception as e:
        logger.error(f"Error loading patient_panel: {e}")
        return []


@st.cache_data(ttl=300, show_spinner="Loading patient data...")
def _cached_get_all_patients():
    """Cached version of get_all_patients - refreshes every 5 minutes"""
    try:
        return db.get_all_patients() if hasattr(db, "get_all_patients") else []
    except Exception as e:
        logger.error(f"Error loading patients: {e}")
        return []


@st.cache_data(ttl=300, show_spinner="Processing patient data...")
def _cached_merge_patient_data(panel_df, patients_df):
    """Cached version of patient data merge"""
    if panel_df.empty or patients_df.empty:
        return panel_df if not panel_df.empty else patients_df

    panel_cols = set(panel_df.columns)
    patients_extra_cols = [
        col
        for col in patients_df.columns
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

    for col in patients_extra_cols:
        if col not in merged.columns:
            merged[col] = pd.NA

    return merged


# Role constants for better maintainability
ROLE_ADMIN = 34
ROLE_CARE_PROVIDER = 33
ROLE_CARE_COORDINATOR = 36
ROLE_COORDINATOR_MANAGER = 40
ROLE_ONBOARDING_TEAM = 37
ROLE_RESULTS_REVIEWER = 43


def _fix_dataframe_for_streamlit(df):
    """
    Fix common Streamlit/PyArrow serialization issues in dataframes.
    Specifically handles current_facility_id column conversion to prevent PyArrow errors.
    """
    if df is None or df.empty:
        return df

    df_fixed = df.copy()

    # Fix current_facility_id column to prevent PyArrow conversion errors
    if "current_facility_id" in df_fixed.columns:
        df_fixed["current_facility_id"] = df_fixed["current_facility_id"].astype(str)

    return df_fixed


def _apply_patient_info_edits_admin(edited_df, original_df):
    """Apply patient info edits to database"""
    import pandas as pd

    from src import database as _db

    if edited_df is None or original_df is None:
        return
    if "patient_id" not in edited_df.columns:
        return
    original_by_id = {
        str(r["patient_id"]): r
        for _, r in original_df.iterrows()
        if pd.notna(r.get("patient_id"))
    }
    conn = _db.get_db_connection()
    try:
        for _, row in edited_df.iterrows():
            pid = str(row.get("patient_id"))
            if not pid or pid not in original_by_id:
                continue
            orig = original_by_id[pid]
            changed = {}
            for col in edited_df.columns:
                if col == "patient_id":
                    continue
                if str(row.get(col)) != str(orig.get(col)):
                    changed[col] = row.get(col)
            if not changed:
                continue

            # Separate changes by target table
            patient_changes = {}
            panel_changes = {}
            patient_cols = [
                c[1] for c in conn.execute("PRAGMA table_info('patients')").fetchall()
            ]
            panel_cols = [
                c[1] for c in conn.execute("PRAGMA table_info('patient_panel')").fetchall()
            ]

            for k, v in changed.items():
                if k in patient_cols:
                    patient_changes[k] = v
                if k in panel_cols:
                    panel_changes[k] = v

            # Update patients table with write-ahead log
            if patient_changes:
                update_data = {"patient_id": pid, **patient_changes}
                log_id = log_write_ahead(
                    user_id=0,  # Admin edits - no user context available here
                    target_table="patients",
                    operation="UPDATE",
                    data_json=update_data,
                    source_system="ADMIN_DASHBOARD"
                )

                set_parts = []
                params = []
                for k, v in patient_changes.items():
                    set_parts.append(f"{k} = ?")
                    params.append(v)
                params.append(pid)

                try:
                    conn.execute(
                        f"UPDATE patients SET {', '.join(set_parts)}, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
                        tuple(params),
                    )
                    mark_log_completed(log_id, target_record_id=pid)
                except Exception as e:
                    mark_log_failed(log_id, str(e))
                    raise

            # Update patient_panel table with write-ahead log
            if panel_changes:
                update_data = {"patient_id": pid, **panel_changes}
                log_id = log_write_ahead(
                    user_id=0,  # Admin edits - no user context available here
                    target_table="patient_panel",
                    operation="UPDATE",
                    data_json=update_data,
                    source_system="ADMIN_DASHBOARD"
                )

                set_parts = []
                params = []
                for k, v in panel_changes.items():
                    set_parts.append(f"{k} = ?")
                    params.append(v)
                params.append(pid)

                try:
                    conn.execute(
                        f"UPDATE patient_panel SET {', '.join(set_parts)}, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
                        tuple(params),
                    )
                    mark_log_completed(log_id, target_record_id=pid)
                except Exception as e:
                    mark_log_failed(log_id, str(e))
                    raise
        conn.commit()
    finally:
        conn.close()


def _execute_patient_reassignment(
    patient_id, role_type, new_assignee_id, admin_user_id
):
    """Execute patient reassignment with audit logging"""
    import datetime

    import pandas as pd

    from src import database as _db

    if not patient_id or not role_type or not new_assignee_id:
        raise ValueError("Missing required parameters for patient reassignment")

    conn = _db.get_db_connection()
    try:
        # Log the original assignment for audit
        audit_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Determine assignment table and column based on role type
        if role_type == "Provider":
            assignment_table = "patient_assignments"
            assignment_column = "provider_id"
            role_id = 33
        elif role_type == "Coordinator":
            assignment_table = "patient_assignments"
            assignment_column = "coordinator_id"
            role_id = 36
        else:
            raise ValueError(f"Invalid role type: {role_type}")

        # Get current assignment info for audit
        current_assignment = conn.execute(
            f"SELECT {assignment_column} FROM {assignment_table} WHERE patient_id = ?",
            (patient_id,),
        ).fetchone()

        current_assignee = current_assignment[0] if current_assignment else None

        # Check if assignment exists, if not create new record
        existing_assignment = conn.execute(
            f"SELECT assignment_id FROM {assignment_table} WHERE patient_id = ?", (patient_id,)
        ).fetchone()

        if existing_assignment:
            # Update existing assignment
            conn.execute(
                f"UPDATE {assignment_table} SET {assignment_column} = ?, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
                (new_assignee_id, patient_id),
            )
        else:
            # Create new assignment record
            conn.execute(
                f"INSERT INTO {assignment_table} (patient_id, {assignment_column}, created_date, updated_date) VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (patient_id, new_assignee_id),
            )

        # Log audit trail
        conn.execute(
            """INSERT INTO audit_log (action_type, table_name, record_id, old_value, new_value, user_id, timestamp, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "REASSIGNMENT",
                assignment_table,
                patient_id,
                f"{role_type}_ID: {current_assignee}",
                f"{role_type}_ID: {new_assignee_id}",
                admin_user_id,
                audit_timestamp,
                f"Patient {patient_id} reassigned from {role_type} {current_assignee} to {role_type} {new_assignee_id}",
            ),
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to reassign patient: {str(e)}")
    finally:
        conn.close()


def show():
    global pd  # Explicitly declare pd as global to prevent UnboundLocalError
    from src.config.ui_style_config import TextStyle

    st.title("Admin Dashboard")
    user_id = st.session_state.get("user_id", None)

    current_user = st.session_state.get("authenticated_user", {})
    active_role_id = None

    # DEBUG: Add session state diagnostic
    if st.sidebar.checkbox("🐛 Debug Session", key="admin_debug_session"):
        st.subheader("🔍 Session State Debug Info")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**user_id:**", user_id)
            st.write("**authenticated_user:**", current_user)
            if current_user:
                st.write("  - user_id:", current_user.get("user_id", "MISSING"))
                st.write("  - full_name:", current_user.get("full_name", "MISSING"))
                st.write("  - email:", current_user.get("email", "MISSING"))
        with col2:
            user_role_ids_debug = st.session_state.get("user_role_ids", "MISSING")
            st.write("**user_role_ids:**", user_role_ids_debug)
            impersonating = st.session_state.get("impersonating_user", None)
            st.write("**impersonating:**", impersonating is not None)
            if impersonating:
                st.write(
                    "  - impersonating_id:", impersonating.get("user_id", "MISSING")
                )
                st.write(
                    "  - impersonating_name:", impersonating.get("full_name", "MISSING")
                )

        # Add role refresh button
        if st.button("🔄 Refresh Roles", key="refresh_roles"):
            # Force refresh roles from database
            try:
                user_roles = db.get_user_roles_by_user_id(user_id)
                role_ids = [r["role_id"] for r in user_roles]
                st.session_state["user_role_ids"] = role_ids
                st.success(f"Roles refreshed: {role_ids}")
                st.rerun()
            except Exception as e:
                st.error(f"Error refreshing roles: {e}")

    def get_user_role_ids(user_id):
        """Get user role IDs from database and cache in session state"""
        # DEBUG: Always refresh roles to avoid stale cache issues
        if True:  # Force refresh - bypass cache
            try:
                user_roles = db.get_user_roles_by_user_id(user_id)
                role_ids = [r["role_id"] for r in user_roles]
                st.session_state["user_role_ids"] = role_ids
                st.session_state["user_id"] = user_id
                if st.session_state.get("admin_debug_session", False):
                    st.write(f"**DEBUG:** Refreshed roles from database: {role_ids}")
            except Exception as e:
                st.session_state["user_role_ids"] = []
                st.session_state["user_id"] = user_id
                st.sidebar.error(f"Error loading user roles: {e}")
        else:  # Original caching logic (disabled for now)
            if (
                "user_role_ids" not in st.session_state
                or "user_id" not in st.session_state
                or st.session_state.get("user_id") != user_id
            ):
                try:
                    user_roles = db.get_user_roles_by_user_id(user_id)
                    role_ids = [r["role_id"] for r in user_roles]
                    st.session_state["user_role_ids"] = role_ids
                    st.session_state["user_id"] = user_id
                except Exception as e:
                    st.session_state["user_role_ids"] = []
                    st.session_state["user_id"] = user_id
                    st.sidebar.error(f"Error loading user roles: {e}")
        return st.session_state.get("user_role_ids", [])

    # Get user role IDs consistently
    user_role_ids = get_user_role_ids(user_id) if user_id else []

    # Role switcher removed - main app.py role switcher handles all role switching

    # New tab order: User Role Management, Staff Onboarding, Coordinator Tasks, Provider Tasks, Patient Info, HHC View Template, Workflow Reassignment, ZMO, Billing Report
    # Note: User Management tab removed (functionality preserved in commented code below)

    # Dynamic tab configuration based on active role
    tab_names = []

    # Workflow Reassignment should be available to both Admin and Coordinator Manager
    # regardless of which role is currently active - use the same user_role_ids from above
    has_admin_access = ROLE_ADMIN in user_role_ids
    has_coordinator_manager_access = ROLE_COORDINATOR_MANAGER in user_role_ids

    if has_admin_access or has_coordinator_manager_access:
        # Both admin and coordinator managers get the full admin dashboard
        tab_names = [
            "User Role Management",
            "Staff Onboarding",
            "Coordinator Tasks",
            "Provider Tasks",
            "Patient Info",
            "HHC View Template",
            "Workflow Reassignment",
            "ZMO",
        ]

        # Add Billing Report for specific admin users (Justin and Harpreet)
        current_user_id = st.session_state.get("user_id")
        if current_user_id in [
            12,
            18,
        ]:  # Harpreet=12, Justin=18 (keep as user IDs, not roles)
            tab_names.append("Billing Report")

    elif active_role_id == 33:  # Care Provider
        tab_names = [
            "My Patients",
            "Onboarding Queue",
            "Phone Reviews",
            "Task Review",
            "Patient Info",
        ]
    elif active_role_id == 36:  # Care Coordinator
        tab_names = ["Patient Info", "Coordinator Tasks"]
    else:
        # Default to admin view for users with multiple roles or unclear role status
        # Check user roles from database as backup
        current_user = st.session_state.get("authenticated_user", {})
        has_admin_roles = False

        if current_user and "user_id" in current_user:
            try:
                current_user_id = current_user["user_id"]
                user_roles = db.get_user_roles_by_user_id(current_user_id)
                role_ids = [r["role_id"] for r in user_roles]
                has_admin_roles = (
                    ROLE_ADMIN in role_ids or ROLE_COORDINATOR_MANAGER in role_ids
                )  # Admin or Coordinator Manager
            except Exception:
                has_admin_roles = False

        if has_admin_roles:
            # Both admin and coordinator managers get the full admin dashboard
            tab_names = [
                "User Role Management",
                "Staff Onboarding",
                "Coordinator Tasks",
                "Provider Tasks",
                "Patient Info",
                "HHC View Template",
                "Workflow Reassignment",
                "ZMO",
                "Workflow Analytics & Unassigned",
            ]

            # Add Billing Report for Justin (18) and Harpreet (12) at the end
            current_user_id = st.session_state.get("user_id")
            if current_user_id in [12, 18]:  # Harpreet=12, Justin=18
                tab_names.append("Billing Report")
        else:
            # Default minimal view for other users
            tab_names = ["Patient Info"]

    # Create tabs based on active role
    tabs = st.tabs(tab_names)

    # Assign to variables while handling different tab counts
    tab_role = tabs[0] if len(tab_names) > 0 else st.empty()
    tab_onboard = tabs[1] if len(tab_names) > 1 else st.empty()
    tab_coord_tasks = tabs[2] if len(tab_names) > 2 else st.empty()
    tab_prov_tasks = tabs[3] if len(tab_names) > 3 else st.empty()
    tab3 = tabs[4] if len(tab_names) > 4 else st.empty()
    tab_hhc = tabs[5] if len(tab_names) > 5 else st.empty()
    tab_workflow = tabs[6] if len(tab_names) > 6 else st.empty()
    tab_test = tabs[7] if len(tab_names) > 7 else st.empty()
    tab_analytics_unassigned = tabs[8] if len(tab_names) > 8 else st.empty()

    # Billing is at index 9 (only for Justin/Harpreet)
    tab_billing = tabs[9] if len(tab_names) > 9 else st.empty()

    # --- TAB: User Role Management ---
    with tab_role:
        # Create sub-tabs for Users and Facilities
        sub_tab_users, sub_tab_facilities = st.tabs(["User Roles", "Facility Management"])

        # ===== SUB-TAB: User Roles =====
        with sub_tab_users:
            st.subheader(TextStyle.INFO_INDICATOR + " User Roles")
            st.markdown("### Assign and Remove User Roles")
        users = db.get_all_users() or []
        roles = db.get_all_roles() or []
        # Filter out roles that are no longer used as separate roles
        roles = [
            role
            for role in roles
            if role["role_name"] not in ["Provider", "INITIAL_TV_PROVIDER"]
        ]
        role_names = [role["role_name"] for role in roles]
        role_id_map = {role["role_name"]: role["role_id"] for role in roles}
        data = []
        for user in users:
            user_id = user["user_id"]
            user_roles = db.get_user_roles_by_user_id(user_id)
            user_role_names = [r["role_name"] for r in user_roles]
            user_role_ids = [r["role_id"] for r in user_roles]
            row = {
                "user_id": user_id,
                "full_name": user["full_name"],
                "email": user["email"] or "",
                "status": user["status"] or "Active",
                "can_edit_patient_info": ROLE_ADMIN
                in user_role_ids,  # Admin role can edit patient info
            }
            for role_name in role_names:
                row[f"role_{role_name}"] = role_name in user_role_names
            data.append(row)
        df = pd.DataFrame(data)
        column_config = {
            "user_id": None,
            "full_name": st.column_config.TextColumn("Full Name"),
            "email": st.column_config.TextColumn("Email"),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["Active", "Inactive", "Pending", "Suspended"],
                required=True,
            ),
            "can_edit_patient_info": st.column_config.CheckboxColumn(
                "🔧 Edit Patient Info",
                help="Allow user to edit patient information - Grant admin role automatically",
            ),
        }
        for role_name in role_names:
            column_config[f"role_{role_name}"] = st.column_config.CheckboxColumn(
                role_name
            )
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            hide_index=True,
            key="user_role_editor",
            use_container_width=True,
        )
        if st.session_state.get("user_role_editor"):
            changes = st.session_state["user_role_editor"]
            if "edited_rows" in changes and changes["edited_rows"]:
                for row_index, changed_cells in changes["edited_rows"].items():
                    user_id = df.iloc[row_index]["user_id"]
                    full_name = df.iloc[row_index]["full_name"]
                    for col_name, new_value in changed_cells.items():
                        try:
                            if col_name.startswith("role_"):
                                role_name = col_name.replace("role_", "")
                                role_id = role_id_map[role_name]
                                if new_value:
                                    db.add_user_role(user_id, role_id)
                                    st.info(
                                        f"{TextStyle.INFO_INDICATOR} Added {role_name} role to {full_name}"
                                    )
                                else:
                                    db.remove_user_role(user_id, role_id)
                                    st.info(
                                        f"{TextStyle.INFO_INDICATOR} Removed {role_name} role from {full_name}"
                                    )
                            elif col_name == "status":
                                conn = db.get_db_connection()
                                conn.execute(
                                    """
                                    UPDATE users
                                    SET status = ?
                                    WHERE user_id = ?
                                """,
                                    (new_value, user_id),
                                )
                                conn.commit()
                                conn.close()
                                st.info(
                                    f"{TextStyle.INFO_INDICATOR} Updated status to {new_value} for {full_name}"
                                )
                            elif col_name == "can_edit_patient_info":
                                if new_value:
                                    # Grant admin access
                                    db.add_user_role(user_id, ROLE_ADMIN)
                                    st.info(
                                        f"{TextStyle.INFO_INDICATOR} Granted edit patient info access to {full_name}"
                                    )
                                else:
                                    # Remove admin access
                                    existing_roles = db.get_user_roles_by_user_id(
                                        user_id
                                    )
                                    if len(existing_roles) > 1 or (
                                        len(existing_roles) == 1
                                        and existing_roles[0]["role_name"] != "ADMIN"
                                    ):
                                        db.remove_user_role(user_id, ROLE_ADMIN)
                                        st.info(
                                            f"{TextStyle.INFO_INDICATOR} Removed edit patient info access from {full_name}"
                                        )
                            elif col_name in ["full_name", "email"]:
                                conn = db.get_db_connection()
                                if col_name == "full_name":
                                    conn.execute(
                                        """
                                        UPDATE users
                                        SET full_name = ?
                                        WHERE user_id = ?
                                    """,
                                        (new_value, user_id),
                                    )
                                elif col_name == "email":
                                    conn.execute(
                                        """
                                        UPDATE users
                                        SET email = ?
                                        WHERE user_id = ?
                                    """,
                                        (new_value, user_id),
                                    )
                                conn.commit()
                                conn.close()
                                st.info(
                                    f"{TextStyle.INFO_INDICATOR} Updated {col_name.replace('_', ' ').title()} for {full_name}"
                                )
                        except Exception as e:
                            st.error(
                                f"{TextStyle.INFO_INDICATOR} Error updating {col_name} for {full_name}: {e}"
                            )
                time.sleep(1)
                st.rerun()

        st.divider()
        st.markdown("#### Quick Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh User Data"):
                st.rerun()
        with col2:
            if st.button("📊 Export User List"):
                st.info("Export functionality would be implemented here")
        with col3:
            if st.button("📧 Send Status Updates"):
                st.info("Email notification functionality would be implemented here")

        st.divider()
        st.markdown("#### 🔧 User Management Actions")
        st.warning(
            "**⚠️ User Management**: Changes below are permanent and cannot be undone!"
        )

        # Create a table with action buttons for each user
        for user_row in users:
            user_id = user_row[0]  # user_id
            username = user_row[1]  # username
            full_name = user_row[2]  # full_name
            email = user_row[3]  # email
            current_status = user_row[4]  # status
            hire_date = user_row[5]  # hire_date

            # Create a card-like display for each user
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

                with col1:
                    st.markdown(f"**{full_name}**")
                    st.caption(f"Username: `{username}` | Status: {current_status}")

                with col2:
                    if current_status == "inactive":
                        if st.button(f"✅ Activate", key=f"activate_{user_id}"):
                            if db.reactivate_user(user_id):
                                st.success(f"Reactivated {full_name}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Failed to reactivate {full_name}")
                    else:
                        if st.button(f"⏸️ Deactivate", key=f"deactivate_{user_id}"):
                            if db.deactivate_user(user_id):
                                st.info(f"Deactivated {full_name}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Failed to deactivate {full_name}")

                with col3:
                    st.markdown("")  # Spacer

                # with col4:
                # # Delete button with confirmation
                # if st.button(f"🗑️ Delete", key=f"delete_{user_id}", type="primary"):
                #     # Create confirmation dialog
                #     st.error(f"⚠️ **PERMANENT DELETE CONFIRMATION**")
                #     st.markdown(f"**This will permanently delete user:** `{full_name}`")
                #     st.markdown("**This action CANNOT be undone!**")

                #     col_yes, col_no = st.columns(2)
                #     with col_yes:
                #         if st.button(f"✅ YES - Delete {full_name}", key=f"confirm_delete_{user_id}"):
                #             if db.delete_user(user_id):
                #                 st.success(f"**DELETED**: {full_name} has been permanently removed")
                #                 time.sleep(2)
                #                 st.rerun()
                #             else:
                #                 st.error(f"Failed to delete {full_name}")
                #     with col_no:
                #         st.info("Operation cancelled")
                #         st.rerun()  # Reset the state

        # ===== SUB-TAB: Facility Management =====
        with sub_tab_facilities:
            st.subheader(TextStyle.INFO_INDICATOR + " Facility Management")
            st.markdown("### Manage Facilities and User Assignments")

            # Facility Management Section
            st.markdown("#### Facilities List")

            # Get facilities with full details
            conn = db.get_db_connection()
            facilities = conn.execute("SELECT * FROM facilities ORDER BY facility_name").fetchall()
            conn.close()

            if facilities:
                facility_data = []
                for f in facilities:
                    facility_data.append({
                        "facility_id": f[0],
                        "facility_name": f[1],
                        "address": f[2] or "",
                        "phone": f[3] or "",
                        "email": f[4] or "",
                    })
                facilities_df = pd.DataFrame(facility_data)

                # Display facilities
                st.dataframe(
                    facilities_df,
                    column_config={
                        "facility_id": None,
                        "facility_name": st.column_config.TextColumn("Facility Name", width="medium"),
                        "address": st.column_config.TextColumn("Address", width="large"),
                        "phone": st.column_config.TextColumn("Phone", width="small"),
                        "email": st.column_config.TextColumn("Email", width="medium"),
                    },
                    hide_index=True,
                    use_container_width=True,
                )

                # Add new facility
                st.divider()
                st.markdown("##### Add New Facility")
                with st.form("add_facility_form"):
                    new_facility_name = st.text_input("Facility Name*")
                    new_facility_address = st.text_input("Address")
                    new_facility_phone = st.text_input("Phone")
                    new_facility_email = st.text_input("Email")

                    submitted = st.form_submit_button("Add Facility", use_container_width=True)
                    if submitted and new_facility_name:
                        try:
                            conn = db.get_db_connection()
                            conn.execute(
                                """
                                INSERT INTO facilities (facility_name, address, phone, email, created_date)
                                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                                """,
                                (new_facility_name, new_facility_address, new_facility_phone, new_facility_email)
                            )
                            conn.commit()
                            conn.close()
                            st.success(f"Added facility: {new_facility_name}")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding facility: {e}")

            else:
                st.info("No facilities found in the system.")

            # User-Facility Assignments
            st.divider()
            st.markdown("#### User-Facility Assignments")

            # Get all assignments with user and facility details
            conn = db.get_db_connection()
            assignments = conn.execute("""
                SELECT
                    ufa.assignment_id,
                    u.user_id,
                    u.full_name,
                    f.facility_id,
                    f.facility_name,
                    ufa.assignment_type,
                    ufa.assigned_date
                FROM user_facility_assignments ufa
                JOIN users u ON ufa.user_id = u.user_id
                JOIN facilities f ON ufa.facility_id = f.facility_id
                ORDER BY f.facility_name, u.full_name
            """).fetchall()
            conn.close()

            if assignments:
                assignment_data = []
                for a in assignments:
                    assignment_data.append({
                        "assignment_id": a[0],
                        "user_id": a[1],
                        "full_name": a[2],
                        "facility_id": a[3],
                        "facility_name": a[4],
                        "assignment_type": a[5],
                        "assigned_date": a[6],
                    })
                assignments_df = pd.DataFrame(assignment_data)

                st.dataframe(
                    assignments_df,
                    column_config={
                        "assignment_id": None,
                        "user_id": None,
                        "facility_id": None,
                        "full_name": st.column_config.TextColumn("User", width="medium"),
                        "facility_name": st.column_config.TextColumn("Facility", width="medium"),
                        "assignment_type": st.column_config.TextColumn("Type", width="small"),
                        "assigned_date": st.column_config.TextColumn("Assigned", width="small"),
                    },
                    hide_index=True,
                    use_container_width=True,
                )

            else:
                st.info("No user-facility assignments found.")

            # Get users and facilities for dropdowns (used in both forms below)
            users_list = db.get_all_users() or []
            conn = db.get_db_connection()
            facilities_list = conn.execute("SELECT facility_id, facility_name FROM facilities ORDER BY facility_name").fetchall()
            conn.close()

            if users_list and facilities_list:
                user_options = {f"{u['full_name']} (ID: {u['user_id']})": u['user_id'] for u in users_list}
                facility_options = {f[1]: f[0] for f in facilities_list}

                # Remove assignment section
                st.divider()
                st.markdown("##### Remove Facility Assignment")
                with st.form("remove_facility_assignment_form"):
                    selected_user = st.selectbox("Select User*", options=list(user_options.keys()), key="remove_user")
                    selected_facility = st.selectbox("Select Facility*", options=list(facility_options.keys()), key="remove_facility")

                    remove_submitted = st.form_submit_button("Remove Assignment", use_container_width=True)
                    if remove_submitted:
                        try:
                            user_id_to_remove = user_options[selected_user]
                            facility_id_to_remove = facility_options[selected_facility]

                            conn = db.get_db_connection()
                            conn.execute(
                                "DELETE FROM user_facility_assignments WHERE user_id = ? AND facility_id = ?",
                                (user_id_to_remove, facility_id_to_remove)
                            )
                            conn.commit()
                            conn.close()
                            st.success(f"Removed {selected_user} from {selected_facility}")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error removing assignment: {e}")

                # Add new assignment
                st.divider()
                st.markdown("##### Add Facility Assignment")
                with st.form("add_facility_assignment_form"):
                    selected_user = st.selectbox("Select User*", options=list(user_options.keys()), key="add_user")
                    selected_facility = st.selectbox("Select Facility*", options=list(facility_options.keys()), key="add_facility")
                    assignment_type = st.selectbox("Assignment Type", options=["primary", "secondary"], index=0)

                    add_submitted = st.form_submit_button("Add Assignment", use_container_width=True)
                    if add_submitted:
                        try:
                            user_id_to_add = user_options[selected_user]
                            facility_id_to_add = facility_options[selected_facility]

                            conn = db.get_db_connection()
                            conn.execute(
                                """
                                INSERT INTO user_facility_assignments (user_id, facility_id, assignment_type, assigned_date)
                                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                                """,
                                (user_id_to_add, facility_id_to_add, assignment_type)
                            )
                            conn.commit()
                            conn.close()
                            st.success(f"Assigned {selected_user} to {selected_facility} as {assignment_type}")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding assignment: {e}")

    # --- TAB: Staff Onboarding (Hidden User Management Table) ---
    # HIDING: User management table display issues - functionality moved to User Role Management tab
    # with tab_onboard:
    #     st.subheader(TextStyle.INFO_INDICATOR + " Staff Onboarding Management")
    #     try:
    #         users = db.get_all_users()
    #         users_df = pd.DataFrame(users)
    #
    #         # Configure columns for the user management table
    #         # Note: Column order matches get_all_users() query
    #         column_config = {
    #             "user_id": st.column_config.TextColumn("User ID"),
    #             "username": st.column_config.TextColumn("Username/Login"),
    #             "full_name": st.column_config.TextColumn("Full Name"),
    #             "email": st.column_config.TextColumn("Email Address"),
    #             "status": st.column_config.SelectboxColumn("Status", options=["active", "inactive", "pending"], required=True),
    #             "hire_date": st.column_config.DateColumn("Hire Date")
    #         }
    #
    #         edited_df = st.data_editor(
    #             users_df,
    #             column_config=column_config,
    #             use_container_width=True,
    #             num_rows="dynamic",
    #             key="user_management_editor"
    #         )
    #
    #         st.markdown("---")
    #
    #
    #     except Exception as e:
    #         st.error(f"Error loading user data: {e}")

    # --- TAB: Staff Onboarding ---
    with tab_onboard:
        st.subheader(TextStyle.INFO_INDICATOR + " Staff Onboarding Management")
        st.info(
            "**Admin Only**: Staff onboarding and user registration is restricted to administrators"
        )
        st.markdown("### New User Registration")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                "Create new users and assign roles (Providers, Coordinators, etc.)"
            )
            with st.form("new_user_form"):
                st.markdown("##### User Information")
                first_name = st.text_input("First Name*", key="new_first_name")
                last_name = st.text_input("Last Name*", key="new_last_name")
                email = st.text_input("Email*", key="new_email")
                username = st.text_input("Username*", key="new_username")
                password = st.text_input(
                    "Password*", type="password", key="new_password"
                )
                try:
                    roles = db.get_user_roles()
                    role_options = [
                        role["role_name"]
                        for role in roles
                        if role["role_name"] not in ["LC", "CPM", "CM"]
                    ]
                    selected_role = st.selectbox(
                        "Primary Role*", role_options, key="new_role"
                    )
                    role_descriptions = {
                        "CP": "Care Provider - Delivers direct patient care",
                        "CC": "Care Coordinator - Coordinates patient care plans",
                        "ADMIN": "Administrator - System administration and management",
                        "OT": "Onboarding Team - Patient intake and onboarding",
                        "DATA ENTRY": "Data Entry - Data entry and documentation",
                    }
                    if selected_role and selected_role in role_descriptions:
                        st.info(role_descriptions[selected_role])
                except Exception as e:
                    st.error(f"Error loading roles: {e}")
                    selected_role = None
                submitted = st.form_submit_button(
                    "Create New User", use_container_width=True
                )
                if submitted:
                    if all(
                        [
                            first_name,
                            last_name,
                            email,
                            username,
                            password,
                            selected_role,
                        ]
                    ):
                        try:
                            db.add_user(
                                username,
                                password,
                                first_name,
                                last_name,
                                email,
                                selected_role,
                            )
                            st.success(
                                f"Successfully created user: {first_name} {last_name} ({selected_role})"
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating user: {e}")
                    else:
                        st.error("Please fill in all required fields")

    # --- TAB: Coordinator Tasks ---
    with tab_coord_tasks:
        # Import the unified coordinator tasks module
        from src.dashboards.coordinator_tasks_module import show_coordinator_tasks_tab
        
        # Show coordinator tasks tab with admin view (show all coordinators)
        show_coordinator_tasks_tab(
            user_id=user_id,
            user_role_ids=user_role_ids,
            show_all_coordinators=True,  # Admin view - show all coordinators
            filter_by_coordinator=False
        )

    # --- TAB: Provider Tasks ---
    with tab_prov_tasks:
        col_header, col_filter = st.columns([3, 2])
        with col_header:
            st.subheader("Provider Tasks Management")
        with col_filter:
            # Get available patient statuses for filter
            conn = db.get_db_connection()
            patient_statuses = conn.execute("""
                SELECT DISTINCT status FROM patients WHERE status IS NOT NULL ORDER BY status
            """).fetchall()
            conn.close()
            all_statuses = [s[0] for s in patient_statuses]

            # Default to active statuses and hospice
            default_patient_statuses = [
                s for s in all_statuses
                if s in ["Active", "Active-Geri", "Active-PCP", "HOSPICE"]
            ]

            selected_patient_statuses = st.multiselect(
                "Patient Status Filter",
                options=all_statuses,
                default=default_patient_statuses,
                key="prov_tasks_patient_status_filter",
                help="Filter tasks by patient status from patients table"
            )

        # View Mode Selection
        view_mode = st.radio(
            "View Mode",
            ["Monthly Detail View", "Weekly Summary View"],
            horizontal=True,
            key="provider_tasks_view_mode",
        )

        # Helper to get available provider task tables and import views
        def get_provider_tables(conn):
            tables = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE (type='table' AND name LIKE 'provider_tasks_20%')
                   OR (type='view' AND name LIKE 'provider_monthly_202%_import')
                ORDER BY name DESC
            """).fetchall()
            return [t[0] for t in tables]

        conn = db.get_db_connection()
        available_tables = get_provider_tables(conn)
        conn.close()

        if view_mode == "Monthly Detail View":
            # --- Monthly View Logic ---
            import calendar

            col_sel1, col_sel2 = st.columns([1, 3])

            with col_sel1:
                # Parse years and months from tables and views
                available_months = []
                for table_name in available_tables:
                    try:
                        # provider_tasks_YYYY_MM or provider_monthly_YYYY_MM_import
                        parts = table_name.split("_")
                        if len(parts) >= 4:
                            if "monthly" in table_name:
                                # provider_monthly_YYYY_MM_import
                                year = int(parts[2])
                                month = int(parts[3])
                                data_type = "IMPORT"
                            else:
                                # provider_tasks_YYYY_MM
                                year = int(parts[2])
                                month = int(parts[3])
                                data_type = "LIVE"
                            available_months.append((year, month, data_type))
                    except:
                        continue

                available_months.sort(key=lambda x: (x[0], x[1]), reverse=True)

                # Create options
                month_options = []
                month_values = []
                for year, month, data_type in available_months:
                    month_name = calendar.month_name[month]
                    if data_type == "IMPORT":
                        month_options.append(f"{month_name} {year} (CSV Import)")
                    else:
                        month_options.append(f"{month_name} {year} (Live)")
                    month_values.append((year, month, data_type))

                # Default selection
                current_date = pd.Timestamp.now()
                default_idx = 0
                for i, (y, m, dt) in enumerate(month_values):
                    if y == current_date.year and m == current_date.month and dt == "LIVE":
                        default_idx = i
                        break

                selected_month_text = st.selectbox(
                    "Select Month",
                    options=month_options if month_options else ["No Data"],
                    index=default_idx if month_options else 0,
                    key="prov_task_month_select",
                )

            if not month_options:
                st.warning("No provider task data found.")
            else:
                sel_year, sel_month, data_type = month_values[
                    month_options.index(selected_month_text)
                ]

                # For IMPORT data, show monthly summary view
                if data_type == "IMPORT":
                    view_name = f"provider_monthly_{sel_year}_{sel_month:02d}_import"

                    with col_sel2:
                        st.markdown(f"### {selected_month_text}")
                        st.caption("Monthly summary from CSV import data")

                    # Load and display monthly summary
                    conn = db.get_db_connection()
                    query = f"""
                    SELECT
                        provider_name,
                        billing_code,
                        task_type,
                        SUM(total_tasks) as total_tasks,
                        SUM(total_minutes) as total_minutes,
                        ROUND(SUM(total_minutes) / 60.0, 2) as total_hours,
                        SUM(unique_patients) as unique_patients
                    FROM {view_name}
                    GROUP BY provider_id, provider_name, billing_code, task_type
                    ORDER BY SUM(total_minutes) DESC
                    """
                    df = pd.read_sql_query(query, conn)
                    conn.close()

                    if not df.empty:
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No data available for this period")

                # For LIVE data, show detailed task view
                else:
                    table_name = f"provider_tasks_{sel_year}_{sel_month:02d}"

                    with col_sel2:
                        st.markdown(f"### {selected_month_text}")

                    # Load data for selected month
                    try:
                        conn = db.get_db_connection()
                        # Join with patients table to get patient status for filtering
                        df = pd.read_sql_query(f"""
                            SELECT pt.*, p.status as patient_status
                            FROM {table_name} pt
                            LEFT JOIN patients p ON pt.patient_id = p.patient_id
                        """, conn)
                        conn.close()

                    except Exception as e:
                        st.error(f"Error loading data: {e}")
                        df = pd.DataFrame()

                    if not df.empty:
                        # Apply patient status filter
                        if selected_patient_statuses:
                            df = df[df["patient_status"].isin(selected_patient_statuses)]

                    if not df.empty:
                        # --- Metrics ---
                        total_visits = len(df)
                        unique_patients = (
                            df["patient_id"].nunique()
                            if "patient_id" in df.columns
                            else 0
                        )

                        # Visit Type Breakdown
                        home_visits = 0
                        tele_visits = 0
                        phone_visits = 0

                        # Check columns for type
                        type_col = (
                            "task_description"
                            if "task_description" in df.columns
                            else ("visit_type" if "visit_type" in df.columns else None)
                        )

                        if type_col:
                            home_visits = len(
                                df[
                                    df[type_col]
                                    .fillna("")
                                    .astype(str)
                                    .str.contains("Home|home", case=False)
                                ]
                            )
                            tele_visits = len(
                                df[
                                    df[type_col]
                                    .fillna("")
                                    .astype(str)
                                    .str.contains(
                                        "Telemed|Telehealth|video", case=False
                                    )
                                ]
                            )
                            phone_visits = len(
                                df[
                                    df[type_col]
                                    .fillna("")
                                    .astype(str)
                                    .str.contains("Phone|phone", case=False)
                                ]
                            )

                        # Display Metrics
                        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
                        m_col1.metric("Total Visits", total_visits)
                        m_col2.metric("Unique Patients", unique_patients)
                        m_col3.metric("Home Visits", home_visits)
                        m_col4.metric("Telehealth", tele_visits)
                        m_col5.metric("Phone", phone_visits)

                        st.divider()

                        # --- Tasks Table ---
                        st.subheader(f"Tasks List - {selected_month_text}")

                        # Filters
                        f_col1, f_col2 = st.columns(2)
                        with f_col1:
                            if "provider_name" in df.columns:
                                provs = sorted(df["provider_name"].dropna().unique())
                                sel_prov = st.multiselect(
                                    "Filter by Provider",
                                    provs,
                                    default=[],
                                    key="prov_task_prov_filter",
                                )
                            else:
                                sel_prov = []
                        with f_col2:
                            if "status" in df.columns:
                                statuses = sorted(df["status"].dropna().unique())
                                default_statuses = [
                                    s
                                    for s in statuses
                                    if s in ["Active", "Active-Geri", "Active-PCP", "Hospice", "HOSPICE"]
                                ]
                                sel_status = st.multiselect(
                                    "Filter by Status",
                                    statuses,
                                    default=default_statuses,
                                    key="prov_task_status_filter",
                                )
                            else:
                                sel_status = []

                        filtered_df = df.copy()
                        if sel_prov:
                            filtered_df = filtered_df[
                                filtered_df["provider_name"].isin(sel_prov)
                            ]
                        if sel_status:
                            filtered_df = filtered_df[
                                filtered_df["status"].isin(sel_status)
                            ]

                        # Column configuration
                        disp_cols = [
                            c
                            for c in [
                                "task_date",
                                "provider_name",
                                "patient_name",
                                "patient_id",
                                "task_description",
                                "minutes_of_service",
                                "billing_code",
                                "status",
                                "notes",
                            ]
                            if c in filtered_df.columns
                        ]

                        st.data_editor(
                            filtered_df[disp_cols],
                            use_container_width=True,
                            num_rows="dynamic",
                            height=600,
                            key="prov_task_monthly_editor",
                        )
                    else:
                        st.info(f"No records found in {table_name}")

        else:
            # --- Weekly View Logic ---
            st.markdown("### Yearly Weekly Summary")

            # Extract available years
            years = set()
            for t in available_tables:
                try:
                    y = int(t.split("_")[2])
                    years.add(y)
                except:
                    continue

            years = sorted(list(years), reverse=True)

            if not years:
                st.warning("No data available.")
            else:
                col_year, col_week = st.columns([1, 2])
                with col_year:
                    sel_year = st.selectbox(
                        "Select Year", years, key="prov_task_year_select"
                    )

                # Load ALL data for that year
                tables_for_year = [t for t in available_tables if f"_{sel_year}_" in t]

                if not tables_for_year:
                    st.info(f"No tables found for {sel_year}")
                else:
                    all_data = []
                    conn = db.get_db_connection()
                    progress_text = "Loading data..."
                    my_bar = st.progress(0, text=progress_text)

                    for i, t_name in enumerate(tables_for_year):
                        try:
                            # Join with patients table to get patient status for filtering
                            d = pd.read_sql_query(f"""
                                SELECT pt.*, p.status as patient_status
                                FROM {t_name} pt
                                LEFT JOIN patients p ON pt.patient_id = p.patient_id
                            """, conn)
                            all_data.append(d)
                        except:
                            pass
                        my_bar.progress(
                            (i + 1) / len(tables_for_year), text=f"Loading {t_name}..."
                        )

                    conn.close()
                    my_bar.empty()

                    if all_data:
                        full_df = pd.concat(all_data, ignore_index=True)

                        # Apply patient status filter
                        if selected_patient_statuses and "patient_status" in full_df.columns:
                            full_df = full_df[full_df["patient_status"].isin(selected_patient_statuses)]

                        # Ensure date column
                        date_col = (
                            "task_date"
                            if "task_date" in full_df.columns
                            else ("date" if "date" in full_df.columns else None)
                        )

                        if date_col:
                            full_df[date_col] = pd.to_datetime(
                                full_df[date_col], errors="coerce"
                            )
                            full_df = full_df.dropna(subset=[date_col])

                            # Add Week Number
                            full_df["Week_Number"] = (
                                full_df[date_col].dt.isocalendar().week
                            )

                            # Prepare weekly stats for dropdown and summary
                            weekly_stats_map = {}
                            weekly_summary_list = []

                            for week_num, group in full_df.groupby("Week_Number"):
                                try:
                                    week_start = group[date_col].min().date()
                                    week_end = group[date_col].max().date()

                                    # Metrics
                                    n_visits = len(group)
                                    n_patients = (
                                        group["patient_id"].nunique()
                                        if "patient_id" in group.columns
                                        else 0
                                    )

                                    # Types
                                    type_col = (
                                        "task_description"
                                        if "task_description" in group.columns
                                        else (
                                            "visit_type"
                                            if "visit_type" in group.columns
                                            else None
                                        )
                                    )
                                    n_home = 0
                                    n_tele = 0
                                    n_phone = 0
                                    if type_col:
                                        n_home = len(
                                            group[
                                                group[type_col]
                                                .fillna("")
                                                .astype(str)
                                                .str.contains("Home|home", case=False)
                                            ]
                                        )
                                        n_tele = len(
                                            group[
                                                group[type_col]
                                                .fillna("")
                                                .astype(str)
                                                .str.contains(
                                                    "Telemed|Telehealth|video",
                                                    case=False,
                                                )
                                            ]
                                        )
                                        n_phone = len(
                                            group[
                                                group[type_col]
                                                .fillna("")
                                                .astype(str)
                                                .str.contains("Phone|phone", case=False)
                                            ]
                                        )

                                    stats = {
                                        "Week #": week_num,
                                        "Start Date": week_start,
                                        "End Date": week_end,
                                        "Total Visits": n_visits,
                                        "Unique Patients": n_patients,
                                        "Home Visits": n_home,
                                        "Telehealth": n_tele,
                                        "Phone": n_phone,
                                        "df": group,  # Store dataframe for detailed view
                                    }
                                    weekly_stats_map[week_num] = stats
                                    weekly_summary_list.append(stats)
                                except Exception:
                                    continue

                            # Sort weeks
                            sorted_weeks = sorted(weekly_stats_map.keys())

                            with col_week:
                                week_options = ["All Weeks"] + [
                                    f"Week {w} ({weekly_stats_map[w]['Start Date'].strftime('%b %d')} - {weekly_stats_map[w]['End Date'].strftime('%b %d')})"
                                    for w in sorted_weeks
                                ]
                                sel_week_text = st.selectbox(
                                    "Select Week",
                                    week_options,
                                    key="prov_task_week_select",
                                )

                            if sel_week_text == "All Weeks":
                                if weekly_summary_list:
                                    summary_df = pd.DataFrame(weekly_summary_list).drop(
                                        columns=["df"]
                                    )
                                    summary_df = summary_df.sort_values("Week #")

                                    st.dataframe(
                                        summary_df,
                                        use_container_width=True,
                                        hide_index=True,
                                        column_config={
                                            "Week #": st.column_config.NumberColumn(
                                                format="%d"
                                            ),
                                            "Start Date": st.column_config.DateColumn(),
                                            "End Date": st.column_config.DateColumn(),
                                            "Total Visits": st.column_config.ProgressColumn(
                                                format="%d",
                                                min_value=0,
                                                max_value=int(
                                                    summary_df["Total Visits"].max()
                                                ),
                                            ),
                                        },
                                    )

                                    # Visualization
                                    st.bar_chart(
                                        summary_df,
                                        x="Week #",
                                        y=["Home Visits", "Telehealth", "Phone"],
                                    )

                                else:
                                    st.info("No weekly data could be aggregated.")
                            else:
                                # Specific Week View
                                try:
                                    # Extract week number from string "Week X (..."
                                    week_num = int(sel_week_text.split(" ")[1])
                                    week_data = weekly_stats_map.get(week_num)

                                    if week_data:
                                        st.markdown(
                                            f"#### Details for Week {week_num} ({week_data['Start Date']} - {week_data['End Date']})"
                                        )

                                        # Metrics
                                        m1, m2, m3, m4, m5 = st.columns(5)
                                        m1.metric(
                                            "Total Visits", week_data["Total Visits"]
                                        )
                                        m2.metric(
                                            "Unique Patients",
                                            week_data["Unique Patients"],
                                        )
                                        m3.metric(
                                            "Home Visits", week_data["Home Visits"]
                                        )
                                        m4.metric("Telehealth", week_data["Telehealth"])
                                        m5.metric("Phone", week_data["Phone"])

                                        st.divider()

                                        # Detailed Table
                                        week_df = week_data["df"].copy()

                                        # Filters similar to monthly view
                                        f1, f2 = st.columns(2)
                                        with f1:
                                            if "provider_name" in week_df.columns:
                                                provs = sorted(
                                                    week_df["provider_name"]
                                                    .dropna()
                                                    .unique()
                                                )
                                                sel_prov_week = st.multiselect(
                                                    "Filter by Provider",
                                                    provs,
                                                    key="prov_task_week_prov_filter",
                                                )
                                                if sel_prov_week:
                                                    week_df = week_df[
                                                        week_df["provider_name"].isin(
                                                            sel_prov_week
                                                        )
                                                    ]

                                        with f2:
                                            if "status" in week_df.columns:
                                                statuses = sorted(
                                                    week_df["status"].dropna().unique()
                                                )
                                                default_statuses = [
                                                    s
                                                    for s in statuses
                                                    if s in ["Active", "Active-Geri", "Active-PCP", "Hospice", "HOSPICE"]
                                                ]
                                                sel_status_week = st.multiselect(
                                                    "Filter by Status",
                                                    statuses,
                                                    default=default_statuses,
                                                    key="prov_task_week_status_filter",
                                                )
                                                if sel_status_week:
                                                    week_df = week_df[
                                                        week_df["status"].isin(
                                                            sel_status_week
                                                        )
                                                    ]

                                        # Display Columns
                                        disp_cols = [
                                            c
                                            for c in [
                                                "task_date",
                                                date_col,  # Ensure we show the date
                                                "provider_name",
                                                "patient_name",
                                                "patient_id",
                                                "task_description",
                                                "minutes_of_service",
                                                "billing_code",
                                                "status",
                                                "notes",
                                            ]
                                            if c in week_df.columns
                                        ]
                                        # Deduplicate columns if date_col is task_date
                                        disp_cols = list(dict.fromkeys(disp_cols))

                                        st.data_editor(
                                            week_df[disp_cols],
                                            use_container_width=True,
                                            num_rows="dynamic",
                                            height=500,
                                            key="prov_task_weekly_detail_editor",
                                        )

                                except Exception as e:
                                    st.error(f"Error displaying week details: {e}")

                        else:
                            st.error("Could not find date column in data.")
                    else:
                        st.info("No data found for this year.")

        # --- Provider Patient Visit Breakdown ---
        st.divider()
        st.subheader("Provider Patient Visit Breakdown")

        # Add patient status filter for provider patient visits
        conn = db.get_db_connection()
        status_query = """
            SELECT DISTINCT status
            FROM patients
            WHERE status IS NOT NULL
            ORDER BY status
        """
        status_rows = conn.execute(status_query).fetchall()
        conn.close()
        available_statuses = [s[0] for s in status_rows]

        # Default to Active statuses and Hospice
        default_statuses = [s for s in available_statuses if s.startswith("Active") or s == "Hospice"]

        selected_pv_statuses = st.multiselect(
            "Filter by Patient Status:",
            options=available_statuses,
            default=default_statuses if default_statuses else available_statuses,
            key="prov_visits_status_filter",
        )

        try:
            # Get patient data for visit breakdown analysis
            patients = (
                db.get_all_patient_panel()
                if hasattr(db, "get_all_patient_panel")
                else []
            )
            patients_df = _fix_dataframe_for_streamlit(pd.DataFrame(patients))

            # Apply patient status filter
            if selected_pv_statuses and "status" in patients_df.columns:
                patients_df = patients_df[patients_df["status"].isin(selected_pv_statuses)]

            if not patients_df.empty:
                # Use the same robust date processing logic as Patient Info tab
                # Normalize last-visit column to a consistent 'Last Visit Date' string column
                possible_last_visit_cols = [
                    "last_visit_date",
                    "last_visit",
                    "last_visit_dt",
                    "last_visit_at",
                    "last_visit_timestamp",
                    "most_recent_visit",
                    "last_visit_date_iso",
                ]
                found_last = None
                for c in possible_last_visit_cols:
                    if c in patients_df.columns:
                        found_last = c
                        break

                def _format_date(val):
                    try:
                        ts = pd.to_datetime(val, errors="coerce")
                        return ts.strftime("%Y-%m-%d") if not pd.isna(ts) else None
                    except Exception:
                        return None

                if found_last:
                    patients_df["Last Visit Date"] = patients_df[found_last].apply(
                        _format_date
                    )
                else:
                    patients_df["Last Visit Date"] = None

                # If many rows are missing Last Visit Date, try to infer from task tables
                def _fill_missing_last_visit_from_tasks(df, db):
                    try:
                        # Collect patient ids that are missing a last visit
                        pids = (
                            df.loc[df["Last Visit Date"].isna(), "patient_id"]
                            .dropna()
                            .unique()
                            .tolist()
                        )
                        if not pids:
                            return {}

                        # Prepare placeholders for IN clause
                        placeholders = ",".join(["?"] * len(pids))

                        # Candidate queries from coordinator_tasks and provider_tasks using common date columns
                        select_templates = [
                            f"SELECT patient_id, date(task_date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(activity_date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(service_date) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(date) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(dos) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                        ]

                        union_sql = "\\nUNION ALL\\n".join(select_templates)
                        final_sql = f"WITH dates AS ({union_sql}) SELECT patient_id, MAX(dt) as last_visit FROM dates WHERE dt IS NOT NULL GROUP BY patient_id"

                        # params need to be repeated for each select template
                        params = pids * len(select_templates)

                        conn = db.get_db_connection()
                        try:
                            rows = conn.execute(final_sql, params).fetchall()
                        finally:
                            conn.close()

                        result = {}
                        for r in rows:
                            try:
                                # r[0] = patient_id, r[1] = last_visit (YYYY-MM-DD or None)
                                if r[1]:
                                    result[r[0]] = str(r[1])
                            except Exception:
                                continue
                        return result
                    except Exception:
                        return {}

                # Attempt to enrich missing Last Visit Dates from task tables
                try:
                    inferred = _fill_missing_last_visit_from_tasks(patients_df, db)
                    if inferred:

                        def _maybe_fill(row):
                            if row.get("Last Visit Date"):
                                return row.get("Last Visit Date")
                            pid = row.get("patient_id")
                            if pid in inferred:
                                return inferred[pid]
                            return None

                        patients_df["Last Visit Date"] = patients_df.apply(
                            _maybe_fill, axis=1
                        )
                except Exception:
                    pass

                import datetime as _dt

                today = _dt.datetime.now().date()

                def get_delta(row):
                    last_visit = row.get("Last Visit Date")
                    if last_visit:
                        try:
                            last_visit_dt = pd.to_datetime(last_visit, errors="coerce")
                            if not pd.isna(last_visit_dt):
                                last_visit_dt = last_visit_dt.date()
                                return (today - last_visit_dt).days
                        except Exception:
                            return None
                    return None

                patients_df["days_since_last_visit"] = patients_df.apply(
                    get_delta, axis=1
                )

                # Create visit category dataframes
                seen_30 = patients_df[
                    (patients_df["days_since_last_visit"] >= 0)
                    & (patients_df["days_since_last_visit"] <= 30)
                ].copy()
                seen_31_60 = patients_df[
                    (patients_df["days_since_last_visit"] > 30)
                    & (patients_df["days_since_last_visit"] <= 60)
                ].copy()
                not_seen_60 = patients_df[
                    (patients_df["days_since_last_visit"] > 60)
                    | (patients_df["days_since_last_visit"].isna())
                ].copy()

                # Columns to show in breakdown tables
                breakdown_cols = [
                    col
                    for col in [
                        "status",
                        "patient_id",
                        "first_name",
                        "last_name",
                        "dob",
                        "provider_name",
                        "coordinator_name",
                        "goc",
                        "code",
                        "Last Visit Date",
                        "last_visit_service_type",
                    ]
                    if col in patients_df.columns
                ]

                def show_styled_table(df, height):
                    try:
                        # Use the same color mapping logic as Patient Info tab
                        def color_patient_name(row):
                            color = ""
                            delta = row.get("days_since_last_visit")
                            if delta is not None:
                                if delta > 60:
                                    color = "background-color: #ffcccc; color: #a00;"
                                elif 30 < delta <= 60:
                                    color = "background-color: #fff3cd; color: #a67c00;"
                                elif 0 <= delta <= 30:
                                    color = "background-color: #d4edda; color: #155724;"
                            return color

                        # Decide which name columns to style (support both lowercase and title-case names)
                        name_cols = []
                        for cand in [
                            "First Name",
                            "Last Name",
                            "first_name",
                            "last_name",
                            "patient_first_name",
                            "patient_last_name",
                        ]:
                            if cand in df.columns:
                                name_cols.append(cand)

                        def style_names(df):
                            def _row_style(row):
                                styles = []
                                row_style = color_patient_name(row)
                                for col in df.columns:
                                    if col in name_cols:
                                        styles.append(row_style)
                                    else:
                                        styles.append("")
                                return styles

                            return df.style.apply(lambda r: _row_style(r), axis=1)

                        styled = style_names(df[breakdown_cols])
                        st.dataframe(styled, height=height, use_container_width=True)
                    except Exception:
                        st.dataframe(
                            df[breakdown_cols], height=height, use_container_width=True
                        )

                provider_col = (
                    "provider_name" if "provider_name" in patients_df.columns else None
                )
                if provider_col:
                    # Create provider statistics summary table
                    st.markdown("##### Provider Statistics Summary")

                    # Calculate stats for each provider across all categories
                    provider_stats = []
                    all_providers = set()

                    # Collect all unique providers (filter out None/NaN values)
                    for _, df_cat in [
                        ("seen_30", seen_30),
                        ("seen_31_60", seen_31_60),
                        ("not_seen_60", not_seen_60),
                    ]:
                        if not df_cat.empty and provider_col in df_cat.columns:
                            # Filter out None and NaN values
                            valid_providers = df_cat[provider_col].dropna().unique()
                            valid_providers = [
                                p
                                for p in valid_providers
                                if p is not None and str(p).strip() != ""
                            ]
                            all_providers.update(valid_providers)

                    # Calculate counts for each provider
                    for provider in sorted(all_providers):
                        # Use safe filtering that handles None values
                        seen_30_count = (
                            len(seen_30[seen_30[provider_col].fillna("") == provider])
                            if not seen_30.empty and provider_col in seen_30.columns
                            else 0
                        )
                        seen_31_60_count = (
                            len(
                                seen_31_60[
                                    seen_31_60[provider_col].fillna("") == provider
                                ]
                            )
                            if not seen_31_60.empty
                            and provider_col in seen_31_60.columns
                            else 0
                        )
                        not_seen_60_count = (
                            len(
                                not_seen_60[
                                    not_seen_60[provider_col].fillna("") == provider
                                ]
                            )
                            if not not_seen_60.empty
                            and provider_col in not_seen_60.columns
                            else 0
                        )
                        total_count = (
                            seen_30_count + seen_31_60_count + not_seen_60_count
                        )

                        provider_stats.append(
                            {
                                "Provider": provider,
                                "🟢 Seen ≤30 days": seen_30_count,
                                "🟡 Seen 31-60 days": seen_31_60_count,
                                "🔴 Not seen >60 days": not_seen_60_count,
                                "Total Patients": total_count,
                            }
                        )

                    if provider_stats:
                        stats_df = pd.DataFrame(provider_stats)
                        st.dataframe(
                            stats_df, use_container_width=True, hide_index=True
                        )
                    else:
                        st.info("No provider data available.")

                    st.markdown("---")
                    for label, df_cat in [
                        ("Patients seen in the last 30 days", seen_30),
                        ("Patients seen 1mo <> 2mo", seen_31_60),
                        ("Patients NOT seen by Regional Provider in 2mo", not_seen_60),
                    ]:
                        # Use expandable sections with color-coded titles
                        if "last 30 days" in label:
                            # Green for recent visits (good)
                            expander_title = f"🟢 {label} by Provider"
                            color_style = "background-color: #d4edda; color: #155724;"
                        elif "1mo <> 2mo" in label:
                            # Yellow for moderate delay
                            expander_title = f"🟡 {label} by Provider"
                            color_style = "background-color: #fff3cd; color: #a67c00;"
                        else:
                            # Red for long delays (concerning)
                            expander_title = f"🔴 {label} by Provider"
                            color_style = "background-color: #ffcccc; color: #a00;"

                        with st.expander(expander_title, expanded=False):
                            grouped = df_cat.groupby(provider_col)
                            if grouped.ngroups == 0:
                                st.info(f"No providers have patients in this category.")
                            else:
                                for prov, prov_df in grouped:
                                    # Use subheader instead of nested expander
                                    st.markdown(
                                        f"**Provider: {prov}** ({len(prov_df)} patients)"
                                    )
                                    if prov_df.empty:
                                        st.info(
                                            "No patients for this provider in this category."
                                        )
                                    else:
                                        show_styled_table(prov_df, 300)
                                    st.markdown(
                                        "---"
                                    )  # Add separator between providers
                else:
                    st.info("Provider information not available in patient data.")
            else:
                st.info("No patient data available for visit breakdown analysis.")
        except Exception as e:
            st.error(f"Error loading provider patient visit breakdown: {e}")

    # --- TAB 3: Patient Info ---
    with tab3:
        st.subheader("Patient Info Table (All Patient Data, Assignments)")

        # --- Search Filter (at the top) ---
        st.markdown("### Search Patients")
        search_term = st.text_input(
            "Search by Name or ID", key="patient_info_search_input"
        )

        # --- Enable Editing Control ---
        editable_admin = st.checkbox(
            "Enable editing", value=False, key="admin_patient_info_editable"
        )

        # --- Patient Reassignment Controls ---
        with st.expander("🔄 Patient Reassignment Controls", expanded=False):
            st.markdown("#### Role-based Patient Assignment Management")

            # Role Selection
            col_assign_role1, col_assign_role2 = st.columns([1, 1])
            with col_assign_role1:
                assignment_role = st.selectbox(
                    "Assignment Role",
                    ["Provider", "Coordinator"],
                    key="admin_assignment_role",
                    help="Select role for patient reassignment",
                )

            # Get available providers/coordinators based on role
            try:
                if assignment_role == "Provider":
                    # Get care providers using proper database function (role_id 33)
                    providers = db.get_users_by_role(ROLE_CARE_PROVIDER)
                    available_assignees = [
                        (
                            p["user_id"],
                            p.get("full_name", ""),
                        )
                        for p in providers
                    ]
                else:
                    # Get care coordinators using proper database function (role_id 36)
                    coordinators = db.get_users_by_role(36)
                    available_assignees = [
                        (
                            c["user_id"],
                            c.get("full_name", ""),
                        )
                        for c in coordinators
                    ]
            except Exception as e:
                st.error(f"Error loading assignees: {e}")
                available_assignees = []

            # Reassignment Method Selection
            reassignment_method = st.radio(
                "Reassignment Method",
                ["Individual Patient Assignment", "Bulk Assignment"],
                key="admin_reassignment_method",
                help="Choose individual or bulk reassignment approach",
            )

            if reassignment_method == "Individual Patient Assignment":
                st.markdown("##### Individual Patient Assignment")

                # Patient Selection (by name/ID search)
                col_patient_search, col_assignee_search = st.columns([2, 1])
                with col_patient_search:
                    patient_search = st.text_input(
                        "Search Patient for Reassignment",
                        key="admin_individual_patient_search",
                        help="Type patient name or ID to find specific patient",
                    )

                # Selected patient display
                if patient_search:
                    # Filter available patients based on search
                    try:
                        all_patients = (
                            db.get_all_patient_panel()
                            if hasattr(db, "get_all_patient_panel")
                            else []
                        )
                        patients_for_search = _fix_dataframe_for_streamlit(
                            pd.DataFrame(all_patients)
                        )

                        if not patients_for_search.empty:
                            search_term_lower = patient_search.lower()
                            # Filter by name or ID
                            search_mask = pd.Series(
                                False, index=patients_for_search.index
                            )

                            if "first_name" in patients_for_search.columns:
                                search_mask |= (
                                    patients_for_search["first_name"]
                                    .fillna("")
                                    .astype(str)
                                    .str.lower()
                                    .str.contains(search_term_lower)
                                )
                            if "last_name" in patients_for_search.columns:
                                search_mask |= (
                                    patients_for_search["last_name"]
                                    .fillna("")
                                    .astype(str)
                                    .str.lower()
                                    .str.contains(search_term_lower)
                                )
                            if "patient_id" in patients_for_search.columns:
                                search_mask |= (
                                    patients_for_search["patient_id"]
                                    .fillna("")
                                    .astype(str)
                                    .str.lower()
                                    .str.contains(search_term_lower)
                                )

                            filtered_patients = patients_for_search[search_mask]

                            if not filtered_patients.empty:
                                # Display searchable patients for selection
                                display_patients = []
                                for _, row in filtered_patients.head(
                                    10
                                ).iterrows():  # Limit to 10 results
                                    p_id = row.get("patient_id", "N/A")
                                    first_name = row.get("first_name", "N/A")
                                    last_name = row.get("last_name", "N/A")
                                    display_patients.append(
                                        f"{p_id} - {first_name} {last_name}"
                                    )

                                selected_patient_display = st.selectbox(
                                    "Select Patient",
                                    display_patients,
                                    key="admin_selected_patient_display",
                                    help="Select patient for reassignment",
                                )

                                # Extract patient_id from selected display
                                if selected_patient_display:
                                    selected_patient_id = (
                                        selected_patient_display.split(" - ")[0]
                                    )

                                    # Assignee Selection
                                    col_assignee_sel = st.columns([2, 1])
                                    with col_assignee_sel[0]:
                                        if available_assignees:
                                            assignee_options = {
                                                name: uid
                                                for uid, name in available_assignees
                                            }
                                            selected_assignee = st.selectbox(
                                                f"New {assignment_role}",
                                                list(assignee_options.keys()),
                                                key="admin_individual_assignee",
                                                help=f"Select new {assignment_role.lower()}",
                                            )
                                            new_assignee_id = assignee_options.get(
                                                selected_assignee
                                            )
                                        else:
                                            st.warning(
                                                f"No available {assignment_role.lower()}s found"
                                            )
                                            new_assignee_id = None

                                    # Confirmation and Execute
                                    with col_assignee_sel[1]:
                                        st.markdown("")  # Spacer
                                        if st.button(
                                            f"Assign to {assignment_role}",
                                            key="admin_execute_individual_assign",
                                        ):
                                            if (
                                                new_assignee_id
                                                and selected_patient_id != "N/A"
                                            ):
                                                try:
                                                    _execute_patient_reassignment(
                                                        selected_patient_id,
                                                        assignment_role,
                                                        new_assignee_id,
                                                        user_id,
                                                    )
                                                    st.success(
                                                        f"Patient {selected_patient_id} successfully reassigned to {assignment_role.lower()}"
                                                    )
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(
                                                        f"Error reassigning patient: {e}"
                                                    )
                                            else:
                                                st.error(
                                                    "Please select both patient and assignee"
                                                )
                            else:
                                st.warning(
                                    f"No patients found matching '{patient_search}'"
                                )
                    except Exception as e:
                        st.error(f"Error searching patients: {e}")

            else:  # Bulk Assignment
                st.markdown("##### Bulk Patient Assignment")

                # Bulk Patient Selection
                bulk_patient_filter = st.selectbox(
                    "Filter Patients for Bulk Assignment",
                    [
                        "All Active Patients",
                        "Search by Name/ID",
                        "Select from Current Results",
                    ],
                    key="admin_bulk_patient_filter",
                    help="Choose how to select patients for bulk assignment",
                )

                bulk_patients_to_assign = []

                if bulk_patient_filter == "Search by Name/ID":
                    bulk_search_term = st.text_input(
                        "Search patients for bulk assignment",
                        key="admin_bulk_search",
                        help="Enter search term to filter patients",
                    )
                    # Apply search logic similar to individual
                    try:
                        all_patients = (
                            db.get_all_patient_panel()
                            if hasattr(db, "get_all_patient_panel")
                            else []
                        )
                        patients_for_bulk = _fix_dataframe_for_streamlit(
                            pd.DataFrame(all_patients)
                        )

                        if bulk_search_term and not patients_for_bulk.empty:
                            search_term_lower = bulk_search_term.lower()
                            bulk_search_mask = pd.Series(
                                False, index=patients_for_bulk.index
                            )

                            if "first_name" in patients_for_bulk.columns:
                                bulk_search_mask |= (
                                    patients_for_bulk["first_name"]
                                    .fillna("")
                                    .astype(str)
                                    .str.lower()
                                    .str.contains(search_term_lower)
                                )
                            if "last_name" in patients_for_bulk.columns:
                                bulk_search_mask |= (
                                    patients_for_bulk["last_name"]
                                    .fillna("")
                                    .astype(str)
                                    .str.lower()
                                    .str.contains(search_term_lower)
                                )
                            if "patient_id" in patients_for_bulk.columns:
                                bulk_search_mask |= (
                                    patients_for_bulk["patient_id"]
                                    .fillna("")
                                    .astype(str)
                                    .str.lower()
                                    .str.contains(search_term_lower)
                                )

                            filtered_bulk_patients = patients_for_bulk[bulk_search_mask]
                            bulk_patients_to_assign = (
                                filtered_bulk_patients["patient_id"].dropna().tolist()
                                if not filtered_bulk_patients.empty
                                else []
                            )
                    except Exception as e:
                        st.error(f"Error filtering patients: {e}")

                elif bulk_patient_filter == "All Active Patients":
                    try:
                        all_patients = (
                            db.get_all_patient_panel()
                            if hasattr(db, "get_all_patient_panel")
                            else []
                        )
                        all_patients_df = _fix_dataframe_for_streamlit(
                            pd.DataFrame(all_patients)
                        )
                        if not all_patients_df.empty:
                            active_statuses = ["Active", "Active-Geri", "Active-PCP", "Hospice", "HOSPICE"]
                            if "status" in all_patients_df.columns:
                                status_normalized = (
                                    all_patients_df["status"]
                                    .fillna("")
                                    .astype(str)
                                    .str.strip()
                                )
                                active_patients = all_patients_df[
                                    (status_normalized.isin(active_statuses))
                                    | (status_normalized.str.startswith("Active"))
                                    | (status_normalized.str.upper() == "HOSPICE")
                                ]
                                bulk_patients_to_assign = (
                                    active_patients["patient_id"].dropna().tolist()
                                )
                    except Exception as e:
                        st.error(f"Error loading active patients: {e}")

                # Display selected patients count
                if bulk_patients_to_assign:
                    st.info(
                        f"Selected {len(bulk_patients_to_assign)} patients for reassignment"
                    )

                    # Bulk Assignee Selection
                    if available_assignees:
                        bulk_assignee_options = {
                            name: uid
                            for uid, name in available_assignees
                        }
                        bulk_selected_assignee = st.selectbox(
                            f"Bulk Assign to {assignment_role}",
                            list(bulk_assignee_options.keys()),
                            key="admin_bulk_assignee",
                            help=f"Select {assignment_role.lower()} for bulk assignment",
                        )
                        bulk_new_assignee_id = bulk_assignee_options.get(
                            bulk_selected_assignee
                        )

                        # Confirmation dialog for bulk operation
                        col_confirm1, col_confirm2 = st.columns([2, 1])
                        with col_confirm1:
                            st.warning(
                                f"This will reassign {len(bulk_patients_to_assign)} patients to {assignment_role.lower()}: {bulk_selected_assignee}"
                            )
                        with col_confirm2:
                            if st.button(
                                f"Execute Bulk Assignment",
                                key="admin_execute_bulk_assign",
                            ):
                                if bulk_new_assignee_id:
                                    try:
                                        success_count = 0
                                        for patient_id in bulk_patients_to_assign:
                                            try:
                                                _execute_patient_reassignment(
                                                    patient_id,
                                                    assignment_role,
                                                    bulk_new_assignee_id,
                                                    user_id,
                                                )
                                                success_count += 1
                                            except Exception:
                                                continue  # Continue with next patient if one fails

                                        st.success(
                                            f"Successfully reassigned {success_count} of {len(bulk_patients_to_assign)} patients"
                                        )
                                        if success_count < len(bulk_patients_to_assign):
                                            st.warning(
                                                f"{len(bulk_patients_to_assign) - success_count} patients could not be reassigned"
                                            )
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error in bulk reassignment: {e}")
                                else:
                                    st.error(
                                        "Please select assignee for bulk assignment"
                                    )
                    else:
                        st.warning(f"No available {assignment_role.lower()}s found")
                else:
                    st.info("No patients selected for bulk assignment")

        st.markdown("---")

        # Apply search filter immediately after data loading
        try:
            patients = (
                db.get_all_patient_panel()
                if hasattr(db, "get_all_patient_panel")
                else []
            )
            patients_df = _fix_dataframe_for_streamlit(pd.DataFrame(patients))
            if patients_df.empty:
                st.info("No patients found in patient_panel.")
            else:
                # Apply search filter
                if search_term:
                    search_term_lower = search_term.lower()
                    # Filter by first_name, last_name, or patient_id
                    mask = pd.Series(False, index=patients_df.index)

                    if "first_name" in patients_df.columns:
                        mask |= (
                            patients_df["first_name"]
                            .fillna("")
                            .astype(str)
                            .str.lower()
                            .str.contains(search_term_lower)
                        )
                    if "last_name" in patients_df.columns:
                        mask |= (
                            patients_df["last_name"]
                            .fillna("")
                            .astype(str)
                            .str.lower()
                            .str.contains(search_term_lower)
                        )
                    if "patient_id" in patients_df.columns:
                        mask |= (
                            patients_df["patient_id"]
                            .fillna("")
                            .astype(str)
                            .str.lower()
                            .str.contains(search_term_lower)
                        )

                    patients_df = patients_df[mask]

                    if patients_df.empty:
                        st.warning(f"No patients found matching '{search_term}'")
                # Prefer sorting by last_name then first_name when available
                sort_cols = [
                    c for c in ["last_name", "first_name"] if c in patients_df.columns
                ]
                if sort_cols:
                    patients_df = patients_df.sort_values(
                        by=sort_cols, na_position="last"
                    )

                # Normalize last-visit column to a consistent 'Last Visit Date' string column
                possible_last_visit_cols = [
                    "last_visit_date",
                    "last_visit",
                    "last_visit_dt",
                    "last_visit_at",
                    "last_visit_timestamp",
                    "most_recent_visit",
                    "last_visit_date_iso",
                ]
                found_last = None
                for c in possible_last_visit_cols:
                    if c in patients_df.columns:
                        found_last = c
                        break

                def _format_date(val):
                    try:
                        ts = pd.to_datetime(val, errors="coerce")
                        return ts.strftime("%Y-%m-%d") if not pd.isna(ts) else None
                    except Exception:
                        return None

                if found_last:
                    patients_df["Last Visit Date"] = patients_df[found_last].apply(
                        _format_date
                    )
                else:
                    patients_df["Last Visit Date"] = None

                # If many rows are missing Last Visit Date, try to infer from task tables
                def _fill_missing_last_visit_from_tasks(df, db):
                    try:
                        # Collect patient ids that are missing a last visit
                        pids = (
                            df.loc[df["Last Visit Date"].isna(), "patient_id"]
                            .dropna()
                            .unique()
                            .tolist()
                        )
                        if not pids:
                            return {}

                        # Prepare placeholders for IN clause
                        placeholders = ",".join(["?"] * len(pids))

                        # Candidate queries from coordinator_tasks and provider_tasks using common date columns
                        union_selects = []
                        select_templates = [
                            f"SELECT patient_id, date(task_date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(activity_date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(service_date) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(date) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                            f"SELECT patient_id, date(dos) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                        ]

                        union_sql = "\nUNION ALL\n".join(select_templates)
                        final_sql = f"WITH dates AS ({union_sql}) SELECT patient_id, MAX(dt) as last_visit FROM dates WHERE dt IS NOT NULL GROUP BY patient_id"

                        # params need to be repeated for each select template
                        params = pids * len(select_templates)

                        conn = db.get_db_connection()
                        try:
                            rows = conn.execute(final_sql, params).fetchall()
                        finally:
                            conn.close()

                        result = {}
                        for r in rows:
                            try:
                                # r[0] = patient_id, r[1] = last_visit (YYYY-MM-DD or None)
                                if r[1]:
                                    result[r[0]] = str(r[1])
                            except Exception:
                                continue
                        return result
                    except Exception:
                        return {}

                # Attempt to enrich missing Last Visit Dates from task tables
                try:
                    inferred = _fill_missing_last_visit_from_tasks(patients_df, db)
                    if inferred:

                        def _maybe_fill(row):
                            if row.get("Last Visit Date"):
                                return row.get("Last Visit Date")
                            pid = row.get("patient_id")
                            if pid in inferred:
                                return inferred[pid]
                            return None

                        patients_df["Last Visit Date"] = patients_df.apply(
                            _maybe_fill, axis=1
                        )
                except Exception:
                    pass

                import datetime as _dt

                today = _dt.datetime.now().date()

                def get_delta(row):
                    last_visit = row.get("Last Visit Date")
                    if last_visit:
                        try:
                            last_visit_dt = pd.to_datetime(last_visit, errors="coerce")
                            if not pd.isna(last_visit_dt):
                                last_visit_dt = last_visit_dt.date()
                                return (today - last_visit_dt).days
                        except Exception:
                            return None
                    return None

                patients_df["days_since_last_visit"] = patients_df.apply(
                    get_delta, axis=1
                )

                # Color mapping for patient name columns
                def color_patient_name(row):
                    color = ""
                    delta = row.get("days_since_last_visit")
                    if delta is not None:
                        if delta > 60:
                            color = "background-color: #ffcccc; color: #a00;"
                        elif 30 < delta <= 60:
                            color = "background-color: #fff3cd; color: #a67c00;"
                        elif 0 <= delta <= 30:
                            color = "background-color: #d4edda; color: #155724;"
                    return color

                # Decide which name columns to style (support both lowercase and title-case names)
                name_cols = []
                for cand in [
                    "First Name",
                    "Last Name",
                    "first_name",
                    "last_name",
                    "patient_first_name",
                    "patient_last_name",
                ]:
                    if cand in patients_df.columns:
                        name_cols.append(cand)

                def style_names(df):
                    def _row_style(row):
                        styles = []
                        row_style = color_patient_name(row)
                        for col in df.columns:
                            if col in name_cols:
                                styles.append(row_style)
                            else:
                                styles.append("")
                        return styles

                    return df.style.apply(lambda r: _row_style(r), axis=1)

                # --- Patient Visit Breakdown (move above main table) ---
                seen_30 = patients_df[
                    (patients_df["days_since_last_visit"] >= 0)
                    & (patients_df["days_since_last_visit"] <= 30)
                ].copy()
                seen_31_60 = patients_df[
                    (patients_df["days_since_last_visit"] > 30)
                    & (patients_df["days_since_last_visit"] <= 60)
                ].copy()
                not_seen_60 = patients_df[
                    (patients_df["days_since_last_visit"] > 60)
                    | (patients_df["days_since_last_visit"].isna())
                ].copy()

                st.markdown("#### Patient Visit Breakdown")

                # Columns to show in breakdown tables - updated order per requirements
                required_columns = [
                    "status",
                    "goc_value",
                    "code_status",
                    "subjective_risk_level",
                    "first_name",
                    "phone_medical",
                    "phone_appointment",
                    "phone_medical_number",
                    "phone_appointment_number",
                    "facility",
                    "provider_name",
                    "coordinator_name",
                    "Last Visit Date",
                    "service_type",
                ]

                breakdown_cols = [
                    col for col in required_columns if col in patients_df.columns
                ]

                def show_styled_table(df, height):
                    try:
                        styled = style_names(df[breakdown_cols])
                        st.dataframe(styled, height=height, use_container_width=True)
                    except Exception:
                        st.dataframe(
                            df[breakdown_cols], height=height, use_container_width=True
                        )

                with st.expander(
                    f"Patients seen in the last 30 days ({len(seen_30)})",
                    expanded=(len(seen_30) > 0 and len(seen_30) <= 10),
                ):
                    if seen_30.empty:
                        st.info("No patients seen in the last 30 days.")
                    else:
                        show_styled_table(seen_30, 400)

                with st.expander(
                    f"Patients seen 1mo <> 2mo ({len(seen_31_60)})",
                    expanded=(len(seen_31_60) > 0 and len(seen_31_60) <= 10),
                ):
                    if seen_31_60.empty:
                        st.info("No patients seen between 1 and 2 months ago.")
                    else:
                        show_styled_table(seen_31_60, 400)

                with st.expander(
                    f"Patients NOT seen by Regional Provider in 2mo ({len(not_seen_60)})",
                    expanded=(len(not_seen_60) > 0 and len(not_seen_60) <= 10),
                ):
                    if not_seen_60.empty:
                        st.info("No patients not seen in over 2 months.")
                    else:
                        show_styled_table(not_seen_60, 400)

                st.markdown("---")

                # Split patients into active and inactive
                active_statuses = ["Active", "Active-Geri", "Active-PCP", "Hospice", "HOSPICE"]
                if "status" in patients_df.columns:
                    # Active patients: status starts with 'Active' or is 'Hospice' (case-insensitive)
                    status_normalized = (
                        patients_df["status"]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    )
                    active_patients = patients_df[
                        (status_normalized.isin(active_statuses))
                        | (status_normalized.str.startswith("Active"))
                        | (status_normalized.str.upper() == "HOSPICE")
                    ].copy()

                    # Inactive patients: everything else
                    inactive_patients = patients_df[
                        ~(
                            (status_normalized.isin(active_statuses))
                            | (status_normalized.str.startswith("Active"))
                            | (status_normalized.str.upper() == "HOSPICE")
                        )
                    ].copy()
                else:
                    # If no status column, treat all as active
                    active_patients = patients_df.copy()
                    inactive_patients = pd.DataFrame()

                if not editable_admin:
                    st.markdown(f"#### 🟢 Active Patients ({len(active_patients)})")
                    if not active_patients.empty:
                        try:
                            styled_active = style_names(active_patients)
                            st.dataframe(
                                styled_active, height=600, use_container_width=True
                            )
                        except Exception:
                            st.dataframe(
                                active_patients, height=600, use_container_width=True
                            )
                    else:
                        st.info("No active patients found.")
                else:
                    display_cols = [
                        "patient_id",
                        "status",
                        "first_name",
                        "last_name",
                        "facility",
                        "Last Visit Date",
                        "service_type",
                        "phone_primary",
                        "labs_notes",
                        "imaging_notes",
                        "general_notes",
                        "next_appointment_date",
                    ]
                    existing_cols = [
                        c for c in display_cols if c in active_patients.columns
                    ]
                    df_display = active_patients[existing_cols].copy()
                    col_config = {}
                    if "patient_id" in df_display.columns:
                        col_config["patient_id"] = st.column_config.TextColumn(
                            "patient_id", disabled=True
                        )
                    if "labs_notes" in df_display.columns:
                        col_config["labs_notes"] = st.column_config.TextColumn(
                            "Labs Notes", help="Notes about lab results"
                        )
                    if "imaging_notes" in df_display.columns:
                        col_config["imaging_notes"] = st.column_config.TextColumn(
                            "Imaging Notes", help="Notes about imaging results"
                        )
                    if "general_notes" in df_display.columns:
                        col_config["general_notes"] = st.column_config.TextColumn(
                            "General Notes", help="General patient notes"
                        )
                    if "next_appointment_date" in df_display.columns:
                        col_config["next_appointment_date"] = st.column_config.TextColumn(
                            "Next Appointment Date", help="Date of next scheduled appointment"
                        )
                    edited = st.data_editor(
                        df_display,
                        use_container_width=True,
                        num_rows="dynamic",
                        height=600,
                        column_config=col_config,
                        key="admin_patient_info_editor",
                    )
                    if st.button("Save changes", key="admin_patient_info_save"):
                        try:
                            _apply_patient_info_edits_admin(edited, df_display)
                            st.success("Patient records updated.")
                        except Exception as e:
                            st.error(f"Error saving changes: {e}")

                # --- Inactive Patients Section (Expandable) ---
                with st.expander(
                    f"🔴 Inactive Patients ({len(inactive_patients)})", expanded=False
                ):
                    if not inactive_patients.empty:
                        if not editable_admin:
                            try:
                                styled_inactive = style_names(inactive_patients)
                                st.dataframe(
                                    styled_inactive,
                                    height=400,
                                    use_container_width=True,
                                )
                            except Exception:
                                st.dataframe(
                                    inactive_patients,
                                    height=400,
                                    use_container_width=True,
                                )
                        else:
                            display_cols = [
                                "patient_id",
                                "status",
                                "first_name",
                                "last_name",
                                "facility",
                                "Last Visit Date",
                                "service_type",
                                "phone_primary",
                                "labs_notes",
                                "imaging_notes",
                                "general_notes",
                                "next_appointment_date",
                            ]
                            existing_cols = [
                                c
                                for c in display_cols
                                if c in inactive_patients.columns
                            ]
                            df_display = inactive_patients[existing_cols].copy()
                            col_config = {}
                            if "patient_id" in df_display.columns:
                                col_config["patient_id"] = st.column_config.TextColumn(
                                    "patient_id", disabled=True
                                )
                            if "labs_notes" in df_display.columns:
                                col_config["labs_notes"] = st.column_config.TextColumn(
                                    "Labs Notes", help="Notes about lab results"
                                )
                            if "imaging_notes" in df_display.columns:
                                col_config["imaging_notes"] = st.column_config.TextColumn(
                                    "Imaging Notes", help="Notes about imaging results"
                                )
                            if "general_notes" in df_display.columns:
                                col_config["general_notes"] = st.column_config.TextColumn(
                                    "General Notes", help="General patient notes"
                                )
                            if "next_appointment_date" in df_display.columns:
                                col_config["next_appointment_date"] = st.column_config.TextColumn(
                                    "Next Appointment Date", help="Date of next scheduled appointment"
                                )
                            edited_inactive = st.data_editor(
                                df_display,
                                use_container_width=True,
                                num_rows="dynamic",
                                height=400,
                                column_config=col_config,
                                key="admin_patient_info_editor_inactive",
                            )
                            if st.button(
                                "Save changes (Inactive)",
                                key="admin_patient_info_save_inactive",
                            ):
                                try:
                                    _apply_patient_info_edits_admin(
                                        edited_inactive, df_display
                                    )
                                    st.success("Patient records updated.")
                                except Exception as e:
                                    st.error(f"Error saving changes: {e}")
                    else:
                        st.info("No inactive patients found.")

        except Exception as e:
            st.error(f"Error loading patient data: {e}")

    # --- TAB: HHC View Template ---
    with tab_hhc:
        st.subheader("HHC View Template - Active Patients")
        st.markdown(
            "Daily export view of all active patients with key clinical and administrative data"
        )

        try:
            # Get all available patient statuses
            conn = db.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT status FROM patients WHERE status IS NOT NULL AND status != '' ORDER BY status"
            )
            all_statuses = [row[0] for row in cursor.fetchall()]
            conn.close()

            # Create filter controls
            st.markdown("### Filter Patients")
            col1, col2 = st.columns([3, 1])

            with col1:
                # Default selection: Active, Active-PCP, Active-Geri, HOSPICE
                default_statuses = [
                    s
                    for s in all_statuses
                    if s in ["Active", "Active-PCP", "Active-Geri", "HOSPICE"]
                ]
                selected_statuses = st.multiselect(
                    "Select Patient Status(es)",
                    options=all_statuses,
                    default=default_statuses,
                    help="Select which patient statuses to display",
                )

            with col2:
                if st.button("Reset to All"):
                    st.session_state.status_filter = all_statuses

            if not selected_statuses:
                st.warning("Please select at least one patient status to display")
                st.stop()

            st.divider()

            # Fetch patients with selected statuses using the new HHC export function
            hhc_data = db.get_hhc_export_data(selected_statuses)

            if hhc_data:
                # Convert to DataFrame for consistency with existing code
                df_hhc = pd.DataFrame(hhc_data)
                rows = [list(row.values()) for row in hhc_data]
                columns = list(hhc_data[0].keys())
            else:
                df_hhc = pd.DataFrame()
                rows = []
                columns = []

            if rows and not df_hhc.empty:
                # Display summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Active Patients", len(df_hhc))
                with col2:
                    assigned_count = (df_hhc["Assigned"] == "Yes").sum()
                    st.metric("Assigned to Coordinator", assigned_count)
                with col3:
                    with_provider = (
                        df_hhc["Prov"]
                        .apply(lambda x: x != "Unassigned" if pd.notna(x) else False)
                        .sum()
                    )
                    st.metric("With Provider", with_provider)
                with col4:
                    st.metric("Unassigned", len(df_hhc) - assigned_count)

                st.divider()

                # Display the data table with key columns visible by default
                key_columns = [
                    "Pt Status",
                    "Name",
                    "LAST FIRST DOB",
                    "Last Visit",
                    "Contact",
                    "City",
                    "Fac",
                    "Prov",
                    "Care Coordinator",
                    "Insurance Eligibility",
                    "Risk",
                    "General Notes",
                ]

                # Reorder columns to show key fields first
                display_columns = [col for col in key_columns if col in df_hhc.columns]
                other_columns = [
                    col for col in df_hhc.columns if col not in display_columns
                ]
                df_display = df_hhc[display_columns + other_columns]

                st.dataframe(
                    df_display,
                    use_container_width=True,
                    height=600,
                    column_config={
                        "Pt Status": st.column_config.TextColumn("Status"),
                        "Name": st.column_config.TextColumn("Patient Name"),
                        "Last Visit": st.column_config.TextColumn("Last Visit Date"),
                        "Contact": st.column_config.TextColumn("Phone"),
                        "Prov": st.column_config.TextColumn("Provider"),
                        "Care Coordinator": st.column_config.TextColumn("Coordinator"),
                        "Risk": st.column_config.TextColumn("Risk Level"),
                        "General Notes": st.column_config.TextColumn(
                            "Notes", width="medium"
                        ),
                    },
                )

                # Export options
                st.divider()
                col1, col2, col3 = st.columns(3)
                with col1:
                    csv_export = df_display.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv_export,
                        file_name=f"hhc_patients_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                    )
                with col2:
                    st.info(
                        "💡 Tip: Click column headers to sort, use search to filter"
                    )
                with col3:
                    if st.button("🔄 Refresh Data"):
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.info("No active patients found in the database.")

        except Exception as e:
            st.error(f"Error loading HHC View Template: {e}")
            logger.error(f"HHC View Template error: {e}", exc_info=True)

    # --- TAB: Billing Report ---
    with tab_billing:
        # Check if user has admin role (role_id 34) and is authorized for billing
        current_user = st.session_state.get("authenticated_user")
        user_email = current_user.get("email", "") if current_user else ""
        has_admin_access = False
        show_billing = False

        if current_user and "user_id" in current_user:
            user_id = current_user["user_id"]
            try:
                user_roles = db.get_user_roles_by_user_id(user_id)
                has_admin_access = any(role["role_id"] == 34 for role in user_roles)
                # Show billing only to Justin (18) and Harpreet (12)
                show_billing = has_admin_access and user_id in [12, 18]
            except Exception as e:
                st.error(f"Error checking user roles: {e}")
                has_admin_access = False
                show_billing = False

        if show_billing:
            # Create sub-tabs for different billing views
            billing_tab1, billing_tab2, billing_tab3 = st.tabs(
                [
                    "Monthly Billing (Coordinators)",
                    "Weekly Billing (Providers)",
                    "Provider Payroll",
                ]
            )

            with billing_tab1:
                st.subheader("Monthly Coordinator Billing")
                st.markdown(
                    "Track coordinator billing by month using patient minutes and billing codes"
                )
                try:
                    from src.dashboards.monthly_coordinator_billing_dashboard import (
                        display_monthly_coordinator_billing_dashboard,
                    )

                    display_monthly_coordinator_billing_dashboard()
                except Exception as e:
                    st.error(
                        f"Error loading monthly coordinator billing dashboard: {e}"
                    )
                    st.info(
                        "Please ensure the monthly coordinator billing dashboard module is properly configured."
                    )

            with billing_tab2:
                st.subheader("Weekly Provider Billing")
                st.markdown(
                    "Track provider billing by week using provider tasks and billing status"
                )
                try:
                    from src.dashboards.weekly_provider_billing_dashboard_v2 import (
                        display_weekly_provider_billing_dashboard,
                    )

                    display_weekly_provider_billing_dashboard()
                except Exception as e:
                    st.error(f"Error loading weekly provider billing dashboard: {e}")
                    st.info(
                        "Please ensure the weekly provider billing dashboard module is properly configured."
                    )

            with billing_tab3:
                st.subheader("Weekly Provider Payroll")
                st.markdown("Track provider payroll by week and mark providers as paid")
                try:
                    from src.dashboards.weekly_provider_payroll_dashboard import (
                        display_weekly_provider_payroll_dashboard,
                    )

                    display_weekly_provider_payroll_dashboard()
                except Exception as e:
                    st.error(f"Error loading weekly provider payroll dashboard: {e}")
                    st.info(
                        "Please ensure the weekly provider payroll dashboard module is properly configured."
                    )
        else:
            st.warning("Billing Access Restricted")
            st.info(
                "Billing dashboard access is restricted to Justin and Harpreet only."
            )
            st.markdown("---")
            st.markdown(
                "**Note:** This tab is visible but billing features are limited to authorized users."
            )
            st.markdown(
                "- Current user email: `{}`".format(
                    user_email if user_email else "Not available"
                )
            )

    # --- TAB: ZMO ---
    with tab_test:
        # Import and use the shared ZMO module
        from src.zmo_module import render_zmo_tab
        render_zmo_tab(user_id=user_id)

    # --- TAB: Workflow Analytics & Unassigned Patients ---
    with tab_analytics_unassigned:
        # Import the new workflow analytics and unassigned patients module
        from src.dashboards.workflow_analytics_unassigned_module import show_workflow_analytics_unassigned_tab

        # Get user's role IDs
        user_role_ids = db.get_user_role_ids(user_id) if hasattr(db, 'get_user_role_ids') else []

        # Show the workflow analytics and unassigned patients tab
        show_workflow_analytics_unassigned_tab(
            user_id=user_id,
            user_role_ids=user_role_ids
        )

    # --- TAB: Workflow Reassignment (Bianchi's Special View) ---
    with tab_workflow:
        st.subheader("🔧 Workflow Reassignment")
        st.markdown(
            "Admin-level workflow management with bulk reassignment capabilities"
        )

        debug_mode = st.session_state.get("admin_debug_session", False)

        try:
            # Simple approach - get all active workflows directly
            conn = db.get_db_connection()
            result = conn.execute("""
                SELECT
                    instance_id,
                    template_name as workflow_type,
                    patient_name,
                    patient_id,
                    coordinator_id,
                    coordinator_name,
                    workflow_status,
                    current_step,
                    priority,
                    created_at,
                    (
                        SELECT COUNT(*)
                        FROM workflow_steps ws
                        WHERE ws.template_id = wi.template_id
                    ) as total_steps
                FROM workflow_instances wi
                WHERE workflow_status = 'Active'
                ORDER BY created_at DESC
            """)

            workflows = result.fetchall()
            conn.close()

            if workflows:
                # Convert to DataFrame with defensive programming
                df_data = []
                for wf in workflows:
                    wf_dict = dict(wf)
                    df_data.append(
                        {
                            "instance_id": wf_dict["instance_id"],
                            "workflow_type": wf_dict.get("template_name", "Unknown"),
                            "patient_name": wf_dict.get("patient_name", "Unknown"),
                            "patient_id": wf_dict.get("patient_id", "Unknown"),
                            "coordinator_name": wf_dict.get(
                                "coordinator_name", "Unknown"
                            ),
                            "workflow_status": wf_dict.get("workflow_status", "Active"),
                            "current_step": wf_dict.get("current_step", 1),
                            "total_steps": wf_dict.get("total_steps", 1),
                            "priority": wf_dict.get("priority", "Normal"),
                            "created_date": str(wf_dict.get("created_at", ""))[:10]
                            if wf_dict.get("created_at")
                            else "N/A",
                        }
                    )

                workflows_df = pd.DataFrame(df_data)
            else:
                workflows_df = pd.DataFrame()

            if debug_mode:
                st.write(f"**DEBUG:** Found {len(workflows_df)} workflows")

            # PRELOAD coordinator data for instant dropdown availability
            from src.utils.workflow_utils import get_available_coordinators

            coordinator_data = get_available_coordinators()
            if debug_mode:
                st.write(
                    f"**DEBUG:** Preloaded {len(coordinator_data)} coordinators for reassignment"
                )
                if len(workflows_df) > 0:
                    st.write("First workflow sample:")
                    st.write(dict(workflows[0]) if workflows else "No workflows")

        except Exception as e:
            st.error(f"Error loading workflows: {e}")
            if debug_mode:
                import traceback

                st.code(traceback.format_exc())
            workflows_df = pd.DataFrame()

        # Show results
        if workflows_df.empty:
            st.info("No active workflows available for reassignment.")
        else:
            st.success(f"Found {len(workflows_df)} workflows for reassignment")

            # Show summary
            from src.utils.workflow_utils import get_reassignment_summary

            summary = get_reassignment_summary(workflows_df)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Workflows", summary["total_workflows"])
            with col2:
                unique_coordinators = len(summary["by_coordinator"])
                st.metric("Active Coordinators", unique_coordinators)
            with col3:
                avg_steps = summary["avg_steps"]
                st.metric("Average Step", f"{avg_steps:.1f}")

            # Show reassignment table
            from src.utils.workflow_reassignment_ui import (
                show_workflow_reassignment_table,
            )

            st.subheader("📋 Workflows Available for Reassignment")
            selected_instance_ids, should_rerun = show_workflow_reassignment_table(
                workflows_df=workflows_df,
                user_id=user_id,
                table_key="admin_workflow",
                show_search_filter=True,
                debug_mode=debug_mode,
                coordinators_preloaded=coordinator_data,
            )

            if should_rerun:
                st.cache_data.clear()
                st.rerun()
