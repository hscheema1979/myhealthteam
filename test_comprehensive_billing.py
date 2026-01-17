
import os
import sys
import pandas as pd
from datetime import datetime
import sqlite3

# Ensure the project root is in sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src import database
from src.billing.weekly_billing_processor import WeeklyBillingProcessor

def log_test_task(provider_id, patient_id, patient_type, location, date_str):
    service_type = patient_type # In the UI, service_type is set to patient_type for the lookup
    
    # Normalize location for database lookup
    loc_map = {"Telehealth": "Telehealth", "Tele": "Telehealth", "Home": "Home", "Office": "Office"}
    db_location = loc_map.get(location, location)
    
    # Lookup billing code
    codes = database.get_billing_codes(location_type=db_location, patient_type=patient_type)
    if not codes:
        # Fallback for TCM/Cognitive which might not have all combinations
        codes = database.get_billing_codes(patient_type=patient_type)
        
    billing_code = codes[0]['billing_code'] if codes else "UNKNOWN"
    description = codes[0]['task_description'] if codes else f"Test {patient_type} {location}"
    
    database.save_daily_task(
        provider_id=provider_id,
        patient_id=patient_id,
        task_date=date_str,
        task_description=description,
        notes=f"Test Task: {patient_type} at {location}",
        billing_code=billing_code
    )
    return billing_code

def run_billing_and_payroll_updates(year, month):
    # 1. Populates provider_task_billing_status
    conn = database.get_db_connection()
    try:
        # Get all monthly tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_%'")
        tables = [row[0] for row in cursor.fetchall()]
        


        for table in tables:
            # Simple version of dashboard ensure_billing_data_populated logic
            conn.execute(f"""
                INSERT OR IGNORE INTO provider_task_billing_status (
                    provider_task_id, provider_id, provider_name, patient_name, patient_id,
                    task_date, billing_week, week_start_date, week_end_date,
                    task_description, minutes_of_service, billing_code,
                    billing_code_description, billing_status, is_billed, created_date
                )
                SELECT pt.provider_task_id, pt.provider_id, pt.provider_name, pt.patient_name, pt.patient_id,
                    pt.task_date, strftime('%Y-%W', pt.task_date) as billing_week,
                    strftime('%Y-%m-%d', pt.task_date, '-6 days', 'weekday 1') as week_start_date,
                    strftime('%Y-%m-%d', pt.task_date, '+0 days', 'weekday 0') as week_end_date,
                    pt.task_description, pt.minutes_of_service, pt.billing_code,
                    pt.billing_code_description, 'Pending', 0, CURRENT_TIMESTAMP
                FROM {table} pt
                WHERE pt.billing_code IS NOT NULL AND pt.billing_code != 'Not_Billable'
            """)
        conn.commit()
    finally:
        conn.close()

    # 2. Process Weekly Billing
    processor = WeeklyBillingProcessor()
    processor.process_weekly_billing()

    # 3. Populate Payroll (Simplified from transform script)
    conn = database.get_db_connection()
    try:
        conn.execute("DELETE FROM provider_weekly_payroll_status WHERE pay_year = ? AND pay_week_number = ?", 
                     (year, datetime.now().isocalendar()[1]))
        conn.execute("""
            INSERT INTO provider_weekly_payroll_status (
                provider_id, provider_name, pay_week_start_date, pay_week_end_date,
                pay_week_number, pay_year, visit_type, task_count, total_minutes_of_service,
                payroll_status, created_date
            )
            SELECT ptbs.provider_id, ptbs.provider_name, ptbs.week_start_date, ptbs.week_end_date,
                ptbs.billing_week, CAST(strftime('%Y', ptbs.task_date) AS INTEGER),
                ptbs.task_description, COUNT(*), SUM(ptbs.minutes_of_service),
                'Pending', CURRENT_TIMESTAMP
            FROM provider_task_billing_status ptbs
            WHERE ptbs.provider_id IS NOT NULL
            GROUP BY ptbs.provider_id, ptbs.provider_name, ptbs.week_start_date, ptbs.week_end_date, ptbs.task_description
        """)
        conn.commit()
    finally:
        conn.close()

