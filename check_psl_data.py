#!/usr/bin/env python3
"""
Check PSL source data vs provider_tasks table to identify missing providers
"""

import sqlite3
import pandas as pd

def main():
    conn = sqlite3.connect('production.db')
    
    print('=== CHECKING SOURCE PSL TABLES ===')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'source_psl%' ORDER BY name")
    source_tables = cursor.fetchall()
    
    print(f'Found {len(source_tables)} source PSL tables:')
    for table in source_tables:
        print(f'- {table[0]}')
    
    if source_tables:
        # Check the most recent table
        table_name = source_tables[-1][0]
        print(f'\n=== ANALYZING {table_name} ===')
        
        # Get column info
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = cursor.fetchall()
        print('Columns:')
        for col in columns[:10]:  # Show first 10 columns
            print(f'  {col[1]}: {col[2]}')
        
        # Check provider data (column 3 typically contains provider codes)
        query = f'''
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT "3") as unique_providers
        FROM {table_name}
        WHERE "3" IS NOT NULL AND "3" != ""
        '''
        df = pd.read_sql_query(query, conn)
        print(f'\nTotal records: {df.iloc[0][0]}, Unique providers: {df.iloc[0][1]}')
        
        # Show sample provider codes
        query = f'''
        SELECT DISTINCT "3" as provider_code, COUNT(*) as count
        FROM {table_name}
        WHERE "3" IS NOT NULL AND "3" != ""
        GROUP BY "3"
        ORDER BY count DESC
        LIMIT 15
        '''
        df = pd.read_sql_query(query, conn)
        print('\nProvider codes in source data:')
        print(df.to_string(index=False))
        
        # Compare with staff_code_mapping
        print('\n=== COMPARING WITH STAFF CODE MAPPING ===')
        query = '''
        SELECT scm.staff_code, u.full_name, scm.confidence_level
        FROM staff_code_mapping scm
        JOIN users u ON scm.user_id = u.user_id
        WHERE scm.confidence_level = 'HIGH'
        ORDER BY scm.staff_code
        '''
        mapping_df = pd.read_sql_query(query, conn)
        print('Staff code mappings:')
        print(mapping_df.to_string(index=False))
        
        # Check which source codes are mapped
        source_codes = set(df['provider_code'].tolist())
        mapped_codes = set(mapping_df['staff_code'].tolist())
        
        print(f'\nSource codes: {len(source_codes)}')
        print(f'Mapped codes: {len(mapped_codes)}')
        print(f'Unmapped codes: {len(source_codes - mapped_codes)}')
        
        if source_codes - mapped_codes:
            print('\nUnmapped provider codes:')
            for code in sorted(source_codes - mapped_codes):
                print(f'  {code}')
    
    # Check current provider_tasks data
    print('\n=== CURRENT PROVIDER_TASKS DATA ===')
    query = '''
    SELECT 
        provider_name,
        COUNT(*) as task_count,
        MIN(task_date) as first_task,
        MAX(task_date) as last_task
    FROM provider_tasks
    WHERE provider_name IS NOT NULL
    GROUP BY provider_name
    ORDER BY task_count DESC
    '''
    df = pd.read_sql_query(query, conn)
    print('Current providers in provider_tasks:')
    print(df.to_string(index=False))
    
    conn.close()

if __name__ == '__main__':
    main()