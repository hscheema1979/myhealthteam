import streamlit as st
import sqlite3
from src.database import (
    get_db_connection, get_user_roles, get_users, add_user, get_user_by_id,
    get_users_by_role, get_tasks_by_user, get_user_patient_assignments,
    get_coordinator_performance_metrics, get_provider_performance_metrics,
    get_tasks_billing_codes,
    get_care_plan, update_care_plan, get_provider_id_from_user_id, get_patient_details_by_id
)
from src import database
from src.core_utils import get_user_role_ids
from src.dashboards import admin_dashboard, onboarding_dashboard, data_entry_dashboard, care_provider_dashboard_enhanced, care_coordinator_dashboard_enhanced

def main():
    st.set_page_config(layout="wide")
    st.sidebar.title("ZEN Medical")
    

    # User selection only (no role selection)
    users = database.get_users()
    if users:
        user_names = [user['username'] for user in users]
        selected_user_name = st.sidebar.selectbox("Select User", user_names)

        if selected_user_name:
            selected_user = next((user for user in users if user['username'] == selected_user_name), None)
            if selected_user:
                st.session_state['user_id'] = selected_user['user_id']
                st.session_state['user_full_name'] = selected_user['full_name']
                # Get all role IDs for the user
                user_role_ids = get_user_role_ids(selected_user['user_id'])
                st.session_state['user_role_ids'] = user_role_ids
    else:
        st.sidebar.warning("No users found in the system.")
        # Clear any existing user session state if no users found
        for key in ['user_id', 'user_full_name', 'user_role_ids']:
            if key in st.session_state:
                del st.session_state[key]


    # Display dashboard based on user and their roles
    if 'user_id' in st.session_state and 'user_role_ids' in st.session_state:
        user_id = st.session_state['user_id']
        user_role_ids = st.session_state['user_role_ids']

        # Prioritize dashboard by role precedence (Provider > Coordinator > Admin > Onboarding > Data Entry)
        if 33 in user_role_ids:
            care_provider_dashboard_enhanced.show(user_id, user_role_ids)
        elif 36 in user_role_ids:
            care_coordinator_dashboard_enhanced.show(user_id, user_role_ids)
        elif 34 in user_role_ids:
            admin_dashboard.show()
        elif 35 in user_role_ids:
            onboarding_dashboard.show()
        elif 39 in user_role_ids:
            data_entry_dashboard.show()
        else:
            st.error(f"User has no recognized dashboard role. Roles: {user_role_ids}")
            st.info("Please contact your administrator.")
    else:
        st.info("Select a user to begin.")

# Initialize the database

if __name__ == "__main__":
    main()