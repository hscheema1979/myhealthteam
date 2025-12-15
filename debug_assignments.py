#!/usr/bin/env python3
"""
Debug why assignments aren't being created
"""

import sqlite3
import pandas as pd
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transform_production_data_v3_fixed import find_provider_by_zmo_name, find_coordinator_by_zmo_name

def debug_assignments():
    print("Debugging assignment creation")
    print("=" * 50)
    
    # Get database connection
    conn = sqlite3.connect('production.db')
    
    # Load a small sample of ZMO data
    zmo_path = 'downloads/ZMO_MAIN.csv'
    if os.path.exists(zmo_path):
        df = pd.read_csv(zmo_path, nrows=20)
        
        prov_col = 'Assigned \nReg Prov'
        cm_col = 'Assigned\nCM'
        
        print(f"Testing {len(df)} rows for assignments:")
        
        assignments_found = 0
        
        for i, row in df.iterrows():
            # Extract patient info (simplified)
            last_name = str(row.get('Last', '')).strip() if pd.notna(row.get('Last')) else ''
            first_name = str(row.get('First', '')).strip() if pd.notna(row.get('First')) else ''
            dob_str = str(row.get('DOB', '')).strip() if pd.notna(row.get('DOB')) else ''
            
            if not last_name or not first_name or not dob_str:
                continue
            
            patient_id = f"{last_name} {first_name} {dob_str}".upper()
            
            # Extract assignments
            assigned_prov = str(row.get('Assigned \nReg Prov', '')).strip().upper() if pd.notna(row.get('Assigned \nReg Prov')) else None
            assigned_cm = str(row.get('Assigned\nCM', '')).strip().upper() if pd.notna(row.get('Assigned\nCM')) else None
            
            print(f"\nRow {i}: {patient_id}")
            print(f"  Provider: {assigned_prov}")
            print(f"  Coordinator: {assigned_cm}")
            
            # Test provider matching
            if assigned_prov:
                provider_id = find_provider_by_zmo_name(conn, assigned_prov)
                print(f"  Provider ID: {provider_id}")
                
                if provider_id:
                    assignments_found += 1
                else:
                    print(f"  NO PROVIDER MATCH for: '{assigned_prov}'")
            
            # Test coordinator matching
            if assigned_cm:
                coordinator_id = find_coordinator_by_zmo_name(conn, assigned_cm)
                print(f"  Coordinator ID: {coordinator_id}")
                
                if coordinator_id:
                    assignments_found += 1
                else:
                    print(f"  NO COORDINATOR MATCH for: '{assigned_cm}'")
        
        print(f"\nTotal assignments that would be created: {assignments_found}")
        
        # Check what unique provider/coordinator names are in the ZMO data
        if prov_col in df.columns:
            unique_providers = df[prov_col].dropna().unique()
            print(f"\nUnique provider names in ZMO ({len(unique_providers)}):")
            for prov in sorted(unique_providers)[:10]:
                provider_id = find_provider_by_zmo_name(conn, prov)
                status = "✓" if provider_id else "✗"
                print(f"  {status} '{prov}' -> ID: {provider_id}")
        
        if cm_col in df.columns:
            unique_cms = df[cm_col].dropna().unique()
            print(f"\nUnique coordinator names in ZMO ({len(unique_cms)}):")
            for cm in sorted(unique_cms)[:10]:
                coordinator_id = find_coordinator_by_zmo_name(conn, cm)
                status = "✓" if coordinator_id else "✗"
                print(f"  {status} '{cm}' -> ID: {coordinator_id}")
    
    conn.close()

if __name__ == "__main__":
    debug_assignments()