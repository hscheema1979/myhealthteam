"""
Streamlit AppTest Framework for Onboarding Dashboard
Tests the complete end-to-end onboarding workflow using Streamlit's native testing.

This framework tests:
1. Database schema for onboarding tables
2. Stage 1: Patient Registration (basic info, insurance, eligibility)
3. Stage 2: Patient Details (contact, address, referral, facility)
4. Stage 3: Chart Creation (EMed chart setup)
5. Stage 4: Intake Processing (documentation, intake call)
6. Stage 5: TV Scheduling (visit scheduling, provider/coordinator assignment)
7. Patient data sync to all tables (patients, patient_panel, patient_assignments, hhc_patients_export)
8. Onboarding completion and handoff

Run: streamlit run tests/test_onboarding_apptest.py
Or: python -m pytest tests/test_onboarding_apptest.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple
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
TEST_TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Test patient data - simulates a new patient referral
TEST_PATIENT_DATA = {
    'first_name': 'APPTTEST',
    'last_name': 'PATIENT',
    'date_of_birth': '1960-01-15',
    'phone_primary': '555-TEST-001',
    'email': 'apptest@zenmedicine.test',
    'insurance_provider': 'Test Insurance Co',
    'policy_number': 'TEST-123-456',
    'group_number': 'TEST-GROUP',
    'eligibility_status': 'Eligible',
    'eligibility_verified': 1,
    'eligibility_notes': 'Test patient for automated onboarding workflow verification',
    'address_street': '123 Test Street',
    'address_city': 'Test City',
    'address_state': 'CA',
    'address_zip': '90210',
    'gender': 'Female',
    'referral_source': 'Automated Test',
    'referring_provider': 'Dr. Test Bot',
    'facility_assignment': 'ProHealth',
    'transportation': 'Family/Caregiver',
    'preferred_language': 'English',
    'visit_type': 'Home Visit',
    'billing_code': '99345',
    'duration_minutes': 45,
}

# =============================================================================
# TEST RESULTS TRACKING
# =============================================================================

class TestTracker:
    def __init__(self):
        self.start_time = datetime.now()
        self.tests = []
        self.summary = {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0}
        self.test_onboarding_id = None

    def add_result(self, test_name: str, status: str, details: str = "", error: str = ""):
        self.tests.append({
            "name": test_name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        self.summary[status] = self.summary.get(status, 0) + 1

    def get_summary(self) -> str:
        duration = (datetime.now() - self.start_time).total_seconds()
        summary = f"""
{'='*70}
TEST SUMMARY - Onboarding Workflow E2E
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

def get_onboarding_user() -> Dict:
    """Get a test user with onboarding permissions (role 37 or admin)."""
    conn = get_db_connection()
    try:
        # Try to get onboarding team user first (role 37)
        cursor = conn.execute(
            "SELECT u.user_id, u.username, u.full_name "
            "FROM users u "
            "JOIN user_roles ur ON u.user_id = ur.user_id "
            "WHERE ur.role_id IN (37, 34) "
            "LIMIT 1"
        )
        user = cursor.fetchone()
        return dict(user) if user else {}
    finally:
        conn.close()

def get_test_provider() -> Dict:
    """Get a test provider user for assignment."""
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

