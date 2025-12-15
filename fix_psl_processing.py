#!/usr/bin/env python3
"""
Fix PSL processing to match actual file structure
"""

import pandas as pd
import os

def fix_psl_processing():
    print("Fixing PSL processing to match actual file structure")
    print("=" * 60)
    
    # Check what PSL files actually contain
    csv_dir = 'downloads'
    psl_files = [f for f in os.listdir(csv_dir) if f.startswith('PSL_') and f.endswith('.csv')]
    
    print(f"Found {len(psl_files)} PSL files:")
    
    # Look at a working PSL file to understand the structure
    working_file = None
    for psl_file in psl_files:
        file_path = os.path.join(csv_dir, psl_file)
        try:
            df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip", nrows=2)
            
            # Check if this file has valid data (not all #REF!)
            has_valid_data = False
            for col in df.columns:
                if col != '#REF!' and not str(col).startswith('Unnamed:'):
                    has_valid_data = True
                    break
            
            if has_valid_data:
                working_file = psl_file
                break
        except:
            continue
    
    if working_file:
        print(f"\nAnalyzing working file: {working_file}")
        
        df = pd.read_csv(os.path.join(csv_dir, working_file), encoding="utf-8", on_bad_lines="skip", nrows=5)
        
        print(f"  Columns: {list(df.columns)}")
        print(f"  Shape: {df.shape}")
        
        # Map the actual columns to what our code needs
        column_mapping = {
            'dos': None,
            'patient': None,
            'code': None,  # This will be the 'Prov' column
            'mins': None,
            'type': None,
            'notes': None
        }
        
        for col in df.columns:
            col_lower = col.lower()
            if "dos" in col_lower:
                column_mapping['dos'] = col
            elif "patient" in col_lower and "last" in col_lower:
                column_mapping['patient'] = col
            elif "prov" in col_lower:
                column_mapping['code'] = col  # Provider code is in 'Prov' column
            elif "min" in col_lower:
                column_mapping['mins'] = col
            elif "service" in col_lower:
                column_mapping['type'] = col
            elif "notes" in col_lower:
                column_mapping['notes'] = col
        
        print(f"  Column mapping:")
        for key, col in column_mapping.items():
            print(f"    {key}: {col}")
        
        # Look at actual data
        if not df.empty:
            print(f"\n  Sample data (first row):")
            first_row = df.iloc[0]
            for col in df.columns[:10]:  # Show first 10 columns
                print(f"    {col}: {repr(first_row[col])}")
    
    print("\n" + "=" * 60)
    print("CONCLUSION: PSL files use 'Prov' column for provider codes, not 'code'")
    print("Need to update process_psl() to use correct column names")

if __name__ == "__main__":
    fix_psl_processing()