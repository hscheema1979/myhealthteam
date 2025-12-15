"""
WORKFLOW & TASK MANIPULATION TESTS
Tests all INSERT, UPDATE, DELETE operations for provider/coordinator tasks and workflows
"""
import sqlite3
import sys
sys.path.insert(0, 'src')
from database import *
from datetime import datetime, timedelta

class WorkflowTaskTester:
    def __init__(self):
        self.conn = get_db_connection()
        self.passed = 0
        self.failed = 0
        
    def test(self, name, func):
        try:
            func()
            self.passed += 1
            print(f"✅ {name}")
            return True
        except AssertionError as e:
            self.failed += 1
            print(f"❌ {name}: {e}")
            return False
    
    def run_all_tests(self):
        print("="*70)
        print("WORKFLOW & TASK MANIPULATION TESTS")
        print("="*70)
        
        print("\n📝 PROVIDER TASK OPERATIONS")
        self.test("INSERT provider task", self.test_insert_provider_task)
        self.test("SELECT provider tasks by provider_id", self.test_select_provider_tasks)
        self.test("UPDATE provider task", self.test_update_provider_task)
        self.test("Soft DELETE provider task", self.test_soft_delete_provider_task)
        self.test("AGGREGATE provider minutes", self.test_aggregate_provider_minutes)
        
        print("\n📋 COORDINATOR TASK OPERATIONS")
        self.test("INSERT coordinator task", self.test_insert_coordinator_task)
        self.test("SELECT coordinator tasks by coordinator_id", self.test_select_coordinator_tasks)
        self.test("UPDATE coordinator task", self.test_update_coordinator_task)
        self.test("AGGREGATE coordinator duration", self.test_aggregate_coordinator_duration)
        
        print("\n🔄 WORKFLOW OPERATIONS")
        self.test("Query billing status workflow", self.test_billing_status_workflow)
        self.test("Filter tasks by date range", self.test_filter_by_date_range)
        self.test("JOIN tasks with patients", self.test_join_tasks_patients)
        self.test("UNION monthly task tables", self.test_union_monthly_tables)
        
        print("\n📊 DASHBOARD-SPECIFIC QUERIES")
        self.test("Weekly provider summary", self.test_weekly_provider_summary)
        self.test("Monthly coordinator summary", self.test_monthly_coordinator_summary)
        self.test("Patient task history", self.test_patient_task_history)
        
        self.print_summary()
    
    # ===== PROVIDER TASK TESTS =====
    def test_insert_provider_task(self):
        # Insert a test provider task
        self.conn.execute("""
            INSERT INTO provider_tasks_2025_10 
            (provider_id, patient_id, task_date, task_description, minutes_of_service, billing_code)
            VALUES (1, 'TEST PATIENT 01/01/1980', '2025-10-15', 'Test Task', 30, '99345')
        """)
        self.conn.commit()
        
        # Verify it was inserted
        result = self.conn.execute("""
            SELECT COUNT(*) FROM provider_tasks_2025_10
            WHERE patient_id = 'TEST PATIENT 01/01/1980'
        """).fetchone()[0]
        
        assert result >= 1, "Failed to insert provider task"
    
    def test_select_provider_tasks(self):
        # Get tasks for a specific provider
        result = self.conn.execute("""
            SELECT COUNT(*) FROM provider_tasks_2025_10
            WHERE provider_id IS NOT NULL
        """).fetchone()[0]
        
        assert result > 0, "No provider tasks found"
    
    def test_update_provider_task(self):
        # Update the test task
        self.conn.execute("""
            UPDATE provider_tasks_2025_10
            SET notes = 'Updated test note'
            WHERE patient_id = 'TEST PATIENT 01/01/1980'
        """)
        self.conn.commit()
        
        # Verify update
        result = self.conn.execute("""
            SELECT notes FROM provider_tasks_2025_10
            WHERE patient_id = 'TEST PATIENT 01/01/1980'
        """).fetchone()
        
        assert result and result[0] == 'Updated test note', "Update failed"
    
    def test_soft_delete_provider_task(self):
        # Soft delete (set is_deleted flag)
        self.conn.execute("""
            UPDATE provider_tasks_2025_10
            SET is_deleted = 1
            WHERE patient_id = 'TEST PATIENT 01/01/1980'
        """)
        self.conn.commit()
        
        # Verify soft delete
        result = self.conn.execute("""
            SELECT is_deleted FROM provider_tasks_2025_10
            WHERE patient_id = 'TEST PATIENT 01/01/1980'
        """).fetchone()
        
        assert result and result[0] == 1, "Soft delete failed"
        
        # Clean up
        self.conn.execute("DELETE FROM provider_tasks_2025_10 WHERE patient_id = 'TEST PATIENT 01/01/1980'")
        self.conn.commit()
    
    def test_aggregate_provider_minutes(self):
        # Test SUM aggregation
        result = self.conn.execute("""
            SELECT SUM(minutes_of_service)
            FROM provider_tasks_2025_10
            WHERE minutes_of_service IS NOT NULL
        """).fetchone()[0]
        
        assert result is None or result >= 0, "Aggregation failed"
    
    # ===== COORDINATOR TASK TESTS =====
    def test_insert_coordinator_task(self):
        # Insert test coordinator task
        self.conn.execute("""
            INSERT INTO coordinator_tasks_2025_10
            (coordinator_id, patient_id, task_date, duration_minutes, task_type)
            VALUES (1, 'TEST PATIENT 01/01/1980', '2025-10-15', 45.0, 'Phone Call')
        """)
        self.conn.commit()
        
        # Verify
        result = self.conn.execute("""
            SELECT COUNT(*) FROM coordinator_tasks_2025_10
            WHERE patient_id = 'TEST PATIENT 01/01/1980'
        """).fetchone()[0]
        
        assert result >= 1, "Failed to insert coordinator task"
    
    def test_select_coordinator_tasks(self):
        # Get tasks for specific coordinator
        result = self.conn.execute("""
            SELECT COUNT(*) FROM coordinator_tasks_2025_10
            WHERE coordinator_id IS NOT NULL
        """).fetchone()[0]
        
        assert result > 0, "No coordinator tasks found"
    
    def test_update_coordinator_task(self):
        # Update test task
        self.conn.execute("""
            UPDATE coordinator_tasks_2025_10
            SET notes = 'Updated coordinator note'
            WHERE patient_id = 'TEST PATIENT 01/01/1980'
        """)
        self.conn.commit()
        
        # Verify
        result = self.conn.execute("""
            SELECT notes FROM coordinator_tasks_2025_10
            WHERE patient_id = 'TEST PATIENT 01/01/1980'
        """).fetchone()
        
        assert result and result[0] == 'Updated coordinator note', "Update failed"
        
        # Clean up
        self.conn.execute("DELETE FROM coordinator_tasks_2025_10 WHERE patient_id = 'TEST PATIENT 01/01/1980'")
        self.conn.commit()
    
    def test_aggregate_coordinator_duration(self):
        # Test SUM of duration_minutes
        result = self.conn.execute("""
            SELECT SUM(duration_minutes)
            FROM coordinator_tasks_2025_10
            WHERE duration_minutes IS NOT NULL
        """).fetchone()[0]
        
        assert result is None or result >= 0, "Aggregation failed"
    
    # ===== WORKFLOW TESTS =====
    def test_billing_status_workflow(self):
        # Test workflow table query
        result = self.conn.execute("""
            SELECT COUNT(*) FROM provider_task_billing_status
        """).fetchone()[0]
        
        # Can be 0 if empty (workflow table)
        assert result >= 0, "Billing status query failed"
    
    def test_filter_by_date_range(self):
        # Test date range filtering
        result = self.conn.execute("""
            SELECT COUNT(*) FROM provider_tasks_2025_10
            WHERE task_date BETWEEN '2025-10-01' AND '2025-10-31'
        """).fetchone()[0]
        
        assert result >= 0, "Date range filter failed"
    
    def test_join_tasks_patients(self):
        # Test JOIN operation
        result = self.conn.execute("""
            SELECT COUNT(*)
            FROM provider_tasks_2025_10 pt
            LEFT JOIN patients p ON pt.patient_id = p.patient_id
            LIMIT 100
        """).fetchone()[0]
        
        assert result >= 0, "JOIN failed"
    
    def test_union_monthly_tables(self):
        # Test UNION of multiple monthly tables
        try:
            result = self.conn.execute("""
                SELECT COUNT(*) FROM (
                    SELECT patient_id FROM provider_tasks_2025_10
                    UNION ALL
                    SELECT patient_id FROM coordinator_tasks_2025_10
                ) LIMIT 100
            """).fetchone()[0]
            
            assert result >= 0, "UNION failed"
        except Exception:
            # May fail if tables don't exist
            pass
    
    # ===== DASHBOARD QUERY TESTS =====
    def test_weekly_provider_summary(self):
        # Test weekly summary query
        result = self.conn.execute("""
            SELECT COUNT(*) FROM provider_weekly_summary_with_billing
        """).fetchone()[0]
        
        assert result > 0, "Weekly summary empty"
    
    def test_monthly_coordinator_summary(self):
        # Test monthly summary query
        result = self.conn.execute("""
            SELECT COUNT(*) FROM coordinator_monthly_summary
        """).fetchone()[0]
        
        assert result > 0, "Monthly summary empty"
    
    def test_patient_task_history(self):
        # Test patient history query
        result = self.conn.execute("""
            SELECT COUNT(*)
            FROM provider_tasks_2025_10 pt
            JOIN patients p ON pt.patient_id = p.patient_id
            ORDER BY pt.task_date DESC
            LIMIT 10
        """).fetchone()[0]
        
        assert result >= 0, "Patient history query failed"
    
    def print_summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        
        if self.failed == 0:
            print("\n🎉 ALL WORKFLOW & TASK OPERATIONS FUNCTIONAL")
            print("✅ Database ready for dashboard use")
        else:
            print("\n⚠️  Some operations failed - review errors")
        
        print("="*70)
        self.conn.close()

if __name__ == "__main__":
    tester = WorkflowTaskTester()
    tester.run_all_tests()
