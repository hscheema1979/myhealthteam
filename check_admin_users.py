#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core_utils import get_user_role_ids
import sqlite3

def check_admin_users():
    print("=== Checking Admin Users ===")
    
    # Connect to database to get user info
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT user_id, username, full_name FROM users WHERE status = 'active'")
    users = cursor.fetchall()
    
    admin_users = []
    billing_users = []
    
    for user_id, username, full_name in users:
        role_ids = get_user_role_ids(user_id)
        
        # Check for admin role (34)
        if 34 in role_ids:
            admin_users.append((user_id, username, full_name, role_ids))
            print(f"ADMIN: {full_name} ({username}) - Roles: {role_ids}")
        
        # Check for billing access (assuming billing is role 34 + possibly others)
        if any(role_id in [34, 38, 39] for role_id in role_ids):  # Admin, CPM, Data Entry might have billing
            billing_users.append((user_id, username, full_name, role_ids))
    
    print(f"\nTotal Admin Users: {len(admin_users)}")
    print(f"Users with Billing Access: {len(billing_users)}")
    
    # Check specific users
    specific_users = ['justin', 'harpreet', 'bianchi']
    print(f"\n=== Specific User Check ===")
    for username_part in specific_users:
        cursor.execute("SELECT user_id, username, full_name FROM users WHERE username LIKE ? AND status = 'active'", (f'%{username_part}%',))
        matches = cursor.fetchall()
        for user_id, username, full_name in matches:
            role_ids = get_user_role_ids(user_id)
            has_admin = 34 in role_ids
            has_billing = 34 in role_ids  # Admin has billing access
            print(f"{full_name} ({username}): Admin={has_admin}, Billing={has_billing}, Roles={role_ids}")
    
    conn.close()

if __name__ == "__main__":
    check_admin_users()