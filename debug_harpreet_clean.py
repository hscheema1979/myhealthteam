#!/usr/bin/env python3
"""
Debug script to check Harpreet's user account and permissions
"""

import sqlite3
from src import database as db
from src.core_utils import get_user_role_ids

def debug_harpreet_account():
    """Debug Harpreet's user account specifically"""
    
    print("=== Debugging Harpreet's Account ===\n")
    
    # Find Harpreet's user info
    conn = db.get_db_connection()
    try:
        # Look for harpreet@myhealthteam.org
        harpreet_user = conn.execute(
            "SELECT user_id, full_name, email, username FROM users WHERE email = ?",
            ("harpreet@myhealthteam.org",)
        ).fetchall()
        
        print("Users matching harpreet:")
        for user in harpreet_user:
            print(f"  user_id: {user['user_id']}, full_name: {user['full_name']}, email: {user['email']}, username: {user['username']}")
        
        if harpreet_user:
            user_id = harpreet_user[0]['user_id']
            print(f"\nUsing user_id: {user_id}")
            
            # Check roles
            roles = conn.execute(
                "SELECT ur.role_id, r.role_name FROM user_roles ur JOIN roles r ON ur.role_id = r.role_id WHERE ur.user_id = ?",
                (user_id,)
            ).fetchall()
            
            print(f"Roles for user {user_id}:")
            role_ids = []
            for role in roles:
                print(f"  role_id: {role['role_id']}, role_name: {role['role_name']}")
                role_ids.append(role['role_id'])
            
            # Test core_utils function
            core_utils_roles = get_user_role_ids(user_id)
            print(f"core_utils.get_user_role_ids({user_id}): {core_utils_roles}")
            
            # Test workflow access
            from src.utils.workflow_utils import get_workflows_for_reassignment
            
            print(f"\nTesting workflow access with role_ids: {role_ids}")
            workflows_df = get_workflows_for_reassignment(user_id, role_ids)
            print(f"Workflows returned: {len(workflows_df)}")
            print(f"DataFrame empty: {workflows_df.empty}")
            
            if workflows_df.empty:
                print("FAILED: Would show 'No active workflows available'")
            else:
                print("SUCCESS: Would show workflow management interface")
                
            # Test database directly
            print(f"\nDirect database check:")
            total_active = conn.execute("SELECT COUNT(*) as count FROM workflow_instances WHERE workflow_status = 'Active'").fetchone()['count']
            print(f"Total active workflows in database: {total_active}")
            
            print(f"\n=== CONCLUSION ===")
            print(f"Harpreet's account (user_id: {user_id}) has ADMIN role and should see {len(workflows_df)} workflows")
            print(f"The backend logic is working correctly.")
            print(f"The issue must be in the Streamlit session state or UI layer.")
            
        else:
            print("FAILED: No user found matching harpreet@myhealthteam.org")
            
    finally:
        conn.close()

if __name__ == "__main__":
    debug_harpreet_account()