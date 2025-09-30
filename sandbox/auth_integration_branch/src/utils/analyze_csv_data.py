import pandas as pd
import sqlite3
import os
from datetime import datetime

def analyze_new_data():
    print("=== NEW DATA ANALYSIS ===\n")
    
    # Connect to database
    conn = sqlite3.connect('production.db')
    
    # Get existing data cutoff dates
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(task_date) FROM coordinator_tasks WHERE task_date LIKE '%/%/%'")
    max_coord_date = cursor.fetchone()[0]
    cursor.execute("SELECT MAX(task_date) FROM provider_tasks")  
    max_prov_date = cursor.fetchone()[0]
    
    print(f"Latest coordinator task date in DB: {max_coord_date}")
    print(f"Latest provider task date in DB: {max_prov_date}")
    print()
    
    # Analyze CMLog files
    print("=== COORDINATOR DATA (CMLog) ANALYSIS ===")
    cmlog_files = [f for f in os.listdir('downloads/google_sheets_tabs') if f.startswith('CMLog_')]
    
    total_new_coord_records = 0
    all_coord_staff = set()
    
    for file in cmlog_files[:3]:  # Sample first 3 files
        try:
            df = pd.read_csv(f'downloads/google_sheets_tabs/{file}')
            
            # Filter valid data
            valid_mask = (
                df['Staff'].notna() & 
                (df['Staff'] != 'Staff') & 
                (~df['Staff'].str.contains('Aaa', na=False))
            )
            valid_data = df[valid_mask].copy()
            
            if len(valid_data) > 0:
                # Parse dates
                valid_data['parsed_date'] = pd.to_datetime(valid_data['Date Only'], errors='coerce')
                
                # Filter for 2025 data (assuming this is "new")
                new_data = valid_data[valid_data['parsed_date'] >= '2025-01-01']
                
                print(f"{file}:")
                print(f"  Total valid records: {len(valid_data)}")
                print(f"  New records (2025+): {len(new_data)}")
                
                if len(new_data) > 0:
                    staff_names = new_data['Staff'].dropna().unique()
                    all_coord_staff.update(staff_names)
                    print(f"  Staff: {list(staff_names)}")
                    
                total_new_coord_records += len(new_data)
                
        except Exception as e:
            print(f"Error processing {file}: {e}")
        
        print()
    
    print(f"TOTAL NEW COORDINATOR RECORDS: {total_new_coord_records}")
    print(f"UNIQUE STAFF IN NEW DATA: {len(all_coord_staff)}")
    print(f"Staff names: {sorted(list(all_coord_staff))}")
    print()
    
    # Analyze PSL files  
    print("=== PROVIDER DATA (PSL) ANALYSIS ===")
    psl_files = [f for f in os.listdir('downloads/google_sheets_tabs') if f.startswith('PSL_')]
    
    total_new_prov_records = 0
    all_prov_names = set()
    
    for file in psl_files[:2]:  # Sample first 2 files
        try:
            df = pd.read_csv(f'downloads/google_sheets_tabs/{file}')
            
            # Filter valid data
            valid_mask = (
                df['Prov'].notna() & 
                (df['Prov'] != 'Prov') & 
                (~df['Prov'].str.contains('Aaa', na=False))
            )
            valid_data = df[valid_mask].copy()
            
            if len(valid_data) > 0:
                # Parse dates
                valid_data['parsed_date'] = pd.to_datetime(valid_data['DOS'], errors='coerce')
                
                # Filter for recent data (2024+)
                new_data = valid_data[valid_data['parsed_date'] >= '2024-01-01']
                
                print(f"{file}:")
                print(f"  Total valid records: {len(valid_data)}")
                print(f"  New records (2024+): {len(new_data)}")
                
                if len(new_data) > 0:
                    prov_names = new_data['Prov'].dropna().unique()
                    all_prov_names.update(prov_names)
                    print(f"  Providers: {list(prov_names)}")
                    
                total_new_prov_records += len(new_data)
                
        except Exception as e:
            print(f"Error processing {file}: {e}")
            
        print()
    
    print(f"TOTAL NEW PROVIDER RECORDS: {total_new_prov_records}")
    print(f"UNIQUE PROVIDERS IN NEW DATA: {len(all_prov_names)}")
    print(f"Provider names: {sorted(list(all_prov_names))}")
    print()
    
    # Check which users are completely new
    print("=== NEW vs EXISTING USER COMPARISON ===")
    existing_coords = pd.read_sql_query("SELECT DISTINCT coordinator_id FROM coordinator_tasks", conn)
    existing_provs = pd.read_sql_query("SELECT DISTINCT provider_name FROM provider_tasks", conn)
    
    print(f"Existing coordinators in DB: {existing_coords['coordinator_id'].tolist()}")
    print(f"Existing providers in DB: {existing_provs['provider_name'].tolist()}")
    
    conn.close()

if __name__ == "__main__":
    analyze_new_data()