#!/usr/bin/env python3

import sqlite3
import os

def examine_database():
    """Examine the sheets_data.db to understand the data structure and identify metrics issues"""
    
    db_path = 'sheets_data.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("="*60)
    print("SHEETS_DATA.DB ANALYSIS")
    print("="*60)
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\nFound {len(tables)} tables:")
    
    task_related_tables = []
    for table in tables:
        table_name = table[0]
        print(f"  - {table_name}")
        if 'task' in table_name.lower():
            task_related_tables.append(table_name)
    
    print(f"\nFound {len(task_related_tables)} task-related tables:")
    
    for table_name in task_related_tables:
        print(f"\n--- {table_name} ---")
        try:
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name});")
            cols = cursor.fetchall()
            print("Columns:")
            for col in cols:
                print(f"  {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")
            
            # Sample first few rows if any data exists
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                sample_rows = cursor.fetchall()
                print("Sample data (first 5 rows):")
                for i, row in enumerate(sample_rows):
                    print(f"  Row {i+1}: {row}")
                    
        except Exception as e:
            print(f"Error examining {table_name}: {e}")
    
    # Now check main database structure for comparison
    print("\n" + "="*60)
    print("MAIN DATABASE (probably production.db)")
    print("="*60)
    
    main_db = None
    for possible_db in ['production.db', 'app.db', 'zen.db']:
        if os.path.exists(possible_db):
            main_db = possible_db
            break
    
    if main_db:
        print(f"Found main database: {main_db}")
        
        main_conn = sqlite3.connect(main_db)
        main_cursor = main_conn.cursor()
        
        # Get all table names
        main_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        main_tables = main_cursor.fetchall()
        
        print(f"\nFound {len(main_tables)} tables in main DB:")
        main_task_tables = []
        for table in main_tables:
            table_name = table[0]
            print(f"  - {table_name}")
            if 'task' in table_name.lower():
                main_task_tables.append(table_name)
        
        print(f"\nFound {len(main_task_tables)} task-related tables in main DB:")
        
        for table_name in main_task_tables:
            print(f"\n--- {table_name} ---")
            try:
                # Get table structure
                main_cursor.execute(f"PRAGMA table_info({table_name});")
                cols = main_cursor.fetchall()
                print("Columns:")
                for col in cols:
                    print(f"  {col[1]} ({col[2]})")
                
                # Get row count
                main_cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = main_cursor.fetchone()[0]
                print(f"Row count: {count}")
                
                # Check for metrics-related columns
                if count > 0:
                    main_cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                    sample_rows = main_cursor.fetchall()
                    print("Sample data (first 3 rows):")
                    for i, row in enumerate(sample_rows):
                        print(f"  Row {i+1}: {row}")
                        
            except Exception as e:
                print(f"Error examining {table_name}: {e}")
        
        main_conn.close()
    else:
        print("No main database found!")
    
    conn.close()

if __name__ == "__main__":
    examine_database()