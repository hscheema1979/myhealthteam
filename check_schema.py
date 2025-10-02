#!/usr/bin/env python3
"""
Check database schema to understand table structure
"""

import sqlite3
import os

def main():
    db_file = "production.db"
    
    if not os.path.exists(db_file):
        print(f"ERROR: {db_file} not found")
        return
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("=== DATABASE TABLES ===")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, primary_key = col
                print(f"  {col_name} ({col_type})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()