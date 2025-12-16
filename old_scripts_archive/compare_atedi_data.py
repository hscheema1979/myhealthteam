
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = 'production.db'
RAW_CSV = 'downloads/CMLog_AteDi000.csv'
MONTHLY_OCT = 'downloads/monthly_CM/coordinator_tasks_2025_10.csv'
MONTHLY_SEP = 'downloads/monthly_CM/coordinator_tasks_2025_09.csv'
USER_ID = 47 # AteDi
USER_NAME = 'AteDi000'

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

def analyze_raw():
    print(f"--- Raw: {RAW_CSV} ---")
    try:
        df = pd.read_csv(RAW_CSV, encoding='utf-8', on_bad_lines='skip')
        col_date = 'Date Only'
        # Filter for Sept and Oct 2025
        count_sep = 0
        count_oct = 0
        
        for _, row in df.iterrows():
            # Strict Filter
            pt = str(row.get('Pt Name','')).strip()
            if not pt or "Place holder" in pt: continue
            
            dt = parse_date(row.get(col_date))
            if not dt: continue
            
            if dt.year == 2025:
                if dt.month == 9: count_sep += 1
                if dt.month == 10: count_oct += 1
        
        print(f"Sept 2025: {count_sep}")
        print(f"Oct 2025:  {count_oct}")
        return count_sep, count_oct
    except Exception as e:
        print(f"Error: {e}")
        return 0, 0

def analyze_monthly(path, label):
    print(f"--- Monthly ({label}): {path} ---")
    try:
        df = pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
        # Filter for Staff = AteDi000
        # Check cols: 'Staff'
        # And check Date match (does file contain cross-month data?)
        
        count_target_user = 0
        dates_in_file = set()
        
        for _, row in df.iterrows():
            staff = str(row.get('Staff','')).strip()
            if staff != USER_NAME: continue
            
            dt = parse_date(row.get('Date Only'))
            if dt: dates_in_file.add(f"{dt.year}-{dt.month}")
            
            count_target_user += 1
            
        print(f"Total Rows for {USER_NAME}: {count_target_user}")
        print(f"Dates found in file: {sorted(list(dates_in_file))}")
        return count_target_user
    except Exception as e:
        print(f"Error: {e}")
        return 0

def analyze_db():
    print(f"--- Database (User ID {USER_ID}) ---")
    conn = sqlite3.connect(DB_PATH)
    
    # Sept
    try:
        cur = conn.execute(f"SELECT count(*) FROM coordinator_tasks_2025_09 WHERE coordinator_id={USER_ID}")
        c_sep = cur.fetchone()[0]
    except: c_sep = 0
    
    # Oct
    try:
        cur = conn.execute(f"SELECT count(*) FROM coordinator_tasks_2025_10 WHERE coordinator_id={USER_ID}")
        c_oct = cur.fetchone()[0]
    except: c_oct = 0
    
    conn.close()
    
    print(f"Sept 2025: {c_sep}")
    print(f"Oct 2025:  {c_oct}")
    return c_sep, c_oct

if __name__ == "__main__":
    rs, ro = analyze_raw()
    
    print("\n")
    ms = analyze_monthly(MONTHLY_SEP, "Sep CSV")
    mo = analyze_monthly(MONTHLY_OCT, "Oct CSV")
    
    print("\n")
    ds, do = analyze_db()
    
    print("\n=== SUMMARY ===")
    print(f"{'Source':<15} | {'Sept 25':<8} | {'Oct 25':<8}")
    print("-" * 40)
    print(f"{'Raw CMLog':<15} | {rs:<8} | {ro:<8}")
    print(f"{'Monthly CSV':<15} | {ms:<8} | {mo:<8}")
    print(f"{'Production DB':<15} | {ds:<8} | {do:<8}")
