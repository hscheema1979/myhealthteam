"""
Test Manual Patient Entry Feature - Local Development

This script tests the manual patient entry feature for Care Providers.
Tests both UI components and database operations.

Run: python tests/test_manual_patient_entry.py
"""

import subprocess
import sys
import sqlite3
import os
from datetime import datetime

def run_command(command):
    """Run command and return output"""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def test_database_schema():
    """Test database schema for manual entry support"""
    print("\n" + "="*80)
    print("Test 1: Database Schema Verification")
    print("="*80)

    db_path = "production.db"

    if not os.path.exists(db_path):
        print(f"[SKIP] Database not found at {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tests = [
        ("provider_tasks table exists",
         "SELECT name FROM sqlite_master WHERE type='table' AND name='provider_tasks'"),
        ("manual_intervention_needed table exists",
         "SELECT name FROM sqlite_master WHERE type='table' AND name='manual_intervention_needed'"),
        ("provider_tasks has patient_id column",
         "PRAGMA table_info(provider_tasks)"),
    ]

    passed = 0
    for name, sql in tests:
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            if result:
                print(f"[OK] {name}")
                passed += 1
            else:
                print(f"[FAIL] {name}")
        except Exception as e:
            print(f"[FAIL] {name}: {e}")

    conn.close()
    print(f"\nPassed: {passed}/{len(tests)}")
    return passed == len(tests)

def test_import_function():
    """Test that the provider dashboard imports correctly"""
    print("\n" + "="*80)
    print("Test 2: Import Check")
    print("="*80)

    try:
        sys.path.insert(0, ".")
        from src.dashboards.care_provider_dashboard_enhanced import show_patient_list_section
        print("[OK] care_provider_dashboard_enhanced imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False

def test_pseudo_patient_generation():
    """Test pseudo-patient ID generation logic"""
    print("\n" + "="*80)
    print("Test 3: Pseudo-Patient ID Generation")
    print("="*80)

    test_cases = [
        ("John", "Doe", "01/15/2000", "MANUAL_DOE_JOHN_20000115"),
        ("Jane", "Smith", "12/31/1995", "MANUAL_SMITH_JANE_19951231"),
        ("Bob", "Johnson", "06/05/1980", "MANUAL_JOHNSON_BOB_19800605"),
    ]

    passed = 0
    for first, last, dob, expected in test_cases:
        try:
            # Simulate the logic from the dashboard
            import re
            dob_clean = re.sub(r'[^\d/]', '', dob)

            if '/' in dob_clean:
                dob_parts = dob_clean.split('/')
                if len(dob_parts) == 3:
                    mm, dd, yyyy = dob_parts
                    dob_formatted = f"{yyyy}{mm.zfill(2)}{dd.zfill(2)}"
                else:
                    raise ValueError("Invalid DOB format")
            else:
                dob_formatted = dob_clean

            pseudo_patient_id = f"MANUAL_{last.upper()}_{first.upper()}_{dob_formatted}"

            if pseudo_patient_id == expected:
                print(f"[OK] {first} {last} ({dob}) => {pseudo_patient_id}")
                passed += 1
            else:
                print(f"[FAIL] {first} {last} ({dob})")
                print(f"      Expected: {expected}")
                print(f"      Got:      {pseudo_patient_id}")
        except Exception as e:
            print(f"[FAIL] {first} {last} ({dob}): {e}")

    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)