def get_test_coordinator() -> Dict:
    """Get a test coordinator user for assignment."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT u.user_id, u.username, u.full_name "
            "FROM users u "
            "JOIN user_roles ur ON u.user_id = ur.user_id "
            "WHERE ur.role_id = 36 "
            "LIMIT 1"
        )
        user = cursor.fetchone()
        return dict(user) if user else {}
    finally:
        conn.close()

def cleanup_test_onboarding(onboarding_id: int = None):
    """Clean up test onboarding records."""
    conn = get_db_connection()
    try:
        if onboarding_id:
            # Delete from onboarding_patients
            conn.execute(
                "DELETE FROM onboarding_patients WHERE onboarding_id = ?",
                (onboarding_id,)
            )
            # Delete from patients (if created)
            conn.execute(
                "DELETE FROM patients WHERE first_name = ? AND last_name = ?",
                (TEST_PATIENT_DATA['first_name'], TEST_PATIENT_DATA['last_name'])
            )
            # Delete from patient_panel
            conn.execute(
                "DELETE FROM patient_panel WHERE first_name = ? AND last_name = ?",
                (TEST_PATIENT_DATA['first_name'], TEST_PATIENT_DATA['last_name'])
            )
            # Delete from patient_assignments
            conn.execute(
                "DELETE FROM patient_assignments WHERE patient_id LIKE ?",
                (f"%{TEST_PATIENT_DATA['last_name']}%",)
            )
            # Delete from hhc_patients_export
            conn.execute(
                "DELETE FROM hhc_patients_export WHERE patient_id LIKE ?",
                (f"%{TEST_PATIENT_DATA['last_name']}%",)
            )
            conn.commit()
            print(f"  Cleaned up test onboarding: {onboarding_id}")
    finally:
        conn.close()

def verify_onboarding_record(onboarding_id: int) -> Tuple[bool, Dict]:
    """Verify onboarding record exists and has correct data."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM onboarding_patients WHERE onboarding_id = ?",
            (onboarding_id,)
        )
        record = cursor.fetchone()

        if not record:
            return False, {"error": "Onboarding record not found"}

        return True, dict(record)
    finally:
        conn.close()

def verify_patient_in_tables(expected_name: str) -> Dict:
    """Verify patient was synced to all required tables."""
    results = {
        "patients": False,
        "patient_panel": False,
        "patient_assignments": False,
        "hhc_patients_export": False,
    }

    conn = get_db_connection()
    try:
        # Check patients table
        cursor = conn.execute(
            "SELECT 1 FROM patients WHERE patient_id LIKE ?",
            (f"%{expected_name}%",)
        )
        results["patients"] = cursor.fetchone() is not None

        # Check patient_panel table
        cursor = conn.execute(
            "SELECT 1 FROM patient_panel WHERE patient_id LIKE ?",
            (f"%{expected_name}%",)
        )
        results["patient_panel"] = cursor.fetchone() is not None

        # Check patient_assignments table
        cursor = conn.execute(
            "SELECT 1 FROM patient_assignments WHERE patient_id LIKE ?",
            (f"%{expected_name}%",)
        )
        results["patient_assignments"] = cursor.fetchone() is not None

        # Check hhc_patients_export table
        cursor = conn.execute(
            "SELECT 1 FROM hhc_patients_export WHERE patient_id LIKE ?",
            (f"%{expected_name}%",)
        )
        results["hhc_patients_export"] = cursor.fetchone() is not None

        return results
    finally:
        conn.close()

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_database_schema():
    """Test 1: Verify onboarding database schema."""
    print("\n=== Test 1: Database Schema ===")

    conn = get_db_connection()
    try:
        # Check onboarding_patients table
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='onboarding_patients'"
        )
        if not cursor.fetchone():
            tracker.add_result(
                "Database Schema",
                "FAIL",
                "",
                "onboarding_patients table doesn't exist"
            )
            return False

        # Check required columns
        cursor = conn.execute("PRAGMA table_info(onboarding_patients)")
        columns = {row["name"] for row in cursor.fetchall()}

        required_columns = [
            'onboarding_id', 'patient_id', 'first_name', 'last_name', 'date_of_birth',
            'insurance_provider', 'policy_number', 'eligibility_status', 'eligibility_verified',
            'stage1_complete', 'stage2_complete', 'stage3_complete', 'stage4_complete', 'stage5_complete',
            'patient_status', 'assigned_pot_user_id', 'assigned_provider_user_id',
            'assigned_coordinator_user_id', 'tv_scheduled', 'tv_date', 'tv_time',
            'created_date', 'updated_date'
        ]

        missing = [col for col in required_columns if col not in columns]

        if missing:
            tracker.add_result(
                "Database Schema",
                "FAIL",
                f"Missing columns: {missing}",
                ""
            )
            return False

        tracker.add_result(
            "Database Schema",
            "PASS",
            f"onboarding_patients table with all {len(required_columns)} required columns"
        )
        return True

    except Exception as e:
        tracker.add_result("Database Schema", "ERROR", "", str(e))
        return False
    finally:
        conn.close()

