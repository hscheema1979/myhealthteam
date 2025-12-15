#!/usr/bin/env python3
"""
Debug exact mapping between ZMO names and database full names
"""

import sqlite3
import pandas as pd
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transform_production_data_v3_fixed import build_provider_map

def debug_exact_mapping():
    print("Debugging exact mapping between ZMO and database")
    print("=" * 60)
    
    # Get provider map from database
    conn = sqlite3.connect('production.db')
    provider_map, id_to_name = build_provider_map(conn)
    
    print("Database full names (uppercase):")
    cursor = conn.execute("SELECT user_id, full_name FROM users WHERE status != 'deleted'")
    db_names = {}
    for uid, full_name in cursor.fetchall():
        if full_name:
            db_names[full_name.upper()] = uid
            print(f"  '{full_name.upper()}' -> ID: {uid}")
    
    # Check ZMO data
    zmo_path = 'downloads/ZMO_MAIN.csv'
    if os.path.exists(zmo_path):
        df = pd.read_csv(zmo_path)
        
        prov_col = 'Assigned \nReg Prov'
        if prov_col in df.columns:
            zmo_providers = df[prov_col].dropna().unique()
            print(f"\nZMO provider names (uppercase):")
            for zmo_name in zmo_providers[:10]:  # Just first 10
                zmo_upper = zmo_name.upper().strip()
                print(f"  '{zmo_upper}'")
                
                # Check exact match
                if zmo_upper in db_names:
                    print(f"    *** EXACT MATCH FOUND! -> ID: {db_names[zmo_upper]}")
                else:
                    print(f"    No exact match in database")
            
            # Test specific problematic names
            test_names = ["Szalas NP, Andrew", "Antonio NP, Ethel"]
            print(f"\nTesting specific names:")
            for name in test_names:
                zmo_upper = name.upper()
                print(f"  ZMO: '{zmo_upper}'")
                print(f"    In provider_map: {zmo_upper in provider_map}")
                print(f"    In db_names: {zmo_upper in db_names}")
                if zmo_upper in provider_map:
                    print(f"    Provider ID: {provider_map[zmo_upper]}")
    
    conn.close()

if __name__ == "__main__":
    debug_exact_mapping()