#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.workflow_utils import get_ongoing_workflows
import pandas as pd

print("=== Debugging Table Display Issues ===")

user_id = 14  # Jan's user_id
user_role_ids = [36, 40]  # CC and CM roles

print("1. Checking if workflows are being retrieved...")
workflows_data = get_ongoing_workflows(user_id, user_role_ids)

print(f"Found {len(workflows_data)} workflows")

if workflows_data:
    print("2. Checking DataFrame creation...")
    workflows_df = pd.DataFrame(workflows_data)
    print(f"DataFrame shape: {workflows_df.shape}")
    print(f"DataFrame columns: {list(workflows_df.columns)}")
    
    print("3. Checking column availability...")
    expected_columns = ['workflow_type', 'patient_name', 'coordinator_name', 'workflow_status', 'current_step', 'created_date', 'updated_at']
    
    for col in expected_columns:
        exists = col in workflows_df.columns
        print(f"   {col}: {'EXISTS' if exists else 'MISSING'}")
    
    print("4. Checking the table filtering logic...")
    
    # Simulate the exact logic from the coordinator dashboard
    display_columns = [
        'Select',
        'workflow_type',
        'patient_name', 
        'coordinator_name',
        'workflow_status',
        'current_step',
        'created_date',
        'updated_at'
    ]
    
    available_columns = [col for col in display_columns if col in workflows_df.columns]
    print(f"Available columns for display: {available_columns}")
    
    if len(available_columns) > 1:  # More than just 'Select'
        display_df = workflows_df[available_columns].copy()
        print(f"Display DataFrame shape: {display_df.shape}")
        print("\n5. First 3 rows of display DataFrame:")
        print(display_df.head(3))
    else:
        print("ERROR: Not enough columns available for display!")
        print("Available columns in workflows_df:", list(workflows_df.columns))
        
        print("\n6. Raw workflow data structure:")
        if workflows_data:
            print("First workflow keys:", list(workflows_data[0].keys()))
            print("First workflow sample:", workflows_data[0])

else:
    print("ERROR: No workflow data returned!")

print("\n=== Debug Complete ===")