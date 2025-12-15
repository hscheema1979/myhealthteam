#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.components.workflow_reassignment_component import show_workflow_reassignment_component
import streamlit as st

print("=== Testing Complete Workflow Reassignment Interface ===")

# Test with Jan's credentials (Coordinator Manager)
try:
    user_id = 14  # Jan's user_id  
    user_role_ids = [36, 40]  # CC and CM roles
    
    print(f"Testing with user_id={user_id}, role_ids={user_role_ids}")
    print("This should show the real workflow reassignment interface")
    print("Expected features:")
    print("- Real workflow data (89 workflows)")
    print("- Multi-select checkboxes for bulk reassignment")
    print("- Coordinator dropdown for target assignment")
    print("- Filters by coordinator, workflow type, status")
    print("- Summary statistics")
    
    # This will show the full interface
    show_workflow_reassignment_component(user_id, user_role_ids)
    
    print("✅ Interface loaded successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()