import pandas as pd
import sqlite3
from datetime import datetime
import re

def normalize_patient_name(name):
    """Normalize patient name by removing prefixes and standardizing format"""
    if pd.isna(name) or not name.strip():
        return ""
    
    # Remove common prefixes like "ZEN-"
    name = re.sub(r'^[A-Z]+-', '', name.strip())
    
    # Handle multi-line names (like "Rivas, Glorybell")
    name = ' '.join(name.split())
    
    # Convert to uppercase and remove extra spaces
    return name.upper().strip()

def normalize_date(date_str):
    """Normalize date from MM/DD/YY format to YYYY-MM-DD"""
    if pd.isna(date_str) or not date_str.strip():
        return None
    
    try:
        # Handle MM/DD/YY format (assuming 25 means 2025)
        date_obj = datetime.strptime(date_str.strip(), '%m/%d/%y')
        # Convert 2-digit year to 4-digit (25 -> 2025, etc.)
        if date_obj.year < 2000:
            date_obj = date_obj.replace(year=date_obj.year + 100)
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        try:
            # Try other common formats
            date_obj = datetime.strptime(date_str.strip(), '%Y-%m-%d')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            print(f"Warning: Could not parse date: {date_str}")
            return None

def extract_duration_minutes(duration_str):
    """Extract numeric duration from duration range strings"""
    if pd.isna(duration_str) or not duration_str.strip():
        return None
    
    # Extract first number from ranges like "30-39", "40-49", etc.
    match = re.search(r'(\d+)', duration_str)
    if match:
        return int(match.group(1))
    return None

def load_psl_highlighted_data():
    """Load and parse the highlighted PSL data from lines 3146-3180"""
    psl_file = r'd:\Git\myhealthteam2\Dev\downloads\PSL_ZEN-SZA.csv'
    
    try:
        # Read the specific lines (3142-3174 based on the highlighted section)
        df = pd.read_csv(psl_file, header=None, skiprows=3141, nrows=33)
        
        # Set column names based on PSL format
        df.columns = ['Row', 'Prov', 'Service', 'Empty1', 'Patient_Name_DOB', 'DOS', 'Service_Description', 'Minutes', 'Empty2', 'Empty3', 'Empty4', 'Empty5', 'Empty6', 'Empty7', 'Empty8', 'Empty9', 'Empty10']
        
        # Filter out empty or placeholder rows
        df = df[df['Patient_Name_DOB'].notna() & (df['Patient_Name_DOB'].str.strip() != '')]
        df = df[~df['Patient_Name_DOB'].str.contains('PLACEHOLDER|placeholder', case=False, na=False)]
        
        # Normalize the data
        df['normalized_patient_name'] = df['Patient_Name_DOB'].apply(normalize_patient_name)
        df['normalized_date'] = df['DOS'].apply(normalize_date)
        df['duration_minutes'] = df['Minutes'].apply(extract_duration_minutes)
        
        # Filter out rows with invalid dates or names
        df = df[df['normalized_date'].notna() & (df['normalized_patient_name'] != '')]
        
        # Create comparison key
        df['comparison_key'] = df['normalized_patient_name'] + '|' + df['normalized_date'] + '|' + df['Service'].astype(str)
        
        print(f"Loaded {len(df)} valid PSL records from highlighted section")
        return df
        
    except Exception as e:
        print(f"Error loading PSL data: {e}")
        return pd.DataFrame()

def get_zen_sza_user_id():
    """Get the user_id for ZEN-SZA from staff_code_mapping table"""
    try:
        conn = sqlite3.connect('production.db')
        
        query = """
        SELECT user_id 
        FROM users
        WHERE full_name LIKE '%Zen%' OR alias LIKE '%ZEN%' OR first_name LIKE '%Zen%' OR last_name LIKE '%Sza%'
        """
        
        result = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(result) > 0:
            user_id = result.iloc[0]['user_id']
            full_name = result.iloc[0]['full_name']
            print(f"Found ZEN-SZA mapping: user_id={user_id}, full_name={full_name}")
            return user_id
        else:
            print("ERROR: No mapping found for ZEN-SZA in staff_code_mapping table")
            return None
            
    except Exception as e:
        print(f"Error getting ZEN-SZA user_id: {e}")
        return None

def load_provider_tasks_data(user_id):
    """Load provider tasks data for ZEN-SZA from both tables"""
    if user_id is None:
        return pd.DataFrame(), pd.DataFrame()
    
    try:
        conn = sqlite3.connect(r'd:\Git\myhealthteam2\Dev\myhealthteam.db')
        
        # Query provider_tasks table
        query1 = """
        SELECT user_id, patient_name, task_date, minutes_of_service, billing_code, notes
        FROM provider_tasks
        WHERE user_id = ? 
        AND task_date BETWEEN '2024-09-23' AND '2024-09-30'
        ORDER BY task_date, patient_name
        """
        
        # Query provider_tasks_2025_09 table  
        query2 = """
        SELECT user_id, patient_name, task_date, minutes_of_service, billing_code, notes
        FROM provider_tasks_2025_09
        WHERE user_id = ?
        AND task_date BETWEEN '2024-09-23' AND '2024-09-30'
        ORDER BY task_date, patient_name
        """
        
        df1 = pd.read_sql_query(query1, conn, params=[user_id])
        df2 = pd.read_sql_query(query2, conn, params=[user_id])
        
        conn.close()
        
        # Normalize database data
        for df in [df1, df2]:
            if len(df) > 0:
                df['normalized_patient_name'] = df['patient_name'].apply(normalize_patient_name)
                df['normalized_date'] = df['task_date']  # Already in YYYY-MM-DD format
                df['comparison_key'] = df['normalized_patient_name'] + '|' + df['normalized_date'] + '|' + df['billing_code'].astype(str)
        
        print(f"Loaded {len(df1)} records from provider_tasks")
        print(f"Loaded {len(df2)} records from provider_tasks_2025_09")
        
        return df1, df2
        
    except Exception as e:
        print(f"Error loading provider tasks data: {e}")
        return pd.DataFrame(), pd.DataFrame()

