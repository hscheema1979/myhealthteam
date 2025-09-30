import streamlit as st

def show():
    st.title("Lead Coordinator Dashboard")

    # Get the current user's ID from the session state
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("Please log in to view this page.")
        return

    # Fetch the lead coordinator's information
    lead_coordinator_info = get_user_by_id(user_id)
    if not lead_coordinator_info:
        st.error("Could not retrieve your information.")
        return

    st.write(f"Welcome, {lead_coordinator_info['username']}!")

    # Fetch all care coordinators
    coordinators = get_users_by_role("Care Coordinator")
    coordinator_usernames = [c['username'] for c in coordinators]

    st.subheader("Assign Task to Care Coordinator")
    with st.form("assign_task_form"):
        selected_coordinator_username = st.selectbox("Select Care Coordinator", coordinator_usernames)
        task_description = st.text_area("Task Description")
        patient_name = st.text_input("Patient Name")
        submitted = st.form_submit_button("Assign Task")

        if submitted:
            # In a real application, you would save this to the database
            st.success(f"Task assigned to {selected_coordinator_username} for patient {patient_name}")