def test_all_providers():
    conn = database.get_db_connection()
    providers = conn.execute("SELECT u.user_id, u.full_name FROM users u JOIN user_roles ur ON u.user_id = ur.user_id WHERE ur.role_id = 33").fetchall()
    conn.close()
    
    patient_types = ["New", "Follow Up", "Acute", "TCM-7", "TCM-14", "Cognitive"]
    locations = ["Home", "Telehealth", "Office"]
    
    test_date = datetime.now().strftime("%Y-%m-%d")
    results = []

    for p_id, p_name in providers:
        print(f"Testing Provider: {p_name}")
        for p_type in patient_types:
            for loc in locations:
                test_patient_id = f"TEST_{p_id}_{p_type[:2]}_{loc[:1]}"
                
                # Cleanup existing test data for this specific test case
                # (Optional: Just use unique IDs)
                
                # 1. Log Task
                b_code = log_test_task(p_id, test_patient_id, p_type, loc, test_date)
                
                # 2. Basic Validation (Immediate DB check)
                results.append({
                    "Provider": p_name,
                    "Patient Type": p_type,
                    "Location": loc,
                    "Billing Code": b_code,
                    "Task Logged": "Yes",
                    "Task Review": "Pending Summary",
                    "Billing Summary": "Pending Summary",
                    "Payroll": "Pending Summary"
                })

    # Run summaries
    now = datetime.now()
    run_billing_and_payroll_updates(now.year, now.month)
    
    # 3. Final Validation across all summary tables
    conn = database.get_db_connection()
    try:
        for res in results:
            p_name = res["Provider"]
            p_type = res["Patient Type"]
            loc = res["Location"]
            b_code = res["Billing Code"]
            
            # Check Task Review (Monthly table)
            table_name = f"provider_tasks_{now.year}_{str(now.month).zfill(2)}"
            task = conn.execute(f"SELECT billing_code FROM {table_name} WHERE provider_name = ? AND notes LIKE ? LIMIT 1", 
                                (p_name, f"%{p_type} at {loc}%")).fetchone()
            res["Task Review"] = "OK" if task and task[0] == b_code else "FAIL"
            
            # Check Billing Summary
            bill = conn.execute("SELECT billing_status FROM provider_task_billing_status WHERE provider_name = ? AND billing_code = ? LIMIT 1",
                                (p_name, b_code)).fetchone()
            res["Billing Summary"] = "OK" if bill else "MISSING"
            
            # Check Payroll
            pay = conn.execute("SELECT payroll_status FROM provider_weekly_payroll_status WHERE provider_name = ? AND visit_type LIKE ? LIMIT 1",
                               (p_name, f"%{p_type}%")).fetchone()
            res["Payroll"] = "OK" if pay else "MISSING"
            
    finally:
        conn.close()


    # Pick one provider's task to test EDIT
    test_p_id, test_p_name = providers[0]
    p_type = "Follow Up"
    loc = "Home"
    target_notes = f"Test Task: {p_type} at {loc}"
    table_name = f"provider_tasks_{now.year}_{str(now.month).zfill(2)}"
    
    print(f"\nPerforming Edit Test for {test_p_name}...")
    conn = database.get_db_connection()
    try:
        # 1. Update the original task
        conn.execute(f"UPDATE {table_name} SET minutes_of_service = 99, notes = ? WHERE provider_id = ? AND notes = ?", 
                     (target_notes + " - UPDATED", test_p_id, target_notes))
        conn.commit()
        
        # 2. Re-run updates
        run_billing_and_payroll_updates(now.year, now.month)
        
        # 3. Verify in all tables
        task_review = conn.execute(f"SELECT minutes_of_service FROM {table_name} WHERE notes = ?", (target_notes + " - UPDATED",)).fetchone()
        billing = conn.execute("SELECT minutes_of_service FROM provider_task_billing_status WHERE provider_id = ? AND task_description LIKE ?", (test_p_id, f"%{p_type}%")).fetchone()
        payroll = conn.execute("SELECT total_minutes_of_service FROM provider_weekly_payroll_status WHERE provider_id = ? AND visit_type LIKE ?", (test_p_id, f"%{p_type}%")).fetchone()
        
        print(f"  Edit Verification:")
        print(f"    Task Review Minutes: {task_review[0] if task_review else 'FAIL'}")
        print(f"    Billing Summary Minutes: {billing[0] if billing else 'FAIL'}")
        print(f"    Payroll Minutes: {payroll[0] if payroll else 'FAIL'}")
        
    finally:
        conn.close()

    # Clean up test data
    conn = database.get_db_connection()
    try:
        # Delete tasks with 'Test Task' in notes
        table_name = f"provider_tasks_{now.year}_{str(now.month).zfill(2)}"
        conn.execute(f"DELETE FROM {table_name} WHERE notes LIKE 'Test Task:%'")
        conn.execute("DELETE FROM provider_task_billing_status WHERE billing_notes LIKE 'CARRYOVER: Test Task:%' OR provider_task_id IN (SELECT provider_task_id FROM " + table_name + " WHERE notes LIKE 'Test Task:%')")
        # For simplicity, just clean the test payroll records if possible or leave them as they are test-specific
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    test_all_providers()
