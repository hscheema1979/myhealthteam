#!/usr/bin/env python3
"""
Detailed RVZ Task Validation - Check patient_name + date + task description matches
Focus on Review tasks specifically
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
    print("=== Detailed RVZ Task Validation ===")
    print(f"Timestamp: {datetime.now()}")
    print("Focus: patient_name + date + task description matches")
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
    except Exception as e:
        print(f"ERROR loading CSV: {e}")
        return
    
    # Filter out placeholder rows and focus on Review tasks
    df_rvz_clean = df_rvz[
        (~df_rvz['Pt Name'].str.contains('Aaa, Aaa', na=False)) &
        (~df_rvz['Type'].str.contains('Place holder', na=False)) &
        (df_rvz['Pt Name'].notna()) &
        (df_rvz['Pt Name'] != '') &
        (~df_rvz['Pt Name'].str.contains('start', na=False))
    ].copy()
    
    # Focus on Review tasks
    df_review_tasks = df_rvz_clean[
        df_rvz_clean['Type'].str.contains('Review', na=False, case=False)
    ].copy()
    
    print(f"Total RVZ records (after filtering): {len(df_rvz_clean)}")
    print(f"Review tasks in RVZ: {len(df_review_tasks)}")
    print()
    
    # Normalize patient IDs and dates
    df_review_tasks['normalized_patient_id'] = df_review_tasks['Pt Name'].apply(normalize_patient_id)
    df_review_tasks['normalized_date'] = df_review_tasks['Date Only'].apply(parse_date)
    
    # Connect to database
    print("Connecting to database...")
    conn = sqlite3.connect(db_file)
    
    try:
        # Get coordinator tasks with Review in task_type
        print("Loading coordinator Review tasks from database...")
        coordinator_query = """
        SELECT patient_id, task_date, task_type, notes, coordinator_id
        FROM coordinator_tasks 
        WHERE patient_id IS NOT NULL AND patient_id != ''
        AND (task_type LIKE '%Review%' OR task_type LIKE '%review%')
        """
        df_coordinator_review = pd.read_sql_query(coordinator_query, conn)
        print(f"Loaded {len(df_coordinator_review)} coordinator Review tasks")
        
        # Get provider tasks with Review in task_description
        print("Loading provider Review tasks from database...")
        provider_query = """
        SELECT patient_id, task_date, task_description, notes, provider_name
        FROM provider_tasks 
        WHERE patient_id IS NOT NULL AND patient_id != ''
        AND (task_description LIKE '%Review%' OR task_description LIKE '%review%')
        """
        df_provider_review = pd.read_sql_query(provider_query, conn)
        print(f"Loaded {len(df_provider_review)} provider Review tasks")
        print()
        
        # Analysis
        print("=== DETAILED VALIDATION RESULTS ===")
        
        # Check Review task types in RVZ
        print("RVZ Review Task Types:")
        review_types = df_review_tasks['Type'].value_counts()
        for task_type, count in review_types.items():
            print(f"  {task_type}: {count}")
        print()
        
        # Exact matches: patient + date + review task
        print("=== EXACT MATCHING ANALYSIS ===")
        
        exact_coordinator_matches = []
        exact_provider_matches = []
        
        for idx, row in df_review_tasks.iterrows():
            patient_id = row['normalized_patient_id']
            task_date = row['normalized_date']
            task_type = row['Type']
            
            if patient_id and task_date:
                # Check coordinator matches
                coord_matches = df_coordinator_review[
                    (df_coordinator_review['patient_id'] == patient_id) &
                    (df_coordinator_review['task_date'] == task_date)
                ]
                
                if len(coord_matches) > 0:
                    exact_coordinator_matches.append({
                        'rvz_patient': row['Pt Name'],
                        'normalized_patient': patient_id,
                        'rvz_date': row['Date Only'],
                        'normalized_date': task_date,
                        'rvz_task_type': task_type,
                        'db_matches': len(coord_matches),
                        'db_task_types': coord_matches['task_type'].tolist()
                    })
                
                # Check provider matches
                prov_matches = df_provider_review[
                    (df_provider_review['patient_id'] == patient_id) &
                    (df_provider_review['task_date'] == task_date)
                ]
                
                if len(prov_matches) > 0:
                    exact_provider_matches.append({
                        'rvz_patient': row['Pt Name'],
                        'normalized_patient': patient_id,
                        'rvz_date': row['Date Only'],
                        'normalized_date': task_date,
                        'rvz_task_type': task_type,
                        'db_matches': len(prov_matches),
                        'db_task_descriptions': prov_matches['task_description'].tolist()
                    })
        
        print(f"Exact coordinator matches (patient + date + Review): {len(exact_coordinator_matches)}")
        print(f"Exact provider matches (patient + date + Review): {len(exact_provider_matches)}")
        print()
        
        # Show sample exact matches
        if exact_coordinator_matches:
            print("Sample Coordinator Exact Matches:")
            for i, match in enumerate(exact_coordinator_matches[:5]):
                print(f"  {i+1}. {match['rvz_patient']} on {match['rvz_date']}")
                print(f"     RVZ Task: {match['rvz_task_type']}")
                print(f"     DB Tasks: {match['db_task_types']}")
                print()
        
        if exact_provider_matches:
            print("Sample Provider Exact Matches:")
            for i, match in enumerate(exact_provider_matches[:5]):
                print(f"  {i+1}. {match['rvz_patient']} on {match['rvz_date']}")
                print(f"     RVZ Task: {match['rvz_task_type']}")
                print(f"     DB Tasks: {match['db_task_descriptions']}")
                print()
        
        # Patient-only matches (ignoring date)
        print("=== PATIENT-ONLY MATCHING (Review tasks) ===")
        
        coord_patient_matches = df_review_tasks[
            df_review_tasks['normalized_patient_id'].isin(df_coordinator_review['patient_id'])
        ]
        
        prov_patient_matches = df_review_tasks[
            df_review_tasks['normalized_patient_id'].isin(df_provider_review['patient_id'])
        ]
        
        print(f"RVZ Review patients found in coordinator Review tasks: {len(coord_patient_matches)} / {len(df_review_tasks)} ({len(coord_patient_matches)/len(df_review_tasks)*100:.1f}%)")
        print(f"RVZ Review patients found in provider Review tasks: {len(prov_patient_matches)} / {len(df_review_tasks)} ({len(prov_patient_matches)/len(df_review_tasks)*100:.1f}%)")
        
        # Unmatched Review tasks
        unmatched_review = df_review_tasks[
            ~df_review_tasks['normalized_patient_id'].isin(df_coordinator_review['patient_id']) &
            ~df_review_tasks['normalized_patient_id'].isin(df_provider_review['patient_id'])
        ]
        
        print(f"\nUnmatched RVZ Review tasks: {len(unmatched_review)}")
        if len(unmatched_review) > 0:
            print("Sample unmatched Review tasks:")
            for i, (_, row) in enumerate(unmatched_review.head(5).iterrows()):
                print(f"  {i+1}. {row['Pt Name']} -> {row['normalized_patient_id']}")
                print(f"     Date: {row['Date Only']} -> {row['normalized_date']}")
                print(f"     Task: {row['Type']}")
                print()
        
        # Database Review task analysis
        print("=== DATABASE REVIEW TASK ANALYSIS ===")
        
        if len(df_coordinator_review) > 0:
            print("Coordinator Review Task Types:")
            coord_review_types = df_coordinator_review['task_type'].value_counts()
            for task_type, count in coord_review_types.head(10).items():
                print(f"  {task_type}: {count}")
            print()
        
        if len(df_provider_review) > 0:
            print("Provider Review Task Descriptions:")
            prov_review_types = df_provider_review['task_description'].value_counts()
            for task_desc, count in prov_review_types.head(10).items():
                print(f"  {task_desc}: {count}")
            print()
        
        # Summary
        print("=== SUMMARY ===")
        print(f"Total RVZ Review tasks: {len(df_review_tasks)}")
        print(f"Exact coordinator matches (patient + date): {len(exact_coordinator_matches)} ({len(exact_coordinator_matches)/len(df_review_tasks)*100:.1f}%)")
        print(f"Exact provider matches (patient + date): {len(exact_provider_matches)} ({len(exact_provider_matches)/len(df_review_tasks)*100:.1f}%)")
        print(f"Patient-only coordinator coverage: {len(coord_patient_matches)/len(df_review_tasks)*100:.1f}%")
        print(f"Patient-only provider coverage: {len(prov_patient_matches)/len(df_review_tasks)*100:.1f}%")
        print(f"Completely unmatched Review tasks: {len(unmatched_review)} ({len(unmatched_review)/len(df_review_tasks)*100:.1f}%)")
        
        if len(exact_coordinator_matches) > 0 or len(exact_provider_matches) > 0:
            print(f"\nGOOD NEWS: Found {len(exact_coordinator_matches) + len(exact_provider_matches)} exact matches!")
            print("This indicates that RVZ Review tasks are being properly imported and tracked.")
        else:
            print("\nNOTE: No exact date matches found for Review tasks.")
            print("This could indicate:")
            print("1. Different date formats or time periods")
            print("2. Tasks imported under different task types")
            print("3. Review tasks may be categorized differently in the database")
            
    except Exception as e:
        print(f"ERROR during validation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
        print(f"\nDetailed validation completed at {datetime.now()}")

if __name__ == "__main__":
    main()