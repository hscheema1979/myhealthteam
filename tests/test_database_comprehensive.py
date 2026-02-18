"""
Comprehensive Database Module Tests
Tests all database operations, connections, and queries.

Tests:
- Database connections
- Patient operations (CRUD)
- User operations (CRUD)
- Coordinator operations
- Provider operations
- Workflow operations
- Billing operations
- Facility operations
- ETL operations
"""

import sys
from pathlib import Path
from datetime import datetime
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import database

class DatabaseTest:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def test_database_connection(self):
        """Test database connection functionality"""
        tests = []

        # Test 1: Can get connection
        try:
            conn = database.get_db_connection()
            if conn:
                conn.close()
                tests.append({
                    "name": "Database Connection",
                    "status": "PASS",
                    "details": "Successfully opened and closed connection"
                })
            else:
                tests.append({
                    "name": "Database Connection",
                    "status": "FAIL",
                    "error": "Connection returned None"
                })
        except Exception as e:
            tests.append({
                "name": "Database Connection",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Can execute query
        try:
            conn = database.get_db_connection()
            result = conn.execute("SELECT 1").fetchone()
            conn.close()

            if result and result[0] == 1:
                tests.append({
                    "name": "Execute Query",
                    "status": "PASS",
                    "details": "Query execution successful"
                })
            else:
                tests.append({
                    "name": "Execute Query",
                    "status": "FAIL",
                    "error": "Unexpected query result"
                })
        except Exception as e:
            tests.append({
                "name": "Execute Query",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: Database file exists
        try:
            db_path = Path(database.DB_PATH)
            if db_path.exists():
                size_mb = db_path.stat().st_size / (1024 * 1024)
                tests.append({
                    "name": "Database File Exists",
                    "status": "PASS",
                    "details": f"Database size: {size_mb:.2f} MB"
                })
            else:
                tests.append({
                    "name": "Database File Exists",
                    "status": "FAIL",
                    "error": f"Database file not found at {database.DB_PATH}"
                })
        except Exception as e:
            tests.append({
                "name": "Database File Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_patient_operations(self):
        """Test patient CRUD operations"""
        tests = []

        # Test 1: Get all patients
        try:
            patients = database.get_all_patients()
            tests.append({
                "name": "Get All Patients",
                "status": "PASS",
                "details": f"Retrieved {len(patients) if patients else 0} patients"
            })
        except Exception as e:
            tests.append({
                "name": "Get All Patients",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Get patient panel
        try:
            panel = database.get_all_patient_panel()
            tests.append({
                "name": "Get Patient Panel",
                "status": "PASS",
                "details": f"Retrieved {len(panel) if panel else 0} panel records"
            })
        except Exception as e:
            tests.append({
                "name": "Get Patient Panel",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: Get patient by ID
        try:
            patients = database.get_all_patients()
            if patients and len(patients) > 0:
                test_patient_id = patients[0]['patient_id']
                patient = database.get_patient_by_id(test_patient_id)

                if patient:
                    tests.append({
                        "name": "Get Patient By ID",
                        "status": "PASS",
                        "details": f"Retrieved patient {test_patient_id}"
                    })
                else:
                    tests.append({
                        "name": "Get Patient By ID",
                        "status": "FAIL",
                        "error": f"Patient {test_patient_id} not found"
                    })
        except Exception as e:
            tests.append({
                "name": "Get Patient By ID",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 4: Patient tables exist
        try:
            conn = database.get_db_connection()
            patients_table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='patients'"
            ).fetchone()
            patient_panel_table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='patient_panel'"
            ).fetchone()
            conn.close()

            if patients_table and patient_panel_table:
                tests.append({
                    "name": "Patient Tables Exist",
                    "status": "PASS",
                    "details": "patients and patient_panel tables found"
                })
            else:
                tests.append({
                    "name": "Patient Tables Exist",
                    "status": "FAIL",
                    "error": "One or both patient tables missing"
                })
        except Exception as e:
            tests.append({
                "name": "Patient Tables Exist",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_user_operations(self):
        """Test user CRUD operations"""
        tests = []

        # Test 1: Get all users
        try:
            users = database.get_all_users()
            tests.append({
                "name": "Get All Users",
                "status": "PASS",
                "details": f"Retrieved {len(users) if users else 0} users"
            })
        except Exception as e:
            tests.append({
                "name": "Get All Users",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Get user roles
        try:
            roles = database.get_all_roles()
            tests.append({
                "name": "Get All Roles",
                "status": "PASS",
                "details": f"Retrieved {len(roles) if roles else 0} roles"
            })
        except Exception as e:
            tests.append({
                "name": "Get All Roles",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: Get user by ID
        try:
            users = database.get_all_users()
            if users and len(users) > 0:
                test_user_id = users[0]['user_id']
                user = database.get_user_by_id(test_user_id)

                if user:
                    tests.append({
                        "name": "Get User By ID",
                        "status": "PASS",
                        "details": f"Retrieved user {test_user_id}"
                    })
                else:
                    tests.append({
                        "name": "Get User By ID",
                        "status": "FAIL",
                        "error": f"User {test_user_id} not found"
                    })
        except Exception as e:
            tests.append({
                "name": "Get User By ID",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 4: Get user roles by user ID
        try:
            users = database.get_all_users()
            if users and len(users) > 0:
                test_user_id = users[0]['user_id']
                user_roles = database.get_user_roles_by_user_id(test_user_id)

                tests.append({
                    "name": "Get User Roles By User ID",
                    "status": "PASS",
                    "details": f"Retrieved {len(user_roles)} roles for user {test_user_id}"
                })
        except Exception as e:
            tests.append({
                "name": "Get User Roles By User ID",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 5: Get users by role
        try:
            role_users = database.get_users_by_role(33)  # Care Provider
            tests.append({
                "name": "Get Users By Role",
                "status": "PASS",
                "details": f"Retrieved {len(role_users)} users for role 33"
            })
        except Exception as e:
            tests.append({
                "name": "Get Users By Role",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_coordinator_operations(self):
        """Test coordinator operations"""
        tests = []

        # Test 1: Get all coordinators
        try:
            coordinators = database.get_users_by_role("CC")  # Care Coordinator
            tests.append({
                "name": "Get Coordinators",
                "status": "PASS",
                "details": f"Retrieved {len(coordinators)} coordinators"
            })
        except Exception as e:
            tests.append({
                "name": "Get Coordinators",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Coordinator tasks table exists
        try:
            conn = database.get_db_connection()
            current_month = datetime.now().strftime("%Y_%m")
            table_name = f"coordinator_tasks_{current_month}"
            result = conn.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            ).fetchone()
            conn.close()

            if result:
                tests.append({
                    "name": "Coordinator Tasks Table Exists",
                    "status": "PASS",
                    "details": f"Table {table_name} found"
                })
            else:
                tests.append({
                    "name": "Coordinator Tasks Table Exists",
                    "status": "FAIL",
                    "error": f"Table {table_name} not found"
                })
        except Exception as e:
            tests.append({
                "name": "Coordinator Tasks Table Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_provider_operations(self):
        """Test provider operations"""
        tests = []

        # Test 1: Get all providers
        try:
            providers = database.get_users_by_role(33)  # Care Provider
            tests.append({
                "name": "Get Providers",
                "status": "PASS",
                "details": f"Retrieved {len(providers)} providers"
            })
        except Exception as e:
            tests.append({
                "name": "Get Providers",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Provider tasks table exists
        try:
            conn = database.get_db_connection()
            current_month = datetime.now().strftime("%Y_%m")
            table_name = f"provider_tasks_{current_month}"
            result = conn.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            ).fetchone()
            conn.close()

            if result:
                tests.append({
                    "name": "Provider Tasks Table Exists",
                    "status": "PASS",
                    "details": f"Table {table_name} found"
                })
            else:
                tests.append({
                    "name": "Provider Tasks Table Exists",
                    "status": "FAIL",
                    "error": f"Table {table_name} not found"
                })
        except Exception as e:
            tests.append({
                "name": "Provider Tasks Table Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_workflow_operations(self):
        """Test workflow operations"""
        tests = []

        # Test 1: Workflow templates table exists
        try:
            conn = database.get_db_connection()
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_templates'"
            ).fetchone()
            conn.close()

            if result:
                tests.append({
                    "name": "Workflow Templates Table Exists",
                    "status": "PASS",
                    "details": "Table found"
                })
            else:
                tests.append({
                    "name": "Workflow Templates Table Exists",
                    "status": "FAIL",
                    "error": "Table not found"
                })
        except Exception as e:
            tests.append({
                "name": "Workflow Templates Table Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Workflow instances table exists
        try:
            conn = database.get_db_connection()
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_instances'"
            ).fetchone()
            conn.close()

            if result:
                tests.append({
                    "name": "Workflow Instances Table Exists",
                    "status": "PASS",
                    "details": "Table found"
                })
            else:
                tests.append({
                    "name": "Workflow Instances Table Exists",
                    "status": "FAIL",
                    "error": "Table not found"
                })
        except Exception as e:
            tests.append({
                "name": "Workflow Instances Table Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: Can query workflow templates
        try:
            conn = database.get_db_connection()
            templates = conn.execute("SELECT * FROM workflow_templates").fetchall()
            conn.close()

            tests.append({
                "name": "Query Workflow Templates",
                "status": "PASS",
                "details": f"Retrieved {len(templates)} templates"
            })
        except Exception as e:
            tests.append({
                "name": "Query Workflow Templates",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_billing_operations(self):
        """Test billing operations"""
        tests = []

        # Test 1: Task billing codes table exists
        try:
            conn = database.get_db_connection()
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='task_billing_codes'"
            ).fetchone()
            conn.close()

            if result:
                tests.append({
                    "name": "Task Billing Codes Table Exists",
                    "status": "PASS",
                    "details": "Table found"
                })
            else:
                tests.append({
                    "name": "Task Billing Codes Table Exists",
                    "status": "FAIL",
                    "error": "Table not found"
                })
        except Exception as e:
            tests.append({
                "name": "Task Billing Codes Table Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Provider task billing status table exists
        try:
            conn = database.get_db_connection()
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='provider_task_billing_status'"
            ).fetchone()
            conn.close()

            if result:
                tests.append({
                    "name": "Provider Task Billing Status Table Exists",
                    "status": "PASS",
                    "details": "Table found"
                })
            else:
                tests.append({
                    "name": "Provider Task Billing Status Table Exists",
                    "status": "FAIL",
                    "error": "Table not found"
                })
        except Exception as e:
            tests.append({
                "name": "Provider Task Billing Status Table Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_facility_operations(self):
        """Test facility operations"""
        tests = []

        # Test 1: Get all facilities
        try:
            facilities = database.get_all_facilities()
            tests.append({
                "name": "Get All Facilities",
                "status": "PASS",
                "details": f"Retrieved {len(facilities)} facilities"
            })
        except Exception as e:
            tests.append({
                "name": "Get All Facilities",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: User facility assignments table exists
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

        return tests

    def run_all_tests(self):
        """Run all database tests"""
        print("\n" + "="*70)
        print("DATABASE MODULE - COMPREHENSIVE TESTS")
        print("="*70 + "\n")

        test_suites = [
            ("Database Connection", self.test_database_connection),
            ("Patient Operations", self.test_patient_operations),
            ("User Operations", self.test_user_operations),
            ("Coordinator Operations", self.test_coordinator_operations),
            ("Provider Operations", self.test_provider_operations),
            ("Workflow Operations", self.test_workflow_operations),
            ("Billing Operations", self.test_billing_operations),
            ("Facility Operations", self.test_facility_operations),
        ]

        all_results = []

        for suite_name, test_func in test_suites:
            print(f"\nTesting: {suite_name}")
            print("-" * 70)

            results = test_func()
            all_results.extend(results)

            for result in results:
                symbol = "[OK]" if result["status"] == "PASS" else "[FAIL]"
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
        print("DATABASE TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total Tests: {len(self.results)}")
        print(f"  [OK] PASSED: {passed}")
        print(f"  [FAIL] FAILED: {failed}")
        print(f"{'='*70}\n")

        # Save to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_database_comprehensive_{timestamp}.json"
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
    tester = DatabaseTest()
    tester.run_all_tests()
    success = tester.print_summary()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
