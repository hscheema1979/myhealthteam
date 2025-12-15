#!/usr/bin/env python3
"""
Debug script to investigate why admin users can't see workflows for reassignment
"""

import sqlite3
import pandas as pd
from src import database
from src.utils.workflow_utils import get_ongoing_workflows, get_workflows_for_reassignment

# Role constants
ROLE_ADMIN = 34
ROLE_CARE_PROVIDER = 33
ROLE_CARE_COORDINATOR = 36
ROLE_COORDINATOR_MANAGER = 40
ROLE_ONBOARDING_TEAM = 37

def test_workflow_access():
    """Test workflow access for different user types"""
    
    print("=== Debugging Workflow Reassignment Issue ===\n")
    
    # Test users
    test_users = [
        {"user_id": 5, "full_name": "Sanchez, Bianchi", "roles": [34]},  # Admin only
        {"user_id": 14, "full_name": "Estomo, Jan", "roles": [36, 40]},  # CC + CM
        {"user_id": 12, "full_name": "Cheema, Harpreet", "roles": [34]},  # Admin only
    ]
    
    for user in test_users:
        print(f"Testing user: {user['full_name']} (ID: {user['user_id']})")
        print(f"Roles: {user['roles']}")
        
        try:
            # Test get_ongoing_workflows directly
            ongoing_workflows = get_ongoing_workflows(user['user_id'], user['roles'])
            print(f"  get_ongoing_workflows() returned: {len(ongoing_workflows)} workflows")
            
            if ongoing_workflows:
                print(f"  First workflow: {ongoing_workflows[0]}")
            
            # Test get_workflows_for_reassignment
            reassignment_workflows = get_workflows_for_reassignment(user['user_id'], user['roles'])
            print(f"  get_workflows_for_reassignment() returned: {len(reassignment_workflows)} workflows")
            
            if not reassignment_workflows.empty:
                print(f"  Columns: {list(reassignment_workflows.columns)}")
                print(f"  First row: {reassignment_workflows.iloc[0].to_dict()}")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 50)
    
    # Check database directly
    print("\n=== Direct Database Check ===")
    conn = database.get_db_connection()
    
    try:
        # Check total active workflows
        result = conn.execute("SELECT COUNT(*) as count FROM workflow_instances WHERE workflow_status = 'Active'")
        total_active = result.fetchone()['count']
        print(f"Total active workflows in database: {total_active}")
        
        # Check admin query specifically
        admin_query = """
            SELECT *, (
                SELECT COUNT(*) FROM workflow_steps ws WHERE ws.template_id = wi.template_id
            ) as total_steps
            FROM workflow_instances wi
            WHERE workflow_status = 'Active'
            ORDER BY created_at DESC
        """
        admin_results = conn.execute(admin_query).fetchall()
        print(f"Admin query returned: {len(admin_results)} workflows")
        
        if admin_results:
            print(f"First result keys: {list(admin_results[0].keys())}")
            print(f"Sample data: {dict(admin_results[0])}")
        
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_workflow_access()