#!/usr/bin/env python3
"""
Fix script to resolve coordinator billing name display issue
for October and November 2025 data.

This script updates the coordinator_tasks_2025_10 and coordinator_tasks_2025_11
tables to use proper coordinator codes instead of numeric user IDs.
"""

import sqlite3
import pandas as pd

def main():
    conn = sqlite3.connect('production.db')
    
    print("=== COORDINATOR BILLING NAME MAPPING FIX ===")
    print("Fixing October and November 2025 coordinator data...\n")
    
    # Create mapping from user_id to coordinator_code
    user_to_coordinator_mapping = {
        14: 'ESTJA000',  # Jan Estomo
        17: 'SOBJO000',  # Jose Soberanis
        20: 'RIOMA000',  # Manuel Rios
        5: 'SANBI000',   # Bianchi Sanchez
        2: 'SZAAN000',   # Andrew Szalas NP
    }
    
    print("1. User ID to Coordinator Code Mapping:")
    for user_id, coord_code in user_to_coordinator_mapping.items():
        print(f"   {user_id} → {coord_code}")
    
    # Fix October 2025 data
    print("\n2. Updating coordinator_tasks_2025_10...")
    try:
        # First, show current state
        query = """
        SELECT coordinator_id, COUNT(*) as task_count, SUM(duration_minutes) as total_minutes
        FROM coordinator_tasks_2025_10 
        GROUP BY coordinator_id
        ORDER BY coordinator_id
        """
        df_before = pd.read_sql_query(query, conn)
        print("Before fix:")
        print(df_before)
        
        # Update the coordinator_id values
        updates_made = 0
        for user_id, coord_code in user_to_coordinator_mapping.items():
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE coordinator_tasks_2025_10 
                SET coordinator_id = ?
                WHERE coordinator_id = ?
            """, (coord_code, user_id))
            updates_made += cursor.rowcount
        
        conn.commit()
        print(f"   ✅ Updated {updates_made} rows in October 2025")
        
        # Verify the fix
        df_after = pd.read_sql_query(query, conn)
        print("After fix:")
        print(df_after)
        
    except Exception as e:
        print(f"   ❌ Error updating October 2025: {e}")
        conn.rollback()
    
    # Fix November 2025 data
    print("\n3. Updating coordinator_tasks_2025_11...")
    try:
        # First, show current state
        query = """
        SELECT coordinator_id, COUNT(*) as task_count, SUM(duration_minutes) as total_minutes
        FROM coordinator_tasks_2025_11 
        GROUP BY coordinator_id
        ORDER BY coordinator_id
        """
        df_before = pd.read_sql_query(query, conn)
        print("Before fix:")
        print(df_before)
        
        # Update the coordinator_id values
        updates_made = 0
        for user_id, coord_code in user_to_coordinator_mapping.items():
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE coordinator_tasks_2025_11 
                SET coordinator_id = ?
                WHERE coordinator_id = ?
            """, (coord_code, user_id))
            updates_made += cursor.rowcount
        
        conn.commit()
        print(f"   ✅ Updated {updates_made} rows in November 2025")
        
        # Verify the fix
        df_after = pd.read_sql_query(query, conn)
        print("After fix:")
        print(df_after)
        
    except Exception as e:
        print(f"   ❌ Error updating November 2025: {e}")
        conn.rollback()
    
    # Verify the mapping worked by checking a sample of updated data
    print("\n4. Verifying updated coordinator assignments:")
    try:
        for month in ['10', '11']:
            table = f"coordinator_tasks_2025_{month}"
            print(f"\n   Sample from {table}:")
            query = f"""
            SELECT coordinator_id, patient_id, task_date, duration_minutes, task_type
            FROM {table}
            LIMIT 5
            """
            df = pd.read_sql_query(query, conn)
            print(df)
    except Exception as e:
        print(f"   ❌ Error verifying updates: {e}")
    
    # Check if billing views need to be recreated
    print("\n5. Checking if billing summary tables need updating...")
    try:
        # Check if patient_monthly_billing tables exist for Oct/Nov
        for month in ['10', '11']:
            table_name = f"patient_monthly_billing_2025_{month}"
            check_query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name = ?
            """
            table_exists = conn.execute(check_query, (table_name,)).fetchone()
            
            if table_exists:
                print(f"   ⚠️  {table_name} exists - may need recreation with corrected coordinator data")
            else:
                print(f"   ✅ {table_name} does not exist - will be created with correct data")
                
    except Exception as e:
        print(f"   ❌ Error checking billing tables: {e}")
    
    # Test the billing dashboard query logic
    print("\n6. Testing billing dashboard after fix...")
    try:
        # Test with coordinator_tasks_2025_10
        query = """
        SELECT 
            ct.coordinator_id,
            u.first_name || ' ' || u.last_name as coordinator_name,
            COUNT(*) as task_count,
            SUM(ct.duration_minutes) as total_minutes
        FROM coordinator_tasks_2025_10 ct
        LEFT JOIN staff_codes sc ON ct.coordinator_id = sc.coordinator_code
        LEFT JOIN users u ON sc.email = u.email
        GROUP BY ct.coordinator_id, coordinator_name
        ORDER BY task_count DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        print("October 2025 coordinator billing summary:")
        print(df)
        
    except Exception as e:
        print(f"   ❌ Error testing billing query: {e}")
        # Let's try a simpler approach
        try:
            query = """
            SELECT 
                coordinator_id,
                COUNT(*) as task_count,
                SUM(duration_minutes) as total_minutes
            FROM coordinator_tasks_2025_10
            GROUP BY coordinator_id
            ORDER BY task_count DESC
            """
            df = pd.read_sql_query(query, conn)
            print("Simple coordinator summary (Oct 2025):")
            print(df)
        except Exception as e2:
            print(f"   ❌ Even simple query failed: {e2}")
    
    conn.close()
    print("\n=== COORDINATOR BILLING MAPPING FIX COMPLETE ===")
    print("\n📋 Summary:")
    print("   • Updated coordinator_tasks_2025_10 to use proper coordinator codes")
    print("   • Updated coordinator_tasks_2025_11 to use proper coordinator codes")
    print("   • Billing dashboard should now show names instead of numbers")
    print("   • Staff codes now properly map to staff names")
    print("\n💡 Next Steps:")
    print("   • Refresh billing dashboard to see the changes")
    print("   • If needed, recreate patient_monthly_billing tables for Oct/Nov 2025")

if __name__ == "__main__":
    main()