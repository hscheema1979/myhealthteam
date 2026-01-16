import os
import sys

# Ensure the project root (parent of 'src') is in sys.path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import calendar
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from src import database
from src.config.ui_style_config import (
    SectionTitles,
    TextStyle,
    get_metric_label,
    get_section_title,
)
from src.dashboards.phone_review import show_phone_review_entry
from src.dashboards.provider_monthly_task_review import show as show_monthly_task_review


def _has_admin_role(user_id):
    """Check if user has admin role (role_id 34) for edit permissions"""
    try:
        user_roles = database.get_user_roles_by_user_id(user_id)
        user_role_ids = [r["role_id"] for r in user_roles]
        return 34 in user_role_ids
    except Exception:
        return False


def render_provider_help_examples(key_prefix: str = ""):
    st.markdown("### Interactive Examples (Live Streamlit widgets, read-only)")

    # My Patients panel example (Annotated, side-by-side)
    st.subheader("My Patients — Panel Example (Annotated)")
    left, right = st.columns([2, 1])
    with left:
        sample_df = pd.DataFrame(
            [
                {
                    "Status": "Active",
                    "GOC": "Rev/Confirm",
                    "Code Status": "Full Code",
                    "First Name": "Ada",
                    "Last Name": "Lopez",
                    "Facility": "Autumn Ridge",
                    "Assigned Coordinator": "Sarah Johnson",
                    "Last Visit Date": "2025-10-28",
                    "Service Type": "PCP",
                    "Phone Number": "(555) 222-0102",
                },
                {
                    "Status": "Gap >60d",
                    "GOC": "Discuss",
                    "Code Status": "DNR",
                    "First Name": "Ben",
                    "Last Name": "Kim",
                    "Facility": "Summit Care",
                    "Assigned Coordinator": "Alex Rivera",
                    "Last Visit Date": "2025-09-01",
                    "Service Type": "PCP",
                    "Phone Number": "(555) 333-0145",
                },
            ]
        )

        # Style rows by Last Visit Date recency to match color legend
        def _row_bg_color(date_str: str) -> str:
            try:
                d = pd.to_datetime(date_str).date()
                days = (datetime.today().date() - d).days
                if days <= 30:
                    return "#d4edda"  # green-ish
                elif days <= 60:
                    return "#fff3cd"  # yellow-ish
                else:
                    return "#f8d7da"  # red-ish
            except Exception:
                return "#ffffff"

        def _style_row(row):
            color = _row_bg_color(row.get("Last Visit Date", ""))
            return [f"background-color: {color}"] * len(row)

        styled = sample_df.style.apply(_style_row, axis=1)
        st.dataframe(styled, use_container_width=True)
    with right:
        st.markdown("- Status: current engagement or gaps.")
        st.markdown("- GOC: Goals of Care status (Rev/Confirm/Discuss).")
        st.markdown("- Code Status: resuscitation preference (e.g., Full, DNR).")
        st.markdown("- Facility: where the patient resides.")
        st.markdown("- Assigned Coordinator: point of contact.")
        st.markdown("- Last Visit Date: recency drives color (green/yellow/red).")
        st.markdown("- Service Type: e.g., PCP.")
        st.markdown("- Phone Number: primary contact.")
        st.caption(
            "Row background colors: Green ≤30d, Yellow 31–60d, Red ≥61d since last visit. Blue badges appear in monthly minutes summaries (≥200 min)."
        )

    # Onboarding Queue example (Initial TV) — annotated
    st.subheader("Onboarding Queue — Initial TV Visit (Annotated)")
    left, right = st.columns([2, 1])
    with left:
        st.selectbox(
            "Visit Type",
            ["Home Visit", "Telehealth Visit"],
            index=0,
            disabled=True,
            key=f"{key_prefix}help_visit_type",
        )
        st.date_input(
            "Date",
            value=pd.to_datetime("today").date(),
            disabled=True,
            key=f"{key_prefix}help_onboarding_date",
        )
        st.text_area(
            "Visit Notes",
            placeholder="Document visit details, response, concerns...",
            disabled=True,
            key=f"{key_prefix}help_visit_notes",
        )
        st.multiselect(
            "Mental Health Concerns",
            ["Anxiety", "Depression", "PTSD", "Substance Use"],
            default=["Anxiety"],
            disabled=True,
            key=f"{key_prefix}help_mental_health_concerns",
        )
        st.selectbox(
            "Code Status",
            ["Full Code", "DNR"],
            index=0,
            disabled=True,
            key=f"{key_prefix}help_code_status",
        )
        st.selectbox(
            "Cognitive Function",
            ["Intact", "Mild Impairment", "Moderate", "Severe"],
            index=0,
            disabled=True,
            key=f"{key_prefix}help_cognitive_function",
        )
        st.selectbox(
            "Functional Status",
            ["Independent", "Needs Assistance", "Dependent"],
            index=0,
            disabled=True,
            key=f"{key_prefix}help_functional_status",
        )
        st.selectbox(
            "GOC", ["Rev/Confirm", "Discuss"], index=0, disabled=True, key=f"{key_prefix}help_goc"
        )
        st.text_area(
            "Goals of Care", placeholder="Patient-centered goals...", disabled=True, key=f"{key_prefix}help_goals_of_care"
        )
        st.text_area(
            "Active Concerns", placeholder="Primary issues to address...", disabled=True, key=f"{key_prefix}help_active_concerns"
        )
        st.text_area(
            "Active Specialists",
            placeholder="Cardiology, Endocrinology, etc.",
            disabled=True,
            key=f"{key_prefix}help_active_specialists",
        )
        st.button("Complete Initial Visit (disabled)", disabled=True, key=f"{key_prefix}help_complete_visit")
    with right:
        st.markdown("- Visit Type: Home vs Telehealth visit.")
        st.markdown("- Date: when the initial visit occurred.")
        st.markdown("- Visit Notes: summary of assessment and plan.")
        st.markdown(
            "- ER Visits/Hospitalizations (12 mo): captured in clinical section during intake."
        )
        st.markdown("- Subjective Risk Level: provider's risk impression.")
        st.markdown("- Mental Health Concerns: multi-select conditions.")
        st.markdown("- Code Status/Cognitive/Functional: baseline profile.")
        st.markdown("- GOC & Goals of Care: current status and narrative.")
        st.markdown("- Active Concerns/Specialists: context for care coordination.")
        st.caption(
            "Completing the initial TV updates onboarding and patient records and removes patient from the queue."
        )

    # Phone Reviews — annotated entry
    st.subheader("Phone Reviews — Entry Form (Annotated)")
    left, right = st.columns([2, 1])
    with left:
        st.selectbox(
            "Task Type",
            ["Phone Review", "Follow-up Call"],
            index=0,
            disabled=True,
            key=f"{key_prefix}help_task_type",
        )
        st.date_input(
            "Date",
            pd.to_datetime("today").date(),
            disabled=True,
            key=f"{key_prefix}help_phone_review_date",
        )
        st.text_area(
            "Notes",
            placeholder="Call summary, clinical updates, next steps...",
            disabled=True,
            key=f"{key_prefix}help_phone_notes",
        )
        st.button("Log Task (disabled)", disabled=True, key=f"{key_prefix}help_log_task")
    with right:
        st.markdown("- Task Type: choose appropriate call/review type.")
        st.markdown("- Date: when the call took place.")
        st.markdown("- Notes: key updates and future actions.")
        st.markdown("- Validation: required fields enforced in live form.")
        st.markdown("- Persistence: saved to provider_tasks for reporting.")

    # Task Review — annotated summary
    st.subheader("Task Review — Summary (Annotated)")
    left, right = st.columns([2, 1])
    with left:
        df = pd.DataFrame(
            [
                {
                    "Task": "PCP-Visit Home Visit (HV)",
                    "Date": "2025-11-10",
                    "Minutes": 45,
                    "Status": "Completed",
                    "Notes": "Initial HV completed",
                },
                {
                    "Task": "Phone Review",
                    "Date": "2025-11-18",
                    "Minutes": 15,
                    "Status": "Queued",
                    "Notes": "Call scheduled",
                },
            ]
        )
        st.dataframe(df, use_container_width=True)
        st.date_input(
            "Filter: Date Range (disabled)",
            value=pd.to_datetime("today").date(),
            disabled=True,
            key=f"{key_prefix}help_task_review_date",
        )
        st.multiselect(
            "Filter: Task (disabled)",
            ["Phone Review", "PCP-Visit Home Visit (HV)"],
            default=["Phone Review"],
            disabled=True,
            key=f"{key_prefix}help_filter_task",
        )
        st.selectbox(
            "Filter: Status (disabled)",
            ["Queued", "Completed"],
            index=0,
            disabled=True,
            key=f"{key_prefix}help_filter_status",
        )
        st.button("Export CSV (disabled)", disabled=True, key=f"{key_prefix}help_export_csv")
    with right:
        st.markdown("- Columns: Task, Date, Minutes, Status, Notes.")
        st.markdown("- Filters: date/task/status to focus on subsets.")
        st.markdown("- Export: download CSV for further analysis.")


