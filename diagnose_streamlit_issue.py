#!/usr/bin/env python3
"""
Diagnostic script to run within Streamlit to identify the workflow reassignment issue
"""

import streamlit as st
import pandas as pd
from src import database as db
from src.utils.workflow_utils import get_workflows_for_reassignment, get_reassignment_summary

def diagnose_workflow_issue():
    """Diagnose the workflow reassignment issue within Streamlit"""
    
    st.title("Workflow Reassignment Diagnostic")
    
    # Get current user info from session
    user_id = st.session_state.get("user_id", None)
    current_user = st.session_state.get("authenticated_user", {})
    
    st.subheader("Session State Info")
    st.write(f"user_id: {user_id}")
    st.write(f"authenticated_user: {current_user}")
    
    if not user_id:
        st.error("No user_id found in session state!")
        return
    
    # Get user roles
    try:
        user_roles = db.get_user_roles_by_user_id(user_id)
        user_role_ids = [r["role_id"] for r in user_roles]
        st.write(f"user_role_ids: {user_role_ids}")
    except Exception as e:
        st.error(f"Error getting user roles: {e}")
        return
    
    # Test workflow access
    st.subheader("Workflow Access Test")
    
    try:
        # This is the exact call from admin_dashboard.py line 3145
        workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
        
        st.write(f"DataFrame shape: {workflows_df.shape}")
        st.write(f"DataFrame empty: {workflows_df.empty}")
        
        if workflows_df.empty:
            st.error("DataFrame is empty - this is why you see 'No active workflows available'")
            
            # Let's debug further
            st.subheader("Debug Info")
            
            # Check database directly
            conn = db.get_db_connection()
            try:
                result = conn.execute("SELECT COUNT(*) as count FROM workflow_instances WHERE workflow_status = 'Active'")
                db_count = result.fetchone()['count']
                st.write(f"Active workflows in database: {db_count}")
                
                # Check if it's a role-based filtering issue
                if 34 in user_role_ids or 40 in user_role_ids:
                    st.write("User has admin/CM privileges - should see all workflows")
                else:
                    st.write("User does not have admin/CM privileges - may have limited access")
                
            finally:
                conn.close()
        else:
            st.success(f"DataFrame has {len(workflows_df)} workflows - should work correctly!")
            
            # Show summary
            summary = get_reassignment_summary(workflows_df)
            st.write("Summary:", summary)
            
            # Show first few workflows
            with st.expander("View first 5 workflows"):
                st.dataframe(workflows_df.head())
    
    except Exception as e:
        st.error(f"Error in get_workflows_for_reassignment: {e}")
        st.write("This exception would cause workflows_df to be set to empty DataFrame")
        
        # Show traceback
        import traceback
        st.code(traceback.format_exc())

def test_role_switching():
    """Test if role switching affects workflow access"""
    
    st.subheader("Role Switching Test")
    
    user_id = st.session_state.get("user_id", None)
    if not user_id:
        st.error("No user_id in session")
        return
    
    # Get all user roles
    try:
        user_roles = db.get_user_roles_by_user_id(user_id)
        role_ids = [r["role_id"] for r in user_roles]
        
        st.write(f"All user roles: {role_ids}")
        
        # Test with different role combinations
        test_roles = [
            ([34], "Admin only"),
            ([40], "CM only"),
            ([36], "CC only"),
            ([34, 40], "Admin + CM"),
            ([36, 40], "CC + CM"),
        ]
        
        for roles, description in test_roles:
            if all(role in role_ids for role in roles):
                try:
                    df = get_workflows_for_reassignment(user_id, roles)
                    st.write(f"{description}: {len(df)} workflows")
                except Exception as e:
                    st.write(f"{description}: ERROR - {e}")
    
    except Exception as e:
        st.error(f"Error testing roles: {e}")

# Run the diagnostic
if __name__ == "__main__":
    diagnose_workflow_issue()
    test_role_switching()