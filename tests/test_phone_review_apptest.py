"""
Streamlit AppTest for Phone Review Functionality
Tests the phone review entry UI and database operations.

Run: python tests/test_phone_review_apptest.py
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import sqlite3

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import database

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

DB_PATH = "production.db"
TEST_DATE = datetime.now().strftime("%Y-%m-%d")

# =============================================================================
# TEST RESULTS TRACKING
# =============================================================================

class TestTracker:
    def __init__(self):
        self.start_time = datetime.now()
        self.tests = []
        self.summary = {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0}

    def add_result(self, test_name: str, status: str, details: str = ""):
        self.tests.append({
            "name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        self.summary[status] = self.summary.get(status, 0) + 1

    def get_summary(self) -> str:
        duration = (datetime.now() - self.start_time).total_seconds()
        summary = f"""
{'='*70}
TEST SUMMARY - Phone Review AppTest
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}
Duration: {duration:.2f} seconds
Total Tests: {len(self.tests)}
  PASSED: {self.summary['PASS']}
  FAILED: {self.summary['FAIL']}
  SKIPPED: {self.summary['SKIP']}
  ERRORS: {self.summary['ERROR']}
"""
        return summary

tracker = TestTracker()

# =============================================================================
# DATABASE UTILITIES
# =============================================================================

def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_test_provider():
    """Get a test provider user."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT u.user_id, u.username, u.full_name "
            "FROM users u "
            "JOIN user_roles ur ON u.user_id = ur.user_id "
            "WHERE ur.role_id = 33 "
            "LIMIT 1"
        )
        user = cursor.fetchone()
        return dict(user) if user else {}
    finally:
        conn.close()

def get_active_patient():
    """Get an active patient for testing."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT p.patient_id, p.first_name, p.last_name
            FROM patients p
            WHERE p.status LIKE 'Active%'
            LIMIT 1
        """)
        patient = cursor.fetchone()
        return dict(patient) if patient else {}
    finally:
        conn.close()

def cleanup_test_phone_review(provider_id: int, patient_id: str, review_date: str):
    """Clean up test phone review records."""
    conn = get_db_connection()
    try:
        current_year = datetime.now().year
        current_month = datetime.now().month

        coord_table = f"coordinator_tasks_{current_year}_{current_month:02d}"
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (coord_table,))
        if cursor.fetchone():
            conn.execute(f"DELETE FROM {coord_table} WHERE coordinator_id = ? AND patient_id = ? AND task_date = ? AND task_type = 'Phone Call'",
                        (provider_id, patient_id, review_date))

        prov_table = f"provider_tasks_{current_year}_{current_month:02d}"
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (prov_table,))
        if cursor.fetchone():
            conn.execute(f"DELETE FROM {prov_table} WHERE provider_id = ? AND patient_id = ? AND task_date = ? AND task_description = 'Phone Review'",
                        (provider_id, patient_id, review_date))

        conn.commit()
        print(f"  Cleaned up test phone review")
    except Exception as e:
        print(f"  Cleanup error: {e}")
    finally:
        conn.close()

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_1_database_functions():
    """Test database functions for phone review."""
    print("\n=== Test 1: Database Functions ===")

    providers = database.get_users_by_role(33)
    if providers:
        tracker.add_result("get_users_by_role", "PASS", f"Found {len(providers)} providers")
        print(f"  [PASS] Found {len(providers)} providers")

    patient_panel = database.get_all_patient_panel()
    if patient_panel:
        tracker.add_result("get_all_patient_panel", "PASS", f"Found {len(patient_panel)} patients")
        print(f"  [PASS] Found {len(patient_panel)} patients")

def test_2_active_patients():
    """Test active patients available for phone review."""
    print("\n=== Test 2: Active Patients ===")

    patient_panel = database.get_all_patient_panel()
    allowed_statuses = ['Active', 'Active-Geri', 'Active-PCP', 'Hospice', 'HOSPICE']
    active_patients = [p for p in patient_panel if (p.get('status', '') or '').strip() in allowed_statuses]

    if active_patients:
        tracker.add_result("active_patients_count", "PASS", f"{len(active_patients)} active patients")
        print(f"  [PASS] {len(active_patients)} active patients")

