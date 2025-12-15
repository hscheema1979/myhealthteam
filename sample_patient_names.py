#!/usr/bin/env python3
"""
Sample patient names from CSV files
"""

import pandas as pd
import glob
import os

def show_patient_samples():
    print("SAMPLE PATIENT NAMES FROM CSV FILES")
    print("=" * 50)
    
    csv_dir = 'downloads'
    
    # PSL files (provider tasks) - using "Patient Last, First DOB" column
    psl_files = glob.glob(os.path.join(csv_dir, "PSL_ZEN-*.csv"))
    if psl_files:
        print("\n1. PSL (Provider Tasks):")
        try:
            df = pd.read_csv(psl_files[0], encoding="utf-8", on_bad_lines="skip", nrows=10)
            if 'Patient Last, First DOB' in df.columns:
                print("Sample patient names from 'Patient Last, First DOB' column:")
                for i, name in enumerate(df['Patient Last, First DOB'].dropna().head(5)):
                    print(f"  {i+1}. {name}")
            else:
                print(f"Available columns: {list(df.columns)}")
        except Exception as e:
            print(f"Error reading PSL file: {e}")
    
    # RVZ files (coordinator tasks) - using "Last, First DOB" column
    rvz_files = glob.glob(os.path.join(csv_dir, "RVZ_ZEN-*.csv"))
    if rvz_files:
        print("\n2. RVZ (Coordinator Tasks):")
        try:
            df = pd.read_csv(rvz_files[0], encoding="utf-8", on_bad_lines="skip", nrows=10)
            if 'Last, First DOB' in df.columns:
                print("Sample patient names from 'Last, First DOB' column:")
                for i, name in enumerate(df['Last, First DOB'].dropna().head(5)):
                    print(f"  {i+1}. {name}")
            else:
                print(f"Available columns: {list(df.columns)}")
        except Exception as e:
            print(f"Error reading RVZ file: {e}")
    
    # CMLog files (coordinator tasks) - using "Last, First DOB" column
    cmlog_files = glob.glob(os.path.join(csv_dir, "CMLog_*.csv"))
    if cmlog_files:
        print("\n3. CMLog (Coordinator Tasks):")
        try:
            df = pd.read_csv(cmlog_files[0], encoding="utf-8", on_bad_lines="skip", nrows=10)
            if 'Last, First DOB' in df.columns:
                print("Sample patient names from 'Last, First DOB' column:")
                for i, name in enumerate(df['Last, First DOB'].dropna().head(5)):
                    print(f"  {i+1}. {name}")
            else:
                print(f"Available columns: {list(df.columns)}")
        except Exception as e:
            print(f"Error reading CMLog file: {e}")
    
    # ZMO file - using "Pt Name" column
    zmo_files = glob.glob(os.path.join(csv_dir, "ZMO*.csv"))
    if zmo_files:
        print("\n4. ZMO (Provider Assignments):")
        try:
            df = pd.read_csv(zmo_files[0], encoding="utf-8", on_bad_lines="skip", nrows=10)
            if 'Pt Name' in df.columns:
                print("Sample patient names from 'Pt Name' column:")
                for i, name in enumerate(df['Pt Name'].dropna().head(5)):
                    print(f"  {i+1}. {name}")
            else:
                print(f"Available columns: {list(df.columns)}")
        except Exception as e:
            print(f"Error reading ZMO file: {e}")

if __name__ == "__main__":
    show_patient_samples()