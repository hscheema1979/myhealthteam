import streamlit as st
import pandas as pd
from src import database as db
from src.dashboards import admin_user_management

def show():
    st.title("Admin Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs(["Performance Metrics", "User Management", "System Metrics", "User Activity"])

    with tab1:
        st.subheader("Coordinator Performance Metrics")
        coordinator_metrics = db.get_coordinator_performance_metrics(st.session_state['user_id'])
        if coordinator_metrics:
            st.dataframe(coordinator_metrics)
        else:
            st.write("No coordinator performance metrics available.")

    with tab2:
        st.subheader("Provider Performance Metrics")
        provider_metrics = db.get_provider_performance_metrics(st.session_state['user_id'])
        if provider_metrics:
            st.dataframe(provider_metrics)
        else:
            st.write("No provider performance metrics available.")

    with tab2:
        admin_user_management.show()

    with tab3:
        st.subheader("System Metrics")
        st.info("System metrics will be displayed here.")

    with tab4:
        st.subheader("User Activity")
        st.info("User activity logs will be displayed here.")

    st.subheader("User List")
    users = db.get_all_users()
    if users:
        for user in users:
            st.write(f"{user['full_name']}")
    else:
        st.write("No users found.")
