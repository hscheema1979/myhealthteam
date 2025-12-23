"""
Populate provider_task_billing_status table from provider_tasks
This script migrates existing provider task data into the billing system
"""
import sys
sys.path.insert(0, 'src')

from database import get_db_connection
from datetime import datetime

def populate_billing_status():
    """Populate billing status table from provider tasks"""
    conn = get_db_connection()
    
    print("\n" + "="*80)
    print("POPULATE PROVIDER TASK BILLING STATUS")
    print("="*80)
    
    try:
        # Check how many provider tasks exist
        print("\n1. Checking existing provider tasks...")
        check_query = """
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN billing_code IS NOT NULL AND billing_code != 'Not_Billable' THEN 1 END) as billable
        FROM provider_tasks
        WHERE task_date IS NOT NULL
        AND provider_id IS NOT NULL
        """
        result = conn.execute(check_query).fetchone()
        total_tasks = result[0] if result else 0
        billable_tasks = result[1] if result else 0
        
        print("   Total provider tasks: {}".format(total_tasks))
        print("   Billable tasks: {}".format(billable_tasks))
        
        if billable_tasks == 0:
            print("\n   No billable tasks found. Nothing to populate.")
            return True
        
        # Check current billing status table
        print("\n2. Checking current billing status table...")
        current_count_query = "SELECT COUNT(*) FROM provider_task_billing_status"
        current_count = conn.execute(current_count_query).fetchone()[0]
        print("   Current records in billing table: {}".format(current_count))
        
        # Populate from provider_tasks
        print("\n3. Populating billing status table...")
        insert_query = """
        INSERT OR IGNORE INTO provider_task_billing_status (
            provider_task_id,
            provider_id,
            provider_name,
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
            billed_date,
            billed_by,
            is_invoiced,
            invoiced_date,
            is_claim_submitted,
            claim_submitted_date,
            is_insurance_processed,
            insurance_processed_date,
            is_approved_to_pay,
            approved_to_pay_date,
            is_paid,
            paid_date,
            is_carried_over,
            original_billing_week,
            carryover_reason,
            billing_notes,
            billing_company,
            created_date,
            updated_date
        )
        SELECT 
            pt.provider_task_id,
            pt.provider_id,
            COALESCE(u.full_name, 'Unknown Provider') as provider_name,
            COALESCE(pt.patient_name, pt.patient_id) as patient_name,
            pt.task_date,
            strftime('%Y-%W', pt.task_date) as billing_week,
            strftime('%Y-%m-%d', pt.task_date, '-6 days', 'weekday 1') as week_start_date,
            strftime('%Y-%m-%d', pt.task_date, '+0 days', 'weekday 0') as week_end_date,
            pt.task_description,
            pt.minutes_of_service,
            COALESCE(pt.billing_code, 'Not_Billable') as billing_code,
            COALESCE(
                pt.billing_code_description,
                pt.task_description || ' - Default'
            ) as billing_code_description,
            'Pending' as billing_status,
            0 as is_billed,
            NULL as billed_date,
            NULL as billed_by,
            0 as is_invoiced,
            NULL as invoiced_date,
            0 as is_claim_submitted,
            NULL as claim_submitted_date,
            0 as is_insurance_processed,
            NULL as insurance_processed_date,
            0 as is_approved_to_pay,
            NULL as approved_to_pay_date,
            0 as is_paid,
            NULL as paid_date,
            0 as is_carried_over,
            NULL as original_billing_week,
            NULL as carryover_reason,
            NULL as billing_notes,
            NULL as billing_company,
            CURRENT_TIMESTAMP as created_date,
            CURRENT_TIMESTAMP as updated_date
        FROM provider_tasks pt
            LEFT JOIN users u ON pt.provider_id = u.user_id
        WHERE pt.billing_code IS NOT NULL
            AND pt.billing_code != 'Not_Billable'
            AND pt.task_date IS NOT NULL
            AND pt.provider_id IS NOT NULL
        """
        
        conn.execute(insert_query)
        conn.commit()
        
        # Check new count
        new_count = conn.execute(current_count_query).fetchone()[0]
        inserted_count = new_count - current_count
        
        print("   Records inserted: {}".format(inserted_count))
        print("   Total records now: {}".format(new_count))
        
        # Skip creating separate weekly billing reports table - billing_status table is authoritative source
        print("\n4. Skipping weekly billing reports (using provider_task_billing_status as source)...")
        
        # Verification
        print("\n5. Verification...")
        weeks_query = """
        SELECT 
            billing_week,
            COUNT(*) as task_count,
            SUM(minutes_of_service) as total_minutes
        FROM provider_task_billing_status
        GROUP BY billing_week
        ORDER BY billing_week DESC
        LIMIT 5
        """
        
        results = conn.execute(weeks_query).fetchall()
        if results:
            print("   Recent billing weeks:")
            for row in results:
                week, count, minutes = row
                print("     Week {}: {} tasks, {} minutes".format(week, count, minutes))
        
        print("\n" + "="*80)
        print("POPULATION COMPLETED SUCCESSFULLY")
        print("="*80)
        return True
        
    except Exception as e:
        print("\n[ERROR] Population failed: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = populate_billing_status()
    sys.exit(0 if success else 1)