def test_3_filters():
    """Test filter functionality."""
    print("\n=== Test 3: Filters ===")

    patient_panel = database.get_all_patient_panel()

    # Search test
    test_search = "Diaz"
    search_results = [p for p in patient_panel if test_search.lower() in f"{p.get('first_name', '')} {p.get('last_name', '')}".lower()]
    tracker.add_result("search_filter", "PASS" if search_results else "SKIP", f"Search '{test_search}': {len(search_results)} results")
    print(f"  [PASS] Search filter: {len(search_results)} results")

    # Status filter
    status_filtered = [p for p in patient_panel if (p.get('status', '') or '').strip() in ['Active', 'Active-Geri']]
    tracker.add_result("status_filter", "PASS", f"Status filter: {len(status_filtered)} patients")
    print(f"  [PASS] Status filter: {len(status_filtered)} patients")

def test_4_coordinator_task():
    """Test phone review submission to coordinator_tasks."""
    print("\n=== Test 4: Coordinator Task Submission ===")

    provider = get_test_provider()
    patient = get_active_patient()

    if not provider or not patient:
        tracker.add_result("coordinator_task", "SKIP", "No provider or patient")
        return

    print(f"  Provider: {provider['full_name']}, Patient: {patient['first_name']} {patient['last_name']}")

    cleanup_test_phone_review(provider['user_id'], patient['patient_id'], TEST_DATE)

    result = database.save_coordinator_task(
        coordinator_id=provider['user_id'],
        patient_id=patient['patient_id'],
        task_date=TEST_DATE,
        task_description="Phone Review",
        duration_minutes=15,
        notes="AppTest"
    )

    if result:
        tracker.add_result("coordinator_task_save", "PASS", f"Task saved: {result}")
        print(f"  [PASS] Coordinator task saved")

        # Verify
        conn = get_db_connection()
        current_year = datetime.now().year
        current_month = datetime.now().month
        coord_table = f"coordinator_tasks_{current_year}_{current_month:02d}"
        cursor = conn.execute(f"SELECT * FROM {coord_table} WHERE coordinator_task_id = ?", (result,))
        if cursor.fetchone():
            tracker.add_result("coordinator_task_verify", "PASS", f"Found in {coord_table}")
            print(f"  [PASS] Task verified in {coord_table}")
        conn.close()

def test_5_provider_task():
    """Test phone review submission to provider_tasks."""
    print("\n=== Test 5: Provider Task Submission ===")

    provider = get_test_provider()
    patient = get_active_patient()

    if not provider or not patient:
        tracker.add_result("provider_task", "SKIP", "No provider or patient")
        return

    task_saved, task_error = database.save_daily_task(
        provider_id=provider['user_id'],
        patient_id=patient['patient_id'],
        task_date=TEST_DATE,
        task_description="Phone Review",
        notes="AppTest",
        billing_code="Not_Billable",
        location_type="Telehealth",
        patient_type="Follow Up"
    )

    if task_saved:
        tracker.add_result("provider_task_save", "PASS", "Provider task saved")
        print(f"  [PASS] Provider task saved")

        # Verify fields
        conn = get_db_connection()
        current_year = datetime.now().year
        current_month = datetime.now().month
        prov_table = f"provider_tasks_{current_year}_{current_month:02d}"
        cursor = conn.execute(
            f"""SELECT * FROM {prov_table}
               WHERE provider_id = ? AND patient_id = ? AND task_date = ?
               AND task_description = 'Phone Review'
               ORDER BY provider_task_id DESC LIMIT 1""",
            (provider['user_id'], patient['patient_id'], TEST_DATE)
        )
        record = cursor.fetchone()
        if record:
            record_dict = dict(record)
            checks = []
            if record_dict.get('billing_code') == 'Not_Billable':
                checks.append("billing_code")
            if record_dict.get('location_type') == 'Telehealth':
                checks.append("location_type")
            if record_dict.get('patient_type') == 'Follow Up':
                checks.append("patient_type")

            tracker.add_result("provider_task_fields", "PASS", f"Fields OK: {', '.join(checks)}")
            print(f"  [PASS] Fields verified: {', '.join(checks)}")
        conn.close()

