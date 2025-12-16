#!/usr/bin/env python3
"""
Thorough code review of the transform function to identify what we broke
"""

import sqlite3
import os

def thorough_review():
    print("THOROUGH CODE REVIEW - IDENTIFYING WHAT WE BROKE")
    print("=" * 60)
    
    conn = sqlite3.connect('production.db')
    
    # 1. Check what tables actually exist
    print("1. TABLE INVENTORY:")
    cursor = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    for name, sql in tables:
        if 'task' in name.lower():
            print(f"  {name}")
            # Check if table has data
            cursor = conn.execute(f"SELECT COUNT(*) FROM {name}")
            count = cursor.fetchone()[0]
            print(f"    Records: {count}")
            if count > 0:
                # Show sample data
                cursor = conn.execute(f"SELECT * FROM {name} LIMIT 3")
                samples = cursor.fetchall()
                for i, sample in enumerate(samples):
                    print(f"    Sample {i+1}: {sample}")
            print()
    
    # 2. Check PSL vs RVZ file processing
    print("2. FILE PROCESSING ANALYSIS:")
    
    # Check what files we should have vs what we processed
    csv_dir = 'downloads'
    if os.path.exists(csv_dir):
        psl_files = [f for f in os.listdir(csv_dir) if f.startswith('PSL_') and f.endswith('.csv')]
        rvz_files = [f for f in os.listdir(csv_dir) if f.startswith('RVZ_') and f.endswith('.csv')]
        cmlog_files = [f for f in os.listdir(csv_dir) if f.startswith('CMLog_') and f.endswith('.csv')]
        
        print(f"  PSL files found: {len(psl_files)}")
        for f in psl_files[:3]:  # Show first 3
            print(f"    {f}")
        
        print(f"  RVZ files found: {len(rvz_files)}")
        for f in rvz_files[:3]:  # Show first 3
            print(f"    {f}")
            
        print(f"  CMLog files found: {len(cmlog_files)}")
        for f in cmlog_files[:3]:  # Show first 3
            print(f"    {f}")
    
    # 3. Check the actual task data vs expected
    print("3. TASK DATA ANALYSIS:")
    
    # Check if we have any provider tasks at all
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'provider_tasks_%' 
        ORDER BY name
    """)
    prov_tables = cursor.fetchall()
    
    total_provider_tasks = 0
    for (table_name,) in prov_tables:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        total_provider_tasks += count
        if count > 0:
            print(f"  {table_name}: {count} records")
    
    print(f"\n  TOTAL PROVIDER TASKS: {total_provider_tasks}")
    
    # Check coordinator tasks
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'coordinator_tasks_%' 
        ORDER BY name
    """)
    coord_tables = cursor.fetchall()
    
    total_coordinator_tasks = 0
    for (table_name,) in coord_tables:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        total_coordinator_tasks += count
        if count > 0:
            print(f"  {table_name}: {count} records")
    
    print(f"\n  TOTAL COORDINATOR TASKS: {total_coordinator_tasks}")
    
    # 4. Check what went wrong with the last run
    print("4. PROBLEMS IDENTIFIED:")
    
    if total_provider_tasks == 0:
        print("  ❌ ZERO provider tasks - this is definitely broken")
        print("     Expected: Thousands of provider tasks from PSL files")
    
    if total_coordinator_tasks < 1000:  # Should be much higher
        print("  ❌ Very few coordinator tasks - likely missing data")
        print(f"     Current: {total_coordinator_tasks}")
        print("     Expected: 40,000+ coordinator tasks")
    
    # 5. Compare with what we should have
    print("5. EXPECTED vs ACTUAL:")
    print(f"  Provider tasks: 0 (actual) vs 33,000+ (expected from previous runs)")
    print(f"  Coordinator tasks: {total_coordinator_tasks} (actual) vs 400,000+ (expected)")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("CONCLUSION: We broke the task import while fixing provider assignments")
    print("The PSL file processing is not working - need to investigate process_psl()")
    print("=" * 60)

if __name__ == "__main__":
    thorough_review()