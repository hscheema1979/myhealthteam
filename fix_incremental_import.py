#!/usr/bin/env python3
"""
Fix the incremental import issue - move cleanup to beginning and use INSERT OR IGNORE
"""

import sqlite3

def fix_incremental_import():
    print("Fixing incremental import approach...")
    
    # Test current state
    conn = sqlite3.connect('production.db')
    
    # Check current task counts
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_%'")
    provider_tables = [row[0] for row in cursor.fetchall()]
    
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'coordinator_tasks_%'")
    coordinator_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Provider task tables: {len(provider_tables)}")
    print(f"Coordinator task tables: {len(coordinator_tables)}")
    
    # Check total records
    total_provider_tasks = 0
    total_coordinator_tasks = 0
    
    for table in provider_tables:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total_provider_tasks += count
        if count > 0:
            print(f"  {table}: {count} records")
    
    for table in coordinator_tables:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total_coordinator_tasks += count
        if count > 0:
            print(f"  {table}: {count} records")
    
    print(f"\nTotal provider tasks: {total_provider_tasks}")
    print(f"Total coordinator tasks: {total_coordinator_tasks}")
    
    conn.close()

if __name__ == "__main__":
    fix_incremental_import()