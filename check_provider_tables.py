"""Check what provider task tables exist in the database."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import get_db_connection

def check_tables():
    conn = get_db_connection()
    
    # Check provider task tables
    print("Provider task tables:")
    tables = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'provider_tasks_%' 
        ORDER BY name DESC
    """).fetchall()
    
    if tables:
        for table in tables:
            print(f"  - {table[0]}")
            
            # Get row count for each table
            count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
            print(f"    Rows: {count}")
    else:
        print("  No provider_tasks tables found")
    
    # Check weekly summary tables
    print("\nWeekly summary tables:")
    weekly_tables = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE '%weekly%' 
        ORDER BY name
    """).fetchall()
    
    if weekly_tables:
        for table in weekly_tables:
            print(f"  - {table[0]}")
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                print(f"    Rows: {count}")
            except Exception as e:
                print(f"    Error: {e}")
    else:
        print("  No weekly tables found")
    
    # Check billing tables
    print("\nBilling system tables:")
    billing_tables = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN (
            'weekly_billing_reports', 
            'provider_task_billing_status', 
            'billing_status_history'
        )
        ORDER BY name
    """).fetchall()
    
    if billing_tables:
        for table in billing_tables:
            print(f"  - {table[0]}")
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                print(f"    Rows: {count}")
            except Exception as e:
                print(f"    Error: {e}")
    else:
        print("  No billing system tables found")
    
    conn.close()

if __name__ == "__main__":
    check_tables()