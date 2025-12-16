#!/usr/bin/env python3

import sqlite3

def check_current_formats():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print('CURRENT COORDINATOR IDs IN tasks:')
    cursor.execute('SELECT DISTINCT coordinator_id FROM coordinator_tasks_2025_10 LIMIT 10;')
    coordinator_ids = cursor.fetchall()
    for row in coordinator_ids:
        print(f'  - {row[0]}')
    
    print('\nCURRENT PROVIDER IDs IN tasks:')
    cursor.execute('SELECT DISTINCT provider_name FROM provider_tasks_2025_10 LIMIT 10;')
    provider_names = cursor.fetchall()
    for row in provider_names:
        print(f'  - {row[0]}')
    
    print('\nLooking for users/staff tables...')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%user%' OR name LIKE '%staff%');")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        print(f'  - {table_name}')
        
        if 'user' in table_name.lower():
            cursor.execute(f'PRAGMA table_info("{table_name}");')
            cols = cursor.fetchall()
            print(f'    Columns: {[col[1] for col in cols]}')
            
            cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 3;')
            sample = cursor.fetchall()
            print(f'    Sample: {sample}')
    
    conn.close()

if __name__ == "__main__":
    check_current_formats()