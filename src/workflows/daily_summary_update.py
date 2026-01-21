"""
Daily Summary Update Workflow

Automated script to update billing and payroll summary tables.
Runs daily at 5:00 AM via Windows Task Scheduler.

Updates:
- Weekly Provider Billing Summary (provider_weekly_summary_with_billing)
- Weekly Provider Payroll Summary
- Monthly Coordinator Billing Summary

Features:
- Processes only new/updated records
- Maintains data integrity during updates
- Includes error handling and logging
- Preserves historical data
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
import logging

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src import database

# Configure logging
LOG_DIR = os.path.join(project_root, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'daily_summary_update.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(project_root, 'production.db')

def get_connection():
    """Get database connection with row factory for dict-like access"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_week_dates(target_date=None):
    """Get the week start (Monday) and end (Sunday) dates for a given date"""
    if target_date is None:
        target_date = datetime.now().date()
    
    # Find Monday of the week
    days_since_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    return week_start, week_end

def update_weekly_provider_billing_summary(conn):
    """
    Update the provider_weekly_summary_with_billing table.
    Aggregates provider tasks by week and calculates billing summaries.
    """
    logger.info("Updating Weekly Provider Billing Summary...")
    
    cursor = conn.cursor()
    
    # Get current week dates
    week_start, week_end = get_week_dates()
    week_start_str = week_start.isoformat()
    week_end_str = week_end.isoformat()
    
    # Get year and week number
    year = week_start.year
    week_number = week_start.isocalendar()[1]
    
    # Get all provider task tables for current and previous months
    current_month = datetime.now().strftime('%Y_%m')
    previous_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y_%m')
    
    task_tables = []
    for month in [current_month, previous_month]:
        table_name = f'provider_tasks_{month}'
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name = ?
        """, (table_name,))
        if cursor.fetchone():
            task_tables.append(table_name)
    
    if not task_tables:
        logger.info("  No provider task tables found to process")
        return 0
    
    # Process each task table
    total_updated = 0
    
    for table_name in task_tables:
        logger.info(f"  Processing {table_name}...")
        
        # Get distinct providers with tasks in the date range
        cursor.execute(f"""
            SELECT DISTINCT provider_id, provider_name
            FROM {table_name}
            WHERE task_date >= ? AND task_date <= ?
        """, (week_start_str, week_end_str))
        
        providers = cursor.fetchall()
        
        for provider in providers:
            provider_id = provider['provider_id']
            provider_name = provider['provider_name']
            
            # Calculate summary metrics
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_tasks,
                    COALESCE(SUM(minutes_of_service), 0) as total_minutes,
                    COUNT(DISTINCT patient_id) as unique_patients,
                    billing_code,
                    billing_code_description
                FROM {table_name}
                WHERE provider_id = ? AND task_date >= ? AND task_date <= ?
                GROUP BY billing_code, billing_code_description
            """, (provider_id, week_start_str, week_end_str))
            
            billing_data = cursor.fetchall()
            
            for billing_row in billing_data:
                # Upsert into summary table (match actual schema)
                cursor.execute("""
                    INSERT OR REPLACE INTO provider_weekly_summary_with_billing
                    (provider_id, provider_name, week_start_date, week_end_date,
                     year, week_number, total_tasks_completed, total_time_spent_minutes,
                     billing_code, billing_code_description, updated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    provider_id,
                    provider_name,
                    week_start_str,
                    week_end_str,
                    year,
                    week_number,
                    billing_row['total_tasks'],
                    int(billing_row['total_minutes']),
                    billing_row['billing_code'],
                    billing_row['billing_code_description']
                ))
                
                total_updated += 1
    
    conn.commit()
    logger.info(f"  Updated {total_updated} billing summary records")
    return total_updated

def update_weekly_provider_payroll_summary(conn):
    """
    Update the provider weekly payroll summary.
    Tracks payment status and hours worked.
    """
    logger.info("Updating Weekly Provider Payroll Summary...")
    
    cursor = conn.cursor()
    
    # Get current week dates
    week_start, week_end = get_week_dates()
    week_start_str = week_start.isoformat()
    week_end_str = week_end.isoformat()
    
    # Get year and week number
    year = week_start.year
    week_number = week_start.isocalendar()[1]
    
    # Check if provider_weekly_payroll_status table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name = 'provider_weekly_payroll_status'
    """)
    if not cursor.fetchone():
        logger.info("  provider_weekly_payroll_status table does not exist, creating...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provider_weekly_payroll_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id INTEGER NOT NULL,
                provider_name TEXT,
                week_start_date DATE NOT NULL,
                week_end_date DATE NOT NULL,
                year INTEGER,
                week_number INTEGER,
                total_hours DECIMAL(10,2),
                hourly_rate DECIMAL(10,2),
                total_pay DECIMAL(10,2),
                paid_by_zen BOOLEAN DEFAULT 0,
                payment_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider_id, week_start_date)
            )
        """)
        conn.commit()
        logger.info("  Created provider_weekly_payroll_status table")
    
    # Get all provider task tables for current and previous months
    current_month = datetime.now().strftime('%Y_%m')
    previous_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y_%m')
    
    task_tables = []
    for month in [current_month, previous_month]:
        table_name = f'provider_tasks_{month}'
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name = ?
        """, (table_name,))
        if cursor.fetchone():
            task_tables.append(table_name)
    
    if not task_tables:
        logger.info("  No provider task tables found to process")
        return 0
    
    # Process each task table
    total_updated = 0
    
    for table_name in task_tables:
        logger.info(f"  Processing {table_name}...")
        
        # Get distinct providers with tasks in the date range
        cursor.execute(f"""
            SELECT DISTINCT provider_id, provider_name
            FROM {table_name}
            WHERE task_date >= ? AND task_date <= ?
        """, (week_start_str, week_end_str))
        
        providers = cursor.fetchall()
        
        for provider in providers:
            provider_id = provider['provider_id']
            provider_name = provider['provider_name']
            
            # Calculate payroll metrics (convert minutes to hours)
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_tasks,
                    COALESCE(SUM(minutes_of_service), 0) / 60.0 as total_hours
                FROM {table_name}
                WHERE provider_id = ? AND task_date >= ? AND task_date <= ?
            """, (provider_id, week_start_str, week_end_str))
            
            payroll_data = cursor.fetchone()

            if payroll_data['total_tasks'] > 0:
                # Upsert into payroll summary table (match actual schema)
                cursor.execute("""
                    INSERT OR REPLACE INTO provider_weekly_payroll_status
                    (provider_id, provider_name, pay_week_start_date, pay_week_end_date,
                     pay_year, pay_week_number, task_count, total_minutes_of_service, updated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    provider_id,
                    provider_name,
                    week_start_str,
                    week_end_str,
                    year,
                    week_number,
                    payroll_data['total_tasks'],
                    int(payroll_data['total_hours'] * 60)  # Convert hours back to minutes
                ))
                
                total_updated += 1
    
    conn.commit()
    logger.info(f"  Updated {total_updated} payroll summary records")
    return total_updated

