#!/usr/bin/env python3
"""
Final comprehensive debug script to find the root cause
"""

import pandas as pd
from src import database as db
from src.utils.workflow_utils import get_workflows_for_reassignment, get_reassignment_summary

def comprehensive_debug():
    """Run comprehensive debug checks"""
    
    print("=== COMPREHENSIVE DEBUG CHECK ===\n")
    
    # Test user: Bianchi (Admin)
    user_id = 5
    user_role_ids = [34]
    
    print(f"Testing user: Bianchi (ID: {user_id}, Roles: {user_role_ids})")
    
    # Step 1: Test database connection
    print("\n1. Testing database connection...")
    try:
        conn = db.get_db_connection()
        result = conn.execute("SELECT COUNT(*) as count FROM workflow_instances WHERE workflow_status = 'Active'")
        count = result.fetchone()['count']
        print(f"   ✅ Database connection successful")
        print(f"   Active workflows in DB: {count}")
        conn.close()
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return
    
    # Step 2: Test get_workflows_for_reassignment with detailed error checking
    print("\n2. Testing get_workflows_for_reassignment...")
    try:
        workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
        print(f"   ✅ Function executed successfully")
        print(f"   DataFrame type: {type(workflows_df)}")
        print(f"   DataFrame shape: {workflows_df.shape}")
        print(f"   DataFrame empty: {workflows_df.empty}")
        
        if workflows_df.empty:
            print("   ❌ DataFrame is empty - this is the problem!")
        else:
            print("   ✅ DataFrame has data")
            print(f"   First few rows:")
            print(workflows_df.head(3).to_string())
            
    except Exception as e:
        print(f"   ❌ Function failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Test get_reassignment_summary
    print("\n3. Testing get_reassignment_summary...")
    try:
        summary = get_reassignment_summary(workflows_df)
        print(f"   ✅ Summary generated successfully")
        print(f"   Summary keys: {list(summary.keys())}")
        print(f"   Total workflows: {summary.get('total_workflows', 'MISSING')}")
    except Exception as e:
        print(f"   ❌ Summary failed: {e}")
        return
    
    # Step 4: Test the exact admin dashboard condition
    print("\n4. Testing admin dashboard condition...")
    print(f"   workflows_df.empty = {workflows_df.empty}")
    
    if workflows_df.empty:
        print("   ❌ Would show: 'No active workflows available for reassignment.'")
        result = "FAILED"
    else:
        print("   ✅ Would show workflow management interface")
        result = "SUCCESS"
    
    # Step 5: Test with different users
    print("\n5. Testing with different admin users...")
    test_users = [
        {"user_id": 5, "name": "Bianchi"},
        {"user_id": 12, "name": "Cheema"},
        {"user_id": 18, "name": "Malhotra"},
    ]
    
    for user in test_users:
        try:
            df = get_workflows_for_reassignment(user["user_id"], [34])
            status = "SUCCESS" if not df.empty else "FAILED"
            print(f"   {user['name']}: {status} ({len(df)} workflows)")
        except Exception as e:
            print(f"   {user['name']}: ERROR - {e}")
    
    print(f"\n=== FINAL RESULT: {result} ===")
    
    if result == "SUCCESS":
        print("All backend logic is working correctly.")
        print("The issue must be in the Streamlit UI layer, session state, or data display logic.")
        print("Possible causes:")
        print("- Session state not properly initialized")
        print("- User roles not correctly passed to admin dashboard")
        print("- Exception being caught and hidden in the UI")
        print("- DataFrame being modified/cleared somewhere in the UI code")
    else:
        print("Backend logic is failing.")
        print("The get_workflows_for_reassignment function is returning an empty DataFrame.")

def check_hidden_exceptions():
    """Check for hidden exceptions that might be caught"""
    
    print("\n=== Checking for Hidden Exceptions ===\n")
    
    user_id = 5
    user_role_ids = [34]
    
    # Test the exact admin dashboard exception handling
    try:
        workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
    except Exception as e:
        print(f"Exception caught: {e}")
        workflows_df = pd.DataFrame()  # This is what admin_dashboard.py does
        print("DataFrame set to empty due to exception")
    
    print(f"Final DataFrame empty: {workflows_df.empty}")
    print(f"Final DataFrame length: {len(workflows_df)}")
    
    # Test if the exception would cause the "No active workflows" message
    if workflows_df.empty:
        print("This would trigger: 'No active workflows available for reassignment.'")
    else:
        print("This would show the workflow management interface.")

if __name__ == "__main__":
    comprehensive_debug()
    check_hidden_exceptions()