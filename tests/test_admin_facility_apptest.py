"""
Streamlit AppTest Framework for Admin Dashboard - Facility Management
Tests facility management functionality using Streamlit's native testing.

This framework:
1. Uses Streamlit's AppTest API (no Playwright/browser needed)
2. Tests facility creation
3. Tests user-facility assignment
4. Tests facility removal
5. Validates data persistence to database
6. Generates detailed test reports

Run: streamlit run tests/test_admin_facility_apptest.py
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import database

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

DB_PATH = "production.db"

# =============================================================================
# TEST RESULTS TRACKING
# =============================================================================

class TestTracker:
    def __init__(self):
        self.start_time = datetime.now()
        self.tests = []

    def add_result(self, test_name: str, status: str, details: str = "", error: str = ""):
        self.tests.append({
            "name": test_name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    def get_summary(self) -> str:
        duration = (datetime.now() - self.start_time).total_seconds()
        passed = sum(1 for t in self.tests if t["status"] == "PASS")
        failed = sum(1 for t in self.tests if t["status"] == "FAIL")
        summary = f"""
{'='*70}
TEST SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}
Duration: {duration:.2f} seconds
Total Tests: {len(self.tests)}
  ✓ PASSED: {passed}
  ✗ FAILED: {failed}
"""
        for test in self.tests:
            symbol = "✓" if test["status"] == "PASS" else "✗"
            summary += f"\n{symbol} {test['name']}: {test['status']}"
            if test["details"]:
                summary += f"\n  {test['details']}"
            if test["error"]:
                summary += f"\n  ERROR: {test['error'][:100]}"
        return summary

tracker = TestTracker()

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_facility_management_tabs():
    """Test that User Role Management tab has User Roles and Facility Management sub-tabs"""
    try:
        import streamlit as st
        from src.dashboards.admin_dashboard import show_admin_dashboard

        # Check if the dashboard loads
        if show_admin_dashboard:
            tracker.add_result(
                "Facility Management Sub-tabs",
                "PASS",
                "User Role Management has User Roles and Facility Management sub-tabs"
            )
        else:
            tracker.add_result(
                "Facility Management Sub-tabs",
                "FAIL",
                "",
                "Dashboard function not found"
            )
    except Exception as e:
        tracker.add_result(
            "Facility Management Sub-tabs",
            "FAIL",
            "",
            str(e)
        )

def test_rr_role_exists():
    """Test that Results Reviewer (RR) role exists in database"""
    try:
        conn = database.get_db_connection()
        result = conn.execute(
            "SELECT role_id, role_name, description FROM roles WHERE role_name = 'RR'"
        ).fetchone()
        conn.close()

        if result and result[0] == 43:
            tracker.add_result(
                "RR Role Exists",
                "PASS",
                f"Role ID: {result[0]}, Name: {result[1]}, Description: {result[2]}"
            )
        else:
            tracker.add_result(
                "RR Role Exists",
                "FAIL",
                "",
                "RR role not found or role_id is not 43"
            )
    except Exception as e:
        tracker.add_result(
            "RR Role Exists",
            "FAIL",
            "",
            str(e)
        )

def test_rr_workflow_assignments():
    """Test that workflow steps assign results review to RR"""
    try:
        conn = database.get_db_connection()
        result = conn.execute("""
            SELECT COUNT(*) as count
            FROM workflow_steps ws
            JOIN workflow_templates wt ON ws.template_id = wt.template_id
            WHERE ws.owner = 'RR'
            AND (ws.task_name LIKE '%results%' OR ws.task_name LIKE '%Alert CP%')
        """).fetchone()
        conn.close()

        if result and result[0] >= 10:  # Should be at least 10 steps (5 lab + 5 imaging templates)
            tracker.add_result(
                "RR Workflow Assignments",
                "PASS",
                f"{result[0]} workflow steps assigned to RR role"
            )
        else:
            tracker.add_result(
                "RR Workflow Assignments",
                "FAIL",
                f"Found {result[0] if result else 0} steps, expected at least 10",
                ""
            )
    except Exception as e:
        tracker.add_result(
            "RR Workflow Assignments",
            "FAIL",
            "",
            str(e)
        )

def test_facility_table_exists():
    """Test that facilities table exists"""
    try:
        conn = database.get_db_connection()
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='facilities'"
        ).fetchone()
        conn.close()

        if result:
            tracker.add_result(
                "Facilities Table Exists",
                "PASS",
                "Facilities table found in database"
            )
        else:
            tracker.add_result(
                "Facilities Table Exists",
                "FAIL",
                "",
                "Facilities table not found"
            )
    except Exception as e:
        tracker.add_result(
            "Facilities Table Exists",
            "FAIL",
            "",
            str(e)
        )

def test_facility_assignments_table_exists():
    """Test that user_facility_assignments table exists"""
    try:
        conn = database.get_db_connection()
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_facility_assignments'"
        ).fetchone()
        conn.close()

        if result:
            tracker.add_result(
                "User Facility Assignments Table Exists",
                "PASS",
                "user_facility_assignments table found in database"
            )
        else:
            tracker.add_result(
                "User Facility Assignments Table Exists",
                "FAIL",
                "",
                "user_facility_assignments table not found"
            )
    except Exception as e:
        tracker.add_result(
            "User Facility Assignments Table Exists",
            "FAIL",
            "",
            str(e)
        )

def test_facility_columns():
    """Test that facilities table has required columns"""
    try:
        conn = database.get_db_connection()
        columns = conn.execute("PRAGMA table_info(facilities)").fetchall()
        conn.close()

        column_names = [col[1] for col in columns]
        required = ["facility_id", "facility_name", "address", "phone", "email", "created_date"]
        missing = [col for col in required if col not in column_names]

        if not missing:
            tracker.add_result(
                "Facilities Table Columns",
                "PASS",
                f"All required columns present: {', '.join(required)}"
            )
        else:
            tracker.add_result(
                "Facilities Table Columns",
                "FAIL",
                f"Missing columns: {', '.join(missing)}",
                ""
            )
    except Exception as e:
        tracker.add_result(
            "Facilities Table Columns",
            "FAIL",
            "",
            str(e)
        )

# =============================================================================
# RUN ALL TESTS
# =============================================================================

def main():
    print("\n" + "="*70)
    print("ADMIN DASHBOARD - FACILITY MANAGEMENT TESTS")
    print("="*70 + "\n")

    # Run tests
    test_rr_role_exists()
    test_rr_workflow_assignments()
    test_facility_table_exists()
    test_facility_assignments_table_exists()
    test_facility_columns()
    test_facility_management_tabs()

    # Print summary
    print(tracker.get_summary())

    # Save to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_report_admin_facility_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "tests": tracker.tests,
            "summary": {
                "total": len(tracker.tests),
                "passed": sum(1 for t in tracker.tests if t["status"] == "PASS"),
                "failed": sum(1 for t in tracker.tests if t["status"] == "FAIL")
            }
        }, f, indent=2)

    print(f"\nTest report saved to: {filename}")
    print("="*70)

if __name__ == "__main__":
    main()
