#!/usr/bin/env python3
"""
Streamlit diagnostic to debug session state issues
"""

import streamlit as st
from src import database as db
from src.core_utils import get_user_role_ids

def streamlit_session_diagnostic():
    """Run comprehensive session state diagnostic in Streamlit"""
    
    st.title("🔍 Streamlit Session State Diagnostic")
    st.markdown("This will help identify why the workflow reassignment isn't working for your account.")
    
    # Get all session state info
    st.subheader("📊 Current Session State")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Basic Session Info:**")
        user_id = st.session_state.get("user_id", "NOT_FOUND")
        st.write(f"- user_id: `{user_id}`")
        
        authenticated_user = st.session_state.get("authenticated_user", {})
        st.write(f"- authenticated_user: `{authenticated_user}`")
        
        if authenticated_user:
            st.write(f"  - user_id: `{authenticated_user.get('user_id', 'MISSING')}`")
            st.write(f"  - full_name: `{authenticated_user.get('full_name', 'MISSING')}`")
            st.write(f"  - email: `{authenticated_user.get('email', 'MISSING')}`")
        
        user_role_ids = st.session_state.get("user_role_ids", "NOT_FOUND")
        st.write(f"- user_role_ids: `{user_role_ids}`")
        
        login_method = st.session_state.get("login_method", "NOT_FOUND")
        st.write(f"- login_method: `{login_method}`")
    
    with col2:
        st.write("**Impersonation Info:**")
        impersonating_user = st.session_state.get("impersonating_user", None)
        original_user = st.session_state.get("original_user", None)
        
        st.write(f"- impersonating_user: `{impersonating_user}`")
        st.write(f"- original_user: `{original_user}`")
        
        is_impersonating = impersonating_user is not None
        st.write(f"- is_impersonating: `{is_impersonating}`")
        
        if impersonating_user:
            st.write(f"  - Impersonating user_id: `{impersonating_user.get('user_id', 'MISSING')}`")
            st.write(f"  - Impersonating full_name: `{impersonating_user.get('full_name', 'MISSING')}`")
        
        if original_user:
            st.write(f"  - Original user_id: `{original_user.get('user_id', 'MISSING')}`")
            st.write(f"  - Original full_name: `{original_user.get('full_name', 'MISSING')}`")
    
    # Check for session inconsistencies
    st.subheader("🚨 Session Consistency Check")
    
    issues = []
    
    # Check 1: user_id consistency
    if authenticated_user and user_id != "NOT_FOUND":
        auth_user_id = authenticated_user.get('user_id')
        if str(auth_user_id) != str(user_id):
            issues.append(f"user_id mismatch: session.user_id={user_id}, authenticated_user.user_id={auth_user_id}")
    
    # Check 2: Missing user_id
    if user_id == "NOT_FOUND" or not user_id:
        issues.append("No user_id found in session state")
    
    # Check 3: Missing user_role_ids
    if user_role_ids == "NOT_FOUND" or not user_role_ids:
        issues.append("No user_role_ids found in session state")
    
    # Check 4: Impersonation state
    if is_impersonating and not impersonating_user:
        issues.append("Inconsistent impersonation state")
    
    if issues:
        st.error("❌ Session Issues Found:")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("✅ No obvious session issues detected")
    
    # Test workflow access with current session
    st.subheader("🧪 Workflow Access Test")
    
    if user_id != "NOT_FOUND" and user_id and user_role_ids != "NOT_FOUND" and user_role_ids:
        try:
            from src.utils.workflow_utils import get_workflows_for_reassignment
            
            st.write(f"**Testing with:**")
            st.write(f"- user_id: {user_id}")
            st.write(f"- user_role_ids: {user_role_ids}")
            
            workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
            
            st.write(f"**Result:**")
            st.write(f"- DataFrame shape: {workflows_df.shape}")
            st.write(f"- DataFrame empty: {workflows_df.empty}")
            
            if workflows_df.empty:
                st.error("❌ Would show 'No active workflows available for reassignment.'")
                
                # Additional debugging
                with st.expander("🔍 Why is it empty?"):
                    # Check database directly
                    conn = db.get_db_connection()
                    try:
                        result = conn.execute("SELECT COUNT(*) as count FROM workflow_instances WHERE workflow_status = 'Active'")
                        db_count = result.fetchone()['count']
                        st.write(f"Active workflows in database: {db_count}")
                        
                        # Check if roles are correct
                        if 34 in user_role_ids or 40 in user_role_ids:
                            st.write("User has admin/CM privileges - should see all workflows")
                            
                            # Test admin query directly
                            admin_query = """
                                SELECT COUNT(*) as count
                                FROM workflow_instances 
                                WHERE workflow_status = 'Active'
                            """
                            result = conn.execute(admin_query).fetchone()
                            admin_count = result['count']
                            st.write(f"Admin query should return: {admin_count} workflows")
                            
                        else:
                            st.write("User does not have admin/CM privileges")
                            
                    finally:
                        conn.close()
            else:
                st.success(f"✅ Found {len(workflows_df)} workflows - should work correctly!")
                
                with st.expander("View sample workflows"):
                    st.dataframe(workflows_df.head())
            
        except Exception as e:
            st.error(f"❌ Error getting workflows: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.error("Cannot test workflow access - missing user_id or user_role_ids")
    
    # Test role retrieval
    st.subheader("🔑 Role Retrieval Test")
    
    if user_id != "NOT_FOUND" and user_id:
        try:
            st.write(f"**Testing get_user_role_ids({user_id}):**")
            
            # Test core_utils function
            core_utils_roles = get_user_role_ids(user_id)
            st.write(f"core_utils result: {core_utils_roles}")
            
            # Test database directly
            conn = db.get_db_connection()
            try:
                db_roles = conn.execute("SELECT role_id FROM user_roles WHERE user_id = ?", (user_id,)).fetchall()
                db_role_ids = [r['role_id'] for r in db_roles]
                st.write(f"Database result: {db_role_ids}")
                
                if core_utils_roles != db_role_ids:
                    st.error("❌ Mismatch between core_utils and database results!")
                else:
                    st.success("✅ Role retrieval working correctly")
                    
            finally:
                conn.close()
                
        except Exception as e:
            st.error(f"❌ Error getting roles: {e}")
            import traceback
            st.code(traceback.format_exc())
    
    # Session reset button
    st.subheader("🔄 Session Management")
    
    if st.button("Clear Session State", type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Session state cleared!")
        st.rerun()
    
    if st.button("Force Session Refresh", type="primary"):
        st.rerun()

# Run the diagnostic
if __name__ == "__main__":
    streamlit_session_diagnostic()