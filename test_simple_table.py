#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.workflow_utils import get_ongoing_workflows
import streamlit as st

print("=== Testing Simple Table Display ===")

# Test with Jan's credentials
user_id = 14  # Jan's user_id
user_role_ids = [36, 40]  # CC and CM roles

print("Testing basic table display...")

try:
    workflows_data = get_ongoing_workflows(user_id, user_role_ids)
    print(f"Found {len(workflows_data)} workflows")
    
    if workflows_data:
        import pandas as pd
        workflows_df = pd.DataFrame(workflows_data)
        
        print("Creating simple table...")
        
        # Create the EXACT same table structure as in the coordinator dashboard
        display_df = workflows_df.copy()
        display_df['Select'] = False
        
        # Test with just a few essential columns first
        essential_cols = ['workflow_type', 'patient_name', 'coordinator_name', 'current_step']
        available_cols = [col for col in essential_cols if col in workflows_df.columns]
        
        if available_cols:
            display_df = display_df[available_cols].copy()
            display_df = display_df.rename(columns={
                'workflow_type': 'Workflow Type',
                'patient_name': 'Patient Name',
                'coordinator_name': 'Assigned Coordinator',
                'current_step': 'Current Step'
            })
            
            print("Creating st.data_editor...")
            print(f"DataFrame shape: {display_df.shape}")
            print(f"Columns: {list(display_df.columns)}")
            
            # Test the EXACT same st.data_editor call as in coordinator dashboard
            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Select": st.column_config.CheckboxColumn("Select", default=False),
                    "Workflow Type": st.column_config.TextColumn("Workflow Type"),
                    "Patient Name": st.column_config.TextColumn("Patient Name"),
                    "Assigned Coordinator": st.column_config.TextColumn("Assigned Coordinator"),
                    "Current Step": st.column_config.NumberColumn("Current Step")
                },
                key="test_workflow_table",
                height=300
            )
            
            print("Table displayed successfully!")
            
            # Test selection
            if len(edited_df[edited_df['Select'] == True]) > 0:
                print("Selection working!")
                selected = edited_df[edited_df['Select'] == True]
                print(f"Selected {len(selected)} workflows")
            else:
                print("No workflows selected")
                
        else:
            print("ERROR: No essential columns available!")
            print("Available columns:", list(workflows_df.columns))
            
    else:
        print("No workflow data returned")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Basic Table Test Complete ===")