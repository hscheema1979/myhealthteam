"""
Runtime Error Detection Script

Tests all dashboard modules for import errors and runtime issues.
This catches errors that only occur when modules are actually imported.
"""

import sys
import os
from pathlib import Path
import traceback
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class RuntimeTester:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def test_module_import(self, module_path, module_name):
        """Test if a module can be imported without errors"""
        print(f"\n[TEST] Importing {module_name}...")
        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                self.failed.append({
                    "module": module_name,
                    "error": "Could not create module spec"
                })
                print(f"  [FAIL] Could not create spec for {module_name}")
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            self.passed.append({"module": module_name})
            print(f"  [PASS] {module_name} imported successfully")
            return True

        except ImportError as e:
            self.failed.append({
                "module": module_name,
                "error": f"ImportError: {str(e)}"
            })
            print(f"  [FAIL] ImportError in {module_name}")
            print(f"         {str(e)}")
            return False

        except Exception as e:
            self.failed.append({
                "module": module_name,
                "error": f"{type(e).__name__}: {str(e)}"
            })
            print(f"  [FAIL] {type(e).__name__} in {module_name}")
            print(f"         {str(e)}")
            return False

    def test_zmo_assignments_import(self):
        """Specifically test the ZMO assignments tab that had logger errors"""
        print("\n[TEST] ZMO Assignments Tab Import (checking for logger error)...")
        try:
            from src.zmo_assignments_tab import _render_patient_assignments_tab
            print("  [PASS] ZMO assignments tab imported (no logger error)")
            self.passed.append({"module": "zmo_assignments_tab"})
            return True
        except ImportError as e:
            if "logger" in str(e):
                print(f"  [FAIL] Logger import error: {str(e)}")
                self.failed.append({
                    "module": "zmo_assignments_tab",
                    "error": str(e)
                })
                return False
            else:
                print(f"  [FAIL] Other import error: {str(e)}")
                self.failed.append({
                    "module": "zmo_assignments_tab",
                    "error": str(e)
                })
                return False
        except Exception as e:
            print(f"  [FAIL] {type(e).__name__}: {str(e)}")
            self.failed.append({
                "module": "zmo_assignments_tab",
                "error": f"{type(e).__name__}: {str(e)}"
            })
            return False

    def test_rr_dashboard_import(self):
        """Test RR dashboard import"""
        print("\n[TEST] RR Dashboard Import...")
        try:
            from src.dashboards import results_reviewer_dashboard
            print("  [PASS] RR dashboard imported successfully")
            self.passed.append({"module": "results_reviewer_dashboard"})
            return True
        except Exception as e:
            print(f"  [FAIL] {type(e).__name__}: {str(e)}")
            self.failed.append({
                "module": "results_reviewer_dashboard",
                "error": f"{type(e).__name__}: {str(e)}"
            })
            return False

    def test_all_dashboard_modules(self):
        """Test all dashboard modules"""
        dashboards = [
            ("src/dashboards/admin_dashboard.py", "admin_dashboard"),
            ("src/dashboards/care_coordinator_dashboard_enhanced.py", "care_coordinator_dashboard"),
            ("src/dashboards/care_provider_dashboard_enhanced.py", "care_provider_dashboard"),
            ("src/dashboards/results_reviewer_dashboard.py", "results_reviewer_dashboard"),
            ("src/dashboards/onboarding_dashboard.py", "onboarding_dashboard"),
            ("src/dashboards/data_entry_dashboard.py", "data_entry_dashboard"),
            ("src/dashboards/lead_coordinator_dashboard.py", "lead_coordinator_dashboard"),
            ("src/dashboards/coordinator_manager_dashboard.py", "coordinator_manager_dashboard"),
        ]

        for dash_path, dash_name in dashboards:
            full_path = project_root / dash_path
            if full_path.exists():
                self.test_module_import(str(full_path), dash_name)
            else:
                print(f"\n[SKIP] {dash_name} - file not found")
                self.warnings.append({"module": dash_name, "error": "File not found"})

    def run_all_tests(self):
        """Run all runtime error tests"""
        print("=" * 70)
        print("RUNTIME ERROR DETECTION")
        print("=" * 70)

        # Critical tests
        self.test_zmo_assignments_import()
        self.test_rr_dashboard_import()

        # All dashboards
        self.test_all_dashboard_modules()

        # Summary
        print("\n" + "=" * 70)
        print("RUNTIME ERROR SUMMARY")
        print("=" * 70)
        print(f"\nPassed: {len(self.passed)}")
        print(f"Failed: {len(self.failed)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.failed:
            print("\n[FAILED] Modules with errors:")
            for fail in self.failed:
                print(f"  - {fail['module']}: {fail['error']}")

        if self.warnings:
            print("\n[WARNINGS] Modules with warnings:")
            for warn in self.warnings:
                print(f"  - {warn['module']}: {warn['error']}")

        if not self.failed:
            print("\n[PASS] No runtime errors detected!")
            return True
        else:
            print("\n[FAIL] Runtime errors detected - must fix before deployment")
            return False


if __name__ == "__main__":
    tester = RuntimeTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
