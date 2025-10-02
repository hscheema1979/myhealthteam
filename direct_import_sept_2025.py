#!/usr/bin/env python3
"""
Direct Import Script for September 27-30, 2025 Data
Bypasses SOURCE tables and imports directly to core monthly tables.
Handles staff mapping and monthly table structure.
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime, date
from pathlib import Path
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('direct_import_sept_2025.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DirectImportSept2025:
    """Direct import handler for September 27-30, 2025 data"""
    
    def __init__(self, db_path='production.db'):
        self.db_path = db_path
        self.target_dates = ['2025-09-27', '2025-09-28', '2025-09-29', '2025-09-30']
        self.staff_mapping = {}
        self.load_staff_mapping()
    
    def load_staff_mapping(self):
        """Load staff code to user_id mapping from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT scm.staff_code, scm.user_id, u.full_name
                FROM staff_code_mapping scm
                LEFT JOIN users u ON scm.user_id = u.user_id
                WHERE scm.confidence_level >= 8
                """
                df = pd.read_sql_query(query, conn)
                
                for _, row in df.iterrows():
                    self.staff_mapping[row['staff_code']] = {
                        'user_id': row['user_id'],
                        'full_name': row['full_name']
                    }
                
                logger.info(f"Loaded {len(self.staff_mapping)} staff mappings")
                
        except Exception as e:
            logger.error(f"Error loading staff mapping: {e}")
            raise
    
    def normalize_patient_id(self, patient_id):
        """Normalize patient ID to standard format"""
        if pd.isna(patient_id) or patient_id == '':
            return None
        
        # Convert to string and strip whitespace
        patient_id = str(patient_id).strip()
        
        # Remove common prefixes and normalize
        patient_id = re.sub(r'^(MRN|mrn|MR|mr)[-_\s]*', '', patient_id, flags=re.IGNORECASE)
        patient_id = re.sub(r'[^\w]', '', patient_id)  # Remove non-alphanumeric
        
        return patient_id.upper() if patient_id else None
    
    def normalize_date(self, date_value):
        """Normalize date to YYYY-MM-DD format"""
        if pd.isna(date_value):
            return None
        
        try:
            if isinstance(date_value, str):
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d']:
                    try:
                        return datetime.strptime(date_value, fmt).strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            elif isinstance(date_value, (datetime, date)):
                return date_value.strftime('%Y-%m-%d')
            
            return str(date_value)
        except Exception:
            return None
    
    def map_staff_code(self, staff_code):
        """Map staff code to user_id and full_name"""
        if pd.isna(staff_code) or staff_code == '':
            return None, None
        
        staff_code = str(staff_code).strip().upper()
        mapping = self.staff_mapping.get(staff_code)
        
        if mapping:
            return mapping['user_id'], mapping['full_name']
        else:
            logger.warning(f"No mapping found for staff code: {staff_code}")
            return None, None
    
    def import_coordinator_tasks(self, csv_file_path):
        """Import coordinator tasks directly to coordinator_tasks_2025_09"""
        logger.info(f"Importing coordinator tasks from {csv_file_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            logger.info(f"Read {len(df)} rows from CSV")
            
            # Filter for target dates (Sept 27-30, 2025)
            df['normalized_date'] = df['task_date'].apply(self.normalize_date)
            df_filtered = df[df['normalized_date'].isin(self.target_dates)]
            logger.info(f"Filtered to {len(df_filtered)} rows for Sept 27-30, 2025")
            
            if len(df_filtered) == 0:
                logger.warning("No data found for target dates")
                return
            
            # Prepare data for import
            import_data = []
            for _, row in df_filtered.iterrows():
                # Map staff code to coordinator_id
                coordinator_id, coordinator_name = self.map_staff_code(row.get('staff_code', ''))
                
                import_row = {
                    'coordinator_id': coordinator_id,
                    'patient_id': self.normalize_patient_id(row.get('patient_id', '')),
                    'task_date': row['normalized_date'],
                    'duration_minutes': int(row.get('duration_minutes', 0)) if pd.notna(row.get('duration_minutes')) else 0,
                    'task_type': str(row.get('task_type', '')).strip(),
                    'notes': str(row.get('notes', '')).strip(),
                    'source_system': 'CMLog',
                    'imported_at': datetime.now().isoformat()
                }
                import_data.append(import_row)
            
            # Insert into database
            with sqlite3.connect(self.db_path) as conn:
                insert_query = """
                INSERT INTO coordinator_tasks_2025_09 
                (coordinator_id, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                for row in import_data:
                    conn.execute(insert_query, (
                        row['coordinator_id'],
                        row['patient_id'],
                        row['task_date'],
                        row['duration_minutes'],
                        row['task_type'],
                        row['notes'],
                        row['source_system'],
                        row['imported_at']
                    ))
                
                conn.commit()
                logger.info(f"Successfully imported {len(import_data)} coordinator task records")
                
        except Exception as e:
            logger.error(f"Error importing coordinator tasks: {e}")
            raise
    
    def import_provider_tasks(self, csv_file_path):
        """Import provider tasks directly to provider_tasks_2025_09"""
        logger.info(f"Importing provider tasks from {csv_file_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            logger.info(f"Read {len(df)} rows from CSV")
            
            # Filter for target dates (Sept 27-30, 2025)
            df['normalized_date'] = df['task_date'].apply(self.normalize_date)
            df_filtered = df[df['normalized_date'].isin(self.target_dates)]
            logger.info(f"Filtered to {len(df_filtered)} rows for Sept 27-30, 2025")
            
            if len(df_filtered) == 0:
                logger.warning("No data found for target dates")
                return
            
            # Prepare data for import
            import_data = []
            for _, row in df_filtered.iterrows():
                # Map staff code to provider info
                user_id, provider_name = self.map_staff_code(row.get('staff_code', ''))
                
                import_row = {
                    'provider_task_id': None,  # Auto-increment
                    'task_id': int(row.get('task_id', 0)) if pd.notna(row.get('task_id')) else None,
                    'provider_id': int(row.get('provider_id', 0)) if pd.notna(row.get('provider_id')) else None,
                    'provider_name': provider_name or str(row.get('provider_name', '')).strip(),
                    'patient_name': str(row.get('patient_name', '')).strip(),
                    'user_id': user_id,
                    'patient_id': self.normalize_patient_id(row.get('patient_id', '')),
                    'status': str(row.get('status', 'completed')).strip(),
                    'notes': str(row.get('notes', '')).strip(),
                    'minutes_of_service': int(row.get('minutes_of_service', 0)) if pd.notna(row.get('minutes_of_service')) else 0,
                    'billing_code_id': int(row.get('billing_code_id', 0)) if pd.notna(row.get('billing_code_id')) else None,
                    'created_date': datetime.now().timestamp(),
                    'updated_date': datetime.now().timestamp(),
                    'task_date': datetime.strptime(row['normalized_date'], '%Y-%m-%d').timestamp(),
                    'month': 9,
                    'year': 2025,
                    'billing_code': str(row.get('billing_code', '')).strip(),
                    'billing_code_description': str(row.get('billing_code_description', '')).strip(),
                    'task_description': str(row.get('task_description', '')).strip(),
                    'source_system': 'PSL/RVZ',
                    'imported_at': datetime.now().isoformat()
                }
                import_data.append(import_row)
            
            # Insert into database
            with sqlite3.connect(self.db_path) as conn:
                insert_query = """
                INSERT INTO provider_tasks_2025_09 
                (task_id, provider_id, provider_name, patient_name, user_id, patient_id, status, notes, 
                 minutes_of_service, billing_code_id, created_date, updated_date, task_date, month, year,
                 billing_code, billing_code_description, task_description, source_system, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                for row in import_data:
                    conn.execute(insert_query, (
                        row['task_id'],
                        row['provider_id'],
                        row['provider_name'],
                        row['patient_name'],
                        row['user_id'],
                        row['patient_id'],
                        row['status'],
                        row['notes'],
                        row['minutes_of_service'],
                        row['billing_code_id'],
                        row['created_date'],
                        row['updated_date'],
                        row['task_date'],
                        row['month'],
                        row['year'],
                        row['billing_code'],
                        row['billing_code_description'],
                        row['task_description'],
                        row['source_system'],
                        row['imported_at']
                    ))
                
                conn.commit()
                logger.info(f"Successfully imported {len(import_data)} provider task records")
                
        except Exception as e:
            logger.error(f"Error importing provider tasks: {e}")
            raise
    
    def import_patients(self, csv_file_path):
        """Import patient data directly to patients table"""
        logger.info(f"Importing patients from {csv_file_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            logger.info(f"Read {len(df)} rows from CSV")
            
            # Prepare data for import
            import_data = []
            for _, row in df.iterrows():
                patient_id = self.normalize_patient_id(row.get('patient_id', ''))
                if not patient_id:
                    continue
                
                import_row = {
                    'patient_id': patient_id,
                    'first_name': str(row.get('first_name', '')).strip(),
                    'last_name': str(row.get('last_name', '')).strip(),
                    'date_of_birth': self.normalize_date(row.get('date_of_birth')),
                    'gender': str(row.get('gender', '')).strip(),
                    'phone_primary': str(row.get('phone', '')).strip(),
                    'email': str(row.get('email', '')).strip(),
                    'address_street': str(row.get('address', '')).strip(),
                    'address_city': str(row.get('city', '')).strip(),
                    'address_state': str(row.get('state', '')).strip(),
                    'address_zip': str(row.get('zip_code', '')).strip(),
                    'insurance_primary': str(row.get('insurance_info', '')).strip(),
                    'chronic_conditions_onboarding': str(row.get('medical_conditions', '')).strip(),
                    'created_date': datetime.now().isoformat(),
                    'updated_date': datetime.now().isoformat()
                }
                import_data.append(import_row)
            
            # Insert into database (with conflict resolution)
            with sqlite3.connect(self.db_path) as conn:
                insert_query = """
                INSERT OR REPLACE INTO patients 
                (patient_id, first_name, last_name, date_of_birth, gender, phone_primary, email, 
                 address_street, address_city, address_state, address_zip, insurance_primary, chronic_conditions_onboarding, created_date, updated_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                for row in import_data:
                    conn.execute(insert_query, (
                        row['patient_id'],
                        row['first_name'],
                        row['last_name'],
                        row['date_of_birth'],
                        row['gender'],
                        row['phone_primary'],
                        row['email'],
                        row['address_street'],
                        row['address_city'],
                        row['address_state'],
                        row['address_zip'],
                        row['insurance_primary'],
                        row['chronic_conditions_onboarding'],
                        row['created_date'],
                        row['updated_date']
                    ))
                
                conn.commit()
                logger.info(f"Successfully imported {len(import_data)} patient records")
                
        except Exception as e:
            logger.error(f"Error importing patients: {e}")
            raise
    
    def run_import(self, coordinator_csv=None, provider_csv=None, patient_csv=None):
        """Run the complete import process"""
        logger.info("Starting direct import for September 27-30, 2025")
        
        try:
            if coordinator_csv and Path(coordinator_csv).exists():
                self.import_coordinator_tasks(coordinator_csv)
            
            if provider_csv and Path(provider_csv).exists():
                self.import_provider_tasks(provider_csv)
            
            if patient_csv and Path(patient_csv).exists():
                self.import_patients(patient_csv)
            
            logger.info("Direct import completed successfully")
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise

def main():
    """Main execution function"""
    importer = DirectImportSept2025()
    
    # Example usage - update paths as needed
    importer.run_import(
        coordinator_csv='coordinator_tasks_sept_27_30.csv',
        provider_csv='provider_tasks_sept_27_30.csv',
        patient_csv='patients_sept_27_30.csv'
    )

if __name__ == "__main__":
    main()