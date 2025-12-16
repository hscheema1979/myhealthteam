#!/usr/bin/env python3
"""
Test if ZMO-only processing works by running the transform function
"""

import os
import sys
import sqlite3

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_zmo_only():
    print("Testing ZMO-only provider assignment processing")
    print("=" * 60)
    
    # Check if we can import the transform function
    try:
        from transform_production_data_v3_fixed import main
        print("SUCCESS: Import transform_production_data_v3_fixed")
    except Exception as e:
        print(f"ERROR: Could not import transform function: {e}")
        return False
    
    # Check database state before
    conn = sqlite3.connect('production.db')
    cursor = conn.execute("SELECT COUNT(*) FROM patient_assignments")
    before_count = cursor.fetchone()[0]
    print(f"Patient assignments before: {before_count}")
    
    # Check ZMO file
    zmo_path = 'downloads/ZMO_MAIN.csv'
    if os.path.exists(zmo_path):
        print(f"ZMO file exists: {zmo_path}")
        
        # Get a sample of the data to understand structure
        import pandas as pd
        try:
            df = pd.read_csv(zmo_path, nrows=3)
            print("ZMO columns found:")
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['prov', 'cm', 'assigned']):
                    print(f"  - {col} (assignment column)")
        except Exception as e:
            print(f"Could not read ZMO file: {e}")
    else:
        print(f"ZMO file NOT found: {zmo_path}")
        return False
    
    conn.close()
    print("\nSetup complete - ready to test ZMO processing")
    return True

if __name__ == "__main__":
    test_zmo_only()