def compare_datasets(psl_df, db_df1, db_df2):
    """Compare PSL data against database tables"""
    
    # Combine database dataframes
    db_combined = pd.concat([db_df1, db_df2], ignore_index=True)
    
    if len(psl_df) == 0:
        print("No PSL data to compare")
        return
    
    if len(db_combined) == 0:
        print("No database data to compare against")
        return
    
    # Find matches and missing records
    psl_keys = set(psl_df['comparison_key'])
    db_keys = set(db_combined['comparison_key'])
    
    matches = psl_keys.intersection(db_keys)
    psl_only = psl_keys - db_keys
    db_only = db_keys - psl_keys
    
    print(f"\n=== COMPARISON RESULTS ===")
    print(f"PSL records: {len(psl_df)}")
    print(f"Database records: {len(db_combined)}")
    print(f"Matches: {len(matches)}")
    print(f"PSL only (missing from DB): {len(psl_only)}")
    print(f"DB only (missing from PSL): {len(db_only)}")
    
    # Generate detailed report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'psl_highlighted_comparison_{timestamp}.txt'
    
    with open(report_file, 'w') as f:
        f.write("PSL HIGHLIGHTED DATA COMPARISON REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"PSL File: PSL_ZEN-SZA.csv (lines 3146-3180)\n")
        f.write(f"Provider: ZEN-SZA\n")
        f.write(f"Date Range: 2024-09-23 to 2024-09-30\n\n")
        
        f.write("SUMMARY:\n")
        f.write(f"  PSL records: {len(psl_df)}\n")
        f.write(f"  Database records (combined): {len(db_combined)}\n")
        f.write(f"  - provider_tasks: {len(db_df1)}\n")
        f.write(f"  - provider_tasks_2025_09: {len(db_df2)}\n")
        f.write(f"  Matches: {len(matches)}\n")
        f.write(f"  PSL only (missing from DB): {len(psl_only)}\n")
        f.write(f"  DB only (missing from PSL): {len(db_only)}\n\n")
        
        if len(psl_only) > 0:
            f.write("RECORDS IN PSL BUT MISSING FROM DATABASE:\n")
            f.write("-" * 50 + "\n")
            missing_psl = psl_df[psl_df['comparison_key'].isin(psl_only)]
            for _, row in missing_psl.iterrows():
                f.write(f"Patient: {row['Patient_Name_DOB']}\n")
                f.write(f"Date: {row['DOS']} -> {row['normalized_date']}\n")
                f.write(f"Service: {row['Service']}\n")
                f.write(f"Duration: {row['Minutes']} -> {row['duration_minutes']} min\n")
                f.write(f"Normalized Name: {row['normalized_patient_name']}\n")
                f.write(f"Key: {row['comparison_key']}\n\n")
        
        if len(db_only) > 0:
            f.write("RECORDS IN DATABASE BUT MISSING FROM PSL:\n")
            f.write("-" * 50 + "\n")
            missing_db = db_combined[db_combined['comparison_key'].isin(db_only)]
            for _, row in missing_db.iterrows():
                f.write(f"Patient: {row['patient_name']}\n")
                f.write(f"Date: {row['task_date']}\n")
                f.write(f"Billing Code: {row['billing_code']}\n")
                f.write(f"Minutes: {row['minutes_of_service']}\n")
                f.write(f"Normalized Name: {row['normalized_patient_name']}\n")
                f.write(f"Key: {row['comparison_key']}\n\n")
        
        if len(matches) > 0:
            f.write("MATCHING RECORDS:\n")
            f.write("-" * 50 + "\n")
            matching_psl = psl_df[psl_df['comparison_key'].isin(matches)]
            for _, row in matching_psl.iterrows():
                f.write(f"✓ {row['Patient_Name_DOB']} | {row['DOS']} | {row['Service']}\n")
    
    print(f"\nDetailed report saved to: {report_file}")
    return report_file

def main():
    """Main comparison function"""
    print("Starting PSL highlighted data comparison...")
    
    # Load PSL data from highlighted section
    psl_df = load_psl_highlighted_data()
    
    # Get ZEN-SZA user_id from staff mapping
    user_id = get_zen_sza_user_id()
    
    # Load database data
    db_df1, db_df2 = load_provider_tasks_data(user_id)
    
    # Perform comparison
    report_file = compare_datasets(psl_df, db_df1, db_df2)
    
    print("Comparison completed!")
    return report_file

if __name__ == "__main__":
    main()