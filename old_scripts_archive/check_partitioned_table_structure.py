#!/usr/bin/env python3
"""
Check the structure of partitioned tables to understand the billing_week column issue
"""
import sqlite3

def main():
    # Connect to production database
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()

    # Check structure of main provider_tasks table
    print('PROVIDER_TASKS TABLE STRUCTURE:')
    print('=' * 50)
    cursor.execute('PRAGMA table_info(provider_tasks)')
    main_columns = cursor.fetchall()
    for col in main_columns:
        print(f'  {col[1]} ({col[2]})')
    
    # Check if main table has billing_week column
    has_billing_week = any(col[1] == 'billing_week' for col in main_columns)
    print(f'\nMain table has billing_week column: {has_billing_week}')
    
    # Check structure of October partitioned table
    print('\n\nPROVIDER_TASKS_2025_10 TABLE STRUCTURE:')
    print('=' * 50)
    try:
        cursor.execute('PRAGMA table_info(provider_tasks_2025_10)')
        oct_columns = cursor.fetchall()
        for col in oct_columns:
            print(f'  {col[1]} ({col[2]})')
        
        # Check if October table has billing_week column
        has_billing_week_oct = any(col[1] == 'billing_week' for col in oct_columns)
        print(f'\nOctober table has billing_week column: {has_billing_week_oct}')
        
    except Exception as e:
        print(f'Error checking provider_tasks_2025_10: {e}')

    # Check structure of November partitioned table
    print('\n\nPROVIDER_TASKS_2025_11 TABLE STRUCTURE:')
    print('=' * 50)
    try:
        cursor.execute('PRAGMA table_info(provider_tasks_2025_11)')
        nov_columns = cursor.fetchall()
        for col in nov_columns:
            print(f'  {col[1]} ({col[2]})')
        
        # Check if November table has billing_week column
        has_billing_week_nov = any(col[1] == 'billing_week' for col in nov_columns)
        print(f'\nNovember table has billing_week column: {has_billing_week_nov}')
        
    except Exception as e:
        print(f'Error checking provider_tasks_2025_11: {e}')
    
    # Sample data from October table to see what we have to work with
    print('\n\nSAMPLE DATA FROM OCTOBER TABLE:')
    print('=' * 50)
    try:
        cursor.execute('SELECT * FROM provider_tasks_2025_10 LIMIT 3')
        sample_data = cursor.fetchall()
        print(f'Found {len(sample_data)} sample records')
        
        if sample_data:
            # Get column names
            column_names = [description[0] for description in cursor.description]
            print('Column names:', column_names)
            print('Sample data:')
            for i, row in enumerate(sample_data):
                print(f'  Record {i+1}: {dict(zip(column_names, row))}')
        
    except Exception as e:
        print(f'Error getting sample data from October table: {e}')
    
    conn.close()

if __name__ == '__main__':
    main()