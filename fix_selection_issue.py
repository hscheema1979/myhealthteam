#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.workflow_utils import get_ongoing_workflows
import pandas as pd

print("=== Fixing Selection Issue ===")

user_id = 14  # Jan's user_id
user_role_ids = [36, 40]  # CC and CM roles

print("Testing selection logic...")

try:
    workflows_data = get_ongoing_workflows(user_id, user_role_ids)
    print(f"Found {len(workflows_data)} workflows")
    
    if workflows_data:
        workflows_df = pd.DataFrame(workflows_data)
        
        # Test the EXACT same logic as in coordinator dashboard
        display_df = workflows_df.copy()
        display_df['Select'] = False
        
        # Essential columns
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
            
            print("Creating st.data_editor with proper selection handling...")
            
            # Create the table EXACTLY like coordinator dashboard does
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
                key="workflow_fix_test",
                height=400
            )
            
            print(f"Table created successfully!")
            print(f"Edited DataFrame shape: {edited_df.shape}")
            print(f"Edited DataFrame columns: {list(edited_df.columns)}")
            
            # Check if Select column exists in returned DataFrame
            if 'Select' in edited_df.columns:
                selected_count = len(edited_df[edited_df['Select'] == True])
                print(f"Selection working! {selected_count} workflows selected")
            else:
                print("WARNING: Select column not in returned DataFrame")
                print("Available columns:", list(edited_df.columns))
                
                # Alternative approach - check original DataFrame
                original_selected = len(display_df[display_df['Select'] == True])
                print(f"Original selection count: {original_selected}")
                
        else:
            print("ERROR: No essential columns available")
            
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Selection Fix Test Complete ===")