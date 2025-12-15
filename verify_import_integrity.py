
import sqlite3
import pandas as pd
import glob
import os
import re
from datetime import datetime

DB_PATH = 'production.db'
CSV_DIR = 'downloads'

def get_db():
    return sqlite3.connect(DB_PATH)

def parse_date(date_str):
    if pd.isna(date_str): return None
    date_str = str(date_str).strip()
    if not date_str: return None
    formats = ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%m/%d/%y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def verify_db_dates(conn):
    print("\n--- Verifying Database Partition Dates ---")
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE 'provider_tasks_%' OR name LIKE 'coordinator_tasks_%') AND name NOT LIKE '%backup%' AND name NOT LIKE '%old%' ORDER BY name").fetchall()
    
    issues = 0
    for (tname,) in tables:
        # Expected Month
        parts = tname.split('_')
        if len(parts) < 4: continue # skip weird names
        try:
            exp_year = int(parts[2])
            exp_month = int(parts[3])
        except ValueError:
            continue # Skip tables like provider_tasks_backup
        
        # Check Date Range
        rows = conn.execute(f"SELECT min(task_date), max(task_date), count(*) FROM {tname}").fetchone()
        min_date, max_date, count = rows
        
        if count == 0:
            # print(f"{tname}: Empty")
            continue
            
        # Parse DB dates (YYYY-MM-DD)
        try:
            min_dt = datetime.strptime(min_date, '%Y-%m-%d')
            max_dt = datetime.strptime(max_date, '%Y-%m-%d')
            
            if (min_dt.year != exp_year or min_dt.month != exp_month) or \
               (max_dt.year != exp_year or max_dt.month != exp_month):
                print(f"❌ {tname}: DATE MISMATCH! Expected {exp_year}-{exp_month:02d}. Found range {min_date} to {max_date}")
                issues += 1
            else:
                # print(f"✅ {tname}: OK ({count} rows, {min_date} to {max_date})")
                pass
        except Exception as e:
            print(f"⚠️ {tname}: Error parsing dates: {e}. Values: {min_date}, {max_date}")
            issues += 1
            
    if issues == 0:
        print("✅ All populated tables contain only dates matching their partition month.")
    else:
        print(f"❌ Found {issues} tables with date mismatches.")

def verify_counts_vs_csv(conn):
    print("\n--- Verifying Counts vs CSV Source ---")
    
    # helper
    def get_source_counts(pattern, type_label):
        files = glob.glob(os.path.join(CSV_DIR, pattern))
        counts = {} # "YYYY_MM" -> count
        
        print(f"Scanning {len(files)} {type_label} CSVs...")
        for f in files:
            try:
                df = pd.read_csv(f, encoding='utf-8', on_bad_lines='skip')
                
                # Determine columns
                col_date = 'DOS' if 'PSL' in f else 'Date Only'
                col_pt = 'Patient Last, First DOB' if 'PSL' in f else 'Pt Name'
                
                if col_date not in df.columns: continue
                
                for _, row in df.iterrows():
                    # Apply STRICT filtering logic from transform script
                    pt_val = str(row.get(col_pt, '')).strip()
                    prov_val = str(row.get('Provider', '')).strip() if 'RVZ' in f else "ignore"
                    
                    if 'RVZ' in f:
                        if not pt_val or not prov_val or "Place holder" in pt_val or "Last, First DOB" in pt_val:
                            continue
                    else:
                        # PSL logic was loose? No, let's match logic: 
                        # process_psl checks parse_date.
                        pass

                    dt = parse_date(row.get(col_date))
                    if dt:
                        key = f"{dt.year}_{str(dt.month).zfill(2)}"
                        counts[key] = counts.get(key, 0) + 1
            except Exception as e:
                print(f"Error reading {os.path.basename(f)}: {e}")
        return counts

    psl_csv_counts = get_source_counts("PSL_ZEN-*.csv", "PSL")
    rvz_csv_counts = get_source_counts("RVZ_ZEN-*.csv", "RVZ")
    cmlog_csv_counts = get_source_counts("CMLog_*.csv", "CMLog")
    
    # Merge RVZ and CMLog counts for Coordinator Tasks comparison
    coord_csv_counts = {}
    all_coord_months = set(rvz_csv_counts.keys()) | set(cmlog_csv_counts.keys())
    for m in all_coord_months:
        coord_csv_counts[m] = rvz_csv_counts.get(m, 0) + cmlog_csv_counts.get(m, 0)
    
    # DB Counts
    print("\nComparing Counts (CSV vs DB):")
    print(f"{'Month':<10} | {'Type':<12} | {'CSV':<8} | {'DB':<8} | {'Diff':<5}")
    print("-" * 55)
    
    # Get all months
    all_months = sorted(list(set(psl_csv_counts.keys()) | set(coord_csv_counts.keys())))
    
    total_diff = 0
    
    for m in all_months:
        # PSL
        csv_n = psl_csv_counts.get(m, 0)
        tname = f"provider_tasks_{m}"
        try:
            db_n = conn.execute(f"SELECT count(*) FROM {tname}").fetchone()[0]
        except:
            db_n = 0
        
        diff = db_n - csv_n
        if diff != 0: total_diff += abs(diff)
        status = "✅" if diff == 0 else f"❌ {diff}"
        if csv_n > 0 or db_n > 0:
            print(f"{m:<10} | Prov (PSL)   | {csv_n:<8} | {db_n:<8} | {status}")

        # Coordinator (RVZ + CMLog)
        csv_n = coord_csv_counts.get(m, 0)
        tname = f"coordinator_tasks_{m}"
        try:
            db_n = conn.execute(f"SELECT count(*) FROM {tname}").fetchone()[0]
        except:
            db_n = 0
        
        diff = db_n - csv_n
        if diff != 0: total_diff += abs(diff)
        status = "✅" if diff == 0 else f"❌ {diff}"
        if csv_n > 0 or db_n > 0:
            print(f"{m:<10} | Coord (All)  | {csv_n:<8} | {db_n:<8} | {status}")

    if total_diff == 0:
        print("\n✅ Perfect Match! DB counts align exactly with CSV source logic.")
    else:
        print(f"\n⚠️ Total Discrepancy: {total_diff} rows. (Minor diffs might be due to parsing edge cases).")

if __name__ == "__main__":
    conn = get_db()
    verify_db_dates(conn)
    verify_counts_vs_csv(conn)
    conn.close()
