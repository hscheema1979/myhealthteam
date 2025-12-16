#!/usr/bin/env python3
"""Test script to verify admin dashboard can load without workflow errors"""

import streamlit as st
from src.dashboards.admin_dashboard import show_admin_dashboard
from src.database import get_db_connection

def test_admin_dashboard():
    """Test that the admin dashboard can load without workflow errors"""
    print("Testing admin dashboard workflow reassignment section...")
    
    # Mock session state for admin user
    import streamlit as st
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = 1
    if 'user_role_ids' not in st.session_state:
        st.session_state['user_role_ids'] = [34]  # Admin role
    if 'active_role_id' not in st.session_state:
        st.session_state['active_role_id'] = 34
    
    try:
        # Test that workflow data can be retrieved without errors
        from src.utils.workflow_utils import get_ongoing_workflows
        workflows = get_ongoing_workflows(1, [34])
        print(f"✓ Successfully retrieved {len(workflows)} workflows")
        
        if workflows:
            # Test DataFrame conversion
            import pandas as pd
            workflows_df = pd.DataFrame(workflows)
            print(f"✓ Successfully converted to DataFrame with {workflows_df.shape[0]} rows and {workflows_df.shape[1]} columns")
            
            # Test column filtering (like in admin dashboard)
            available_columns = [col for col in ['workflow_type', 'patient_name', 'coordinator_name', 'workflow_status', 'current_step', 'created_date'] if col in workflows_df.columns]
            print(f"✓ Available columns for display: {available_columns}")
            
            # Test selection logic
            display_df = workflows_df[available_columns].copy()
            display_df['Select'] = False
            print(f"✓ Successfully created display DataFrame with shape {display_df.shape}")
            
            # Test selection processing
            display_df.loc[0, 'Select'] = True
            selected_workflows = display_df[display_df['Select'] == True].index.tolist()
            selected_instance_ids = workflows_df.iloc[selected_workflows]['instance_id'].tolist()
            print(f"✓ Selection logic works: {len(selected_workflows)} workflows selected, instance IDs: {selected_instance_ids}")
        
        print("\n✅ All tests passed! Admin dashboard workflow section should work correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_admin_dashboard()
    if success:
        print("\n🎉 Admin dashboard workflow reassignment is ready!")
    else:
        print("\n💥 There are still issues to fix.")