#!/usr/bin/env python3
"""
Check database schema and staff_code_mapping table
"""

import sqlite3
import pandas as pd

def check_database_schema():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print("Available tables:", tables)
    
    # Check if staff_code_mapping exists
    if 'staff_code_mapping' in tables:
        print("\n✓ staff_code_mapping table exists")
        
        # Show schema
        cursor.execute("PRAGMA table_info(staff_code_mapping)")
        columns = cursor.fetchall()
        print("staff_code_mapping columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
            
        # Show sample data
        df = pd.read_sql_query("SELECT * FROM staff_code_mapping LIMIT 10", conn)
        print("\nSample data:")
        print(df)
        
    else:
        print("\n✗ staff_code_mapping table does NOT exist")
        
    # Check other relevant tables
    for table in ['coordinator_tasks', 'provider_tasks']:
        if table in tables:
            print(f"\n{table} columns:")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    check_database_schema()