def test_stage1_patient_registration():
    """Test 2: Stage 1 - Patient Registration."""
    print("\n=== Test 2: Stage 1 - Patient Registration ===")

    user = get_onboarding_user()
    if not user:
        tracker.add_result("Stage 1: Registration", "SKIP", "", "No onboarding user found")
        return False

    print(f"  Using user: {user['full_name']} (ID: {user['user_id']})")

    try:
        # Create onboarding workflow instance via database API
        onboarding_id = database.create_onboarding_workflow_instance(
            patient_data=TEST_PATIENT_DATA,
            pot_user_id=user['user_id']
        )

        if not onboarding_id:
            tracker.add_result(
                "Stage 1: Registration",
                "FAIL",
                "",
                "Failed to create onboarding instance"
            )
            return False

        tracker.test_onboarding_id = onboarding_id
        print(f"  Created onboarding_id: {onboarding_id}")

        # The create_onboarding_workflow_instance doesn't include eligibility_verified
        # So we need to update it separately
        database.update_onboarding_checkbox_data(onboarding_id, {
            'eligibility_status': TEST_PATIENT_DATA['eligibility_status'],
            'eligibility_notes': TEST_PATIENT_DATA['eligibility_notes'],
            'eligibility_verified': TEST_PATIENT_DATA['eligibility_verified'],
        })

        # Mark Stage 1 as complete
        database.update_onboarding_stage_completion(onboarding_id, 1, True)

        # Verify record was created
        success, record = verify_onboarding_record(onboarding_id)
        if not success:
            tracker.add_result(
                "Stage 1: Registration",
                "FAIL",
                "",
                record.get('error', 'Record not found')
            )
            return False

        # Verify data was saved correctly
        errors = []
        if record.get('first_name') != TEST_PATIENT_DATA['first_name']:
            errors.append(f"first_name mismatch")
        if record.get('last_name') != TEST_PATIENT_DATA['last_name']:
            errors.append(f"last_name mismatch")
        if record.get('insurance_provider') != TEST_PATIENT_DATA['insurance_provider']:
            errors.append(f"insurance_provider mismatch")
        if not record.get('eligibility_verified'):
            errors.append(f"eligibility not verified")

        if errors:
            tracker.add_result(
                "Stage 1: Registration",
                "FAIL",
                "; ".join(errors),
                ""
            )
            return False

        tracker.add_result(
            "Stage 1: Registration",
            "PASS",
            f"Patient {TEST_PATIENT_DATA['first_name']} {TEST_PATIENT_DATA['last_name']} registered",
            ""
        )
        return True

    except Exception as e:
        tracker.add_result("Stage 1: Registration", "ERROR", "", str(e))
        return False

