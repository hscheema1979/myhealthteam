"""
Weekly Billing Report Processor (P00)
This module handles the automated generation of weekly billing reports with carryover logic.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import logging
import sys
from typing import Dict, List, Tuple, Optional
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database import get_db_connection

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, 'weekly_billing_processor.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)

class WeeklyBillingProcessor:
    """Handles the weekly billing report generation and carryover logic."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_current_billing_week(self, target_date: Optional[datetime] = None) -> Tuple[str, str, str]:
        """
        Calculate the current billing week in YYYY-WW format.
        
        Args:
            target_date: Optional date to calculate week for. Defaults to current date.
            
        Returns:
            Tuple of (billing_week, week_start_date, week_end_date)
        """
        if target_date is None:
            target_date = datetime.now()
            
        # Calculate Monday of the current week
        days_since_monday = target_date.weekday()
        week_start = target_date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        # Format billing week as YYYY-WW
        week_number = week_start.isocalendar()[1]
        billing_week = f"{week_start.year}-{week_number:02d}"
        
        return (
            billing_week,
            week_start.strftime('%Y-%m-%d'),
            week_end.strftime('%Y-%m-%d')
        )
    
    def setup_billing_system(self) -> bool:
        """
        Initialize the billing system tables if they don't exist.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = get_db_connection()
            
            # Read and execute the schema creation script
            schema_file = os.path.join(os.path.dirname(__file__), '..', 'sql', 'create_weekly_billing_system.sql')
            
            if os.path.exists(schema_file):
                with open(schema_file, 'r') as f:
                    schema_sql = f.read()
                
                # Execute the schema creation
                conn.executescript(schema_sql)
                conn.commit()
                self.logger.info("Billing system schema created successfully")
                
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up billing system: {str(e)}")
            return False
    
    def migrate_existing_data(self) -> bool:
        """
        Migrate existing provider task data into the billing system.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = get_db_connection()
            
            # Read and execute the population script
            populate_file = os.path.join(os.path.dirname(__file__), '..', 'sql', 'populate_weekly_billing_system.sql')
            
            if os.path.exists(populate_file):
                with open(populate_file, 'r') as f:
                    populate_sql = f.read()
                
                # Execute the population script
                conn.executescript(populate_sql)
                conn.commit()
                self.logger.info("Existing data migrated successfully")
                
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error migrating existing data: {str(e)}")
            return False
    
    def process_weekly_billing(self, target_date: Optional[datetime] = None) -> Dict:
        """
        Process the weekly billing report for the specified date.
        
        Args:
            target_date: Date to process billing for. Defaults to current date.
            
        Returns:
            Dictionary with processing results
        """

        conn = None
        try:
            billing_week, week_start, week_end = self.get_current_billing_week(target_date)
            
            self.logger.info(f"Processing weekly billing for week {billing_week} ({week_start} to {week_end})")
            
            conn = get_db_connection()
            
            # Process weekly billing directly in Python instead of using SQL generator file
            self._process_weekly_billing_python(conn, billing_week, week_start, week_end)
            
            # Get summary results
            summary = self.get_billing_summary(billing_week, conn, None, None, None)
            
            self.logger.info(f"Weekly billing processed successfully for week {billing_week}")
            return {
                'success': True,
                'billing_week': billing_week,
                'week_start': week_start,
                'week_end': week_end,
                'summary': summary
            }
        except Exception as e:
            self.logger.error(f"Error processing weekly billing: {str(e)}")
            # Even if there's an error, we want to return a structure that won't break the dashboard
            # Make sure we have all the required fields even if we can't determine the exact week
            try:
                billing_week, week_start, week_end = self.get_current_billing_week(target_date)
            except:
                billing_week = None
                week_start = None
                week_end = None
                
            return {
                'success': False,
                'error': str(e),
                'billing_week': billing_week,
                'week_start': week_start,
                'week_end': week_end,
                'summary': {}
            }
        finally:
            if conn:
                conn.close()
    
    def get_billing_summary(self, billing_week: str, conn: sqlite3.Connection, provider_filter: str = None,
                          year_filter: str = None, status_filter: str = None) -> Dict:
        """
        Get billing summary for a specific week with optional filtering.
        
        Args:
            billing_week: Week in YYYY-WW format
            conn: Database connection
            provider_filter: Optional filter by provider name
            year_filter: Optional filter by year
            status_filter: Optional filter by billing status
            
        Returns:
            Dictionary with billing summary
        """
        try:
            # Build dynamic query with filters - use provider_task_billing_status which has the actual data
            summary_query = """
            SELECT
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN is_billed = 1 THEN 1 END) as total_billed_tasks,
                COUNT(CASE WHEN is_carried_over = 1 THEN 1 END) as total_carried_over_tasks,
                'Generated' as report_status
            FROM provider_task_billing_status
            WHERE 1=1
            """
            params = []
            
            if billing_week:
                summary_query += " AND billing_week = ?"
                params.append(billing_week)
                
            if year_filter:
                # Handle year filter - filter by year in week_start_date
                summary_query += " AND strftime('%Y', week_start_date) = ?"
                params.append(year_filter)
            
            summary_df = pd.read_sql_query(summary_query, conn, params=params)
            
            # Get provider breakdown with filters
            provider_query = """
            SELECT
                provider_id,
                provider_name,
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN is_billed = 1 THEN 1 END) as billed_tasks,
                COUNT(CASE WHEN billing_status = 'Not Billed' THEN 1 END) as not_billed_tasks,
                COUNT(CASE WHEN is_carried_over = 1 THEN 1 END) as carried_over_tasks,
                SUM(minutes_of_service) as total_minutes
            FROM provider_task_billing_status
            WHERE 1=1
            """
            params = []
            
            if billing_week:
                provider_query += " AND billing_week = ?"
                params.append(billing_week)
                
            if provider_filter:
                provider_query += " AND provider_name = ?"
                params.append(provider_filter)
                
            if year_filter:
                provider_query += " AND strftime('%Y', week_start_date) = ?"
                params.append(year_filter)
                
            if status_filter:
                provider_query += " AND billing_status = ?"
                params.append(status_filter)
                
            provider_query += " GROUP BY provider_id, provider_name ORDER BY provider_name"
            
            provider_df = pd.read_sql_query(provider_query, conn, params=params)
            
            # Get tasks requiring attention with filters
            attention_query = """
            SELECT
                provider_task_id,
                provider_name,
                patient_name,
                task_date,
                billing_code,
                minutes_of_service,
                billing_status
            FROM provider_task_billing_status
            WHERE 1=1
            """
            params = []
            
            if billing_week:
                attention_query += " AND billing_week = ?"
                params.append(billing_week)
                
            if provider_filter:
                attention_query += " AND provider_name = ?"
                params.append(provider_filter)
                
            if year_filter:
                attention_query += " AND strftime('%Y', week_start_date) = ?"
                params.append(year_filter)
                
            if status_filter:
                attention_query += " AND billing_status = ?"
                params.append(status_filter)
            else:
                attention_query += " AND billing_status = 'Not Billed' AND is_billed = 0"
                
            attention_query += " ORDER BY provider_name, task_date"
            
            attention_df = pd.read_sql_query(attention_query, conn, params=params)
            
            return {
                'overall': summary_df.to_dict('records')[0] if not summary_df.empty else {},
                'by_provider': provider_df.to_dict('records'),
                'attention_required': attention_df.to_dict('records')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting billing summary: {str(e)}")
            return {}
    
    def _process_weekly_billing_python(self, conn: sqlite3.Connection, billing_week: str, week_start: str, week_end: str):
        """
        Process weekly billing directly in Python without relying on SQL generator file.
        Handles carryover logic for unbilled tasks.
        
        Args:
            conn: Database connection
            billing_week: Week in YYYY-WW format
            week_start: Week start date in YYYY-MM-DD format
            week_end: Week end date in YYYY-MM-DD format
        """
        try:
            # Step 1: Create carryover entries for unbilled tasks from previous weeks
            carryover_query = """
            INSERT OR IGNORE INTO provider_task_billing_status (
                provider_task_id,
                provider_id,
                provider_name,
                patient_id,
                patient_name,
                task_date,
                billing_week,
                week_start_date,
                week_end_date,
                task_description,
                minutes_of_service,
                billing_code,
                billing_code_description,
                billing_status,
                is_billed,
                is_carried_over,
                original_billing_week,
                carryover_reason,
                created_date,
                billing_notes
            )
            SELECT
                pbs.provider_task_id,
                pbs.provider_id,
                pbs.provider_name,
                pbs.patient_id,
                pbs.patient_name,
                pbs.task_date,
                ? as billing_week,
                ? as week_start_date,
                ? as week_end_date,
                pbs.task_description,
                pbs.minutes_of_service,
                pbs.billing_code,
                pbs.billing_code_description,
                'Not Billed' as billing_status,
                0 as is_billed,
                1 as is_carried_over,
                pbs.billing_week as original_billing_week,
                'Carried over from week ' || pbs.billing_week || ' - not billed in original week' as carryover_reason,
                CURRENT_TIMESTAMP as created_date,
                'CARRYOVER: ' || COALESCE(pbs.billing_notes, '') as billing_notes
            FROM provider_task_billing_status pbs
            WHERE pbs.billing_status = 'Not Billed'
                AND pbs.billing_week < ?
                AND pbs.is_carried_over = 0
            """
            conn.execute(carryover_query, (billing_week, week_start, week_end, billing_week))
            
            # Step 2: Mark original tasks as carried over
            carryover_update_query = """
            UPDATE provider_task_billing_status
            SET is_carried_over = 1,
                updated_date = CURRENT_TIMESTAMP,
                billing_notes = COALESCE(billing_notes, '') || ' [CARRIED OVER TO ' || ? || ']'
            WHERE billing_status = 'Not Billed'
                AND billing_week < ?
                AND is_carried_over = 0
            """
            conn.execute(carryover_update_query, (billing_week, billing_week))
            
            # Step 3: Process current week's tasks - Mark eligible tasks as "Billed"
            update_query = """
            UPDATE provider_task_billing_status
            SET billing_status = 'Billed',
                is_billed = 1,
                billed_date = CURRENT_TIMESTAMP,
                updated_date = CURRENT_TIMESTAMP
            WHERE billing_week = ?
                AND billing_status = 'Not Billed'
                AND billing_code IS NOT NULL
                AND billing_code != ''
                AND billing_code != 'Not_Billable'
                AND minutes_of_service > 0
            """
            conn.execute(update_query, (billing_week,))
            
            # Step 4: Log status changes in history table
            history_insert_query = """
            INSERT INTO billing_status_history (
                billing_status_id,
                provider_task_id,
                previous_status,
                new_status,
                change_reason,
                changed_by,
                change_date,
                additional_notes
            )
            SELECT
                pbs.billing_status_id,
                pbs.provider_task_id,
                'Not Billed' as previous_status,
                'Billed' as new_status,
                'Weekly billing report processing - Saturday billing cycle' as change_reason,
                1 as changed_by,
                CURRENT_TIMESTAMP as change_date,
                'Automatically billed during week ' || pbs.billing_week || ' processing' as additional_notes
            FROM provider_task_billing_status pbs
            WHERE pbs.billing_week = ?
                AND pbs.is_billed = 1
                AND pbs.billed_date >= ?
            """
            conn.execute(history_insert_query, (billing_week, datetime.now()))
            
            conn.commit()
        except Exception as e:
            self.logger.error(f"Error processing weekly billing in Python: {str(e)}")
            raise
    
    def update_billing_status(self, provider_task_id: int, new_status: str, 
                            external_id: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """
        Update the billing status of a specific task.
        
        Args:
            provider_task_id: ID of the provider task
            new_status: New billing status
            external_id: External system ID (invoice, claim, payment)
            notes: Additional notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = get_db_connection()
            
            # Get current status for history
            current_query = """
            SELECT billing_status_id, billing_status 
            FROM provider_task_billing_status 
            WHERE provider_task_id = ?
            ORDER BY created_date DESC
            LIMIT 1
            """
            
            current_result = conn.execute(current_query, [provider_task_id]).fetchone()
            
            if not current_result:
                self.logger.error(f"Provider task {provider_task_id} not found")
                return False
            
            billing_status_id, current_status = current_result
            
            # Update the status
            update_query = """
            UPDATE provider_task_billing_status 
            SET billing_status = ?,
                updated_date = CURRENT_TIMESTAMP,
                billing_notes = COALESCE(billing_notes, '') || CASE WHEN ? IS NOT NULL THEN ' | ' || ? ELSE '' END
            """
            
            # Set appropriate flags based on status
            status_flags = {
                'Billed': 'is_billed = 1, billed_date = CURRENT_TIMESTAMP',
                'Invoiced': 'is_invoiced = 1, invoiced_date = CURRENT_TIMESTAMP',
                'Claim Submitted': 'is_claim_submitted = 1, claim_submitted_date = CURRENT_TIMESTAMP',
                'Insurance Processed': 'is_insurance_processed = 1, insurance_processed_date = CURRENT_TIMESTAMP',
                'Approve to Pay': 'is_approved_to_pay = 1, approved_to_pay_date = CURRENT_TIMESTAMP',
                'Paid': 'is_paid = 1, paid_date = CURRENT_TIMESTAMP'
            }
            
            if new_status in status_flags:
                update_query += f", {status_flags[new_status]}"
            
            if external_id:
                if new_status == 'Invoiced':
                    update_query += ", external_invoice_id = ?"
                elif new_status == 'Claim Submitted':
                    update_query += ", external_claim_id = ?"
                elif new_status == 'Paid':
                    update_query += ", external_payment_id = ?"
            
            update_query += " WHERE billing_status_id = ?"
            
            # Prepare parameters
            params = [new_status, notes, notes, billing_status_id]
            if external_id:
                params.insert(-1, external_id)
            
            conn.execute(update_query, params)
            
            # Log the change in history
            history_query = """
            INSERT INTO billing_status_history (
                billing_status_id, provider_task_id, previous_status, new_status,
                change_reason, changed_by, additional_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            conn.execute(history_query, [
                billing_status_id, provider_task_id, current_status, new_status,
                f"Status updated via API", 1, notes
            ])
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Updated task {provider_task_id} status from {current_status} to {new_status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating billing status: {str(e)}")
            return False
    
    def get_weekly_report_data(self, billing_week: Optional[str] = None) -> pd.DataFrame:
        """
        Get comprehensive weekly report data.
        
        Args:
            billing_week: Week in YYYY-WW format. Defaults to current week.
            
        Returns:
            DataFrame with weekly report data
        """
        if billing_week is None:
            billing_week, _, _ = self.get_current_billing_week()
        
        try:
            conn = get_db_connection()
            
            query = """
            SELECT 
                pbs.*,
                CASE 
                    WHEN pbs.billing_code IS NULL OR pbs.billing_code = '' THEN 'Missing billing code'
                    WHEN pbs.billing_code = 'Not_Billable' THEN 'Not billable'
                    WHEN pbs.minutes_of_service = 0 THEN 'Zero minutes'
                    ELSE 'Billable'
                END as billability_status
            FROM provider_task_billing_status pbs
            WHERE pbs.billing_week = ?
            ORDER BY pbs.provider_name, pbs.task_date, pbs.created_date
            """
            
            df = pd.read_sql_query(query, conn, params=[billing_week])
            conn.close()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting weekly report data: {str(e)}")
            return pd.DataFrame()

def main():
    """Main function for command-line usage."""
    processor = WeeklyBillingProcessor()
    
    # Setup system if needed
    processor.setup_billing_system()
    
    # Process current week
    result = processor.process_weekly_billing()
    
    if result['success']:
        print(f"Weekly billing processed successfully for week {result['billing_week']}")
        print(f"Summary: {result['summary']['overall']}")
    else:
        print(f"Error processing weekly billing: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()