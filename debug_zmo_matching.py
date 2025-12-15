#!/usr/bin/env python3
"""
Debug the ZMO name matching to see why no assignments are being created
"""

import sqlite3
import pandas as pd
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transform_production_data_v3_fixed import find_provider_by_zmo_name, find_coordinator_by_zmo_name

def debug_zmo_matching():
    print("Debugging ZMO name matching")
    print("=" * 60)
    
    # Get database connection
    conn = sqlite3.connect('production.db')
    
    # Check what providers are in the database
    print("Providers in database:")
    cursor = conn.execute("SELECT user_id, full_name, first_name FROM users WHERE status != 'deleted' ORDER BY full_name")
    for user_id, full_name, first_name in cursor.fetchall():
        print(f"  ID {user_id}: '{full_name}' (first: '{first_name}')")
    
    # Load ZMO data and test some assignments
    zmo_path = 'downloads/ZMO_MAIN.csv'
    if os.path.exists(zmo_path):
        df = pd.read_csv(zmo_path, nrows=20)  # Just first 20 rows for testing
        
        print(f"\nTesting ZMO data ({len(df)} rows):")
        
        prov_col = 'Assigned \nReg Prov'
        cm_col = 'Assigned\nCM'
        
        if prov_col in df.columns:
            print("\nProvider assignments in ZMO:")
            unique_providers = df[prov_col].dropna().unique()
            for provider in unique_providers[:10]:  # Just first 10
                provider_id = find_provider_by_zmo_name(conn, provider)
                print(f"  ZMO: '{provider}' -> ID: {provider_id}")
        
        if cm_col in df.columns:
            print("\nCoordinator assignments in ZMO:")
            unique_cms = df[cm_col].dropna().unique()
            for cm in unique_cms[:10]:  # Just first 10
                cm_id = find_coordinator_by_zmo_name(conn, cm)
                print(f"  ZMO: '{cm}' -> ID: {cm_id}")
        
        # Test specific problematic cases
        print("\nTesting specific cases:")
        test_cases = [
            ("Szalas NP, Andrew", "provider"),
            ("Antonio NP, Ethel", "provider"),
            ("Atencio, Dianela", "coordinator"),
            ("Sumpay, Laura", "coordinator")
        ]
        
        for name, type in test_cases:
            if type == "provider":
                result = find_provider_by_zmo_name(conn, name)
                print(f"  {name} (provider) -> ID: {result}")
            else:
                result = find_coordinator_by_zmo_name(conn, name)
                print(f"  {name} (coordinator) -> ID: {result}")
    
    conn.close()

if __name__ == "__main__":
    debug_zmo_matching()