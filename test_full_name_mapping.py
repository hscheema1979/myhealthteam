#!/usr/bin/env python3
"""
Test if full names are properly mapped in the provider map
"""

import sqlite3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transform_production_data_v3_fixed import build_provider_map

def test_full_name_mapping():
    print("Testing full name mapping in provider map")
    print("=" * 50)
    
    # Get provider map from database
    conn = sqlite3.connect('production.db')
    provider_map, id_to_name = build_provider_map(conn)
    
    print("Testing specific full name mappings:")
    
    # Test the exact names from ZMO data
    test_names = [
        "Szalas NP, Andrew",
        "Antonio NP, Ethel", 
        "Jackson PA, Anisha",
        "Dabalus NP, Eden",
        "Atencio, Dianela"
    ]
    
    for name in test_names:
        provider_id = provider_map.get(name.upper())
        print(f"  '{name}' -> ID: {provider_id}")
        
        # Also try without the NP/PA suffixes
        name_clean = name.replace(" NP,", ",").replace(" PA,", ",").replace(" MD,", ",")
        provider_id_clean = provider_map.get(name_clean.upper())
        if provider_id_clean:
            print(f"    Clean '{name_clean}' -> ID: {provider_id_clean}")
    
    print(f"\nTotal provider map entries: {len(provider_map)}")
    
    # Show some entries that contain commas (full names)
    full_name_entries = {k: v for k, v in provider_map.items() if ',' in k}
    print(f"Entries with commas (full names): {len(full_name_entries)}")
    for name, uid in list(full_name_entries.items())[:10]:
        print(f"  '{name}' -> ID: {uid}")
    
    conn.close()

if __name__ == "__main__":
    test_full_name_mapping()