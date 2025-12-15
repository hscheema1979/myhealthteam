#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core_utils import get_user_role_ids
import sqlite3

def test_bianchi_access():
    print("=== Testing Bianchi's Access ===")
    
    # Test using the core_utils function (what app.py uses)
    user_id = 5  # Bianchi's user_id
    role_ids = get_user_role_ids(user_id)
    print(f"Bianchi's role IDs from core_utils: {role_ids}")
    
    # Check if she has admin role
    has_admin = 34 in role_ids
    print(f"Has Admin role (34): {has_admin}")
    
    # Test direct database query
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role_id FROM user_roles WHERE user_id = ?", (user_id,))
    db_role_ids = [row[0] for row in cursor.fetchall()]
    print(f"Bianchi's role IDs from direct DB query: {db_role_ids}")
    conn.close()
    
    # Check what dashboard she should see
    if 34 in role_ids:
        print("✅ Should see ADMIN dashboard with all tabs")
    elif 33 in role_ids:
        print("Should see PROVIDER dashboard")
    elif 36 in role_ids:
        print("Should see COORDINATOR dashboard")
    else:
        print("❌ Should see minimal/default dashboard")

if __name__ == "__main__":
    test_bianchi_access()