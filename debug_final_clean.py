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
        print(f"   Database connection successful")
        print(f"   Active workflows in DB: {count}")
        conn.close()
    except Exception as e:
        print(f"   Database connection failed: {e}")
        return
    
    # Step 2: Test get_workflows_for_reassignment with detailed error checking
    print("\n2. Testing get_workflows_for_reassignment...")
    try:
        workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
        print(f"   Function executed successfully")
        print(f"   DataFrame type: {type(workflows_df)}")
        print(f"   DataFrame shape: {workflows_df.shape}")
        print(f"   DataFrame empty: {workflows_df.empty}")
        
        if workflows_df.empty:
            print("   DataFrame is empty - this is the problem!")
        else:
            print("   DataFrame has data")
            print(f"   First few rows:")
            print(workflows_df.head(3).to_string())
            
    except Exception as e:
        print(f"   Function failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Test the exact admin dashboard condition
    print("\n3. Testing admin dashboard condition...")
    print(f"   workflows_df.empty = {workflows_df.empty}")
    
    if workflows_df.empty:
        print("   Would show: 'No active workflows available for reassignment.'")
        result = "FAILED"
    else:
        print("   Would show workflow management interface")
        result = "SUCCESS"
    
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

if __name__ == "__main__":
    comprehensive_debug()