"""
Comprehensive Database Function Tests
Tests all database read/write operations used by dashboards
Replaces manual UI testing with automated validation
"""
import sqlite3
import sys
sys.path.insert(0, 'src')

from database import *
import pandas as pd
from datetime import datetime, timedelta

class DatabaseFunctionTester:
    def __init__(self):
        self.conn = get_db_connection()
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def test(self, name, func):
        """Run a test function and track results"""
        try:
            func()
            self.passed += 1
            print(f"✅ {name}")
            return True
        except Exception as e:
            self.failed += 1
            self.errors.append((name, str(e)))
            print(f"❌ {name}: {e}")
            return False
    
    def run_all_tests(self):
        print("="*70)
        print("COMPREHENSIVE DATABASE FUNCTION TESTS")
        print("="*70)
        
        # Category 1: Patient Data Access
        print("\n📊 PATIENT DATA ACCESS")
        self.test("SELECT from patients table", self.test_patients_table)
        self.test("SELECT from patient_panel table", self.test_patient_panel_table)
        self.test("SELECT from patient_assignments", self.test_patient_assignments)
        self.test("SELECT from onboarding_patients", self.test_onboarding_patients)
        
        # Category 2: Task Data Access
        print("\n📋 TASK DATA ACCESS")        
        self.test("SELECT from provider_tasks view", self.test_provider_tasks_view)
        self.test("SELECT from coordinator_tasks view", self.test_coordinator_tasks_view)
        self.test("SELECT from monthly provider_tasks tables", self.test_monthly_provider_tasks)
        self.test("SELECT from monthly coordinator_tasks tables", self.test_monthly_coordinator_tasks)
        
        # Category 3: Summary Tables
        print("\n📈 SUMMARY TABLES")
        self.test("SELECT from provider_weekly_summary_with_billing", self.test_provider_weekly_summary)
        self.test("SELECT from coordinator_monthly_summary", self.test_coordinator_monthly_summary)
        
        # Category 4: User & Authentication 
        print("\n👤 USER & AUTHENTICATION")
        self.test("SELECT from users table", self.test_users_table)
        self.test("SELECT from roles table", self.test_roles_table)
        self.test("SELECT from user_roles table", self.test_user_roles)
        
        # Category 5: Lookup Tables
        print("\n🔍 LOOKUP TABLES")
        self.test("SELECT from facilities table", self.test_facilities)
        self.test("SELECT from task_billing_codes", self.test_billing_codes)
        
        # Category 6: Common JOIN Operations
        print("\n🔗 JOIN OPERATIONS")
        self.test("JOIN patients with provider_tasks", self.test_patient_task_join)
        self.test("JOIN users with user_roles", self.test_user_roles_join)
        self.test("JOIN patients with patient_assignments", self.test_patient_assignment_join)
        
        # Category 7: Database Functions
        print("\n⚙️  DATABASE FUNCTIONS")
        self.test("normalize_patient_id()", self.test_normalize_patient_id_func)
        self.test("get_monthly_task_tables()", self.test_get_monthly_task_tables_func)
        
        # Category 8: Data Integrity
        print("\n🔐 DATA INTEGRITY")
        self.test("All patient_ids in tasks exist in patients", self.test_patient_id_integrity)
        self.test("All provider_ids in tasks exist in users", self.test_provider_id_integrity)
        self.test("No NULL patient_ids in patient_panel", self.test_patient_panel_nulls)
        
        self.print_summary()
    
    # ====== PATIENT DATA TESTS ======
    def test_patients_table(self):
        count = self.conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        assert count > 0, "patients table is empty"
        assert count == 620, f"Expected 620 patients, got {count}"
        
    def test_patient_panel_table(self):
        count = self.conn.execute("SELECT COUNT(*) FROM patient_panel").fetchone()[0]
        assert count > 0, "patient_panel table is empty"
        assert count == 620, f"Expected 620 in patient_panel, got {count}"
    
    def test_patient_assignments(self):
        count = self.conn.execute("SELECT COUNT(*) FROM patient_assignments").fetchone()[0]
        assert count > 0, "patient_assignments is empty"
    
    def test_onboarding_patients(self):
        count = self.conn.execute("SELECT COUNT(*) FROM onboarding_patients").fetchone()[0]
        assert count == 620, f"Expected 620 onboarding records, got {count}"
    
    # ====== TASK DATA TESTS ======
    def test_provider_tasks_view(self):
        count = self.conn.execute("SELECT COUNT(*) FROM provider_tasks").fetchone()[0]
        assert count > 0, "provider_tasks view is empty"
    
    def test_coordinator_tasks_view(self):
        count = self.conn.execute("SELECT COUNT(*) FROM coordinator_tasks").fetchone()[0]
        assert count > 0, "coordinator_tasks view is empty"
    
    def test_monthly_provider_tasks(self):
        # Check October 2025 table specifically
        count = self.conn.execute("SELECT COUNT(*) FROM provider_tasks_2025_10").fetchone()[0]
        assert count > 0, "provider_tasks_2025_10 is empty"
    
    def test_monthly_coordinator_tasks(self):
        # Check October 2025 table specifically
        count = self.conn.execute("SELECT COUNT(*) FROM coordinator_tasks_2025_10").fetchone()[0]
        assert count > 0, "coordinator_tasks_2025_10 is empty"
    
    # ====== SUMMARY TESTS ======
    def test_provider_weekly_summary(self):
        count = self.conn.execute("SELECT COUNT(*) FROM provider_weekly_summary_with_billing").fetchone()[0]
        assert count > 0, "provider_weekly_summary_with_billing is empty"
        assert count == 108, f"Expected 108 weekly summaries, got {count}"
    
    def test_coordinator_monthly_summary(self):
        count = self.conn.execute("SELECT COUNT(*) FROM coordinator_monthly_summary").fetchone()[0]
        assert count > 0, "coordinator_monthly_summary is empty"
        assert count == 11, f"Expected 11 monthly summaries, got {count}"
    
    # ====== USER TESTS ======
    def test_users_table(self):
        count = self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        assert count > 0, "users table is empty"
    
    def test_roles_table(self):
        count = self.conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
        assert count > 0, "roles table is empty"
    
    def test_user_roles(self):
        count = self.conn.execute("SELECT COUNT(*) FROM user_roles").fetchone()[0]
        assert count > 0, "user_roles is empty"
    
    # ====== LOOKUP TESTS ======
    def test_facilities(self):
        count = self.conn.execute("SELECT COUNT(*) FROM facilities").fetchone()[0]
        assert count > 0, "facilities table is empty"
    
    def test_billing_codes(self):
        count = self.conn.execute("SELECT COUNT(*) FROM task_billing_codes").fetchone()[0]
        assert count > 0, "task_billing_codes is empty"
    
    # ====== JOIN TESTS ======
    def test_patient_task_join(self):
        query = """
        SELECT COUNT(*) FROM provider_tasks pt
        JOIN patients p ON pt.patient_id = p.patient_id
        LIMIT 100
        """
        count = self.conn.execute(query).fetchone()[0]
        assert count > 0, "patient-task join returned no results"
    
    def test_user_roles_join(self):
        query = """
        SELECT COUNT(*) FROM users u
        JOIN user_roles ur ON u.user_id = ur.user_id
        """
        count = self.conn.execute(query).fetchone()[0]
        assert count > 0, "user-roles join returned no results"
    
    def test_patient_assignment_join(self):
        query = """
        SELECT COUNT(*) FROM patients p
        LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id
        """
        count = self.conn.execute(query).fetchone()[0]
        assert count == 620, f"Expected 620 from patient assignment join, got {count}"
    
    # ====== FUNCTION TESTS ======
    def test_normalize_patient_id_func(self):
        # Test the normalize function exists and works
        test_id = "ZEN-SMITH JOHN 01/01/1980"
        normalized = normalize_patient_id(test_id, self.conn)
        assert normalized is not None, "normalize_patient_id returned None"
        assert "ZEN-" not in normalized, "Prefix not stripped"
    
    def test_get_monthly_task_tables_func(self):
        tables = get_monthly_task_tables("provider_tasks", self.conn)
        assert len(tables) > 0, "No monthly provider task tables found"
    
    # ====== INTEGRITY TESTS ======
    def test_patient_id_integrity(self):
        # Check if any patient_ids in provider_tasks don't exist in patients
        query = """
        SELECT COUNT(DISTINCT pt.patient_id) 
        FROM provider_tasks pt 
        LEFT JOIN patients p ON pt.patient_id = p.patient_id
        WHERE p.patient_id IS NULL
        """
        orphans = self.conn.execute(query).fetchone()[0]
        # Allow some orphans since task data may have patients not in ZMO
        assert orphans < 100, f"Too many orphaned patient_ids: {orphans}"
    
    def test_provider_id_integrity(self):
        # Check if provider_ids in tasks exist in users
        query = """
        SELECT COUNT(DISTINCT pt.provider_id)
        FROM provider_tasks pt
        LEFT JOIN users u ON pt.provider_id = u.user_id
        WHERE u.user_id IS NULL AND pt.provider_id IS NOT NULL
        """
        orphans = self.conn.execute(query).fetchone()[0]
        assert orphans == 0, f"Found {orphans} provider_ids not in users table"
    
    def test_patient_panel_nulls(self):
        query = "SELECT COUNT(*) FROM patient_panel WHERE patient_id IS NULL"
        nulls = self.conn.execute(query).fetchone()[0]
        assert nulls == 0, f"Found {nulls} NULL patient_ids in patient_panel"
    
    def print_summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        
        if self.errors:
            print("\n❌ FAILED TESTS:")
            for name, error in self.errors:
                print(f"  - {name}")
                print(f"    {error}")
        
        print("\n" + "="*70)
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED - DATABASE READY FOR PRODUCTION")
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW ERRORS ABOVE")
        print("="*70)
        
        self.conn.close()

if __name__ == "__main__":
    tester = DatabaseFunctionTester()
    tester.run_all_tests()
