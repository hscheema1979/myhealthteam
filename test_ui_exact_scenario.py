#!/usr/bin/env python3
"""
Test the exact scenario that happens in the UI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Simulate Streamlit session state
class MockSessionState:
    def __init__(self):
        self._data = {
            "user_id": 14,
            "authenticated_user": {
                "user_id": 14,
                "full_name": "Estomo, Jan",
                "email": "jan@example.com"
            },
            "user_role_ids": [36, 40]
        }
    
    def get(self, key, default=None):
        return self._data.get(key, default)

# Mock streamlit module
class MockStreamlit:
    def __init__(self):
        self.session_state = MockSessionState()
    
    def write(self, text):
        print(f"ST WRITE: {text}")
    
    def error(self, text):
        print(f"ST ERROR: {text}")

# Mock the streamlit module
import types
mock_st = MockStreamlit()
sys.modules['streamlit'] = mock_st

# Import after mocking
import pandas as pd
from src.utils.workflow_utils import (
    get_workflows_for_reassignment,
    get_ongoing_workflows,
    ROLE_ADMIN, ROLE_CARE_COORDINATOR, ROLE_COORDINATOR_MANAGER
)

def test_exact_ui_scenario():
    """Test the exact scenario that happens in the UI"""
    print("=== Testing Exact UI Scenario ===")
    
    # Simulate the exact variables from admin_dashboard.py
    user_id = mock_st.session_state.get("user_id", None)
    current_user = mock_st.session_state.get("authenticated_user", {})
    user_role_ids = mock_st.session_state.get('user_role_ids', [])
    
    print(f"user_id: {user_id}")
    print(f"current_user: {current_user}")
    print(f"user_role_ids: {user_role_ids}")
    
    # This is the exact call that happens in the UI
    try:
        workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
        print(f"workflows_df.shape: {workflows_df.shape}")
        print(f"workflows_df.empty: {workflows_df.empty}")
        
        if workflows_df.empty:
            print("UI would show: 'No active workflows available for reassignment.'")
        else:
            print(f"UI would show workflows: {len(workflows_df)} found")
            print("First few workflow IDs:", workflows_df['instance_id'].head(3).tolist())
            
    except Exception as e:
        print(f"Exception occurred: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_exact_ui_scenario()