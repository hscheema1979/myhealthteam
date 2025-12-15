#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.dashboards.workflow_module import get_workflow_templates, get_ongoing_workflows
from src.utils.workflow_utils import get_ongoing_workflows as workflow_utils_get

print("=== Testing Existing Workflow Infrastructure ===")

# Test with Jan's credentials (Coordinator Manager)
user_id = 14  # Jan's user_id
user_role_ids = [36, 40]  # CC and CM roles

print("1. Testing workflow_module.get_workflow_templates():")
try:
    templates = get_workflow_templates()
    print(f"   Found {len(templates)} workflow templates")
    for template in templates[:3]:
        print(f"   - ID: {template['template_id']}, Name: {template['template_name']}")
except Exception as e:
    print(f"   Error: {e}")

print("\n2. Testing existing get_ongoing_workflows():")
try:
    workflows = workflow_utils_get(user_id, user_role_ids)
    print(f"   Found {len(workflows)} ongoing workflows")
    
    if workflows:
        print("   Sample workflow structure:")
        for key, value in workflows[0].items():
            print(f"   - {key}: {value}")
            
except Exception as e:
    print(f"   Error: {e}")

print("\n3. What should the workflow reassignment table look like?")
print("   - Should match existing coordinator patient tables")
print("   - Use st.data_editor() with proper formatting")
print("   - Include selection checkboxes for bulk operations")
print("   - Show real workflow data, not demo data")