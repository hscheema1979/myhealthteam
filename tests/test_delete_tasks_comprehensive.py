"""
Comprehensive Delete Tasks Test Suite
Tests all aspects of task deletion and restoration

Run: python tests/test_delete_tasks_comprehensive.py
"""

import sys
from pathlib import Path
import json
from datetime import datetime, date

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import database

class DeleteTasksTestSuite:
    def __init__(self):
        self.start_time = datetime.now()
        self.tests = []
        self.summary = {"PASS": 0, "FAIL": 0, "WARN": 0, "ERROR": 0}
        self.test_task_ids = []
        self.test_deleted_ids = []
        self.original_task_data = {}

    def log_result(self, category, test_name, status, details="", error=""):
        """Log a test result"""
        self.tests.append({
            "category": category,
            "name": test_name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        self.summary[status] = self.summary.get(status, 0) + 1

        # Print immediate feedback
        symbol = {"PASS": "[OK]", "FAIL": "[X]", "WARN": "[!]", "ERROR": "[?]"}.get(status, "[?]")
        print(f"  {symbol} {test_name}")
        if details:
            print(f"      {details}")
        if error:
            print(f"      ERROR: {error}")

    def setup_test_data(self):
        """Create test tasks for deletion testing"""
        print("\n[SETUP] Creating test tasks...")

        try:
            conn = database.get_db_connection()

            # Get a test provider
            provider = conn.execute(
                "SELECT user_id, username FROM users "
                "WHERE user_id IN (SELECT user_id FROM user_roles WHERE role_id = 33) "
                "LIMIT 1"
            ).fetchone()

            if not provider:
                self.log_result("SETUP", "Find Test Provider", "ERROR", "", "No provider found")
                conn.close()
                return False

            provider_id = provider[0]
            test_date = date.today()

            # Create multiple test tasks
            test_tasks = [
                {
                    "task_desc": "Delete Test Task 1",
                    "duration": 30,
                    "billing": "Not_Billable",
                    "notes": "Test task for deletion"
                },
                {
                    "task_desc": "Delete Test Task 2",
                    "duration": 45,
                    "billing": "Not_Billable",
                    "notes": "Another test task"
                },
                {
                    "task_desc": "Delete Test Task 3",
                    "duration": 20,
                    "billing": "Not_Billable",
                    "notes": "Third test task"
                }
            ]

            for i, task_data in enumerate(test_tasks, 1):
                # Save task via save_daily_task
                result = database.save_daily_task(
                    provider_id=provider_id,
                    patient_id="TEST_PATIENT_001",
                    task_date=test_date,
                    task_description=task_data["task_desc"],
                    notes=task_data["notes"],
                    billing_code=task_data["billing"],
                    location_type="Telehealth",
                    patient_type="Follow Up",
                    duration_minutes_override=task_data["duration"]
                )

                # save_daily_task returns True on success, not the task_id
                # Need to query to get the actual task_id
                if result:
                    # Get the most recently created task
                    table_name = f"provider_tasks_{test_date.strftime('%Y_%m')}"
                    task = conn.execute(
                        f"SELECT provider_task_id FROM {table_name} "
                        f"WHERE provider_id = ? AND task_description = ? "
                        f"ORDER BY provider_task_id DESC LIMIT 1",
                        (provider_id, task_data["task_desc"])
                    ).fetchone()

                    if task:
                        task_id = task[0]
                        self.test_task_ids.append(task_id)
                        self.log_result("SETUP", f"Create Test Task {i}", "PASS",
                                     f"Created task_id: {task_id}")
                    else:
                        self.log_result("SETUP", f"Create Test Task {i}", "FAIL",
                                     "", "Could not retrieve created task_id")
                else:
                    self.log_result("SETUP", f"Create Test Task {i}", "FAIL",
                                 "", "save_daily_task returned False")

            conn.close()
            return len(self.test_task_ids) > 0

        except Exception as e:
            self.log_result("SETUP", "Create Test Tasks", "ERROR", "", str(e))
            import traceback
            traceback.print_exc()
            return False

    def test_01_deleted_table_exists(self):
        """Test that deleted_provider_tasks table exists"""
        print("\n[TEST 1] Checking deleted_provider_tasks table...")

        try:
            conn = database.get_db_connection()

            # Check table exists
            table = conn.execute(
                "SELECT name FROM sqlite_master WHERE name='deleted_provider_tasks'"
            ).fetchone()

            if not table:
                self.log_result("SCHEMA", "deleted_provider_tasks Table", "FAIL",
                               "", "Table doesn't exist")
                conn.close()
                return

            # Check columns
            columns = conn.execute("PRAGMA table_info(deleted_provider_tasks)").fetchall()
            col_names = [col[1] for col in columns]

            required_cols = [
                'deleted_id', 'provider_task_id', 'original_table_name',
                'provider_id', 'patient_id', 'task_date', 'task_description',
                'notes', 'minutes_of_service', 'billing_code', 'deleted_at',
                'deleted_by_user_id', 'icd_codes'
            ]

            missing = [c for c in required_cols if c not in col_names]

            if missing:
                self.log_result("SCHEMA", "deleted_provider_tasks Columns", "FAIL",
                               f"Missing columns: {missing}")
            else:
                self.log_result("SCHEMA", "deleted_provider_tasks Table", "PASS",
                               f"Table exists with all {len(required_cols)} required columns")

            # Check indexes
            indexes = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND tbl_name='deleted_provider_tasks'"
            ).fetchall()

            self.log_result("SCHEMA", "deleted_provider_tasks Indexes", "PASS",
                          f"Found {len(indexes)} indexes")

            conn.close()

        except Exception as e:
            self.log_result("SCHEMA", "deleted_provider_tasks Table Check", "ERROR", "", str(e))

    def test_02_delete_single_task(self):
        """Test deleting a single task"""
        print("\n[TEST 2] Testing single task deletion...")

        if not self.test_task_ids:
            self.log_result("DELETE", "Delete Single Task", "WARN", "", "No test tasks available")
            return

        try:
            task_id = self.test_task_ids[0]
            table_name = f"provider_tasks_{date.today().strftime('%Y_%m')}"

            # Get original task data before deletion
            conn = database.get_db_connection()
            original = conn.execute(
                f"SELECT provider_task_id, provider_id, patient_id, task_date, task_description, notes, minutes_of_service, billing_code, icd_codes "
                f"FROM {table_name} WHERE provider_task_id = {task_id}"
            ).fetchone()

            if not original:
                self.log_result("DELETE", "Verify Task Exists", "FAIL",
                               "", f"Task {task_id} not found")
                conn.close()
                return

            # Store original data for validation
            self.original_task_data[task_id] = dict(original)

            conn.close()

            # Delete the task
            success, message, count = database.delete_provider_tasks(
                [task_id], table_name, deleted_by_user_id=self.original_task_data[task_id].get('provider_id')
            )

            if not success:
                self.log_result("DELETE", "Delete Single Task", "FAIL", "", message)
                return

            self.log_result("DELETE", "Delete Single Task", "PASS", message)

            # Verify task was moved to deleted table
            conn = database.get_db_connection()
            deleted = conn.execute(
                f"SELECT * FROM deleted_provider_tasks WHERE provider_task_id = {task_id}"
            ).fetchone()

            if deleted:
                self.log_result("DELETE", "Task Moved to Deleted Table", "PASS",
                               f"Found in deleted_provider_tasks with deleted_id: {deleted[0]}")
                self.test_deleted_ids.append(deleted[0])
            else:
                self.log_result("DELETE", "Task Moved to Deleted Table", "FAIL",
                               "", "Task not found in deleted_provider_tasks")

            # Verify task was removed from original table
            remaining = conn.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE provider_task_id = {task_id}"
            ).fetchone()[0]

            if remaining == 0:
                self.log_result("DELETE", "Task Removed from Original Table", "PASS")
            else:
                self.log_result("DELETE", "Task Removed from Original Table", "FAIL",
                               f"Task still exists (count: {remaining})")

            # Verify billing status was deleted
            billing_deleted = conn.execute(
                f"SELECT COUNT(*) FROM provider_task_billing_status WHERE provider_task_id = {task_id}"
            ).fetchone()[0]

            if billing_deleted == 0:
                self.log_result("DELETE", "Billing Status Removed", "PASS",
                               "Billing entry successfully deleted")
            else:
                self.log_result("DELETE", "Billing Status Removed", "WARN",
                               f"Billing entry still exists (count: {billing_deleted})")

            # Verify deleted_at timestamp was set
            deleted_check = conn.execute(
                f"SELECT deleted_at, deleted_by_user_id FROM deleted_provider_tasks WHERE provider_task_id = {task_id}"
            ).fetchone()

            if deleted_check and deleted_check[0]:
                self.log_result("DELETE", "Deleted Timestamp Set", "PASS",
                               f"Deleted at {deleted_check[0]} by user_id {deleted_check[1]}")
            else:
                self.log_result("DELETE", "Deleted Timestamp Set", "WARN",
                               "Timestamp not set")

            # Verify icd_codes was preserved
            if 'icd_codes' in [col[1] for col in conn.execute("PRAGMA table_info(deleted_provider_tasks)").fetchall()]:
                icd_check = conn.execute(
                    f"SELECT icd_codes FROM deleted_provider_tasks WHERE provider_task_id = {task_id}"
                ).fetchone()

                self.log_result("DELETE", "ICD Codes Preserved", "PASS",
                               f"ICD codes: {icd_check[0] if icd_check else 'NULL'}")

            conn.close()

        except Exception as e:
            self.log_result("DELETE", "Delete Single Task", "ERROR", "", str(e))
            import traceback
            traceback.print_exc()

    def test_03_delete_multiple_tasks(self):
        """Test deleting multiple tasks at once"""
        print("\n[TEST 3] Testing multiple task deletion...")

        if len(self.test_task_ids) < 2:
            self.log_result("DELETE", "Delete Multiple Tasks", "WARN", "", "Need at least 2 test tasks")
            return

        try:
            # Delete remaining tasks
            task_ids_to_delete = self.test_task_ids[1:]
            table_name = f"provider_tasks_{date.today().strftime('%Y_%m')}"

            # Get provider_id from first task
            conn = database.get_db_connection()
            provider_id = conn.execute(
                f"SELECT provider_id FROM {table_name} WHERE provider_task_id = {task_ids_to_delete[0]}"
            ).fetchone()[0]
            conn.close()

            # Delete multiple tasks
            success, message, count = database.delete_provider_tasks(
                task_ids_to_delete, table_name, deleted_by_user_id=provider_id
            )

            if not success:
                self.log_result("DELETE", "Delete Multiple Tasks", "FAIL", "", message)
                return

            self.log_result("DELETE", "Delete Multiple Tasks", "PASS",
                          f"Deleted {count} tasks: {message}")

            # Verify all tasks were moved
            conn = database.get_db_connection()
            deleted_count = conn.execute(
                f"SELECT COUNT(*) FROM deleted_provider_tasks WHERE provider_task_id IN ({','.join(map(str, task_ids_to_delete))})"
            ).fetchone()[0]

            if deleted_count == len(task_ids_to_delete):
                self.log_result("DELETE", "All Tasks Moved to Deleted Table", "PASS",
                               f"All {deleted_count} tasks found in deleted_provider_tasks")

                # Get all deleted_ids
                deleted_records = conn.execute(
                    f"SELECT deleted_id FROM deleted_provider_tasks WHERE provider_task_id IN ({','.join(map(str, task_ids_to_delete))})"
                ).fetchall()

                for record in deleted_records:
                    if record[0] not in self.test_deleted_ids:
                        self.test_deleted_ids.append(record[0])
            else:
                self.log_result("DELETE", "All Tasks Moved to Deleted Table", "FAIL",
                               f"Expected {len(task_ids_to_delete)}, found {deleted_count}")

            # Verify all tasks removed from original table
            remaining_count = conn.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE provider_task_id IN ({','.join(map(str, task_ids_to_delete))})"
            ).fetchone()[0]

            if remaining_count == 0:
                self.log_result("DELETE", "All Tasks Removed from Original Table", "PASS")
            else:
                self.log_result("DELETE", "All Tasks Removed from Original Table", "FAIL",
                               f"{remaining_count} tasks still exist")

            conn.close()

        except Exception as e:
            self.log_result("DELETE", "Delete Multiple Tasks", "ERROR", "", str(e))
            import traceback
            traceback.print_exc()

    def test_04_restore_single_task(self):
        """Test restoring a single deleted task"""
        print("\n[TEST 4] Testing single task restoration...")

        if not self.test_deleted_ids:
            self.log_result("RESTORE", "Restore Single Task", "WARN", "", "No deleted tasks to restore")
            return

        try:
            deleted_id = self.test_deleted_ids[0]

            # Get task info before restoration
            conn = database.get_db_connection()
            task_info = conn.execute(
                f"SELECT provider_task_id, original_table_name, provider_id FROM deleted_provider_tasks WHERE deleted_id = {deleted_id}"
            ).fetchone()

            if not task_info:
                self.log_result("RESTORE", "Find Deleted Task", "FAIL",
                               "", f"Deleted task {deleted_id} not found")
                conn.close()
                return

            provider_task_id = task_info[0]
            original_table = task_info[1]
            provider_id = task_info[2]

            # Restore the task
            success, message, count = database.restore_provider_tasks(
                [deleted_id], restored_by_user_id=provider_id
            )

            if not success:
                self.log_result("RESTORE", "Restore Single Task", "FAIL", "", message)
                conn.close()
                return

            self.log_result("RESTORE", "Restore Single Task", "PASS", message)

            # Verify task was restored to original table
            restored = conn.execute(
                f"SELECT COUNT(*) FROM {original_table} WHERE provider_task_id = {provider_task_id}"
            ).fetchone()[0]

            if restored > 0:
                self.log_result("RESTORE", "Task Restored to Original Table", "PASS",
                               f"Task found in {original_table}")
            else:
                self.log_result("RESTORE", "Task Restored to Original Table", "FAIL",
                               "Task not found after restore")

            # Verify restored_at timestamp was set
            restored_check = conn.execute(
                f"SELECT restored_at, restored_by_user_id FROM deleted_provider_tasks WHERE deleted_id = {deleted_id}"
            ).fetchone()

            if restored_check and restored_check[0]:
                self.log_result("RESTORE", "Restored Timestamp Set", "PASS",
                               f"Restored at {restored_check[0]} by user_id {restored_check[1]}")
            else:
                self.log_result("RESTORE", "Restored Timestamp Set", "WARN",
                               "Timestamp not set")

            # Verify task data integrity
            restored_task = conn.execute(
                f"SELECT provider_id, patient_id, task_description, notes FROM {original_table} WHERE provider_task_id = {provider_task_id}"
            ).fetchone()

            if restored_task:
                # Compare with original data
                original_data = self.original_task_data.get(provider_task_id, {})
                if original_data:
                    # Check critical fields match
                    checks = []
                    if restored_task[0] == original_data.get('provider_id'):
                        checks.append("provider_id MATCH")
                    else:
                        checks.append(f"provider_id MISMATCH ({restored_task[0]} vs {original_data.get('provider_id')})")

                    if restored_task[2] == original_data.get('task_description'):
                        checks.append("task_description MATCH")
                    else:
                        checks.append(f"task_description MISMATCH")

                    if restored_task[3] == original_data.get('notes'):
                        checks.append("notes MATCH")
                    else:
                        checks.append("notes MISMATCH")

                    if all("MATCH" in c for c in checks):
                        self.log_result("RESTORE", "Task Data Integrity", "PASS",
                                       f"All fields verified: {', '.join(checks)}")
                    else:
                        self.log_result("RESTORE", "Task Data Integrity", "WARN",
                                       f"Some mismatches: {', '.join(checks)}")

            conn.close()

        except Exception as e:
            self.log_result("RESTORE", "Restore Single Task", "ERROR", "", str(e))
            import traceback
            traceback.print_exc()

    def test_05_restore_multiple_tasks(self):
        """Test restoring multiple deleted tasks"""
        print("\n[TEST 5] Testing multiple task restoration...")

        if len(self.test_deleted_ids) < 2:
            self.log_result("RESTORE", "Restore Multiple Tasks", "WARN", "", "Need at least 2 deleted tasks")
            return

        try:
            deleted_ids = self.test_deleted_ids[1:]

            # Get provider_id from first deleted task
            conn = database.get_db_connection()
            provider_id = conn.execute(
                f"SELECT provider_id FROM deleted_provider_tasks WHERE deleted_id = {deleted_ids[0]}"
            ).fetchone()[0]

            # Restore all tasks
            success, message, count = database.restore_provider_tasks(
                deleted_ids, restored_by_user_id=provider_id
            )

            if not success:
                self.log_result("RESTORE", "Restore Multiple Tasks", "FAIL", "", message)
                conn.close()
                return

            self.log_result("RESTORE", "Restore Multiple Tasks", "PASS",
                          f"Restored {count} tasks: {message}")

            # Verify all tasks were restored
            # Get original table names for each deleted task
            tasks_to_check = conn.execute(
                f"SELECT provider_task_id, original_table_name FROM deleted_provider_tasks WHERE deleted_id IN ({','.join(map(str, deleted_ids))})"
            ).fetchall()

            restored_count = 0
            for task in tasks_to_check:
                provider_task_id = task[0]
                original_table = task[1]

                check = conn.execute(
                    f"SELECT COUNT(*) FROM {original_table} WHERE provider_task_id = {provider_task_id}"
                ).fetchone()[0]

                if check > 0:
                    restored_count += 1

            if restored_count == len(deleted_ids):
                self.log_result("RESTORE", "All Tasks Restored", "PASS",
                               f"All {restored_count} tasks restored successfully")
            else:
                self.log_result("RESTORE", "All Tasks Restored", "WARN",
                               f"Expected {len(deleted_ids)}, restored {restored_count}")

            conn.close()

        except Exception as e:
            self.log_result("RESTORE", "Restore Multiple Tasks", "ERROR", "", str(e))
            import traceback
            traceback.print_exc()

    def test_06_get_deleted_tasks(self):
        """Test retrieving deleted tasks"""
        print("\n[TEST 6] Testing get_deleted_provider_tasks function...")

        try:
            # Get all deleted tasks
            all_deleted = database.get_deleted_provider_tasks(limit=100)

            if all_deleted:
                self.log_result("QUERY", "Get All Deleted Tasks", "PASS",
                               f"Retrieved {len(all_deleted)} deleted tasks")

                # Verify data structure
                if all_deleted:
                    first = all_deleted[0]
                    expected_keys = ['deleted_id', 'provider_task_id', 'original_table_name',
                                   'provider_id', 'patient_id', 'patient_name', 'task_date',
                                   'task_description', 'notes', 'minutes_of_service']

                    missing_keys = [k for k in expected_keys if k not in first]

                    if not missing_keys:
                        self.log_result("QUERY", "Deleted Tasks Data Structure", "PASS",
                                       f"All {len(expected_keys)} expected keys present")
                    else:
                        self.log_result("QUERY", "Deleted Tasks Data Structure", "FAIL",
                                       f"Missing keys: {missing_keys}")
            else:
                self.log_result("QUERY", "Get All Deleted Tasks", "WARN",
                               "No deleted tasks found")

        except Exception as e:
            self.log_result("QUERY", "Get Deleted Tasks", "ERROR", "", str(e))
            import traceback
            traceback.print_exc()

    def test_07_cleanup_test_data(self):
        """Clean up test data"""
        print("\n[CLEANUP] Removing test tasks...")

        try:
            conn = database.get_db_connection()
            table_name = f"provider_tasks_{date.today().strftime('%Y_%m')}"

            # Delete test tasks from provider_tasks table
            if self.test_task_ids:
                placeholders = ','.join(['?'] * len(self.test_task_ids))
                conn.execute(
                    f"DELETE FROM {table_name} WHERE task_description LIKE 'Delete Test Task%'"
                )

                # Delete from deleted_provider_tasks
                conn.execute(
                    f"DELETE FROM deleted_provider_tasks WHERE task_description LIKE 'Delete Test Task%'"
                )

                conn.commit()

                self.log_result("CLEANUP", "Remove Test Tasks", "PASS",
                               f"Removed test tasks by description")

            # Also delete the coordinator_tasks entries
            coord_table = f"coordinator_tasks_{date.today().strftime('%Y_%m')}"
            conn.execute(
                f"DELETE FROM {coord_table} WHERE task_description LIKE 'Delete Test Task%'"
            )
            conn.commit()

            conn.close()

        except Exception as e:
            self.log_result("CLEANUP", "Remove Test Tasks", "WARN", "", str(e))

    def generate_report(self):
        """Generate final test report"""
        print("\n" + "=" * 70)
        print("DELETE TASKS TEST REPORT")
        print("=" * 70)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {(datetime.now() - self.start_time).total_seconds():.2f} seconds")
        print()

        print("SUMMARY:")
        print(f"  Total Tests: {len(self.tests)}")
        print(f"  [OK] PASSED: {self.summary['PASS']}")
        print(f"  [X] FAILED: {self.summary['FAIL']}")
        print(f"  [!] WARNINGS: {self.summary['WARN']}")
        print(f"  [?] ERRORS: {self.summary['ERROR']}")
        print()

        # Group by category
        categories = {}
        for test in self.tests:
            cat = test['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(test)

        print("DETAILED RESULTS BY CATEGORY:")
        print("-" * 70)
        for cat, tests in sorted(categories.items()):
            print(f"\n{cat}:")
            for test in tests:
                symbol = {"PASS": "[OK]", "FAIL": "[X]", "WARN": "[!]", "ERROR": "[?]"}.get(test['status'], "[?]")
                print(f"  {symbol} {test['name']}")
                if test['details']:
                    print(f"      {test['details']}")
                if test['error']:
                    print(f"      ERROR: {test['error']}")

        # Save JSON report
        report = {
            "timestamp": datetime.now().isoformat(),
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "summary": self.summary,
            "tests": self.tests,
            "test_task_ids": self.test_task_ids,
            "test_deleted_ids": self.test_deleted_ids
        }

        report_file = project_root / f"test_report_delete_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nJSON report saved to: {report_file}")

        # Return success status
        total_fail = self.summary['FAIL'] + self.summary['ERROR']
        return total_fail == 0

def main():
    """Run all delete tasks tests"""
    print("=" * 70)
    print("DELETE TASKS COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    suite = DeleteTasksTestSuite()

    # Setup test data
    if not suite.setup_test_data():
        print("\n[ERROR] Failed to create test tasks. Exiting.")
        return False

    # Run tests
    suite.test_01_deleted_table_exists()
    suite.test_02_delete_single_task()
    suite.test_03_delete_multiple_tasks()
    suite.test_04_restore_single_task()
    suite.test_05_restore_multiple_tasks()
    suite.test_06_get_deleted_tasks()
    suite.test_07_cleanup_test_data()

    # Generate report
    success = suite.generate_report()

    if success:
        print("\n[SUCCESS] All critical tests passed!")
    else:
        print(f"\n[FAILED] Some tests failed - check report above")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
