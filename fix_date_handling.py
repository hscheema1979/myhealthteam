#!/usr/bin/env python3
"""
Fix the date handling issues in process_zmo
"""

import sqlite3
import pandas as pd

def test_date_handling():
    """Test date handling to see what's causing the NaT errors"""
    
    # Load some ZMO data to see the date formats
    zmo_path = 'downloads/ZMO_MAIN.csv'
    df = pd.read_csv(zmo_path, nrows=10)
    
    print("ZMO date column samples:")
    print(f"DOB column: {df.columns}")
    
    if 'DOB' in df.columns:
        print("DOB values:")
        for i, val in enumerate(df['DOB'].head(10)):
            print(f"  Row {i}: {repr(val)} (type: {type(val)})")
            
            # Test our parse_date function
            from transform_production_data_v3_fixed import parse_date
            parsed = parse_date(val)
            print(f"    Parsed: {parsed} (type: {type(parsed)})")
            
            if parsed is not None and not pd.isna(parsed):
                try:
                    formatted = parsed.strftime("%Y-%m-%d")
                    print(f"    Formatted: {formatted}")
                except Exception as e:
                    print(f"    Format error: {e}")
            print()

if __name__ == "__main__":
    test_date_handling()