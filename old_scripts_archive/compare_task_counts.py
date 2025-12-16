#!/usr/bin/env python3
"""
Compare task counts between CSV files and database
"""

import pandas as pd
import sqlite3
import os
import glob

def compare_task_counts():
    print("COMPARING TASK COUNTS: CSV FILES vs DATABASE")
    print("=" * 70)
    
    # First, get counts from CSV files
    csv_dir = 'downloads'
    if not os.path.exists(csv_dir):
        print(f"ERROR: {csv_dir} directory not found")
        return
    
    conn = sqlite3.connect('production.db')
    
    # ===== CSV FILE COUNTS =====
    print("\n1. CSV FILE COUNTS:")
    
    # PSL files (provider tasks)
    psl_files = glob.glob(os.path.join(csv_dir, "PSL_ZEN-*.csv"))
    csv_psl_total = 0
    csv_psl_by_file = {}
    
    for psl_file in psl_files:
        try:
            df = pd.read_csv(psl_file, encoding="utf-8", on_bad_lines="skip")
            count = len(df)
            csv_psl_total += count
            csv_psl_by_file[os.path.basename(psl_file)] = count
        except Exception as e:
            print(f"  ERROR reading {psl_file}: {e}")
            csv_psl_by_file[os.path.basename(psl_file)] = 0
    
    print(f"\nPSL Files (Provider Tasks): {len(psl_files)} files")
    for filename, count in sorted(csv_psl_by_file.items()):
        print(f"  {filename}: {count:,} rows")
    print(f"  PSL TOTAL: {csv_psl_total:,} rows")
    
    # RVZ files (coordinator tasks)
    rvz_files = glob.glob(os.path.join(csv_dir, "RVZ_ZEN-*.csv"))
    csv_rvz_total = 0
    csv_rvz_by_file = {}
    
    for rvz_file in rvz_files:
        try:
            df = pd.read_csv(rvz_file, encoding="utf-8", on_bad_lines="skip")
            count = len(df)
            csv_rvz_total += count
            csv_rvz_by_file[os.path.basename(rvz_file)] = count
        except Exception as e:
            print(f"  ERROR reading {rvz_file}: {e}")
            csv_rvz_by_file[os.path.basename(rvz_file)] = 0
    
    print(f"\nRVZ Files (Coordinator Tasks): {len(rvz_files)} files")
    for filename, count in sorted(csv_rvz_by_file.items()):
        print(f"  {filename}: {count:,} rows")
    print(f"  RVZ TOTAL: {csv_rvz_total:,} rows")
    
    # CMLog files (coordinator tasks)
    cmlog_files = glob.glob(os.path.join(csv_dir, "CMLog_*.csv"))
    csv_cmlog_total = 0
    csv_cmlog_by_file = {}
    
    for cmlog_file in cmlog_files:
        try:
            df = pd.read_csv(cmlog_file, encoding="utf-8", on_bad_lines="skip")
            count = len(df)
            csv_cmlog_total += count
            csv_cmlog_by_file[os.path.basename(cmlog_file)] = count
        except Exception as e:
            print(f"  ERROR reading {cmlog_file}: {e}")
            csv_cmlog_by_file[os.path.basename(cmlog_file)] = 0
    
    print(f"\nCMLog Files (Coordinator Tasks): {len(cmlog_files)} files")
    for filename, count in sorted(csv_cmlog_by_file.items()):
        print(f"  {filename}: {count:,} rows")
    print(f"  CMLog TOTAL: {csv_cmlog_total:,} rows")
    
    csv_total_all = csv_psl_total + csv_rvz_total + csv_cmlog_total
    print(f"\nCSV GRAND TOTAL: {csv_total_all:,} rows")
    
    # ===== DATABASE COUNTS =====
    print("\n2. DATABASE COUNTS:")
    
    # Provider tasks in database
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'provider_tasks_%'
    """)
    provider_tables = [row[0] for row in cursor.fetchall()]
    
    db_psl_total = 0
    db_psl_by_table = {}
    
    for table_name in provider_tables:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        db_psl_total += count
        db_psl_by_table[table_name] = count
    
    print(f"\nDatabase Provider Tasks: {len(provider_tables)} tables")
    # Show top 10 tables by count
    sorted_tables = sorted(db_psl_by_table.items(), key=lambda x: x[1], reverse=True)[:10]
    for table_name, count in sorted_tables:
        print(f"  {table_name}: {count:,} rows")
    if len(provider_tables) > 10:
        print(f"  ... and {len(provider_tables) - 10} more tables")
    print(f"  DB PROVIDER TOTAL: {db_psl_total:,} rows")
    
    # Coordinator tasks in database
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'coordinator_tasks_%'
    """)
    coordinator_tables = [row[0] for row in cursor.fetchall()]
    
    db_rvz_total = 0
    db_rvz_by_table = {}
    
    for table_name in coordinator_tables:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        db_rvz_total += count
        db_rvz_by_table[table_name] = count
    
    print(f"\nDatabase Coordinator Tasks: {len(coordinator_tables)} tables")
    # Show top 10 tables by count
    sorted_tables = sorted(db_rvz_by_table.items(), key=lambda x: x[1], reverse=True)[:10]
    for table_name, count in sorted_tables:
        print(f"  {table_name}: {count:,} rows")
    if len(coordinator_tables) > 10:
        print(f"  ... and {len(coordinator_tables) - 10} more tables")
    print(f"  DB COORDINATOR TOTAL: {db_rvz_total:,} rows")
    
    db_total_all = db_psl_total + db_rvz_total
    print(f"\nDB GRAND TOTAL: {db_total_all:,} rows")
    
    # ===== COMPARISON =====
    print("\n3. COMPARISON:")
    print(f"Provider Tasks - CSV: {csv_psl_total:,} vs DB: {db_psl_total:,}")
    print(f"Coordinator Tasks - CSV: {csv_rvz_total + csv_cmlog_total:,} vs DB: {db_rvz_total:,}")
    print(f"TOTAL - CSV: {csv_total_all:,} vs DB: {db_total_all:,}")
    
    # Calculate differences
    psl_diff = db_psl_total - csv_psl_total
    coord_diff = db_rvz_total - (csv_rvz_total + csv_cmlog_total)
    total_diff = db_total_all - csv_total_all
    
    print(f"\nDifferences:")
    print(f"Provider tasks: {psl_diff:+,} rows ({psl_diff/csv_psl_total*100:.1f}% change)" if csv_psl_total > 0 else "Provider tasks: N/A (no CSV data)")
    print(f"Coordinator tasks: {coord_diff:+,} rows ({coord_diff/(csv_rvz_total + csv_cmlog_total)*100:.1f}% change)" if (csv_rvz_total + csv_cmlog_total) > 0 else "Coordinator tasks: N/A (no CSV data)")
    print(f"TOTAL: {total_diff:+,} rows ({total_diff/csv_total_all*100:.1f}% change)" if csv_total_all > 0 else "TOTAL: N/A (no CSV data)")
    
    # Show some examples of the data format
    print(f"\n4. DATA FORMAT EXAMPLES:")
    
    # Get a few sample patient names from each file type
    psl_examples = []
    rvz_examples = []
    cmlog_examples = []
    
    if psl_files:
        try:
            df = pd.read_csv(psl_files[0], encoding="utf-8", on_bad_lines="skip")
            if len(df) > 0 and 'patient' in df.columns:
                psl_examples = df['patient'].dropna().head(3).tolist()
        except:
            pass
    
    if rvz_files:
        try:
            df = pd.read_csv(rvz_files[0], encoding="utf-8", on_bad_lines="skip")
            if len(df) > 0 and 'patient' in df.columns:
                rvz_examples = df['patient'].dropna().head(3).tolist()
        except:
            pass
    
    if cmlog_files:
        try:
            df = pd.read_csv(cmlog_files[0], encoding="utf-8", on_bad_lines="skip")
            if len(df) > 0 and 'patient' in df.columns:
                cmlog_examples = df['patient'].dropna().head(3).tolist()
        except:
            pass
    
    print(f"Provider task patient format: {psl_examples[0] if psl_examples else 'N/A'}")
    print(f"RVZ coordinator task patient format: {rvz_examples[0] if rvz_examples else 'N/A'}")
    print(f"CMLog coordinator task patient format: {cmlog_examples[0] if cmlog_examples else 'N/A'}")
    
    conn.close()

if __name__ == "__main__":
    compare_task_counts()