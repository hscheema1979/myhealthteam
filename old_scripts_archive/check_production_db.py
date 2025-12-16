#!/usr/bin/env python3

import sqlite3
import os

def check_production_database():
    """Check what's in production.db"""
    
    if not os.path.exists('production.db'):
        print("❌ production.db not found!")
        return
    
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print("=== PRODUCTION.DB ANALYSIS ===")
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} total tables")
    
    task_tables = []
    for table in tables:
        table_name = table[0]
        if 'task' in table_name.lower():
            task_tables.append(table_name)
    
    print(f"\nFound {len(task_tables)} task-related tables in production.db:")
    
    for table in task_tables:
        print(f"  - {table}")
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"    Row count: {count}")
            
            # Show first few rows if data exists
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample_rows = cursor.fetchall()
                print("    Sample data (first 3 rows):")
                for i, row in enumerate(sample_rows):
                    print(f"      Row {i+1}: {row}")
        except Exception as e:
            print(f"    Error: {e}")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_production_database()