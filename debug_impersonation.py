#!/usr/bin/env python3
"""
Debug script to test impersonation and session state issues
"""

import streamlit as st
from src import database as db
from src.core_utils import get_user_role_ids

def debug_session_state():
    """Debug the current session state"""
    
    st.title("Session State Debug")
    
    # Show all session state keys
    st.subheader("All Session State Keys")
    session_keys = list(st.session_state.keys())
    st.write("Session keys:", session_keys)
    
    # Show key values
    st.subheader("Key Session Values")
    
    user_id = st.session_state.get("user_id", "NOT_FOUND")
    authenticated_user = st.session_state.get("authenticated_user", {})
    user_role_ids = st.session_state.get("user_role_ids", "NOT_FOUND")
    impersonating_user = st.session_state.get("impersonating_user", None)
    original_user = st.session_state.get("original_user", None)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**user_id:**", user_id)
        st.write("**user_role_ids:**", user_role_ids)
        st.write("**authenticated_user:**")
        st.write(authenticated_user)
    
    with col2:
        st.write("**impersonating_user:**", impersonating_user)
        st.write("**original_user:**", original_user)
    
    # Check if impersonating
    is_impersonating = impersonating_user is not None
    st.write("**Is Impersonating:**", is_impersonating)
    
    # Get roles for current user
    st.subheader("Role Analysis")
    
    if user_id != "NOT_FOUND" and user_id:
        try:
            # Test the core_utils function
            core_utils_roles = get_user_role_ids(user_id)
            st.write(f"**core_utils.get_user_role_ids({user_id}):** {core_utils_roles}")
            
            # Test database directly
            conn = db.get_db_connection()
            try:
                db_roles = conn.execute("SELECT role_id FROM user_roles WHERE user_id = ?", (user_id,)).fetchall()
                db_role_ids = [r['role_id'] for r in db_roles]
                st.write(f"**Database roles:** {db_role_ids}")
                
                # Show role names
                if db_role_ids:
                    roles_info = conn.execute(
                        "SELECT role_id, role_name FROM roles WHERE role_id IN (%s)" % ','.join('?'*len(db_role_ids)), 
                        db_role_ids
                    ).fetchall()
                    st.write("**Role Names:**")
                    for role in roles_info:
                        st.write(f"  - {role['role_id']}: {role['role_name']}")
                        
            finally:
                conn.close()
                
        except Exception as e:
            st.error(f"Error getting roles: {e}")
    else:
        st.error("No valid user_id found in session")
    
    # Test workflow access
    st.subheader("Workflow Access Test")
    
    if user_id != "NOT_FOUND" and user_id and user_role_ids != "NOT_FOUND" and user_role_ids:
        try:
            from src.utils.workflow_utils import get_workflows_for_reassignment
            
            workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
            st.write(f"**Workflows returned:** {len(workflows_df)}")
            st.write(f"**DataFrame empty:** {workflows_df.empty}")
            
            if not workflows_df.empty:
                st.success("Workflows found! Should show management interface.")
                with st.expander("View sample workflows"):
                    st.dataframe(workflows_df.head())
            else:
                st.error("No workflows found! Would show 'No active workflows available'")
                
        except Exception as e:
            st.error(f"Error getting workflows: {e}")
            import traceback
            st.code(traceback.format_exc())
    
    # Test with different role combinations
    st.subheader("Role Combination Tests")
    
    if user_id and user_id != "NOT_FOUND":
        try:
            # Get all roles for this user
            all_roles = get_user_role_ids(user_id)
            st.write(f"All user roles: {all_roles}")
            
            # Test different combinations
            test_cases = [
                ([34], "Admin only"),
                ([40], "Coordinator Manager only"),
                ([36], "Care Coordinator only"),
                ([34, 40], "Admin + CM"),
                ([36, 40], "CC + CM"),
                (all_roles, "All user roles"),
            ]
            
            for roles, description in test_cases:
                if all(role in all_roles for role in roles):
                    try:
                        df = get_workflows_for_reassignment(user_id, roles)
                        status = "SUCCESS" if not df.empty else "FAILED"
                        st.write(f"{description}: {status} ({len(df)} workflows)")
                    except Exception as e:
                        st.write(f"{description}: ERROR - {e}")
                        
        except Exception as e:
            st.error(f"Error testing role combinations: {e}")

# Run the debug
if __name__ == "__main__":
    debug_session_state()