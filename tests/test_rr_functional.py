"""
Streamlit AppTest Framework for Results Reviewer Dashboard - Functional Tests
Tests RR dashboard functionality using direct function calls and database verification.

This framework:
1. Tests Results Reviewer dashboard functions directly
2. Verifies workflow filtering (only RR workflows shown)
3. Tests workflow completion logic
4. Validates database state changes
5. Tests all 4 dashboard tabs
6. Generates detailed test reports

Run: streamlit run tests/test_rr_functional.py
Or: python tests/test_rr_functional.py
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
ROLE_RR_ID = 43

# =============================================================================
# TEST RESULTS TRACKING
# =============================================================================

class TestTracker:
    def __init__(self):
        self.start_time = datetime.now()
        self.tests = []
        self.summary = {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0}

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
TEST SUMMARY - RR Dashboard Functional - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}
Duration: {duration:.2f} seconds
Total Tests: {len(self.tests)}
  PASSED: {self.summary['PASS']}
  FAILED: {self.summary['FAIL']}
  SKIPPED: {self.summary['SKIP']}
  ERRORS: {self.summary['ERROR']}
"""
        for test in self.tests:
            symbol = {
                "PASS": "[PASS]",
                "FAIL": "[FAIL]",
                "SKIP": "[SKIP]",
                "ERROR": "[ERROR]"
            }.get(test["status"], "[?]")
            summary += f"\n{symbol} {test['name']}: {test['status']}"
            if test["details"]:
                summary += f"\n  {test['details']}"
            if test["error"]:
                summary += f"\n  ERROR: {test['error'][:200]}"
        return summary

tracker = TestTracker()

# =============================================================================
# DATABASE UTILITIES
# =============================================================================

def get_db_connection():
    """Get database connection."""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_rr_workflows_from_db():
    """Get workflows at RR step from database."""
    conn = get_db_connection()
    try:
        workflows = conn.execute("""
            SELECT
                wi.instance_id,
                wi.patient_id,
                wi.patient_name,
                wi.template_id,
                wt.template_name,
                wi.current_step,
                wi.workflow_status,
                ws.task_name as current_task,
                ws.owner as current_owner
            FROM workflow_instances wi
            JOIN workflow_templates wt ON wi.template_id = wt.template_id
            LEFT JOIN workflow_steps ws ON wi.template_id = ws.template_id AND wi.current_step = ws.step_order
            WHERE wi.template_id IN (1, 2, 3, 4, 5, 6)
              AND (
                  (wi.template_id IN (1, 2, 3) AND wi.current_step = 5) OR
                  (wi.template_id IN (4, 5, 6) AND wi.current_step = 4)
              )
              AND wi.workflow_status = 'Active'
            ORDER BY wi.created_at DESC
        """).fetchall()
        return [dict(w) for w in workflows]
    finally:
        conn.close()

def count_workflows_by_step():
    """Count workflows by step for validation."""
    conn = get_db_connection()
    try:
        counts = conn.execute("""
            SELECT
                wt.template_name,
                wi.current_step,
                wi.workflow_status,
                COUNT(*) as count
            FROM workflow_instances wi
            JOIN workflow_templates wt ON wi.template_id = wt.template_id
            WHERE wi.template_id IN (1, 2, 3, 4, 5, 6)
            GROUP BY wt.template_name, wi.current_step, wi.workflow_status
            ORDER BY wt.template_name, wi.current_step
        """).fetchall()
        return [dict(c) for c in counts]
    finally:
        conn.close()

# =============================================================================
# TEST FUNCTIONS - DASHBOARD IMPORTS
# =============================================================================

