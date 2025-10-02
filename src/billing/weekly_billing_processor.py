"""
Weekly Billing Report Processor (P00)
This module handles the automated generation of weekly billing reports with carryover logic.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import logging
import sys
import os
from typing import Dict, List, Tuple, Optional

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weekly_billing_processor.log'),
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
        try:
            billing_week, week_start, week_end = self.get_current_billing_week(target_date)
            
            self.logger.info(f"Processing weekly billing for week {billing_week} ({week_start} to {week_end})")
            
            conn = get_db_connection()
            
            # Execute the weekly billing report generator
            generator_file = os.path.join(os.path.dirname(__file__), '..', 'sql', 'weekly_billing_report_generator.sql')
            
            if os.path.exists(generator_file):
                with open(generator_file, 'r') as f:
                    generator_sql = f.read()
                
                # Execute the generator script
                conn.executescript(generator_sql)
                conn.commit()
                
                # Get summary results
                summary = self.get_billing_summary(billing_week, conn)
                
                conn.close()
                
                self.logger.info(f"Weekly billing processed successfully for week {billing_week}")
                return {
                    'success': True,
                    'billing_week': billing_week,
                    'week_start': week_start,
                    'week_end': week_end,
                    'summary': summary
                }
            else:
                self.logger.error("Weekly billing generator SQL file not found")
                return {'success': False, 'error': 'Generator SQL file not found'}
                
        except Exception as e:
            self.logger.error(f"Error processing weekly billing: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_billing_summary(self, billing_week: str, conn: sqlite3.Connection) -> Dict:
        """
        Get billing summary for a specific week.
        
        Args:
            billing_week: Week in YYYY-WW format
            conn: Database connection
            
        Returns:
            Dictionary with billing summary
        """
        try:
            # Get overall summary
            summary_query = """
            SELECT 
                total_tasks,
                total_billed_tasks,
                total_carried_over_tasks,
                report_status
            FROM weekly_billing_reports 
            WHERE billing_week = ?
            """
            
            summary_df = pd.read_sql_query(summary_query, conn, params=[billing_week])
            
            # Get provider breakdown
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
            WHERE billing_week = ?
            GROUP BY provider_id, provider_name
            ORDER BY provider_name
            """
            
            provider_df = pd.read_sql_query(provider_query, conn, params=[billing_week])
            
            # Get tasks requiring attention
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
            WHERE billing_week = ?
                AND billing_status = 'Not Billed'
                AND is_billed = 0
            ORDER BY provider_name, task_date
            """
            
            attention_df = pd.read_sql_query(attention_query, conn, params=[billing_week])
            
            return {
                'overall': summary_df.to_dict('records')[0] if not summary_df.empty else {},
                'by_provider': provider_df.to_dict('records'),
                'attention_required': attention_df.to_dict('records')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting billing summary: {str(e)}")
            return {}
    
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