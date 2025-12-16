#!/usr/bin/env python3

import sqlite3
import sys

def main():
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        print("=== VALIDATING COORDINATOR BILLING FIX ===\n")
        
        # Check staff_code_mapping
        print("1. STAFF CODE MAPPING ENTRIES:")
        cursor.execute('SELECT staff_code, user_id, mapping_type FROM staff_code_mapping WHERE mapping_type = "COORDINATOR" ORDER BY staff_code')
        mappings = cursor.fetchall()
        print(f"   Found {len(mappings)} coordinator mappings:")
        for staff_code, user_id, mapping_type in mappings:
            print(f"   - {staff_code} -> User ID {user_id}")
        
        print("\n2. COORDINATOR_TASKS TABLES:")
        # Check what coordinator_tasks tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'coordinator_tasks_%' ORDER BY name")
        tables = cursor.fetchall()
        print(f"   Found {len(tables)} coordinator_tasks tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Check recent months for coordinators
        print("\n3. COORDINATORS IN RECENT MONTHS:")
        recent_months = ['2025_07', '2025_08', '2025_09', '2025_10', '2025_11', '2025_12']
        
        for month in recent_months:
            table_name = f'coordinator_tasks_{month}'
            try:
                cursor.execute(f'SELECT DISTINCT coordinator_name, coordinator_id, COUNT(*) as task_count FROM {table_name} GROUP BY coordinator_name, coordinator_id ORDER BY coordinator_name')
                coordinators = cursor.fetchall()
                print(f"\n   {month}: {len(coordinators)} coordinators, {sum(row[2] for row in coordinators)} total tasks")
                for name, co_id, count in coordinators:
                    print(f"   - {name} (ID: {co_id}) - {count} tasks")
                    
                # Check if Dianela appears
                dianela_found = any('Dianela' in str(row[0]) for row in coordinators)
                if dianela_found:
                    print(f"   ✅ DIANELA FOUND in {month}")
                else:
                    print(f"   ❌ DIANELA NOT FOUND in {month}")
                    
            except Exception as e:
                print(f"   {month}: Table error - {e}")
        
        # Check billing summary tables if they exist
        print("\n4. BILLING SUMMARY TABLES:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%billing%' ORDER BY name")
        billing_tables = cursor.fetchall()
        print(f"   Found {len(billing_tables)} billing tables:")
        for table in billing_tables:
            print(f"   - {table[0]}")
        
        # Check if monthly coordinator billing exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'monthly_coordinator_billing_%' ORDER BY name")
            monthly_tables = cursor.fetchall()
            if monthly_tables:
                print(f"\n   Monthly coordinator billing tables:")
                for table in monthly_tables:
                    print(f"   - {table[0]}")
                    
                    # Check coordinators in this table
                    table_name = table[0]
                    cursor.execute(f'SELECT DISTINCT coordinator_name, coordinator_id FROM {table_name} ORDER BY coordinator_name')
                    coordinators = cursor.fetchall()
                    print(f"     {len(coordinators)} coordinators:")
                    for name, co_id in coordinators:
                        print(f"     - {name} (ID: {co_id})")
        except Exception as e:
            print(f"   Error checking monthly billing: {e}")
        
        conn.close()
        print("\n=== VALIDATION COMPLETE ===")
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()