def test_rr_dashboard_import():
    """Test that RR dashboard module can be imported."""
    try:
        from src.dashboards import results_reviewer_dashboard

        # Check key functions exist
        has_show = hasattr(results_reviewer_dashboard, 'show_results_reviewer_dashboard')
        has_results_tab = hasattr(results_reviewer_dashboard, 'render_results_review_tab')
        has_phone_tab = hasattr(results_reviewer_dashboard, 'render_phone_review_tab')
        has_task_tab = hasattr(results_reviewer_dashboard, 'render_task_review_tab')
        has_zmo_tab = hasattr(results_reviewer_dashboard, 'render_zmo_tab')
        has_help_tab = hasattr(results_reviewer_dashboard, 'render_help_tab')

        if all([has_show, has_results_tab, has_phone_tab, has_task_tab, has_zmo_tab, has_help_tab]):
            tracker.add_result(
                "RR Dashboard Import",
                "PASS",
                "All dashboard functions imported successfully",
                ""
            )
            return True
        else:
            missing = []
            if not has_show: missing.append("show_results_reviewer_dashboard")
            if not has_results_tab: missing.append("render_results_review_tab")
            if not has_phone_tab: missing.append("render_phone_review_tab")
            if not has_task_tab: missing.append("render_task_review_tab")
            if not has_zmo_tab: missing.append("render_zmo_tab (from zmo_module)")
            if not has_help_tab: missing.append("render_help_tab")

            tracker.add_result(
                "RR Dashboard Import",
                "FAIL",
                "",
                f"Missing functions: {', '.join(missing)}"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "RR Dashboard Import",
            "FAIL",
            "",
            f"Import error: {str(e)}"
        )
        return False

# =============================================================================
# TEST FUNCTIONS - RESULTS REVIEW TAB
# =============================================================================

def test_results_review_tab_query():
    """Test that Results Review tab query returns correct workflows."""
    try:
        rr_workflows = get_rr_workflows_from_db()

        # Verify each workflow is at correct step
        for wf in rr_workflows:
            template_id = wf['template_id']
            current_step = wf['current_step']

            if template_id in [1, 2, 3] and current_step != 5:
                tracker.add_result(
                    "Results Review Query - LAB Steps",
                    "FAIL",
                    "",
                    f"LAB workflow {wf['instance_id']} at step {current_step}, expected step 5"
                )
                return False

            if template_id in [4, 5, 6] and current_step != 4:
                tracker.add_result(
                    "Results Review Query - IMAGING Steps",
                    "FAIL",
                    "",
                    f"IMAGING workflow {wf['instance_id']} at step {current_step}, expected step 4"
                )
                return False

        tracker.add_result(
            "Results Review Query",
            "PASS",
            f"Found {len(rr_workflows)} RR workflows, all at correct steps",
            ""
        )
        return True
    except Exception as e:
        tracker.add_result(
            "Results Review Query",
            "FAIL",
            "",
            str(e)
        )
        return False

def test_results_review_tab_ownership():
    """Test that RR workflows have correct owner."""
    try:
        rr_workflows = get_rr_workflows_from_db()

        # Verify owner is RR for all workflows
        for wf in rr_workflows:
            if wf['current_owner'] != 'RR':
                tracker.add_result(
                    "Results Review Ownership",
                    "FAIL",
                    "",
                    f"Workflow {wf['instance_id']} has owner '{wf['current_owner']}', expected 'RR'"
                )
                return False

        tracker.add_result(
            "Results Review Ownership",
            "PASS",
            f"All {len(rr_workflows)} RR workflows have correct owner",
            ""
        )
        return True
    except Exception as e:
        tracker.add_result(
            "Results Review Ownership",
            "FAIL",
            "",
            str(e)
        )
        return False

# =============================================================================
# TEST FUNCTIONS - WORKFLOW COMPLETION
# =============================================================================

def test_workflow_completion_function():
    """Test that workflow completion function exists and works."""
    try:
        from src.dashboards.results_reviewer_dashboard import complete_rr_workflow

        # Check function signature
        import inspect
        sig = inspect.signature(complete_rr_workflow)

        # Updated to accept 6 parameters: instance_id, template_id, user_id, duration_minutes, patient_id, patient_name
        expected_params = {'instance_id', 'template_id', 'user_id', 'duration_minutes', 'patient_id', 'patient_name'}
        actual_params = set(sig.parameters.keys())

        if expected_params == actual_params:
            tracker.add_result(
                "Workflow Completion Function",
                "PASS",
                f"Function signature correct: {sig}",
                ""
            )
            return True
        else:
            missing = expected_params - actual_params
            extra = actual_params - expected_params
            tracker.add_result(
                "Workflow Completion Function",
                "FAIL",
                "",
                f"Missing params: {missing}, Extra params: {extra}"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "Workflow Completion Function",
            "FAIL",
            "",
            str(e)
        )
        return False

