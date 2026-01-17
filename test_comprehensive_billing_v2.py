
import os
import sys
import pandas as pd
from datetime import datetime
import sqlite3
import logging

# Ensure the project root is in sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src import database
from src.billing.weekly_billing_processor import WeeklyBillingProcessor

def log_test_task(provider_id, provider_name, patient_id, patient_type, location, date_str):
    # Normalize location for database lookup
    loc_map = {"Telehealth": "Telehealth", "Tele": "Telehealth", "Home": "Home", "Office": "Office"}
    db_location = loc_map.get(location, location)
    
    # Lookup billing code
    codes = database.get_billing_codes(location_type=db_location, patient_type=patient_type)
    if not codes:
        codes = database.get_billing_codes(patient_type=patient_type)
        
    billing_code = codes[0]['billing_code'] if codes else "UNKNOWN"
    description = codes[0]['task_description'] if codes else f"Test {patient_type} {location}"
    
    database.save_daily_task(
        provider_id=provider_id,
        patient_id=patient_id,
        task_date=date_str,
        task_description=description,
        notes=f"TEST_TASK: {patient_type} at {location} for {provider_name}",
        billing_code=billing_code
    )
    return billing_code

def run_billing_and_payroll_updates():
    # 1. Populates provider_task_billing_status
    # We use OR REPLACE here for testing to ensure edits propagate
    conn = database.get_db_connection()
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            conn.execute(f"""
                INSERT OR REPLACE INTO provider_task_billing_status (
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

    # 3. Populate Payroll (Simplified)
    conn = database.get_db_connection()
    try:
        conn.execute("DELETE FROM provider_weekly_payroll_status") # Clear for clean test run
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
    
    patient_types = ["New", "Follow Up", "Acute", "TCM-7", "Cognitive"]
    locations = ["Home", "Telehealth", "Office"]
    
    test_date = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now()
    table_name = f"provider_tasks_{now.year}_{str(now.month).zfill(2)}"
    
    # 1. Log all tasks
    print("Logging tasks for all providers...")
    for p_id, p_name in providers:
        for p_type in patient_types:
            for loc in locations:
                test_patient_id = f"TPAT_{p_id}_{p_type[:2]}_{loc[:1]}"
                log_test_task(p_id, p_name, test_patient_id, p_type, loc, test_date)

    # 2. Run updates
    run_billing_and_payroll_updates()

    # 3. Perform EDIT for 1 task per provider
    print("Performing EDIT test for each provider...")
    for p_id, p_name in providers:
        # Pick one task to edit: Follow Up Home
        target_notes = f"TEST_TASK: Follow Up at Home for {p_name}"
        conn = database.get_db_connection()
        try:
            conn.execute(f"UPDATE {table_name} SET minutes_of_service = 123, notes = ? WHERE provider_id = ? AND notes = ?", 
                         (target_notes + " (EDITED)", p_id, target_notes))
            conn.commit()
        finally:
            conn.close()

    # 4. Re-run updates to propagate edits
    run_billing_and_payroll_updates()

    # 5. Validate and build results table
    print("Validating results...")
    results = []
    conn = database.get_db_connection()
    try:
        for p_id, p_name in providers:
            # Check the Edited Task
            target_notes = f"TEST_TASK: Follow Up at Home for {p_name} (EDITED)"
            
            # Task Review
            task = conn.execute(f"SELECT minutes_of_service, billing_code FROM {table_name} WHERE notes = ?", (target_notes,)).fetchone()
            task_status = "OK (123)" if task and task[0] == 123 else "FAIL"
            b_code = task[1] if task else "unknown"
            
            # Billing Summary
            bill = conn.execute("SELECT minutes_of_service FROM provider_task_billing_status WHERE provider_id = ? AND task_description LIKE '%Follow Up at Home%'", (p_id,)).fetchone()
            bill_status = "OK (123)" if bill and bill[0] == 123 else f"FAIL ({bill[0] if bill else 'None'})"
            
            # Payroll
            pay = conn.execute("SELECT total_minutes_of_service FROM provider_weekly_payroll_status WHERE provider_id = ? AND visit_type LIKE '%Follow Up at Home%'", (p_id,)).fetchone()
            pay_status = "OK (123)" if pay and pay[0] == 123 else f"FAIL ({pay[0] if pay else 'None'})"
            
            # Check any other random combo (e.g. Acute Tele)
            acute_notes = f"TEST_TASK: Acute at Telehealth for {p_name}"
            acute_task = conn.execute(f"SELECT minutes_of_service FROM {table_name} WHERE notes = ?", (acute_notes,)).fetchone()
            acute_status = "OK" if acute_task else "FAIL"

            results.append({
                "Provider": p_name,
                "Edited Task Review": task_status,
                "Edited Billing Sum": bill_status,
                "Edited Payroll": pay_status,
                "General Task Log": acute_status
            })
    finally:
        conn.close()

    # 6. Print Markdown Table
    df = pd.DataFrame(results)
    print("\n### FINAL TEST RESULTS TABLE")
    print(df.to_markdown(index=False))

    # 7. Cleanup
    print("\nCleaning up test data...")
    conn = database.get_db_connection()
    try:
        conn.execute(f"DELETE FROM {table_name} WHERE notes LIKE 'TEST_TASK:%'")
        conn.execute(f"DELETE FROM provider_task_billing_status WHERE task_description LIKE 'TEST_TASK:%' OR provider_task_id NOT IN (SELECT provider_task_id FROM {table_name})")
        conn.execute("DELETE FROM provider_weekly_payroll_status") # This is a bit aggressive but cleans the test data
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    test_all_providers()
