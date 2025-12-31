"""
Coordinator Tasks Module
Purpose: Provides a unified Coordinator Tasks tab view that can be used by both
Admin Dashboard and Coordinator Dashboard to ensure consistent functionality
across all dashboards.

This module includes:
1. Month selection
2. Total minutes display
3. Patient Monthly Summary (color-coded breakdown: red <40, yellow 40-89, green/blue >=90)
4. Coordinator Monthly Summary
5. Coordinator Tasks Table (editable, filterable, sortable)

Author: AI Agent
Date: December 2025
"""

import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta

from src import database
from src.core_utils import get_user_role_ids

# Role constants
ROLE_ADMIN = 34
ROLE_CARE_COORDINATOR = 36
ROLE_COORDINATOR_MANAGER = 40


def _build_coordinator_name_mapping():
    """
    Build a mapping of user_id -> full_name from the users table.
    This ensures all users appearing as coordinators have names even if the tasks table has gaps.
    Queries ALL users since coordinators in tasks table may have various roles (CC, CP, etc.)
    """
    id_to_name = {}
    try:
        # Get ALL users since coordinator_id in tasks table may reference users with any role
        conn = database.get_db_connection()
        users = conn.execute("SELECT user_id, full_name, username FROM users").fetchall()
        conn.close()
        for user in users:
            uid = user[0]
            full_name = user[1]
            username = user[2]
            if uid is not None:
                name = full_name if full_name else (username if username else "Unknown")
                id_to_name[str(int(uid))] = name
    except Exception:
        pass
    return id_to_name


def _safe_key(val):
    """Convert a value to a safe string key for mapping."""
    try:
        if pd.isna(val):
            return None
        return str(int(val))
    except Exception:
        return str(val) if val else None


