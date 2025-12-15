#!/usr/bin/env python3
"""
Check what provider assignments are actually in the ZMO data
"""

import pandas as pd
import os

def check_zmo_assignments():
    print("Checking ZMO data for provider assignments")
    print("=" * 50)
    
    zmo_path = 'downloads/ZMO_MAIN.csv'
    if not os.path.exists(zmo_path):
        print(f"ZMO file not found: {zmo_path}")
        return
    
    try:
        df = pd.read_csv(zmo_path)
        print(f"ZMO file loaded: {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        
        # Look for assignment columns
        assignment_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['prov', 'cm', 'assigned']):
                assignment_cols.append(col)
        
        print(f"\nAssignment columns found: {assignment_cols}")
        
        # Check data in assignment columns
        for col in assignment_cols:
            print(f"\nColumn: {col}")
            non_null_count = df[col].notna().sum()
            print(f"  Non-null values: {non_null_count}")
            
            if non_null_count > 0:
                # Show unique values
                unique_vals = df[col].dropna().unique()
                print(f"  Unique values: {len(unique_vals)}")
                print(f"  Sample values: {unique_vals[:10]}")
        
        # Check specifically for provider assignments
        prov_col = None
        for col in df.columns:
            if 'assigned' in col.lower() and 'prov' in col.lower():
                prov_col = col
                break
        
        if prov_col:
            prov_assignments = df[prov_col].dropna()
            print(f"\nProvider assignments found: {len(prov_assignments)}")
            if len(prov_assignments) > 0:
                print("Top provider assignments:")
                print(prov_assignments.value_counts().head(10))
        
        # Check for coordinator assignments  
        cm_col = None
        for col in df.columns:
            if 'assigned' in col.lower() and 'cm' in col.lower():
                cm_col = col
                break
        
        if cm_col:
            cm_assignments = df[cm_col].dropna()
            print(f"\nCoordinator assignments found: {len(cm_assignments)}")
            if len(cm_assignments) > 0:
                print("Top coordinator assignments:")
                print(cm_assignments.value_counts().head(10))
        
    except Exception as e:
        print(f"Error reading ZMO file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_zmo_assignments()