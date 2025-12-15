#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.components.workflow_reassignment_component import show_workflow_reassignment_component
import streamlit as st

# Test the new workflow reassignment component
print("=== Testing New Workflow Reassignment Interface ===")

# Simulate the component being called by the coordinator dashboard
try:
    # Test with Jan's user ID and coordinator manager role
    user_id = 14  # Jan's user_id
    user_role_ids = [36, 40]  # CC and CM roles
    
    print(f"Testing with user_id={user_id}, role_ids={user_role_ids}")
    
    # This should now show the real workflow interface
    show_workflow_reassignment_component(user_id, user_role_ids)
    
    print("✅ Component loaded successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()