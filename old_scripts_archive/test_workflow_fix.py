import sys
sys.path.append('src')
from src.utils.workflow_utils import get_workflows_for_reassignment, get_available_coordinators
import pandas as pd

# Test workflow reassignment functionality
print('Testing workflow reassignment functions...')

# Test get_available_coordinators
coordinators = get_available_coordinators()
print(f'Available coordinators: {len(coordinators)} found')
for coord in coordinators[:3]:  # Show first 3
    print(f'  - {coord["full_name"]} (ID: {coord["user_id"]})')

# Test get_workflows_for_reassignment
workflows_df = get_workflows_for_reassignment(1, [34, 40])  # Admin user with roles
print(f'\nWorkflows for reassignment: {len(workflows_df)} total')
if not workflows_df.empty:
    print('Columns available:', list(workflows_df.columns))
    print('Sample workflow data:')
    for idx, row in workflows_df.head(3).iterrows():
        print(f'  {dict(row)}')
else:
    print('No workflows found')
