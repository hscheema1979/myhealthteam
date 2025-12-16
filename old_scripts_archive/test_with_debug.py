#!/usr/bin/env python3
"""
Test the transform function with debug output to see what's happening
"""

import sqlite3
import pandas as pd
import sys
import os
from difflib import SequenceMatcher

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transform_production_data_v3_fixed import build_provider_map, normalize_patient_id

def test_with_debug():
    print("Testing transform with debug output")
    print("=" * 50)
    
    # Get provider map from database
    conn = sqlite3.connect('production.db')
    provider_map, id_to_name = build_provider_map(conn)
    
    print(f"Provider map has {len(provider_map)} entries")
    
    # Load a small sample of ZMO data
    zmo_path = 'downloads/ZMO_MAIN.csv'
    if os.path.exists(zmo_path):
        df = pd.read_csv(zmo_path, nrows=10)
        
        prov_col = 'Assigned \nReg Prov'
        if prov_col in df.columns:
            print(f"\nTesting {len(df)} rows of ZMO data:")
            
            for i, row in df.iterrows():
                # Extract patient info
                last_name = str(row.get('Last', '')).strip() if pd.notna(row.get('Last')) else None
                first_name = str(row.get('First', '')).strip() if pd.notna(row.get('First')) else None
                dob_str = str(row.get('DOB', '')).strip() if pd.notna(row.get('DOB')) else None
                
                if not last_name or not first_name or not dob_str:
                    print(f"Row {i}: Skipping - missing patient data")
                    continue
                
                # Create patient_id
                combined_id = f"{last_name} {first_name} {dob_str}"
                patient_id = normalize_patient_id(combined_id)
                
                # Extract provider assignment
                assigned_prov = str(row.get('Assigned \nReg Prov', '')).strip().upper() if pd.notna(row.get('Assigned \nReg Prov')) else None
                
                if not assigned_prov:
                    print(f"Row {i}: {patient_id} - No provider assignment")
                    continue
                
                print(f"\nRow {i}: {patient_id}")
                print(f"  Provider from ZMO: '{assigned_prov}'")
                
                # Try exact match
                exact_match = provider_map.get(assigned_prov)
                print(f"  Exact match: {exact_match}")
                
                # Try fuzzy matching manually
                target_clean = assigned_prov.replace(" NP,", ",").replace(" MD,", ",").replace(" PA,", ",").replace(" ZZ,", ",")
                target_clean = " ".join(target_clean.split())
                
                best_match = None
                best_ratio = 0
                
                for map_name in provider_map.keys():
                    map_clean = map_name.replace(" NP,", ",").replace(" MD,", ",").replace(" PA,", ",").replace(" ZZ,", ",")
                    map_clean = " ".join(map_clean.split())
                    
                    ratio = SequenceMatcher(None, target_clean, map_clean).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_match = map_name
                
                if best_match and best_ratio >= 0.85:
                    print(f"  Fuzzy match ({best_ratio:.2f}): '{best_match}' -> ID: {provider_map[best_match]}")
                else:
                    print(f"  No fuzzy match (best: {best_ratio:.2f} for '{best_match}')")
                
                # Show some close matches for debugging
                if best_match and best_ratio < 0.85:
                    print(f"  Closest matches:")
                    matches = []
                    for map_name in provider_map.keys():
                        map_clean = map_name.replace(" NP,", ",").replace(" MD,", ",").replace(" PA,", ",").replace(" ZZ,", ",")
                        map_clean = " ".join(map_clean.split())
                        ratio = SequenceMatcher(None, target_clean, map_clean).ratio()
                        if ratio > 0.5:  # Show matches above 50%
                            matches.append((map_name, ratio, provider_map[map_name]))
                    
                    matches.sort(key=lambda x: x[1], reverse=True)
                    for map_name, ratio, uid in matches[:3]:
                        print(f"    '{map_name}' ({ratio:.2f}) -> ID: {uid}")
    
    conn.close()

if __name__ == "__main__":
    test_with_debug()