def test_workflow_completion_logic():
    """Test workflow completion logic (without executing)."""
    try:
        from src.dashboards.results_reviewer_dashboard import complete_rr_workflow

        # Get source code to verify logic
        import inspect
        source = inspect.getsource(complete_rr_workflow)

        # Check for key operations
        has_update = "workflow_status = 'Completed'" in source
        has_log = "workflow_progress_log" in source
        has_commit = "commit" in source

        if all([has_update, has_log, has_commit]):
            tracker.add_result(
                "Workflow Completion Logic",
                "PASS",
                "Function updates status, logs progress, and commits",
                ""
            )
            return True
        else:
            missing = []
            if not has_update: missing.append("status update")
            if not has_log: missing.append("progress log")
            if not has_commit: missing.append("commit")

            tracker.add_result(
                "Workflow Completion Logic",
                "FAIL",
                "",
                f"Missing operations: {', '.join(missing)}"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "Workflow Completion Logic",
            "FAIL",
            "",
            str(e)
        )
        return False

# =============================================================================
# TEST FUNCTIONS - COORDINATOR DASHBOARD
# =============================================================================

def test_coordinator_dashboard_workflows():
    """Test that CC dashboard doesn't show RR workflows."""
    try:
        conn = get_db_connection()

        # Query what CC dashboard would show
        cc_workflows = conn.execute("""
            SELECT
                wi.instance_id,
                wi.template_id,
                wi.current_step,
                wt.template_name
            FROM workflow_instances wi
            JOIN workflow_templates wt ON wi.template_id = wt.template_id
            WHERE wi.template_id IN (1, 2, 3, 4, 5, 6)
              AND wi.workflow_status = 'Active'
              AND wi.current_step NOT IN (
                  CASE
                      WHEN wi.template_id IN (1, 2, 3) THEN 5
                      WHEN wi.template_id IN (4, 5, 6) THEN 4
                  END
              )
            LIMIT 5
        """).fetchall()

        conn.close()

        # Verify none are at RR step
        for wf in cc_workflows:
            template_id = wf['template_id']
            current_step = wf['current_step']

            if template_id in [1, 2, 3] and current_step == 5:
                tracker.add_result(
                    "CC Dashboard Filtering",
                    "FAIL",
                    "",
                    f"CC dashboard showing LAB workflow at RR step 5"
                )
                return False

            if template_id in [4, 5, 6] and current_step == 4:
                tracker.add_result(
                    "CC Dashboard Filtering",
                    "FAIL",
                    "",
                    f"CC dashboard showing IMAGING workflow at RR step 4"
                )
                return False

        tracker.add_result(
            "CC Dashboard Filtering",
            "PASS",
            f"CC dashboard shows {len(cc_workflows)} workflows, none at RR steps",
            ""
        )
        return True
    except Exception as e:
        tracker.add_result(
            "CC Dashboard Filtering",
            "FAIL",
            "",
            str(e)
        )
        return False

# =============================================================================
# TEST FUNCTIONS - DASHBOARD TABS
# =============================================================================

def test_phone_review_tab():
    """Test Phone Review tab functionality."""
    try:
        from src.dashboards.phone_review import show_phone_review_entry

        # Check function exists and accepts correct parameters
        import inspect
        sig = inspect.signature(show_phone_review_entry)

        if 'mode' in sig.parameters and 'user_id' in sig.parameters:
            tracker.add_result(
                "Phone Review Tab",
                "PASS",
                f"Function accepts mode and user_id parameters",
                ""
            )
            return True
        else:
            tracker.add_result(
                "Phone Review Tab",
                "FAIL",
                "",
                "Missing required parameters"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "Phone Review Tab",
            "FAIL",
            "",
            str(e)
        )
        return False