def show(user_id, user_role_ids=None):
    if user_role_ids is None:
        user_role_ids = []

    # Check if user has Care Provider Manager role (role_id 38)
    has_cpm_role = 38 in user_role_ids

    st.title("Care Provider Dashboard")

    # Check for onboarding queue for all care providers
    onboarding_queue = database.get_provider_onboarding_queue(user_id)

    if has_cpm_role:
        
        # Create tabs with management functionality for CPM
        if onboarding_queue and len(onboarding_queue) > 0:
            tab1, tab2, tab3, tab4, tab5, tab6, tab_zmo, tab_help = st.tabs(
                [
                    "My Patients",
                    "Team Management",
                    "Onboarding Queue & Initial TV Visits",
                    "Phone Reviews",
                    "Task Review",
                    "Daily Task Log",
                    "ZMO (Patient Data)",
                    "Help",
                ]
            )

            with tab1:
                show_patient_list_section(
                    user_id,
                    section_id="cpm_patients_with_queue",
                    has_cpm_role=has_cpm_role,
                )

            with tab2:
                show_team_management_section()

            with tab3:
                show_provider_onboarding_queue(user_id, onboarding_queue)

            with tab4:
                show_phone_review_entry(mode="cp", user_id=user_id)

            with tab5:
                show_monthly_task_review(user_id)

            with tab6:
                show_daily_task_log(user_id, "provider")

            with tab_zmo:
                from src.zmo_module import render_zmo_tab
                render_zmo_tab(user_id=user_id)
            with tab_help:
                st.header("Help")
                st.markdown(
                    "This help uses real UI elements to explain what you see and how to act."
                )
                st.subheader("Color Legend (Patient Activity)")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.success("Green: Seen in the last 30 days")
                with col2:
                    st.warning("Yellow: Seen 1–2 months ago")
                with col3:
                    st.error("Red: NOT seen in 2+ months")
                with col4:
                    st.info("Blue: ≥200 minutes this month")
                st.caption(
                    "These colors appear in summaries and expanders to help triage quickly."
                )

                st.subheader("My Patients")
                st.markdown(
                    "- Filter and act on your assigned patients.\n- Common actions: Open Chart, Call Patient, Add Task."
                )
                st.markdown(
                    "- Columns: Status, GOC, Code Status, Risk, First Name, Last Name, Med POC, Appt POC, Med Phone, Appt Phone, Facility, CP Name, CC Name, Last Visit Date, Service Type, Phone Number"
                )

                st.subheader("Onboarding Queue & Initial TV")
                st.markdown("- Fields: Visit Type, Date, Visit Notes")
                st.markdown(
                    "- Clinical fields: ER Visits (12 mo), Hospitalizations (12 mo), Subjective Risk Level, Mental Health Concerns (checkboxes), Code Status, Cognitive Function, Functional Status, GOC, Goals of Care, Active Concerns, Active Specialists"
                )
                st.markdown(
                    "- Action: Complete Initial Visit — updates onboarding and patient records"
                )

                st.subheader("Phone Reviews")
                st.markdown(
                    "- Fields: Task Type, Date, Notes; validates required fields; saves to provider_tasks"
                )

                st.subheader("Task Review")
                st.markdown(
                    "- Monthly view only: edit Duration (minutes) for tasks"
                )
                st.markdown(
                    "- Columns: Patient Name, Date, Duration, Service Type; CSV export"
                )
                render_provider_help_examples(key_prefix="cpm_queue_")
        else:
            tab1, tab2, tab3, tab4, tab_zmo, tab_help = st.tabs(
                [
                    "My Patients",
                    "Team Management",
                    "Phone Reviews",
                    "Task Review",
                    "ZMO (Patient Data)",
                    "Help",
                ]
            )

            with tab1:
                show_patient_list_section(user_id, section_id="cpm_patients_no_queue")

            with tab2:
                show_team_management_section()

            with tab3:
                show_phone_review_entry(mode="cp", user_id=user_id)

            with tab4:
                show_monthly_task_review(user_id)
            with tab_zmo:
                from src.zmo_module import render_zmo_tab
                render_zmo_tab(user_id=user_id)
            with tab_help:
                st.header("Help")
                st.subheader("Color Legend (Patient Activity)")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.success("Green: Seen in the last 30 days")
                with col2:
                    st.warning("Yellow: Seen 1–2 months ago")
                with col3:
                    st.error("Red: NOT seen in 2+ months")
                with col4:
                    st.info("Blue: ≥200 minutes this month")
                st.subheader("Sections")
                st.markdown("- My Patients: act on your panel.")
                st.markdown(
                    "  • Columns: Status, GOC, Code Status, Risk, First Name, Last Name, Med POC, Appt POC, Med Phone, Appt Phone, Facility, Provider, Coordinator, Last Visit Date, Service Type, Phone Number"
                )
                st.markdown("- Onboarding Queue: initial TV visit tasks.")
                st.markdown(
                    "  • Fields: Visit Type, Date, Visit Notes; Clinical: ER Visits, Hospitalizations, Subjective Risk, MH Concerns, Code Status, Cognitive, Functional, GOC, Goals of Care, Active Concerns, Specialists"
                )
                st.markdown("- Phone Reviews: structured entry forms.")
                st.markdown(
                    "  • Fields: Task Type, Date, Notes; validation and save to provider_tasks"
                )
                st.markdown("- Task Review: monthly view with minutes editing.")
                st.markdown(
                    "  • Columns: Patient Name, Date, Duration, Service Type; CSV export"
                )
                render_provider_help_examples(key_prefix="cpm_noqueue_")
            with tab_help:
                st.header("Help")
                st.subheader("Color Legend (Patient Activity)")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.success("Green: Seen in the last 30 days")
                with col2:
                    st.warning("Yellow: Seen 1–2 months ago")
                with col3:
                    st.error("Red: NOT seen in 2+ months")
                with col4:
                    st.info("Blue: ≥200 minutes this month")
                st.subheader("Sections")
                st.markdown("- My Patients: act on your panel.")
                st.markdown(
                    "  • Columns: Status, GOC, Code Status, Risk, First Name, Last Name, Med POC, Appt POC, Med Phone, Appt Phone, Facility, Provider, Coordinator, Last Visit Date, Service Type, Phone Number"
                )
                st.markdown("- Phone Reviews: structured entry forms.")
                st.markdown(
                    "  • Fields: Task Type, Date, Notes; validation and save to provider_tasks"
                )
                st.markdown("- Task Review: monthly view with minutes editing.")
                st.markdown(
                    "  • Columns: Patient Name, Date, Duration, Service Type; CSV export"
                )
                render_provider_help_examples(key_prefix="cp_noqueue_")
    else:
        # Regular care provider tabs - include onboarding queue if they have assigned patients
        if onboarding_queue and len(onboarding_queue) > 0:
            tab1, tab2, tab3, tab4, tab_zmo, tab_help = st.tabs(
                [
                    "My Patients",
                    "Onboarding Queue & Initial TV Visits",
                    "Phone Reviews",
                    "Task Review",
                    "ZMO (Patient Data)",
                    "Help",
                ]
            )

            with tab1:
                show_patient_list_section(
                    user_id,
                    section_id="cp_patients_with_queue",
                    has_cpm_role=has_cpm_role,
                )

            with tab2:
                show_provider_onboarding_queue(user_id, onboarding_queue)

            with tab3:
                show_phone_review_entry(mode="cp", user_id=user_id)

            with tab4:
                show_monthly_task_review(user_id)
            with tab_zmo:
                from src.zmo_module import render_zmo_tab
                render_zmo_tab(user_id=user_id)
            with tab_help:
                st.header("Help")
                st.markdown(
                    "This help uses real UI elements to explain what you see and how to act."
                )
                st.subheader("Color Legend (Patient Activity)")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.success("Green: Seen in the last 30 days")
                with col2:
                    st.warning("Yellow: Seen 1–2 months ago")
                with col3:
                    st.error("Red: NOT seen in 2+ months")
                with col4:
                    st.info("Blue: ≥200 minutes this month")
                st.caption(
                    "These colors appear in summaries and expanders to help triage quickly."
                )

                st.subheader("My Patients")
                st.markdown(
                    "- Filter and act on your assigned patients.\n- Common actions: Open Chart, Call Patient, Add Task."
                )
                st.markdown(
                    "- Columns: Status, GOC, Code Status, Risk, First Name, Last Name, Med POC, Appt POC, Med Phone, Appt Phone, Facility, Provider, Coordinator, Last Visit Date, Service Type, Phone Number"
                )

                st.subheader("Onboarding Queue & Initial TV")
                st.markdown(
                    "- Patients assigned for initial visits. Completing the visit updates onboarding and patient records."
                )
                st.markdown("- Fields: Visit Type, Date, Visit Notes")
                st.markdown(
                    "- Clinical fields: ER Visits (12 mo), Hospitalizations (12 mo), Subjective Risk Level, Mental Health Concerns (checkboxes), Code Status, Cognitive Function, Functional Status, GOC, Goals of Care, Active Concerns, Active Specialists"
                )
                st.markdown(
                    "- Action: Complete Initial Visit — updates onboarding and patient records"
                )

                st.subheader("Phone Reviews")
                st.markdown(
                    "- Fields: Task Type, Date, Notes; validates required fields; saves to provider_tasks"
                )

                st.subheader("Task Review")
                st.markdown(
                    "- Monthly view only: edit Duration (minutes) for tasks"
                )
                st.markdown(
                    "- Columns: Patient Name, Date, Duration, Service Type; CSV export"
                )
                render_provider_help_examples(key_prefix="cp_queue_")
        else:
            tab1, tab2, tab3, tab_zmo, tab_help = st.tabs(
                ["My Patients", "Phone Reviews", "Task Review", "ZMO (Patient Data)", "Help"]
            )

            with tab1:
                show_patient_list_section(
                    user_id, section_id="cp_patients", has_cpm_role=has_cpm_role
                )

            with tab2:
                show_phone_review_entry(mode="cp", user_id=user_id)

            with tab3:
                show_monthly_task_review(user_id)
            with tab_zmo:
                from src.zmo_module import render_zmo_tab
                render_zmo_tab(user_id=user_id)
            with tab_help:
                st.header("Help")
                st.subheader("Color Legend (Patient Activity)")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.success("Green: Seen in the last 30 days")
                with col2:
                    st.warning("Yellow: Seen 1–2 months ago")
                with col3:
                    st.error("Red: NOT seen in 2+ months")
                with col4:
                    st.info("Blue: ≥200 minutes this month")
                st.subheader("Sections")
                st.markdown(
                    "- My Patients: act on your panel.\n- Phone Reviews: structured entry forms.\n- Task Review: monthly view with minutes editing."
                )


