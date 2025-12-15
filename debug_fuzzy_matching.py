#!/usr/bin/env python3
"""
Debug the fuzzy matching logic in process_zmo
"""

import sqlite3
import pandas as pd
import sys
import os
from difflib import SequenceMatcher

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transform_production_data_v3_fixed import build_provider_map, clean_name_for_matching

def debug_fuzzy_matching():
    print("Debugging fuzzy matching logic")
    print("=" * 50)
    
    # Get provider map from database
    conn = sqlite3.connect('production.db')
    provider_map, id_to_name = build_provider_map(conn)
    
    print(f"Provider map has {len(provider_map)} entries")
    
    # Test the fuzzy matching function manually
    test_zmo_names = [
        "Szalas NP, Andrew",
        "Antonio NP, Ethel", 
        "Otebulu NP, Angela",
        "Atencio, Dianela"
    ]
    
    def fuzzy_match_provider_name(target_name, provider_map, threshold=0.85):
        """Fuzzy match a provider name against the provider map"""
        if not target_name:
            return None
        
        # Clean the target name
        target_clean = clean_name_for_matching(target_name)
        
        best_match = None
        best_ratio = 0
        
        for map_name in provider_map.keys():
            # Clean the map name too
            map_clean = clean_name_for_matching(map_name)
            
            # Calculate similarity
            ratio = SequenceMatcher(None, target_clean, map_clean).ratio()
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = map_name
        
        # Return the best match if it meets threshold
        if best_match and best_ratio >= threshold:
            return provider_map[best_match]
        
        return None
    
    for zmo_name in test_zmo_names:
        print(f"\nTesting: '{zmo_name}'")
        
        # Try exact match
        exact_match = provider_map.get(zmo_name.upper().strip())
        print(f"  Exact match: {exact_match}")
        
        # Try fuzzy match
        fuzzy_match = fuzzy_match_provider_name(zmo_name, provider_map, threshold=0.85)
        print(f"  Fuzzy match: {fuzzy_match}")
        
        # Show the cleaning process
        target_clean = clean_name_for_matching(zmo_name)
        print(f"  Cleaned: '{target_clean}'")
        
        # Show some comparisons
        target_clean = clean_name_for_matching(zmo_name)
        best_ratio = 0
        best_match = None
        
        for map_name in list(provider_map.keys())[:10]:  # Just first 10 for demo
            map_clean = clean_name_for_matching(map_name)
            ratio = SequenceMatcher(None, target_clean, map_clean).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = map_name
        
        if best_match:
            print(f"  Best match: '{best_match}' (ratio: {best_ratio:.2f})")
    
    # Test with actual ZMO data
    zmo_path = 'downloads/ZMO_MAIN.csv'
    if os.path.exists(zmo_path):
        df = pd.read_csv(zmo_path, nrows=5)
        
        prov_col = 'Assigned \nReg Prov'
        if prov_col in df.columns:
            print(f"\nTesting with actual ZMO data:")
            for _, row in df.iterrows():
                zmo_prov = row[prov_col]
                if pd.notna(zmo_prov):
                    exact_match = provider_map.get(zmo_prov.upper().strip())
                    fuzzy_match = fuzzy_match_provider_name(zmo_prov, provider_map, threshold=0.85)
                    print(f"  '{zmo_prov}' -> Exact: {exact_match}, Fuzzy: {fuzzy_match}")
    
    conn.close()

if __name__ == "__main__":
    debug_fuzzy_matching()