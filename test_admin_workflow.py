#!/usr/bin/env python3
"""
Test with Harpreet's admin user context
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from src.utils.workflow_utils import (
    get_workflows_for_reassignment,
    ROLE_ADMIN, ROLE_CARE_COORDINATOR, ROLE_COORDINATOR_MANAGER
)

def test_admin_workflow():
    """Test with Harpreet's admin user context"""
    print("=== Testing Admin User (Harpreet) ===")
    
    # Test with Harpreet's actual user info from the debug output
    user_id = 12  # Harpreet's user_id
    user_role_ids = [34]  # Harpreet's role: Admin
    
    print(f"Testing with user_id={user_id}, user_role_ids={user_role_ids}")
    print(f"Has Admin Access: {ROLE_ADMIN in user_role_ids}")
    print(f"Has Coordinator Manager Access: {ROLE_COORDINATOR_MANAGER in user_role_ids}")
    
    try:
        workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
        
        print(f"DataFrame shape: {workflows_df.shape}")
        print(f"DataFrame empty: {workflows_df.empty}")
        
        if workflows_df.empty:
            print("FAIL: Admin should see all workflows but DataFrame is empty")
        else:
            print(f"SUCCESS: Admin sees {len(workflows_df)} workflows")
            print("First few workflow IDs:", workflows_df['instance_id'].head(3).tolist())
            
    except Exception as e:
        print(f"FAIL Exception: {e}")
        import traceback
        traceback.print_exc()

def test_regular_coordinator():
    """Test with regular coordinator (should see limited workflows)"""
    print("\n=== Testing Regular Coordinator ===")
    
    # Test with a regular coordinator (no admin/CM roles)
    user_id = 1  # Some coordinator
    user_role_ids = [36]  # Only Care Coordinator role
    
    print(f"Testing with user_id={user_id}, user_role_ids={user_role_ids}")
    print(f"Has Admin Access: {ROLE_ADMIN in user_role_ids}")
    print(f"Has Coordinator Manager Access: {ROLE_COORDINATOR_MANAGER in user_role_ids}")
    
    try:
        workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
        
        print(f"DataFrame shape: {workflows_df.shape}")
        print(f"DataFrame empty: {workflows_df.empty}")
        
        if workflows_df.empty:
            print("INFO: Regular coordinator sees no workflows (expected if not assigned any)")
        else:
            print(f"SUCCESS: Regular coordinator sees {len(workflows_df)} workflows")
            
    except Exception as e:
        print(f"FAIL Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_admin_workflow()
    test_regular_coordinator()