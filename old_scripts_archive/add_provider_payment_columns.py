"""
Add provider_paid and provider_paid_date columns to provider_tasks tables
This enables tracking of provider payment status for payroll
"""

import sqlite3

DB_PATH = 'production.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Adding provider payment tracking columns to provider_tasks tables...")
    
    # Get all provider_tasks tables (including partitioned ones)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks%'")
    provider_tables = [row[0] for row in cursor.fetchall()]
    
    for table in provider_tables:
        try:
            # Check current columns
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Add provider_paid column if it doesn't exist
            if 'provider_paid' not in columns:
                print(f"  Adding provider_paid to {table}")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN provider_paid INTEGER DEFAULT 0")
            else:
                print(f"  {table} already has provider_paid column")
            
            # Add provider_paid_date column if it doesn't exist
            if 'provider_paid_date' not in columns:
                print(f"  Adding provider_paid_date to {table}")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN provider_paid_date DATE")
            else:
                print(f"  {table} already has provider_paid_date column")
                
        except Exception as e:
            print(f"  Error on {table}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\nDone! Provider payment tracking columns added.")

if __name__ == "__main__":
    main()
