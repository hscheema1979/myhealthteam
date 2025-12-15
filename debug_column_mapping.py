#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.workflow_reassignment_utils import get_workflows_for_reassignment

print("=== Debugging Column Mapping ===")

# Test with Jan's credentials
user_id = 14
user_role_ids = [36, 40]

workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)

if not workflows_df.empty:
    print(f"DataFrame has {len(workflows_df)} rows")
    print(f"DataFrame columns: {list(workflows_df.columns)}")
    print("\nFirst row data:")
    print(workflows_df.iloc[0].to_dict())
    
    # Check which columns exist for summary
    print("\nColumn availability check:")
    for col in ['Workflow Type', 'Patient Name', 'Assigned Coordinator', 'Status', 'Current Step']:
        exists = col in workflows_df.columns
        print(f"  {col}: {'EXISTS' if exists else 'MISSING'}")
        
else:
    print("No workflows returned")