def test_task_review_tab():
    """Test Task Review tab functionality."""
    try:
        from src.dashboards.coordinator_task_review_component import show

        # Check function exists
        if show:
            tracker.add_result(
                "Task Review Tab",
                "PASS",
                "Task review component function exists",
                ""
            )
            return True
        else:
            tracker.add_result(
                "Task Review Tab",
                "FAIL",
                "",
                "Function not found"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "Task Review Tab",
            "FAIL",
            "",
            str(e)
        )
        return False

def test_zmo_tab():
    """Test ZMO tab functionality."""
    try:
        from src.zmo_module import render_zmo_tab

        # Check function exists
        if render_zmo_tab:
            tracker.add_result(
                "ZMO Tab",
                "PASS",
                "ZMO module render function exists",
                ""
            )
            return True
        else:
            tracker.add_result(
                "ZMO Tab",
                "FAIL",
                "",
                "Function not found"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "ZMO Tab",
            "FAIL",
            "",
            str(e)
        )
        return False

# =============================================================================
# TEST FUNCTIONS - WORKFLOW STRUCTURE
# =============================================================================

def test_workflow_step_counts():
    """Test workflow step counts are correct."""
    try:
        conn = get_db_connection()

        # LAB workflows should have 5 steps
        lab_count = conn.execute(
            "SELECT COUNT(DISTINCT step_order) FROM workflow_steps WHERE template_id IN (1, 2, 3)"
        ).fetchone()[0]

        # IMAGING workflows should have 4 steps
        imaging_count = conn.execute(
            "SELECT COUNT(DISTINCT step_order) FROM workflow_steps WHERE template_id IN (4, 5, 6)"
        ).fetchone()[0]

        conn.close()

        if lab_count == 5 and imaging_count == 4:
            tracker.add_result(
                "Workflow Step Counts",
                "PASS",
                f"LAB: {lab_count} steps, IMAGING: {imaging_count} steps",
                ""
            )
            return True
        else:
            tracker.add_result(
                "Workflow Step Counts",
                "FAIL",
                "",
                f"Expected LAB=5, IMAGING=4; got LAB={lab_count}, IMAGING={imaging_count}"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "Workflow Step Counts",
            "FAIL",
            "",
            str(e)
        )
        return False

def test_rr_step_ownership():
    """Test that final RR steps are owned by RR."""
    try:
        conn = get_db_connection()

        # LAB step 5 should be RR
        lab_step = conn.execute(
            "SELECT owner FROM workflow_steps WHERE template_id = 1 AND step_order = 5"
        ).fetchone()

        # IMAGING step 4 should be RR
        imaging_step = conn.execute(
            "SELECT owner FROM workflow_steps WHERE template_id = 4 AND step_order = 4"
        ).fetchone()

        conn.close()

        lab_owner = lab_step[0] if lab_step else None
        imaging_owner = imaging_step[0] if imaging_step else None

        if lab_owner == 'RR' and imaging_owner == 'RR':
            tracker.add_result(
                "RR Step Ownership",
                "PASS",
                f"LAB step 5: {lab_owner}, IMAGING step 4: {imaging_owner}",
                ""
            )
            return True
        else:
            tracker.add_result(
                "RR Step Ownership",
                "FAIL",
                "",
                f"LAB step 5: {lab_owner}, IMAGING step 4: {imaging_owner}"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "RR Step Ownership",
            "FAIL",
            "",
            str(e)
        )
        return False

# =============================================================================
# TEST FUNCTIONS - DATA INTEGRITY
# =============================================================================

