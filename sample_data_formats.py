#!/usr/bin/env python3
"""
Sample data formats from CSV files
"""

import pandas as pd
import glob
import os

def show_sample_formats():
    print("SAMPLE DATA FORMATS FROM CSV FILES")
    print("=" * 50)
    
    csv_dir = 'downloads'
    
    # PSL files (provider tasks)
    psl_files = glob.glob(os.path.join(csv_dir, "PSL_ZEN-*.csv"))
    if psl_files:
        print("\n1. PSL (Provider Tasks):")
        try:
            df = pd.read_csv(psl_files[0], encoding="utf-8", on_bad_lines="skip", nrows=5)
            print(f"Columns: {list(df.columns)}")
            if 'patient' in df.columns:
                print("Sample patient names:")
                for i, name in enumerate(df['patient'].dropna().head(5)):
                    print(f"  {i+1}. {name}")
        except Exception as e:
            print(f"Error reading PSL file: {e}")
    
    # RVZ files (coordinator tasks)
    rvz_files = glob.glob(os.path.join(csv_dir, "RVZ_ZEN-*.csv"))
    if rvz_files:
        print("\n2. RVZ (Coordinator Tasks):")
        try:
            df = pd.read_csv(rvz_files[0], encoding="utf-8", on_bad_lines="skip", nrows=5)
            print(f"Columns: {list(df.columns)}")
            if 'patient' in df.columns:
                print("Sample patient names:")
                for i, name in enumerate(df['patient'].dropna().head(5)):
                    print(f"  {i+1}. {name}")
        except Exception as e:
            print(f"Error reading RVZ file: {e}")
    
    # CMLog files (coordinator tasks)
    cmlog_files = glob.glob(os.path.join(csv_dir, "CMLog_*.csv"))
    if cmlog_files:
        print("\n3. CMLog (Coordinator Tasks):")
        try:
            df = pd.read_csv(cmlog_files[0], encoding="utf-8", on_bad_lines="skip", nrows=5)
            print(f"Columns: {list(df.columns)}")
            if 'patient' in df.columns:
                print("Sample patient names:")
                for i, name in enumerate(df['patient'].dropna().head(5)):
                    print(f"  {i+1}. {name}")
        except Exception as e:
            print(f"Error reading CMLog file: {e}")
    
    # ZMO file
    zmo_files = glob.glob(os.path.join(csv_dir, "ZMO*.csv"))
    if zmo_files:
        print("\n4. ZMO (Provider Assignments):")
        try:
            df = pd.read_csv(zmo_files[0], encoding="utf-8", on_bad_lines="skip", nrows=5)
            print(f"Columns: {list(df.columns)}")
            if 'patient' in df.columns:
                print("Sample patient names:")
                for i, name in enumerate(df['patient'].dropna().head(5)):
                    print(f"  {i+1}. {name}")
        except Exception as e:
            print(f"Error reading ZMO file: {e}")

if __name__ == "__main__":
    show_sample_formats()