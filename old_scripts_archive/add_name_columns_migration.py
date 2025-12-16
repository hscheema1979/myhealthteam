"""
Add provider_name and coordinator_name columns to all existing task tables
This is a one-time migration script
"""

import sqlite3

DB_PATH = 'production.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Adding name columns to existing task tables...")
    
    # Get all provider_tasks tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_%'")
    provider_tables = [row[0] for row in cursor.fetchall()]
    
    # Get all coordinator_tasks tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'coordinator_tasks_%'")
    coordinator_tables = [row[0] for row in cursor.fetchall()]
    
    # Add provider_name column to provider_tasks tables
    for table in provider_tables:
        try:
            # Check if column already exists
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'provider_name' not in columns:
                print(f"Adding provider_name to {table}")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN provider_name TEXT")
            else:
                print(f"  {table} already has provider_name column")
        except Exception as e:
            print(f"  Error on {table}: {e}")
    
    # Add coordinator_name column to coordinator_tasks tables
    for table in coordinator_tables:
        try:
            # Check if column already exists
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'coordinator_name' not in columns:
                print(f"Adding coordinator_name to {table}")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN coordinator_name TEXT")
            else:
                print(f"  {table} already has coordinator_name column")
        except Exception as e:
            print(f"  Error on {table}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\nDone! Now re-run transform_production_data_v3.py to populate the names.")

if __name__ == "__main__":
    main()
