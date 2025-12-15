#!/usr/bin/env python3

import sqlite3
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core_utils import get_user_role_ids

# Check what role IDs the get_user_role_ids function returns for user_id 5
user_id = 5
role_ids = get_user_role_ids(user_id)
print(f"Role IDs for user_id {user_id}: {role_ids}")

# Also check the database directly
conn = sqlite3.connect('production.db')
cursor = conn.cursor()
cursor.execute("SELECT role_id FROM user_roles WHERE user_id = ?", (user_id,))
db_role_ids = [row[0] for row in cursor.fetchall()]
print(f"Direct DB query - Role IDs for user_id {user_id}: {db_role_ids}")
conn.close()