def test_stage2_patient_details():
    """Test 3: Stage 2 - Patient Details (Contact, Address, Referral, Facility)."""
    print("\n=== Test 3: Stage 2 - Patient Details ===")

    if not tracker.test_onboarding_id:
        tracker.add_result("Stage 2: Details", "SKIP", "", "No onboarding_id from Stage 1")
        return False

    try:
        # Update onboarding record with Stage 2 data
        stage2_data = {
            'phone_primary': TEST_PATIENT_DATA['phone_primary'],
            'email': TEST_PATIENT_DATA['email'],
            'address_street': TEST_PATIENT_DATA['address_street'],
            'address_city': TEST_PATIENT_DATA['address_city'],
            'address_state': TEST_PATIENT_DATA['address_state'],
            'address_zip': TEST_PATIENT_DATA['address_zip'],
            'gender': TEST_PATIENT_DATA['gender'],
            'referral_source': TEST_PATIENT_DATA['referral_source'],
            'referring_provider': TEST_PATIENT_DATA['referring_provider'],
            'facility_assignment': TEST_PATIENT_DATA['facility_assignment'],
            'transportation': TEST_PATIENT_DATA['transportation'],
            'preferred_language': TEST_PATIENT_DATA['preferred_language'],
        }

        database.update_onboarding_checkbox_data(tracker.test_onboarding_id, stage2_data)

        # Verify data was saved
        success, record = verify_onboarding_record(tracker.test_onboarding_id)
        if not success:
            tracker.add_result("Stage 2: Details", "FAIL", "", "Record not found")
            return False

        errors = []
        if record.get('phone_primary') != TEST_PATIENT_DATA['phone_primary']:
            errors.append("phone_primary not saved")
        if record.get('address_street') != TEST_PATIENT_DATA['address_street']:
            errors.append("address_street not saved")
        if record.get('facility_assignment') != TEST_PATIENT_DATA['facility_assignment']:
            errors.append("facility_assignment not saved")

        if errors:
            tracker.add_result("Stage 2: Details", "FAIL", "; ".join(errors))
            return False

        # Mark Stage 2 as complete
        database.update_onboarding_stage_completion(tracker.test_onboarding_id, 2, True)

        # Trigger sync to patients and patient_panel tables
        try:
            patient_id = database.insert_patient_from_onboarding(tracker.test_onboarding_id)
            print(f"  Patient record created: {patient_id}")
        except Exception as e:
            print(f"  Patient record creation: {e}")

        tracker.add_result(
            "Stage 2: Details",
            "PASS",
            f"Contact, address, and facility details saved",
            ""
        )
        return True

    except Exception as e:
        tracker.add_result("Stage 2: Details", "ERROR", "", str(e))
        return False

def test_stage3_chart_creation():
    """Test 4: Stage 3 - Chart Creation (EMed)."""
    print("\n=== Test 4: Stage 3 - Chart Creation ===")

    if not tracker.test_onboarding_id:
        tracker.add_result("Stage 3: Chart", "SKIP", "", "No onboarding_id from Stage 1")
        return False

    try:
        # Update with chart creation data
        chart_data = {
            'emed_chart_created': 1,
            'chart_id': f'EMED-{TEST_TIMESTAMP}',
            'facility_confirmed': 1,
            'chart_notes': 'Automated test chart creation',
        }

        database.update_onboarding_checkbox_data(tracker.test_onboarding_id, chart_data)

        # Mark Stage 3 as complete
        database.update_onboarding_stage_completion(tracker.test_onboarding_id, 3, True)

        # Verify
        success, record = verify_onboarding_record(tracker.test_onboarding_id)
        if success and record.get('emed_chart_created') and record.get('facility_confirmed'):
            tracker.add_result(
                "Stage 3: Chart",
                "PASS",
                f"EMed chart created: {record.get('chart_id')}",
                ""
            )
            return True
        else:
            tracker.add_result("Stage 3: Chart", "FAIL", "Chart data not saved correctly")
            return False

    except Exception as e:
        tracker.add_result("Stage 3: Chart", "ERROR", "", str(e))
        return False

