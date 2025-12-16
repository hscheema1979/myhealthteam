#!/usr/bin/env python3
"""
Check the actual column structure of task tables
"""

import sqlite3

def check_task_table_structure():
    print("Checking task table column structure")
    print("=" * 50)
    
    conn = sqlite3.connect('production.db')
    
    # Get a few task tables to check their structure
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'provider_tasks_%' 
        LIMIT 3
    """)
    
    provider_tables = [row[0] for row in cursor.fetchall()]
    
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'coordinator_tasks_%' 
        LIMIT 3
    """)
    
    coordinator_tables = [row[0] for row in cursor.fetchall()]
    
    print("Provider task tables:")
    for table_name in provider_tables:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"\n{table_name}:")
        for col in columns:
            cid, name, type, notnull, dflt_value, pk = col
            print(f"  {name}: {type}")
    
    print("\nCoordinator task tables:")
    for table_name in coordinator_tables:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"\n{table_name}:")
        for col in columns:
            cid, name, type, notnull, dflt_value, pk = col
            print(f"  {name}: {type}")
    
    # Also check the billing status table
    print("\nProvider task billing status table:")
    try:
        cursor = conn.execute("PRAGMA table_info(provider_task_billing_status)")
        columns = cursor.fetchall()
        for col in columns:
            cid, name, type, notnull, dflt_value, pk = col
            print(f"  {name}: {type}")
    except:
        print("  Table not found")
    
    conn.close()

if __name__ == "__main__":
    check_task_table_structure()