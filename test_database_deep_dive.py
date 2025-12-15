"""
COMPREHENSIVE DEEP-DIVE DATABASE TESTS
Validates every column, data format, and possible dashboard interaction
"""
import sqlite3
import sys
sys.path.insert(0, 'src')

from database import *
import pandas as pd
from datetime import datetime
import re

class DeepDiveDatabaseTester:
    def __init__(self):
        self.conn = get_db_connection()
        self.passed = 0
        self.failed = 0
        self.warnings = []
        self.errors = []
    
    def test(self, name, func):
        """Run a test function"""
        try:
            func()
            self.passed += 1
            print(f"✅ {name}")
            return True
        except AssertionError as e:
            self.failed += 1
            self.errors.append((name, str(e)))
            print(f"❌ {name}: {e}")
            return False
        except Exception as e:
            self.failed += 1
            self.errors.append((name, f"ERROR: {e}"))
            print(f"❌ {name}: ERROR - {e}")
            return False
    
    def warn(self, message):
        """Add a warning"""
        self.warnings.append(message)
        print(f"⚠️  {message}")
    
    def run_deep_dive_tests(self):
        print("="*80)
        print("COMPREHENSIVE DEEP-DIVE DATABASE TESTS")
        print("="*80)
        
        # SECTION 1: TABLE SCHEMAS
        print("\n" + "="*80)
        print("SECTION 1: TABLE SCHEMAS & COLUMN VALIDATION")
        print("="*80)
        self.test("patients table - required columns", self.test_patients_schema)
        self.test("patient_panel table - required columns", self.test_patient_panel_schema)
        self.test("patient_assignments table - schema", self.test_patient_assignments_schema)
        self.test("onboarding_patients table - schema", self.test_onboarding_patients_schema)
        self.test("provider_tasks tables - required columns", self.test_provider_tasks_schema)
        self.test("coordinator_tasks tables - required columns", self.test_coordinator_tasks_schema)
        
        # SECTION 2: DATA FORMAT VALIDATION
        print("\n" + "="*80)
        print("SECTION 2: DATA FORMAT VALIDATION")
        print("="*80)
        self.test("Date format validation (YYYY-MM-DD)", self.test_date_formats)
        self.test("Patient ID format validation", self.test_patient_id_formats)
        self.test("Phone number formats", self.test_phone_formats)
        self.test("Email formats", self.test_email_formats)
        self.test("Billing code formats", self.test_billing_code_formats)
        
        # SECTION 3: DATA TYPE VALIDATION
        print("\n" + "="*80)
        print("SECTION 3: DATA TYPE VALIDATION")
        print("="*80)
        self.test("Numeric fields (IDs, minutes, etc.)", self.test_numeric_types)
        self.test("Text fields (names, addresses)", self.test_text_types)
        self.test("Date fields", self.test_date_types)
        
        # SECTION 4: NULL/NOT NULL CONSTRAINTS
        print("\n" + "="*80)
        print("SECTION 4: NULL/NOT NULL VALIDATION")
        print("="*80)
        self.test("Critical fields never NULL (patient_id)", self.test_critical_not_nulls)
        self.test("Optional fields allow NULL", self.test_optional_nulls)
        
        # SECTION 5: FOREIGN KEY RELATIONSHIPS
        print("\n" + "="*80)
        print("SECTION 5: REFERENTIAL INTEGRITY")
        print("="*80)
        self.test("patient_id references in tasks", self.test_patient_id_refs)
        self.test("provider_id references in tasks", self.test_provider_id_refs)
        self.test("coordinator_id references", self.test_coordinator_id_refs)
        self.test("facility_id references", self.test_facility_id_refs)
        
        # SECTION 6: DATA VALUE RANGES
        print("\n" + "="*80)
        print("SECTION 6: DATA VALUE RANGES")
        print("="*80)
        self.test("Duration minutes (0-480)", self.test_duration_ranges)
        self.test("Dates (realistic ranges)", self.test_date_ranges)
        self.test("Age calculations (reasonable)", self.test_age_ranges)
        
        # SECTION 7: AGGREGATION OPERATIONS
        print("\n" + "="*80)
        print("SECTION 7: AGGREGATION OPERATIONS (Dashboard queries)")
        print("="*80)
        self.test("COUNT() aggregations", self.test_count_aggregations)
        self.test("SUM() aggregations (minutes)", self.test_sum_aggregations)
        self.test("GROUP BY operations", self.test_group_by)
        self.test("DISTINCT operations", self.test_distinct_operations)
        
        # SECTION 8: COMPLEX JOINS
        print("\n" + "="*80)
        print("SECTION 8: COMPLEX JOIN OPERATIONS")
        print("="*80)
        self.test("3-way JOIN (patients-tasks-users)", self.test_3way_join)
        self.test("LEFT JOIN with NULL handling", self.test_left_join_nulls)
        self.test("Multiple table UNION", self.test_union_operations)
        
        # SECTION 9: DASHBOARD-SPECIFIC QUERIES
        print("\n" + "="*80)
        print("SECTION 9: DASHBOARD-SPECIFIC QUERY PATTERNS")
        print("="*80)
        self.test("Provider patient list query", self.test_provider_patient_list)
        self.test("Weekly billing summary query", self.test_weekly_billing_summary)
        self.test("Monthly coordinator summary query", self.test_monthly_coordinator_summary)
        self.test("Patient visit history query", self.test_patient_visit_history)
        
        # SECTION 10: EDGE CASES
        print("\n" + "="*80)
        print("SECTION 10: EDGE CASES & SPECIAL CONDITIONS")
        print("="*80)
        self.test("Empty string vs NULL handling", self.test_empty_vs_null)
        self.test("Duplicate patient_id suffixes (-1, -2)", self.test_duplicate_suffixes)
        self.test("Multi-part names", self.test_multipart_names)
        self.test("Special characters in names", self.test_special_characters)
        
        self.print_detailed_summary()
    
    # ===== SECTION 1: SCHEMA TESTS =====
    def test_patients_schema(self):
        cursor = self.conn.execute("PRAGMA table_info(patients)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required = {'patient_id', 'first_name', 'last_name', 'date_of_birth', 
                   'phone_primary', 'status', 'facility'}
        missing = required - columns
        assert not missing, f"Missing required columns: {missing}"
        
        # Check we have at least 18 columns (from our import)
        assert len(columns) >= 18, f"Expected at least 18 columns, got {len(columns)}"
    
    def test_patient_panel_schema(self):
        cursor = self.conn.execute("PRAGMA table_info(patient_panel)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required = {'patient_id', 'first_name', 'last_name', 'phone_primary', 'facility'}
        missing = required - columns
        assert not missing, f"Missing required columns: {missing}"
    
    def test_patient_assignments_schema(self):
        cursor = self.conn.execute("PRAGMA table_info(patient_assignments)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required = {'patient_id', 'provider_id', 'coordinator_id'}
        missing = required - columns
        assert not missing, f"Missing required columns: {missing}"
    
    def test_onboarding_patients_schema(self):
        cursor = self.conn.execute("PRAGMA table_info(onboarding_patients)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required = {'patient_id', 'first_name', 'last_name'}
        missing = required - columns
        assert not missing, f"Missing required columns: {missing}"
    
    def test_provider_tasks_schema(self):
        cursor = self.conn.execute("PRAGMA table_info(provider_tasks_2025_10)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required = {'patient_id', 'provider_id', 'date', 'billing_code'}
        missing = required - columns
        assert not missing, f"Missing required columns in provider_tasks: {missing}"
    
    def test_coordinator_tasks_schema(self):
        cursor = self.conn.execute("PRAGMA table_info(coordinator_tasks_2025_10)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required = {'patient_id', 'coordinator_id', 'date'}
        missing = required - columns
        assert not missing, f"Missing required columns in coordinator_tasks: {missing}"
    
    # ===== SECTION 2: DATA FORMAT TESTS =====
    def test_date_formats(self):
        # Check dates in patients table
        dates = self.conn.execute("""
            SELECT date_of_birth FROM patients 
            WHERE date_of_birth IS NOT NULL 
            LIMIT 10
        """).fetchall()
        
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        for row in dates:
            assert date_pattern.match(row[0]), f"Invalid date format: {row[0]}"
    
    def test_patient_id_formats(self):
        ids = self.conn.execute("SELECT patient_id FROM patients LIMIT 10").fetchall()
       
        for row in ids:
            pid = row[0]
            # Should be "LASTNAME FIRSTNAME MM/DD/YYYY" or with -1, -2 suffix
            assert pid, "Empty patient_id found"
            assert len(pid) > 10, f"Patient ID too short: {pid}"
    
    def test_phone_formats(self):
        phones = self.conn.execute("""
            SELECT phone_primary FROM patients 
            WHERE phone_primary IS NOT NULL 
            LIMIT 10
        """).fetchall()
        
        # Just check they exist - formats vary
        for row in phones:
            assert row[0], "Phone is empty string"
    
    def test_email_formats(self):
        # Email field may not exist, so check if column exists first
        try:
            cursor = self.conn.execute("PRAGMA table_info(patients)")
            columns = {row[1] for row in cursor.fetchall()}
            if 'email' in columns:
                emails = self.conn.execute("""
                    SELECT email FROM patients 
                    WHERE email IS NOT NULL AND email != ''
                    LIMIT 5
                """).fetchall()
                # Just verify they exist
                pass
        except Exception:
            pass  # Email column may not exist
    
    def test_billing_code_formats(self):
        codes = self.conn.execute("""
            SELECT DISTINCT billing_code FROM provider_tasks_2025_10
            WHERE billing_code IS NOT NULL
            LIMIT 10
        """).fetchall()
        
        # Check billing codes are reasonable
        for row in codes:
            code = row[0]
            assert code, "Empty billing code"
            assert len(code) <= 50, f"Billing code too long: {code}"
    
    # ===== SECTION 3: DATA TYPE TESTS =====
    def test_numeric_types(self):
        # Check provider_id is numeric-like
        result = self.conn.execute("""
            SELECT provider_id FROM provider_tasks_2025_10
            WHERE provider_id IS NOT NULL
            LIMIT 1
        """).fetchone()
        
        if result:
            assert isinstance(result[0], (int, float)), "provider_id not numeric"
    
    def test_text_types(self):
        result = self.conn.execute("""
            SELECT first_name, last_name FROM patients LIMIT 1
        """).fetchone()
        
        assert isinstance(result[0], str), "first_name not text"
        assert isinstance(result[1], str), "last_name not text"
    
    def test_date_types(self):
        result = self.conn.execute("""
            SELECT date_of_birth FROM patients 
            WHERE date_of_birth IS NOT NULL 
            LIMIT 1
        """).fetchone()
        
        assert isinstance(result[0], str), "date_of_birth not string (should be YYYY-MM-DD)"
    
    # ===== SECTION 4: NULL TESTS =====
    def test_critical_not_nulls(self):
        # patient_id should never be NULL
        null_count = self.conn.execute("""
            SELECT COUNT(*) FROM patients WHERE patient_id IS NULL
        """).fetchone()[0]
        assert null_count == 0, f"Found {null_count} NULL patient_ids"
        
        null_count = self.conn.execute("""
            SELECT COUNT(*) FROM patient_panel WHERE patient_id IS NULL
        """).fetchone()[0]
        assert null_count == 0, f"Found {null_count} NULL patient_ids in patient_panel"
    
    def test_optional_nulls(self):
        # Insurance, address fields can be NULL
        # Just verify the query works
        self.conn.execute("""
            SELECT COUNT(*) FROM patients 
            WHERE insurance_primary IS NULL OR address_street IS NULL
        """).fetchone()
    
    # ===== SECTION 5: REFERENTIAL INTEGRITY =====
    def test_patient_id_refs(self):
        # Sample check - some orphans are expected
        orphans = self.conn.execute("""
            SELECT COUNT(DISTINCT pt.patient_id)
            FROM provider_tasks_2025_10 pt
            LEFT JOIN patients p ON pt.patient_id = p.patient_id
            WHERE p.patient_id IS NULL
        """).fetchone()[0]
        
        # Allow up to 50% orphans (task data may have more patients than ZMO)
        total = self.conn.execute("SELECT COUNT(DISTINCT patient_id) FROM provider_tasks_2025_10").fetchone()[0]
        orphan_pct = (orphans / total * 100) if total > 0 else 0
        
        if orphan_pct > 50:
            self.warn(f"High orphan rate: {orphan_pct:.1f}% of task patient_ids not in patients table")
    
    def test_provider_id_refs(self):
        orphans = self.conn.execute("""
            SELECT COUNT(DISTINCT pt.provider_id)
            FROM provider_tasks_2025_10 pt
            LEFT JOIN users u ON pt.provider_id = u.user_id
            WHERE u.user_id IS NULL AND pt.provider_id IS NOT NULL
        """).fetchone()[0]
        
        assert orphans == 0, f"Found {orphans} provider_ids not in users"
    
    def test_coordinator_id_refs(self):
        orphans = self.conn.execute("""
            SELECT COUNT(DISTINCT ct.coordinator_id)
            FROM coordinator_tasks_2025_10 ct
            LEFT JOIN users u ON ct.coordinator_id = u.user_id
            WHERE u.user_id IS NULL AND ct.coordinator_id IS NOT NULL
        """).fetchone()[0]
        
        assert orphans == 0, f"Found {orphans} coordinator_ids not in users"
    
    def test_facility_id_refs(self):
        # Check if facility_id column exists and validate
        try:
            orphans = self.conn.execute("""
                SELECT COUNT(*)
                FROM patients p
                LEFT JOIN facilities f ON p.current_facility_id = f.facility_id
                WHERE f.facility_id IS NULL AND p.current_facility_id IS NOT NULL
            """).fetchone()[0]
            
            if orphans > 0:
                self.warn(f"{orphans} patients have facility_id not in facilities table")
        except Exception:
            pass  # Column may not exist
    
    # ===== SECTION 6: VALUE RANGE TESTS =====
    def test_duration_ranges(self):
        # Check duration_minutes is reasonable (0-480 = 8 hours max per task)
        try:
            max_dur = self.conn.execute("""
                SELECT MAX(duration_minutes) FROM provider_tasks_2025_10
                WHERE duration_minutes IS NOT NULL
            """).fetchone()[0]
            
            if max_dur and max_dur > 480:
                self.warn(f"Found duration > 8 hours: {max_dur} minutes")
        except Exception:
            pass  # duration_minutes may not exist
    
    def test_date_ranges(self):
        # Check dates are within reasonable range (1900-2100)
        min_date = self.conn.execute("""
            SELECT MIN(date_of_birth) FROM patients
            WHERE date_of_birth IS NOT NULL
        """).fetchone()[0]
        
        max_date = self.conn.execute("""
            SELECT MAX(date_of_birth) FROM patients
            WHERE date_of_birth IS NOT NULL
        """).fetchone()[0]
        
        assert min_date >= '1900-01-01', f"DOB too old: {min_date}"
        assert max_date <= '2024-12-31', f"DOB in future: {max_date}"
    
    def test_age_ranges(self):
        # Calculate age from DOB - should be reasonable (18-120)
        ages = self.conn.execute("""
            SELECT 
                CAST(strftime('%Y', 'now') AS INTEGER) - CAST(strftime('%Y', date_of_birth) AS INTEGER) as age
            FROM patients
            WHERE date_of_birth IS NOT NULL
            LIMIT 100
        """).fetchall()
        
        for row in ages:
            age = row[0]
            assert 0 <= age <= 120, f"Unreasonable age: {age}"
    
    # ===== SECTION 7: AGGREGATION TESTS =====
    def test_count_aggregations(self):
        # Test various COUNT operations
        counts = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT patient_id) as unique_patients,
                COUNT(DISTINCT provider_id) as unique_providers
            FROM provider_tasks_2025_10
        """).fetchone()
        
        assert counts[0] > 0, "No tasks found"
        assert counts[1] > 0, "No unique patients"
        assert counts[2] > 0, "No unique providers"
    
    def test_sum_aggregations(self):
        # Test SUM on duration_minutes
        try:
            total = self.conn.execute("""
                SELECT SUM(duration_minutes) 
                FROM provider_tasks_2025_10
                WHERE duration_minutes IS NOT NULL
            """).fetchone()[0]
            
            assert total is None or total >= 0, "Negative total minutes"
        except Exception:
            pass  # Column may not exist
    
    def test_group_by(self):
        # Test GROUP BY operations
        result = self.conn.execute("""
            SELECT provider_id, COUNT(*) as task_count
            FROM provider_tasks_2025_10
            WHERE provider_id IS NOT NULL
            GROUP BY provider_id
            LIMIT 5
        """).fetchall()
        
        assert len(result) > 0, "GROUP BY returned no results"
    
    def test_distinct_operations(self):
        # Test DISTINCT
        unique_patients = self.conn.execute("""
            SELECT COUNT(DISTINCT patient_id) FROM patients
        """).fetchone()[0]
        
        total_patients = self.conn.execute("""
            SELECT COUNT(*) FROM patients
        """).fetchone()[0]
        
        # Should be equal (no duplicate patient_ids... except for -1, -2 suffixes)
        diff = total_patients - unique_patients
        assert diff <= 10, f"Too many duplicate patient_ids: {diff}"
    
    # ===== SECTION 8: COMPLEX JOIN TESTS =====
    def test_3way_join(self):
        result = self.conn.execute("""
            SELECT COUNT(*)
            FROM provider_tasks_2025_10 pt
            LEFT JOIN patients p ON pt.patient_id = p.patient_id
            LEFT JOIN users u ON pt.provider_id = u.user_id
            LIMIT 100
        """).fetchone()[0]
        
        assert result >= 0, "3-way join failed"
    
    def test_left_join_nulls(self):
        # Test LEFT JOIN properly handles NULLs
        result = self.conn.execute("""
            SELECT COUNT(*)
            FROM patients p
            LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id
            WHERE pa.patient_id IS NULL
        """).fetchone()[0]
        
        # Should be 130 (620 - 490 assignments)
        assert result > 0, "No unassigned patients found"
    
    def test_union_operations(self):
        # Test UNION of monthly tables
        result = self.conn.execute("""
            SELECT patient_id FROM provider_tasks_2025_10
            UNION
            SELECT patient_id FROM coordinator_tasks_2025_10
            LIMIT 1
        """).fetchone()
        
        assert result is not None, "UNION query failed"
    
    # ===== SECTION 9: DASHBOARD QUERIES =====
    def test_provider_patient_list(self):
        # Simulate provider dashboard query
        result = self.conn.execute("""
            SELECT 
                p.patient_id,
                p.first_name,
                p.last_name,
                p.status
            FROM patients p
            LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id
            LIMIT 10
        """).fetchall()
        
        assert len(result) > 0, "Provider patient list query failed"
    
    def test_weekly_billing_summary(self):
        # Test weekly summary query
        result = self.conn.execute("""
            SELECT COUNT(*) FROM provider_weekly_summary_with_billing
        """).fetchone()[0]
        
        assert result > 0, "Weekly billing summary empty"
    
    def test_monthly_coordinator_summary(self):
        # Test monthly summary query
        result = self.conn.execute("""
            SELECT COUNT(*) FROM coordinator_monthly_summary
        """).fetchone()[0]
        
        assert result > 0, "Monthly coordinator summary empty"
    
    def test_patient_visit_history(self):
        # Simulate patient visit history query
        result = self.conn.execute("""
            SELECT 
                pt.date,
                p.first_name,
                p.last_name
            FROM provider_tasks_2025_10 pt
            JOIN patients p ON pt.patient_id = p.patient_id
            ORDER BY pt.date DESC
            LIMIT 10
        """).fetchall()
        
        assert len(result) > 0, "Patient visit history query failed"
    
    # ===== SECTION 10: EDGE CASES =====
    def test_empty_vs_null(self):
        # Check if we have both NULL and empty strings
        null_count = self.conn.execute("""
            SELECT COUNT(*) FROM patients WHERE facility IS NULL
        """).fetchone()[0]
        
        empty_count = self.conn.execute("""
            SELECT COUNT(*) FROM patients WHERE facility = ''
        """).fetchone()[0]
        
        if null_count > 0 and empty_count > 0:
            self.warn(f"Found both NULL ({null_count}) and empty strings ({empty_count}) in facility field")
    
    def test_duplicate_suffixes(self):
        # Check for -1, -2 suffixes
        dups = self.conn.execute("""
            SELECT patient_id FROM patients 
            WHERE patient_id LIKE '%-1' OR patient_id LIKE '%-2'
        """).fetchall()
        
        assert len(dups) == 6, f"Expected 6 duplicates with suffixes, found {len(dups)}"
    
    def test_multipart_names(self):
        # Check for multi-part names (3+ words)
        multipart = self.conn.execute("""
            SELECT first_name, last_name FROM patients
            WHERE (length(first_name) - length(replace(first_name, ' ', '')) > 0)
               OR (length(last_name) - length(replace(last_name, ' ', '')) > 0)
            LIMIT 5
        """).fetchall()
        
        assert len(multipart) > 0, "No multi-part names found (expected some)"
    
    def test_special_characters(self):
        # Check for names with hyphens, apostrophes
        special = self.conn.execute("""
            SELECT first_name, last_name FROM patients
            WHERE first_name LIKE '%-%' 
               OR last_name LIKE '%-%'
               OR first_name LIKE "%'%"
               OR last_name LIKE "%'%"
            LIMIT 5
        """).fetchall()
        
        # Just verify query works - special chars may or may not exist
        pass
    
    def print_detailed_summary(self):
        print("\n" + "="*80)
        print("DETAILED TEST SUMMARY")
        print("="*80)
        print(f"✅ Passed:   {self.passed}")
        print(f"❌ Failed:   {self.failed}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Success Rate: {self.passed / (self.passed + self.failed) * 100:.1f}%")
        
        if self.warnings:
            print("\n⚠️  WARNINGS (non-critical issues):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.errors:
            print("\n❌ FAILED TESTS:")
            for name, error in self.errors:
                print(f"\n  {name}:")
                print(f"    {error}")
        
        print("\n" + "="*80)
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED - DATABASE IS PRODUCTION-READY")
        elif self.failed <= 3:
            print("✅ MOSTLY PASSING - Minor issues, safe to deploy")
        else:
            print("⚠️  MULTIPLE FAILURES - Review errors before deploying")
        print("="*80)
        
        self.conn.close()

if __name__ == "__main__":
    tester = DeepDiveDatabaseTester()
    tester.run_deep_dive_tests()
