#!/usr/bin/env python3
"""
Debug PSL file processing to see why it's returning 0 tasks
"""

import pandas as pd
import os

def debug_psl_processing():
    print("Debugging PSL file processing")
    print("=" * 50)
    
    # Check what PSL files actually contain
    csv_dir = 'downloads'
    psl_files = [f for f in os.listdir(csv_dir) if f.startswith('PSL_') and f.endswith('.csv')]
    
    print(f"Found {len(psl_files)} PSL files:")
    
    for psl_file in psl_files[:3]:  # Check first 3 files
        file_path = os.path.join(csv_dir, psl_file)
        print(f"\nAnalyzing: {psl_file}")
        
        try:
            df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip", nrows=5)
            print(f"  Columns: {list(df.columns)}")
            print(f"  Shape: {df.shape}")
            
            # Look for the columns our code expects
            expected_cols = {
                'dos': None,
                'patient': None, 
                'code': None,
                'mins': None,
                'type': None,
                'notes': None
            }
            
            for col in df.columns:
                col_lower = col.lower()
                if "dos" in col_lower or "date" in col_lower:
                    expected_cols['dos'] = col
                elif "patient" in col_lower and col_lower != "patient_id":
                    expected_cols['patient'] = col
                elif "code" in col_lower and "billing" not in col_lower:
                    expected_cols['code'] = col
                elif "min" in col_lower and "total" not in col_lower:
                    expected_cols['mins'] = col
                elif "type" in col_lower:
                    expected_cols['type'] = col
                elif "notes" in col_lower:
                    expected_cols['notes'] = col
            
            print(f"  Found columns:")
            for key, col in expected_cols.items():
                print(f"    {key}: {col}")
            
            # Check if we have the required DOS column
            if expected_cols['dos'] is None:
                print(f"  ERROR: NO DOS COLUMN FOUND!")
                print(f"  Available columns: {list(df.columns)}")
            else:
                print(f"  SUCCESS: DOS column found: {expected_cols['dos']}")
                
            # Look at actual data
            if not df.empty:
                print(f"  Sample data (first row):")
                first_row = df.iloc[0]
                for col in df.columns:
                    print(f"    {col}: {repr(first_row[col])}")
            
        except Exception as e:
            print(f"  ERROR: Error reading file: {e}")
    
    print("\n" + "=" * 50)
    print("CONCLUSION: Need to check if PSL files have the expected column structure")

if __name__ == "__main__":
    debug_psl_processing()