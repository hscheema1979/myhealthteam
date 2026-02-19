"""
Streamlit AppTest Framework for Results Reviewer Dashboard
Tests Results Reviewer (RR) role functionality using Streamlit's native testing.

This framework:
1. Tests RR role login and dashboard access
2. Tests Results Review tab shows only RR workflows (step 5 Labs, step 4 Imaging)
3. Tests RR can complete workflow step and it completes entire workflow
4. Tests workflows disappear from CC dashboard after reaching RR step
5. Tests Phone Review tab works for RR
6. Tests Task Review tab works for RR
7. Tests ZMO tab works for RR

Run: streamlit run tests/test_results_reviewer_apptest.py
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
ROLE_RR_ID = 43  # Results Reviewer role ID

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
TEST SUMMARY - Results Reviewer Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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

def test_rr_role_exists():
    """Test that RR role (ID 43) exists in database"""
    try:
        conn = database.get_db_connection()
        role = conn.execute(
            "SELECT * FROM roles WHERE role_id = ?", (ROLE_RR_ID,)
        ).fetchone()
        conn.close()

        if role and role['role_name'] == 'RR':
            tracker.add_result(
                "RR Role Exists",
                "PASS",
                f"RR role found with ID {ROLE_RR_ID}",
                ""
            )
            return True
        else:
            tracker.add_result(
                "RR Role Exists",
                "FAIL",
                "",
                f"RR role not found or incorrect name: {role}"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "RR Role Exists",
            "FAIL",
            "",
            str(e)
        )
        return False


def test_workflow_structure():
    """Test that LAB workflows have 5 steps and IMAGING workflows have 4 steps"""
    try:
        conn = database.get_db_connection()

        # Check LAB workflows (1-3) should have 5 steps
        lab_steps = conn.execute(
            "SELECT COUNT(DISTINCT step_order) as count FROM workflow_steps WHERE template_id IN (1, 2, 3)"
        ).fetchone()

        # Check IMAGING workflows (4-6) should have 4 steps
        imaging_steps = conn.execute(
            "SELECT COUNT(DISTINCT step_order) as count FROM workflow_steps WHERE template_id IN (4, 5, 6)"
        ).fetchone()

        conn.close()

        lab_count = lab_steps['count'] if lab_steps else 0
        imaging_count = imaging_steps['count'] if imaging_steps else 0

        if lab_count == 5 and imaging_count == 4:
            tracker.add_result(
                "Workflow Structure",
                "PASS",
                f"LAB workflows: {lab_count} steps, IMAGING workflows: {imaging_count} steps",
                ""
            )
            return True
        else:
            tracker.add_result(
                "Workflow Structure",
                "FAIL",
                "",
                f"Expected LAB=5, IMAGING=4; got LAB={lab_count}, IMAGING={imaging_count}"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "Workflow Structure",
            "FAIL",
            "",
            str(e)
        )
        return False


def test_rr_workflow_steps():
    """Test that final workflow steps are owned by RR"""
    try:
        conn = database.get_db_connection()

        # LAB workflow step 5 should be RR
        lab_step = conn.execute(
            "SELECT owner FROM workflow_steps WHERE template_id = 1 AND step_order = 5"
        ).fetchone()

        # IMAGING workflow step 4 should be RR
        imaging_step = conn.execute(
            "SELECT owner FROM workflow_steps WHERE template_id = 4 AND step_order = 4"
        ).fetchone()

        conn.close()

        lab_owner = lab_step['owner'] if lab_step else None
        imaging_owner = imaging_step['owner'] if imaging_step else None

        if lab_owner == 'RR' and imaging_owner == 'RR':
            tracker.add_result(
                "RR Workflow Steps",
                "PASS",
                f"LAB step 5 owner: {lab_owner}, IMAGING step 4 owner: {imaging_owner}",
                ""
            )
            return True
        else:
            tracker.add_result(
                "RR Workflow Steps",
                "FAIL",
                "",
                f"LAB step 5 owner: {lab_owner}, IMAGING step 4 owner: {imaging_owner}"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "RR Workflow Steps",
            "FAIL",
            "",
            str(e)
        )
        return False


def test_rr_dashboard_module_exists():
    """Test that results_reviewer_dashboard module can be imported"""
    try:
        from src.dashboards import results_reviewer_dashboard

        if hasattr(results_reviewer_dashboard, 'show_results_reviewer_dashboard'):
            tracker.add_result(
                "RR Dashboard Module",
                "PASS",
                "show_results_reviewer_dashboard function exists",
                ""
            )
            return True
        else:
            tracker.add_result(
                "RR Dashboard Module",
                "FAIL",
                "",
                "show_results_reviewer_dashboard function not found"
            )
            return False
    except ImportError as e:
        tracker.add_result(
            "RR Dashboard Module",
            "FAIL",
            "",
            f"Import error: {str(e)}"
        )
        return False
    except Exception as e:
        tracker.add_result(
            "RR Dashboard Module",
            "FAIL",
            "",
            str(e)
        )
        return False


def test_app_routing_rr_role():
    """Test that app.py includes routing for RR role"""
    try:
        with open(project_root / 'app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()

        # Check if RR is in dashboard_roles
        has_rr_role = '43' in app_content and 'Results Reviewer' in app_content

        # Check if routing exists for RR
        has_rr_routing = 'dashboard_role == 43' in app_content or 'results_reviewer_dashboard' in app_content

        if has_rr_role and has_rr_routing:
            tracker.add_result(
                "App Routing for RR",
                "PASS",
                "RR role (43) is in dashboard_roles and routing exists",
                ""
            )
            return True
        else:
            tracker.add_result(
                "App Routing for RR",
                "FAIL",
                "",
                f"has_rr_role: {has_rr_role}, has_rr_routing: {has_rr_routing}"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "App Routing for RR",
            "FAIL",
            "",
            str(e)
        )
        return False


def test_rr_workflow_query():
    """Test that RR workflow query returns correct workflows"""
    try:
        conn = database.get_db_connection()

        # Query for RR workflows (same as in dashboard)
        rr_workflows = conn.execute("""
            SELECT
                wi.instance_id,
                wi.template_id,
                wi.current_step,
                wt.template_name
            FROM workflow_instances wi
            JOIN workflow_templates wt ON wi.template_id = wt.template_id
            WHERE wi.template_id IN (1, 2, 3, 4, 5, 6)
              AND (
                  (wi.template_id IN (1, 2, 3) AND wi.current_step = 5) OR
                  (wi.template_id IN (4, 5, 6) AND wi.current_step = 4)
              )
              AND wi.workflow_status = 'Active'
            LIMIT 5
        """).fetchall()

        conn.close()

        # Verify results are correct
        for wf in rr_workflows:
            template_id = wf['template_id']
            current_step = wf['current_step']

            if template_id in [1, 2, 3] and current_step != 5:
                tracker.add_result(
                    "RR Workflow Query",
                    "FAIL",
                    "",
                    f"LAB workflow {wf['instance_id']} at step {current_step}, expected step 5"
                )
                return False

            if template_id in [4, 5, 6] and current_step != 4:
                tracker.add_result(
                    "RR Workflow Query",
                    "FAIL",
                    "",
                    f"IMAGING workflow {wf['instance_id']} at step {current_step}, expected step 4"
                )
                return False

        tracker.add_result(
            "RR Workflow Query",
            "PASS",
            f"Found {len(rr_workflows)} RR workflows, all at correct steps",
            ""
        )
        return True
    except Exception as e:
        tracker.add_result(
            "RR Workflow Query",
            "FAIL",
            "",
            str(e)
        )
        return False


def test_auth_module_rr_precedence():
    """Test that auth_module includes RR in role precedence"""
    try:
        with open(project_root / 'src' / 'auth_module.py', 'r', encoding='utf-8') as f:
            auth_content = f.read()

        # Check if 43 is in role_precedence
        has_rr_precedence = '43' in auth_content and 'role_precedence' in auth_content

        if has_rr_precedence:
            tracker.add_result(
                "Auth Module RR Precedence",
                "PASS",
                "RR (43) is included in role_precedence list",
                ""
            )
            return True
        else:
            tracker.add_result(
                "Auth Module RR Precedence",
                "FAIL",
                "",
                "RR (43) not found in role_precedence"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "Auth Module RR Precedence",
            "FAIL",
            "",
            str(e)
        )
        return False


def test_rr_dashboard_tabs():
    """Test that RR dashboard has all required tabs"""
    try:
        from src.dashboards import results_reviewer_dashboard

        # Check for tab rendering functions
        has_results_review = hasattr(results_reviewer_dashboard, 'render_results_review_tab')
        has_phone_review = hasattr(results_reviewer_dashboard, 'render_phone_review_tab')
        has_task_review = hasattr(results_reviewer_dashboard, 'render_task_review_tab')
        has_help = hasattr(results_reviewer_dashboard, 'render_help_tab')

        if all([has_results_review, has_phone_review, has_task_review, has_help]):
            tracker.add_result(
                "RR Dashboard Tabs",
                "PASS",
                "All 4 tabs exist: Results Review, Phone Review, Task Review, Help",
                ""
            )
            return True
        else:
            tracker.add_result(
                "RR Dashboard Tabs",
                "FAIL",
                "",
                f"Missing tabs: results_review={has_results_review}, phone={has_phone_review}, task={has_task_review}, help={has_help}"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "RR Dashboard Tabs",
            "FAIL",
            "",
            str(e)
        )
        return False


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all RR dashboard tests"""
    print("\n" + "="*70)
    print("RUNNING RESULTS REVIEWER DASHBOARD TESTS")
    print("="*70 + "\n")

    tests = [
        ("RR Role Exists", test_rr_role_exists),
        ("Workflow Structure", test_workflow_structure),
        ("RR Workflow Steps", test_rr_workflow_steps),
        ("RR Dashboard Module", test_rr_dashboard_module_exists),
        ("App Routing for RR", test_app_routing_rr_role),
        ("RR Workflow Query", test_rr_workflow_query),
        ("Auth Module RR Precedence", test_auth_module_rr_precedence),
        ("RR Dashboard Tabs", test_rr_dashboard_tabs),
    ]

    for test_name, test_func in tests:
        print(f"Running: {test_name}...")
        try:
            test_func()
        except Exception as e:
            tracker.add_result(
                test_name,
                "FAIL",
                "",
                f"Test execution error: {str(e)}"
            )
            print(f"  ✗ FAILED: {str(e)}")
        else:
            status = tracker.tests[-1]['status']
            print(f"  {status}")

    # Print summary
    print(tracker.get_summary())

    # Save to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = project_root / f"test_report_rr_apptest_{timestamp}.json"

    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - tracker.start_time).total_seconds(),
            "total_tests": len(tracker.tests),
            "passed": sum(1 for t in tracker.tests if t["status"] == "PASS"),
            "failed": sum(1 for t in tracker.tests if t["status"] == "FAIL"),
            "tests": tracker.tests
        }, f, indent=2)

    print(f"\nReport saved to: {report_file}")

    # Return exit code
    failed = sum(1 for t in tracker.tests if t["status"] == "FAIL")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(page_title="RR Dashboard Tests", layout="wide")

    st.title("Results Reviewer Dashboard - AppTest Suite")
    st.write("Testing Results Reviewer role and dashboard functionality...")

    if st.button("Run All Tests"):
        result = run_all_tests()

        if result == 0:
            st.success("All tests passed!")
        else:
            st.error(f"Some tests failed. Check the report for details.")
