#!/usr/bin/env python3

import sqlite3
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src import database as db

# Debug Jan's dashboard access
print("=== Debugging Jan's Dashboard Access ===")

# Check Jan's user info
conn = sqlite3.connect('production.db')
cursor = conn.cursor()

# Find Jan
cursor.execute("SELECT user_id, username, full_name FROM users WHERE username = 'estomo.jan'")
jan = cursor.fetchone()

if jan:
    user_id, username, full_name = jan
    print(f"Jan found: User ID {user_id}, Username {username}, Full Name {full_name}")
    
    # Get Jan's roles
    user_roles = db.get_user_roles_by_user_id(user_id)
    role_ids = [r["role_id"] for r in user_roles]
    role_names = [r["role_name"] for r in user_roles]
    
    print(f"Jan's roles: {role_ids} - {role_names}")
    
    # Check what dashboard role Jan should get
    print(f"Has Admin (34): {34 in role_ids}")
    print(f"Has Coordinator Manager (40): {40 in role_ids}")
    print(f"Has Care Coordinator (36): {36 in role_ids}")
    
    # Based on the logic, Jan should see the admin dashboard because he has role 40
    if 34 in role_ids or 40 in role_ids:
        print("Jan should see the ADMIN dashboard with Workflow Reassignment tab")
    else:
        print("Jan should NOT see the admin dashboard")
        
else:
    print("❌ Jan not found in database")

conn.close()