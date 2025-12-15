#!/usr/bin/env python3
"""
Debug the name conversion from ZMO to username format
"""

import sqlite3
import pandas as pd
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transform_production_data_v3_fixed import convert_zmo_name_to_username, build_provider_map

def debug_name_conversion():
    print("Debugging ZMO name to username conversion")
    print("=" * 50)
    
    # Get provider map from database
    conn = sqlite3.connect('production.db')
    provider_map, id_to_name = build_provider_map(conn)
    
    print("Provider map keys (usernames):")
    for username in sorted(provider_map.keys()):
        print(f"  '{username}' -> ID {provider_map[username]}")
    
    # Test some ZMO names
    test_zmo_names = [
        "Szalas NP, Andrew",
        "Antonio NP, Ethel", 
        "Jackson PA, Anisha",
        "Dabalus NP, Eden",
        "Atencio, Dianela"
    ]
    
    print(f"\nTesting name conversion:")
    for zmo_name in test_zmo_names:
        username = convert_zmo_name_to_username(zmo_name)
        provider_id = provider_map.get(username) if username else None
        print(f"  ZMO: '{zmo_name}'")
        print(f"    -> Username: '{username}'")
        print(f"    -> Provider ID: {provider_id}")
        print()
    
    # Check actual ZMO data
    zmo_path = 'downloads/ZMO_MAIN.csv'
    if os.path.exists(zmo_path):
        df = pd.read_csv(zmo_path, nrows=10)
        
        prov_col = 'Assigned \nReg Prov'
        cm_col = 'Assigned\nCM'
        
        if prov_col in df.columns:
            print("Sample ZMO provider assignments:")
            for _, row in df.iterrows():
                zmo_prov = row[prov_col]
                if pd.notna(zmo_prov):
                    username = convert_zmo_name_to_username(zmo_prov)
                    provider_id = provider_map.get(username) if username else None
                    print(f"  '{zmo_prov}' -> '{username}' -> ID: {provider_id}")
            print()
        
        if cm_col in df.columns:
            print("Sample ZMO coordinator assignments:")
            for _, row in df.iterrows():
                zmo_cm = row[cm_col]
                if pd.notna(zmo_cm):
                    username = convert_zmo_name_to_username(zmo_cm)
                    provider_id = provider_map.get(username) if username else None
                    print(f"  '{zmo_cm}' -> '{username}' -> ID: {provider_id}")
    
    conn.close()

if __name__ == "__main__":
    debug_name_conversion()