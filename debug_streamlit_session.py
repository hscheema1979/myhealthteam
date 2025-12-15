#!/usr/bin/env python3
"""
Debug script to test Streamlit session state issues
"""

import streamlit as st
import pandas as pd
from src.utils.workflow_utils import get_workflows_for_reassignment

# Role constants
ROLE_ADMIN = 34
ROLE_CARE_PROVIDER = 33
ROLE_CARE_COORDINATOR = 36
ROLE_COORDINATOR_MANAGER = 40
ROLE_ONBOARDING_TEAM = 37

def test_streamlit_workflow_tab():
    """Test the exact Streamlit workflow tab logic"""
    
    # Simulate different user sessions
    test_sessions = [
        {
            "user_id": 5,
            "full_name": "Sanchez, Bianchi",
            "user_role_ids": [34],  # Admin only
            "expected_result": "should see workflows"
        },
        {
            "user_id": 14, 
            "full_name": "Estomo, Jan",
            "user_role_ids": [36, 40],  # CC + CM
            "expected_result": "should see workflows"
        },
        {
            "user_id": 12,
            "full_name": "Cheema, Harpreet", 
            "user_role_ids": [34],  # Admin only
            "expected_result": "should see workflows"
        }
    ]
    
    print("=== Testing Streamlit Workflow Reassignment Logic ===\n")
    
    for session in test_sessions:
        print(f"Testing session for: {session['full_name']} (ID: {session['user_id']})")
        print(f"Roles: {session['user_role_ids']} ({session['expected_result']})")
        
        try:
            # This is the exact logic from admin_dashboard.py
            user_id = session['user_id']
            user_role_ids = session['user_role_ids']
            
            # Line 3145 from admin_dashboard.py
            workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
            
            print(f"  workflows_df.empty: {workflows_df.empty}")
            print(f"  len(workflows_df): {len(workflows_df)}")
            
            if workflows_df.empty:
                print("  RESULT: Would show 'No active workflows available for reassignment.'")
            else:
                print("  RESULT: Would show workflow management interface")
                # Lines 3154-3164 from admin_dashboard.py
                from src.utils.workflow_utils import get_reassignment_summary
                summary = get_reassignment_summary(workflows_df)
                print(f"  Summary - Total: {summary['total_workflows']}, Avg Steps: {summary['avg_steps']:.1f}")
                
            print("-" * 60)
            
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            print("-" * 60)

def test_role_detection():
    """Test role detection logic"""
    
    print("\n=== Testing Role Detection Logic ===\n")
    
    # Test cases from app.py around line 453
    test_cases = [
        {"user_role_ids": [34], "expected": "Admin dashboard"},
        {"user_role_ids": [40], "expected": "Coordinator Manager dashboard"}, 
        {"user_role_ids": [34, 40], "expected": "Both roles"},
        {"user_role_ids": [36], "expected": "Coordinator only"},
    ]
    
    for case in test_cases:
        print(f"Roles: {case['user_role_ids']} -> {case['expected']}")
        
        # Check if user should see workflow reassignment (line 453 logic)
        if 40 in case['user_role_ids']:
            print("  -> Would get coordinator dashboard with workflow reassignment tab")
        elif 34 in case['user_role_ids']:
            print("  -> Would get admin dashboard")
        else:
            print("  -> Would get regular dashboard")
        
        # Test workflow access
        try:
            workflows_df = get_workflows_for_reassignment(5, case['user_role_ids'])  # Using user 5 with different roles
            print(f"  -> Workflow access: {len(workflows_df)} workflows")
        except Exception as e:
            print(f"  -> Workflow access: ERROR - {e}")
        
        print()

if __name__ == "__main__":
    test_streamlit_workflow_tab()
    test_role_detection()