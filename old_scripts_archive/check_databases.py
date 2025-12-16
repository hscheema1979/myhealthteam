#!/usr/bin/env python3
"""
Check database files and structure for billing dashboard
"""
import sqlite3
import os
import glob

def main():
    # Check for database files
    print('DATABASE FILES:')
    for db_file in ['healthcare.db', 'production.db', '*.db']:
        files = glob.glob(db_file)
        if files:
            print(f'Found {db_file}: {files}')
            
            # Try to connect to each found file
            for db_path in files:
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    print(f'\nChecking {db_path}:')
                    
                    # Check provider_tasks tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE name LIKE 'provider_tasks%' ORDER BY name")
                    tables = cursor.fetchall()
                    print(f'  provider_tasks tables: {[t[0] for t in tables]}')
                    
                    # If we have partitioned tables, check their structure
                    for table in tables:
                        table_name = table[0]
                        if table_name != 'provider_tasks':
                            try:
                                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                                count = cursor.fetchone()[0]
                                print(f'    {table_name}: {count} records')
                            except Exception as e:
                                print(f'    {table_name}: Error - {e}')
                    
                    conn.close()
                    
                except Exception as e:
                    print(f'Error connecting to {db_path}: {e}')

if __name__ == '__main__':
    main()