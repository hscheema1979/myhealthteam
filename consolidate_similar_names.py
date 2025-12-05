#!/usr/bin/env python3
"""
CONSOLIDATE SIMILAR NAMES - Fix Andrew Szalas variations
"""

import sqlite3

def consolidate_similar_names():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print("CONSOLIDATING SIMILAR NAMES")
    print("=" * 50)
    
    # Fix Andrew Szalas variations
    print("Looking for Andrew Szalas variations...")
    cursor.execute("""
        SELECT DISTINCT coordinator_id 
        FROM coordinator_tasks_2025_11 
        WHERE coordinator_id LIKE '%Szalas%' OR coordinator_id LIKE '%Andrew%'
    """)
    szalas_names = cursor.fetchall()
    
    print("Found Andrew Szalas variations:")
    for row in szalas_names:
        name = row[0]
        cursor.execute("SELECT COUNT(*) FROM coordinator_tasks_2025_11 WHERE coordinator_id = ?", (name,))
        count = cursor.fetchone()[0]
        print(f"  - {name}: {count} tasks")
    
    # Consolidate to "Szalas NP, Andrew" (the proper format)
    print("\nConsolidating to 'Szalas NP, Andrew'...")
    cursor.execute("""
        UPDATE coordinator_tasks_2025_11 
        SET coordinator_id = 'Szalas NP, Andrew' 
        WHERE coordinator_id = 'Szalas, Andrew'
    """)
    
    updated = cursor.rowcount
    if updated > 0:
        print(f"✅ Updated {updated} records: 'Szalas, Andrew' -> 'Szalas NP, Andrew'")
    else:
        print("✅ No consolidation needed")
    
    # Check if similar issue exists in other months
    months = ['2025_09', '2025_10']
    for month in months:
        print(f"\nChecking {month} for similar issues...")
        cursor.execute(f"""
            SELECT DISTINCT coordinator_id 
            FROM coordinator_tasks_{month} 
            WHERE coordinator_id LIKE '%Szalas%'
        """)
        szalas_names = cursor.fetchall()
        
        if len(szalas_names) > 1:
            print(f"  ⚠️  Found {len(szalas_names)} variations in {month}:")
            for row in szalas_names:
                name = row[0]
                cursor.execute(f"SELECT COUNT(*) FROM coordinator_tasks_{month} WHERE coordinator_id = ?", (name,))
                count = cursor.fetchone()[0]
                print(f"    - {name}: {count} tasks")
        else:
            print(f"  ✅ No variations found in {month}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    consolidate_similar_names()