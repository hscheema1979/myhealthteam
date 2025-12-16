#!/usr/bin/env python3
"""
Minimal test to check if the issue is with pandas or DataFrame handling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test direct import and usage
import pandas as pd
from src.utils.workflow_utils import get_workflows_for_reassignment

def test_minimal():
    """Minimal test without any mocking"""
    print("=== Minimal Test ===")
    
    # Test with Jan's actual user info
    user_id = 14
    user_role_ids = [36, 40]
    
    print(f"Testing with user_id={user_id}, user_role_ids={user_role_ids}")
    
    try:
        # This is the exact function call from admin_dashboard.py
        workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
        
        print(f"Function returned type: {type(workflows_df)}")
        print(f"DataFrame shape: {workflows_df.shape}")
        print(f"DataFrame empty: {workflows_df.empty}")
        print(f"DataFrame columns: {list(workflows_df.columns)}")
        
        if workflows_df.empty:
            print("FAIL: DataFrame is empty - this would show 'No active workflows'")
        else:
            print(f"SUCCESS: DataFrame has {len(workflows_df)} rows")
            print("First workflow:", workflows_df.iloc[0].to_dict())
            
        # Test the exact condition from admin_dashboard.py
        if workflows_df.empty:
            print("UI would show: 'No active workflows available for reassignment.'")
        else:
            print("UI would show the workflow table")
            
    except Exception as e:
        print(f"FAIL Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal()