#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.workflow_utils import get_ongoing_workflows

print("=== Debugging Workflow Column Names ===")

# Test with Jan's credentials
user_id = 14
user_role_ids = [36, 40]

workflows_data = get_ongoing_workflows(user_id, user_role_ids)

if workflows_data:
    print(f"Found {len(workflows_data)} workflows")
    
    # Check first workflow to see column names
    if len(workflows_data) > 0:
        first_workflow = workflows_data[0]
        print("\nFirst workflow data:")
        for key, value in first_workflow.items():
            print(f"  {key}: {value}")
            
    # Convert to DataFrame to see structure
    import pandas as pd
    df = pd.DataFrame(workflows_data)
    print(f"\nDataFrame columns: {list(df.columns)}")
    print(f"\nDataFrame shape: {df.shape}")
    
    if not df.empty:
        print("\nFirst 3 rows:")
        print(df.head(3))
        
else:
    print("No workflow data returned")

print("\n=== Analysis Complete ===")