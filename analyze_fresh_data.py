#!/usr/bin/env python3
"""
Fresh Data Analysis Script
Uses the same logic as import_fresh_data.py to identify what data would be imported
without actually performing the import.
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
import re

# Database configuration
DB_PATH = r'd:\Git\myhealthteam2\Dev\production.db'

def is_date_from_cutoff(date_str, cutoff_date='2025-09-26'):
    """Check if date is from cutoff date (09/26/25) onwards"""
    if not date_str or pd.isna(date_str):
        return False
    
    try:
        # Handle various date formats
        date_str = str(date_str).strip()
        
        # Try MM/DD/YY format first
        if '/' in date_str and len(date_str.split('/')) == 3:
            parts = date_str.split('/')
            if len(parts[2]) == 2:  # YY format
                mm, dd, yy = parts
                yy = int(yy)
                # Convert 2-digit year to 4-digit
                if yy <= 50:  # Assume 00-50 means 2000-2050
                    yyyy = 2000 + yy
                else:  # 51-99 means 1951-1999
                    yyyy = 1900 + yy
                normalized_date = f"{yyyy:04d}-{int(mm):02d}-{int(dd):02d}"
            else:  # Already 4-digit year
                mm, dd, yyyy = parts
                normalized_date = f"{int(yyyy):04d}-{int(mm):02d}-{int(dd):02d}"
        else:
            # Try to parse as-is
            parsed_date = pd.to_datetime(date_str, errors='coerce')
            if pd.isna(parsed_date):
                return False
            normalized_date = parsed_date.strftime('%Y-%m-%d')
        
        # Compare with cutoff date
        return normalized_date >= cutoff_date
        
    except Exception as e:
        print(f"  Warning: Could not parse date '{date_str}': {e}")
        return False

def get_existing_data():
    """Get existing data from database tables for comparison"""
    conn = sqlite3.connect(DB_PATH)
    
    # Get existing coordinator tasks
    existing_coordinator_keys = set()
    try:
        coordinator_df = pd.read_sql_query("""
            SELECT coordinator_id, patient_id, task_date 
            FROM coordinator_tasks 
            WHERE task_type = 'RVZ'
        """, conn)
        
        for _, row in coordinator_df.iterrows():
            key = f"{row['coordinator_id']}_{row['patient_id']}_{row['task_date']}_RVZ"
            existing_coordinator_keys.add(key)
    except Exception as e:
        print(f"Warning: Could not load coordinator_tasks: {e}")
    
    # Get existing provider tasks
    existing_provider_keys = set()
    try:
        provider_df = pd.read_sql_query("""
            SELECT provider_id, patient_id, task_date, task_description 
            FROM provider_tasks
        """, conn)
        
        for _, row in provider_df.iterrows():
            key = f"{row['provider_id']}_{row['patient_id']}_{row['task_date']}_{row['task_description']}"
            existing_provider_keys.add(key)
    except Exception as e:
        print(f"Warning: Could not load provider_tasks: {e}")
    
    # Get existing provider tasks 2025_09
    try:
        provider_2025_df = pd.read_sql_query("""
            SELECT provider_id, patient_id, task_date, task_description 
            FROM provider_tasks_2025_09
        """, conn)
        
        for _, row in provider_2025_df.iterrows():
            key = f"{row['provider_id']}_{row['patient_id']}_{row['task_date']}_{row['task_description']}"
            existing_provider_keys.add(key)
    except Exception as e:
        print(f"Warning: Could not load provider_tasks_2025_09: {e}")
    
    # Get existing patients
    existing_patient_keys = set()
    try:
        patients_df = pd.read_sql_query("""
            SELECT first_name, last_name, date_of_birth 
            FROM patients
        """, conn)
        
        for _, row in patients_df.iterrows():
            # Normalize patient name and DOB for comparison
            normalized_name = f"{str(row['first_name']).strip().upper()} {str(row['last_name']).strip().upper()}"
            normalized_dob = str(row['date_of_birth']).strip()
            key = f"{normalized_name}_{normalized_dob}"
            existing_patient_keys.add(key)
    except Exception as e:
        print(f"Warning: Could not load patients: {e}")
    
    # Get staff code mapping
    staff_code_mapping = {}
    try:
        staff_mapping_df = pd.read_sql_query("""
            SELECT staff_code, user_id, confidence_level, mapping_type, notes 
            FROM staff_code_mapping
            WHERE user_id IS NOT NULL
        """, conn)
        
        for _, row in staff_mapping_df.iterrows():
            staff_code_mapping[row['staff_code']] = row['user_id']
    except Exception as e:
        print(f"Warning: Could not load staff_code_mapping: {e}")
    
    conn.close()
    
    return {
        'coordinator_keys': existing_coordinator_keys,
        'provider_keys': existing_provider_keys,
        'patient_keys': existing_patient_keys,
        'staff_code_mapping': staff_code_mapping
    }

def normalize_patient_name_dob(name, dob):
    """Normalize patient name and DOB for comparison"""
    # Remove common prefixes
    prefixes_to_remove = ['MR.', 'MRS.', 'MS.', 'DR.', 'MISS']
    normalized_name = str(name).strip().upper()
    
    for prefix in prefixes_to_remove:
        if normalized_name.startswith(prefix):
            normalized_name = normalized_name[len(prefix):].strip()
    
    # Normalize DOB
    normalized_dob = str(dob).strip()
    
    return f"{normalized_name}_{normalized_dob}"

def extract_duration_minutes(duration_str):
    """Extract duration in minutes from various formats"""
    if pd.isna(duration_str) or str(duration_str).strip() == '':
        return 0
    
    duration_str = str(duration_str).strip()
    
    # Handle time format (HH:MM)
    if ':' in duration_str:
        try:
            parts = duration_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours * 60 + minutes
        except:
            return 0
    
    # Handle numeric values (assume minutes)
    try:
        return int(float(duration_str))
    except:
        return 0

def analyze_cmlog_files():
    """Analyze CMLog files for fresh coordinator data"""
    fresh_coordinator_data = []
    total_records = 0
    filtered_by_date = 0
    
    # Look for CMLog files in downloads folder
    downloads_path = './downloads'
    if not os.path.exists(downloads_path):
        downloads_path = os.path.expanduser('~/Downloads')
        if not os.path.exists(downloads_path):
            downloads_path = '.'  # Fallback to current directory
    
    try:
        cmlog_files = [f for f in os.listdir(downloads_path) if f.startswith('CMLog_') and f.endswith('.csv')]
    except:
        cmlog_files = []
    
    if not cmlog_files:
        print("No CMLog files found in current directory")
        return fresh_coordinator_data
    
    existing_data = get_existing_data()
    
    for file in cmlog_files:
        print(f"\nAnalyzing {file}...")
        
        try:
            file_path = os.path.join(downloads_path, file)
            df = pd.read_csv(file_path)
            
            # Extract staff code from filename
            staff_code = file.replace('CMLog_', '').replace('.csv', '')
            
            # Get user_id for this staff code
            user_id = existing_data['staff_code_mapping'].get(staff_code)
            
            if not user_id:
                print(f"  Warning: No user_id found for staff code {staff_code}")
                user_id = staff_code  # Use staff code as fallback
            
            # Process each row
            for _, row in df.iterrows():
                try:
                    # Extract and normalize data
                    patient_name = str(row.get('Patient', '')).strip()
                    patient_id = str(row.get('Patient ID', '')).strip()
                    task_date = str(row.get('Date', '')).strip()
                    duration = extract_duration_minutes(row.get('Duration', ''))
                    
                    if not patient_name or not patient_id or not task_date:
                        continue
                    
                    # Filter by date cutoff (09/26/25 onwards)
                    if not is_date_from_cutoff(task_date):
                        continue
                    
                    # Create comparison key
                    comparison_key = f"{user_id}_{patient_id}_{task_date}_RVZ"
                    
                    # Check if this is fresh data
                    if comparison_key not in existing_data['coordinator_keys']:
                        fresh_coordinator_data.append({
                            'file': file,
                            'staff_code': staff_code,
                            'user_id': user_id,
                            'patient_name': patient_name,
                            'patient_id': patient_id,
                            'task_date': task_date,
                            'duration_minutes': duration,
                            'task_type': 'RVZ',
                            'comparison_key': comparison_key
                        })
                
                except Exception as e:
                    print(f"  Error processing row: {e}")
                    continue
        
        except Exception as e:
            print(f"  Error reading {file}: {e}")
            continue
    
    return fresh_coordinator_data

def analyze_provider_files():
    """Analyze Provider files for fresh provider data"""
    fresh_provider_data = []
    
    # Look for Provider files (PSL and RVZ)
    downloads_path = './downloads'
    if not os.path.exists(downloads_path):
        downloads_path = '.'
    
    provider_files = [f for f in os.listdir(downloads_path) if 
                     (f.startswith('PSL_') or f.startswith('RVZ_')) and f.endswith('.csv')]
    
    if not provider_files:
        print("No Provider files found in current directory")
        return fresh_provider_data
    
    existing_data = get_existing_data()
    
    for file in provider_files:
        print(f"\nAnalyzing {file}...")
        
        try:
            file_path = os.path.join(downloads_path, file)
            df = pd.read_csv(file_path)
            
            # Extract staff code and task type from filename
            if file.startswith('PSL_'):
                task_type = 'PSL'
                staff_code = file.replace('PSL_', '').replace('.csv', '')
            else:  # RVZ_
                task_type = 'RVZ'
                staff_code = file.replace('RVZ_', '').replace('.csv', '')
            
            # Get user_id for this staff code
            user_id = existing_data['staff_code_mapping'].get(staff_code)
            
            if not user_id:
                print(f"  Warning: No user_id found for staff code {staff_code}")
                user_id = staff_code  # Use staff code as fallback
            
            # Process each row
            for _, row in df.iterrows():
                try:
                    # Extract and normalize data
                    patient_name = str(row.get('Patient', '')).strip()
                    patient_id = str(row.get('Patient ID', '')).strip()
                    task_date = str(row.get('Date', '')).strip()
                    duration = extract_duration_minutes(row.get('Duration', ''))
                    
                    if not patient_name or not patient_id or not task_date:
                        continue
                    
                    # Filter by date cutoff (09/26/25 onwards)
                    if not is_date_from_cutoff(task_date):
                        continue
                    
                    # Create comparison key
                    comparison_key = f"{user_id}_{patient_id}_{task_date}_{task_type}"
                    
                    # Check if this is fresh data
                    if comparison_key not in existing_data['provider_keys']:
                        fresh_provider_data.append({
                            'file': file,
                            'staff_code': staff_code,
                            'user_id': user_id,
                            'patient_name': patient_name,
                            'patient_id': patient_id,
                            'task_date': task_date,
                            'duration_minutes': duration,
                            'task_type': task_type,
                            'comparison_key': comparison_key
                        })
                
                except Exception as e:
                    print(f"  Error processing row: {e}")
                    continue
        
        except Exception as e:
            print(f"  Error reading {file}: {e}")
            continue
    
    return fresh_provider_data

def analyze_zmo_files():
    """Analyze ZMO files for fresh patient data"""
    fresh_patient_data = []
    
    # Look for ZMO_MAIN.csv
    downloads_path = './downloads'
    if not os.path.exists(downloads_path):
        downloads_path = '.'
    
    zmo_file = os.path.join(downloads_path, 'ZMO_MAIN.csv')
    if not os.path.exists(zmo_file):
        print("No ZMO_MAIN.csv file found")
        return fresh_patient_data
    
    print(f"\nAnalyzing {zmo_file}...")
    
    try:
        df = pd.read_csv(zmo_file)
        existing_data = get_existing_data()
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Extract and normalize patient data
                first_name = str(row.get('First Name', '')).strip()
                last_name = str(row.get('Last Name', '')).strip()
                dob = str(row.get('Date of Birth', '')).strip()
                patient_id = str(row.get('Patient ID', '')).strip()
                
                if not first_name or not last_name or not dob:
                    continue
                
                # Create comparison key
                comparison_key = normalize_patient_name_dob(f"{first_name} {last_name}", dob)
                
                # Check if this is fresh data
                if comparison_key not in existing_data['patient_keys']:
                    fresh_patient_data.append({
                        'file': zmo_file,
                        'first_name': first_name,
                        'last_name': last_name,
                        'date_of_birth': dob,
                        'patient_id': patient_id,
                        'comparison_key': comparison_key
                    })
            
            except Exception as e:
                print(f"  Error processing row: {e}")
                continue
    
    except Exception as e:
        print(f"  Error reading {zmo_file}: {e}")
    
    return fresh_patient_data

def generate_analysis_report(coordinator_data, provider_data, patient_data):
    """Generate a comprehensive analysis report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"fresh_data_analysis_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write("FRESH DATA ANALYSIS REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Date Filter: Only analyzing data from 09/26/25 onwards\n\n")
        
        # Summary
        f.write("SUMMARY\n")
        f.write("-" * 20 + "\n")
        f.write(f"Fresh Coordinator Tasks: {len(coordinator_data)}\n")
        f.write(f"Fresh Provider Tasks: {len(provider_data)}\n")
        f.write(f"Fresh Patients: {len(patient_data)}\n")
        f.write(f"Total Fresh Records: {len(coordinator_data) + len(provider_data) + len(patient_data)}\n\n")
        
        # Coordinator Tasks Detail
        if coordinator_data:
            f.write("FRESH COORDINATOR TASKS\n")
            f.write("-" * 30 + "\n")
            for item in coordinator_data:
                f.write(f"File: {item['file']}\n")
                f.write(f"  Staff: {item['staff_code']} (User ID: {item['user_id']})\n")
                f.write(f"  Patient: {item['patient_name']} (ID: {item['patient_id']})\n")
                f.write(f"  Date: {item['task_date']}, Duration: {item['duration_minutes']} min\n")
                f.write(f"  Key: {item['comparison_key']}\n\n")
        
        # Provider Tasks Detail
        if provider_data:
            f.write("FRESH PROVIDER TASKS\n")
            f.write("-" * 25 + "\n")
            for item in provider_data:
                f.write(f"File: {item['file']}\n")
                f.write(f"  Staff: {item['staff_code']} (User ID: {item['user_id']})\n")
                f.write(f"  Patient: {item['patient_name']} (ID: {item['patient_id']})\n")
                f.write(f"  Date: {item['task_date']}, Type: {item['task_type']}, Duration: {item['duration_minutes']} min\n")
                f.write(f"  Key: {item['comparison_key']}\n\n")
        
        # Patient Data Detail
        if patient_data:
            f.write("FRESH PATIENTS\n")
            f.write("-" * 15 + "\n")
            for item in patient_data:
                f.write(f"File: {item['file']}\n")
                f.write(f"  Name: {item['first_name']} {item['last_name']}\n")
                f.write(f"  DOB: {item['date_of_birth']}, Patient ID: {item['patient_id']}\n")
                f.write(f"  Key: {item['comparison_key']}\n\n")
        
        # File breakdown
        f.write("FILE BREAKDOWN\n")
        f.write("-" * 15 + "\n")
        
        all_files = set()
        for item in coordinator_data + provider_data + patient_data:
            all_files.add(item['file'])
        
        for file in sorted(all_files):
            coord_count = len([x for x in coordinator_data if x['file'] == file])
            prov_count = len([x for x in provider_data if x['file'] == file])
            pat_count = len([x for x in patient_data if x['file'] == file])
            
            f.write(f"{file}:\n")
            if coord_count > 0:
                f.write(f"  Coordinator Tasks: {coord_count}\n")
            if prov_count > 0:
                f.write(f"  Provider Tasks: {prov_count}\n")
            if pat_count > 0:
                f.write(f"  Patients: {pat_count}\n")
            f.write("\n")
    
    return report_file

