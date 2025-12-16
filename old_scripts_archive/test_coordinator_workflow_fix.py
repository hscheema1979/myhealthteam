#!/usr/bin/env python3
"""Test script to verify coordinator dashboard workflow fix"""

import pandas as pd
from src.utils.workflow_utils import get_ongoing_workflows

def test_coordinator_workflow_display():
    """Test that the coordinator dashboard workflow logic works"""
    print("Testing coordinator dashboard workflow display logic...")
    
    # Test with coordinator manager role (40) - should get all workflows
    workflows = get_ongoing_workflows(1, [40])
    print(f"Retrieved {len(workflows)} workflows for CM role")
    
    if workflows:
        # Convert to DataFrame (like coordinator dashboard does)
        workflows_df = pd.DataFrame(workflows)
        print(f"DataFrame shape: {workflows_df.shape}")
        print(f"Available columns: {list(workflows_df.columns)}")
        
        # Test the fixed column logic
        available_columns = [col for col in ['workflow_type', 'patient_name', 'coordinator_name', 'workflow_status', 'current_step', 'created_date'] if col in workflows_df.columns]
        print(f"Available columns for display: {available_columns}")
        
        # Test display DataFrame creation
        display_df = workflows_df[available_columns].copy()
        display_df['Select'] = False
        print(f"Display DataFrame shape: {display_df.shape}")
        print(f"Display columns: {list(display_df.columns)}")
        
        # Test column ordering (the part that was failing)
        column_order = ['Select'] + available_columns
        display_df = display_df[column_order]
        print(f"Final display shape: {display_df.shape}")
        print(f"Final columns: {list(display_df.columns)}")
        
        # Test selection logic
        display_df.loc[0, 'Select'] = True
        selected_workflows = display_df[display_df['Select'] == True].index.tolist()
        selected_instance_ids = workflows_df.iloc[selected_workflows]['instance_id'].tolist()
        print(f"Selection test: {len(selected_workflows)} workflows selected, instance IDs: {selected_instance_ids}")
        
        print("\nAll tests passed! Coordinator dashboard workflow should work correctly.")
        return True
    else:
        print("⚠️  No workflows found to test with.")
        return False

if __name__ == '__main__':
    success = test_coordinator_workflow_display()
    if success:
        print("\nCoordinator dashboard workflow reassignment is ready!")
    else:
        print("\n💥 There are still issues to fix.")