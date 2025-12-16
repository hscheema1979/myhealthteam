#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.components.workflow_reassignment_component import show_workflow_reassignment_component
import streamlit as st

# Test the component directly
print("Testing workflow reassignment component...")

try:
    # Simulate Streamlit app context
    st.set_page_config(page_title="Workflow Test", layout="wide")
    
    # Test with Bianchi's user ID (5) and admin role (34)
    user_id = 5
    user_role_ids = [34]  # Admin role
    
    print(f"Testing with user_id={user_id}, role_ids={user_role_ids}")
    
    # This should work now with the real database
    show_workflow_reassignment_component(user_id, user_role_ids)
    
    print("✅ Component loaded successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()