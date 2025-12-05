#!/usr/bin/env python3

import sqlite3

def check_table_names():
    conn = sqlite3.connect('sheets_data.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    print('Actual table names in sheets_data.db:')
    task_tables = []
    for table in tables:
        table_name = table[0]
        if 'task' in table_name.lower():
            task_tables.append(table_name)
            print(f'  - {table_name}')
    
    print(f'\nFound {len(task_tables)} task tables total:')
    for table_name in sorted(task_tables):
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
            count = cursor.fetchone()[0]
            print(f'  {table_name}: {count} records')
        except Exception as e:
            print(f'  {table_name}: Error - {e}')
    
    conn.close()

if __name__ == "__main__":
    check_table_names()