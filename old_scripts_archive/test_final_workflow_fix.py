#!/usr/bin/env python3
"""
Final test to verify workflow reassignment fixes work correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from src.utils.workflow_utils import (
    get_workflows_for_reassignment,
    ROLE_ADMIN, ROLE_CARE_COORDINATOR, ROLE_COORDINATOR_MANAGER
)

def test_all_scenarios():
    """Test all user scenarios for workflow reassignment"""
    print("=== Final Workflow Reassignment Fix Test ===")
    
    test_cases = [
        {
            "name": "Harpreet (Admin)",
            "user_id": 12,
            "user_role_ids": [34],
            "expected_workflows": 89,
            "description": "Admin should see ALL workflows"
        },
        {
            "name": "Jan (Coordinator Manager)", 
            "user_id": 14,
            "user_role_ids": [40],
            "expected_workflows": 89,
            "description": "Coordinator Manager should see ALL workflows"
        },
        {
            "name": "Jan (Admin + CM)",
            "user_id": 14,
            "user_role_ids": [34, 40],
            "expected_workflows": 89,
            "description": "Admin + CM should see ALL workflows"
        },
        {
            "name": "Jan (CC + CM)",
            "user_id": 14,
            "user_role_ids": [36, 40],
            "expected_workflows": 89,
            "description": "CC + CM should see ALL workflows"
        },
        {
            "name": "Regular Coordinator",
            "user_id": 1,
            "user_role_ids": [36],
            "expected_workflows": 2,
            "description": "Regular coordinator should see only assigned workflows"
        },
        {
            "name": "No Roles",
            "user_id": 999,
            "user_role_ids": [],
            "expected_workflows": 0,
            "description": "User with no roles should see no workflows"
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n--- Testing {test_case['name']} ---")
        print(f"Roles: {test_case['user_role_ids']}")
        print(f"Expected: {test_case['description']}")
        
        try:
            workflows_df = get_workflows_for_reassignment(
                test_case['user_id'], 
                test_case['user_role_ids']
            )
            
            actual_count = len(workflows_df)
            expected_count = test_case['expected_workflows']
            
            if actual_count == expected_count:
                print(f"SUCCESS: Found {actual_count} workflows (expected {expected_count})")
            else:
                print(f"FAIL: Found {actual_count} workflows (expected {expected_count})")
                all_passed = False
                
            if not workflows_df.empty:
                print(f"  Sample workflow: {workflows_df.iloc[0]['workflow_type']} for {workflows_df.iloc[0]['patient_name']}")
                
        except Exception as e:
            print(f"FAIL: Exception occurred: {e}")
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("ALL TESTS PASSED! Workflow reassignment should now work correctly.")
        print("\nExpected behavior:")
        print("- Admin users (role 34): See ALL workflows")
        print("- Coordinator Managers (role 40): See ALL workflows") 
        print("- Regular coordinators (role 36): See only assigned workflows")
        print("- Users with both roles: See ALL workflows (admin/CM takes precedence)")
    else:
        print("SOME TESTS FAILED! Please review the implementation.")

def test_workflow_data_structure():
    """Test that the workflow DataFrame has the correct structure"""
    print("\n=== Testing Workflow Data Structure ===")
    
    workflows_df = get_workflows_for_reassignment(12, [34])  # Harpreet as admin
    
    expected_columns = [
        'instance_id', 'workflow_type', 'patient_name', 'patient_id',
        'coordinator_name', 'coordinator_id', 'workflow_status', 
        'current_step', 'total_steps', 'priority', 'created_date'
    ]
    
    actual_columns = list(workflows_df.columns)
    
    print(f"Expected columns: {expected_columns}")
    print(f"Actual columns: {actual_columns}")
    
    if actual_columns == expected_columns:
        print("SUCCESS: DataFrame has correct column structure")
    else:
        print("FAIL: DataFrame column structure mismatch")
        missing = set(expected_columns) - set(actual_columns)
        extra = set(actual_columns) - set(expected_columns)
        if missing:
            print(f"  Missing columns: {missing}")
        if extra:
            print(f"  Extra columns: {extra}")

if __name__ == "__main__":
    test_all_scenarios()
    test_workflow_data_structure()