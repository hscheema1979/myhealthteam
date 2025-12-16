#!/usr/bin/env python3
"""
Debug script to simulate the exact admin dashboard workflow reassignment logic
"""

import pandas as pd
from src import database
from src.utils.workflow_utils import get_workflows_for_reassignment, get_reassignment_summary
from src.utils.workflow_reassignment_ui import show_workflow_reassignment_table

# Role constants
ROLE_ADMIN = 34
ROLE_CARE_PROVIDER = 33
ROLE_CARE_COORDINATOR = 36
ROLE_COORDINATOR_MANAGER = 40
ROLE_ONBOARDING_TEAM = 37

def simulate_admin_dashboard():
    """Simulate the exact admin dashboard workflow reassignment logic"""
    
    print("=== Simulating Admin Dashboard Workflow Reassignment ===\n")
    
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
            print("   ❌ DataFrame is empty - this would show 'No active workflows available'")
            return
        else:
            print("   ✅ DataFrame has data")
            print(f"   Columns: {list(workflows_df.columns)}")
            print(f"   First few rows:")
            print(workflows_df.head())
        
        # Step 2: Get reassignment summary (exact call from admin_dashboard.py line 3154)
        print("\n2. Calling get_reassignment_summary...")
        summary = get_reassignment_summary(workflows_df)
        print(f"   Summary: {summary}")
        
        # Step 3: Test the UI component (exact call from admin_dashboard.py line 3182)
        print("\n3. Testing show_workflow_reassignment_table...")
        selected_instance_ids, should_rerun = show_workflow_reassignment_table(
            workflows_df, 
            user_id, 
            table_key="admin_workflow_reassignment"
        )
        print(f"   Selected instance IDs: {selected_instance_ids}")
        print(f"   Should rerun: {should_rerun}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_dataframe_structure():
    """Test if the DataFrame has the expected structure"""
    
    print("\n=== Testing DataFrame Structure ===\n")
    
    user_id = 5
    user_role_ids = [34]
    
    workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
    
    print(f"DataFrame shape: {workflows_df.shape}")
    print(f"DataFrame empty: {workflows_df.empty}")
    print(f"Column names: {list(workflows_df.columns)}")
    
    if not workflows_df.empty:
        print(f"\nFirst row data types:")
        for col in workflows_df.columns:
            val = workflows_df.iloc[0][col]
            print(f"  {col}: {type(val)} = {val}")
        
        # Check for expected columns that the UI needs
        expected_columns = [
            'instance_id', 'workflow_type', 'patient_name', 'patient_id',
            'coordinator_name', 'coordinator_id', 'workflow_status', 
            'current_step', 'total_steps', 'priority', 'created_date'
        ]
        
        print(f"\nExpected columns check:")
        for col in expected_columns:
            if col in workflows_df.columns:
                print(f"  ✅ {col}")
            else:
                print(f"  ❌ {col} - MISSING")

if __name__ == "__main__":
    simulate_admin_dashboard()
    test_dataframe_structure()