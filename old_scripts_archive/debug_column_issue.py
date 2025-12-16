#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.workflow_utils import get_ongoing_workflows
import pandas as pd

print("=== Debugging Column Issue ===")

user_id = 14  # Jan's user_id
user_role_ids = [36, 40]  # CC and CM roles

workflows_data = get_ongoing_workflows(user_id, user_role_ids)

if workflows_data:
    workflows_df = pd.DataFrame(workflows_data)
    
    print(f"Found {len(workflows_df)} workflows")
    print(f"DataFrame columns: {list(workflows_df.columns)}")
    
    # Test the exact column mapping that's causing the error
    expected_columns = ['workflow_type', 'patient_name', 'coordinator_name', 'workflow_status', 'current_step', 'created_date', 'updated_at']
    
    print("Column availability check:")
    for col in expected_columns:
        exists = col in workflows_df.columns
        print(f"   {col}: {'EXISTS' if exists else 'MISSING'}")
    
    # Test the exact filtered column selection
    display_columns = ['workflow_type', 'patient_name', 'coordinator_name', 'workflow_status', 'current_step', 'created_date', 'updated_at']
    available_display_columns = [col for col in display_columns if col in workflows_df.columns]
    
    print(f"Available display columns: {available_display_columns}")
    
    # Test the exact DataFrame operation that's failing
    try:
        display_df = workflows_df[available_display_columns].copy()
        display_df = display_df.rename(columns={
            'workflow_type': 'Workflow Type',
            'patient_name': 'Patient Name',
            'coordinator_name': 'Assigned Coordinator',
            'workflow_status': 'Status',
            'current_step': 'Current Step',
            'created_date': 'Created Date',
            'updated_at': 'Last Updated'
        })
        print("Column mapping successful!")
        print(f"Final DataFrame shape: {display_df.shape}")
        print(f"Final DataFrame columns: {list(display_df.columns)}")
        
    except Exception as e:
        print(f"ERROR in column mapping: {e}")
        import traceback
        traceback.print_exc()

else:
    print("No workflow data returned")

print("\n=== Column Issue Debug Complete ===")