#!/usr/bin/env python3
"""
Debug script to test the exact admin dashboard session state logic
"""

import streamlit as st
from src import database as db

def simulate_admin_dashboard_session():
    """Simulate the exact session state logic from admin_dashboard.py"""
    
    print("=== Simulating Admin Dashboard Session State ===\n")
    
    # Simulate different logged-in users
    test_users = [
        {"user_id": 5, "full_name": "Sanchez, Bianchi"},
        {"user_id": 14, "full_name": "Estomo, Jan"},
        {"user_id": 12, "full_name": "Cheema, Harpreet"},
    ]
    
    for user_info in test_users:
        print(f"Testing session for: {user_info['full_name']} (ID: {user_info['user_id']})")
        
        # Simulate st.session_state from admin_dashboard.py line 196
        user_id = user_info['user_id']  # This is st.session_state.get("user_id", None)
        
        print(f"  user_id from session: {user_id}")
        
        if user_id:
            # Simulate get_user_role_ids function from admin_dashboard.py lines 201-213
            def get_user_role_ids(user_id):
                """Get user role IDs from database and cache in session state"""
                # Simulate session state check
                try:
                    user_roles = db.get_user_roles_by_user_id(user_id)
                    role_ids = [r["role_id"] for r in user_roles]
                    print(f"    Database returned roles: {role_ids}")
                    return role_ids
                except Exception as e:
                    print(f"    ERROR loading roles: {e}")
                    return []
            
            # This is the exact logic from admin_dashboard.py line 216
            user_role_ids = get_user_role_ids(user_id) if user_id else []
            print(f"  Final user_role_ids: {user_role_ids}")
            
            # Test if this user should see workflow reassignment
            if user_role_ids:
                if 34 in user_role_ids:  # Admin
                    print("  -> This is an ADMIN user")
                if 40 in user_role_ids:  # Coordinator Manager
                    print("  -> This is a COORDINATOR MANAGER user")
                
                # Test workflow access
                from src.utils.workflow_utils import get_workflows_for_reassignment
                try:
                    workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
                    print(f"  -> Workflow access: {len(workflows_df)} workflows")
                    
                    if workflows_df.empty:
                        print("  -> RESULT: Would show 'No active workflows available'")
                    else:
                        print("  -> RESULT: Would show workflow management interface")
                        
                except Exception as e:
                    print(f"  -> ERROR in workflow access: {e}")
            else:
                print("  -> No roles found!")
        else:
            print("  -> No user_id in session!")
        
        print("-" * 50)

def test_actual_session_values():
    """Test with actual database values"""
    
    print("\n=== Testing with Actual Database Values ===\n")
    
    # Get actual users and their roles
    conn = db.get_db_connection()
    try:
        users = conn.execute("""
            SELECT u.user_id, u.full_name, r.role_id, r.role_name 
            FROM users u 
            JOIN user_roles ur ON u.user_id = ur.user_id 
            JOIN roles r ON ur.role_id = r.role_id
            WHERE r.role_name IN ('ADMIN', 'CC', 'CM')
            ORDER BY u.user_id
        """).fetchall()
        
        current_user_id = None
        user_roles = {}
        
        for row in users:
            user_id = row['user_id']
            if user_id != current_user_id:
                if current_user_id:
                    # Process previous user
                    _test_user_session(current_user_id, user_roles)
                current_user_id = user_id
                user_roles = {
                    'full_name': row['full_name'],
                    'roles': []
                }
            user_roles['roles'].append({
                'role_id': row['role_id'],
                'role_name': row['role_name']
            })
        
        # Process last user
        if current_user_id:
            _test_user_session(current_user_id, user_roles)
            
    finally:
        conn.close()

def _test_user_session(user_id, user_info):
    """Helper function to test a user's session"""
    print(f"Testing {user_info['full_name']} (ID: {user_id})")
    
    role_ids = [r['role_id'] for r in user_info['roles']]
    role_names = [r['role_name'] for r in user_info['roles']]
    print(f"  Roles: {role_ids} ({', '.join(role_names)})")
    
    # Test workflow access
    from src.utils.workflow_utils import get_workflows_for_reassignment
    try:
        workflows_df = get_workflows_for_reassignment(user_id, role_ids)
        print(f"  Workflows: {len(workflows_df)}")
        
        if workflows_df.empty:
            print("  ❌ Would show 'No active workflows available'")
        else:
            print("  ✅ Would show workflow management interface")
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
    
    print("-" * 40)

if __name__ == "__main__":
    simulate_admin_dashboard_session()
    test_actual_session_values()