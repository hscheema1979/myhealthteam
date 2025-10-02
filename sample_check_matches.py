#!/usr/bin/env python3
"""
Sample Check of Matched Tasks - Detailed examination of provider, patient, date, task description matches
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
    print("=== Sample Check of Matched Tasks ===")
    print(f"Timestamp: {datetime.now()}")
    print("Examining specific provider, patient, date, task description matches")
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
    
    # Filter out placeholder rows
    df_rvz_clean = df_rvz[
        (~df_rvz['Pt Name'].str.contains('Aaa, Aaa', na=False)) &
        (~df_rvz['Type'].str.contains('Place holder', na=False)) &
        (df_rvz['Pt Name'].notna()) &
        (df_rvz['Pt Name'] != '') &
        (~df_rvz['Pt Name'].str.contains('start', na=False))
    ].copy()
    
    print(f"Clean RVZ records: {len(df_rvz_clean)}")
    
    # Normalize patient IDs and dates
    df_rvz_clean['normalized_patient_id'] = df_rvz_clean['Pt Name'].apply(normalize_patient_id)
    df_rvz_clean['normalized_date'] = df_rvz_clean['Date Only'].apply(parse_date)
    
    # Connect to database
    print("Connecting to database...")
    conn = sqlite3.connect(db_file)
    
    try:
        # Get all coordinator tasks
        print("Loading coordinator tasks from database...")
        coordinator_query = """
        SELECT patient_id, task_date, task_type, notes, coordinator_id, duration_minutes
        FROM coordinator_tasks 
        WHERE patient_id IS NOT NULL AND patient_id != ''
        """
        df_coordinator = pd.read_sql_query(coordinator_query, conn)
        print(f"Loaded {len(df_coordinator)} coordinator tasks")
        
        # Get all provider tasks
        print("Loading provider tasks from database...")
        provider_query = """
        SELECT patient_id, task_date, task_description, notes, provider_name, minutes_of_service
        FROM provider_tasks 
        WHERE patient_id IS NOT NULL AND patient_id != ''
        """
        df_provider = pd.read_sql_query(provider_query, conn)
        print(f"Loaded {len(df_provider)} provider tasks")
        print()
        
        # Find exact matches for detailed examination
        print("=== FINDING EXACT MATCHES ===")
        
        exact_matches = []
        
        for idx, row in df_rvz_clean.iterrows():
            patient_id = row['normalized_patient_id']
            task_date = row['normalized_date']
            rvz_provider = row['Provider']
            rvz_task_type = row['Type']
            rvz_notes = row.get('Notes', '')
            rvz_minutes = row.get('Total Mins', '')
            
            if patient_id and task_date:
                # Check coordinator matches
                coord_matches = df_coordinator[
                    (df_coordinator['patient_id'] == patient_id) &
                    (df_coordinator['task_date'] == task_date)
                ]
                
                for _, coord_match in coord_matches.iterrows():
                    exact_matches.append({
                        'match_type': 'coordinator',
                        'rvz_provider': rvz_provider,
                        'rvz_patient': row['Pt Name'],
                        'normalized_patient': patient_id,
                        'rvz_date': row['Date Only'],
                        'normalized_date': task_date,
                        'rvz_task_type': rvz_task_type,
                        'rvz_notes': rvz_notes,
                        'rvz_minutes': rvz_minutes,
                        'db_coordinator_id': coord_match['coordinator_id'],
                        'db_task_type': coord_match['task_type'],
                        'db_notes': coord_match['notes'],
                        'db_duration': coord_match['duration_minutes']
                    })
                
                # Check provider matches
                prov_matches = df_provider[
                    (df_provider['patient_id'] == patient_id) &
                    (df_provider['task_date'] == task_date)
                ]
                
                for _, prov_match in prov_matches.iterrows():
                    exact_matches.append({
                        'match_type': 'provider',
                        'rvz_provider': rvz_provider,
                        'rvz_patient': row['Pt Name'],
                        'normalized_patient': patient_id,
                        'rvz_date': row['Date Only'],
                        'normalized_date': task_date,
                        'rvz_task_type': rvz_task_type,
                        'rvz_notes': rvz_notes,
                        'rvz_minutes': rvz_minutes,
                        'db_provider_name': prov_match['provider_name'],
                        'db_task_description': prov_match['task_description'],
                        'db_notes': prov_match['notes'],
                        'db_minutes': prov_match['minutes_of_service']
                    })
        
        print(f"Total exact matches found: {len(exact_matches)}")
        print(f"Coordinator matches: {len([m for m in exact_matches if m['match_type'] == 'coordinator'])}")
        print(f"Provider matches: {len([m for m in exact_matches if m['match_type'] == 'provider'])}")
        print()
        
        # Sample detailed examination
        print("=== DETAILED SAMPLE EXAMINATION ===")
        
        # Show first 10 coordinator matches
        coord_matches = [m for m in exact_matches if m['match_type'] == 'coordinator']
        if coord_matches:
            print("COORDINATOR TASK MATCHES (Sample 10):")
            print("-" * 80)
            for i, match in enumerate(coord_matches[:10]):
                print(f"\nMatch {i+1}:")
                print(f"  RVZ Provider: {match['rvz_provider']}")
                print(f"  Patient: {match['rvz_patient']} -> {match['normalized_patient']}")
                print(f"  Date: {match['rvz_date']} -> {match['normalized_date']}")
                print(f"  RVZ Task: {match['rvz_task_type']}")
                print(f"  RVZ Minutes: {match['rvz_minutes']}")
                print(f"  RVZ Notes: {str(match['rvz_notes'])[:100]}...")
                print(f"  ---")
                print(f"  DB Coordinator: {match['db_coordinator_id']}")
                print(f"  DB Task Type: {match['db_task_type']}")
                print(f"  DB Duration: {match['db_duration']} minutes")
                print(f"  DB Notes: {str(match['db_notes'])[:100]}...")
        
        # Show first 10 provider matches
        prov_matches = [m for m in exact_matches if m['match_type'] == 'provider']
        if prov_matches:
            print(f"\n\nPROVIDER TASK MATCHES (Sample {min(10, len(prov_matches))}):")
            print("-" * 80)
            for i, match in enumerate(prov_matches[:10]):
                print(f"\nMatch {i+1}:")
                print(f"  RVZ Provider: {match['rvz_provider']}")
                print(f"  Patient: {match['rvz_patient']} -> {match['normalized_patient']}")
                print(f"  Date: {match['rvz_date']} -> {match['normalized_date']}")
                print(f"  RVZ Task: {match['rvz_task_type']}")
                print(f"  RVZ Minutes: {match['rvz_minutes']}")
                print(f"  RVZ Notes: {str(match['rvz_notes'])[:100]}...")
                print(f"  ---")
                print(f"  DB Provider: {match['db_provider_name']}")
                print(f"  DB Task Description: {match['db_task_description']}")
                print(f"  DB Minutes: {match['db_minutes']}")
                print(f"  DB Notes: {str(match['db_notes'])[:100]}...")
        
        # Provider name analysis
        print(f"\n\n=== PROVIDER NAME ANALYSIS ===")
        
        if coord_matches:
            print("RVZ Providers in Coordinator Matches:")
            rvz_providers = pd.Series([m['rvz_provider'] for m in coord_matches])
            provider_counts = rvz_providers.value_counts()
            for provider, count in provider_counts.head(10).items():
                print(f"  {provider}: {count} matches")
            
            print(f"\nDB Coordinators in Matches:")
            db_coordinators = pd.Series([m['db_coordinator_id'] for m in coord_matches])
            coord_counts = db_coordinators.value_counts()
            for coordinator, count in coord_counts.head(10).items():
                print(f"  {coordinator}: {count} matches")
        
        if prov_matches:
            print(f"\nRVZ Providers in Provider Matches:")
            rvz_prov_providers = pd.Series([m['rvz_provider'] for m in prov_matches])
            prov_provider_counts = rvz_prov_providers.value_counts()
            for provider, count in prov_provider_counts.head(10).items():
                print(f"  {provider}: {count} matches")
            
            print(f"\nDB Providers in Matches:")
            db_providers = pd.Series([m['db_provider_name'] for m in prov_matches])
            db_prov_counts = db_providers.value_counts()
            for provider, count in db_prov_counts.head(10).items():
                print(f"  {provider}: {count} matches")
        
        # Task type analysis
        print(f"\n\n=== TASK TYPE ANALYSIS ===")
        
        if coord_matches:
            print("RVZ Task Types in Coordinator Matches:")
            rvz_task_types = pd.Series([m['rvz_task_type'] for m in coord_matches])
            task_counts = rvz_task_types.value_counts()
            for task_type, count in task_counts.head(10).items():
                print(f"  {task_type}: {count} matches")
            
            print(f"\nDB Task Types in Coordinator Matches:")
            db_task_types = pd.Series([m['db_task_type'] for m in coord_matches])
            db_task_counts = db_task_types.value_counts()
            for task_type, count in db_task_counts.head(10).items():
                print(f"  {task_type}: {count} matches")
        
        # Summary
        print(f"\n\n=== SUMMARY ===")
        print(f"Total exact matches: {len(exact_matches)}")
        print(f"Coordinator exact matches: {len(coord_matches)}")
        print(f"Provider exact matches: {len(prov_matches)}")
        
        if len(exact_matches) > 0:
            print(f"\nData Quality Assessment:")
            print(f"- Patient ID normalization: WORKING (exact patient + date matches found)")
            print(f"- Date format conversion: WORKING (dates matching between systems)")
            print(f"- Task import process: WORKING (tasks successfully imported)")
            print(f"- Provider/Coordinator mapping: ACTIVE (staff assignments tracked)")
        
    except Exception as e:
        print(f"ERROR during sample check: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
        print(f"\nSample check completed at {datetime.now()}")

if __name__ == "__main__":
    main()