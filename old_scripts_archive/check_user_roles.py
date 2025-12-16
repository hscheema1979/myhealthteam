#!/usr/bin/env python3

import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('production.db')

# Query for Sanchez, Bianchi user
user_query = """
SELECT user_id, username, full_name, email, status 
FROM users 
WHERE username LIKE '%sanchez%' OR full_name LIKE '%sanchez%' OR full_name LIKE '%bianchi%'
"""

user_df = pd.read_sql_query(user_query, conn)
print('User data for Sanchez/Bianchi:')
print(user_df)
print()

if not user_df.empty:
    user_id = user_df.iloc[0]['user_id']
    
    # Get user roles
    roles_query = """
    SELECT ur.user_id, r.role_name, r.role_id 
    FROM user_roles ur 
    JOIN roles r ON ur.role_id = r.role_id 
    WHERE ur.user_id = ?
    """
    
    roles_df = pd.read_sql_query(roles_query, conn, params=[user_id])
    print('Roles for this user:')
    print(roles_df)
    print()

# Get all roles
all_roles_query = """SELECT * FROM roles"""
all_roles_df = pd.read_sql_query(all_roles_query, conn)
print('All available roles:')
print(all_roles_df)

conn.close()