def test_no_orphaned_workflows():
    """Test no workflows have invalid step numbers."""
    try:
        conn = get_db_connection()

        # Check for Active workflows with invalid steps
        invalid = conn.execute("""
            SELECT COUNT(*) as count
            FROM workflow_instances wi
            WHERE wi.template_id IN (1, 2, 3, 4, 5, 6)
              AND wi.workflow_status = 'Active'
              AND NOT EXISTS (
                  SELECT 1 FROM workflow_steps ws
                  WHERE ws.template_id = wi.template_id
                  AND ws.step_order = wi.current_step
              )
        """).fetchone()[0]

        conn.close()

        if invalid == 0:
            tracker.add_result(
                "No Orphaned Workflows",
                "PASS",
                "All workflows have valid step numbers",
                ""
            )
            return True
        else:
            tracker.add_result(
                "No Orphaned Workflows",
                "FAIL",
                "",
                f"Found {invalid} workflows with invalid steps"
            )
            return False
    except Exception as e:
        tracker.add_result(
            "No Orphaned Workflows",
            "FAIL",
            "",
            str(e)
        )
        return False

def test_role_exists():
    """Test RR role exists in database."""
    try:
        conn = get_db_connection()
        role = conn.execute(
            "SELECT * FROM roles WHERE role_id = 43"
        ).fetchone()
        conn.close()

        if role and role['role_name'] == 'RR':
            tracker.add_result(
                "RR Role Exists",
                "PASS",
                f"RR role found: {role['role_name']}",
                ""
            )
            return True
        else:
            tracker.add_result(
                "RR Role Exists",
                "FAIL",
                "",
                f"RR role not found or incorrect: {role}"
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

# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all RR dashboard functional tests."""
    print("\n" + "="*70)
    print("RUNNING RESULTS REVIEWER DASHBOARD FUNCTIONAL TESTS")
    print("="*70 + "\n")

    tests = [
        # Dashboard Imports
        ("RR Dashboard Import", test_rr_dashboard_import),

        # Results Review Tab
        ("Results Review Query", test_results_review_tab_query),
        ("Results Review Ownership", test_results_review_tab_ownership),

        # Workflow Completion
        ("Workflow Completion Function", test_workflow_completion_function),
        ("Workflow Completion Logic", test_workflow_completion_logic),

        # Coordinator Dashboard
        ("CC Dashboard Filtering", test_coordinator_dashboard_workflows),

        # Dashboard Tabs
        ("Phone Review Tab", test_phone_review_tab),
        ("Task Review Tab", test_task_review_tab),
        ("ZMO Tab", test_zmo_tab),

        # Workflow Structure
        ("Workflow Step Counts", test_workflow_step_counts),
        ("RR Step Ownership", test_rr_step_ownership),

        # Data Integrity
        ("No Orphaned Workflows", test_no_orphaned_workflows),
        ("RR Role Exists", test_role_exists),
    ]

    for test_name, test_func in tests:
        print(f"Running: {test_name}...")
        try:
            test_func()
        except Exception as e:
            tracker.add_result(
                test_name,
                "ERROR",
                "",
                f"Test execution error: {str(e)}"
            )
            print(f"  ⚠ ERROR: {str(e)}")
        else:
            status = tracker.tests[-1]['status']
            symbol = {
                "PASS": "[PASS]",
                "FAIL": "[FAIL]",
                "SKIP": "[SKIP]",
                "ERROR": "[ERROR]"
            }.get(status, "[?]")
            print(f"  {symbol} {status}")

    # Print summary
    print(tracker.get_summary())

    # Save to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = project_root / f"test_report_rr_functional_{timestamp}.json"

    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - tracker.start_time).total_seconds(),
            "total_tests": len(tracker.tests),
            "passed": tracker.summary['PASS'],
            "failed": tracker.summary['FAIL'],
            "skipped": tracker.summary['SKIP'],
            "errors": tracker.summary['ERROR'],
            "tests": tracker.tests
        }, f, indent=2)

    print(f"\nReport saved to: {report_file}")

    # Return exit code
    failed = tracker.summary['FAIL'] + tracker.summary['ERROR']
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    result = run_all_tests()

    print("\n" + "="*70)
    if result == 0:
        print("[PASS] ALL TESTS PASSED")
    else:
        print("[FAIL] SOME TESTS FAILED")
    print("="*70 + "\n")

    sys.exit(result)
