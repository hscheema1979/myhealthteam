import streamlit as st
import pandas as pd
from src.database import get_user_by_id, get_users_by_role, get_tasks_by_user, get_coordinator_performance_metrics

def show():
    st.title("Coordinator Manager Dashboard")

    # Get the current user's ID from the session state
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("Please log in to view this page.")
        return

    # Fetch the coordinator manager's information
    manager_info = get_user_by_id(user_id)
    if not manager_info:
        st.error("Could not retrieve your information.")
        return

    st.write(f"Welcome, {manager_info['username']}!")

    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs([
        "Overview", 
        "Team Management", 
        "Reports"
    ])

    # Tab 1: Overview
    with tab1:
        st.subheader("📊 Coordinator Team Overview")
        
        # Fetch the care coordinators managed by this manager
        managed_coordinators = get_users_by_role("Care Coordinator")
        if not managed_coordinators:
            st.info("There are no care coordinators to manage.")
            return

        # Coordinator metrics
        col1, col2, col3, col4 = st.columns(4)
        total_coordinators = len(managed_coordinators)
        active_coordinators = len([c for c in managed_coordinators if c.get('status') == 'Active'])
        
        col1.metric("Total Coordinators", total_coordinators)
        col2.metric("Active Coordinators", active_coordinators)
        col3.metric("Pending Reviews", "TBD")  # Placeholder
        col4.metric("This Month Tasks", "TBD")  # Placeholder

        st.subheader("Managed Care Coordinators")
        if managed_coordinators:
            coordinator_data = []
            for coordinator in managed_coordinators:
                coordinator_data.append({
                    'Name': coordinator['username'],
                    'Full Name': coordinator.get('full_name', ''),
                    'Status': coordinator.get('status', 'Unknown'),
                    'Email': coordinator.get('email', '')
                })
            
            coordinator_df = pd.DataFrame(coordinator_data)
            st.dataframe(coordinator_df, use_container_width=True)

        # Display tasks for each managed care coordinator
        st.subheader("Recent Coordinator Tasks")
        for coordinator in managed_coordinators[:5]:  # Limit to first 5 coordinators
            with st.expander(f"Tasks for {coordinator['username']}"):
                tasks = get_tasks_by_user(coordinator['id'])
                if tasks:
                    task_data = []
                    for task in tasks[:10]:  # Limit to recent 10 tasks
                        task_data.append({
                            'Description': task.get('description', ''),
                            'Status': task.get('status', ''),
                            'Date': task.get('task_date', ''),
                            'Type': task.get('task_type', '')
                        })
                    if task_data:
                        task_df = pd.DataFrame(task_data)
                        st.dataframe(task_df, use_container_width=True)
                else:
                    st.write("No tasks found for this coordinator.")

    # Tab 2: Team Management
    with tab2:
        st.subheader("👥 Team Management")
        
        # Import and display performance summaries
        try:
            from src.utils.performance_components import (
                display_coordinator_monthly_summary,
                display_coordinator_weekly_summary,
                display_patient_assignments_by_workflow
            )
            
            # Performance Section
            st.header("📊 Coordinator Performance")
            st.markdown("Monitor and analyze coordinator performance metrics across your team.")
            
            # Coordinator Monthly Performance Summary
            display_coordinator_monthly_summary(show_all=True, title="📈 Coordinator Monthly Performance Summary")
            
            st.divider()
            
            # Coordinator Weekly Performance Summary
            display_coordinator_weekly_summary(show_all=True, title="📅 Coordinator Weekly Performance Summary")
            
            st.divider()
            
            # Patient Assignments Section
            st.header("👥 Patient Assignments")
            st.markdown("Review patient assignments and onboarding workflow progress for your coordinator team.")
            
            # Show patient assignments for each coordinator
            for coordinator in managed_coordinators[:3]:  # Show for first 3 coordinators to avoid overload
                with st.expander(f"Patient Assignments - {coordinator.get('full_name', coordinator['username'])}"):
                    try:
                        # Get coordinator user ID for assignments
                        coordinator_user_id = coordinator.get('user_id', coordinator['id'])
                        display_patient_assignments_by_workflow(
                            user_id=coordinator_user_id,
                            role_id=36,  # Care Coordinator role
                            title=f"Assignments for {coordinator.get('full_name', coordinator['username'])}"
                        )
                    except Exception as e:
                        st.error(f"Error loading assignments for {coordinator['username']}: {e}")
            
            if len(managed_coordinators) > 3:
                st.info(f"Showing assignments for first 3 coordinators. Total coordinators: {len(managed_coordinators)}")
                
        except ImportError as e:
            st.error(f"Error importing performance components: {e}")
            # Fallback to basic performance metrics
            st.subheader("Coordinator Performance Metrics")
            # Note: get_coordinator_performance_metrics expects user_id parameter
            try:
                metrics = get_coordinator_performance_metrics(user_id)  # Use manager's user_id as fallback
                if metrics:
                    metrics_df = pd.DataFrame(metrics)
                    st.dataframe(metrics_df, use_container_width=True)
                else:
                    st.info("No performance metrics available for coordinators.")
            except Exception as e:
                st.error(f"Error getting coordinator performance metrics: {e}")
    
    # Tab 3: Reports
    with tab3:
        st.subheader("📈 Reports & Analytics")
        
        st.info("🚧 Advanced reporting features coming soon...")
        
        # Placeholder for future reporting features
        st.markdown("""
        **Upcoming Features:**
        - Coordinator performance trends
        - Team productivity analysis
        - Patient coordination metrics
        - Workflow completion rates
        - Custom date range analysis
        """)
        
        # Basic metrics placeholder
        st.subheader("Basic Team Metrics")
        if managed_coordinators:
            total_tasks_all_coordinators = 0
            for coordinator in managed_coordinators:
                tasks = get_tasks_by_user(coordinator['id'])
                total_tasks_all_coordinators += len(tasks) if tasks else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Team Tasks", total_tasks_all_coordinators)
            col2.metric("Average per Coordinator", round(total_tasks_all_coordinators / len(managed_coordinators), 1) if managed_coordinators else 0)
            col3.metric("Team Utilization", "TBD%")  # Placeholder