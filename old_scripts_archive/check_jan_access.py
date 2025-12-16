#!/usr/bin/env python3

import sqlite3

# Check Jan's user info and roles
conn = sqlite3.connect('production.db')
cursor = conn.cursor()

# Find Jan in the users table
cursor.execute("SELECT user_id, username, full_name, email FROM users WHERE full_name LIKE '%jan%' OR username LIKE '%jan%'")
jan_users = cursor.fetchall()

print("Users with 'jan' in name/username:")
for user in jan_users:
    user_id, username, full_name, email = user
    print(f"  User ID: {user_id}, Username: {username}, Full Name: {full_name}, Email: {email}")
    
    # Get Jan's roles
    cursor.execute("""
        SELECT r.role_name, r.role_id 
        FROM user_roles ur 
        JOIN roles r ON ur.role_id = r.role_id 
        WHERE ur.user_id = ?
    """, (user_id,))
    roles = cursor.fetchall()
    
    print(f"    Roles: {[f'{r[0]} ({r[1]})' for r in roles]}")

# Also check what roles should have workflow reassignment access
print("\n=== Roles that should have workflow reassignment access ===")
print("Based on the component code, these roles should have access:")
print("- Admin (34)")  
print("- Coordinator Manager (40)")

# Check if there are any users with Coordinator Manager role
cursor.execute("""
    SELECT u.user_id, u.username, u.full_name 
    FROM users u 
    JOIN user_roles ur ON u.user_id = ur.user_id 
    WHERE ur.role_id = 40
""")
cm_users = cursor.fetchall()

print(f"\nUsers with Coordinator Manager role (40):")
for user in cm_users:
    print(f"  User ID: {user[0]}, Username: {user[1]}, Full Name: {user[2]}")

conn.close()