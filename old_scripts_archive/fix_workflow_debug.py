#!/usr/bin/env python3
"""
Enhanced admin dashboard with better debugging for workflow reassignment
"""

import streamlit as st
import pandas as pd
from src import database as db
from src.utils.workflow_utils import get_workflows_for_reassignment, get_reassignment_summary

def enhanced_workflow_reassignment_section(user_id, user_role_ids):
    """
    Enhanced workflow reassignment section with detailed debugging info
    """
    
    st.subheader("🔧 Workflow Reassignment (Enhanced Debug Version)")
    st.markdown("Admin-level workflow management with bulk reassignment capabilities")
    
    # Add debug info section
    with st.expander("🐛 Debug Information", expanded=True):
        st.write(f"User ID: {user_id}")
        st.write(f"User Role IDs: {user_role_ids}")
        st.write(f"Is Admin: {34 in user_role_ids}")
        st.write(f"Is Coordinator Manager: {40 in user_role_ids}")
    
    try:
        # Log the exact parameters being passed
        st.write(f"**DEBUG**: Calling get_workflows_for_reassignment(user_id={user_id}, user_role_ids={user_role_ids})")
        
        # Get workflows with detailed error handling
        workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
        
        st.write(f"**DEBUG**: Returned DataFrame with shape {workflows_df.shape}")
        st.write(f"**DEBUG**: DataFrame empty: {workflows_df.empty}")
        
        if workflows_df.empty:
            st.warning("No workflows returned from get_workflows_for_reassignment")
            
            # Additional debugging
            with st.expander("🔍 Additional Debug Info"):
                # Check database directly
                conn = db.get_db_connection()
                try:
                    result = conn.execute("SELECT COUNT(*) as count FROM workflow_instances WHERE workflow_status = 'Active'")
                    db_count = result.fetchone()['count']
                    st.write(f"Active workflows in database: {db_count}")
                    
                    # Test the admin query directly
                    if 34 in user_role_ids or 40 in user_role_ids:
                        admin_query = """
                            SELECT COUNT(*) as count
                            FROM workflow_instances wi
                            WHERE workflow_status = 'Active'
                        """
                        result = conn.execute(admin_query).fetchone()
                        admin_count = result['count']
                        st.write(f"Admin query would return: {admin_count} workflows")
                        
                        # Show a few sample workflows
                        sample_query = """
                            SELECT instance_id, template_name, patient_name, coordinator_name, workflow_status
                            FROM workflow_instances 
                            WHERE workflow_status = 'Active'
                            LIMIT 3
                        """
                        samples = conn.execute(sample_query).fetchall()
                        st.write("Sample workflows from database:")
                        for sample in samples:
                            st.write(f"  - {dict(sample)}")
                            
                finally:
                    conn.close()
            
            st.info("No active workflows available for reassignment.")
            
        else:
            st.success(f"Found {len(workflows_df)} workflows for reassignment")
            
            # Show summary
            summary = get_reassignment_summary(workflows_df)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Workflows", summary['total_workflows'])
            with col2:
                unique_coordinators = len(summary['by_coordinator'])
                st.metric("Active Coordinators", unique_coordinators)
            with col3:
                avg_steps = summary['avg_steps']
                st.metric("Average Step", f"{avg_steps:.1f}")
            
            # Show workflow distribution
            with st.expander("📊 Assignment Distribution", expanded=False):
                col_summary1, col_summary2 = st.columns(2)
                with col_summary1:
                    st.markdown("**By Coordinator**")
                    for coord, count in summary['by_coordinator'].items():
                        st.markdown(f"- {coord}: **{count}** workflows")
                
                with col_summary2:
                    st.markdown("**By Workflow Type**")
                    for workflow_type, count in summary['by_workflow_type'].items():
                        st.markdown(f"- {workflow_type}: **{count}** workflows")
            
            # Import and use the workflow reassignment UI
            from src.utils.workflow_reassignment_ui import show_workflow_reassignment_table
            
            st.subheader("📋 Workflows Available for Reassignment")
            
            # Use shared workflow reassignment table
            selected_instance_ids, should_rerun = show_workflow_reassignment_table(
                workflows_df, 
                user_id, 
                table_key="admin_workflow_reassignment",
                show_search_filter=True
            )
            
            if should_rerun:
                st.success("Workflow reassignment completed successfully!")
                st.experimental_rerun()
    
    except Exception as e:
        st.error(f"Error in workflow reassignment: {e}")
        st.write("**Exception Details:**")
        st.code(str(e))
        
        import traceback
        st.write("**Traceback:**")
        st.code(traceback.format_exc())
        
        st.warning("This exception would cause workflows_df to be set to empty DataFrame")
        st.info("No active workflows available for reassignment.")

# Example usage in admin dashboard
def show_enhanced_admin_dashboard():
    """Example of how to use the enhanced workflow reassignment"""
    
    st.title("Admin Dashboard - Enhanced Debug Version")
    
    # Get user info from session (same as original)
    user_id = st.session_state.get("user_id", None)
    
    if not user_id:
        st.error("No user logged in")
        return
    
    # Get user roles (same as original)
    def get_user_role_ids(user_id):
        try:
            user_roles = db.get_user_roles_by_user_id(user_id)
            role_ids = [r["role_id"] for r in user_roles]
            return role_ids
        except Exception as e:
            st.error(f"Error loading user roles: {e}")
            return []
    
    user_role_ids = get_user_role_ids(user_id)
    
    # Show enhanced workflow reassignment
    enhanced_workflow_reassignment_section(user_id, user_role_ids)

if __name__ == "__main__":
    show_enhanced_admin_dashboard()