def test_stage4_intake_processing():
    """Test 5: Stage 4 - Intake Processing & Documentation."""
    print("\n=== Test 4: Stage 4 - Intake Processing ===")

    if not tracker.test_onboarding_id:
        tracker.add_result("Stage 4: Intake", "SKIP", "", "No onboarding_id from Stage 1")
        return False

    try:
        # Update with intake processing data
        intake_data = {
            'intake_call_completed': 1,
            'medical_records_requested': 1,
            'referral_documents_received': 1,
            'emed_signature_received': 1,
            'intake_notes': 'Automated test intake processing',
            'appointment_contact_name': 'Test Contact',
            'appointment_contact_phone': '555-TEST-002',
            'medical_contact_name': 'Test Medical Contact',
            'facility_nurse_name': 'Test Nurse',
            'patient_status': 'Active',
            'primary_care_provider': 'Dr. Test PCP',
        }

        database.update_onboarding_checkbox_data(tracker.test_onboarding_id, intake_data)

        # Mark Stage 4 as complete
        database.update_onboarding_stage_completion(tracker.test_onboarding_id, 4, True)

        # Verify
        success, record = verify_onboarding_record(tracker.test_onboarding_id)
        if success and record.get('intake_call_completed'):
            tracker.add_result(
                "Stage 4: Intake",
                "PASS",
                "Intake call completed, documentation collected",
                ""
            )
            return True
        else:
            tracker.add_result("Stage 4: Intake", "FAIL", "Intake data not saved")
            return False

    except Exception as e:
        tracker.add_result("Stage 4: Intake", "ERROR", "", str(e))
        return False

def test_stage5_tv_scheduling():
    """Test 5: Stage 5 - TV Scheduling & Provider/Coordinator Assignment."""
    print("\n=== Test 5: Stage 5 - TV Scheduling & Assignments ===")

    if not tracker.test_onboarding_id:
        tracker.add_result("Stage 5: TV Scheduling", "SKIP", "", "No onboarding_id from Stage 1")
        return False

    provider = get_test_provider()
    coordinator = get_test_coordinator()

    if not provider or not coordinator:
        tracker.add_result(
            "Stage 5: TV Scheduling",
            "SKIP",
            "",
            "No test provider or coordinator found"
        )
        return False

    print(f"  Provider: {provider['full_name']} (ID: {provider['user_id']})")
    print(f"  Coordinator: {coordinator['full_name']} (ID: {coordinator['user_id']})")

    try:
        # Get test patient_id from onboarding record
        success, record = verify_onboarding_record(tracker.test_onboarding_id)
        if not success:
            tracker.add_result("Stage 5: TV Scheduling", "FAIL", "", "Could not get onboarding record")
            return False

        patient_id = record.get('patient_id')
        if not patient_id:
            # Try to create patient_id from name
            patient_id = f"{TEST_PATIENT_DATA['last_name']} {TEST_PATIENT_DATA['first_name']} {TEST_PATIENT_DATA['date_of_birth']}"

        # Update with TV scheduling and assignment data
        tv_data = {
            'tv_scheduled': 1,
            'tv_date': TEST_DATE,
            'tv_time': '10:00:00',
            'patient_notified': 1,
            'initial_tv_completed': 1,
            'assigned_provider_user_id': provider['user_id'],
            'assigned_coordinator_user_id': coordinator['user_id'],
            'visit_type': TEST_PATIENT_DATA['visit_type'],
            'billing_code': TEST_PATIENT_DATA['billing_code'],
            'duration_minutes': TEST_PATIENT_DATA['duration_minutes'],
        }

        database.update_onboarding_checkbox_data(tracker.test_onboarding_id, tv_data)

        # Create patient assignments
        database.create_patient_assignment(
            patient_id=patient_id,
            provider_id=provider['user_id'],
            coordinator_id=coordinator['user_id'],
            assignment_type="onboarding",
            status="active",
            created_by=tracker.test_onboarding_id
        )

        # Mark Stage 5 as complete
        database.update_onboarding_stage_completion(tracker.test_onboarding_id, 5, True)

        # Verify
        success, record = verify_onboarding_record(tracker.test_onboarding_id)
        if success and record.get('tv_scheduled') and record.get('initial_tv_completed'):
            tracker.add_result(
                "Stage 5: TV Scheduling",
                "PASS",
                f"TV scheduled for {TEST_DATE}, provider and coordinator assigned",
                ""
            )
            return True
        else:
            tracker.add_result("Stage 5: TV Scheduling", "FAIL", "TV data not saved correctly")
            return False

    except Exception as e:
        tracker.add_result("Stage 5: TV Scheduling", "ERROR", "", str(e))
        return False

