#!/usr/bin/env python3
"""
Simple syntax test for the workflow replacement
"""

import ast

# Simple test of the core logic without problematic strings
test_code = '''
import streamlit as st
import pandas as pd

def test_workflow():
    with tab_workflow:
        st.subheader("Workflow Reassignment")
        st.markdown("Admin-level workflow management")
        
        debug_mode = st.session_state.get('admin_debug_session', False)
        
        try:
            conn = db.get_db_connection()
            result = conn.execute("SELECT * FROM workflow_instances WHERE workflow_status = 'Active'")
            workflows = result.fetchall()
            conn.close()
            
            if workflows:
                workflows_df = pd.DataFrame([dict(wf) for wf in workflows])
            else:
                workflows_df = pd.DataFrame()
            
        except Exception as e:
            st.error(f"Error: {e}")
            workflows_df = pd.DataFrame()
        
        if workflows_df.empty:
            st.info("No workflows available")
        else:
            st.success(f"Found {len(workflows_df)} workflows")
            
            from src.utils.workflow_utils import get_reassignment_summary
            summary = get_reassignment_summary(workflows_df)
            
            st.metric("Total Workflows", summary['total_workflows'])
            
            from src.utils.workflow_reassignment_ui import show_workflow_reassignment_table
            selected_instance_ids, should_rerun = show_workflow_reassignment_table(
                workflows_df=workflows_df,
                user_id=user_id,
                table_key="admin_workflow",
                show_search_filter=True
            )
            
            if should_rerun:
                st.rerun()
'''

try:
    ast.parse(test_code)
    print("Core syntax is correct!")
except Exception as e:
    print(f"Syntax error: {e}")

# Now test the actual replacement file structure
print("\nTesting actual replacement structure...")

# Read the replacement file and check just the function structure
with open('workflow_replacement.py', 'r') as f:
    content = f.read()

# Extract just the function part (skip the header comments)
lines = content.split('\n')
func_start = None
for i, line in enumerate(lines):
    if 'with tab_workflow:' in line:
        func_start = i
        break

if func_start:
    func_code = '\n'.join(lines[func_start:])
    try:
        ast.parse(func_code)
        print("Function structure is correct!")
    except Exception as e:
        print(f"Function syntax error: {e}")
        print("First few lines of function:")
        for i, line in enumerate(lines[func_start:func_start+10], 1):
            print(f"{i}: {repr(line)}")
else:
    print("Could not find function start")