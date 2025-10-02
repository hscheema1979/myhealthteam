#!/usr/bin/env python3
"""
Normalize and Import Fresh Data
- Normalize CMLog, Provider (PSL/RVZ), and ZMO data files
- Compare against existing database records
- Import only new data to avoid duplicates
- Follow RASM principles for reliability and maintainability
"""

import pandas as pd
import sqlite3
import glob
import os
from datetime import datetime
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FreshDataNormalizer:
    def __init__(self, downloads_dir="./downloads", db_path="./production.db"):
        self.downloads_dir = downloads_dir
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.stats = {
            'cmlog_processed': 0,
            'cmlog_new': 0,
            'provider_processed': 0,
            'provider_new': 0,
            'zmo_processed': 0,
            'zmo_new': 0
        }
        
    def normalize_patient_id(self, patient_name):
        """Normalize patient ID: remove ZEN- prefix and commas, keep existing format"""
        if not patient_name or pd.isna(patient_name):
            return None
        
        normalized = str(patient_name).strip()
        
        # Remove ZEN- prefix
        normalized = normalized.replace('ZEN-', '')
        
        # Remove commas (both ", " and ",")
        normalized = normalized.replace(', ', ' ')
        normalized = normalized.replace(',', ' ')
        
        # Replace multiple spaces with single space
        while '  ' in normalized:
            normalized = normalized.replace('  ', ' ')
        
        # Convert to uppercase to match database format
        normalized = normalized.upper()
        
        return normalized.strip()
    
    def normalize_date(self, date_str):
        """Normalize date to YYYY-MM-DD format"""
        if not date_str or pd.isna(date_str):
            return None
            
        date_str = str(date_str).strip()
        
        # Handle MM/DD/YYYY format
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
            parts = date_str.split('/')
            month, day, year = parts[0].zfill(2), parts[1].zfill(2), parts[2]
            return f"{year}-{month}-{day}"
        
        # Handle MM/DD/YY format
        if re.match(r'^\d{1,2}/\d{1,2}/\d{2}$', date_str):
            parts = date_str.split('/')
            month, day, year = parts[0].zfill(2), parts[1].zfill(2), f"20{parts[2]}"
            return f"{year}-{month}-{day}"
        
        # Already in YYYY-MM-DD format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
            
        return None
    
    def normalize_patient_id_date(self, date_str):
        """Normalize date to MM/DD/YYYY format for patient IDs"""
        if not date_str or pd.isna(date_str):
            return None
            
        date_str = str(date_str).strip()
        
        # Handle MM/DD/YYYY format (already correct)
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
            parts = date_str.split('/')
            month, day, year = parts[0].zfill(2), parts[1].zfill(2), parts[2]
            return f"{month}/{day}/{year}"
        
        # Handle MM/DD/YY format
        if re.match(r'^\d{1,2}/\d{1,2}/\d{2}$', date_str):
            parts = date_str.split('/')
            month, day, year = parts[0].zfill(2), parts[1].zfill(2), f"20{parts[2]}"
            return f"{month}/{day}/{year}"
        
        # Handle YYYY-MM-DD format (convert to MM/DD/YYYY)
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            parts = date_str.split('-')
            year, month, day = parts[0], parts[1], parts[2]
            return f"{month}/{day}/{year}"
            
        return None
    
    def normalize_cmlog_files(self):
        """Normalize CMLog files and identify new coordinator tasks"""
        logger.info("=== NORMALIZING CMLOG FILES ===")
        
        cmlog_files = glob.glob(os.path.join(self.downloads_dir, "CMLog_*.csv"))
        
        if not cmlog_files:
            logger.warning(f"No CMLog files found in {self.downloads_dir}")
            return pd.DataFrame()
        
        # Get existing coordinator tasks for comparison
        existing_tasks = pd.read_sql_query("""
            SELECT coordinator_id, patient_id, task_date
            FROM coordinator_tasks
        """, self.conn)
        
        # Create comparison keys for existing tasks
        existing_tasks['comparison_key'] = (
            existing_tasks['coordinator_id'].astype(str) + '|' +
            existing_tasks['patient_id'].astype(str) + '|' +
            existing_tasks['task_date'].astype(str)
        )
        existing_keys = set(existing_tasks['comparison_key'].tolist())
        
        # No complex patient matching needed - just normalize and import
        
        # Get staff mapping
        staff_mapping = pd.read_sql_query("""
            SELECT scm.staff_code, scm.user_id, u.full_name
            FROM staff_code_mapping scm
            LEFT JOIN users u ON scm.user_id = u.user_id
        """, self.conn)
        staff_dict = dict(zip(staff_mapping['staff_code'], staff_mapping['user_id']))
        
        all_new_tasks = []
        
        for file in cmlog_files:
            try:
                logger.info(f"Processing {os.path.basename(file)}")
                df = pd.read_csv(file)
                
                # Filter out placeholder and invalid rows
                df = df[~df['Pt Name'].str.contains('Aaa, Aaa', na=False)]
                df = df[~df['Notes'].str.contains('Place holder', na=False)]
                df = df.dropna(subset=['Staff', 'Pt Name', 'Date Only'])
                
                # Normalize patient IDs and dates
                df['normalized_patient_id'] = df['Pt Name'].apply(self.normalize_patient_id)
                df['normalized_date'] = df['Date Only'].apply(self.normalize_date)
                df['coordinator_id'] = df['Staff'].map(staff_dict)
                
                # Extract duration (prefer Mins B, fallback to Total Mins)
                df['duration_minutes'] = pd.to_numeric(df['Mins B'], errors='coerce')
                df['duration_minutes'] = df['duration_minutes'].fillna(
                    pd.to_numeric(df['Total Mins'], errors='coerce')
                )
                
                # Filter valid records
                valid_df = df[
                    (df['normalized_patient_id'].notna()) &
                    (df['normalized_date'].notna()) &
                    (df['coordinator_id'].notna()) &
                    (df['duration_minutes'] > 0)
                ]
                
                # Create comparison keys for new data
                valid_df['comparison_key'] = (
                    valid_df['coordinator_id'].astype(str) + '|' +
                    valid_df['normalized_patient_id'].astype(str) + '|' +
                    valid_df['normalized_date'].astype(str) + '|' +
                    valid_df['duration_minutes'].astype(str) + '|' +
                    valid_df['Type'].fillna('').astype(str)
                )
                
                # Filter out existing tasks
                new_tasks = valid_df[~valid_df['comparison_key'].isin(existing_keys)]
                
                if len(new_tasks) > 0:
                    # Prepare final data structure
                    normalized_tasks = pd.DataFrame({
                        'coordinator_id': new_tasks['coordinator_id'],
                        'patient_id': new_tasks['normalized_patient_id'],
                        'task_date': new_tasks['normalized_date'],
                        'duration_minutes': new_tasks['duration_minutes'].astype(int),
                        'task_type': new_tasks['Type'].fillna(''),
                        'notes': new_tasks['Notes'].fillna('')
                    })
                    
                    all_new_tasks.append(normalized_tasks)
                    logger.info(f"Found {len(new_tasks)} new tasks in {os.path.basename(file)}")
                else:
                    logger.info(f"No new tasks found in {os.path.basename(file)}")
                
                self.stats['cmlog_processed'] += len(df)
                
            except Exception as e:
                logger.error(f"Error processing {file}: {e}")
        
        if all_new_tasks:
            final_new_tasks = pd.concat(all_new_tasks, ignore_index=True)
            self.stats['cmlog_new'] = len(final_new_tasks)
            logger.info(f"Total new CMLog tasks to import: {len(final_new_tasks)}")
            return final_new_tasks
        
        return pd.DataFrame()
    
    def normalize_provider_files(self):
        """Normalize Provider (PSL/RVZ) files and identify new provider tasks"""
        logger.info("=== NORMALIZING PROVIDER FILES ===")
        
        psl_files = glob.glob(os.path.join(self.downloads_dir, "PSL_*.csv"))
        rvz_files = glob.glob(os.path.join(self.downloads_dir, "RVZ_*.csv"))
        
        if not psl_files and not rvz_files:
            logger.warning(f"No PSL or RVZ files found in {self.downloads_dir}")
            return [], []
        
        # Get staff mapping for provider codes
        staff_mapping = pd.read_sql_query("""
            SELECT scm.staff_code, scm.user_id, u.full_name
            FROM staff_code_mapping scm
            LEFT JOIN users u ON scm.user_id = u.user_id
        """, self.conn)
        staff_dict = dict(zip(staff_mapping['staff_code'], staff_mapping['user_id']))
        staff_name_dict = dict(zip(staff_mapping['staff_code'], staff_mapping['full_name']))
        
        # Get existing provider tasks for comparison
        existing_provider_tasks = pd.read_sql_query("""
            SELECT provider_id, patient_id, task_date, task_description
            FROM provider_tasks
        """, self.conn)
        
        # Get existing coordinator tasks for comparison (for RVZ dual insertion)
        existing_coordinator_tasks = pd.read_sql_query("""
            SELECT coordinator_id, patient_id, task_date, task_type
            FROM coordinator_tasks
        """, self.conn)
        
        # Create comparison keys for existing tasks
        existing_provider_tasks['comparison_key'] = (
            existing_provider_tasks['provider_id'].astype(str) + '|' +
            existing_provider_tasks['patient_id'].astype(str) + '|' +
            existing_provider_tasks['task_date'].astype(str) + '|' +
            existing_provider_tasks['task_description'].astype(str)
        )
        existing_provider_keys = set(existing_provider_tasks['comparison_key'].tolist())
        
        existing_coordinator_tasks['comparison_key'] = (
            existing_coordinator_tasks['coordinator_id'].astype(str) + '|' +
            existing_coordinator_tasks['patient_id'].astype(str) + '|' +
            existing_coordinator_tasks['task_date'].astype(str) + '|' +
            existing_coordinator_tasks['task_type'].astype(str)
        )
        existing_coordinator_keys = set(existing_coordinator_tasks['comparison_key'].tolist())
        
        all_new_provider_tasks = []
        all_new_coordinator_tasks = []
        
        # Process PSL files
        for file in psl_files:
            try:
                logger.info(f"Processing {os.path.basename(file)}")
                df = pd.read_csv(file)
                
                # Extract provider code from filename (PSL_ZEN-XXX.csv)
                provider_code = os.path.basename(file).replace('PSL_', '').replace('.csv', '')
                
                # Get user_id and full_name from staff mapping
                user_id = staff_dict.get(provider_code)
                provider_name = staff_name_dict.get(provider_code)
                
                if not user_id:
                    logger.warning(f"No staff mapping found for provider code: {provider_code}")
                    continue
                
                # Normalize patient IDs
                if 'Patient Last, First DOB' in df.columns:
                    df['normalized_patient_id'] = df['Patient Last, First DOB'].apply(self.normalize_patient_id)
                elif 'Pt Name' in df.columns:
                    df['normalized_patient_id'] = df['Pt Name'].apply(self.normalize_patient_id)
                else:
                    logger.warning(f"No patient name column found in {file}")
                    continue
                
                # Normalize dates
                if 'Date' in df.columns:
                    df['normalized_date'] = df['Date'].apply(self.normalize_date)
                elif 'Date Only' in df.columns:
                    df['normalized_date'] = df['Date Only'].apply(self.normalize_date)
                else:
                    logger.warning(f"No date column found in {file}")
                    continue
                
                # Extract task description and duration
                # For RVZ files: Type column for task, Total Mins for duration
                # For PSL files: Service column for task, Minutes for duration
                if 'Total Mins' in df.columns:  # RVZ file
                    task_col = df.get('Type', pd.Series(['RVZ Review'] * len(df)))
                    duration_col = df.get('Total Mins', pd.Series([0] * len(df)))
                else:  # PSL file
                    task_col = df.get('Service', df.get('Task', pd.Series(['PSL Review'] * len(df))))
                    duration_col = df.get('Minutes', df.get('Duration', pd.Series([0] * len(df))))
                
                task_description = task_col.fillna('Review') if hasattr(task_col, 'fillna') else task_col
                duration_minutes = pd.to_numeric(duration_col, errors='coerce')
                duration_minutes = duration_minutes.fillna(0) if hasattr(duration_minutes, 'fillna') else duration_minutes
                
                # Filter valid records
                valid_df = df[
                    (df['normalized_patient_id'].notna()) &
                    (df['normalized_date'].notna())
                ].copy()
                
                valid_df['task_description'] = task_description
                valid_df['duration_minutes'] = duration_minutes
                
                # Create comparison keys for new data
                valid_df['comparison_key'] = (
                    str(user_id) + '|' +
                    valid_df['normalized_patient_id'].astype(str) + '|' +
                    valid_df['normalized_date'].astype(str) + '|' +
                    valid_df['task_description'].astype(str)
                )
                
                # Filter out existing tasks
                new_tasks = valid_df[~valid_df['comparison_key'].isin(existing_provider_keys)]
                
                if len(new_tasks) > 0:
                    # Prepare final data structure for provider_tasks
                    notes_column = new_tasks.get('Notes', pd.Series([''] * len(new_tasks)))
                    if hasattr(notes_column, 'fillna'):
                        notes_column = notes_column.fillna('')
                    
                    normalized_tasks = pd.DataFrame({
                        'provider_id': user_id,
                        'provider_name': provider_name,
                        'patient_id': new_tasks['normalized_patient_id'],
                        'task_date': new_tasks['normalized_date'],
                        'task_description': new_tasks['task_description'],
                        'minutes_of_service': new_tasks['duration_minutes'].astype(int),
                        'notes': notes_column,
                        'source_system': 'PSL',
                        'imported_at': datetime.now().isoformat()
                    })
                    
                    all_new_provider_tasks.append(normalized_tasks)
                    logger.info(f"Found {len(new_tasks)} new PSL tasks in {os.path.basename(file)}")
                
                self.stats['provider_processed'] += len(df)
                
            except Exception as e:
                logger.error(f"Error processing {file}: {e}")
        
        # Process RVZ files - INSERT INTO BOTH provider_tasks AND coordinator_tasks
        for file in rvz_files:
            try:
                logger.info(f"Processing {os.path.basename(file)}")
                df = pd.read_csv(file)
                
                # Extract provider code from filename (RVZ_ZEN-XXX.csv)
                provider_code = os.path.basename(file).replace('RVZ_', '').replace('.csv', '')
                
                # Get user_id and full_name from staff mapping
                user_id = staff_dict.get(provider_code)
                provider_name = staff_name_dict.get(provider_code)
                
                if not user_id:
                    logger.warning(f"No staff mapping found for provider code: {provider_code}")
                    continue
                
                # Normalize patient IDs
                if 'Patient Last, First DOB' in df.columns:
                    df['normalized_patient_id'] = df['Patient Last, First DOB'].apply(self.normalize_patient_id)
                elif 'Pt Name' in df.columns:
                    df['normalized_patient_id'] = df['Pt Name'].apply(self.normalize_patient_id)
                else:
                    logger.warning(f"No patient name column found in {file}")
                    continue
                
                # Normalize dates
                if 'Date' in df.columns:
                    df['normalized_date'] = df['Date'].apply(self.normalize_date)
                elif 'Date Only' in df.columns:
                    df['normalized_date'] = df['Date Only'].apply(self.normalize_date)
                else:
                    logger.warning(f"No date column found in {file}")
                    continue
                
                # Extract task description and duration
                task_description = df.get('Task', df.get('Type', 'RVZ Review')).fillna('RVZ Review')
                duration_minutes = pd.to_numeric(df.get('Duration', df.get('Minutes', 0)), errors='coerce').fillna(0)
                
                # Filter valid records
                valid_df = df[
                    (df['normalized_patient_id'].notna()) &
                    (df['normalized_date'].notna())
                ].copy()
                
                valid_df['task_description'] = task_description
                valid_df['duration_minutes'] = duration_minutes
                
                # === PROVIDER TASKS INSERTION ===
                # Create comparison keys for provider tasks
                valid_df['provider_comparison_key'] = (
                    str(user_id) + '|' +
                    valid_df['normalized_patient_id'].astype(str) + '|' +
                    valid_df['normalized_date'].astype(str) + '|' +
                    valid_df['task_description'].astype(str)
                )
                
                # Filter out existing provider tasks
                new_provider_tasks = valid_df[~valid_df['provider_comparison_key'].isin(existing_provider_keys)]
                
                if len(new_provider_tasks) > 0:
                    # Prepare data for provider_tasks table
                    notes_column = new_provider_tasks.get('Notes', pd.Series([''] * len(new_provider_tasks)))
                    if hasattr(notes_column, 'fillna'):
                        notes_column = notes_column.fillna('')
                    
                    provider_tasks_data = pd.DataFrame({
                        'provider_id': user_id,
                        'provider_name': provider_name,
                        'patient_id': new_provider_tasks['normalized_patient_id'],
                        'task_date': new_provider_tasks['normalized_date'],
                        'task_description': new_provider_tasks['task_description'],
                        'minutes_of_service': new_provider_tasks['duration_minutes'].astype(int),
                        'notes': notes_column,
                        'source_system': 'RVZ',
                        'imported_at': datetime.now().isoformat()
                    })
                    
                    all_new_provider_tasks.append(provider_tasks_data)
                    logger.info(f"Found {len(new_provider_tasks)} new RVZ provider tasks in {os.path.basename(file)}")
                
                # === COORDINATOR TASKS INSERTION ===
                # Create comparison keys for coordinator tasks
                valid_df['coordinator_comparison_key'] = (
                    str(user_id) + '|' +
                    valid_df['normalized_patient_id'].astype(str) + '|' +
                    valid_df['normalized_date'].astype(str) + '|' +
                    'RVZ'
                )
                
                # Filter out existing coordinator tasks
                new_coordinator_tasks = valid_df[~valid_df['coordinator_comparison_key'].isin(existing_coordinator_keys)]
                
                if len(new_coordinator_tasks) > 0:
                    # Prepare data for coordinator_tasks table
                    notes_column = new_coordinator_tasks.get('Notes', pd.Series([''] * len(new_coordinator_tasks)))
                    if hasattr(notes_column, 'fillna'):
                        notes_column = notes_column.fillna('')
                    
                    coordinator_tasks_data = pd.DataFrame({
                        'coordinator_id': user_id,
                        'patient_id': new_coordinator_tasks['normalized_patient_id'],
                        'task_date': new_coordinator_tasks['normalized_date'],
                        'duration_minutes': new_coordinator_tasks['duration_minutes'].astype(int),
                        'task_type': 'RVZ',
                        'notes': notes_column
                    })
                    
                    all_new_coordinator_tasks.append(coordinator_tasks_data)
                    logger.info(f"Found {len(new_coordinator_tasks)} new RVZ coordinator tasks in {os.path.basename(file)}")
                
                self.stats['provider_processed'] += len(df)
                
            except Exception as e:
                logger.error(f"Error processing {file}: {e}")
        
        # Combine and return results
        final_provider_tasks = pd.DataFrame()
        final_coordinator_tasks = pd.DataFrame()
        
        if all_new_provider_tasks:
            final_provider_tasks = pd.concat(all_new_provider_tasks, ignore_index=True)
            self.stats['provider_new'] = len(final_provider_tasks)
            logger.info(f"Total new Provider tasks to import: {len(final_provider_tasks)}")
        
        if all_new_coordinator_tasks:
            final_coordinator_tasks = pd.concat(all_new_coordinator_tasks, ignore_index=True)
            logger.info(f"Total new Coordinator tasks from RVZ to import: {len(final_coordinator_tasks)}")
        
        return final_provider_tasks, final_coordinator_tasks
    
    def normalize_zmo_file(self):
        """Normalize ZMO_MAIN.csv file and identify new patients"""
        logger.info("=== NORMALIZING ZMO FILE ===")
        
        zmo_file = os.path.join(self.downloads_dir, "ZMO_MAIN.csv")
        
        if not os.path.exists(zmo_file):
            logger.warning(f"ZMO_MAIN.csv not found in {self.downloads_dir}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(zmo_file)
            logger.info(f"Loaded {len(df)} records from ZMO_MAIN.csv")
            
            # Get existing patients for comparison
            existing_patients = pd.read_sql_query("""
                SELECT patient_id, last_first_dob
                FROM patients
            """, self.conn)
            
            # Normalize patient data
            df['normalized_patient_id'] = df['Pt Name'].apply(self.normalize_patient_id)
            df['normalized_dob'] = df['DOB'].apply(self.normalize_date)
            
            # Create comparison key (patient_name + DOB)
            df['comparison_key'] = (
                df['normalized_patient_id'].astype(str) + ' ' +
                df['normalized_dob'].fillna('').astype(str)
            )
            
            existing_patients['comparison_key'] = existing_patients['last_first_dob'].astype(str)
            existing_keys = set(existing_patients['comparison_key'].tolist())
            
            # Filter valid records
            valid_df = df[
                (df['normalized_patient_id'].notna()) &
                (df['normalized_dob'].notna())
            ]
            
            # Filter out existing patients
            new_patients = valid_df[~valid_df['comparison_key'].isin(existing_keys)]
            
            if len(new_patients) > 0:
                # Prepare final data structure with safe fillna handling
                def safe_fillna(column_name, default=''):
                    col = new_patients.get(column_name, pd.Series([default] * len(new_patients)))
                    return col.fillna(default) if hasattr(col, 'fillna') else col
                
                # Only include columns that exist in the patients table
                normalized_patients = pd.DataFrame({
                    'patient_id': new_patients['normalized_patient_id'],
                    'last_first_dob': new_patients['comparison_key']
                })
                
                self.stats['zmo_processed'] = len(df)
                self.stats['zmo_new'] = len(new_patients)
                logger.info(f"Found {len(new_patients)} new patients to import")
                return normalized_patients
            else:
                logger.info("No new patients found in ZMO_MAIN.csv")
                self.stats['zmo_processed'] = len(df)
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error processing ZMO_MAIN.csv: {e}")
            return pd.DataFrame()
    
    def import_data(self, cmlog_data, provider_data, rvz_coordinator_data, zmo_data):
        """Import normalized data into database tables"""
        logger.info("=== IMPORTING NEW DATA ===")
        
        try:
            # Import coordinator tasks from CMLog
            if not cmlog_data.empty:
                cmlog_data.to_sql('coordinator_tasks', self.conn, if_exists='append', index=False)
                logger.info(f"Imported {len(cmlog_data)} coordinator tasks from CMLog")
            
            # Import coordinator tasks from RVZ
            if not rvz_coordinator_data.empty:
                rvz_coordinator_data.to_sql('coordinator_tasks', self.conn, if_exists='append', index=False)
                logger.info(f"Imported {len(rvz_coordinator_data)} coordinator tasks from RVZ")
            
            # Import provider tasks
            if not provider_data.empty:
                provider_data.to_sql('provider_tasks', self.conn, if_exists='append', index=False)
                logger.info(f"Imported {len(provider_data)} provider tasks")
            
            # Import patients
            if not zmo_data.empty:
                zmo_data.to_sql('patients', self.conn, if_exists='append', index=False)
                logger.info(f"Imported {len(zmo_data)} new patients")
            
            self.conn.commit()
            logger.info("All data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            self.conn.rollback()
            raise
    
    def run_normalization_and_import(self):
        """Run the complete normalization and import process"""
        logger.info("=== STARTING FRESH DATA NORMALIZATION AND IMPORT ===")
        start_time = datetime.now()
        
        try:
            # Normalize all data types
            cmlog_data = self.normalize_cmlog_files()
            provider_data, rvz_coordinator_data = self.normalize_provider_files()
            zmo_data = self.normalize_zmo_file()
            
            # Import new data
            self.import_data(cmlog_data, provider_data, rvz_coordinator_data, zmo_data)
            
            # Print summary
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("=== NORMALIZATION AND IMPORT COMPLETE ===")
            logger.info(f"Processing time: {duration}")
            logger.info(f"CMLog: {self.stats['cmlog_processed']} processed, {self.stats['cmlog_new']} new")
            logger.info(f"Provider: {self.stats['provider_processed']} processed, {self.stats['provider_new']} new")
            logger.info(f"ZMO: {self.stats['zmo_processed']} processed, {self.stats['zmo_new']} new")
            logger.info(f"RVZ Coordinator tasks: {len(rvz_coordinator_data) if not rvz_coordinator_data.empty else 0} new")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Error in normalization and import process: {e}")
            raise
        finally:
            self.conn.close()

if __name__ == "__main__":
    normalizer = FreshDataNormalizer()
    try:
        stats = normalizer.run_normalization_and_import()
        print("\n=== FINAL SUMMARY ===")
        print(f"CMLog files: {stats['cmlog_processed']} processed, {stats['cmlog_new']} new tasks imported")
        print(f"Provider files: {stats['provider_processed']} processed, {stats['provider_new']} new tasks imported")
        print(f"ZMO file: {stats['zmo_processed']} processed, {stats['zmo_new']} new patients imported")
        print("\nNormalization and import completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)