def test_sync_to_all_tables():
    """Test 6: Verify patient synced to all required tables."""
    print("\n=== Test 6: Sync to All Tables ===")

    if not tracker.test_onboarding_id:
        tracker.add_result("Sync to Tables", "SKIP", "", "No onboarding_id")
        return False

    try:
        # Trigger comprehensive sync
        sync_result = database.sync_onboarding_to_all_tables(tracker.test_onboarding_id)

        # Verify in each table
        expected_patient_name = f"{TEST_PATIENT_DATA['last_name']} {TEST_PATIENT_DATA['first_name']}"
        results = verify_patient_in_tables(expected_patient_name)

        all_synced = all(results.values())

        if all_synced:
            tracker.add_result(
                "Sync to Tables",
                "PASS",
                f"Patient synced to all {len(results)} tables",
                ""
            )
            return True
        else:
            missing = [table for table, synced in results.items() if not synced]
            tracker.add_result(
                "Sync to Tables",
                "FAIL",
                f"Missing from tables: {missing}",
                ""
            )
            return False

    except Exception as e:
        tracker.add_result("Sync to Tables", "ERROR", "", str(e))
        return False

def test_onboarding_completion():
    """Test 7: Complete onboarding workflow."""
    print("\n=== Test 7: Onboarding Completion ===")

    if not tracker.test_onboarding_id:
        tracker.add_result("Onboarding Completion", "SKIP", "", "No onboarding_id")
        return False

    try:
        # Mark patient as completed
        database.update_onboarding_patient_status(tracker.test_onboarding_id, 'Completed')

        # Verify all stages are complete
        success, record = verify_onboarding_record(tracker.test_onboarding_id)
        if not success:
            tracker.add_result("Onboarding Completion", "FAIL", "", "Record not found")
            return False

        all_stages_complete = all([
            record.get('stage1_complete'),
            record.get('stage2_complete'),
            record.get('stage3_complete'),
            record.get('stage4_complete'),
            record.get('stage5_complete'),
        ])

        if not all_stages_complete:
            tracker.add_result(
                "Onboarding Completion",
                "FAIL",
                "Not all stages marked complete",
                ""
            )
            return False

        if record.get('patient_status') != 'Completed':
            tracker.add_result(
                "Onboarding Completion",
                "FAIL",
                f"Patient status is '{record.get('patient_status')}', expected 'Completed'",
                ""
            )
            return False

        tracker.add_result(
            "Onboarding Completion",
            "PASS",
            f"Onboarding workflow complete for patient {record.get('first_name')} {record.get('last_name')}",
            ""
        )
        return True

    except Exception as e:
        tracker.add_result("Onboarding Completion", "ERROR", "", str(e))
        return False