def show_coordinator_tasks_tab(
    user_id: int,
    user_role_ids=None,
    show_all_coordinators: bool = False,
    filter_by_coordinator: bool = False
):
    """
    Display Coordinator Tasks tab with Patient Monthly Summary, Coordinator Monthly Summary,
    and Coordinator Tasks Table.
    
    Args:
        user_id: Current user ID
        user_role_ids: List of user role IDs
        show_all_coordinators: If True, show all coordinators' data (admin view)
        filter_by_coordinator: If True, filter by specific coordinator_id (coordinator view)
    """
    
    if user_role_ids is None:
        user_role_ids = []
    
    # Check if user has management roles (Admin or Coordinator Manager)
    has_management_role = ROLE_ADMIN in user_role_ids or ROLE_COORDINATOR_MANAGER in user_role_ids
    
    # Build coordinator name mapping from users table (always available as fallback)
    users_id_to_name = _build_coordinator_name_mapping()
    
    # --- Month Selection ---
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Get current date
        now = pd.Timestamp.now()
        current_year = int(now.year)
        current_month = int(now.month)
        
        # Get available months from coordinator_tasks tables
        conn = database.get_db_connection()
        available_tables = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'coordinator_tasks_20%'
            ORDER BY name DESC
        """).fetchall()
        conn.close()
        
        available_months = []
        for table in available_tables:
            table_name = table[0]
            try:
                # Extract year and month from table name (coordinator_tasks_YYYY_MM)
                parts = table_name.split("_")
                if len(parts) >= 3:
                    year = int(parts[2])
                    month = int(parts[3])
                    available_months.append((year, month))
            except:
                continue
        
        # Sort by year, month descending (most recent first)
        available_months.sort(reverse=True)
        
        # Create month options for selectbox
        month_options = []
        month_values = []
        for year, month in available_months:
            month_name = calendar.month_name[month]
            option_text = f"{month_name} {year}"
            month_options.append(option_text)
            month_values.append((year, month))
        
        # Default to current month if available, otherwise first available
        default_index = 0
        for i, (year, month) in enumerate(month_values):
            if year == current_year and month == current_month:
                default_index = i
                break
        
        if month_options:
            selected_month_text = st.selectbox(
                "Select Month:",
                options=month_options,
                index=default_index,
                key="coord_tasks_month_select"
            )
            selected_year, selected_month = month_values[month_options.index(selected_month_text)]
        else:
            st.warning("No coordinator tasks data available")
            selected_year, selected_month = current_year, current_month
    
    with col2:
        st.markdown(f"### Coordinator Tasks - {calendar.month_name[selected_month]} {selected_year}")
    
    # --- Coordinator Tasks: Total Minutes Selected Month Header ---
    table_name = f"coordinator_tasks_{selected_year}_{selected_month:02d}"
    conn = database.get_db_connection()
    table_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    
    if table_exists:
        total_minutes_query = f"SELECT SUM(duration_minutes) as total FROM {table_name} WHERE duration_minutes IS NOT NULL"
        total_result = conn.execute(total_minutes_query).fetchone()
        total_minutes = total_result[0] if total_result and total_result[0] else 0
        st.markdown(
            f"### Total Minutes {calendar.month_name[selected_month]} {selected_year}: **{int(total_minutes):,}**"
        )
    else:
        st.markdown(
            f"### Total Minutes {calendar.month_name[selected_month]} {selected_year}: _No data available_"
        )
    
    conn.close()
    
    # --- Patient and Coordinator Monthly Summary Tables Side-by-Side ---
    st.divider()
    col_patient, col_coord = st.columns(2)
    
    # --- Patient Monthly Summary (color-coded breakdown) ---
    with col_patient:
        st.subheader(
            f"Patient Monthly Summary ({calendar.month_name[selected_month]} {selected_year})"
        )
        try:
            if table_exists:
                conn = database.get_db_connection()
                
                # Get patient data with billing codes for selected month
                patient_query = f"""
                SELECT
                    p.patient_id,
                    (p.first_name || ' ' || p.last_name) as patient_name,
                    ct.task_type as billing_code,
                    SUM(ct.duration_minutes) as total_minutes
                FROM {table_name} ct
                JOIN patients p ON ct.patient_id = p.patient_id
                WHERE ct.duration_minutes IS NOT NULL
                GROUP BY p.patient_id, p.first_name, p.last_name, ct.task_type
                ORDER BY p.patient_id, ct.task_type
                """
                
                patient_rows = conn.execute(patient_query).fetchall()
                conn.close()
                
                if patient_rows:
                    df_patients = pd.DataFrame(
                        patient_rows,
                        columns=[
                            "patient_id",
                            "patient_name",
                            "billing_code",
                            "total_minutes",
                        ],
                    )
                    
                    # Ensure total_minutes is numeric
                    df_patients["total_minutes"] = pd.to_numeric(
                        df_patients["total_minutes"], errors="coerce"
                    ).fillna(0)
                    
                    # Create patient totals (sum across all billing codes)
                    patient_totals = (
                        df_patients.groupby(["patient_id", "patient_name"])[
                            "total_minutes"
                        ]
                        .sum()
                        .reset_index()
                    )
                    patient_totals = patient_totals.sort_values(
                        "total_minutes", ascending=True
                    )  # lowest to highest
                    patient_totals.rename(
                        columns={"total_minutes": "Sum of Minutes"}, inplace=True
                    )
                    
                    # Color coding function
                    def _color_minutes(val):
                        try:
                            v = float(val)
                        except Exception:
                            return ""
                        if v < 40:
                            return "background-color: #f94144; color: white"
                        elif v < 90:
                            return "background-color: #f9c74f; color: black"
                        elif v < 200:
                            return "background-color: #90be6d; color: black"
                        else:
                            return "background-color: #89C2E0; color: black"
                    
                    # Partition into sections
                    red_df = patient_totals[
                        patient_totals["Sum of Minutes"] < 40
                    ].copy()
                    yellow_df = patient_totals[
                        (patient_totals["Sum of Minutes"] >= 40)
                        & (patient_totals["Sum of Minutes"] < 90)
                    ].copy()
                    greenblue_df = patient_totals[
                        patient_totals["Sum of Minutes"] >= 90
                    ].copy()
                    
                    st.write("Sorted by Sum of Minutes (lowest to highest):")
                    
                    with st.expander(
                        f"Red (<40 minutes) - {len(red_df)} patients",
                        expanded=(len(red_df) > 0 and len(red_df) <= 10),
                    ):
                        if red_df.empty:
                            st.info("No patients in this category.")
                        else:
                            try:
                                styled = red_df.style.map(
                                    _color_minutes, subset=["Sum of Minutes"]
                                )
                                st.dataframe(styled, use_container_width=True)
                            except Exception:
                                st.dataframe(red_df, use_container_width=True)
                    
                    with st.expander(
                        f"Yellow (40-89 minutes) - {len(yellow_df)} patients",
                        expanded=(len(yellow_df) > 0 and len(yellow_df) <= 10),
                    ):
                        if yellow_df.empty:
                            st.info("No patients in this category.")
                        else:
                            try:
                                styled = yellow_df.style.map(
                                    _color_minutes, subset=["Sum of Minutes"]
                                )
                                st.dataframe(styled, use_container_width=True)
                            except Exception:
                                st.dataframe(yellow_df, use_container_width=True)
                    
                    with st.expander(
                        f"Green / Blue (>=90 minutes) - {len(greenblue_df)} patients",
                        expanded=(
                            len(greenblue_df) > 0 and len(greenblue_df) <= 10
                        ),
                    ):
                        if greenblue_df.empty:
                            st.info("No patients in this category.")
                        else:
                            try:
                                styled = greenblue_df.style.map(
                                    _color_minutes, subset=["Sum of Minutes"]
                                )
                                st.dataframe(styled, use_container_width=True)
                            except Exception:
                                st.dataframe(greenblue_df, use_container_width=True)
                    
                    # Add billing code breakdown section
                    st.markdown("---")
                    st.markdown("**Billing Code Breakdown:**")
                    
                    # Show detailed breakdown by billing code
                    df_billing_display = df_patients[
                        ["patient_name", "billing_code", "total_minutes"]
                    ].copy()
                    df_billing_display.rename(
                        columns={
                            "patient_name": "Patient Name",
                            "billing_code": "Billing Code",
                            "total_minutes": "Total Minutes",
                        },
                        inplace=True,
                    )
                    
                    st.dataframe(df_billing_display, use_container_width=True)
                    
                else:
                    st.info("No patient data available for this month.")
        except Exception as e:
            st.error(f"Error loading patient monthly summary: {e}")
    
    # --- Coordinator Monthly Summary ---
    with col_coord:
        st.subheader(
            f"Coordinator Monthly Summary ({calendar.month_name[selected_month]} {selected_year})"
        )
        try:
            if table_exists:
                conn = database.get_db_connection()
                
                # Get coordinator summary for selected month
                coordinator_query = f"""
                SELECT
                    ct.coordinator_id,
                    SUM(ct.duration_minutes) as total_minutes
                FROM {table_name} ct
                WHERE ct.duration_minutes IS NOT NULL
                GROUP BY ct.coordinator_id
                ORDER BY total_minutes ASC
                """
                
                coordinator_rows = conn.execute(coordinator_query).fetchall()
                
                if coordinator_rows:
                    df_summary = pd.DataFrame(
                        coordinator_rows,
                        columns=["coordinator_id", "total_minutes"],
                    )
                    
                    # Build coordinator name mapping
                    # Start with names from tasks table (where available and not empty)
                    id_to_name = {}
                    try:
                        tasks_df = pd.read_sql_query(
                            f"SELECT coordinator_id, coordinator_name FROM {table_name} WHERE coordinator_name IS NOT NULL AND coordinator_name != ''",
                            conn,
                        )
                        if not tasks_df.empty:
                            mapping = tasks_df.drop_duplicates("coordinator_id")
                            for _, row in mapping.iterrows():
                                key = _safe_key(row["coordinator_id"])
                                name = row["coordinator_name"]
                                if key and name and str(name).strip():
                                    id_to_name[key] = name
                    except Exception:
                        pass
                    
                    conn.close()
                    
                    # Always supplement from users table for any missing coordinator names
                    for coord_id, name in users_id_to_name.items():
                        if coord_id not in id_to_name:
                            id_to_name[coord_id] = name
                    
                    # Map coordinator names
                    df_summary["coord_key"] = df_summary["coordinator_id"].apply(
                        lambda x: _safe_key(x) if pd.notna(x) else None
                    )
                    df_summary["Coordinator"] = (
                        df_summary["coord_key"]
                        .map(id_to_name)
                        .fillna(df_summary["coord_key"])
                    )
                    df_summary = df_summary[["Coordinator", "total_minutes"]]
                    df_summary = df_summary.rename(
                        columns={"total_minutes": "Sum of Minutes"}
                    )
                    df_summary = df_summary.sort_values(
                        "Sum of Minutes", ascending=True
                    )
                    st.write("Sorted by Sum of Minutes (lowest to highest):")
                    st.dataframe(df_summary, use_container_width=True)
                else:
                    st.info("No coordinator summary data available for this month.")
        except Exception as e:
            st.error(f"Error loading coordinator monthly summary: {e}")
    
    st.divider()
    
    # --- Coordinator Tasks Table ---
    st.subheader(f"Coordinator Tasks Table - {calendar.month_name[selected_month]} {selected_year} (Editable, Filterable, Sortable)")
    
    try:
        conn = database.get_db_connection()
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        
        # If patient_id is present, join with patients table for patient info
        if "patient_id" in df.columns:
            try:
                patients = (
                    database.get_all_patients()
                    if hasattr(database, "get_all_patients")
                    else []
                )
                patients_df = pd.DataFrame(patients)
                required_cols = {
                    "patient_id",
                    "first_name",
                    "last_name",
                    "dob",
                }
                if not patients_df.empty and required_cols.issubset(patients_df.columns):
                    df = df.merge(
                        patients_df[
                            [
                                "patient_id",
                                "first_name",
                                "last_name",
                                "dob",
                            ]
                        ],
                        on="patient_id",
                        how="left",
                    )
                    # Move patient info columns to front
                    first_cols = [
                        col
                        for col in ["last_name", "first_name", "dob"]
                        if col in df.columns
                    ]
                    other_cols = [
                        c for c in df.columns if c not in first_cols
                    ]
                    df = df[first_cols + other_cols]
            except Exception as e:
                st.warning(f"Could not join patient info: {e}")
        
        # Build coordinator name mapping for tasks table
        # Start with names from tasks table (where available and not empty)
        id_to_name = {}
        if "coordinator_id" in df.columns and "coordinator_name" in df.columns:
            mapping = (
                df[["coordinator_id", "coordinator_name"]]
                .dropna()
                .drop_duplicates("coordinator_id")
            )
            for _, row in mapping.iterrows():
                key = _safe_key(row["coordinator_id"])
                name = row["coordinator_name"]
                if key and name and str(name).strip():
                    id_to_name[key] = name
        
        # Always supplement from users table for any missing coordinator names
        for coord_id, name in users_id_to_name.items():
            if coord_id not in id_to_name:
                id_to_name[coord_id] = name
        
        # Update coordinator_name column with resolved names
        if "coordinator_id" in df.columns:
            df["coordinator_name"] = df["coordinator_id"].apply(
                lambda x: id_to_name.get(_safe_key(x), str(x) if pd.notna(x) else None)
                if pd.notna(x)
                else None
            )
        
        # --- FILTERS ---
        filter_cols = st.columns(3)
        
        # Only show coordinator filter if we're showing all coordinators
        if show_all_coordinators:
            with filter_cols[0]:
                st.markdown("**Coordinator Name**")
                coord_names = (
                    sorted(df["coordinator_name"].dropna().unique())
                    if "coordinator_name" in df.columns
                    else []
                )
                selected_coord = st.selectbox(
                    "Filter by Coordinator",
                    ["All"] + list(coord_names),
                    key="coord_tasks_coord_filter",
                    label_visibility="collapsed",
                )
        else:
            selected_coord = "All"
        
        with filter_cols[1]:
            st.markdown("**Patient**")
            if "Patient Name" in df.columns:
                patient_display = (
                    df[["patient_id", "Patient Name"]]
                    .drop_duplicates()
                    .dropna()
                )
                patient_options = [
                    f"{row['Patient Name']} ({row['patient_id']})"
                    for _, row in patient_display.iterrows()
                ]
                patient_map = {
                    f"{row['Patient Name']} ({row['patient_id']})": row[
                        "patient_id"
                    ]
                    for _, row in patient_display.iterrows()
                }
            elif "patient_name" in df.columns:
                patient_display = (
                    df[["patient_id", "patient_name"]]
                    .drop_duplicates()
                    .dropna()
                )
                patient_options = [
                    f"{row['patient_name']} ({row['patient_id']})"
                    for _, row in patient_display.iterrows()
                ]
                patient_map = {
                    f"{row['patient_name']} ({row['patient_id']})": row[
                        "patient_id"
                    ]
                    for _, row in patient_display.iterrows()
                }
            else:
                patient_options = (
                    [
                        str(pid)
                        for pid in sorted(df["patient_id"].dropna().unique())
                    ]
                    if "patient_id" in df.columns
                    else []
                )
                patient_map = {str(pid): pid for pid in patient_options}
            
            selected_patient = st.selectbox(
                "Patient",
                ["All"] + patient_options,
                key="coord_tasks_patient_filter",
                label_visibility="collapsed",
            )
        
        with filter_cols[2]:
            st.markdown("**Status**")
            if "status" in df.columns:
                status_options = sorted(df["status"].dropna().unique())
                selected_status = st.selectbox(
                    "Filter by Status",
                    ["All"] + list(status_options),
                    key="coord_tasks_status_filter",
                    label_visibility="collapsed",
                )
            else:
                selected_status = "All"
        
        # --- Apply Filters ---
        filtered_df = df.copy()
        
        # Filter by coordinator (only if showing all coordinators)
        if show_all_coordinators and selected_coord != "All":
            filtered_df = filtered_df[
                filtered_df["coordinator_name"] == selected_coord
            ]
        
        # Filter by coordinator (if filtering by specific coordinator)
        if filter_by_coordinator and not show_all_coordinators:
            filtered_df = filtered_df[
                filtered_df["coordinator_id"] == str(user_id)
            ]
        
        # Filter by patient
        if selected_patient != "All":
            filtered_df = filtered_df[
                filtered_df["patient_id"] == patient_map[selected_patient]
            ]
        
        # Filter by status
        if selected_status != "All":
            filtered_df = filtered_df[
                filtered_df["status"] == selected_status
            ]
        
        # --- Display Tasks Table ---
        if not filtered_df.empty:
            # Only show a fixed set of columns
            preferred_order = [
                "coordinator_name",
                "status",
                "patient_id",
                "patient_name",
                "patient_full_name",
                "first_name",
                "last_name",
                "dob",
                "task_type",
                "duration_minutes",
                "date",
                "notes",
                "Patient Name",
            ]
            show_cols = [
                col
                for col in preferred_order
                if col in filtered_df.columns
            ]
            
            # Prefer patient_name/full_name, else first_name + last_name
            if "patient_name" in show_cols:
                pass
            elif "patient_full_name" in show_cols:
                pass
            elif "first_name" in show_cols and "last_name" in show_cols:
                # Combine first_name and last_name into a single column
                filtered_df["Patient Name"] = (
                    filtered_df["first_name"].fillna("")
                    + " "
                    + filtered_df["last_name"].fillna("")
                )
                show_cols.append("Patient Name")
            
            st.data_editor(
                filtered_df[show_cols],
                use_container_width=True,
                num_rows="dynamic",
                height=700,
                key="coordinator_tasks_table_editor",
            )
        else:
            st.info(f"No data in table {table_name} after filtering.")
    
    except Exception as e:
        st.error(f"Error loading coordinator tasks: {e}")
