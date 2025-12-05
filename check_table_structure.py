#!/usr/bin/env python3
"""
Check database table structure for billing dashboard fixes
"""
import sqlite3
from datetime import datetime

def main():
    # Connect to database and check table structure
    conn = sqlite3.connect('healthcare.db')
    cursor = conn.cursor()

    # Check all provider_tasks related tables
    cursor.execute("SELECT name FROM sqlite_master WHERE name LIKE 'provider_tasks%' ORDER BY name")
    tables = cursor.fetchall()
    print('Provider tasks related tables:')
    for table in tables:
        print(f'  - {table[0]}')

    # Check structure of partitioned tables
    cursor.execute('PRAGMA table_info(provider_tasks_2025_11)')
    columns = cursor.fetchall()
    print(f'\nColumns in provider_tasks_2025_11: {[col[1] for col in columns]}')

    # Check data ranges in partitioned tables
    print('\nDate ranges in partitioned tables:')
    for table in ['provider_tasks_2025_10', 'provider_tasks_2025_11']:
        try:
            cursor.execute(f'SELECT MIN(task_date), MAX(task_date) FROM {table}')
            min_date, max_date = cursor.fetchone()
            print(f'  {table}: {min_date} to {max_date}')
        except sqlite3.OperationalError as e:
            print(f'  {table}: Error - {e}')

    conn.close()

if __name__ == '__main__':
    main()