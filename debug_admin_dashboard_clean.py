#!/usr/bin/env python3
"""
Debug script to simulate the exact admin dashboard workflow reassignment logic
"""

import pandas as pd
from src import database
from src.utils.workflow_utils import get_workflows_for_reassignment, get_reassignment_summary

def test_admin_workflow_logic():
    """Test the exact admin dashboard workflow reassignment logic"""
    
    print("=== Testing Admin Dashboard Workflow Reassignment Logic ===\n")
    
    # Test with Bianchi (Admin user ID 5)
    user_id = 5
    user_role_ids = [34]  # Admin only
    
    print(f"Testing with user_id={user_id}, user_role_ids={user_role_ids}")
    
    try:
        # Step 1: Get workflows for reassignment (exact call from admin_dashboard.py line 3145)
        print("\n1. Calling get_workflows_for_reassignment...")
        workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
        print(f"   Returned DataFrame with {len(workflows_df)} rows")
        print(f"   DataFrame empty: {workflows_df.empty}")
        
        if workflows_df.empty:
            print("   RESULT: DataFrame is empty - this would show 'No active workflows available'")
            return "EMPTY_DATAFRAME"
        else:
            print("   RESULT: DataFrame has data - should proceed to show workflows")
            print(f"   Shape: {workflows_df.shape}")
            print(f"   Columns: {list(workflows_df.columns)}")
            
        # Step 2: Get reassignment summary (exact call from admin_dashboard.py line 3154)
        print("\n2. Calling get_reassignment_summary...")
        summary = get_reassignment_summary(workflows_df)
        print(f"   Summary total_workflows: {summary.get('total_workflows', 'MISSING')}")
        
        return "SUCCESS" if summary.get('total_workflows', 0) > 0 else "SUMMARY_FAILED"
        
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return "ERROR"

def test_different_admin_users():
    """Test with different admin users"""
    
    print("\n=== Testing Different Admin Users ===\n")
    
    # Test users from database
    test_cases = [
        {"user_id": 5, "full_name": "Sanchez, Bianchi", "roles": [34]},  # Admin only
        {"user_id": 12, "full_name": "Cheema, Harpreet", "roles": [34]},  # Admin only  
        {"user_id": 18, "full_name": "Malhotra MD, Justin", "roles": [34]},  # Admin only
    ]
    
    for user in test_cases:
        print(f"Testing {user['full_name']} (ID: {user['user_id']})...")
        
        try:
            workflows_df = get_workflows_for_reassignment(user['user_id'], user['roles'])
            result = "SUCCESS" if not workflows_df.empty else "FAILED"
            print(f"   Result: {result} ({len(workflows_df)} workflows)")
            
        except Exception as e:
            print(f"   ERROR: {e}")
            result = "ERROR"
        
        print(f"   --- {result} ---")

if __name__ == "__main__":
    result = test_admin_workflow_logic()
    print(f"\n=== FINAL RESULT: {result} ===")
    
    if result == "SUCCESS":
        print("The backend logic is working correctly. The issue must be in the Streamlit UI layer.")
    else:
        print("There's an issue in the backend logic.")
        
    test_different_admin_users()