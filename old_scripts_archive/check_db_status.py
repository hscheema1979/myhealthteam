#!/usr/bin/env python3
import sqlite3
import os

def check_database_status():
    """Check the current status of the production database"""
    
    if not os.path.exists('production.db'):
        print("❌ production.db not found!")
        return
    
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    try:
        # Check what monthly task tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'coordinator_tasks_%' ORDER BY name")
        coordinator_tables = cursor.fetchall()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_%' ORDER BY name")
        provider_tables = cursor.fetchall()
        
        print("📊 DATABASE STATUS REPORT")
        print("=" * 50)
        
        print("\n📋 COORDINATOR TABLES:")
        for table in coordinator_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table[0]}: {count} rows")
        
        if not coordinator_tables:
            print("  ❌ No coordinator tables found!")
        
        print("\n🏥 PROVIDER TABLES:")
        for table in provider_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table[0]}: {count} rows")
        
        if not provider_tables:
            print("  ❌ No provider tables found!")
        
        # Check summary tables
        print("\n📈 SUMMARY TABLES:")
        summary_tables = [
            'provider_performance_summary', 
            'coordinator_performance_summary', 
            'patient_assignment_summary',
            'task_summary',
            'provider_region_summary',
            'provider_zip_summary'
        ]
        
        for table in summary_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✅ {table}: {count} rows")
            except Exception as e:
                print(f"  ❌ {table}: Error - {e}")
        
        # Check base tables
        print("\n👥 CORE TABLES:")
        core_tables = ['users', 'providers', 'coordinators', 'patients', 'regions', 'patient_assignments']
        
        for table in core_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✅ {table}: {count} records")
            except Exception as e:
                print(f"  ❌ {table}: Error - {e}")
                
    finally:
        conn.close()

if __name__ == "__main__":
    check_database_status()