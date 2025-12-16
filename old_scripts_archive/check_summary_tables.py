#!/usr/bin/env python3

import sqlite3

def check_summary_tables():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Check for coordinator monthly summary tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%coordinator_monthly_summary%';")
    summary_tables = cursor.fetchall()
    
    print('Found coordinator monthly summary tables:')
    for table in summary_tables:
        table_name = table[0]
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
            count = cursor.fetchone()[0]
            print(f'  {table_name}: {count} records')
        except Exception as e:
            print(f'  {table_name}: Error - {e}')
    
    conn.close()

if __name__ == "__main__":
    check_summary_tables()