def update_monthly_coordinator_billing_summary(conn):
    """
    Update monthly coordinator billing summary tables.
    Aggregates coordinator tasks by month.
    """
    logger.info("Updating Monthly Coordinator Billing Summary...")
    
    cursor = conn.cursor()
    
    # Get current month dates
    today = datetime.now().date()
    month_start = today.replace(day=1)
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    year = today.year
    month = today.month
    
    month_start_str = month_start.isoformat()
    month_end_str = month_end.isoformat()
    
    # Get all coordinator task tables for current and previous months
    current_month = datetime.now().strftime('%Y_%m')
    previous_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y_%m')
    
    task_tables = []
    for month in [current_month, previous_month]:
        table_name = f'coordinator_tasks_{month}'
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name = ?
        """, (table_name,))
        if cursor.fetchone():
            task_tables.append(table_name)
    
    if not task_tables:
        logger.info("  No coordinator task tables found to process")
        return 0
    
    # Process each task table
    total_updated = 0
    
    for table_name in task_tables:
        logger.info(f"  Processing {table_name}...")
        
        # Get distinct coordinators with tasks in the date range
        cursor.execute(f"""
            SELECT DISTINCT coordinator_id, coordinator_name
            FROM {table_name}
            WHERE task_date >= ? AND task_date <= ?
        """, (month_start_str, month_end_str))
        
        coordinators = cursor.fetchall()
        
        for coord in coordinators:
            coordinator_id = coord['coordinator_id']
            coordinator_name = coord['coordinator_name']
            
            # Calculate summary metrics
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_tasks,
                    COALESCE(SUM(minutes_of_service), 0) as total_minutes,
                    COUNT(DISTINCT patient_id) as unique_patients,
                    SUM(CASE WHEN is_billed = 1 THEN 1 ELSE 0 END) as billed_tasks,
                    SUM(CASE WHEN is_paid = 1 THEN 1 ELSE 0 END) as paid_tasks,
                    SUM(CASE WHEN is_carried_over = 1 THEN 1 ELSE 0 END) as carried_over_tasks
                FROM {table_name}
                WHERE coordinator_id = ? AND task_date >= ? AND task_date <= ?
            """, (coordinator_id, month_start_str, month_end_str))
            
            summary_data = cursor.fetchone()
            
            # Upsert into monthly summary table
            cursor.execute("""
                INSERT OR REPLACE INTO coordinator_monthly_summary
                (coordinator_id, coordinator_name, year, month,
                 total_tasks_completed, total_time_spent_minutes,
                 unique_patients_served, billed_tasks, paid_tasks, carried_over_tasks,
                 updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                coordinator_id,
                coordinator_name,
                year,
                month,
                summary_data['total_tasks'],
                summary_data['total_minutes'],
                summary_data['unique_patients'],
                summary_data['billed_tasks'],
                summary_data['paid_tasks'],
                summary_data['carried_over_tasks']
            ))
            
            total_updated += 1
    
    conn.commit()
    logger.info(f"  Updated {total_updated} coordinator summary records")
    return total_updated

def run_daily_update():
    """Main function to run all daily summary updates"""
    start_time = datetime.now()
    logger.info("="*60)
    logger.info(f"Daily Summary Update Started at {start_time}")
    
    try:
        conn = get_connection()
        
        # Update all summary tables
        billing_count = update_weekly_provider_billing_summary(conn)
        payroll_count = update_weekly_provider_payroll_summary(conn)
        coordinator_count = update_monthly_coordinator_billing_summary(conn)
        
        conn.close()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("="*60)
        logger.info(f"Daily Summary Update Complete!")
        logger.info(f"  - Provider Billing Records: {billing_count}")
        logger.info(f"  - Provider Payroll Records: {payroll_count}")
        logger.info(f"  - Coordinator Summary Records: {coordinator_count}")
        logger.info(f"  - Duration: {duration:.2f} seconds")
        logger.info("="*60)
        
        return {
            'success': True,
            'billing_records': billing_count,
            'payroll_records': payroll_count,
            'coordinator_records': coordinator_count,
            'duration_seconds': duration
        }
        
    except Exception as e:
        logger.error(f"Error during daily summary update: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    result = run_daily_update()
    if result['success']:
        print(f"\n✓ Daily update completed successfully!")
        print(f"  - Provider Billing Records: {result['billing_records']}")
        print(f"  - Provider Payroll Records: {result['payroll_records']}")
        print(f"  - Coordinator Summary Records: {result['coordinator_records']}")
        sys.exit(0)
    else:
        print(f"\n✗ Daily update failed: {result['error']}")
        sys.exit(1)
