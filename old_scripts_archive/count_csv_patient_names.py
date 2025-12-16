#!/usr/bin/env python3
"""
Count how many rows with actual patient names are in the original CSV files
"""

import pandas as pd
import os
import glob

def count_csv_patient_names():
    print("Counting rows with actual patient names in CSV files")
    print("=" * 70)
    
    csv_dir = 'downloads'
    if not os.path.exists(csv_dir):
        print(f"ERROR: {csv_dir} directory not found")
        return
    
    # PSL files (provider tasks)
    psl_files = glob.glob(os.path.join(csv_dir, "PSL_ZEN-*.csv"))
    print(f"\nPSL FILES (Provider Tasks): {len(psl_files)} files")
    
    psl_total_rows = 0
    psl_real_patients = 0
    psl_examples = []
    
    for psl_file in psl_files:
        try:
            df = pd.read_csv(psl_file, encoding="utf-8", on_bad_lines="skip")
            
            # Find the patient column - look for "Patient Last, First DOB"
            patient_col = None
            for col in df.columns:
                if "patient" in col.lower() and "last" in col.lower():
                    patient_col = col
                    break
            
            if patient_col:
                total_rows = len(df)
                
                # Count real patients (not placeholders)
                real_mask = (
                    ~df[patient_col].isna() & 
                    ~df[patient_col].astype(str).str.contains('Aaa, Aaa', na=False) &
                    ~df[patient_col].astype(str).str.contains('Place holder', na=False) &
                    ~df[patient_col].astype(str).str.contains('nan', na=False) &
                    (df[patient_col].astype(str).str.len() > 5)  # Basic check for real names
                )
                
                real_count = real_mask.sum()
                
                psl_total_rows += total_rows
                psl_real_patients += real_count
                
                if real_count > 0 and len(psl_examples) < 3:
                    examples = df[real_mask][patient_col].head(2).tolist()
                    psl_examples.extend(examples)
                    
                print(f"  {os.path.basename(psl_file)}: {total_rows} total, {real_count} real patients")
            else:
                print(f"  {os.path.basename(psl_file)}: No patient column found")
                
        except Exception as e:
            print(f"  ERROR reading {psl_file}: {e}")
    
    # RVZ files (coordinator tasks)
    rvz_files = glob.glob(os.path.join(csv_dir, "RVZ_ZEN-*.csv"))
    print(f"\nRVZ FILES (Coordinator Tasks): {len(rvz_files)} files")
    
    rvz_total_rows = 0
    rvz_real_patients = 0
    rvz_examples = []
    
    for rvz_file in rvz_files:
        try:
            df = pd.read_csv(rvz_file, encoding="utf-8", on_bad_lines="skip")
            
            # Find the patient column - look for "Pt Name" or similar
            patient_col = None
            for col in df.columns:
                if "pt" in col.lower() and "name" in col.lower():
                    patient_col = col
                    break
            
            if patient_col:
                total_rows = len(df)
                
                # Count real patients (not placeholders)
                real_mask = (
                    ~df[patient_col].isna() & 
                    ~df[patient_col].astype(str).str.contains('Aaa, Aaa', na=False) &
                    ~df[patient_col].astype(str).str.contains('Place holder', na=False) &
                    ~df[patient_col].astype(str).str.contains('nan', na=False) &
                    (df[patient_col].astype(str).str.len() > 5)  # Basic check for real names
                )
                
                real_count = real_mask.sum()
                
                rvz_total_rows += total_rows
                rvz_real_patients += real_count
                
                if real_count > 0 and len(rvz_examples) < 3:
                    examples = df[real_mask][patient_col].head(2).tolist()
                    rvz_examples.extend(examples)
                    
                print(f"  {os.path.basename(rvz_file)}: {total_rows} total, {real_count} real patients")
            else:
                print(f"  {os.path.basename(rvz_file)}: No patient column found")
                
        except Exception as e:
            print(f"  ERROR reading {rvz_file}: {e}")
    
    # CMLog files (coordinator tasks)
    cmlog_files = glob.glob(os.path.join(csv_dir, "CMLog_*.csv"))
    print(f"\nCMLog FILES (Coordinator Tasks): {len(cmlog_files)} files")
    
    cmlog_total_rows = 0
    cmlog_real_patients = 0
    cmlog_examples = []
    
    for cmlog_file in cmlog_files:
        try:
            df = pd.read_csv(cmlog_file, encoding="utf-8", on_bad_lines="skip")
            
            # Find the patient column - look for "Pt Name" or similar
            patient_col = None
            for col in df.columns:
                if "pt" in col.lower() and "name" in col.lower():
                    patient_col = col
                    break
            
            if patient_col:
                total_rows = len(df)
                
                # Count real patients (not placeholders)
                real_mask = (
                    ~df[patient_col].isna() & 
                    ~df[patient_col].astype(str).str.contains('Aaa, Aaa', na=False) &
                    ~df[patient_col].astype(str).str.contains('Place holder', na=False) &
                    ~df[patient_col].astype(str).str.contains('nan', na=False) &
                    (df[patient_col].astype(str).str.len() > 5)  # Basic check for real names
                )
                
                real_count = real_mask.sum()
                
                cmlog_total_rows += total_rows
                cmlog_real_patients += real_count
                
                if real_count > 0 and len(cmlog_examples) < 3:
                    examples = df[real_mask][patient_col].head(2).tolist()
                    cmlog_examples.extend(examples)
                    
                print(f"  {os.path.basename(cmlog_file)}: {total_rows} total, {real_count} real patients")
            else:
                print(f"  {os.path.basename(cmlog_file)}: No patient column found")
                
        except Exception as e:
            print(f"  ERROR reading {cmlog_file}: {e}")
    
    print(f"\n{'='*70}")
    print("SUMMARY:")
    print(f"PSL files: {psl_total_rows} total rows, {psl_real_patients} with real patient names")
    print(f"RVZ files: {rvz_total_rows} total rows, {rvz_real_patients} with real patient names")
    print(f"CMLog files: {cmlog_total_rows} total rows, {cmlog_real_patients} with real patient names")
    print(f"\nTotal across all files: {psl_total_rows + rvz_total_rows + cmlog_total_rows} rows")
    print(f"Total with real patient names: {psl_real_patients + rvz_real_patients + cmlog_real_patients}")
    
    if psl_examples:
        print(f"\nPSL patient name examples: {psl_examples[:3]}")
    if rvz_examples:
        print(f"RVZ patient name examples: {rvz_examples[:3]}")
    if cmlog_examples:
        print(f"CMLog patient name examples: {cmlog_examples[:3]}")

if __name__ == "__main__":
    count_csv_patient_names()