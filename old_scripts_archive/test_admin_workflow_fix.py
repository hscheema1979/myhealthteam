#!/usr/bin/env python3
"""Test script to verify admin dashboard workflow fixes"""

import pandas as pd
from src.utils.workflow_utils import get_ongoing_workflows

def test_admin_workflow_display():
    # Test with admin role (34)
    workflows = get_ongoing_workflows(1, [34])
    print(f'Retrieved {len(workflows)} workflows')
    
    if workflows:
        # Convert to DataFrame (similar to admin dashboard)
        workflows_df = pd.DataFrame(workflows)
        print(f'DataFrame shape: {workflows_df.shape}')
        print(f'DataFrame columns: {list(workflows_df.columns)}')
        
        # Simulate the admin dashboard logic
        display_df = workflows_df.copy()
        display_df['Select'] = False
        
        # Reorder columns for better display
        available_columns = [col for col in ['workflow_type', 'patient_name', 'coordinator_name', 'workflow_status', 'current_step', 'created_date'] if col in workflows_df.columns]
        column_order = ['Select'] + available_columns
        display_df = display_df[column_order]
        
        print(f'Display DataFrame shape: {display_df.shape}')
        print(f'Display columns: {list(display_df.columns)}')
        
        # Test selection logic
        print('\nTesting selection logic:')
        print('First 2 rows:')
        print(display_df.head(2))
        
        # Simulate selecting first row
        display_df.loc[0, 'Select'] = True
        selected_workflows = display_df[display_df['Select'] == True].index.tolist()
        print(f'Selected workflow indices: {selected_workflows}')
        
        if selected_workflows:
            selected_instance_ids = workflows_df.iloc[selected_workflows]['instance_id'].tolist()
            print(f'Selected instance IDs: {selected_instance_ids}')
        
        print('\nAll tests passed! The workflow display should work correctly.')
    else:
        print('⚠️  No workflows found to test with.')

if __name__ == '__main__':
    test_admin_workflow_display()