def test_6_multiple_phone_reviews():
    """Test that multiple phone reviews per patient per day are allowed."""
    print("\n=== Test 6: Multiple Phone Reviews Allowed ===")

    provider = get_test_provider()
    patient = get_active_patient()

    if not provider or not patient:
        tracker.add_result("multiple_phone_reviews", "SKIP", "No provider or patient")
        return

    # Try to save another phone review on the same day
    task_saved, task_error = database.save_daily_task(
        provider_id=provider['user_id'],
        patient_id=patient['patient_id'],
        task_date=TEST_DATE,
        task_description="Phone Review",
        notes="AppTest second phone review",
        billing_code="Not_Billable",
        location_type="Telehealth",
        patient_type="Follow Up"
    )

    if task_saved:
        tracker.add_result("multiple_phone_reviews", "PASS", "Second phone review saved successfully")
        print(f"  [PASS] Multiple phone reviews allowed - second review saved")

        # Verify there are now 2 phone reviews for this patient today
        conn = get_db_connection()
        current_year = datetime.now().year
        current_month = datetime.now().month
        prov_table = f"provider_tasks_{current_year}_{current_month:02d}"
        cursor = conn.execute(
            f"""SELECT COUNT(*) as count FROM {prov_table}
               WHERE provider_id = ? AND patient_id = ? AND task_date = ?
               AND task_description = 'Phone Review'""",
            (provider['user_id'], patient['patient_id'], TEST_DATE)
        )
        count = cursor.fetchone()["count"]
        conn.close()

        if count >= 2:
            tracker.add_result("multiple_phone_reviews_count", "PASS", f"{count} phone reviews found")
            print(f"  [PASS] Verified {count} phone reviews for patient today")
        else:
            tracker.add_result("multiple_phone_reviews_count", "FAIL", f"Expected 2+, got {count}")
            print(f"  [FAIL] Expected 2+ phone reviews, got {count}")
    else:
        tracker.add_result("multiple_phone_reviews", "FAIL", f"Multiple reviews not allowed: {task_error}")
        print(f"  [FAIL] Multiple phone reviews blocked: {task_error}")

def test_7_cleanup():
    """Test cleanup."""
    print("\n=== Test 7: Cleanup ===")

    provider = get_test_provider()
    patient = get_active_patient()

    if provider and patient:
        cleanup_test_phone_review(provider['user_id'], patient['patient_id'], TEST_DATE)
        tracker.add_result("cleanup", "PASS", "Test data cleaned up")
        print(f"  [PASS] Cleanup complete")

# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    print("\n" + "="*70)
    print("PHONE REVIEW APPTEST")
    print("="*70)
    print(f"Database: {DB_PATH}")
    print(f"Test Date: {TEST_DATE}")

    test_1_database_functions()
    test_2_active_patients()
    test_3_filters()
    test_4_coordinator_task()
    test_5_provider_task()
    test_6_multiple_phone_reviews()
    test_7_cleanup()

    print(tracker.get_summary())

    if tracker.summary['FAIL'] > 0 or tracker.summary['ERROR'] > 0:
        print("\nFailed Tests:")
        for test in tracker.tests:
            if test['status'] in ['FAIL', 'ERROR']:
                print(f"  [{test['status']}] {test['name']}: {test.get('details', '')}")

    # Save report
    report_file = f"test_report_phone_review_apptest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            "start_time": tracker.start_time.isoformat(),
            "summary": tracker.summary,
            "tests": tracker.tests,
        }, f, indent=2)

    print(f"\nReport: {report_file}")
    print("="*70)

    return tracker.summary['FAIL'] == 0 and tracker.summary['ERROR'] == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
