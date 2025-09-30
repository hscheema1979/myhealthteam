import streamlit as st
import pandas as pd
from src import database
from src.database import get_coordinator_performance_metrics
from datetime import date

def show():
    st.title("Care Coordinator Dashboard")

    if "user_full_name" not in st.session_state:
        st.session_state.user_full_name = ""

    user_id = st.session_state.user_id
    # provider_id = database.get_provider_id_from_user_id(user_id)
    # if provider_id is None:
    #     st.error("Provider ID not found for the current user.")
    #     return
    patient_assignments = database.get_user_patient_assignments(user_id)

    if patient_assignments:
        st.subheader("Your Patient Assignments")
        # Fetch full patient details for each assigned patient
        full_patient_details = []
        for assignment in patient_assignments:
            patient_id = assignment['patient_id']
            patient_details = database.get_patient_details_by_id(patient_id)
            if patient_details:
                full_patient_details.append(dict(patient_details))

        patient_df = pd.DataFrame(full_patient_details)
        if not patient_df.empty:
            patient_df['full_address'] = patient_df.apply(lambda row: f"{row['address_street']}, {row['address_city']}, {row['address_state']} {row['address_zip']}", axis=1)
            st.dataframe(patient_df[['first_name', 'last_name', 'phone_primary', 'email', 'full_address']])
        else:
            st.info("No patients assigned to this coordinator.")
        # Create a list of patient names for the selectbox
        patient_names = [f"{p['first_name']} {p['last_name']}" for p in full_patient_details]

        st.subheader("Daily Task Entries")

        if 'coordinator_daily_tasks_data' not in st.session_state:
            st.session_state.coordinator_daily_tasks_data = [{}] * 10


        if st.button("Add another task entry"):
            st.session_state.coordinator_daily_tasks_data.append({})
            st.rerun()

    else:
        st.info("You have no patients assigned.")

    # st.subheader("Your Performance Metrics")
    # coordinator_metrics = get_coordinator_performance_metrics(user_id)

    # if coordinator_metrics:
    #     metrics_df = pd.DataFrame([coordinator_metrics])
    #     st.dataframe(metrics_df)
    # else:
    #     st.info("No performance metrics available yet.")
