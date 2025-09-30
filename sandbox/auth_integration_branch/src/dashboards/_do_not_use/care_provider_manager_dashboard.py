import streamlit as st
import pandas as pd
from src.database import get_user_by_id, get_users_by_role, get_tasks_by_user, get_provider_performance_metrics

def show():
    st.title("Care Provider Manager Dashboard")

    # Get the current user's ID from the session state
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("Please log in to view this page.")
        return

    # Fetch the care provider manager's information
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
        st.subheader("📊 Provider Team Overview")
        
        # Fetch the care providers managed by this manager
        managed_providers = get_users_by_role("Care Provider")
        if not managed_providers:
            st.info("There are no care providers to manage.")
            return

        # Provider metrics
        col1, col2, col3, col4 = st.columns(4)
        total_providers = len(managed_providers)
        active_providers = len([p for p in managed_providers if p.get('status') == 'Active'])
        
        col1.metric("Total Providers", total_providers)
        col2.metric("Active Providers", active_providers)
        col3.metric("Pending Reviews", "TBD")  # Placeholder
        col4.metric("This Month Tasks", "TBD")  # Placeholder

        st.subheader("Managed Care Providers")
        if managed_providers:
            provider_data = []
            for provider in managed_providers:
                provider_data.append({
                    'Name': provider['username'],
                    'Full Name': provider.get('full_name', ''),
                    'Status': provider.get('status', 'Unknown'),
                    'Email': provider.get('email', '')
                })
            
            provider_df = pd.DataFrame(provider_data)
            st.dataframe(provider_df, use_container_width=True)

        # Display tasks for each managed care provider
        st.subheader("Recent Provider Tasks")
        for provider in managed_providers[:5]:  # Limit to first 5 providers
            with st.expander(f"Tasks for {provider['username']}"):
                tasks = get_tasks_by_user(provider['id'])
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
                    st.write("No tasks found for this provider.")

    # Tab 2: Team Management
    with tab2:
        st.subheader("🏥 Team Management")
        
        # Import and display performance summaries
        try:
            from src.utils.performance_components import (
                display_provider_monthly_summary,
                display_provider_weekly_summary,
                display_patient_assignments_by_workflow
            )
            
            # Performance Section
            st.header("📊 Provider Performance")
            st.markdown("Monitor and analyze provider performance metrics across your team.")
            
            # Provider Monthly Performance Summary
            display_provider_monthly_summary(show_all=True, title="📈 Provider Monthly Performance Summary")
            
            st.divider()
            
            # Provider Weekly Performance Summary
            display_provider_weekly_summary(show_all=True, title="📅 Provider Weekly Performance Summary")
            
            st.divider()
            
            # Patient Assignments Section
            st.header("👥 Patient Assignments")
            st.markdown("Review patient assignments and onboarding workflow progress for your provider team.")
            
            # Show patient assignments for each provider
            for provider in managed_providers[:3]:  # Show for first 3 providers to avoid overload
                with st.expander(f"Patient Assignments - {provider.get('full_name', provider['username'])}"):
                    try:
                        # Get provider user ID for assignments
                        provider_user_id = provider.get('user_id', provider['id'])
                        display_patient_assignments_by_workflow(
                            user_id=provider_user_id,
                            role_id=33,  # Care Provider role
                            title=f"Assignments for {provider.get('full_name', provider['username'])}"
                        )
                    except Exception as e:
                        st.error(f"Error loading assignments for {provider['username']}: {e}")
            
            if len(managed_providers) > 3:
                st.info(f"Showing assignments for first 3 providers. Total providers: {len(managed_providers)}")
                
        except ImportError as e:
            st.error(f"Error importing performance components: {e}")
            # Fallback to basic performance metrics
            st.subheader("Provider Performance Metrics")
            metrics = get_provider_performance_metrics()
            if metrics:
                metrics_df = pd.DataFrame(metrics)
                st.dataframe(metrics_df, use_container_width=True)
            else:
                st.info("No performance metrics available for providers.")
    
    # Tab 3: Reports
    with tab3:
        st.subheader("📈 Reports & Analytics")
        
        st.info("🚧 Advanced reporting features coming soon...")
        
        # Placeholder for future reporting features
        st.markdown("""
        **Upcoming Features:**
        - Provider performance trends
        - Team utilization reports
        - Patient outcome metrics
        - Billing and productivity reports
        - Custom date range analysis
        """)
        
        # Basic metrics placeholder
        st.subheader("Basic Team Metrics")
        if managed_providers:
            total_tasks_all_providers = 0
            for provider in managed_providers:
                tasks = get_tasks_by_user(provider['id'])
                total_tasks_all_providers += len(tasks) if tasks else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Team Tasks", total_tasks_all_providers)
            col2.metric("Average per Provider", round(total_tasks_all_providers / len(managed_providers), 1) if managed_providers else 0)
            col3.metric("Team Utilization", "TBD%")  # Placeholder