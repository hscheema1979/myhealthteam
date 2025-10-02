#!/usr/bin/env python3
"""
Analyze fresh downloaded data and perform differential imports
- Compare new data against existing database records
- Import only new patients, tasks, and updated last visit data
"""

import pandas as pd
import sqlite3
import glob
import os
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FreshDataAnalyzer:
    def __init__(self, downloads_dir="./downloads", db_path="./production.db"):
        self.downloads_dir = downloads_dir
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.validate_schema()
        
    def validate_schema(self):
        """Validate database schema before proceeding"""
        required_tables = ['patients', 'patient_panel', 'coordinator_tasks', 'provider_tasks', 'user_patient_assignments']
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in required_tables:
            if table not in existing_tables:
                raise Exception(f"Required table '{table}' not found in database")
                
        logger.info(f"Schema validation passed. Found tables: {existing_tables}")
        
    def get_current_counts(self):
        """Get current record counts from database"""
        counts = {}
        tables = ['patients', 'patient_panel', 'coordinator_tasks', 'provider_tasks', 'user_patient_assignments']
        
        for table in tables:
            query = f"SELECT COUNT(*) FROM {table}"
            counts[table] = self.conn.execute(query).fetchone()[0]
            
        logger.info(f"Current database counts: {counts}")
        return counts
    
    def analyze_fresh_patients(self):
        """Analyze ZMO_MAIN.csv for new patients"""
        zmo_file = os.path.join(self.downloads_dir, "ZMO_MAIN.csv")
        
        if not os.path.exists(zmo_file):
            logger.error(f"ZMO_MAIN.csv not found in {self.downloads_dir}")
            return None
            
        # Load fresh patient data
        fresh_patients = pd.read_csv(zmo_file)
        logger.info(f"Fresh patient data: {len(fresh_patients)} records")
        
        # Get existing patients from database (using correct column name)
        existing_patients = pd.read_sql_query(
            "SELECT patient_id, last_first_dob FROM patients", 
            self.conn
        )
        logger.info(f"Existing patients in DB: {len(existing_patients)} records")
        
        # Compare and find new patients using name+DOB as key
        # Fresh data: combine 'Pt Name' and 'DOB' to match 'last_first_dob' format
        fresh_patients['comparison_key'] = (
            fresh_patients['Pt Name'].astype(str).str.strip().str.upper() + ' ' + 
            fresh_patients['DOB'].astype(str).str.strip()
        )
        existing_patients['comparison_key'] = (
            existing_patients['last_first_dob'].astype(str).str.strip().str.upper()
        )
        
        new_patients = fresh_patients[~fresh_patients['comparison_key'].isin(existing_patients['comparison_key'])]
        logger.info(f"New patients found: {len(new_patients)} records")
        
        return {
            'fresh_total': len(fresh_patients),
            'existing_total': len(existing_patients),
            'new_count': len(new_patients),
            'new_patients': new_patients
        }
    
    def analyze_fresh_coordinator_tasks(self):
        """Analyze CMLog files for new coordinator tasks"""
        cmlog_files = glob.glob(os.path.join(self.downloads_dir, "CMLog_*.csv"))
        
        if not cmlog_files:
            logger.error(f"No CMLog files found in {self.downloads_dir}")
            return None
            
        # Combine all CMLog files
        all_tasks = []
        for file in cmlog_files:
            try:
                df = pd.read_csv(file)
                # Skip placeholder rows
                df = df[~df['Pt Name'].str.contains('Aaa, Aaa', na=False)]
                df = df[~df['Notes'].str.contains('Place holder', na=False)]
                # Remove empty rows
                df = df.dropna(subset=['Staff', 'Pt Name', 'Date Only'])
                all_tasks.append(df)
                logger.info(f"Loaded {len(df)} tasks from {os.path.basename(file)}")
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
                
        if not all_tasks:
            return None
            
        fresh_tasks = pd.concat(all_tasks, ignore_index=True)
        logger.info(f"Fresh coordinator tasks: {len(fresh_tasks)} records")
        
        # Get existing coordinator tasks (using correct column names)
        existing_tasks = pd.read_sql_query(
            "SELECT coordinator_id, patient_id, task_date FROM coordinator_tasks", 
            self.conn
        )
        logger.info(f"Existing coordinator tasks in DB: {len(existing_tasks)} records")
        
        # Create comparison keys (coordinator_id + patient_name + date)
        fresh_tasks['comparison_key'] = (
            fresh_tasks['Staff'].astype(str).str.strip() + '|' + 
            fresh_tasks['Pt Name'].astype(str).str.strip() + '|' + 
            fresh_tasks['Date Only'].astype(str).str.strip()
        )
        
        existing_tasks['comparison_key'] = (
            existing_tasks['coordinator_id'].astype(str).str.strip() + '|' + 
            existing_tasks['patient_id'].astype(str).str.strip() + '|' + 
            existing_tasks['task_date'].astype(str).str.strip()
        )
        
        new_tasks = fresh_tasks[~fresh_tasks['comparison_key'].isin(existing_tasks['comparison_key'])]
        logger.info(f"New coordinator tasks found: {len(new_tasks)} records")
        
        return {
            'fresh_total': len(fresh_tasks),
            'existing_total': len(existing_tasks),
            'new_count': len(new_tasks),
            'new_tasks': new_tasks
        }
    
    def analyze_fresh_provider_tasks(self):
        """Analyze PSL files for new provider tasks"""
        psl_files = glob.glob(os.path.join(self.downloads_dir, "PSL_ZEN-*.csv"))
        
        if not psl_files:
            logger.error(f"No PSL files found in {self.downloads_dir}")
            return None
            
        # Combine all PSL files
        all_tasks = []
        for file in psl_files:
            try:
                df = pd.read_csv(file)
                # Remove empty rows using correct column names
                df = df.dropna(subset=['Prov', 'Patient Last, First DOB', 'DOS'])
                all_tasks.append(df)
                logger.info(f"Loaded {len(df)} tasks from {os.path.basename(file)}")
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
                
        if not all_tasks:
            return None
            
        fresh_tasks = pd.concat(all_tasks, ignore_index=True)
        logger.info(f"Fresh provider tasks: {len(fresh_tasks)} records")
        
        # Get existing provider tasks (using correct column names)
        existing_tasks = pd.read_sql_query(
            "SELECT provider_id, patient_id, task_date FROM provider_tasks", 
            self.conn
        )
        logger.info(f"Existing provider tasks in DB: {len(existing_tasks)} records")
        
        # Create comparison keys (provider + patient + date)
        fresh_tasks['comparison_key'] = (
            fresh_tasks['Prov'].astype(str).str.strip() + '|' + 
            fresh_tasks['Patient Last, First DOB'].astype(str).str.strip() + '|' + 
            fresh_tasks['DOS'].astype(str).str.strip()
        )
        
        existing_tasks['comparison_key'] = (
            existing_tasks['provider_id'].astype(str).str.strip() + '|' + 
            existing_tasks['patient_id'].astype(str).str.strip() + '|' + 
            existing_tasks['task_date'].astype(str).str.strip()
        )
        
        new_tasks = fresh_tasks[~fresh_tasks['comparison_key'].isin(existing_tasks['comparison_key'])]
        logger.info(f"New provider tasks found: {len(new_tasks)} records")
        
        return {
            'fresh_total': len(fresh_tasks),
            'existing_total': len(existing_tasks),
            'new_count': len(new_tasks),
            'new_tasks': new_tasks
        }
    
    def run_analysis(self):
        """Run complete analysis of fresh data"""
        logger.info("Starting fresh data analysis...")
        
        # Get current database state
        initial_counts = self.get_current_counts()
        
        # Analyze each data type
        patient_analysis = self.analyze_fresh_patients()
        coordinator_analysis = self.analyze_fresh_coordinator_tasks()
        provider_analysis = self.analyze_fresh_provider_tasks()
        
        # Summary report
        summary = {
            'timestamp': datetime.now().isoformat(),
            'initial_counts': initial_counts,
            'patient_analysis': patient_analysis,
            'coordinator_analysis': coordinator_analysis,
            'provider_analysis': provider_analysis
        }
        
        logger.info("=== FRESH DATA ANALYSIS SUMMARY ===")
        if patient_analysis:
            logger.info(f"Patients - Fresh: {patient_analysis['fresh_total']}, "
                       f"Existing: {patient_analysis['existing_total']}, "
                       f"New: {patient_analysis['new_count']}")
        
        if coordinator_analysis:
            logger.info(f"Coordinator Tasks - Fresh: {coordinator_analysis['fresh_total']}, "
                       f"Existing: {coordinator_analysis['existing_total']}, "
                       f"New: {coordinator_analysis['new_count']}")
        
        if provider_analysis:
            logger.info(f"Provider Tasks - Fresh: {provider_analysis['fresh_total']}, "
                       f"Existing: {provider_analysis['existing_total']}, "
                       f"New: {provider_analysis['new_count']}")
        
        return summary
    
    def close(self):
        """Close database connection"""
        self.conn.close()

if __name__ == "__main__":
    analyzer = FreshDataAnalyzer()
    try:
        summary = analyzer.run_analysis()
        print("\nAnalysis complete! Check logs for detailed results.")
    finally:
        analyzer.close()