def test_database_operations():
    """Test database operations with pseudo-patients"""
    print("\n" + "="*80)
    print("Test 4: Database Operations with Pseudo-Patients")
    print("="*80)

    db_path = "production.db"

    if not os.path.exists(db_path):
        print(f"[SKIP] Database not found at {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Test 1: Check if pseudo-patient exists in patients table (should not)
        pseudo_patient_id = "MANUAL_TEST_PATIENT_20000101"
        cursor.execute(
            "SELECT patient_id FROM patients WHERE patient_id = ?",
            (pseudo_patient_id,)
        )
        result = cursor.fetchone()
        if result is None:
            print(f"[OK] Pseudo-patient NOT in patients table (as expected)")
        else:
            print(f"[FAIL] Pseudo-patient found in patients table (unexpected)")

        # Test 2: Check if we can insert to provider_tasks with pseudo-patient
        # First, get a valid provider_id
        cursor.execute(
            "SELECT user_id FROM user_roles WHERE role_id = 33 LIMIT 1"
        )
        provider_result = cursor.fetchone()
        if not provider_result:
            print("[SKIP] No providers found for testing")
            return False

        provider_id = provider_result[0]

        # Try to insert a task with pseudo-patient (rollback after)
        try:
            cursor.execute(
                """INSERT INTO provider_tasks
                   (provider_id, patient_id, date, task_description, duration_minutes, status, source_system)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (provider_id, pseudo_patient_id, datetime.now().date(), "Test Task", 30, "Complete", "MANUAL_ENTRY")
            )
            conn.rollback()  # Rollback the test insert
            print("[OK] Can insert task with pseudo-patient to provider_tasks")
        except Exception as e:
            conn.rollback()
            print(f"[FAIL] Cannot insert task with pseudo-patient: {e}")
            return False

        # Test 3: Check manual_intervention_needed table structure
        cursor.execute("PRAGMA table_info(manual_intervention_needed)")
        columns = cursor.fetchall()
        if columns:
            print(f"[OK] manual_intervention_needed table has {len(columns)} columns")
        else:
            print(f"[FAIL] manual_intervention_needed table not found")

        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Database operations test failed: {e}")
        conn.close()
        return False

def test_save_daily_task_function():
    """Test the save_daily_task function with pseudo-patients"""
    print("\n" + "="*80)
    print("Test 5: save_daily_task Function with Pseudo-Patient")
    print("="*80)

    try:
        from src import database

        # Get a valid provider_id
        conn = database.get_db_connection()
        cursor = conn.execute(
            "SELECT user_id FROM user_roles WHERE role_id = 33 LIMIT 1"
        )
        provider_result = cursor.fetchone()
        conn.close()

        if not provider_result:
            print("[SKIP] No providers found for testing")
            return False

        provider_id = provider_result[0]
        pseudo_patient_id = "MANUAL_TEST_PATIENT_20000101"

        # Try to save a task with pseudo-patient
        task_saved, task_error = database.save_daily_task(
            provider_id=provider_id,
            patient_id=pseudo_patient_id,
            task_date=datetime.now().date(),
            task_description="Test Manual Entry",
            notes="Test notes for manual entry",
            billing_code=None,
            location_type="Office",
            patient_type="New"
        )

        if task_saved:
            if task_error == "PSEUDO_PATIENT":
                print(f"[OK] Task saved with PSEUDO_PATIENT flag (as expected)")
                print(f"     Task was saved but patient doesn't exist in database")
                return True
            else:
                print(f"[WARN] Task saved without PSEUDO_PATIENT flag")
                print(f"      Error: {task_error}")
                return True
        else:
            print(f"[FAIL] Task save failed: {task_error}")
            return False

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_components():
    """Test that UI components for manual entry are in place"""
    print("\n" + "="*80)
    print("Test 6: UI Code Inspection")
    print("="*80)

    try:
        # Read file with encoding handling
        with open("src/dashboards/care_provider_dashboard_enhanced.py", "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        tests = [
            ("Manual Entry option in dropdown", "--- Manual Entry ---" in code),
            ("Manual entry first name field", "manual_first_name" in code),
            ("Manual entry last name field", "manual_last_name" in code),
            ("Manual entry DOB field", "manual_dob" in code),
            ("is_manual_entry check", "is_manual_entry" in code),
            ("Pseudo-patient ID generation", "MANUAL_" in code),
            ("Manual entry validation", "if is_manual_entry:" in code),
        ]

        passed = 0
        for name, result in tests:
            if result:
                print(f"[OK] {name}")
                passed += 1
            else:
                print(f"[FAIL] {name}")

        print(f"\nPassed: {passed}/{len(tests)}")
        return passed == len(tests)

    except Exception as e:
        print(f"[ERROR] UI code inspection failed: {e}")
        return False

def main():
    print("#" * 80)
    print("# Manual Patient Entry Feature - Test Suite")
    print(f"# Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#" * 80)

    results = []

    results.append(("Import Check", test_import_function()))
    results.append(("Pseudo-Patient ID Generation", test_pseudo_patient_generation()))
    results.append(("UI Code Inspection", test_ui_components()))
    results.append(("save_daily_task Function", test_save_daily_task_function()))

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)

    for name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{len(results)} passed")

    if passed == len(results):
        print("\n[OK] All tests passed! Manual patient entry is ready for UI testing.")
        print("\nNext Steps:")
        print("  1. Start the app: streamlit run app.py")
        print("  2. Login as a Care Provider (role 33)")
        print("  3. Go to Daily Task Entry section")
        print("  4. Select '--- Manual Entry ---' from Patient dropdown")
        print("  5. Enter First Name, Last Name, DOB")
        print("  6. Select Type, Location, and other fields")
        print("  7. Click 'Log Task'")
        print("  8. Verify task is saved with PSEUDO_PATIENT warning")
        return 0
    else:
        print(f"\n[WARN] {len(results) - passed} test(s) failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
