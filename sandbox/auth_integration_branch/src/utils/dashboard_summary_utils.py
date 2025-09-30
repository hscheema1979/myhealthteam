"""
Utility scripts for creating and refreshing dashboard summary tables
in production.db without deleting or overwriting non-dashboard tables.
"""

import sqlite3
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DashboardSummaryUtils:
    def __init__(self, db_path='production.db'):
        self.db_path = db_path
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def get_dashboard_tables(self):
        """Get list of all dashboard tables"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'dashboard_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    
    def get_non_dashboard_tables(self):
        """Get list of all non-dashboard tables that should be preserved"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'dashboard_%' 
            AND name NOT LIKE '%summary%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    
    def create_dashboard_tables(self):
        """Create all dashboard summary tables if they don't exist"""
        if not self.connection:
            self.connect()
        
        # Define dashboard summary tables
        dashboard_tables = [
            """
            CREATE TABLE IF NOT EXISTS "dashboard_provider_monthly_summary" (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                total_tasks_completed INTEGER DEFAULT 0,
                total_time_spent_minutes INTEGER DEFAULT 0,
                average_task_completion_time_minutes REAL DEFAULT 0.0,
                total_patients_served INTEGER DEFAULT 0,
                max_patients_allowed INTEGER DEFAULT 60,
                patients_assigned INTEGER DEFAULT 0,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (provider_id) REFERENCES "providers"(provider_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "dashboard_coordinator_monthly_summary" (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                coordinator_id INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                total_minutes INTEGER DEFAULT 0,
                total_minutes_per_patient REAL DEFAULT 0.0,
                total_tasks_completed INTEGER DEFAULT 0,
                average_daily_tasks REAL DEFAULT 0.0,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coordinator_id) REFERENCES "coordinators"(coordinator_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "dashboard_patient_assignment_summary" (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                patient_id INTEGER NOT NULL,
                patient_name TEXT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                total_minutes INTEGER NOT NULL,
                billing_code_id INTEGER,
                billing_code TEXT,
                billing_code_description TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (billing_code_id) REFERENCES coordinator_billing_codes(code_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "dashboard_task_summary" (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_category TEXT NOT NULL,
                total_tasks INTEGER DEFAULT 0,
                total_minutes INTEGER DEFAULT 0,
                average_minutes_per_task REAL DEFAULT 0.0,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "dashboard_region_patient_assignment_summary" (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                region_id INTEGER NOT NULL,
                patient_id INTEGER NOT NULL,
                patient_name TEXT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                total_minutes INTEGER NOT NULL,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (region_id) REFERENCES "regions"(region_id)
            );
            """
        ]
        
        try:
            cursor = self.connection.cursor()
            for table_sql in dashboard_tables:
                cursor.execute(table_sql)
            self.connection.commit()
            logger.info("Dashboard summary tables created/verified successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating dashboard tables: {e}")
            return False
    
    def refresh_dashboard_table(self, table_name):
        """Refresh a specific dashboard table with current data"""
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            # Clear existing data for this table
            cursor.execute(f"DELETE FROM {table_name}")
            
            # Generate and execute appropriate refresh query based on table name
            refresh_queries = {
                "dashboard_provider_monthly_summary": self._refresh_provider_monthly_summary,
                "dashboard_coordinator_monthly_summary": self._refresh_coordinator_monthly_summary,
                "dashboard_patient_assignment_summary": self._refresh_patient_assignment_summary,
                "dashboard_task_summary": self._refresh_task_summary,
                "dashboard_region_patient_assignment_summary": self._refresh_region_patient_assignment_summary
            }
            
            if table_name in refresh_queries:
                refresh_queries[table_name](cursor)
                self.connection.commit()
                logger.info(f"Successfully refreshed {table_name}")
                return True
            else:
                logger.warning(f"No refresh function defined for table: {table_name}")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Error refreshing {table_name}: {e}")
            return False
    
    def refresh_all_dashboard_tables(self):
        """Refresh all dashboard summary tables"""
        if not self.connection:
            self.connect()
        
        dashboard_tables = self.get_dashboard_tables()
        logger.info(f"Refreshing {len(dashboard_tables)} dashboard tables")
        
        success_count = 0
        for table_name in dashboard_tables:
            if self.refresh_dashboard_table(table_name):
                success_count += 1
        
        logger.info(f"Successfully refreshed {success_count}/{len(dashboard_tables)} dashboard tables")
        return success_count == len(dashboard_tables)
    
    def _refresh_provider_monthly_summary(self, cursor):
        """Refresh provider monthly summary table"""
        query = """
        INSERT INTO dashboard_provider_monthly_summary 
        (provider_id, month, year, total_tasks_completed, total_time_spent_minutes, 
         average_task_completion_time_minutes, total_patients_served, patients_assigned)
        SELECT 
            pt.provider_id,
            strftime('%m', pt.task_date) as month,
            strftime('%Y', pt.task_date) as year,
            COUNT(*) as total_tasks_completed,
            SUM(pt.minutes_of_service) as total_time_spent_minutes,
            AVG(pt.minutes_of_service) as average_task_completion_time_minutes,
            COUNT(DISTINCT pt.patient_id) as total_patients_served,
            COUNT(DISTINCT pt.patient_id) as patients_assigned
        FROM provider_tasks pt
        WHERE pt.task_date IS NOT NULL AND pt.task_date != ''
        GROUP BY pt.provider_id, strftime('%m', pt.task_date), strftime('%Y', pt.task_date)
        """
        cursor.execute(query)
    
    def _refresh_coordinator_monthly_summary(self, cursor):
        """Refresh coordinator monthly summary table"""
        query = """
        INSERT INTO dashboard_coordinator_monthly_summary 
        (coordinator_id, month, year, total_minutes, total_minutes_per_patient, 
         total_tasks_completed, average_daily_tasks)
        SELECT 
            CAST(ct.coordinator_id AS INTEGER) as coordinator_id,
            CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER) as month,
            CAST('20' || SUBSTR(ct.task_date, -2) AS INTEGER) as year,
            SUM(ct.duration_minutes) as total_minutes,
            CASE 
                WHEN COUNT(DISTINCT ct.patient_id) > 0 
                THEN SUM(ct.duration_minutes) * 1.0 / COUNT(DISTINCT ct.patient_id) 
                ELSE 0 
            END as total_minutes_per_patient,
            COUNT(*) as total_tasks_completed,
            COUNT(*) * 1.0 / 30.0 as average_daily_tasks
        FROM coordinator_tasks ct
        WHERE ct.task_date IS NOT NULL AND ct.task_date != ''
        AND ct.coordinator_id IS NOT NULL AND ct.coordinator_id != ''
        AND ct.coordinator_id GLOB '[0-9]*'
        AND ct.duration_minutes IS NOT NULL AND ct.duration_minutes > 0
        GROUP BY 
            CAST(ct.coordinator_id AS INTEGER),
            CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER),
            CAST('20' || SUBSTR(ct.task_date, -2) AS INTEGER)
        HAVING coordinator_id IS NOT NULL AND coordinator_id > 0
        """
    
    def _refresh_patient_assignment_summary(self, cursor):
        """Refresh patient assignment summary table"""
        query = """
        INSERT INTO dashboard_patient_assignment_summary 
        (user_id, patient_id, patient_name, year, month, total_minutes, 
         billing_code_id, billing_code, billing_code_description)
        SELECT 
            upa.user_id,
            upa.patient_id,
            p.first_name || ' ' || p.last_name as patient_name,
            strftime('%Y', pa.assignment_date) as year,
            strftime('%m', pa.assignment_date) as month,
            SUM(ct.duration_minutes) as total_minutes,
            NULL as billing_code_id,
            NULL as billing_code,
            NULL as billing_code_description
        FROM user_patient_assignments upa
        JOIN patient_assignments pa ON upa.patient_id = pa.patient_id
        JOIN coordinator_tasks ct ON pa.assignment_id = ct.coordinator_task_id
        JOIN patients p ON upa.patient_id = p.patient_id
        WHERE pa.assignment_date IS NOT NULL AND pa.assignment_date != ''
        GROUP BY upa.user_id, upa.patient_id, p.first_name, p.last_name, 
                 strftime('%Y', pa.assignment_date), strftime('%m', pa.assignment_date)
        """
        cursor.execute(query)
    
    def _refresh_task_summary(self, cursor):
        """Refresh task summary table"""
        query = """
        INSERT INTO dashboard_task_summary 
        (task_category, total_tasks, total_minutes, average_minutes_per_task, year, month)
        SELECT 
            td.task_category,
            COUNT(*) as total_tasks,
            SUM(pt.minutes_of_service) as total_minutes,
            AVG(pt.minutes_of_service) as average_minutes_per_task,
            strftime('%Y', pt.task_date) as year,
            strftime('%m', pt.task_date) as month
        FROM provider_tasks pt
        JOIN task_definitions td ON pt.task_definition_id = td.task_definition_id
        WHERE pt.task_date IS NOT NULL AND pt.task_date != ''
        GROUP BY td.task_category, strftime('%Y', pt.task_date), strftime('%m', pt.task_date)
        """
        cursor.execute(query)
    
    def _refresh_region_patient_assignment_summary(self, cursor):
        """Refresh region patient assignment summary table"""
        query = """
        INSERT INTO dashboard_region_patient_assignment_summary 
        (region_id, patient_id, patient_name, year, month, total_minutes)
        SELECT 
            r.region_id,
            p.patient_id,
            p.first_name || ' ' || p.last_name as patient_name,
            strftime('%Y', pa.assignment_date) as year,
            strftime('%m', pa.assignment_date) as month,
            SUM(ct.duration_minutes) as total_minutes
        FROM regions r
        JOIN patient_assignments pa ON r.region_id = pa.region_id
        JOIN patients p ON pa.patient_id = p.patient_id
        JOIN coordinator_tasks ct ON pa.assignment_id = ct.coordinator_task_id
        WHERE pa.assignment_date IS NOT NULL AND pa.assignment_date != ''
        GROUP BY r.region_id, p.patient_id, p.first_name, p.last_name, 
                 strftime('%Y', pa.assignment_date), strftime('%m', pa.assignment_date)
        """
        cursor.execute(query)
    
    def get_table_info(self, table_name):
        """Get information about a specific table"""
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            return {
                'columns': columns,
                'row_count': row_count
            }
        except sqlite3.Error as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return None
    
    def backup_database(self, backup_path=None):
        """Create a backup of the current database"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"production_backup_{timestamp}.db"
        
        try:
            # Copy the database file
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return False

def main():
    """Main function to demonstrate usage"""
    utils = DashboardSummaryUtils()
    
    print("Dashboard Summary Utilities")
    print("=" * 40)
    
    # Connect to database
    if not utils.connect():
        print("Failed to connect to database")
        return
    
    try:
        # Show dashboard tables
        dashboard_tables = utils.get_dashboard_tables()
        print(f"Dashboard tables found: {dashboard_tables}")
        
        # Show non-dashboard tables
        non_dashboard_tables = utils.get_non_dashboard_tables()
        print(f"Non-dashboard tables (to preserve): {len(non_dashboard_tables)} tables")
        
        # Create dashboard tables if they don't exist
        print("\nCreating/verifying dashboard tables...")
        if utils.create_dashboard_tables():
            print("✓ Dashboard tables created/verified successfully")
        else:
            print("✗ Failed to create dashboard tables")
        
        # Show table information
        print("\nTable information:")
        for table in dashboard_tables[:2]:  # Show first 2 tables
            info = utils.get_table_info(table)
            if info:
                print(f"  {table}: {info['row_count']} rows, {len(info['columns'])} columns")
        
        # Example of refreshing tables (uncomment to use)
        # print("\nRefreshing all dashboard tables...")
        # utils.refresh_all_dashboard_tables()
        
    finally:
        utils.disconnect()

if __name__ == "__main__":
    main()
