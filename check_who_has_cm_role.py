#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src import database as db

print("=== Checking Who Has Coordinator Manager Role ===")

conn = db.get_db_connection()
cursor = conn.cursor()

# Get users with role 40 (Coordinator Manager)
cursor.execute("""
    SELECT u.user_id, u.username, u.full_name, r.role_name 
    FROM users u 
    JOIN user_roles ur ON u.user_id = ur.user_id 
    JOIN roles r ON ur.role_id = r.role_id 
    WHERE ur.role_id = 40 AND u.status = 'active'
    ORDER BY u.full_name
""")

cm_users = cursor.fetchall()

print("Users with Coordinator Manager role (40):")
for user in cm_users:
    print(f"  - ID: {user['user_id']}, Username: {user['username']}, Name: {user['full_name']}")

conn.close()

if cm_users:
    print(f"\nTotal users with CM role: {len(cm_users)}")
else:
    print("No users found with Coordinator Manager role")

print("\nThese users will see the workflow reassignment functionality!")