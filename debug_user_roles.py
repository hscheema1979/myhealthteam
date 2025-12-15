#!/usr/bin/env python3

import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('production.db')

# Check user_roles table structure
print("=== User Roles Table Structure ===")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(user_roles)")
columns = cursor.fetchall()
for col in columns:
    print(f"Column: {col[1]} (Type: {col[2]})")
print()

# Check all entries for user_id 5
print("=== All user_roles entries for user_id 5 ===")
cursor.execute("SELECT * FROM user_roles WHERE user_id = 5")
entries = cursor.fetchall()
for entry in entries:
    print(f"Entry: {entry}")
print()

# Check if there are any issues with the join
print("=== Direct check of user_roles for user_id 5 ===")
cursor.execute("SELECT role_id FROM user_roles WHERE user_id = 5")
role_ids = cursor.fetchall()
print(f"Role IDs found: {[r[0] for r in role_ids]}")
print()

# Check roles table
print("=== Roles table entries ===")
cursor.execute("SELECT * FROM roles WHERE role_id IN (SELECT role_id FROM user_roles WHERE user_id = 5)")
roles = cursor.fetchall()
for role in roles:
    print(f"Role: {role}")

conn.close()