#!/usr/bin/env python3
"""
RVZ Task Validation by Table Breakdown
Analyzes RVZ task matches across different table structures:
- Main tables: provider_tasks, coordinator_tasks
- Monthly tables: provider_tasks_YYYY_MM, coordinator_tasks_YYYY_MM
"""

import pandas as pd
import sqlite3
from datetime import datetime
import re

def normalize_patient_id(patient_id_raw):
    """Normalize patient ID using the same logic as SQL scripts"""
    if pd.isna(patient_id_raw) or patient_id_raw == '':
        return ''
    
    # Convert to string and apply normalization
    patient_id = str(patient_id_raw).strip()
    
    # Remove ZEN- prefix
    patient_id = patient_id.replace('ZEN-', '')
    
    # Replace comma-space with space
    patient_id = patient_id.replace(', ', ' ')
    
    # Replace comma with space
    patient_id = patient_id.replace(',', ' ')
    
    # Replace multiple spaces with single space
    patient_id = re.sub(r'\s+', ' ', patient_id)
    
    return patient_id.strip()

def normalize_date(date_str):
    """Normalize date to YYYY-MM-DD format"""
    if pd.isna(date_str) or date_str == '':
        return None
    
    try:
        # Try parsing MM/DD/YYYY format first
        if '/' in str(date_str):
            date_obj = pd.to_datetime(str(date_str), format='%m/%d/%Y')
        else:
            date_obj = pd.to_datetime(str(date_str))
        return date_obj.strftime('%Y-%m-%d')
    except:
        return None

