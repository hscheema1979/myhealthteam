#!/usr/bin/env python3
"""
Debug the build_provider_map function to see what's happening
"""

import sqlite3
import pandas as pd
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_build_provider_map():
    print("Debugging build_provider_map function")
    print("=" * 50)
    
    conn = sqlite3.connect('production.db')
    
    # Get users data directly
    cursor = conn.execute(
        "SELECT user_id, first_name, last_name, full_name, username, alias FROM users WHERE status != 'deleted'"
    )
    users = cursor.fetchall()
    
    print(f"Found {len(users)} users in database")
    
    provis = {}
    id_to_name = {}
    
    for uid, fn, ln, full_name, uname, alias in users:
        fn = fn or ""
        ln = ln or ""
        full_name = full_name or f"{fn} {ln}".strip()
        uname = uname or ""
        alias = alias or ""
        
        print(f"\nProcessing user {uid}:")
        print(f"  full_name: '{full_name}'")
        print(f"  first_name: '{fn}'")
        print(f"  last_name: '{ln}'")
        print(f"  username: '{uname}'")
        
        # Store reverse mapping
        id_to_name[uid] = full_name
        
        # Check if full_name should be added to provis
        if full_name:
            print(f"  Adding full_name to provis: '{full_name.upper()}'")
            provis[full_name.upper()] = uid
        else:
            print(f"  No full_name to add")
    
    print(f"\nFinal provis count: {len(provis)}")
    print("Full name entries in provis:")
    for name, uid in provis.items():
        if ',' in name:
            print(f"  '{name}' -> ID: {uid}")
    
    print(f"\nid_to_name count: {len(id_to_name)}")
    print("id_to_name entries:")
    for uid, name in id_to_name.items():
        print(f"  ID {uid}: '{name}'")
    
    conn.close()

if __name__ == "__main__":
    debug_build_provider_map()