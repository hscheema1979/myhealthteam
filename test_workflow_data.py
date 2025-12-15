#!/usr/bin/env python3
"""Test script to check workflow data structure"""

from src.utils.workflow_utils import get_ongoing_workflows
from src.database import get_db_connection

def test_workflow_data():
    # Test the workflow data retrieval
    conn = get_db_connection()
    cursor = conn.execute("SELECT COUNT(*) as count FROM workflow_instances WHERE workflow_status = 'Active'")
    count = cursor.fetchone()['count']
    print(f'Active workflows in database: {count}')

    # Test with admin role (34)
    workflows = get_ongoing_workflows(1, [34])
    print(f'Retrieved {len(workflows)} workflows')
    if workflows:
        print('Available columns:', list(workflows[0].keys()))
        # Show first workflow as example
        print('First workflow sample:')
        for key, value in workflows[0].items():
            print(f'  {key}: {value}')
    conn.close()

if __name__ == '__main__':
    test_workflow_data()