def get_table_list(cursor):
    """Get all table names from the database"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]

def analyze_table_matches(cursor, rvz_data, table_name, table_type):
    """Analyze matches for a specific table"""
    print(f"\n=== Analyzing {table_name} ({table_type}) ===")
    
    try:
        # Check if table exists and get its schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        if not columns:
            print(f"  Table {table_name} not found or empty")
            return None
        
        print(f"  Columns: {', '.join(columns)}")
        
        # Build query based on available columns
        base_columns = ['patient_id', 'task_date']
        if 'task_description' in columns:
            base_columns.append('task_description')
        elif 'task_type' in columns:
            base_columns.append('task_type')
        
        if 'provider_id' in columns:
            base_columns.append('provider_id')
            staff_type = 'provider'
        elif 'coordinator_id' in columns:
            base_columns.append('coordinator_id')
            staff_type = 'coordinator'
        else:
            staff_type = 'unknown'
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]
        print(f"  Total rows: {total_rows:,}")
        
        if total_rows == 0:
            return {
                'table_name': table_name,
                'table_type': table_type,
                'staff_type': staff_type,
                'total_rows': 0,
                'patient_matches': 0,
                'exact_matches': 0,
                'match_rate': 0.0
            }
        
        # Query the table
        query = f"SELECT {', '.join(base_columns)} FROM {table_name}"
        cursor.execute(query)
        
        # Convert to DataFrame
        db_data = pd.DataFrame(cursor.fetchall(), columns=base_columns)
        
        if db_data.empty:
            print(f"  No data in {table_name}")
            return None
        
        # Normalize patient IDs and dates
        db_data['normalized_patient_id'] = db_data['patient_id'].apply(normalize_patient_id)
        db_data['normalized_date'] = db_data['task_date'].apply(normalize_date)
        
        # Create matching keys
        db_data['patient_date_key'] = db_data['normalized_patient_id'] + '|' + db_data['normalized_date'].fillna('')
        
        # Get task description column name
        task_desc_col = 'task_description' if 'task_description' in db_data.columns else 'task_type'
        
        # Create exact match key (patient + date + task description)
        if task_desc_col in db_data.columns:
            db_data['exact_match_key'] = (db_data['normalized_patient_id'] + '|' + 
                                        db_data['normalized_date'].fillna('') + '|' + 
                                        db_data[task_desc_col].fillna('').str.upper())
        else:
            db_data['exact_match_key'] = db_data['patient_date_key']
        
        # Count matches
        rvz_patient_ids = set(rvz_data['normalized_patient_id'])
        rvz_patient_date_keys = set(rvz_data['patient_date_key'])
        rvz_exact_keys = set(rvz_data['exact_match_key'])
        
        db_patient_ids = set(db_data['normalized_patient_id'])
        db_patient_date_keys = set(db_data['patient_date_key'])
        db_exact_keys = set(db_data['exact_match_key'])
        
        patient_matches = len(rvz_patient_ids.intersection(db_patient_ids))
        patient_date_matches = len(rvz_patient_date_keys.intersection(db_patient_date_keys))
        exact_matches = len(rvz_exact_keys.intersection(db_exact_keys))
        
        match_rate = (patient_matches / len(rvz_patient_ids)) * 100 if rvz_patient_ids else 0
        
        print(f"  Patient matches: {patient_matches:,} / {len(rvz_patient_ids):,} ({match_rate:.1f}%)")
        print(f"  Patient+Date matches: {patient_date_matches:,}")
        print(f"  Exact matches (patient+date+task): {exact_matches:,}")
        
        return {
            'table_name': table_name,
            'table_type': table_type,
            'staff_type': staff_type,
            'total_rows': total_rows,
            'patient_matches': patient_matches,
            'patient_date_matches': patient_date_matches,
            'exact_matches': exact_matches,
            'match_rate': match_rate
        }
        
    except Exception as e:
        print(f"  Error analyzing {table_name}: {str(e)}")
        return None

def main():
    print("RVZ Task Validation by Table Breakdown")
    print("=" * 50)
    print(f"Analysis started at {datetime.now()}")
    
    # Load RVZ data
    print("\n=== Loading RVZ Data ===")
    try:
        rvz_data = pd.read_csv('downloads/rvz.csv')
        print(f"Loaded {len(rvz_data):,} rows from RVZ CSV")
        
        # Normalize RVZ data
        rvz_data['normalized_patient_id'] = rvz_data['Pt Name'].apply(normalize_patient_id)
        rvz_data['normalized_date'] = rvz_data['Date Only'].apply(normalize_date)
        rvz_data['patient_date_key'] = rvz_data['normalized_patient_id'] + '|' + rvz_data['normalized_date'].fillna('')
        
        # Create exact match key for RVZ (patient + date + task type)
        rvz_data['exact_match_key'] = (rvz_data['normalized_patient_id'] + '|' + 
                                     rvz_data['normalized_date'].fillna('') + '|' + 
                                     rvz_data['Type'].fillna('').str.upper())
        
        # Filter out empty patient IDs
        rvz_data = rvz_data[rvz_data['normalized_patient_id'] != '']
        print(f"After filtering: {len(rvz_data):,} rows with valid patient IDs")
        
    except Exception as e:
        print(f"Error loading RVZ data: {str(e)}")
        return
    
    # Connect to database
    print("\n=== Connecting to Database ===")
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        print("Connected to production.db")
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return
    
    # Get all tables
    all_tables = get_table_list(cursor)
    print(f"Found {len(all_tables)} tables in database")
    
    # Categorize tables
    main_tables = []
    monthly_tables = []
    other_tables = []
    
    for table in all_tables:
        if table in ['provider_tasks', 'coordinator_tasks']:
            main_tables.append(table)
        elif re.match(r'(provider|coordinator)_tasks_\d{4}_\d{2}', table):
            monthly_tables.append(table)
        else:
            other_tables.append(table)
    
    print(f"\nTable categorization:")
    print(f"  Main tables: {len(main_tables)}")
    print(f"  Monthly tables: {len(monthly_tables)}")
    print(f"  Other tables: {len(other_tables)}")
    
    # Analyze tables
    results = []
    
    # Analyze main tables
    print(f"\n{'='*60}")
    print("MAIN TABLES ANALYSIS")
    print(f"{'='*60}")
    
    for table in main_tables:
        result = analyze_table_matches(cursor, rvz_data, table, 'main')
        if result:
            results.append(result)
    
    # Analyze monthly tables
    print(f"\n{'='*60}")
    print("MONTHLY TABLES ANALYSIS")
    print(f"{'='*60}")
    
    # Sort monthly tables by date
    monthly_tables.sort()
    
    for table in monthly_tables:
        result = analyze_table_matches(cursor, rvz_data, table, 'monthly')
        if result:
            results.append(result)
    
    # Summary analysis
    print(f"\n{'='*60}")
    print("SUMMARY BY TABLE TYPE")
    print(f"{'='*60}")
    
    if results:
        df_results = pd.DataFrame(results)
        
        # Group by table type
        for table_type in ['main', 'monthly']:
            type_data = df_results[df_results['table_type'] == table_type]
            if not type_data.empty:
                print(f"\n{table_type.upper()} TABLES:")
                total_rows = type_data['total_rows'].sum()
                total_patient_matches = type_data['patient_matches'].sum()
                total_exact_matches = type_data['exact_matches'].sum()
                
                print(f"  Tables: {len(type_data)}")
                print(f"  Total rows: {total_rows:,}")
                print(f"  Total patient matches: {total_patient_matches:,}")
                total_patient_date_matches = type_data['patient_date_matches'].sum()
                print(f"  Total patient+date matches: {total_patient_date_matches:,}")
                print(f"  Total exact matches (patient+date+task): {total_exact_matches:,}")
                
                # Show individual table breakdown
                for _, row in type_data.iterrows():
                    print(f"    {row['table_name']}: {row['total_rows']:,} rows, "
                          f"{row['patient_matches']:,} patient, "
                          f"{row['patient_date_matches']:,} patient+date, "
                          f"{row['exact_matches']:,} exact matches ({row['match_rate']:.1f}%)")
        
        # Overall summary
        print(f"\nOVERALL SUMMARY:")
        total_rows = df_results['total_rows'].sum()
        total_patient_matches = df_results['patient_matches'].sum()
        total_patient_date_matches = df_results['patient_date_matches'].sum()
        total_exact_matches = df_results['exact_matches'].sum()
        
        print(f"  All tables: {len(df_results)}")
        print(f"  Total rows across all tables: {total_rows:,}")
        print(f"  Total patient matches: {total_patient_matches:,}")
        print(f"  Total patient+date matches: {total_patient_date_matches:,}")
        print(f"  Total exact matches (patient+date+task): {total_exact_matches:,}")
        
        # Show top performing tables
        print(f"\nTOP PERFORMING TABLES (by exact matches):")
        top_tables = df_results.nlargest(10, 'exact_matches')
        for _, row in top_tables.iterrows():
            print(f"  {row['table_name']}: {row['exact_matches']:,} exact matches "
                  f"({row['match_rate']:.1f}% patient coverage)")
    
    conn.close()
    print(f"\nAnalysis completed at {datetime.now()}")

if __name__ == "__main__":
    main()