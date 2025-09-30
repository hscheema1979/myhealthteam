import pandas as pd
import sqlite3
import os
from datetime import datetime
from collections import defaultdict

def compare_csv_vs_database():
    """
    Compare staff codes and task dates between CSV files and existing database tables
    to identify potential duplicates and overlaps before importing.
    """
    
    print("=== CSV vs DATABASE OVERLAP ANALYSIS ===")
    print(f"Analysis started at: {datetime.now()}")
    print()
    
    conn = sqlite3.connect('production.db')
    
    # ===== COORDINATOR DATA COMPARISON =====
    print("=" * 60)
    print("COORDINATOR DATA ANALYSIS")
    print("=" * 60)
    
    # Get existing coordinator data from database
    print("Analyzing existing SOURCE_COORDINATOR_TASKS_HISTORY...")
    db_coord_query = """
        SELECT 
            "Staff" as staff_code,
            "Date Only" as task_date,
            COUNT(*) as record_count
        FROM SOURCE_COORDINATOR_TASKS_HISTORY 
        WHERE "Staff" IS NOT NULL AND "Date Only" IS NOT NULL
        GROUP BY "Staff", "Date Only"
        ORDER BY "Staff", "Date Only"
    """
    
    db_coord_df = pd.read_sql_query(db_coord_query, conn)
    print(f"Database coordinator records: {len(db_coord_df)} unique staff-date combinations")
    
    # Group by staff for summary
    db_coord_summary = db_coord_df.groupby('staff_code').agg({
        'task_date': ['min', 'max', 'count'],
        'record_count': 'sum'
    }).round(0)
    
    db_coord_summary.columns = ['earliest_date', 'latest_date', 'unique_dates', 'total_records']
    print("Database coordinator summary by staff:")
    print(db_coord_summary.to_string())
    print()
    
    # Analyze CSV coordinator files
    print("📁 Analyzing CSV coordinator files...")
    csv_coord_data = defaultdict(list)
    csv_coord_summary = {}
    
    cmlog_files = [f for f in os.listdir('downloads/coordinators') if f.endswith('.csv')]
    
    for file in sorted(cmlog_files):
        staff_code = file.replace('CMLog_', '').replace('.csv', '')
        print(f"  Processing {file} (Staff: {staff_code})...")
        
        try:
            df = pd.read_csv(f'downloads/coordinators/{file}')
            
            # Filter valid data
            valid_mask = (
                df['Staff'].notna() & 
                (df['Staff'] != 'Staff') & 
                (~df['Staff'].str.contains('Aaa', na=False, case=False))
            )
            valid_data = df[valid_mask].copy()
            
            if len(valid_data) > 0:
                # Parse dates
                valid_data['parsed_date'] = pd.to_datetime(valid_data['Date Only'], errors='coerce')
                date_data = valid_data[valid_data['parsed_date'].notna()]
                
                if len(date_data) > 0:
                    # Group by date
                    date_counts = date_data.groupby('Date Only').size()
                    
                    csv_coord_summary[staff_code] = {
                        'earliest_date': date_data['Date Only'].min(),
                        'latest_date': date_data['Date Only'].max(), 
                        'unique_dates': len(date_counts),
                        'total_records': len(date_data),
                        'date_range': f"{date_data['parsed_date'].min().strftime('%Y-%m-%d')} to {date_data['parsed_date'].max().strftime('%Y-%m-%d')}"
                    }
                    
                    # Store detailed date data for overlap analysis
                    for date_str, count in date_counts.items():
                        csv_coord_data[staff_code].append((date_str, count))
                        
                    print(f"    ✓ {len(date_data)} records, {len(date_counts)} unique dates")
                else:
                    print(f"    ⚠ No valid dates found")
            else:
                print(f"    ⚠ No valid records found")
                
        except Exception as e:
            print(f"    ✗ Error processing {file}: {e}")
    
    print()
    print("CSV coordinator summary:")
    csv_coord_df = pd.DataFrame(csv_coord_summary).T
    if not csv_coord_df.empty:
        print(csv_coord_df.to_string())
    else:
        print("No valid CSV coordinator data found")
    
    # ===== OVERLAP ANALYSIS - COORDINATORS =====
    print()
    print("🔍 COORDINATOR OVERLAP ANALYSIS:")
    
    if not csv_coord_df.empty and not db_coord_df.empty:
        for staff_code in csv_coord_summary.keys():
            print(f"\nStaff: {staff_code}")
            
            # Check if staff exists in database
            staff_db_data = db_coord_df[db_coord_df['staff_code'] == staff_code]
            
            if len(staff_db_data) > 0:
                print(f"  ✓ Staff exists in database with {len(staff_db_data)} unique dates")
                print(f"    DB date range: {staff_db_data['task_date'].min()} to {staff_db_data['task_date'].max()}")
                print(f"    CSV date range: {csv_coord_summary[staff_code]['date_range']}")
                
                # Check for exact date overlaps
                db_dates = set(staff_db_data['task_date'].tolist())
                csv_dates = set([date for date, count in csv_coord_data[staff_code]])
                
                overlapping_dates = db_dates.intersection(csv_dates)
                if overlapping_dates:
                    print(f"    ⚠ OVERLAP WARNING: {len(overlapping_dates)} dates appear in both DB and CSV")
                    if len(overlapping_dates) <= 10:
                        print(f"      Overlapping dates: {sorted(list(overlapping_dates))}")
                    else:
                        print(f"      Sample overlapping dates: {sorted(list(overlapping_dates))[:10]}...")
                else:
                    print(f"    No date overlaps found")
            else:
                print(f"  Staff NOT in database - all CSV data is new")
    
    print()
    print("=" * 60)
    print("PROVIDER DATA ANALYSIS") 
    print("=" * 60)
    
    # Get existing provider data from database
    print("Analyzing existing SOURCE_PROVIDER_TASKS_HISTORY...")
    db_prov_query = """
        SELECT 
            "Prov" as provider_code,
            "DOS" as service_date,
            COUNT(*) as record_count
        FROM SOURCE_PROVIDER_TASKS_HISTORY 
        WHERE "Prov" IS NOT NULL AND "DOS" IS NOT NULL
        GROUP BY "Prov", "DOS"
        ORDER BY "Prov", "DOS"
    """
    
    db_prov_df = pd.read_sql_query(db_prov_query, conn)
    print(f"Database provider records: {len(db_prov_df)} unique provider-date combinations")
    
    # Group by provider for summary
    db_prov_summary = db_prov_df.groupby('provider_code').agg({
        'service_date': ['min', 'max', 'count'],
        'record_count': 'sum'
    }).round(0)
    
    db_prov_summary.columns = ['earliest_date', 'latest_date', 'unique_dates', 'total_records']
    print("Database provider summary by code:")
    print(db_prov_summary.to_string())
    print()
    
    # Analyze CSV provider files
    print("📁 Analyzing CSV provider files...")
    csv_prov_data = defaultdict(list)
    csv_prov_summary = {}
    
    psl_files = [f for f in os.listdir('downloads/providers') if f.endswith('.csv')]
    
    for file in sorted(psl_files):
        provider_code = file.replace('PSL_', '').replace('.csv', '')
        print(f"  Processing {file} (Provider: {provider_code})...")
        
        try:
            df = pd.read_csv(f'downloads/providers/{file}')
            
            # Filter valid data
            valid_mask = (
                df['Prov'].notna() & 
                (df['Prov'] != 'Prov') & 
                (~df['Prov'].str.contains('Aaa', na=False, case=False))
            )
            valid_data = df[valid_mask].copy()
            
            if len(valid_data) > 0:
                # Parse dates (DOS = Date of Service)
                valid_data['parsed_date'] = pd.to_datetime(valid_data['DOS'], errors='coerce')
                date_data = valid_data[valid_data['parsed_date'].notna()]
                
                if len(date_data) > 0:
                    # Group by date
                    date_counts = date_data.groupby('DOS').size()
                    
                    csv_prov_summary[provider_code] = {
                        'earliest_date': date_data['DOS'].min(),
                        'latest_date': date_data['DOS'].max(),
                        'unique_dates': len(date_counts),
                        'total_records': len(date_data),
                        'date_range': f"{date_data['parsed_date'].min().strftime('%Y-%m-%d')} to {date_data['parsed_date'].max().strftime('%Y-%m-%d')}"
                    }
                    
                    # Store detailed date data for overlap analysis
                    for date_str, count in date_counts.items():
                        csv_prov_data[provider_code].append((date_str, count))
                        
                    print(f"    ✓ {len(date_data)} records, {len(date_counts)} unique dates")
                else:
                    print(f"    ⚠ No valid dates found")
            else:
                print(f"    ⚠ No valid records found")
                
        except Exception as e:
            print(f"    ✗ Error processing {file}: {e}")
    
    print()
    print("CSV provider summary:")
    csv_prov_df = pd.DataFrame(csv_prov_summary).T
    if not csv_prov_df.empty:
        print(csv_prov_df.to_string())
    else:
        print("No valid CSV provider data found")
    
    # ===== OVERLAP ANALYSIS - PROVIDERS =====
    print()
    print("🔍 PROVIDER OVERLAP ANALYSIS:")
    
    if not csv_prov_df.empty and not db_prov_df.empty:
        for provider_code in csv_prov_summary.keys():
            print(f"\nProvider: {provider_code}")
            
            # Check if provider exists in database
            prov_db_data = db_prov_df[db_prov_df['provider_code'] == provider_code]
            
            if len(prov_db_data) > 0:
                print(f"  ✓ Provider exists in database with {len(prov_db_data)} unique dates")
                print(f"    DB date range: {prov_db_data['service_date'].min()} to {prov_db_data['service_date'].max()}")
                print(f"    CSV date range: {csv_prov_summary[provider_code]['date_range']}")
                
                # Check for exact date overlaps
                db_dates = set(prov_db_data['service_date'].tolist())
                csv_dates = set([date for date, count in csv_prov_data[provider_code]])
                
                overlapping_dates = db_dates.intersection(csv_dates)
                if overlapping_dates:
                    print(f"    ⚠ OVERLAP WARNING: {len(overlapping_dates)} dates appear in both DB and CSV")
                    if len(overlapping_dates) <= 10:
                        print(f"      Overlapping dates: {sorted(list(overlapping_dates))}")
                    else:
                        print(f"      Sample overlapping dates: {sorted(list(overlapping_dates))[:10]}...")
                else:
                    print(f"    No date overlaps found")
            else:
                print(f"  Provider NOT in database - all CSV data is new")
    
    # ===== FINAL SUMMARY =====
    print()
    print("=" * 60)
    print("IMPORT RECOMMENDATION SUMMARY")
    print("=" * 60)
    
    total_coord_overlaps = 0
    total_prov_overlaps = 0
    
    # Count coordinator overlaps
    if not csv_coord_df.empty and not db_coord_df.empty:
        for staff_code in csv_coord_summary.keys():
            staff_db_data = db_coord_df[db_coord_df['staff_code'] == staff_code]
            if len(staff_db_data) > 0:
                db_dates = set(staff_db_data['task_date'].tolist())
                csv_dates = set([date for date, count in csv_coord_data[staff_code]])
                overlaps = len(db_dates.intersection(csv_dates))
                if overlaps > 0:
                    total_coord_overlaps += overlaps
    
    # Count provider overlaps  
    if not csv_prov_df.empty and not db_prov_df.empty:
        for provider_code in csv_prov_summary.keys():
            prov_db_data = db_prov_df[db_prov_df['provider_code'] == provider_code]
            if len(prov_db_data) > 0:
                db_dates = set(prov_db_data['service_date'].tolist())
                csv_dates = set([date for date, count in csv_prov_data[provider_code]])
                overlaps = len(db_dates.intersection(csv_dates))
                if overlaps > 0:
                    total_prov_overlaps += overlaps
    
    print(f"COORDINATOR OVERLAPS: {total_coord_overlaps} date overlaps found")
    print(f"📊 PROVIDER OVERLAPS: {total_prov_overlaps} date overlaps found")
    print()
    
    if total_coord_overlaps > 0 or total_prov_overlaps > 0:
        print("⚠️  WARNING: Data overlaps detected!")
        print("   Importing in APPEND mode may create duplicates.")
        print("   Consider:")
        print("   1. Using date filters to import only newer data")
        print("   2. Using REPLACE mode to overwrite existing data")
        print("   3. Manual deduplication after import")
    else:
        print("✅ No overlaps detected - safe to proceed with APPEND mode")
    
    print()
    print(f"Analysis completed at: {datetime.now()}")
    
    conn.close()

if __name__ == "__main__":
    compare_csv_vs_database()