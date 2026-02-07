import streamlit as st
import pandas as pd
from src import database

def show_phone_review_entry(mode, user_id, provider_id=None, filtered_patients=None):
    """
    Modular phone review entry UI.
    mode: 'cm' (Care Manager) or 'cp' (Care Provider)
    user_id: current user's user_id
    provider_id: (optional) provider to show patients for (for CM mode)
    filtered_patients: (optional) pre-filtered patient list from patient panel (respects filters)
    """
    # Get all providers for filters
    all_providers = database.get_users_by_role(33)  # 33 = Care Provider

    if mode == 'cm':
        # CM: select provider, then patient
        providers = database.get_users_by_role(33)  # 33 = Care Provider
        provider_options = [f"{p['full_name']} ({p['username']})" for p in providers]
        provider_map = {f"{p['full_name']} ({p['username']})": p['user_id'] for p in providers}
        selected_provider = st.selectbox("Select Provider", provider_options, key="phone_review_provider_select")
        selected_provider_id = provider_map[selected_provider]
        # CM mode always uses all patients for provider selection
        patient_data_list = database.get_all_patient_panel()
    else:
        # CP: provider is current user
        selected_provider_id = user_id if provider_id is None else provider_id
        # Get all patient data for filtering (independent from patient panel filters)
        patient_data_list = database.get_all_patient_panel()

    # --- Add Search and Filter UI at the top ---
    st.markdown("#### Search and Filter Patients")

    # Create filter columns
    col_search, col_filter, col_status = st.columns([2, 1, 1])

    with col_search:
        search_query = st.text_input(
            "Search by patient name or ID",
            key="phone_review_patient_search",
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

        # Get current user's name for default selection
        current_user_name = None
        current_provider_id = None
        try:
            current_user = database.get_user_by_id(user_id)
            if current_user:
                try:
                    full_name = current_user["full_name"]
                    username = current_user["username"]
                    current_provider_id = current_user["user_id"]
                except (KeyError, TypeError):
                    full_name = None
                    username = None
                    current_provider_id = None

                current_user_name = (
                    full_name if full_name else username if username else "Unknown User"
                )
        except Exception:
            pass

        # Set default selection - current user's patients only
        default_selection = (
            [current_user_name]
            if current_user_name and current_user_name in provider_options
            else ["All Providers"]
        )

        selected_providers = st.multiselect(
            "Filter by Provider(s)",
            provider_options,
            key="phone_review_provider_filter",
            default=default_selection,
            help="Select one or more providers to view their patients. Default shows your patients.",
        )

    with col_status:
        # Get all unique patient statuses for the filter dropdown
        all_statuses = sorted(
            set(
                (p.get("status", "") or "").strip()
                for p in patient_data_list
                if (p.get("status", "") or "").strip()
            )
        )

        # Default to common active statuses
        default_statuses = ["Active", "Active-Geri", "Active-PCP", "HOSPICE"]
        # Ensure default statuses exist in the available options
        default_statuses = [s for s in default_statuses if s in all_statuses]

        selected_statuses = st.multiselect(
            "Filter by Patient Status",
            all_statuses,
            key="phone_review_status_filter",
            default=default_statuses if default_statuses else None,
            help="Select one or more patient statuses to filter. Default shows active and hospice patients.",
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
    filtered_review_patients = patient_data_list

    # Filter by search query
    if search_query and search_query.strip():
        q = search_query.lower().strip()
        filtered_review_patients = [
            p
            for p in filtered_review_patients
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

        # Apply provider filter
        if selected_provider_ids or show_unassigned:
            filtered_by_provider = []
            for p in filtered_review_patients:
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

            filtered_review_patients = filtered_by_provider

    # Filter by patient status
    if selected_statuses:
        filtered_by_status = []
        for p in filtered_review_patients:
            patient_status = (p.get("status", "") or "").strip()
            if patient_status in selected_statuses:
                filtered_by_status.append(p)
        filtered_review_patients = filtered_by_status

    # Use filtered results
    patient_data_list = filtered_review_patients

    # Only show active patients (based on filtered results)
    allowed_statuses = ['Active', 'Active-Geri', 'Active-PCP', 'Hospice', 'HOSPICE']
    active_patients = [p for p in patient_data_list if (p.get('status', '') or '').strip() in allowed_statuses]
    patient_names = [f"{p.get('first_name','').strip()} {p.get('last_name','').strip()}".strip() for p in active_patients]
    patient_map = {f"{p.get('first_name','').strip()} {p.get('last_name','').strip()}": p for p in active_patients}

    # Show patient count
    if patient_names:
        st.info(f"Showing {len(patient_names)} eligible patients for phone review.")
    else:
        st.info("No active patients available for phone review with the current filters.")
        return

    selected_patient = st.selectbox("Select Patient", patient_names, key="phone_review_patient_select")
    # Phone review form fields
    st.markdown("### Phone Review Entry")
    with st.form("phone_review_form"):
        review_date = st.date_input("Date", value=pd.to_datetime('today'))
        duration = st.number_input("Duration (min)", min_value=1, value=10)
        notes = st.text_area("Notes", height=80)
        submitted = st.form_submit_button("Log Phone Review")
        if submitted:
            patient = patient_map.get(selected_patient)
            if not patient:
                st.error("Selected patient not found. Please try again.")
                return
            patient_id = patient.get('patient_id') or patient.get('id') or selected_patient
            provider_user_id = selected_provider_id
            # Write to coordinator_tasks (as provider is acting as coordinator for phone review)
            ok1 = database.save_coordinator_task(
                coordinator_id=provider_user_id,
                patient_id=patient_id,
                task_date=review_date,
                task_description="Phone Review",
                duration_minutes=duration,
                notes=notes
            )
            # Write to provider_tasks and provider_tasks_YYYY_MM with Not_Billable
            ok2 = database.save_daily_task(
                provider_id=provider_user_id,
                patient_id=patient_id,
                task_date=review_date,
                task_description="Phone Review",
                notes=notes,
                billing_code="Not_Billable"
            )
            if ok1 and ok2:
                st.success(f"Phone review for {selected_patient} logged to coordinator and provider tasks.")
            else:
                st.error("Error logging phone review. Please check your entry and try again.")
