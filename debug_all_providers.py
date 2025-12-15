#!/usr/bin/env python3
"""
Debug all provider names and create better matching logic
"""

import sqlite3
import pandas as pd
import sys
import os
from difflib import SequenceMatcher

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transform_production_data_v3_fixed import build_provider_map

def fuzzy_match(name1, name2, threshold=0.8):
    """Calculate fuzzy match ratio between two names"""
    return SequenceMatcher(None, name1, name2).ratio() >= threshold

def clean_name_for_matching(name):
    """Clean name for better matching"""
    if not name:
        return ""
    
    # Convert to uppercase and strip
    cleaned = str(name).upper().strip()
    
    # Remove common suffixes and prefixes
    cleaned = cleaned.replace(" NP,", ",").replace(" MD,", ",").replace(" PA,", ",").replace(" ZZ,", ",")
    cleaned = cleaned.replace("NP", "").replace("MD", "").replace("PA", "").replace("ZZ", "")
    
    # Remove extra spaces
    cleaned = " ".join(cleaned.split())
    
    return cleaned

def debug_all_providers():
    print("All Provider Names Analysis")
    print("=" * 60)
    
    # Get all provider data from database
    conn = sqlite3.connect('production.db')
    cursor = conn.execute("""
        SELECT user_id, username, first_name, last_name, full_name 
        FROM users 
        WHERE status != 'deleted' 
        ORDER BY full_name
    """)
    
    db_providers = {}
    print("Database providers:")
    for uid, username, first_name, last_name, full_name in cursor.fetchall():
        if full_name:
            db_providers[full_name.upper()] = {
                'id': uid,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': full_name
            }
            print(f"  ID {uid:2d}: '{full_name}' (username: {username})")
    
    # Get ZMO data
    zmo_path = 'downloads/ZMO_MAIN.csv'
    if os.path.exists(zmo_path):
        df = pd.read_csv(zmo_path)
        
        prov_col = 'Assigned \nReg Prov'
        if prov_col in df.columns:
            zmo_providers = df[prov_col].dropna().unique()
            print(f"\nZMO provider assignments ({len(zmo_providers)} unique):")
            
            # Track matches
            exact_matches = 0
            fuzzy_matches = 0
            no_matches = 0
            
            for zmo_name in sorted(zmo_providers):
                zmo_clean = clean_name_for_matching(zmo_name)
                zmo_upper = zmo_name.upper().strip()
                
                print(f"\nZMO: '{zmo_name}'")
                print(f"     Clean: '{zmo_clean}'")
                
                # Check exact match
                if zmo_upper in db_providers:
                    db_info = db_providers[zmo_upper]
                    print(f"     *** EXACT MATCH -> ID: {db_info['id']} (username: {db_info['username']})")
                    exact_matches += 1
                else:
                    # Try fuzzy matching
                    best_match = None
                    best_ratio = 0
                    
                    for db_name in db_providers.keys():
                        db_clean = clean_name_for_matching(db_name)
                        ratio = SequenceMatcher(None, zmo_clean, db_clean).ratio()
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_match = db_name
                    
                    if best_match and best_ratio > 0.7:
                        db_info = db_providers[best_match]
                        print(f"     *** FUZZY MATCH ({best_ratio:.2f}) -> ID: {db_info['id']} (username: {db_info['username']})")
                        print(f"         DB: '{best_match}'")
                        fuzzy_matches += 1
                    else:
                        print(f"     *** NO MATCH FOUND")
                        no_matches += 1
            
            print(f"\nMatching Summary:")
            print(f"  Exact matches: {exact_matches}")
            print(f"  Fuzzy matches: {fuzzy_matches}")
            print(f"  No matches: {no_matches}")
            print(f"  Total ZMO providers: {len(zmo_providers)}")
            
            # Show some specific problematic cases
            print(f"\nProblematic cases that need fixing:")
            for zmo_name in ["OTEBULU NP, ANGELA", "ANTONIO NP, ETHEL"]:
                if zmo_name in zmo_providers:
                    zmo_clean = clean_name_for_matching(zmo_name)
                    print(f"  ZMO: '{zmo_name}' -> Clean: '{zmo_clean}'")
                    
                    # Find closest match
                    best_match = None
                    best_ratio = 0
                    for db_name in db_providers.keys():
                        db_clean = clean_name_for_matching(db_name)
                        ratio = SequenceMatcher(None, zmo_clean, db_clean).ratio()
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_match = db_name
                    
                    if best_match:
                        db_info = db_providers[best_match]
                        print(f"    Best match ({best_ratio:.2f}): '{best_match}' -> ID: {db_info['id']}")
    
    conn.close()

if __name__ == "__main__":
    debug_all_providers()