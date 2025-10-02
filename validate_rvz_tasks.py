#!/usr/bin/env python3
"""
Validate RVZ Tasks - Check if tasks from rvz.csv are present in database tables
"""

import pandas as pd
import sqlite3
from datetime import datetime
import os

def normalize_patient_id(patient_name):
    """Apply the same normalization used in SQL scripts"""
    if not patient_name or pd.isna(patient_name):
        return None
    
    # Remove ZEN- prefix and normalize spaces/commas
    normalized = str(patient_name).strip()
    normalized = normalized.replace('ZEN-', '')
    normalized = normalized.replace(', ', ' ')
    normalized = normalized.replace(',', ' ')
    # Replace multiple spaces with single space
    while '  ' in normalized:
        normalized = normalized.replace('  ', ' ')
    
    return normalized.strip()

def parse_date(date_str):
    """Parse date string to standardized format"""
    if not date_str or pd.isna(date_str):
        return None
    
    try:
        # Handle MM/DD/YY format
        if '/' in str(date_str):
            parts = str(date_str).split('/')
            if len(parts) == 3:
                month, day, year = parts
                # Convert 2-digit year to 4-digit
                if len(year.strip()) == 2:
                    year = '20' + year.strip()
                return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"
        
        return str(date_str)
    except:
        return None

