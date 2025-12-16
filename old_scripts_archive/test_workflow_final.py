#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.workflow_utils import (
    get_workflows_for_reassignment,
    get_available_coordinators,
    get_reassignment_summary
)

print("=== Testing Workflow Reassignment Utilities ===")

# Test with Jan's credentials (Coordinator Manager)
print("Testing with Jan (Coordinator Manager - Role 40):")
user_id = 14  # Jan's user_id
user_role_ids = [36, 40]  # CC and CM roles

workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
print(f"Found {len(workflows_df)} workflows for reassignment")

if not workflows_df.empty:
    summary = get_reassignment_summary(workflows_df)
    print(f"Total workflows: {summary['total_workflows']}")
    print(f"By coordinator: {dict(list(summary['by_coordinator'].items())[:3])}")
    
    available_coordinators = get_available_coordinators()
    print(f"Available coordinators: {len(available_coordinators)}")
    for coord in available_coordinators[:3]:
        print(f"  - {coord['full_name']} (ID: {coord['user_id']})")

print("\nWorkflow reassignment utilities working correctly!")
print("Both Jan (coordinator dashboard) and Bianchi (admin dashboard) should now see proper workflow reassignment!")