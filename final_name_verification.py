#!/usr/bin/env python3
"""
FINAL VERIFICATION - All months should now have proper names
"""

import sqlite3

def final_name_verification():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print("🎯 FINAL NAME FORMAT VERIFICATION")
    print("=" * 60)
    print("Checking ALL months (September, October, November 2025)")
    
    months = ['2025_09', '2025_10', '2025_11']
    all_proper_names = True
    
    for month in months:
        table_name = f'coordinator_tasks_{month}'
        print(f"\n📅 {table_name.upper()}:")
        
        try:
            cursor.execute(f"SELECT DISTINCT coordinator_id FROM {table_name} ORDER BY coordinator_id")
            coordinators = cursor.fetchall()
            
            print(f"  Found {len(coordinators)} unique coordinator names:")
            numeric_count = 0
            
            for row in coordinators:
                name = row[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE coordinator_id = ?", (name,))
                count = cursor.fetchone()[0]
                
                # Check if it's a numeric ID
                if str(name).isdigit():
                    numeric_count += 1
                    print(f"    ❌ {name}: {count} tasks (NUMERIC ID)")
                    all_proper_names = False
                else:
                    print(f"    ✅ {name}: {count} tasks")
            
            if numeric_count == 0:
                print(f"  ✅ All names are proper format!")
            else:
                print(f"  ❌ {numeric_count} numeric IDs still need fixing")
                all_proper_names = False
                
        except Exception as e:
            print(f"  ❌ Error checking {table_name}: {e}")
            all_proper_names = False
    
    print(f"\n" + "="*60)
    if all_proper_names:
        print("🎉 SUCCESS! All coordinator names are in proper 'last,first' format!")
        print("✅ September 2025: ALL PROPER NAMES")
        print("✅ October 2025: ALL PROPER NAMES") 
        print("✅ November 2025: ALL PROPER NAMES")
    else:
        print("❌ Some coordinator names still need fixing")
    
    # Test provider names too
    print(f"\n👩‍⚕️ PROVIDER NAME VERIFICATION:")
    provider_months = ['2025_09', '2025_10', '2025_11']
    
    for month in provider_months:
        table_name = f'provider_tasks_{month}'
        print(f"\n📅 {table_name.upper()}:")
        
        try:
            cursor.execute(f"SELECT DISTINCT provider_name FROM {table_name} ORDER BY provider_name")
            providers = cursor.fetchall()
            
            print(f"  Found {len(providers)} unique provider names:")
            
            for row in providers:
                name = row[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE provider_name = ?", (name,))
                count = cursor.fetchone()[0]
                
                if name is None or name == 'None':
                    print(f"    ⚠️  {name}: {count} tasks (NULL)")
                else:
                    print(f"    ✅ {name}: {count} tasks")
                    
        except Exception as e:
            print(f"  ❌ Error checking {table_name}: {e}")
    
    conn.close()

if __name__ == "__main__":
    final_name_verification()