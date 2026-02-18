"""
Comprehensive Test Runner for MyHealthTeam Application
Runs all dashboard, script, and database tests using Streamlit AppTest framework.

Usage:
    python tests/test_runner.py                    # Run all tests
    python tests/test_runner.py --dashboard        # Run dashboard tests only
    python tests/test_runner.py --script          # Run script tests only
    python tests/test_runner.py --database        # Run database tests only
    python tests/test_runner.py --admin           # Run specific test suite
"""

import sys
import os
from pathlib import Path
import subprocess
import json
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

TEST_DIR = project_root / "tests"
REPORT_DIR = project_root / "test_reports"
REPORT_DIR.mkdir(exist_ok=True)

# Test categories and their test files
TEST_SUITES = {
    "admin": {
        "name": "Admin Dashboard Tests",
        "tests": [
            "test_admin_facility_apptest.py",
            "test_admin_patient_info_apptest.py",
            "test_admin_user_roles_apptest.py",
        ]
    },
    "coordinator": {
        "name": "Coordinator Dashboard Tests",
        "tests": [
            "test_coordinator_dashboard_apptest.py",
            "test_coordinator_tasks_apptest.py",
            "test_coordinator_billing_apptest.py",
        ]
    },
    "provider": {
        "name": "Provider Dashboard Tests",
        "tests": [
            "test_provider_dashboard_apptest.py",
            "test_provider_tasks_apptest.py",
            "test_provider_billing_apptest.py",
        ]
    },
    "onboarding": {
        "name": "Onboarding Dashboard Tests",
        "tests": [
            "test_onboarding_dashboard_apptest.py",
            "test_phone_review_apptest.py",
        ]
    },
    "workflow": {
        "name": "Workflow System Tests",
        "tests": [
            "test_workflow_system_apptest.py",
            "test_workflow_templates_apptest.py",
        ]
    },
    "facility": {
        "name": "Facility Management Tests",
        "tests": [
            "test_facility_dashboard_apptest.py",
            "test_facility_intake_apptest.py",
        ]
    },
    "zmo": {
        "name": "ZMO Module Tests",
        "tests": [
            "test_zmo_module_apptest.py",
            "test_zmo_editing_apptest.py",
        ]
    },
    "database": {
        "name": "Database Operations Tests",
        "tests": [
            "test_database_connections_apptest.py",
            "test_database_queries_apptest.py",
            "test_database_etl_apptest.py",
        ]
    },
    "scripts": {
        "name": "Script Tests",
        "tests": [
            "test_etl_scripts_apptest.py",
            "test_sync_scripts_apptest.py",
            "test_backup_scripts_apptest.py",
        ]
    }
}

ALL_TESTS = []
for suite_name, suite_info in TEST_SUITES.items():
    for test_file in suite_info["tests"]:
        ALL_TESTS.append((suite_name, test_file))

# =============================================================================
# TEST RUNNER
# =============================================================================

class TestRunner:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self.total_tests = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def run_test(self, test_file: str, suite_name: str = ""):
        """Run a single test file"""
        test_path = TEST_DIR / test_file

        if not test_path.exists():
            result = {
                "suite": suite_name,
                "test_file": test_file,
                "status": "SKIPPED",
                "message": "Test file not found",
                "duration": 0,
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            self.skipped += 1
            return result

        try:
            start = datetime.now()
            result = subprocess.run(
                [sys.executable, str(test_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(project_root)
            )
            duration = (datetime.now() - start).total_seconds()

            if result.returncode == 0:
                status = "PASS"
                message = "Test passed"
            else:
                status = "FAIL"
                message = result.stderr or result.stdout or "Unknown error"

            test_result = {
                "suite": suite_name,
                "test_file": test_file,
                "status": status,
                "message": message,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(test_result)
            self.total_tests += 1

            if status == "PASS":
                self.passed += 1
            elif status == "FAIL":
                self.failed += 1
            else:
                self.skipped += 1

            return test_result

        except subprocess.TimeoutExpired:
            test_result = {
                "suite": suite_name,
                "test_file": test_file,
                "status": "TIMEOUT",
                "message": "Test exceeded 5 minute timeout",
                "duration": 300,
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(test_result)
            self.failed += 1
            return test_result

        except Exception as e:
            test_result = {
                "suite": suite_name,
                "test_file": test_file,
                "status": "ERROR",
                "message": str(e),
                "duration": 0,
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(test_result)
            self.failed += 1
            return test_result

    def run_suite(self, suite_name: str):
        """Run all tests in a suite"""
        suite = TEST_SUITES.get(suite_name)
        if not suite:
            print(f"Unknown test suite: {suite_name}")
            return

        print(f"\n{'='*70}")
        print(f"Running: {suite['name']}")
        print(f"{'='*70}\n")

        for test_file in suite["tests"]:
            result = self.run_test(test_file, suite_name)
            symbol = "✓" if result["status"] == "PASS" else "✗" if result["status"] == "FAIL" else "○"
            print(f"{symbol} {test_file}: {result['status']} ({result['duration']:.2f}s)")

    def run_all(self):
        """Run all test suites"""
        print(f"\n{'='*70}")
        print("COMPREHENSIVE TEST SUITE - MyHealthTeam")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        for suite_name in TEST_SUITES.keys():
            self.run_suite(suite_name)

    def print_summary(self):
        """Print test summary"""
        duration = (datetime.now() - self.start_time).total_seconds()

        print(f"\n{'='*70}")
        print("TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total Tests: {self.total_tests}")
        print(f"  ✓ PASSED: {self.passed}")
        print(f"  ✗ FAILED: {self.failed}")
        print(f"  ○ SKIPPED: {self.skipped}")

        # Print failures
        if self.failed > 0:
            print(f"\n{'='*70}")
            print("FAILED TESTS:")
            print(f"{'='*70}")
            for result in self.results:
                if result["status"] in ["FAIL", "ERROR", "TIMEOUT"]:
                    print(f"\n✗ {result['test_file']}")
                    print(f"  Suite: {result['suite']}")
                    print(f"  Error: {result['message'][:200]}")

        print(f"\n{'='*70}\n")

    def save_report(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = REPORT_DIR / f"test_report_comprehensive_{timestamp}.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "summary": {
                "total": self.total_tests,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped
            },
            "results": self.results
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Test report saved to: {filename}")
        return filename

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Run MyHealthTeam test suite")
    parser.add_argument(
        "--suite",
        choices=list(TEST_SUITES.keys()) + ["all"],
        default="all",
        help="Test suite to run (default: all)"
    )
    parser.add_argument(
        "--test",
        help="Run specific test file"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate JSON test report"
    )

    args = parser.parse_args()

    runner = TestRunner()

    if args.test:
        # Run specific test
        result = runner.run_test(args.test)
        print(f"\n{result['test_file']}: {result['status']}")
    elif args.suite == "all":
        # Run all tests
        runner.run_all()
    else:
        # Run specific suite
        runner.run_suite(args.suite)

    runner.print_summary()

    if args.report:
        runner.save_report()

    # Exit with error code if tests failed
    sys.exit(0 if runner.failed == 0 else 1)

if __name__ == "__main__":
    main()
