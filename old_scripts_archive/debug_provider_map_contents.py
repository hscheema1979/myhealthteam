#!/usr/bin/env python3
"""
Debug what's actually in the provider map
"""

import sqlite3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transform_production_data_v3_fixed import build_provider_map, clean_name_for_matching

def debug_provider_map_contents():
    print("Debugging provider map contents")
    print("=" * 50)
    
    # Get provider map from database
    conn = sqlite3.connect('production.db')
    provider_map, id_to_name = build_provider_map(conn)
    
    print(f"Provider map has {len(provider_map)} entries")
    
    # Look for entries with commas (full names)
    print("\nEntries with commas (full names):")
    full_name_entries = {}
    for name, uid in provider_map.items():
        if ',' in name:
            full_name_entries[name] = uid
            print(f"  '{name}' -> ID: {uid}")
    
    # Test the specific names we need
    test_names = ["SZALAS NP, ANDREW", "ANTONIO NP, ETHEL", "OTEGBULU, ANGELA", "ATENCIO, DIANELA"]
    
    print(f"\nTesting specific names against full name entries:")
    for test_name in test_names:
        print(f"\nLooking for: '{test_name}'")
        
        # Check exact match in full names
        if test_name in full_name_entries:
            print(f"  *** EXACT MATCH in full names -> ID: {full_name_entries[test_name]}")
        else:
            print(f"  Not found in full names")
            
            # Try fuzzy matching against full names only
            from difflib import SequenceMatcher
            best_match = None
            best_ratio = 0
            
            for map_name in full_name_entries.keys():
                ratio = SequenceMatcher(None, test_name, map_name).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = map_name
            
            if best_match and best_ratio > 0.8:
                print(f"  *** FUZZY MATCH ({best_ratio:.2f}) -> '{best_match}' -> ID: {full_name_entries[best_match]}")
            else:
                print(f"  No good fuzzy match (best: {best_ratio:.2f})")
    
    # Also check what's in the id_to_name mapping
    print(f"\nid_to_name mapping:")
    for uid, name in id_to_name.items():
        print(f"  ID {uid}: '{name}'")
    
    conn.close()

if __name__ == "__main__":
    debug_provider_map_contents()