def show_patient_list_section(user_id, section_id=None, has_cpm_role=False):
    # Get all providers and coordinators for filtering capabilities
    try:
        all_providers = database.get_users_by_role(33)  # 33 = Care Provider
        all_coordinators = database.get_users_by_role(36)  # 36 = Care Coordinator
    except Exception as e:
        st.error(f"Error fetching user data: {e}")
        all_providers = []
        all_coordinators = []

    # Get all patient data (like admin dashboard shows all workflows, provider dashboard should show all patients)
    try:
        patient_data_list = database.get_all_patient_panel()
    except Exception as e:
        st.error(f"Error fetching patient data: {e}")
        patient_data_list = []

    # --- Add Search and Filter UI at the top ---
    st.markdown("#### Search and Filter Patients")

    # Create filter columns
    col_search, col_filter = st.columns([2, 1])

    with col_search:
        search_query = st.text_input(
            "Search by patient name or ID",
            key="provider_patient_search",
            placeholder="Enter patient name or ID...",
        )

    with col_filter:
        # Get all providers for the filter dropdown
        provider_options = ["All Providers"]
        for provider in all_providers:
            provider_name = (
                f"{provider.get('full_name', provider.get('username', 'Unknown'))}"
            )
            provider_options.append(provider_name)
        provider_options.append("Unassigned")

        # Default to showing only the logged-in provider's patients (like other dashboards)
        current_user_name = None
        current_provider_id = None
        try:
            current_user = database.get_user_by_id(user_id)
            if current_user:
                # Handle sqlite3.Row object by accessing directly like a dictionary
                try:
                    full_name = current_user["full_name"]
                    username = current_user["username"]
                    current_provider_id = current_user["user_id"]
                except (KeyError, TypeError):
                    # Fallback if direct access fails
                    full_name = None
                    username = None
                    current_provider_id = None

                current_user_name = (
                    full_name if full_name else username if username else "Unknown User"
                )
        except Exception:
            pass

        # Add "All Providers" option for admin/managers who need to see everyone
        provider_options = ["All Providers"] + [
            opt for opt in provider_options if opt != "All Providers"
        ]

        # Set default selection - current user's patients only
        default_selection = (
            [current_user_name]
            if current_user_name and current_user_name in provider_options
            else ["All Providers"]
        )

        selected_providers = st.multiselect(
            "Filter by Provider(s)",
            provider_options,
            key="provider_filter",
            default=default_selection,
            help="Select one or more providers to view their patients. Default shows your patients.",
        )

    # Initialize provider map for filtering
    provider_map = {}
    for provider in all_providers:
        provider_name = (
            f"{provider.get('full_name', provider.get('username', 'Unknown'))}"
        )
        provider_id = provider.get("user_id")
        provider_map[provider_name] = provider_id
    provider_map["Unassigned"] = 0

    # Apply filtering
    filtered_patients = patient_data_list

    # Filter by search query
    if search_query.strip():
        q = search_query.lower().strip()
        filtered_patients = [
            p
            for p in filtered_patients
            if (
                q in str(p.get("patient_id", "")).lower()
                or q in f"{p.get('first_name', '')} {p.get('last_name', '')}".lower()
            )
        ]

    # Filter by provider(s)
    if selected_providers and "All Providers" not in selected_providers:
        selected_provider_ids = []
        show_unassigned = "Unassigned" in selected_providers

        for provider_name in selected_providers:
            if provider_name != "Unassigned":
                provider_id = provider_map.get(provider_name)
                if provider_id is not None:
                    selected_provider_ids.append(int(provider_id))

        # Enforce CPM role restrictions
        if not has_cpm_role and "All Providers" not in selected_providers:
            current_user_provider_id = (
                int(current_provider_id) if current_provider_id else None
            )
            if (
                current_user_provider_id
                and current_user_provider_id not in selected_provider_ids
            ):
                selected_provider_ids = [current_user_provider_id]

        # Apply provider filter
        if selected_provider_ids or show_unassigned:
            filtered_by_provider = []
            for p in filtered_patients:
                pid = (
                    int(p.get("provider_id", 0))
                    if p.get("provider_id") not in [None, "UNASSIGNED"]
                    else 0
                )
                if pd.isna(pid):
                    pid = 0

                # Match if assigned provider is selected, or show unassigned if selected
                if (pid > 0 and pid in selected_provider_ids) or (
                    show_unassigned and pid == 0
                ):
                    filtered_by_provider.append(p)

            filtered_patients = filtered_by_provider

    # Use filtered results
    patient_data_list = filtered_patients

    # --- Map facility_id to facility_name using modular utility ---
    from src.core_utils import get_facility_id_to_name_map, map_facility_id_to_name

    facility_id_to_name = get_facility_id_to_name_map(database)
    unmapped_facilities = set()
    for p in patient_data_list:
        fid = p.get("current_facility_id")
        facility_name = map_facility_id_to_name(fid, facility_id_to_name)
        # Fallback: if no id or not mapped, try the text field
        if not facility_name:
            fallback_name = p.get("facility")
            if fallback_name and fallback_name not in facility_id_to_name.values():
                unmapped_facilities.add(fallback_name)
            facility_name = fallback_name or "Unknown"
        p["facility"] = facility_name
    if unmapped_facilities:
        st.warning(
            f"Unmapped facilities found in patient data: {sorted(unmapped_facilities)}"
        )

    # Only show patients with status in Active, Active-Geri, Active-PCP, Hospice
    allowed_statuses = ["Active", "Active-Geri", "Active-PCP", "Hospice"]
    # filtered_patients = [p for p in patient_data_list if (p.get('status', '') or '').strip() in allowed_statuses]
    filtered_patients = patient_data_list

    # Metrics for active patient counts (show only once, no dropdown)
    total_active = len(
        [
            p
            for p in patient_data_list
            if (p.get("status", "") or "").strip() in allowed_statuses
        ]
    )
    count_geri = len(
        [
            p
            for p in patient_data_list
            if (p.get("status", "") or "").strip() == "Active-Geri"
        ]
    )
    count_pcp = len(
        [
            p
            for p in patient_data_list
            if (p.get("status", "") or "").strip() == "Active-PCP"
        ]
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("All Active Patients", total_active)
    col2.metric("Active-Geri Patients", count_geri)
    col3.metric("Active-PCP Patients", count_pcp)


    st.divider()
    st.subheader("Patients")
    st.divider()

    if filtered_patients:
        try:
            # Define required columns and display names in requested order
            required_columns = [
                ("status", "Status"),
                ("goc_value", "GOC"),
                ("code_status", "Code Status"),
                ("subjective_risk_level", "Risk"),
                ("first_name", "First Name"),
                ("last_name", "Last Name"),
                ("medical_contact_name", "Med POC"),
                ("appointment_contact_name", "Appt POC"),
                ("medical_contact_phone", "Med Phone"),
                ("appointment_contact_phone", "Appt Phone"),
                ("facility", "Facility"),
                ("care_provider_name", "Provider"),
                ("care_coordinator_name", "Coordinator"),
                ("last_visit_date", "Last Visit Date"),
                ("service_type", "Service Type"),
                ("phone_primary", "Phone Number"),
            ]
            patients_df = pd.DataFrame(filtered_patients)
            # Ensure all required columns are present and sourced from patient_data_list
            for col, _ in required_columns:
                if col not in patients_df.columns:
                    patients_df[col] = None
            display_columns = [col for col, _ in required_columns]
            column_names = [name for _, name in required_columns]

            # Standardize last_visit_date format for display and logic
            display_df = patients_df[display_columns].copy()
            display_df.columns = column_names
            if "Last Visit Date" in display_df.columns:
                display_df["Last Visit Date"] = display_df["Last Visit Date"].apply(
                    lambda x: pd.to_datetime(x, errors="coerce").strftime("%m-%d-%Y")
                    if pd.notnull(pd.to_datetime(x, errors="coerce"))
                    else None
                )

            def color_patient_name(row):
                color = ""
                last_visit = row["Last Visit Date"]
                today = datetime.now().date()
                if last_visit:
                    try:
                        last_visit_dt = pd.to_datetime(
                            last_visit, errors="coerce"
                        ).date()
                        delta = (today - last_visit_dt).days
                        if delta > 60:
                            color = "background-color: #ffcccc; color: #a00;"  # red
                        elif 30 < delta <= 60:
                            color = (
                                "background-color: #fff3cd; color: #a67c00;"  # yellow
                            )
                        elif 0 <= delta <= 30:
                            color = (
                                "background-color: #d4edda; color: #155724;"  # green
                            )
                    except Exception:
                        pass
                return color

            def style_patient_names(df):
                return df.style.apply(
                    lambda row: [
                        color_patient_name(row)
                        if col in ["First Name", "Last Name"]
                        else ""
                        for col in df.columns
                    ],
                    axis=1,
                )

            # Display patient data with conditional formatting
            try:
                # Try to display with styling first
                st.dataframe(
                    style_patient_names(display_df),
                    height=400,
                    use_container_width=True,
                    column_config={
                        "Status": st.column_config.TextColumn("Status", width=None),
                        "GOC": st.column_config.TextColumn("GOC", width=None),
                        "Code Status": st.column_config.TextColumn(
                            "Code Status", width=None
                        ),
                        "First Name": st.column_config.TextColumn(
                            "First Name", width=None
                        ),
                        "Last Name": st.column_config.TextColumn(
                            "Last Name", width=None
                        ),
                        "Facility": st.column_config.TextColumn("Facility", width=None),
                        "Assigned Coordinator": st.column_config.TextColumn(
                            "Assigned Coordinator", width=None
                        ),
                        "Last Visit Date": st.column_config.DateColumn(
                            "Last Visit Date", width=None
                        ),
                        "Service Type": st.column_config.TextColumn(
                            "Service Type", width=None
                        ),
                        "Phone Number": st.column_config.TextColumn(
                            "Phone Number", width=None
                        ),
                    },
                    hide_index=True,
                )
            except Exception as styling_error:
                # If styling fails due to compatibility issues, fall back to plain display
                st.warning(
                    "⚠️ Color mapping temporarily unavailable due to styling compatibility. Displaying plain table."
                )
                st.dataframe(
                    display_df,
                    height=400,
                    use_container_width=True,
                    column_config={
                        "Status": st.column_config.TextColumn("Status", width=None),
                        "GOC": st.column_config.TextColumn("GOC", width=None),
                        "Code Status": st.column_config.TextColumn(
                            "Code Status", width=None
                        ),
                        "First Name": st.column_config.TextColumn(
                            "First Name", width=None
                        ),
                        "Last Name": st.column_config.TextColumn(
                            "Last Name", width=None
                        ),
                        "Facility": st.column_config.TextColumn("Facility", width=None),
                        "Assigned Coordinator": st.column_config.TextColumn(
                            "Assigned Coordinator", width=None
                        ),
                        "Last Visit Date": st.column_config.DateColumn(
                            "Last Visit Date", width=None
                        ),
                        "Service Type": st.column_config.TextColumn(
                            "Service Type", width=None
                        ),
                        "Phone Number": st.column_config.TextColumn(
                            "Phone Number", width=None
                        ),
                    },
                    hide_index=True,
                )

            # Validation code removed for production

            # Duplicate patient selector removed to avoid two selection widgets.
            # The single patient selector used for task logging is the one in the 'Daily Task Entry' section below.

        except Exception as e:
            st.error(f"Error processing patient data: {e}")
            # Fallback to simple dataframe
            st.dataframe(
                display_df,
                height=400,
                use_container_width=True,
                column_config={
                    "First Name": st.column_config.TextColumn(
                        "First Name", width="medium"
                    ),
                    "Last Name": st.column_config.TextColumn(
                        "Last Name", width="medium"
                    ),
                    "DOB": st.column_config.DateColumn("DOB", width="small"),
                    "Gender": st.column_config.TextColumn("Gender", width="small"),
                    "Phone": st.column_config.TextColumn("Phone", width="medium"),
                    # Email column removed per request
                    "City": st.column_config.TextColumn("City", width="medium"),
                    "State": st.column_config.TextColumn("State", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                },
                hide_index=True,
            )
    else:
        st.info("No patients match the selected filters.")

    st.subheader("Visit Task Entry")

    # Fetch task billing codes for the task dropdown - filtered by Primary Care Visit
    task_billing_codes = database.get_tasks_billing_codes_by_service_type(
        "Primary Care Visit"
    )
    unique_task_descriptions = list(
        set(task["task_description"] for task in task_billing_codes)
    )
    task_options = sorted(unique_task_descriptions)

    # Build patient list for selection
    # Sort filtered_patients by last_name, then first_name
    filtered_patients = sorted(
        filtered_patients,
        key=lambda p: (
            str(p.get("last_name", "")).lower(),
            str(p.get("first_name", "")).lower(),
        ),
    )
    patient_names = [
        f"{p.get('first_name','').strip()} {p.get('last_name','').strip()}".strip()
        for p in filtered_patients
        if p.get("first_name") and p.get("last_name")
    ]
    patient_map = {
        f"{p.get('first_name','').strip()} {p.get('last_name','').strip()}": p
        for p in filtered_patients
        if p.get("first_name") and p.get("last_name")
    }

    if not patient_names:
        st.info("No patients available to log tasks for.")
        key_prefix = f"single_task_{user_id}_{section_id or 'main'}"  # Still set, but widgets won't be rendered
    else:
        # Single, compact form for one task at a time
        key_prefix = f"single_task_{user_id}_{section_id or 'main'}"

        # Initialize patient type in session state for dynamic location options
        if f"{key_prefix}_patient_type" not in st.session_state:
            st.session_state[f"{key_prefix}_patient_type"] = "Follow Up"

        # All fields in one row: Date | Patient | Patient Type | Location
        col_date, col_patient, col_type, col_location = st.columns([0.7, 3, 1.2, 1])

        with col_date:
            task_date = st.date_input(
                "DOS",
                value=pd.to_datetime("today"),
                key=f"{key_prefix}_date",
            )

        with col_patient:
            patient_options = ["Select one"] + patient_names
            selected_patient_name = st.selectbox(
                "Patient", patient_options, key=f"{key_prefix}_patient"
            )

        with col_type:
            patient_type_options = ["Select one", "Follow Up", "New", "Acute", "Cognitive", "TCM-7", "TCM-14"]
            selected_patient_type = st.selectbox(
                "Type",
                patient_type_options,
                index=1,  # Default to "Follow Up"
                key=f"{key_prefix}_patient_type",
            )

        with col_location:
            current_patient_type = selected_patient_type
            if current_patient_type == "Acute":
                location_options = ["Select one", "Tele", "Office"]
            else:
                location_options = ["Select one", "Home", "Tele", "Office"]

            task_location = st.selectbox(
                "Location",
                location_options,
                index=0,
                key=f"{key_prefix}_location",
            )
            task_location_val = (
                None if (task_location == "Select one") else task_location
            )

        # Billing code display (hidden, used for form submission)
        selected_billing_code = None
        selected_billing_desc = ""

        # Determine base patient type for billing lookup
        patient_type_for_billing = (
            selected_patient_type if selected_patient_type != "Select one"
            else "New"
        )

        # Map UI location to database location type
        location_map = {
            "Home": "Home",
            "Tele": "Telehealth",
            "Office": "Office"
        }
        db_location_type = location_map.get(task_location_val)

        # Look up billing code from database
        billing_options = database.get_billing_codes(
            service_type=patient_type_for_billing,
            location_type=db_location_type,
            patient_type=patient_type_for_billing,
        )

        if billing_options:
            selected_billing_code = billing_options[0].get("billing_code", "Unknown")
            selected_billing_desc = billing_options[0].get("description", "")
        else:
            # TCM specific fallbacks if lookup fails (should not happen if DB is correct)
            if selected_patient_type == "TCM-7":
                selected_billing_code = "99496"
                selected_billing_desc = "TCM 7-day"
            elif selected_patient_type == "TCM-14":
                selected_billing_code = "99495"
                selected_billing_desc = "TCM 14-day"
            else:
                selected_billing_code = None

        # Store the selected billing code (invisible to provider)
        if selected_billing_code:
            selected_billing = selected_billing_code
        else:
            selected_billing = None
            st.warning(
                f"No billing codes configured for Patient Type: '{patient_type_for_billing}' with Location: '{db_location_type}' - please contact admin"
            )

        st.markdown("#### Patient Risk & Clinical Fields (Optional)")
        col1, col2 = st.columns(2)
        with col1:
            er_visits_6mo = st.number_input(
                "ER Visits (last 12 months)", min_value=0, step=1, key="er_visits_6mo"
            )
            hospitalizations_6mo = st.number_input(
                "Hospitalizations (last 12 months)",
                min_value=0,
                step=1,
                key="hospitalizations_6mo",
            )
            subjective_risk = st.selectbox(
                "Subjective Risk Level",
                [
                    "Select one",
                    "Level 6 - in danger of dying or institutionalized within 1 yr",
                    "Level 5 - complications of chronic conditions or high risk social determinants of health",
                    "Level 4 - unstable chronic conditions but no complications",
                    "Level 3 - stable chronic conditions",
                    "Level 2 - healthy, some out of range biometrics",
                    "Level 1 - healthy, in range biometrics",
                ],
                index=0,
                key="subjective_risk",
            )
            provider_mh_concerns = st.checkbox(
                "Provider: Mental Health Concerns", key="provider_mh_concerns"
            )
            provider_mh_fields = [
                ("provider_mh_schizophrenia", "Schizophrenia"),
                ("provider_mh_depression", "Depression"),
                ("provider_mh_anxiety", "Anxiety"),
                ("provider_mh_stress", "Stress/PTSD"),
                ("provider_mh_adhd", "ADHD"),
                ("provider_mh_bipolar", "Bipolar Disorder"),
                ("provider_mh_suicidal", "Suicidal Ideation"),
            ]
            provider_mh_values = {}
            for col, label in provider_mh_fields:
                provider_mh_values[col] = st.checkbox(label, key=col)
            active_specialists = st.text_input(
                "Active Specialists (comma-separated)", key="active_specialists"
            )
        with col2:
            code_status = st.selectbox(
                "Code Status",
                ["Select one", "Full Code", "DNR", "Limited", "Unknown"],
                index=0,
                key="code_status",
            )
            cognitive_function = st.selectbox(
                "Cognitive Function",
                ["Select one", "Intact", "Mild Impairment", "Moderate", "Severe"],
                index=0,
                key="cognitive_function",
            )
            functional_status = st.selectbox(
                "Functional Status Summary",
                [
                    "Select one",
                    "Ambulatory without fall risk",
                    "Ambulatory with fall risk requiring device",
                    "Wheelchair",
                    "Bedbound",
                ],
                index=0,
                key="functional_status",
            )
            goc_value = st.selectbox(
                "GOC (Goals of Care)",
                ["Select one", "Full", "Palliative", "Hospice", "Unknown"],
                index=0,
                key="goc_value",
            )
            goals_of_care = st.text_area("Goals of Care (brief)", key="goals_of_care")
            active_concerns = st.text_area("Active Concerns", key="active_concerns")

    notes = st.text_area("Notes / Clinical Summary", key=f"{key_prefix}_notes")

    if st.button("Log Task", key=f"{key_prefix}_log_task"):
        if (
            not selected_patient_name
            or selected_patient_name == "Select one"
            or not selected_billing
        ):
            st.warning(
                "Please select a patient and ensure a billing code is available before saving."
            )
        else:
            selected_patient = patient_map.get(selected_patient_name)
            if not selected_patient:
                st.error("Selected patient not found. Refresh and try again.")
            else:
                try:
                    # Append notes to patient and save a provider task record using selected billing code
                    billing_code_to_use = selected_billing

                    database.save_daily_task(
                        provider_id=user_id,
                        patient_id=selected_patient["patient_id"],
                        task_date=task_date,
                        task_description=f"Primary Care Visit - {billing_code_to_use or 'Unknown'}",
                        notes=notes,
                        billing_code=billing_code_to_use,
                    )

                    # Directly persist clinical fields without schema validation
                    try:
                        conn = database.get_db_connection()

                        # Prepare base params for clinical fields
                        # Store subjective_risk as string value only
                        # Convert placeholders to None so DB gets NULL when user hasn't selected a value
                        functional_status_val = (
                            None
                            if (functional_status == "Select one")
                            else functional_status
                        )
                        subjective_risk_val = (
                            None
                            if (subjective_risk == "Select one")
                            else subjective_risk
                        )
                        code_status_val = (
                            None if (code_status == "Select one") else code_status
                        )
                        cognitive_function_val = (
                            None
                            if (cognitive_function == "Select one")
                            else cognitive_function
                        )
                        goc_value_val = (
                            None if (goc_value == "Select one") else goc_value
                        )

                        base_params = [
                            er_visits_6mo,
                            hospitalizations_6mo,
                            subjective_risk_val,
                            1 if provider_mh_concerns else 0,
                            provider_mh_values.get("provider_mh_schizophrenia", False),
                            provider_mh_values.get("provider_mh_depression", False),
                            provider_mh_values.get("provider_mh_anxiety", False),
                            provider_mh_values.get("provider_mh_stress", False),
                            provider_mh_values.get("provider_mh_adhd", False),
                            provider_mh_values.get("provider_mh_bipolar", False),
                            provider_mh_values.get("provider_mh_suicidal", False),
                            active_specialists,
                            code_status_val,
                            cognitive_function_val,
                            functional_status_val,
                            goals_of_care,
                            active_concerns,
                            goc_value_val,
                        ]

                        # If provider entered notes, append them with a dated header; otherwise leave notes unchanged
                        notes_text = (notes or "").strip()

                        # Build header with Date of Service - define date_str outside conditional blocks
                        try:
                            date_str = pd.to_datetime(task_date).date().isoformat()
                        except Exception:
                            date_str = str(task_date)

                        if notes_text:
                            header = (
                                """*************************************************************************\n"""
                                + f"Date {date_str}\n"
                                + "*************************************************************************\n"
                            )
                            notes_combined = header + notes_text

                            # Update patient record with clinical data and notes
                            conn.execute(
                                """
                                    UPDATE patients SET
                                        er_count_1yr = ?,
                                        hospitalization_count_1yr = ?,
                                        subjective_risk_level = ?,
                                        mental_health_concerns = ?,
                                        provider_mh_schizophrenia = ?,
                                        provider_mh_depression = ?,
                                        provider_mh_anxiety = ?,
                                        provider_mh_stress = ?,
                                        provider_mh_adhd = ?,
                                        provider_mh_bipolar = ?,
                                        provider_mh_suicidal = ?,
                                        active_specialists = ?,
                                        code_status = ?,
                                        cognitive_function = ?,
                                        functional_status = ?,
                                        goals_of_care = ?,
                                        chronic_conditions_provider = ?,
                                        goc_value = ?,
                                        last_visit_date = ?,
                                        notes = CASE WHEN notes IS NULL OR trim(notes) = '' THEN ? ELSE notes || '\n\n' || ? END
                                    WHERE patient_id = ?
                                """,
                                tuple(
                                    base_params
                                    + [
                                        date_str,
                                        notes_combined,
                                        notes_combined,
                                        selected_patient["patient_id"],
                                    ]
                                ),
                            )

                            # Also update patient_panel table with clinical fields (notes branch)
                            conn.execute(
                                """
                                    UPDATE patient_panel SET
                                        er_count_1yr = ?,
                                        hospitalization_count_1yr = ?,
                                        subjective_risk_level = ?,
                                        mental_health_concerns = ?,
                                        provider_mh_schizophrenia = ?,
                                        provider_mh_depression = ?,
                                        provider_mh_anxiety = ?,
                                        provider_mh_stress = ?,
                                        provider_mh_adhd = ?,
                                        provider_mh_bipolar = ?,
                                        provider_mh_suicidal = ?,
                                        active_specialists = ?,
                                        code_status = ?,
                                        cognitive_function = ?,
                                        functional_status = ?,
                                        goals_of_care = ?,
                                        chronic_conditions_provider = ?,
                                        goc_value = ?,
                                        last_visit_date = ?
                                    WHERE patient_id = ?
                                """,
                                tuple(
                                    base_params
                                    + [date_str, selected_patient["patient_id"]]
                                ),
                            )
                        else:
                            # Update only clinical fields without notes
                            conn.execute(
                                """
                                    UPDATE patients SET
                                        er_count_1yr = ?,
                                        hospitalization_count_1yr = ?,
                                        subjective_risk_level = ?,
                                        mental_health_concerns = ?,
                                        provider_mh_schizophrenia = ?,
                                        provider_mh_depression = ?,
                                        provider_mh_anxiety = ?,
                                        provider_mh_stress = ?,
                                        provider_mh_adhd = ?,
                                        provider_mh_bipolar = ?,
                                        provider_mh_suicidal = ?,
                                        active_specialists = ?,
                                        code_status = ?,
                                        cognitive_function = ?,
                                        functional_status = ?,
                                        goals_of_care = ?,
                                        chronic_conditions_provider = ?,
                                        goc_value = ?,
                                        last_visit_date = ?
                                    WHERE patient_id = ?
                                """,
                                tuple(
                                    base_params
                                    + [date_str, selected_patient["patient_id"]]
                                ),
                            )

                        # Also update patient_panel table with clinical fields
                        conn.execute(
                            """
                                UPDATE patient_panel SET
                                    er_count_1yr = ?,
                                    hospitalization_count_1yr = ?,
                                    subjective_risk_level = ?,
                                    mental_health_concerns = ?,
                                    provider_mh_schizophrenia = ?,
                                    provider_mh_depression = ?,
                                    provider_mh_anxiety = ?,
                                    provider_mh_stress = ?,
                                    provider_mh_adhd = ?,
                                    provider_mh_bipolar = ?,
                                    provider_mh_suicidal = ?,
                                    active_specialists = ?,
                                    code_status = ?,
                                    cognitive_function = ?,
                                    functional_status = ?,
                                    goals_of_care = ?,
                                    chronic_conditions_provider = ?,
                                    goc_value = ?,
                                    last_visit_date = ?
                                WHERE patient_id = ?
                            """,
                            tuple(
                                base_params + [date_str, selected_patient["patient_id"]]
                            ),
                        )

                        conn.commit()
                        conn.close()
                        st.success(
                            "Task saved and clinical fields persisted to patient record."
                        )

                        # Force refresh of patient data in session state
                        if f"patient_data_{user_id}" in st.session_state:
                            del st.session_state[f"patient_data_{user_id}"]
                        if f"onboarding_tasks_data_{user_id}" in st.session_state:
                            del st.session_state[f"onboarding_tasks_data_{user_id}"]

                        # Reset all clinical form fields to default values
                        clinical_field_keys = [
                            "er_visits_6mo",
                            "hospitalizations_6mo",
                            "subjective_risk",
                            "provider_mh_concerns",
                            "provider_mh_schizophrenia",
                            "provider_mh_depression",
                            "provider_mh_anxiety",
                            "provider_mh_stress",
                            "provider_mh_adhd",
                            "provider_mh_bipolar",
                            "provider_mh_suicidal",
                            "active_specialists",
                            "code_status",
                            "cognitive_function",
                            "functional_status",
                            "goc_value",
                            "goals_of_care",
                            "active_concerns",
                            f"{key_prefix}_notes",
                            f"{key_prefix}_patient",  # Reset patient selection to "Select one"
                        ]

                        # Debug: Show which keys are being reset
                        reset_keys = []
                        for field_key in clinical_field_keys:
                            if field_key in st.session_state:
                                reset_keys.append(field_key)
                                del st.session_state[field_key]

                        if reset_keys:
                            # st.info(f"Reset session state keys: {', '.join(reset_keys)}")
                            pass

                        # Trigger a rerun to refresh the patient list with updated data
                        st.rerun()
                    except Exception as e:
                        # Provide detailed error information to help diagnose the issue
                        error_msg = str(e)
                        st.warning(
                            f"Task saved. Clinical fields were not persisted to patient record."
                        )
                        st.error(f"**Error details:** {error_msg}")

                        # Log additional debugging information
                        st.write("**Debug Info:**")
                        st.write(f"- Patient ID: {selected_patient['patient_id']}")
                        st.write(f"- Notes provided: {'Yes' if notes_text else 'No'}")
                        st.write(f"- Base params count: {len(base_params)}")

                        # Check if it's a column-related error
                        if "no such column" in error_msg.lower():
                            st.write(
                                "**Missing column detected** - This indicates a schema mismatch."
                            )
                        elif "constraint" in error_msg.lower():
                            st.write(
                                "**Constraint violation** - Check data types and foreign key relationships."
                            )
                        elif "syntax error" in error_msg.lower():
                            st.write(
                                "**SQL syntax error** - Check the UPDATE statement structure."
                            )

                        # Close connection if still open
                        try:
                            conn.close()
                        except:
                            pass

                except Exception as e:
                    st.error(f"Error saving task: {e}")

    st.markdown("---")

    # # Additional zip code information section
    # st.subheader("Zip Code Information")
    # st.write("Available zip codes for filtering:")

    # # Create a simple table of zip codes
    # zip_code_df = pd.DataFrame(all_zip_codes, columns=['Zip Code', 'Location'])
    # st.dataframe(zip_code_df, height=200, use_container_width=True)

    # # Add a summary section
    # st.subheader("Quick Summary")
    # st.write(f"Total patients assigned: {total_patients}")
    # st.write(f"Active patients: {active_patients}")
    # st.write(f"Time served this month: {time_string}")
    # st.write(f"Available task types: {len(task_options)}")


def show_unfiltered_patient_summary(patients_list=None, height=900):
    """
    Display an unfiltered patient summary table (no provider filtering) using
    the same columns, ordering and Last Visit conditional coloring used in
    the provider view.

    - patients_list: optional list of patient dicts. If None, will try
      database.get_all_patients() then database.get_patient_assignment_overview().
    - height: pixel height for the displayed table.
    """
    # Lazy import / fallbacks
    try:
        if patients_list is None:
            # Prefer the denormalized patient_panel table which already contains
            # coordinator_name/provider_name/last_visit_date fields used by the UI.
            try:
                patients_list = database.get_all_patient_panel()
            except Exception:
                try:
                    patients_list = database.get_all_patients()
                except Exception:
                    patients_list = database.get_patient_assignment_overview()
    except Exception:
        patients_list = patients_list or []

    if not patients_list:
        st.info("No patients available to display.")
        return

    # Required columns and display names (same as provider view)
    required_columns = [
        ("status", "Status"),
        ("goc_value", "GOC"),
        ("code_status", "Code Status"),
        ("first_name", "First Name"),
        ("last_name", "Last Name"),
        ("facility", "Facility"),
        ("assigned_coordinator", "Assigned Coordinator"),
        ("last_visit_date", "Last Visit Date"),
        ("service_type", "Service Type"),
        ("phone_primary", "Phone Number"),
    ]

    try:
        patients_df = pd.DataFrame(patients_list)

        # patient_panel already provides human-readable coordinator/provider fields
        # but normalize a few common keys to 'assigned_coordinator' to be safe.
        if (
            "coordinator_name" in patients_df.columns
            and "assigned_coordinator" not in patients_df.columns
        ):
            patients_df["assigned_coordinator"] = patients_df["coordinator_name"]
        elif (
            "coordinator_full_name" in patients_df.columns
            and "assigned_coordinator" not in patients_df.columns
        ):
            patients_df["assigned_coordinator"] = patients_df["coordinator_full_name"]
        else:
            # fallback: try mapping by id if present
            try:
                coordinators = database.get_users_by_role(36) or []
                coord_map = {
                    c["user_id"]: c.get("full_name") or c.get("username")
                    for c in coordinators
                }
                coord_map.update({str(k): v for k, v in list(coord_map.items())})
            except Exception:
                coord_map = {}
            coord_id_fields = [
                "assigned_coordinator_id",
                "coordinator_user_id",
                "assigned_coordinator_user_id",
                "coord_id",
            ]
            mapped = False
            for fld in coord_id_fields:
                if fld in patients_df.columns:
                    patients_df["assigned_coordinator"] = patients_df[fld].map(
                        lambda x: coord_map.get(x)
                        if x in coord_map
                        else coord_map.get(str(x))
                        if pd.notna(x)
                        else "Unassigned"
                    )
                    mapped = True
                    break
            if not mapped and "assigned_coordinator" not in patients_df.columns:
                patients_df["assigned_coordinator"] = None

        # Normalize last-visit column: accept several possible source column names
        possible_last_visit_cols = [
            "last_visit_date",
            "last_visit",
            "last_visit_dt",
            "last_visit_at",
            "last_visit_timestamp",
            "most_recent_visit",
            "last_visit_date_iso",
        ]
        found = None
        for c in possible_last_visit_cols:
            if c in patients_df.columns:
                found = c
                break
        if found and found != "last_visit_date":
            patients_df["last_visit_date"] = patients_df[found]

        # Ensure required columns exist
        for col, _ in required_columns:
            if col not in patients_df.columns:
                patients_df[col] = None

        display_columns = [col for col, _ in required_columns]
        column_names = [name for _, name in required_columns]

        display_df = patients_df[display_columns].copy()
        display_df.columns = column_names

        # Normalize last visit date to MM-DD-YYYY strings (or None)
        if "Last Visit Date" in display_df.columns:

            def _format_date(val):
                try:
                    ts = pd.to_datetime(val, errors="coerce")
                    return ts.strftime("%m-%d-%Y") if not pd.isna(ts) else None
                except Exception:
                    return None

            display_df["Last Visit Date"] = display_df["Last Visit Date"].apply(
                _format_date
            )

        import datetime as _dt

        def color_patient_name(row):
            color = ""
            last_visit = row.get("Last Visit Date")
            today = _dt.datetime.now().date()
            if last_visit:
                try:
                    last_visit_dt = pd.to_datetime(last_visit, errors="coerce")
                    if not pd.isna(last_visit_dt):
                        last_visit_dt = last_visit_dt.date()
                        delta = (today - last_visit_dt).days
                        if delta > 60:
                            color = "background-color: #ffcccc; color: #a00;"
                        elif 30 < delta <= 60:
                            color = "background-color: #fff3cd; color: #a67c00;"
                        elif 0 <= delta <= 30:
                            color = "background-color: #d4edda; color: #155724;"
                except Exception:
                    pass
            return color

        def style_patient_names(df):
            return df.style.apply(
                lambda row: [
                    color_patient_name(row)
                    if col in ["First Name", "Last Name"]
                    else ""
                    for col in df.columns
                ],
                axis=1,
            )

        try:
            # Try to display with styling first
            st.dataframe(
                style_patient_names(display_df),
                height=height,
                use_container_width=True,
                column_config={
                    "Status": st.column_config.TextColumn("Status", width=None),
                    "GOC": st.column_config.TextColumn("GOC", width=None),
                    "Code Status": st.column_config.TextColumn(
                        "Code Status", width=None
                    ),
                    "First Name": st.column_config.TextColumn("First Name", width=None),
                    "Last Name": st.column_config.TextColumn("Last Name", width=None),
                    "Facility": st.column_config.TextColumn("Facility", width=None),
                    "Assigned Coordinator": st.column_config.TextColumn(
                        "Assigned Coordinator", width=None
                    ),
                    "Last Visit Date": st.column_config.DateColumn(
                        "Last Visit Date", width=None
                    ),
                    "Service Type": st.column_config.TextColumn(
                        "Service Type", width=None
                    ),
                    "Phone Number": st.column_config.TextColumn(
                        "Phone Number", width=None
                    ),
                },
                hide_index=True,
                # autosize_columns removed (not needed)
            )
        except Exception as styling_error:
            # If styling fails due to compatibility issues, fall back to plain display
            st.warning(
                "⚠️ Color mapping temporarily unavailable due to styling compatibility. Displaying plain table."
            )
            st.dataframe(
                display_df,
                height=height,
                use_container_width=True,
                column_config={
                    "Status": st.column_config.TextColumn("Status", width=None),
                    "GOC": st.column_config.TextColumn("GOC", width=None),
                    "Code Status": st.column_config.TextColumn(
                        "Code Status", width=None
                    ),
                    "First Name": st.column_config.TextColumn("First Name", width=None),
                    "Last Name": st.column_config.TextColumn("Last Name", width=None),
                    "Facility": st.column_config.TextColumn("Facility", width=None),
                    "Assigned Coordinator": st.column_config.TextColumn(
                        "Assigned Coordinator", width=None
                    ),
                    "Last Visit Date": st.column_config.DateColumn(
                        "Last Visit Date", width=None
                    ),
                    "Service Type": st.column_config.TextColumn(
                        "Service Type", width=None
                    ),
                    "Phone Number": st.column_config.TextColumn(
                        "Phone Number", width=None
                    ),
                },
                hide_index=True,
            )

    except Exception as e:
        st.error(f"Error rendering unfiltered patient summary: {e}")
        try:
            st.dataframe(
                pd.DataFrame(patients_list), height=height, use_container_width=True
            )
            st.dataframe(
                pd.DataFrame(patients_list), height=height, use_container_width=True
            )
        except Exception:
            st.write("Unable to render patient table.")


def show_patient_info_tab_provider(user_id):
    try:
        search_query = st.text_input(
            "Search by name or ID", key="cp_patient_info_search"
        )

        # Check if user has admin role for edit access
        has_admin_access = _has_admin_role(user_id)

        if has_admin_access:
            edit_mode = st.checkbox("Enable editing", key="cp_patient_edit_mode")
        else:
            edit_mode = False
            st.info(
                "🔒 **View-Only Mode**: Patient info editing is restricted to administrators"
            )

        # Always use the full patient panel (admin-equivalent view)
        patient_data_list = (
            database.get_all_patient_panel()
            if hasattr(database, "get_all_patient_panel")
            else []
        )

        import pandas as pd

        df = pd.DataFrame(patient_data_list)

        if df.empty:
            st.info("No patient data available.")
            return

        if "patient_id" not in df.columns:
            df["patient_id"] = None

        df["full_name"] = (
            df.get("first_name", "").fillna("")
            + " "
            + df.get("last_name", "").fillna("")
        ).str.strip()

        if search_query:
            q = str(search_query).lower().strip()
            df = df[
                df.apply(
                    lambda r: q in str(r.get("patient_id", "")).lower()
                    or q in str(r.get("full_name", "")).lower(),
                    axis=1,
                )
            ]

        from datetime import datetime

        def _days_since(date_val):
            try:
                if pd.isna(date_val) or not str(date_val).strip():
                    return None
                return (datetime.now() - pd.to_datetime(date_val)).days
            except Exception:
                return None

        # Normalize last visit date to consistent column
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
            if c in df.columns:
                found_last = c
                break
        df["Last Visit Date"] = df[found_last] if found_last else None
        df["days_since_last_visit"] = df.get("Last Visit Date").apply(_days_since)

        # Define columns that should be disabled for editing (must use reassignment function)
        disabled_columns = []
        for col in ["coordinator_id", "provider_id", "coordinator_name", "provider_name",
                    "care_coordinator_name", "care_provider_name"]:
            if col in df.columns:
                disabled_columns.append(col)

        display_cols = [
            "patient_id",
            "status",
            "first_name",
            "last_name",
            "facility",
            "Last Visit Date",
            "service_type",
            "phone_primary",
        ]
        # Add coordinator and provider columns if they exist
        for col in ["coordinator_name", "provider_name"]:
            if col in df.columns and col not in display_cols:
                display_cols.append(col)

        existing_cols = [c for c in display_cols if c in df.columns]
        df_display = df[existing_cols].copy()

        def _color_last_visit(val):
            try:
                d = _days_since(val)
                if d is None:
                    return ""
                if d <= 30:
                    return "background-color: #90be6d; color: black"
                if d <= 60:
                    return "background-color: #f9c74f; color: black"
                return "background-color: #f94144; color: white"
            except Exception:
                return ""

        # Display based on edit permissions
        if edit_mode and has_admin_access:
            # Show editable dataframe for admin users
            # Disable coordinator and provider columns - must use reassignment function
            disabled_in_display = [col for col in disabled_columns if col in df_display.columns]
            edited_df = st.data_editor(
                df_display,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="cp_patient_info_editor",
                disabled=disabled_in_display if disabled_in_display else None,
            )
            if edited_df is not None and not edited_df.equals(df_display):
                _apply_patient_info_edits(edited_df, df_display)
                st.success("Patient information updated successfully!")
                st.rerun()
        else:
            # Show read-only dataframe for non-admin users
            try:
                styled = (
                    df_display.style.map(_color_last_visit, subset=["Last Visit Date"])
                    if "Last Visit Date" in df_display.columns
                    else df_display.style
                )
                st.dataframe(styled, use_container_width=True)
            except Exception:
                st.dataframe(df_display, use_container_width=True)

    except Exception as e:
        st.error(f"Error in Patient Info tab: {e}")


def _apply_patient_info_edits(edited_df, original_df):
    import pandas as pd

    if edited_df is None or original_df is None:
        return
    if "patient_id" not in edited_df.columns:
        return
    original_by_id = {
        str(r["patient_id"]): r
        for _, r in original_df.iterrows()
        if pd.notna(r.get("patient_id"))
    }
    conn = database.get_db_connection()
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
            patient_cols = [
                c[1] for c in conn.execute("PRAGMA table_info('patients')").fetchall()
            ]
            set_parts = []
            params = []
            for k, v in changed.items():
                if k in patient_cols:
                    set_parts.append(f"{k} = ?")
                    params.append(v)
            if set_parts:
                params.append(pid)
                conn.execute(
                    f"UPDATE patients SET {', '.join(set_parts)}, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
                    tuple(params),
                )
            panel_cols = [
                c[1]
                for c in conn.execute("PRAGMA table_info('patient_panel')").fetchall()
            ]
            set_parts = []
            params = []
            for k, v in changed.items():
                if k in panel_cols:
                    set_parts.append(f"{k} = ?")
                    params.append(v)
            if set_parts:
                params.append(pid)
                conn.execute(
                    f"UPDATE patient_panel SET {', '.join(set_parts)}, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
                    tuple(params),
                )
        conn.commit()
    finally:
        conn.close()


def show_provider_onboarding_queue(user_id, onboarding_queue):
    """Display the provider's onboarding queue for initial visits"""
    st.subheader("Onboarding Queue & Initial Visits")

    st.info(f"You have {len(onboarding_queue)} patients assigned for initial visits")

    # Display onboarding queue table
    st.markdown("### Patients Assigned for Initial Visits")

    if onboarding_queue:
        # Sort onboarding_queue by last_name, then first_name
        onboarding_queue = sorted(
            onboarding_queue,
            key=lambda p: (
                str(p.get("last_name", "")).lower(),
                str(p.get("first_name", "")).lower(),
            ),
        )
        # Create a table of patients
        patients_data = []
        for patient in onboarding_queue:
            # Format specialist requirements
            requirements = []
            if patient.get("hypertension"):
                requirements.append("Hypertension")
            if patient.get("mental_health_concerns"):
                requirements.append("Mental Health")
            if patient.get("dementia"):
                requirements.append("Dementia")
            if patient.get("annual_well_visit"):
                requirements.append("Annual Wellness")

            requirements_str = (
                " | ".join(requirements) if requirements else "No special requirements"
            )

            patients_data.append(
                {
                    "Patient Name": f"{patient['first_name']} {patient['last_name']}",
                    "DOB": patient.get("date_of_birth", ""),
                    "Phone": patient.get("phone_primary", ""),
                    "Visit Type": patient.get("visit_type", "Home Visit"),
                    "Appointment": f"{patient.get('tv_date', 'Not scheduled')} {patient.get('tv_time', '')}".strip(),
                    # "Billing Code": patient.get('billing_code', '99345'),
                    # "Duration": f"{patient.get('duration_minutes', 45)} min",
                    "Special Requirements": requirements_str,
                    "Created": patient.get("created_date", "")[:10]
                    if patient.get("created_date")
                    else "",
                }
            )

        # Display as dataframe
        df = pd.DataFrame(patients_data)
        # Default sort by Patient Name (last name)
        if not df.empty:
            # Try to split Patient Name for sorting
            df["Last Name"] = df["Patient Name"].apply(
                lambda x: x.split(" ")[-1] if isinstance(x, str) and " " in x else x
            )
            df = df.sort_values(by=["Last Name", "Patient Name"], ascending=True)
            df = df.drop(columns=["Last Name"])
        st.data_editor(
            df, use_container_width=True, hide_index=True, num_rows="dynamic"
        )
    else:
        st.warning("No patients assigned for initial TV visits.")

    # Daily task entries for onboarding queue
    st.markdown("### 📝 Initial Visit Task Logging")
    st.info(
        "Complete initial visit tasks for your assigned onboarding patients (Home Visit or Telehealth)"
    )

    # Force refresh of session state to ensure fresh data
    if st.button("Refresh Patient Data", key="refresh_onboarding_data"):
        session_key = f"onboarding_tasks_data_{user_id}"
        if session_key in st.session_state:
            del st.session_state[session_key]
        st.rerun()

    # Initialize session state for onboarding tasks (refresh every time if no data)
    session_key = f"onboarding_tasks_data_{user_id}"
    if (
        session_key not in st.session_state
        or not st.session_state[session_key]
        or len(st.session_state[session_key]) != len(onboarding_queue)
    ):
        # Always refresh if patient count changed or data is stale
        st.session_state[session_key] = []
        for patient in onboarding_queue:
            # Determine task type based on visit type
            visit_type = patient.get("visit_type", "Home Visit")
            if visit_type == "Telehealth Visit":
                task_type = "PCP-Visit Telehealth (TE) (NEW pt)"
            else:
                task_type = "PCP-Visit Home Visit (HV) (NEW pt)"

            st.session_state[session_key].append(
                {
                    "patient_name": f"{patient['first_name']} {patient['last_name']}",
                    "patient_id": patient.get("patient_id"),
                    "onboarding_id": patient["onboarding_id"],
                    "visit_type": visit_type,
                    "billing_code": patient.get("billing_code", "99345"),
                    "duration_minutes": patient.get("duration_minutes", 45),
                    "task_type": task_type,
                    "date": pd.to_datetime("today").date(),
                    "notes": "",
                    "specialist_requirements": {
                        "hypertension": patient.get("hypertension", False),
                        "mental_health_concerns": patient.get(
                            "mental_health_concerns", False
                        ),
                        "dementia": patient.get("dementia", False),
                        "annual_well_visit": patient.get("annual_well_visit", False),
                    },
                }
            )

    # Create task entries for each onboarding patient
    for i, task_entry in enumerate(st.session_state[session_key]):
        if i < len(onboarding_queue):  # Only show tasks for current queue
            visit_type = task_entry.get("visit_type", "Home Visit")
            st.markdown(
                f"#### Initial {visit_type} Task {i+1}: {task_entry['patient_name']}"
            )

            # Show specialist requirements prominently - make them interactive for provider to confirm
            requirements = task_entry.get("specialist_requirements", {})
            st.markdown("**Confirm Specialist Requirements for this Patient:**")
            st.markdown(
                "*Review and confirm specialist needs during the initial TV visit*"
            )

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                task_entry["confirm_hypertension"] = st.checkbox(
                    "Hypertension",
                    value=requirements.get("hypertension", False),
                    key=f"hypertension_{i}",
                    help="Check if patient needs hypertension management",
                )
            with col2:
                task_entry["confirm_mental_health"] = st.checkbox(
                    "Mental Health",
                    value=requirements.get("mental_health_concerns", False),
                    key=f"mental_health_{i}",
                    help="Check if patient needs mental health support",
                )
            with col3:
                task_entry["confirm_dementia"] = st.checkbox(
                    "Dementia Care",
                    value=requirements.get("dementia", False),
                    key=f"dementia_{i}",
                    help="Check if patient needs dementia care",
                )
            with col4:
                task_entry["confirm_annual_wellness"] = st.checkbox(
                    "Annual Wellness",
                    value=requirements.get("annual_well_visit", False),
                    key=f"annual_wellness_{i}",
                    help="Check if patient needs annual wellness visit",
                )

            # Show any changes from initial assessment
            changes = []
            if task_entry.get("confirm_hypertension") != requirements.get(
                "hypertension", False
            ):
                changes.append(
                    f"Hypertension: {'Added' if task_entry.get('confirm_hypertension') else 'Removed'}"
                )
            if task_entry.get("confirm_mental_health") != requirements.get(
                "mental_health_concerns", False
            ):
                changes.append(
                    f"Mental Health: {'Added' if task_entry.get('confirm_mental_health') else 'Removed'}"
                )
            if task_entry.get("confirm_dementia") != requirements.get(
                "dementia", False
            ):
                changes.append(
                    f"Dementia Care: {'Added' if task_entry.get('confirm_dementia') else 'Removed'}"
                )
            if task_entry.get("confirm_annual_wellness") != requirements.get(
                "annual_well_visit", False
            ):
                changes.append(
                    f"Annual Wellness: {'Added' if task_entry.get('confirm_annual_wellness') else 'Removed'}"
                )

            if changes:
                st.info(f"**Changes from initial assessment:** {', '.join(changes)}")

            st.divider()

            # Task entry form
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

            with col1:
                task_entry["date"] = st.date_input(
                    f"Date {i+1}",
                    value=task_entry.get("date", pd.to_datetime("today").date()),
                    key=f"onb_date_{i}",
                )

            with col2:
                # Visit type selection
                current_visit_type = task_entry.get("visit_type", "Home Visit")
                new_visit_type = st.selectbox(
                    f"Visit Type {i+1}",
                    options=["Home Visit", "Telehealth Visit"],
                    index=0 if current_visit_type == "Home Visit" else 1,
                    key=f"visit_type_{i}",
                )

                # Update task entry if visit type changed
                if new_visit_type != current_visit_type:
                    task_entry["visit_type"] = new_visit_type
                    # Map visit type to location_type for billing lookup
                    location_map = {
                        "Home Visit": "Home",
                        "Telehealth Visit": "Telehealth",
                    }
                    db_location_type = location_map.get(new_visit_type, "Home")

                    # Look up billing code for new selection, using the current patient type
                    current_pt_type = task_entry.get("patient_type", "New")
                    billing_options = database.get_billing_codes(
                        service_type=current_pt_type,
                        location_type=db_location_type,
                        patient_type=current_pt_type,
                    )
                    if billing_options:
                        task_entry["billing_code"] = billing_options[0].get("billing_code", "Unknown")
                        duration_min = billing_options[0].get("min_minutes", 45)
                        duration_max = billing_options[0].get("max_minutes", 75)
                        task_entry["duration_minutes"] = (duration_min + duration_max) // 2
                    else:
                        # Fallback defaults
                        if new_visit_type == "Home Visit":
                            task_entry["billing_code"] = "99345"
                            task_entry["duration_minutes"] = 45
                        else:
                            task_entry["billing_code"] = "99201"
                            task_entry["duration_minutes"] = 30

                    # Update task type description to be dynamic based on selected patient type
                    if new_visit_type == "Home Visit":
                        task_entry["task_type"] = f"PCP-Visit Home Visit (HV) ({current_pt_type})"
                    else:
                        task_entry["task_type"] = f"PCP-Visit Telehealth (TE) ({current_pt_type})"

            with col3:
                # Patient type selection for billing code lookup
                patient_type_options = ["New", "Acute", "Cognitive", "Follow Up", "TCM-7", "TCM-14"]
                task_entry["patient_type"] = st.selectbox(
                    f"Patient Type {i+1}",
                    patient_type_options,
                    index=patient_type_options.index(task_entry.get("patient_type", "New")),
                    key=f"patient_type_{i}",
                    help="Select patient type for accurate billing code assignment"
                )

                # Update billing code when patient type changes
                current_patient_type = task_entry.get("patient_type", "New")
                session_key_patient_type = f"prev_patient_type_{i}"
                if session_key_patient_type in st.session_state and st.session_state[session_key_patient_type] != current_patient_type:
                    # Patient type changed, update billing code
                    visit_type = task_entry.get("visit_type", "Home Visit")
                    
                    location_map = {
                        "Home Visit": "Home",
                        "Telehealth Visit": "Telehealth",
                    }
                    db_location_type = location_map.get(visit_type, "Home")

                    # Special handling for TCM codes (direct code assignment)
                    if current_patient_type == "TCM-7":
                        task_entry["billing_code"] = "99496"  # TCM 7-day
                        task_entry["duration_minutes"] = 30  # Typical TCM duration
                    elif current_patient_type == "TCM-14":
                        task_entry["billing_code"] = "99495"  # TCM 14-day
                        task_entry["duration_minutes"] = 60  # Typical TCM duration
                    else:
                        # Regular lookup for other patient types
                        billing_options = database.get_billing_codes(
                            service_type=current_patient_type,
                            location_type=db_location_type,
                            patient_type=current_patient_type,
                        )

                        if billing_options:
                            task_entry["billing_code"] = billing_options[0].get("billing_code", "Unknown")
                            duration_min = billing_options[0].get("min_minutes", 45)
                            duration_max = billing_options[0].get("max_minutes", 75)
                            task_entry["duration_minutes"] = (duration_min + duration_max) // 2
                        else:
                            # Final fallback
                            if current_patient_type == "Follow Up":
                                task_entry["billing_code"] = "99350" if db_location_type == "Home" else "99214"
                            else:
                                task_entry["billing_code"] = "99345" if db_location_type == "Home" else "99204"
                            task_entry["duration_minutes"] = 45

                    # Update task type description to match new patient type
                    if visit_type == "Home Visit":
                        task_entry["task_type"] = f"PCP-Visit Home Visit (HV) ({current_patient_type})"
                    else:
                        task_entry["task_type"] = f"PCP-Visit Telehealth (TE) ({current_patient_type})"

                st.session_state[session_key_patient_type] = current_patient_type

            with col4:
                st.write(f"**Patient:** {task_entry['patient_name']}")
                st.write(f"**Task:** {task_entry['task_type']}")
                st.write(f"**Billing Code:** {task_entry.get('billing_code', 'Unknown')} ({task_entry.get('duration_minutes', 45)} min)")
                st.caption(f"Patient Type: {task_entry.get('patient_type', 'New')}")

            task_entry["notes"] = st.text_area(
                f"Visit Notes {i+1}",
                value=task_entry.get("notes", ""),
                key=f"onb_notes_{i}",
                placeholder="Document visit details, patient response, any concerns...",
            )

            # Clinical assessment fields for both visit types
            visit_type_display = task_entry.get("visit_type", "Home Visit")
            st.markdown(f"#### Clinical Assessment ({visit_type_display})")
            st.markdown(
                "*Please collect comprehensive clinical data during the visit:*"
            )

            col_left, col_right = st.columns(2)

            with col_left:
                task_entry["er_visits_6mo"] = st.number_input(
                    f"ER Visits (last 12 months) {i+1}",
                    min_value=0,
                    step=1,
                    value=task_entry.get("er_visits_6mo", 0),
                    key=f"onb_er_visits_{i}",
                )

                task_entry["hospitalizations_6mo"] = st.number_input(
                    f"Hospitalizations (last 12 months) {i+1}",
                    min_value=0,
                    step=1,
                    value=task_entry.get("hospitalizations_6mo", 0),
                    key=f"onb_hospitalizations_{i}",
                )

                task_entry["subjective_risk"] = st.selectbox(
                    f"Subjective Risk Level {i+1}",
                    [
                        "Select one",
                        "Level 6 - in danger of dying or institutionalized within 1 yr",
                        "Level 5 - complications of chronic conditions or high risk social determinants of health",
                        "Level 4 - unstable chronic conditions but no complications",
                        "Level 3 - stable chronic conditions",
                        "Level 2 - healthy, some out of range biometrics",
                        "Level 1 - healthy, in range biometrics",
                    ],
                    index=0,
                    key=f"onb_subjective_risk_{i}",
                )

                task_entry["provider_mh_concerns"] = st.checkbox(
                    f"Mental Health Concerns {i+1}",
                    value=task_entry.get("provider_mh_concerns", False),
                    key=f"onb_mh_concerns_{i}",
                )

                if task_entry.get("provider_mh_concerns"):
                    st.markdown("**Specific Mental Health Conditions:**")
                    mh_fields = [
                        ("provider_mh_schizophrenia", "Schizophrenia"),
                        ("provider_mh_depression", "Depression"),
                        ("provider_mh_anxiety", "Anxiety"),
                        ("provider_mh_stress", "Stress/PTSD"),
                        ("provider_mh_adhd", "ADHD"),
                        ("provider_mh_bipolar", "Bipolar Disorder"),
                        ("provider_mh_suicidal", "Suicidal Ideation"),
                    ]
                    for field_name, label in mh_fields:
                        task_entry[field_name] = st.checkbox(
                            label,
                            value=task_entry.get(field_name, False),
                            key=f"onb_{field_name}_{i}",
                        )

                task_entry["active_specialists"] = st.text_input(
                    f"Active Specialists (comma-separated) {i+1}",
                    value=task_entry.get("active_specialists", ""),
                    key=f"onb_specialists_{i}",
                )

            with col_right:
                task_entry["code_status"] = st.selectbox(
                    f"Code Status {i+1}",
                    ["Select one", "Full Code", "DNR", "Limited", "Unknown"],
                    index=0,
                    key=f"onb_code_status_{i}",
                )

                task_entry["cognitive_function"] = st.selectbox(
                    f"Cognitive Function {i+1}",
                    ["Select one", "Intact", "Mild Impairment", "Moderate", "Severe"],
                    index=0,
                    key=f"onb_cognitive_{i}",
                )

                task_entry["functional_status"] = st.selectbox(
                    f"Functional Status {i+1}",
                    [
                        "Select one",
                        "Ambulatory without fall risk",
                        "Ambulatory with fall risk requiring device",
                        "Wheelchair",
                        "Bedbound",
                    ],
                    index=0,
                    key=f"onb_functional_{i}",
                )

                task_entry["goc_value"] = st.selectbox(
                    f"GOC (Goals of Care) {i+1}",
                    ["Select one", "Full", "Palliative", "Hospice", "Unknown"],
                    index=0,
                    key=f"onb_goc_{i}",
                )

                task_entry["goals_of_care"] = st.text_area(
                    f"Goals of Care (brief) {i+1}",
                    value=task_entry.get("goals_of_care", ""),
                    key=f"onb_goals_{i}",
                )

                task_entry["active_concerns"] = st.text_area(
                    f"Active Concerns {i+1}",
                    value=task_entry.get("active_concerns", ""),
                    key=f"onb_concerns_{i}",
                )

            # Submit button
            visit_type_short = (
                "TV" if task_entry.get("visit_type") == "Telehealth Visit" else "HV"
            )
            if st.button(
                f"Complete Initial {visit_type_short} Visit {i+1}",
                key=f"complete_onb_task_{i}",
                type="primary",
            ):
                if task_entry.get("patient_name") and task_entry.get("task_type"):
                    try:
                        # Get provider_id
                        provider_id = database.get_provider_id_from_user_id(user_id)
                        if provider_id:
                            # Save the task (this will automatically update onboarding workflow)
                            success = database.save_daily_task(
                                provider_id=provider_id,
                                patient_id=task_entry.get("patient_id"),
                                task_date=task_entry["date"],
                                task_description=task_entry["task_type"],
                                notes=task_entry["notes"],
                                billing_code=task_entry.get("billing_code"),
                            )

                            # Save additional clinical data for both visit types
                            if success:
                                try:
                                    conn = database.get_db_connection()

                                    # Prepare clinical data with proper null handling
                                    subjective_risk_val = (
                                        None
                                        if task_entry.get("subjective_risk")
                                        == "Select one"
                                        else task_entry.get("subjective_risk")
                                    )
                                    code_status_val = (
                                        None
                                        if task_entry.get("code_status") == "Select one"
                                        else task_entry.get("code_status")
                                    )
                                    cognitive_function_val = (
                                        None
                                        if task_entry.get("cognitive_function")
                                        == "Select one"
                                        else task_entry.get("cognitive_function")
                                    )
                                    functional_status_val = (
                                        None
                                        if task_entry.get("functional_status")
                                        == "Select one"
                                        else task_entry.get("functional_status")
                                    )
                                    goc_value_val = (
                                        None
                                        if task_entry.get("goc_value") == "Select one"
                                        else task_entry.get("goc_value")
                                    )

                                    # Format notes with header if provided
                                    notes_text = (task_entry.get("notes") or "").strip()
                                    if notes_text:
                                        try:
                                            date_str = (
                                                pd.to_datetime(task_entry["date"])
                                                .date()
                                                .isoformat()
                                            )
                                        except Exception:
                                            date_str = str(task_entry["date"])

                                        header = f"*************************************************************************\nDate {date_str}\n*************************************************************************\n"
                                        notes_combined = header + notes_text

                                        # Update patient record with clinical data and notes
                                        conn.execute(
                                            """
                                            UPDATE patients SET
                                                er_count_1yr = ?,
                                                hospitalization_count_1yr = ?,
                                                subjective_risk_level = ?,
                                                mental_health_concerns = ?,
                                                provider_mh_schizophrenia = ?,
                                                provider_mh_depression = ?,
                                                provider_mh_anxiety = ?,
                                                provider_mh_stress = ?,
                                                provider_mh_adhd = ?,
                                                provider_mh_bipolar = ?,
                                                provider_mh_suicidal = ?,
                                                active_specialists = ?,
                                                code_status = ?,
                                                cognitive_function = ?,
                                                functional_status = ?,
                                                goals_of_care = ?,
                                                chronic_conditions_provider = ?,
                                                goc_value = ?,
                                                last_visit_date = ?,
                                                notes = CASE WHEN notes IS NULL OR trim(notes) = '' THEN ? ELSE notes || '\n\n' || ? END
                                            WHERE patient_id = ?
                                        """,
                                            (
                                                task_entry.get("er_visits_6mo", 0),
                                                task_entry.get(
                                                    "hospitalizations_6mo", 0
                                                ),
                                                subjective_risk_val,
                                                1
                                                if task_entry.get(
                                                    "provider_mh_concerns"
                                                )
                                                else 0,
                                                task_entry.get(
                                                    "provider_mh_schizophrenia", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_depression", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_anxiety", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_stress", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_adhd", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_bipolar", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_suicidal", False
                                                ),
                                                task_entry.get(
                                                    "active_specialists", ""
                                                ),
                                                code_status_val,
                                                cognitive_function_val,
                                                functional_status_val,
                                                task_entry.get("goals_of_care", ""),
                                                task_entry.get("active_concerns", ""),
                                                goc_value_val,
                                                date_str,
                                                notes_combined,
                                                notes_combined,
                                                task_entry.get("patient_id"),
                                            ),
                                        )
                                    else:
                                        # Update only clinical fields without notes
                                        conn.execute(
                                            """
                                            UPDATE patients SET
                                                er_count_1yr = ?,
                                                hospitalization_count_1yr = ?,
                                                subjective_risk_level = ?,
                                                mental_health_concerns = ?,
                                                provider_mh_schizophrenia = ?,
                                                provider_mh_depression = ?,
                                                provider_mh_anxiety = ?,
                                                provider_mh_stress = ?,
                                                provider_mh_adhd = ?,
                                                provider_mh_bipolar = ?,
                                                provider_mh_suicidal = ?,
                                                active_specialists = ?,
                                                code_status = ?,
                                                cognitive_function = ?,
                                                functional_status = ?,
                                                goals_of_care = ?,
                                                chronic_conditions_provider = ?,
                                                goc_value = ?,
                                                last_visit_date = ?
                                            WHERE patient_id = ?
                                        """,
                                            (
                                                task_entry.get("er_visits_6mo", 0),
                                                task_entry.get(
                                                    "hospitalizations_6mo", 0
                                                ),
                                                subjective_risk_val,
                                                1
                                                if task_entry.get(
                                                    "provider_mh_concerns"
                                                )
                                                else 0,
                                                task_entry.get(
                                                    "provider_mh_schizophrenia", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_depression", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_anxiety", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_stress", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_adhd", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_bipolar", False
                                                ),
                                                task_entry.get(
                                                    "provider_mh_suicidal", False
                                                ),
                                                task_entry.get(
                                                    "active_specialists", ""
                                                ),
                                                code_status_val,
                                                cognitive_function_val,
                                                functional_status_val,
                                                task_entry.get("goals_of_care", ""),
                                                task_entry.get("active_concerns", ""),
                                                goc_value_val,
                                                date_str,
                                                task_entry.get("patient_id"),
                                            ),
                                        )

                                    conn.commit()
                                    conn.close()
                                except Exception as e:
                                    st.error(f"Error saving clinical data: {e}")

                            # Update specialist requirements and visit type based on provider's confirmation during visit
                            if success and task_entry.get("onboarding_id"):
                                conn = database.get_db_connection()
                                try:
                                    conn.execute(
                                        """
                                        UPDATE onboarding_patients
                                        SET hypertension = ?,
                                            mental_health_concerns = ?,
                                            dementia = ?,
                                            annual_well_visit = ?,
                                            initial_tv_completed = 1,
                                            initial_tv_completed_date = ?,
                                            provider_completed_initial_tv = 1,
                                            visit_type = ?,
                                            billing_code = ?,
                                            duration_minutes = ?,
                                            updated_date = CURRENT_TIMESTAMP
                                        WHERE onboarding_id = ?
                                    """,
                                        (
                                            task_entry.get(
                                                "confirm_hypertension", False
                                            ),
                                            task_entry.get(
                                                "confirm_mental_health", False
                                            ),
                                            task_entry.get("confirm_dementia", False),
                                            task_entry.get(
                                                "confirm_annual_wellness", False
                                            ),
                                            task_entry["date"],
                                            task_entry.get("visit_type", "Home Visit"),
                                            task_entry.get("billing_code", "99345"),
                                            task_entry.get("duration_minutes", 45),
                                            task_entry.get("onboarding_id"),
                                        ),
                                    )
                                    conn.commit()
                                    conn.close()
                                except Exception as e:
                                    st.error(
                                        f"Error updating specialist requirements and visit type: {e}"
                                    )

                            if success:
                                visit_type_display = task_entry.get(
                                    "visit_type", "Home Visit"
                                )
                                st.success(
                                    f"Initial {visit_type_display.lower()} completed for {task_entry['patient_name']}. Specialist requirements confirmed and patient removed from onboarding queue."
                                )

                                # Reset all clinical form fields to default values for onboarding tasks
                                onboarding_field_keys = [
                                    f"onb_er_visits_6mo_{i}",
                                    f"onb_hospitalizations_6mo_{i}",
                                    f"onb_subjective_risk_{i}",
                                    f"onb_mh_concerns_{i}",
                                    f"onb_provider_mh_schizophrenia_{i}",
                                    f"onb_provider_mh_depression_{i}",
                                    f"onb_provider_mh_anxiety_{i}",
                                    f"onb_provider_mh_stress_{i}",
                                    f"onb_provider_mh_adhd_{i}",
                                    f"onb_provider_mh_bipolar_{i}",
                                    f"onb_provider_mh_suicidal_{i}",
                                    f"onb_active_specialists_{i}",
                                    f"onb_code_status_{i}",
                                    f"onb_cognitive_function_{i}",
                                    f"onb_functional_status_{i}",
                                    f"onb_goc_value_{i}",
                                    f"onb_goals_of_care_{i}",
                                    f"onb_active_concerns_{i}",
                                    f"onb_notes_{i}",
                                    f"onb_patient_name_{i}",
                                    f"onb_task_type_{i}",
                                    f"onb_visit_type_{i}",
                                    f"onb_billing_code_{i}",
                                    f"onb_duration_{i}",
                                    f"onb_confirm_hypertension_{i}",
                                    f"onb_confirm_mental_health_{i}",
                                    f"onb_confirm_dementia_{i}",
                                    f"onb_confirm_annual_wellness_{i}",
                                ]

                                for field_key in onboarding_field_keys:
                                    if field_key in st.session_state:
                                        del st.session_state[field_key]

                                # Refresh the page to update the queue
                                st.rerun()
                            else:
                                st.error("Failed to save the task. Please try again.")
                        else:
                            st.error(
                                "Provider ID not found. Please contact administrator."
                            )
                    except Exception as e:
                        st.error(f"Error completing visit: {e}")
                else:
                    st.warning(
                        "Please fill in all required fields (Patient name, Task type, and Notes)."
                    )

            st.markdown("---")


def show_team_management_section():
    """Team Management section with Provider Patient Visit Breakdown and complete patient panel"""
    st.subheader(get_section_title(SectionTitles.PATIENT_ASSIGNMENTS))

    # --- Provider Patient Visit Breakdown Section ---
    st.markdown("#### 📊 Provider Patient Visit Breakdown")

    try:
        # Get all patient panel data
        patient_panel_data = (
            database.get_all_patient_panel()
            if hasattr(database, "get_all_patient_panel")
            else []
        )

        if patient_panel_data:
            patients_df = pd.DataFrame(patient_panel_data)

            # Normalize last_visit columns into a consistent 'Last Visit Date' string
            last_visit_cols = [
                col for col in patients_df.columns if "last_visit" in col.lower()
            ]
            for col in last_visit_cols:
                if col != "Last Visit Date":
                    patients_df[col] = patients_df[col].apply(
                        lambda x: pd.to_datetime(x, errors="coerce").strftime(
                            "%Y-%m-%d"
                        )
                        if pd.notnull(pd.to_datetime(x, errors="coerce"))
                        else None
                    )

            # Create 'Last Visit Date' column from available last_visit columns
            if "last_visit_date" in patients_df.columns:
                patients_df["Last Visit Date"] = patients_df["last_visit_date"].apply(
                    lambda x: pd.to_datetime(x, errors="coerce").strftime("%m-%d-%Y")
                    if pd.notnull(pd.to_datetime(x, errors="coerce"))
                    else None
                )
            elif "last_visit" in patients_df.columns:
                patients_df["Last Visit Date"] = patients_df["last_visit"].apply(
                    lambda x: pd.to_datetime(x, errors="coerce").strftime("%m-%d-%Y")
                    if pd.notnull(pd.to_datetime(x, errors="coerce"))
                    else None
                )
            else:
                patients_df["Last Visit Date"] = None

            # Fill missing Last Visit Date values from coordinator_tasks and provider_tasks
            def _fill_missing_last_visit_from_tasks(df, db):
                try:
                    missing_mask = df["Last Visit Date"].isna() | (
                        df["Last Visit Date"] == ""
                    )
                    missing_patients = df[missing_mask]
                    if missing_patients.empty:
                        return {}

                    pids = [
                        str(pid)
                        for pid in missing_patients["patient_id"].dropna().unique()
                    ]
                    if not pids:
                        return {}

                    placeholders = ", ".join(["?" for _ in pids])
                    select_templates = [
                        f"SELECT patient_id, date(date) as dt FROM coordinator_tasks WHERE patient_id IN ({placeholders})",
                        f"SELECT patient_id, date(date) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                        f"SELECT patient_id, date(dos) as dt FROM provider_tasks WHERE patient_id IN ({placeholders})",
                    ]

                    union_sql = "\nUNION ALL\n".join(select_templates)
                    final_sql = f"WITH dates AS ({union_sql}) SELECT patient_id, MAX(dt) as last_visit FROM dates WHERE dt IS NOT NULL GROUP BY patient_id"

                    params = pids * len(select_templates)

                    conn = database.get_db_connection()
                    try:
                        rows = conn.execute(final_sql, params).fetchall()
                    finally:
                        conn.close()

                    result = {}
                    for r in rows:
                        try:
                            if r[1]:
                                result[r[0]] = str(r[1])
                        except Exception:
                            continue
                    return result
                except Exception:
                    return {}

            # Attempt to enrich missing Last Visit Dates from task tables
            try:
                inferred = _fill_missing_last_visit_from_tasks(patients_df, database)
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

            patients_df["days_since_last_visit"] = patients_df.apply(get_delta, axis=1)

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

            # Decide which name columns to style
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

            # Categorize patients by visit recency
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
                    styled = style_names(df[breakdown_cols])
                    st.dataframe(styled, height=height, use_container_width=True)
                except Exception:
                    st.dataframe(
                        df[breakdown_cols], height=height, use_container_width=True
                    )

            # Check if provider information is available
            provider_col = None
            for col in ["provider_name", "provider", "assigned_provider"]:
                if col in patients_df.columns:
                    provider_col = col
                    break

            if provider_col:
                # Provider statistics summary
                providers = patients_df[provider_col].fillna("Unassigned").unique()
                provider_stats = []

                for provider in providers:
                    seen_30_count = (
                        len(seen_30[seen_30[provider_col].fillna("") == provider])
                        if not seen_30.empty and provider_col in seen_30.columns
                        else 0
                    )
                    seen_31_60_count = (
                        len(seen_31_60[seen_31_60[provider_col].fillna("") == provider])
                        if not seen_31_60.empty and provider_col in seen_31_60.columns
                        else 0
                    )
                    not_seen_60_count = (
                        len(
                            not_seen_60[
                                not_seen_60[provider_col].fillna("") == provider
                            ]
                        )
                        if not not_seen_60.empty and provider_col in not_seen_60.columns
                        else 0
                    )
                    total_count = seen_30_count + seen_31_60_count + not_seen_60_count

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
                    st.dataframe(stats_df, use_container_width=True, hide_index=True)
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
                        expander_title = f"🟢 {label} by Provider"
                    elif "1mo <> 2mo" in label:
                        expander_title = f"🟡 {label} by Provider"
                    else:
                        expander_title = f"🔴 {label} by Provider"

                    with st.expander(expander_title, expanded=False):
                        grouped = df_cat.groupby(provider_col)
                        if grouped.ngroups == 0:
                            st.info(f"No providers have patients in this category.")
                        else:
                            for prov, prov_df in grouped:
                                st.markdown(
                                    f"**Provider: {prov}** ({len(prov_df)} patients)"
                                )
                                if prov_df.empty:
                                    st.info(
                                        "No patients for this provider in this category."
                                    )
                                else:
                                    show_styled_table(prov_df, 300)
                                st.markdown("---")
            else:
                st.info("Provider information not available in patient data.")

            st.markdown("---")

            # --- Complete Patient Panel with Active/Inactive Sections ---
            st.markdown("#### 👥 Complete Patient Panel")

            # Define active status patterns
            active_statuses = ["Active", "Active-Geri", "Active-PCP", "Hospice"]

            # Split patients into active and inactive
            if "status" in patients_df.columns:
                # Active patients: status starts with 'Active' or is 'Hospice'
                active_patients = patients_df[
                    patients_df["status"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .isin(active_statuses)
                    | patients_df["status"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .str.startswith("Active")
                    | patients_df["status"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    == "Hospice"
                ].copy()

                # Inactive patients: everything else
                inactive_patients = patients_df[
                    ~(
                        patients_df["status"]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .isin(active_statuses)
                        | patients_df["status"]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .str.startswith("Active")
                        | patients_df["status"]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        == "Hospice"
                    )
                ].copy()
            else:
                # If no status column, treat all as active
                active_patients = patients_df.copy()
                inactive_patients = pd.DataFrame()

            # --- Active Patients Section ---
            st.markdown(f"##### 🟢 Active Patients ({len(active_patients)})")
            if not active_patients.empty:
                try:
                    styled_active = style_names(active_patients)
                    st.dataframe(styled_active, height=600, use_container_width=True)
                except Exception:
                    st.dataframe(active_patients, height=600, use_container_width=True)
            else:
                st.info("No active patients found.")

            # --- Inactive Patients Section (Expandable) ---
            with st.expander(
                f"🔴 Inactive Patients ({len(inactive_patients)})", expanded=False
            ):
                if not inactive_patients.empty:
                    try:
                        styled_inactive = style_names(inactive_patients)
                        st.dataframe(
                            styled_inactive, height=400, use_container_width=True
                        )
                    except Exception:
                        st.dataframe(
                            inactive_patients, height=400, use_container_width=True
                        )
                else:
                    st.info("No inactive patients found.")
        else:
            st.info("No patient data available for visit breakdown analysis.")
    except Exception as e:
        st.error(f"Error loading team management data: {e}")


# show_psl_monthly_view was removed per P0 scope (PSL Monthly View no longer used).
# The function body is preserved here commented out in case it needs to be restored later.
"""
def show_psl_monthly_view(user_id):
    # Original PSL Monthly View implementation commented out.
    pass
"""


def show_billing_status_section(user_id):
    """Display billing status for the provider - Billed vs Not Billed (P00)"""
    st.markdown(
        get_section_title("Billing Status - Billed vs Not Billed"),
        unsafe_allow_html=True,
    )

    try:
        # Get billing summary data
        billing_summary_df = database.get_provider_billing_summary(user_id)
        unbilled_tasks_df = database.get_provider_unbilled_tasks(user_id)

        if billing_summary_df.empty and unbilled_tasks_df.empty:
            st.info("No billing data available for this provider.")
            return

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_weeks = len(billing_summary_df)
            st.metric("Total Weeks", total_weeks)

        with col2:
            if not billing_summary_df.empty:
                billed_weeks = len(
                    billing_summary_df[billing_summary_df["paid"] == True]
                )
                st.metric("Billed Weeks", billed_weeks)
            else:
                st.metric("Billed Weeks", 0)

        with col3:
            if not billing_summary_df.empty:
                unbilled_weeks = len(
                    billing_summary_df[billing_summary_df["paid"] == False]
                )
                st.metric("Unbilled Weeks", unbilled_weeks)
            else:
                st.metric("Unbilled Weeks", 0)

        with col4:
            if total_weeks > 0:
                billing_rate = (billed_weeks / total_weeks) * 100
                st.metric("Billing Rate", f"{billing_rate:.1f}%")
            else:
                st.metric("Billing Rate", "0%")

        # Tabs for different views
        tab1, tab2 = st.tabs(["Weekly Summary", "Unbilled Tasks"])

        with tab1:
            st.markdown("#### Weekly Billing Summary")
            if not billing_summary_df.empty:
                # Add status filter
                status_filter = st.selectbox(
                    "Filter by Status",
                    ["All", "Billed", "Not Billed"],
                    key="billing_status_filter",
                )

                # Filter data based on selection
                filtered_df = billing_summary_df.copy()
                if status_filter == "Billed":
                    filtered_df = filtered_df[filtered_df["paid"] == True]
                elif status_filter == "Not Billed":
                    filtered_df = filtered_df[filtered_df["paid"] == False]

                # Display data with action buttons
                if not filtered_df.empty:
                    for idx, row in filtered_df.iterrows():
                        col1, col2, col3 = st.columns([3, 1, 1])

                        with col1:
                            billing_status = "Billed" if row["paid"] else "Not Billed"
                            st.write(
                                f"**Week {row['week_number']}, {row['year']}** ({row['week_start_date']} to {row['week_end_date']})"
                            )
                            st.write(
                                f"Tasks: {row['total_tasks_completed']}, Minutes: {row['total_time_spent_minutes']}, Status: **{billing_status}**"
                            )
                            st.write(
                                f"Billing Code: {row['billing_code']} - {row['billing_code_description']}"
                            )

                        with col2:
                            if not row["paid"]:
                                if st.button("Mark as Billed", key=f"bill_{idx}"):
                                    if database.update_billing_status(
                                        user_id, row["week_start_date"], True
                                    ):
                                        st.success("Marked as billed!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to update billing status")

                        with col3:
                            if row["paid"]:
                                if st.button("Mark as Unbilled", key=f"unbill_{idx}"):
                                    if database.update_billing_status(
                                        user_id, row["week_start_date"], False
                                    ):
                                        st.success("Marked as unbilled!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to update billing status")

                        st.divider()
                else:
                    st.info(f"No {status_filter.lower()} weeks found.")
            else:
                st.info("No weekly billing summary data available.")

        with tab2:
            st.markdown("#### Unbilled Tasks")
            if not unbilled_tasks_df.empty:
                # Display unbilled tasks
                display_df = unbilled_tasks_df.copy()
                display_df["task_date"] = pd.to_datetime(
                    display_df["task_date"]
                ).dt.strftime("%m-%d-%Y")

                # Show summary
                st.write(f"**Total Unbilled Tasks:** {len(display_df)}")

                # Display the data
                columns_to_show = [
                    "task_date",
                    "patient_name",
                    "task_description",
                    "minutes_of_service",
                    "billing_code",
                    "status",
                ]

                available_columns = [
                    col for col in columns_to_show if col in display_df.columns
                ]
                st.dataframe(
                    display_df[available_columns], use_container_width=True, height=400
                )
            else:
                st.info("No unbilled tasks found.")

    except Exception as e:
        st.error(f"Error loading billing status data: {e}")
        print(f"Billing status error: {e}")


def show_task_review_section(user_id):
    """Display monthly task review for providers with month selection and summary"""
    try:
        st.subheader("Task Review")

        # Get available provider task tables using SQLite syntax
        conn = database.get_db_connection()
        try:
            query = """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name LIKE 'provider_tasks_%'
            ORDER BY name DESC
            """

            result = conn.execute(query).fetchall()
            if not result:
                st.info("No monthly task tables found.")
                return

            # Extract available months from table names
            available_months = []
            for row in result:
                table_name = row[0]
                # Extract year and month from table name (e.g., provider_tasks_2025_08)
                parts = table_name.split("_")
                if len(parts) >= 4:
                    year = parts[2]
                    month = parts[3]
                    try:
                        month_name = calendar.month_name[int(month)]
                        display_name = f"{month_name} {year}"
                        available_months.append((display_name, table_name))
                    except (ValueError, IndexError):
                        continue

            if not available_months:
                st.info("No valid monthly task tables found.")
                return

            # View selection
            view_tab1, view_tab2 = st.tabs(["Task List", "Monthly Summary"])

            with view_tab1:
                # Original task list functionality
                selected_option = st.selectbox(
                    "Select Month:",
                    available_months,
                    format_func=lambda x: x[0],
                    key="task_list_month",
                )

                if selected_option:
                    selected_display, selected_table = selected_option

                # Get provider tasks for selected month using SQLite syntax
                provider_query = f"""
                SELECT
                    patient_name,
                    task_date,
                    minutes_of_service,
                    task_description
                FROM {selected_table}
                WHERE provider_id = ?
                ORDER BY task_date DESC
                """

                provider_tasks = conn.execute(provider_query, (user_id,)).fetchall()

                if provider_tasks:
                    # Convert to DataFrame
                    df = pd.DataFrame(
                        provider_tasks,
                        columns=["Patient Name", "DOS", "Duration", "Service Type"],
                    )

                    # Format the DOS column
                    df["DOS"] = pd.to_datetime(df["DOS"]).dt.strftime("%m-%d-%Y")

                    # Display summary
                    total_tasks = len(df)
                    total_duration = (
                        df["Duration"].sum() if "Duration" in df.columns else 0
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Tasks", total_tasks)
                    with col2:
                        st.metric("Total Duration (minutes)", total_duration)

                    # Display the tasks table
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Download option
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Tasks as CSV",
                        data=csv,
                        file_name=f"provider_tasks_{selected_display.replace(' ', '_')}.csv",
                        mime="text/csv",
                    )
                else:
                    st.info(f"No tasks found for {selected_display}")

            with view_tab2:
                # Monthly Summary functionality
                st.markdown("### Monthly Summary")

                # Month selection for summary
                selected_summary_option = st.selectbox(
                    "Select Month for Summary:",
                    available_months,
                    format_func=lambda x: x[0],
                    key="summary_month",
                )

                if selected_summary_option:
                    summary_display, summary_table = selected_summary_option

                    # Get summary data for the selected month
                    summary_query = f"""
                    SELECT
                        task_description,
                        COUNT(*) as task_count,
                        SUM(minutes_of_service) as total_minutes,
                        billing_code,
                        billing_code_description
                    FROM {summary_table}
                    WHERE provider_id = ?
                    GROUP BY task_description, billing_code, billing_code_description
                    ORDER BY total_minutes DESC, task_count DESC
                    """

                    summary_data = conn.execute(summary_query, (user_id,)).fetchall()

                    if summary_data:
                        # Convert to DataFrame
                        summary_df = pd.DataFrame(
                            summary_data,
                            columns=[
                                "Service Type",
                                "Task Count",
                                "Total Minutes",
                                "Billing Code",
                                "Billing Code Description",
                            ],
                        )

                        # Calculate totals
                        total_summary_tasks = summary_df["Task Count"].sum()
                        total_summary_minutes = summary_df["Total Minutes"].sum()

                        # Display key metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Tasks", total_summary_tasks)
                        with col2:
                            st.metric("Total Minutes", total_summary_minutes)
                        with col3:
                            # Calculate average duration per task
                            avg_minutes = (
                                total_summary_minutes / total_summary_tasks
                                if total_summary_tasks > 0
                                else 0
                            )
                            st.metric("Avg Minutes/Task", f"{avg_minutes:.1f}")

                        # Display the summary table
                        st.markdown("#### Service Type Summary")
                        st.dataframe(
                            summary_df, use_container_width=True, hide_index=True
                        )

                        # Download summary option
                        summary_csv = summary_df.to_csv(index=False)
                        st.download_button(
                            label="Download Summary as CSV",
                            data=summary_csv,
                            file_name=f"provider_summary_{summary_display.replace(' ', '_')}.csv",
                            mime="text/csv",
                        )

                        # Show billing code breakdown
                        st.markdown("#### Billing Code Breakdown")
                        billing_breakdown = (
                            summary_df.groupby("Billing Code")
                            .agg({"Task Count": "sum", "Total Minutes": "sum"})
                            .reset_index()
                        )

                        st.dataframe(
                            billing_breakdown, use_container_width=True, hide_index=True
                        )
                    else:
                        st.info(f"No summary data found for {summary_display}")

        finally:
            conn.close()

    except Exception as e:
        st.error(f"Error loading task review data: {e}")
        print(f"Task review error: {e}")


def show_daily_task_log(user_id, role="provider"):
    """Display Daily Task Log with today's tasks, metrics, and submission functionality"""
    try:
        st.subheader("Daily Task Log")

        # Get today's tasks
        todays_tasks = database.get_todays_tasks(user_id, role)

        if not todays_tasks:
            st.info("No tasks found for today.")
            # Still show metrics (all zero)
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Tasks Today", 0)
            col2.metric("Unique Patients", 0)
            col3.metric("Total Minutes", 0)
            return

        # Convert to DataFrame for display
        tasks_df = pd.DataFrame(todays_tasks)

        # Calculate metrics
        total_tasks = len(tasks_df)
        unique_patients = (
            tasks_df["patient_name"].nunique()
            if "patient_name" in tasks_df.columns
            else 0
        )
        total_minutes = (
            tasks_df["duration_minutes"].sum()
            if "duration_minutes" in tasks_df.columns
            else 0
        )

        # Display metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks Today", total_tasks)
        col2.metric("Unique Patients", unique_patients)
        col3.metric("Total Minutes", total_minutes)

        # Prepare display columns
        display_columns = []
        if "task_date" in tasks_df.columns:
            display_columns.append("Time")
        if "patient_name" in tasks_df.columns:
            display_columns.append("Patient ID / Name")
        if "task_type" in tasks_df.columns:
            display_columns.append("Task Type")
        if "duration_minutes" in tasks_df.columns:
            display_columns.append("Minutes Spent")
        if "notes" in tasks_df.columns:
            display_columns.append("Notes")

        # Rename columns for display
        column_mapping = {
            "task_date": "Time",
            "patient_name": "Patient ID / Name",
            "task_type": "Task Type",
            "duration_minutes": "Minutes Spent",
            "notes": "Notes",
        }

        display_df = tasks_df.rename(columns=column_mapping)

        # Add task_id column for tracking edits
        if "provider_task_id" in display_df.columns:
            display_df["_task_id"] = display_df["provider_task_id"]
        elif "coordinator_task_id" in display_df.columns:
            display_df["_task_id"] = display_df["coordinator_task_id"]
        else:
            display_df["_task_id"] = None

        # Format time column
        if "Time" in display_df.columns:
            display_df["Time"] = pd.to_datetime(display_df["Time"]).dt.strftime("%H:%M")

        # Show editable table - always editable to allow corrections
        st.markdown("#### Today's Tasks")
        st.markdown("*Edit minutes, task type, or notes if corrections are needed*")

        # Show editable table with hidden _task_id column for tracking
        editable_columns = display_columns + ["_task_id"]
        edited_df = st.data_editor(
            display_df[editable_columns],
            use_container_width=True,
            hide_index=True,
            key=f"daily_tasks_{user_id}_{role}",
            num_rows="fixed",
            disabled=["_task_id"],  # Disable only the _task_id column, not the entire table
        )

        # Handle edits using database.update_task_details function
        if edited_df is not None and not edited_df.equals(
            display_df[editable_columns]
        ):
            # Save each changed row using update_task_details function
            updates_count = 0
            for idx, edited_row in edited_df.iterrows():
                original_row = display_df[editable_columns].iloc[idx]

                # Get task_id from the hidden column
                task_id = original_row["_task_id"]

                # Skip if no task_id or it's NaN
                if pd.isna(task_id):
                    continue

                # Build updates dict with changed fields
                updates = {}

                # Check minutes_spent
                if "Minutes Spent" in edited_df.columns:
                    orig_min = original_row["Minutes Spent"]
                    edited_min = edited_row["Minutes Spent"]
                    if pd.notna(edited_min) and str(edited_min) != str(orig_min):
                        updates["duration_minutes"] = edited_min

                # Check task_type
                if "Task Type" in edited_df.columns:
                    orig_type = original_row["Task Type"]
                    edited_type = edited_row["Task Type"]
                    if pd.notna(edited_type) and str(edited_type) != str(orig_type):
                        updates["task_type"] = edited_type

                # Check notes
                if "Notes" in edited_df.columns:
                    orig_notes = original_row["Notes"]
                    edited_notes = edited_row["Notes"]
                    if pd.notna(edited_notes) and str(edited_notes) != str(orig_notes):
                        updates["notes"] = edited_notes

                # Apply update if there are changes
                if updates:
                    success = database.update_task_details(task_id, role, updates)
                    if success:
                        updates_count += 1

            if updates_count > 0:
                st.success(f"✅ Saved {updates_count} task updates to database!")
                st.rerun()  # Refresh table to show updated data
            else:
                st.info("💾 No changes detected.")

        # Submit button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("📤 Submit Day", type="primary", use_container_width=True):
                # Show confirmation dialog
                confirm_submit = st.checkbox(
                    "I confirm that today's task log is accurate and complete.",
                    key=f"confirm_submit_{user_id}",
                )

                if confirm_submit:
                    # Submit the day's tasks
                    success = database.submit_daily_tasks(user_id, role)
                    if success:
                        st.success(
                            "✅ Daily task log submitted successfully!"
                        )
                        st.balloons()
                        time.sleep(2)  # Give user time to see success message
                        st.rerun()
                    else:
                        st.error("❌ Failed to submit daily tasks. Please try again.")
                else:
                    st.warning(
                            "Please confirm submission by checking the box above."
                        )

    except Exception as e:
        st.error(f"Error loading daily task log: {e}")
        print(f"Daily task log error: {e}")
