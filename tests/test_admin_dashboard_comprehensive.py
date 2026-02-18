"""
Comprehensive Admin Dashboard Tests
Tests all tabs, components, and functionality in the admin dashboard.

Tests:
- Patient Info tab with editable columns
- User Roles tab with role assignment
- Facility Management tab with CRUD operations
- Staff Onboarding tab
- System metrics and statistics
- Database operations
"""

import sys
from pathlib import Path
from datetime import datetime
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import database

class AdminDashboardTest:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def test_patient_info_tab(self):
        """Test Patient Info tab functionality"""
        tests = []

        # Test 1: Patient data loads
        try:
            patients = database.get_all_patients()
            if patients and len(patients) > 0:
                tests.append({
                    "name": "Patient Data Loads",
                    "status": "PASS",
                    "details": f"Loaded {len(patients)} patients"
                })
            else:
                tests.append({
                    "name": "Patient Data Loads",
                    "status": "FAIL",
                    "details": "No patients loaded",
                    "error": "Patient query returned empty or None"
                })
        except Exception as e:
            tests.append({
                "name": "Patient Data Loads",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Editable columns exist
        try:
            conn = database.get_db_connection()
            patient_columns = conn.execute("PRAGMA table_info(patients)").fetchall()
            conn.close()

            column_names = [col[1] for col in patient_columns]
            required_editable = ["labs_notes", "imaging_notes", "general_notes"]

            missing = [col for col in required_editable if col not in column_names]

            if not missing:
                tests.append({
                    "name": "Editable Notes Columns Exist",
                    "status": "PASS",
                    "details": f"All editable columns present: {', '.join(required_editable)}"
                })
            else:
                tests.append({
                    "name": "Editable Notes Columns Exist",
                    "status": "FAIL",
                    "details": f"Missing columns: {', '.join(missing)}"
                })
        except Exception as e:
            tests.append({
                "name": "Editable Notes Columns Exist",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: Patient panel view
        try:
            panel_data = database.get_all_patient_panel()
            if panel_data and len(panel_data) > 0:
                tests.append({
                    "name": "Patient Panel View Loads",
                    "status": "PASS",
                    "details": f"Loaded {len(panel_data)} patient panel records"
                })
            else:
                tests.append({
                    "name": "Patient Panel View Loads",
                    "status": "FAIL",
                    "error": "Patient panel query returned empty"
                })
        except Exception as e:
            tests.append({
                "name": "Patient Panel View Loads",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_user_roles_tab(self):
        """Test User Roles tab functionality"""
        tests = []

        # Test 1: Users load
        try:
            users = database.get_all_users()
            if users and len(users) > 0:
                tests.append({
                    "name": "User List Loads",
                    "status": "PASS",
                    "details": f"Loaded {len(users)} users"
                })
            else:
                tests.append({
                    "name": "User List Loads",
                    "status": "FAIL",
                    "error": "No users loaded"
                })
        except Exception as e:
            tests.append({
                "name": "User List Loads",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Roles load
        try:
            roles = database.get_all_roles()
            if roles and len(roles) > 0:
                tests.append({
                    "name": "Role List Loads",
                    "status": "PASS",
                    "details": f"Loaded {len(roles)} roles"
                })
            else:
                tests.append({
                    "name": "Role List Loads",
                    "status": "FAIL",
                    "error": "No roles loaded"
                })
        except Exception as e:
            tests.append({
                "name": "Role List Loads",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: RR role exists
        try:
            conn = database.get_db_connection()
            result = conn.execute(
                "SELECT role_id, role_name, description FROM roles WHERE role_name = 'RR'"
            ).fetchone()
            conn.close()

            if result and result[0] == 43:
                tests.append({
                    "name": "Results Reviewer Role Exists",
                    "status": "PASS",
                    "details": f"Role ID: {result[0]}, Description: {result[2]}"
                })
            else:
                tests.append({
                    "name": "Results Reviewer Role Exists",
                    "status": "FAIL",
                    "error": "RR role not found or incorrect ID"
                })
        except Exception as e:
            tests.append({
                "name": "Results Reviewer Role Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 4: User role assignments work
        try:
            if len(users) > 0:
                test_user = users[0]
                user_roles = database.get_user_roles_by_user_id(test_user['user_id'])
                tests.append({
                    "name": "User Role Query Works",
                    "status": "PASS",
                    "details": f"Retrieved {len(user_roles)} roles for test user"
                })
        except Exception as e:
            tests.append({
                "name": "User Role Query Works",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_facility_management_tab(self):
        """Test Facility Management tab functionality"""
        tests = []

        # Test 1: Facilities table exists
        try:
            conn = database.get_db_connection()
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='facilities'"
            ).fetchone()
            conn.close()

            if result:
                tests.append({
                    "name": "Facilities Table Exists",
                    "status": "PASS",
                    "details": "Facilities table found"
                })
            else:
                tests.append({
                    "name": "Facilities Table Exists",
                    "status": "FAIL",
                    "error": "Facilities table not found"
                })
        except Exception as e:
            tests.append({
                "name": "Facilities Table Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Facility columns correct
        try:
            conn = database.get_db_connection()
            columns = conn.execute("PRAGMA table_info(facilities)").fetchall()
            conn.close()

            column_names = [col[1] for col in columns]
            required = ["facility_id", "facility_name", "address", "phone", "email", "created_date"]
            missing = [col for col in required if col not in column_names]

            if not missing:
                tests.append({
                    "name": "Facility Table Columns Correct",
                    "status": "PASS",
                    "details": f"All {len(required)} required columns present"
                })
            else:
                tests.append({
                    "name": "Facility Table Columns Correct",
                    "status": "FAIL",
                    "details": f"Missing: {', '.join(missing)}"
                })
        except Exception as e:
            tests.append({
                "name": "Facility Table Columns Correct",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: User facility assignments table exists
        try:
            conn = database.get_db_connection()
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='user_facility_assignments'"
            ).fetchone()
            conn.close()

            if result:
                tests.append({
                    "name": "User Facility Assignments Table Exists",
                    "status": "PASS",
                    "details": "Table found"
                })
            else:
                tests.append({
                    "name": "User Facility Assignments Table Exists",
                    "status": "FAIL",
                    "error": "Table not found"
                })
        except Exception as e:
            tests.append({
                "name": "User Facility Assignments Table Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 4: Can query facilities
        try:
            facilities = database.get_all_facilities()
            tests.append({
                "name": "Query All Facilities Works",
                "status": "PASS",
                "details": f"Retrieved {len(facilities)} facilities"
            })
        except Exception as e:
            tests.append({
                "name": "Query All Facilities Works",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_staff_onboarding_tab(self):
        """Test Staff Onboarding tab functionality"""
        tests = []

        # Test 1: Can create user query works
        try:
            conn = database.get_db_connection()
            # Test the structure of users table
            columns = conn.execute("PRAGMA table_info(users)").fetchall()
            conn.close()

            column_names = [col[1] for col in columns]
            required = ["user_id", "username", "full_name", "email", "password", "status"]

            missing = [col for col in required if col not in column_names]

            if not missing:
                tests.append({
                    "name": "Users Table Structure Correct",
                    "status": "PASS",
                    "details": f"All {len(required)} required columns present"
                })
            else:
                tests.append({
                    "name": "Users Table Structure Correct",
                    "status": "FAIL",
                    "details": f"Missing: {', '.join(missing)}"
                })
        except Exception as e:
            tests.append({
                "name": "Users Table Structure Correct",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: User roles table exists
        try:
            conn = database.get_db_connection()
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='user_roles'"
            ).fetchone()
            conn.close()

            if result:
                tests.append({
                    "name": "User Roles Table Exists",
                    "status": "PASS",
                    "details": "Table found"
                })
            else:
                tests.append({
                    "name": "User Roles Table Exists",
                    "status": "FAIL",
                    "error": "Table not found"
                })
        except Exception as e:
            tests.append({
                "name": "User Roles Table Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_system_metrics(self):
        """Test system metrics and statistics"""
        tests = []

        # Test 1: Patient count
        try:
            conn = database.get_db_connection()
            patient_count = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
            conn.close()

            tests.append({
                "name": "Patient Count Metric",
                "status": "PASS",
                "details": f"Total patients: {patient_count}"
            })
        except Exception as e:
            tests.append({
                "name": "Patient Count Metric",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: User count
        try:
            users = database.get_all_users()
            tests.append({
                "name": "User Count Metric",
                "status": "PASS",
                "details": f"Total users: {len(users)}"
            })
        except Exception as e:
            tests.append({
                "name": "User Count Metric",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: Facility count
        try:
            facilities = database.get_all_facilities()
            tests.append({
                "name": "Facility Count Metric",
                "status": "PASS",
                "details": f"Total facilities: {len(facilities)}"
            })
        except Exception as e:
            tests.append({
                "name": "Facility Count Metric",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def run_all_tests(self):
        """Run all admin dashboard tests"""
        print("\n" + "="*70)
        print("ADMIN DASHBOARD - COMPREHENSIVE TESTS")
        print("="*70 + "\n")

        test_suites = [
            ("Patient Info Tab", self.test_patient_info_tab),
            ("User Roles Tab", self.test_user_roles_tab),
            ("Facility Management Tab", self.test_facility_management_tab),
            ("Staff Onboarding Tab", self.test_staff_onboarding_tab),
            ("System Metrics", self.test_system_metrics),
        ]

        all_results = []

        for suite_name, test_func in test_suites:
            print(f"\nTesting: {suite_name}")
            print("-" * 70)

            results = test_func()
            all_results.extend(results)

            for result in results:
                symbol = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
                print(f"{symbol} {result['name']}: {result['status']}")
                if "details" in result:
                    print(f"  {result['details']}")
                if "error" in result:
                    print(f"  ERROR: {result['error'][:100]}")

        self.results = all_results
        return all_results

    def print_summary(self):
        """Print test summary"""
        duration = (datetime.now() - self.start_time).total_seconds()
        passed = sum(1 for t in self.results if t["status"] == "PASS")
        failed = sum(1 for t in self.results if t["status"] == "FAIL")

        print(f"\n{'='*70}")
        print("ADMIN DASHBOARD TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total Tests: {len(self.results)}")
        print(f"  [OK] PASSED: {passed}")
        print(f"  [FAIL] FAILED: {failed}")
        print(f"{'='*70}\n")

        # Save to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_admin_comprehensive_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "duration": duration,
                "tests": self.results,
                "summary": {
                    "total": len(self.results),
                    "passed": passed,
                    "failed": failed
                }
            }, f, indent=2)

        print(f"Test report saved to: {filename}\n")

        return failed == 0

def main():
    tester = AdminDashboardTest()
    tester.run_all_tests()
    success = tester.print_summary()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
