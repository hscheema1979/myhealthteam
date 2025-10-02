#!/usr/bin/env python3
"""
Normalize patient names in provider_tasks table by removing commas
"""

import sqlite3
import pandas as pd

def normalize_provider_patient_names():
    """Remove commas from patient_name column in provider_tasks table"""
    
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print('=== NORMALIZING PROVIDER_TASKS PATIENT NAMES ===')
    
    # Count records with commas before normalization
    cursor.execute('SELECT COUNT(*) FROM provider_tasks WHERE patient_name LIKE "%,%"')
    before_count = cursor.fetchone()[0]
    print(f'Records with commas before normalization: {before_count}')
    
    if before_count == 0:
        print('No records with commas found. Already normalized.')
        conn.close()
        return
    
    # Update patient_name to remove commas
    cursor.execute('''
        UPDATE provider_tasks 
        SET patient_name = REPLACE(patient_name, ",", "")
        WHERE patient_name LIKE "%,%"
    ''')
    
    # Count records with commas after normalization
    cursor.execute('SELECT COUNT(*) FROM provider_tasks WHERE patient_name LIKE "%,%"')
    after_count = cursor.fetchone()[0]
    print(f'Records with commas after normalization: {after_count}')
    
    print(f'Successfully normalized {before_count} records')
    
    # Show sample of normalized names
    print('\nSample normalized patient names:')
    sample_df = pd.read_sql_query('''
        SELECT patient_name, COUNT(*) as count
        FROM provider_tasks 
        GROUP BY patient_name 
        ORDER BY count DESC 
        LIMIT 10
    ''', conn)
    print(sample_df.to_string(index=False))
    
    conn.commit()
    conn.close()
    
    print('\nNormalization complete!')

if __name__ == "__main__":
    normalize_provider_patient_names()