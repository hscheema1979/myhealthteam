import streamlit as st
import pandas as pd
from src import database

def show_phone_review_entry(mode, user_id, provider_id=None):
    """
    Modular phone review entry UI.
    mode: 'cm' (Care Manager) or 'cp' (Care Provider)
    user_id: current user's user_id
    provider_id: (optional) provider to show patients for (for CM mode)
    """
    if mode == 'cm':
        # CM: select provider, then patient
        providers = database.get_users_by_role(33)  # 36 = Care Provider
        provider_options = [f"{p['full_name']} ({p['username']})" for p in providers]
        provider_map = {f"{p['full_name']} ({p['username']})": p['user_id'] for p in providers}
        selected_provider = st.selectbox("Select Provider", provider_options, key="phone_review_provider_select")
        selected_provider_id = provider_map[selected_provider]
        # Get active patients for selected provider
        patient_data_list = database.get_provider_patient_panel_enhanced(selected_provider_id)
    else:
        # CP: provider is current user
        selected_provider_id = user_id if provider_id is None else provider_id
        st.info(f"Provider: {database.get_user_by_id(selected_provider_id)['full_name']}")
        patient_data_list = database.get_provider_patient_panel_enhanced(selected_provider_id)

    # Only show active patients
    allowed_statuses = ['Active', 'Active-Geri', 'Active-PCP']
    active_patients = [p for p in patient_data_list if (p.get('status', '') or '').strip() in allowed_statuses]
    patient_names = [f"{p.get('first_name','').strip()} {p.get('last_name','').strip()}".strip() for p in active_patients]
    patient_map = {f"{p.get('first_name','').strip()} {p.get('last_name','').strip()}": p for p in active_patients}

    if not patient_names:
        st.info("No active patients available for phone review.")
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