def main():
    print("=== RVZ Task Validation ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Check if files exist
    csv_file = "downloads/rvz.csv"
    db_file = "production.db"
    
    if not os.path.exists(csv_file):
        print(f"ERROR: {csv_file} not found")
        return
    
    if not os.path.exists(db_file):
        print(f"ERROR: {db_file} not found")
        return
    
    # Load RVZ CSV data
    print("Loading RVZ CSV data...")
    try:
        df_rvz = pd.read_csv(csv_file)
        print(f"Loaded {len(df_rvz)} rows from RVZ CSV")
        print(f"Columns: {list(df_rvz.columns)}")
        print()
    except Exception as e:
        print(f"ERROR loading CSV: {e}")
        return
    
    # Filter out placeholder rows and empty data
    df_rvz_clean = df_rvz[
        (~df_rvz['Pt Name'].str.contains('Aaa, Aaa', na=False)) &
        (~df_rvz['Type'].str.contains('Place holder', na=False)) &
        (df_rvz['Pt Name'].notna()) &
        (df_rvz['Pt Name'] != '') &
        (~df_rvz['Pt Name'].str.contains('start', na=False))
    ].copy()
    
    print(f"After filtering placeholders: {len(df_rvz_clean)} rows")
    
    # Normalize patient IDs
    df_rvz_clean['normalized_patient_id'] = df_rvz_clean['Pt Name'].apply(normalize_patient_id)
    df_rvz_clean['normalized_date'] = df_rvz_clean['Date Only'].apply(parse_date)
    
    # Connect to database
    print("Connecting to database...")
    conn = sqlite3.connect(db_file)
    
    try:
        # Get coordinator tasks
        print("Loading coordinator tasks from database...")
        coordinator_query = """
        SELECT patient_id, task_date, task_type, notes, coordinator_id
        FROM coordinator_tasks 
        WHERE patient_id IS NOT NULL AND patient_id != ''
        """
        df_coordinator = pd.read_sql_query(coordinator_query, conn)
        print(f"Loaded {len(df_coordinator)} coordinator tasks")
        
        # Get provider tasks  
        print("Loading provider tasks from database...")
        provider_query = """
        SELECT patient_id, task_date, task_description, notes, provider_name, source_system
        FROM provider_tasks 
        WHERE patient_id IS NOT NULL AND patient_id != ''
        """
        df_provider = pd.read_sql_query(provider_query, conn)
        print(f"Loaded {len(df_provider)} provider tasks")
        print()
        
        # Analysis
        print("=== VALIDATION RESULTS ===")
        
        # Check unique patients in RVZ
        unique_rvz_patients = df_rvz_clean['normalized_patient_id'].nunique()
        print(f"Unique patients in RVZ data: {unique_rvz_patients}")
        
        # Check matches in coordinator tasks
        coordinator_matches = df_rvz_clean[
            df_rvz_clean['normalized_patient_id'].isin(df_coordinator['patient_id'])
        ]
        print(f"RVZ patients found in coordinator_tasks: {len(coordinator_matches)} / {len(df_rvz_clean)} ({len(coordinator_matches)/len(df_rvz_clean)*100:.1f}%)")
        
        # Check matches in provider tasks
        provider_matches = df_rvz_clean[
            df_rvz_clean['normalized_patient_id'].isin(df_provider['patient_id'])
        ]
        print(f"RVZ patients found in provider_tasks: {len(provider_matches)} / {len(df_rvz_clean)} ({len(provider_matches)/len(df_rvz_clean)*100:.1f}%)")
        
        # Check for exact date + patient matches in coordinator tasks
        print("\n=== DETAILED MATCHING ===")
        
        exact_coordinator_matches = 0
        for _, row in df_rvz_clean.iterrows():
            patient_id = row['normalized_patient_id']
            task_date = row['normalized_date']
            
            if patient_id and task_date:
                matches = df_coordinator[
                    (df_coordinator['patient_id'] == patient_id) &
                    (df_coordinator['task_date'] == task_date)
                ]
                if len(matches) > 0:
                    exact_coordinator_matches += 1
        
        print(f"Exact date+patient matches in coordinator_tasks: {exact_coordinator_matches} / {len(df_rvz_clean)} ({exact_coordinator_matches/len(df_rvz_clean)*100:.1f}%)")
        
        # Sample of unmatched RVZ records
        unmatched_rvz = df_rvz_clean[
            ~df_rvz_clean['normalized_patient_id'].isin(df_coordinator['patient_id']) &
            ~df_rvz_clean['normalized_patient_id'].isin(df_provider['patient_id'])
        ]
        
        print(f"\nUnmatched RVZ records: {len(unmatched_rvz)}")
        if len(unmatched_rvz) > 0:
            print("Sample unmatched patients:")
            for i, (_, row) in enumerate(unmatched_rvz.head(10).iterrows()):
                print(f"  {i+1}. {row['Pt Name']} -> {row['normalized_patient_id']} ({row['Date Only']})")
        
        # Check task types
        print(f"\nRVZ Task Types:")
        task_type_counts = df_rvz_clean['Type'].value_counts()
        for task_type, count in task_type_counts.head(10).items():
            print(f"  {task_type}: {count}")
        
        # Check date range
        valid_dates = df_rvz_clean[df_rvz_clean['normalized_date'].notna()]
        if len(valid_dates) > 0:
            print(f"\nRVZ Date Range:")
            print(f"  Earliest: {valid_dates['normalized_date'].min()}")
            print(f"  Latest: {valid_dates['normalized_date'].max()}")
        
        # Summary
        print(f"\n=== SUMMARY ===")
        print(f"Total RVZ records (after filtering): {len(df_rvz_clean)}")
        print(f"Patient coverage in coordinator_tasks: {len(coordinator_matches)/len(df_rvz_clean)*100:.1f}%")
        print(f"Patient coverage in provider_tasks: {len(provider_matches)/len(df_rvz_clean)*100:.1f}%")
        print(f"Exact date+patient matches: {exact_coordinator_matches/len(df_rvz_clean)*100:.1f}%")
        
        if len(unmatched_rvz) > 0:
            print(f"\nRecommendation: {len(unmatched_rvz)} RVZ records appear to be missing from the database.")
            print("This could indicate:")
            print("1. RVZ data hasn't been imported yet")
            print("2. Patient ID normalization differences")
            print("3. Data from different time periods")
        else:
            print("\nAll RVZ records appear to be present in the database!")
            
    except Exception as e:
        print(f"ERROR during validation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
        print(f"\nValidation completed at {datetime.now()}")

if __name__ == "__main__":
    main()