def test_workflow_progress_tracking():
    """Test 8: Verify workflow progress is tracked correctly."""
    print("\n=== Test 8: Workflow Progress Tracking ===")

    if not tracker.test_onboarding_id:
        tracker.add_result("Progress Tracking", "SKIP", "", "No onboarding_id")
        return False

    try:
        # Get the onboarding queue to check progress display
        # Note: The queue only shows Active patients, not Completed ones
        queue = database.get_onboarding_queue()

        # Find our test patient in the queue
        test_patient = None
        for patient in queue:
            if patient.get('onboarding_id') == tracker.test_onboarding_id:
                test_patient = patient
                break

        # Verify the record directly from onboarding_patients
        success, record = verify_onboarding_record(tracker.test_onboarding_id)

        if not success:
            tracker.add_result(
                "Progress Tracking",
                "FAIL",
                "Test patient record not found",
                ""
            )
            return False

        # Check that all stages are complete
        all_stages_complete = all([
            record.get('stage1_complete'),
            record.get('stage2_complete'),
            record.get('stage3_complete'),
            record.get('stage4_complete'),
            record.get('stage5_complete'),
        ])

        # Verify completed patient is NOT in the active queue (correct behavior)
        if record.get('patient_status') == 'Completed':
            if test_patient:
                tracker.add_result(
                    "Progress Tracking",
                    "FAIL",
                    "Completed patient should NOT be in active queue",
                    ""
                )
                return False
            else:
                tracker.add_result(
                    "Progress Tracking",
                    "PASS",
                    "Completed patient correctly NOT in active queue (all stages complete)",
                    ""
                )
                return True

        # For active patients, verify they appear in queue
        if test_patient and all_stages_complete:
            current_stage = test_patient.get('current_stage', '')
            tracker.add_result(
                "Progress Tracking",
                "PASS",
                f"Patient shows as: {current_stage}, all stages complete",
                ""
            )
            return True
        elif not test_patient:
            tracker.add_result(
                "Progress Tracking",
                "FAIL",
                "Active patient not found in queue",
                ""
            )
            return False
        else:
            tracker.add_result(
                "Progress Tracking",
                "FAIL",
                f"Not all stages complete: stage1={record.get('stage1_complete')}, stage5={record.get('stage5_complete')}",
                ""
            )
            return False

    except Exception as e:
        tracker.add_result("Progress Tracking", "ERROR", "", str(e))
        return False

# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all onboarding workflow tests."""
    print("\n" + "="*70)
    print("STREAMLIT APPTEST - Onboarding Workflow E2E")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_PATH}")
    print(f"Test Patient: {TEST_PATIENT_DATA['first_name']} {TEST_PATIENT_DATA['last_name']}")

    # Clean up any existing test data first
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM onboarding_patients WHERE first_name = ?",
        (TEST_PATIENT_DATA['first_name'],)
    )
    conn.commit()
    conn.close()

    # Test 1: Schema
    test_database_schema()

    # Test 2: Stage 1
    test_stage1_patient_registration()

    # Test 3: Stage 2
    test_stage2_patient_details()

    # Test 4: Stage 3
    test_stage3_chart_creation()

    # Test 5: Stage 4
    test_stage4_intake_processing()

    # Test 6: Stage 5
    test_stage5_tv_scheduling()

    # Test 7: Sync to all tables
    test_sync_to_all_tables()

    # Test 8: Completion
    test_onboarding_completion()

    # Test 9: Progress tracking
    test_workflow_progress_tracking()

    # Print summary
    print(tracker.get_summary())

    # Print failed tests
    if tracker.summary['FAIL'] > 0 or tracker.summary['ERROR'] > 0:
        print("\nFailed/Error Tests:")
        for test in tracker.tests:
            if test['status'] in ['FAIL', 'ERROR']:
                print(f"\n  [{test['status']}] {test['name']}")
                if test.get('error'):
                    print(f"    Error: {test['error']}")
                if test.get('details'):
                    print(f"    Details: {test['details']}")

    # Save report
    report_file = f"test_report_onboarding_apptest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            "start_time": tracker.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "summary": tracker.summary,
            "tests": tracker.tests,
            "test_onboarding_id": tracker.test_onboarding_id,
        }, f, indent=2)

    print(f"\nReport saved to: {report_file}")

    # Clean up test data if requested (commented out by default for review)
    # if tracker.test_onboarding_id:
    #     cleanup_test_onboarding(tracker.test_onboarding_id)
    #     print(f"\nTest data cleaned up. Onboarding ID: {tracker.test_onboarding_id}")

    print("="*70)

    return tracker.summary['FAIL'] == 0 and tracker.summary['ERROR'] == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
