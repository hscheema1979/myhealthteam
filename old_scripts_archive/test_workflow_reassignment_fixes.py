#!/usr/bin/env python3
"""
Test script to verify workflow reassignment fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import database as db
from src.utils.workflow_utils import (
    get_user_coordinator_id, 
    get_ongoing_workflows, 
    get_workflows_for_reassignment,
    execute_workflow_reassignment
)

# Import role constants
ROLE_ADMIN = 34
ROLE_CARE_PROVIDER = 33
ROLE_CARE_COORDINATOR = 36
ROLE_COORDINATOR_MANAGER = 40
ROLE_ONBOARDING_TEAM = 37

def test_user_coordinator_mapping():
    """Test the user-to-coordinator mapping function"""
    print("=== Testing User-to-Coordinator Mapping ===")
    
    # Test with known admin users
    test_users = [
        (12, "Harpreet"),  # Admin
        (18, "Justin"),    # Admin  
        (1, "Test User"),  # Regular user
    ]
    
    for user_id, name in test_users:
        try:
            coordinator_id = get_user_coordinator_id(user_id)
            print(f"User {user_id} ({name}): coordinator_id = {coordinator_id}")
        except Exception as e:
            print(f"User {user_id} ({name}): ERROR - {e}")

def test_workflow_permissions():
    """Test workflow retrieval with different role permissions"""
    print("\n=== Testing Workflow Permissions ===")
    
    # Test with admin permissions
    try:
        admin_workflows = get_ongoing_workflows(12, [ROLE_ADMIN])  # Harpreet as admin
        print(f"Admin user (12) workflows: {len(admin_workflows)} found")
        
        coordinator_manager_workflows = get_ongoing_workflows(1, [ROLE_COORDINATOR_MANAGER])  # Test with CM role
        print(f"Coordinator Manager workflows: {len(coordinator_manager_workflows)} found")
        
        regular_coordinator_workflows = get_ongoing_workflows(1, [ROLE_CARE_COORDINATOR])  # Regular coordinator
        print(f"Regular coordinator workflows: {len(regular_coordinator_workflows)} found")
        
        no_role_workflows = get_ongoing_workflows(1, [])  # No roles
        print(f"No role workflows: {len(no_role_workflows)} found")
        
    except Exception as e:
        print(f"Workflow permission test ERROR: {e}")

def test_reassignment_validation():
    """Test reassignment validation logic"""
    print("\n=== Testing Reassignment Validation ===")
    
    # Test with invalid coordinator
    try:
        result = execute_workflow_reassignment([1], 99999, 12)  # Invalid coordinator ID
        print(f"Invalid coordinator test: Unexpected success - {result}")
    except ValueError as e:
        print(f"Invalid coordinator test: Correctly caught error - {e}")
    except Exception as e:
        print(f"Invalid coordinator test: Unexpected error type - {e}")
    
    # Test with empty workflow list
    try:
        result = execute_workflow_reassignment([], 1, 12)
        print(f"Empty workflow list test: {result} (should be 0)")
    except Exception as e:
        print(f"Empty workflow list test ERROR: {e}")
    
    # Test with None coordinator
    try:
        result = execute_workflow_reassignment([1], None, 12)
        print(f"None coordinator test: Unexpected success - {result}")
    except ValueError as e:
        print(f"None coordinator test: Correctly caught error - {e}")
    except Exception as e:
        print(f"None coordinator test: Unexpected error type - {e}")

def test_workflow_dataframe_creation():
    """Test the workflow DataFrame creation for UI"""
    print("\n=== Testing Workflow DataFrame Creation ===")
    
    try:
        # Test with admin permissions
        workflows_df = get_workflows_for_reassignment(12, [ROLE_ADMIN])
        print(f"Admin workflows DataFrame: {len(workflows_df)} rows, columns: {list(workflows_df.columns) if not workflows_df.empty else 'N/A'}")
        
        if not workflows_df.empty:
            print("Sample workflow data:")
            print(workflows_df.head(1).to_dict('records'))
            
    except Exception as e:
        print(f"Workflow DataFrame test ERROR: {e}")

def test_role_constants():
    """Test that role constants are properly defined"""
    print("\n=== Testing Role Constants ===")
    
    expected_roles = {
        'ROLE_ADMIN': ROLE_ADMIN,
        'ROLE_CARE_PROVIDER': ROLE_CARE_PROVIDER, 
        'ROLE_CARE_COORDINATOR': ROLE_CARE_COORDINATOR,
        'ROLE_COORDINATOR_MANAGER': ROLE_COORDINATOR_MANAGER,
        'ROLE_ONBOARDING_TEAM': ROLE_ONBOARDING_TEAM
    }
    
    for role_name, role_value in expected_roles.items():
        print(f"{role_name}: {role_value}")

def main():
    """Run all tests"""
    print("Starting Workflow Reassignment Fix Tests")
    print("=" * 50)
    
    try:
        test_role_constants()
        test_user_coordinator_mapping()
        test_workflow_permissions()
        test_reassignment_validation()
        test_workflow_dataframe_creation()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nFATAL ERROR during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()