def main():
    """Main analysis function"""
    print("FRESH DATA ANALYSIS")
    print("=" * 50)
    print("Analyzing what data would be imported using import_fresh_data.py logic...")
    print()
    
    # Analyze each data type
    coordinator_data = analyze_cmlog_files()
    provider_data = analyze_provider_files()
    patient_data = analyze_zmo_files()
    
    # Generate report
    report_file = generate_analysis_report(coordinator_data, provider_data, patient_data)
    
    # Print summary to console
    print("\nANALYSIS COMPLETE")
    print("=" * 30)
    print(f"Fresh Coordinator Tasks: {len(coordinator_data)}")
    print(f"Fresh Provider Tasks: {len(provider_data)}")
    print(f"Fresh Patients: {len(patient_data)}")
    print(f"Total Fresh Records: {len(coordinator_data) + len(provider_data) + len(patient_data)}")
    print(f"\nDetailed report saved to: {report_file}")
    
    # Show sample data if available
    if coordinator_data:
        print(f"\nSample Coordinator Task:")
        sample = coordinator_data[0]
        print(f"  {sample['staff_code']} -> {sample['patient_name']} on {sample['task_date']}")
    
    if provider_data:
        print(f"\nSample Provider Task:")
        sample = provider_data[0]
        print(f"  {sample['staff_code']} -> {sample['patient_name']} ({sample['task_type']}) on {sample['task_date']}")
    
    if patient_data:
        print(f"\nSample Patient:")
        sample = patient_data[0]
        print(f"  {sample['first_name']} {sample['last_name']} (DOB: {sample['date_of_birth']})")

if __name__ == "__main__":
    main()