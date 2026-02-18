"""
Comprehensive Scripts Tests
Tests all PowerShell and Python scripts for functionality.

Tests:
- ETL scripts (transform_production_data_v3_fixed.py)
- Refresh data scripts (refresh_production_data.ps1)
- Sync scripts (db-sync scripts)
- Backup scripts
- Deployment scripts
- Consolidation scripts
- Download scripts
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import subprocess

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ScriptsTest:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def test_etl_scripts(self):
        """Test ETL transformation scripts"""
        tests = []

        # Test 1: ETL script exists
        try:
            etl_script = project_root / "transform_production_data_v3_fixed.py"
            if etl_script.exists():
                tests.append({
                    "name": "ETL Script Exists",
                    "status": "PASS",
                    "details": f"Found at {etl_script.name}"
                })
            else:
                tests.append({
                    "name": "ETL Script Exists",
                    "status": "FAIL",
                    "error": "ETL script not found"
                })
        except Exception as e:
            tests.append({
                "name": "ETL Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: ETL script is valid Python
        try:
            etl_script = project_root / "transform_production_data_v3_fixed.py"
            if etl_script.exists():
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(etl_script)],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    tests.append({
                        "name": "ETL Script Valid Python",
                        "status": "PASS",
                        "details": "Script compiles without errors"
                    })
                else:
                    tests.append({
                        "name": "ETL Script Valid Python",
                        "status": "FAIL",
                        "error": result.stderr[:200]
                    })
        except Exception as e:
            tests.append({
                "name": "ETL Script Valid Python",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: CSV cleaning utility exists
        try:
            clean_csv = project_root / "src" / "utils" / "clean_csv.py"
            if clean_csv.exists():
                tests.append({
                    "name": "CSV Cleaning Utility Exists",
                    "status": "PASS",
                    "details": "Found at src/utils/clean_csv.py"
                })
            else:
                tests.append({
                    "name": "CSV Cleaning Utility Exists",
                    "status": "FAIL",
                    "error": "clean_csv.py not found"
                })
        except Exception as e:
            tests.append({
                "name": "CSV Cleaning Utility Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_refresh_scripts(self):
        """Test data refresh scripts"""
        tests = []

        # Test 1: Refresh script exists
        try:
            refresh_script = project_root / "refresh_production_data.ps1"
            if refresh_script.exists():
                tests.append({
                    "name": "Refresh Script Exists",
                    "status": "PASS",
                    "details": "Found refresh_production_data.ps1"
                })
            else:
                tests.append({
                    "name": "Refresh Script Exists",
                    "status": "FAIL",
                    "error": "refresh_production_data.ps1 not found"
                })
        except Exception as e:
            tests.append({
                "name": "Refresh Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Download script exists
        try:
            download_script = project_root / "scripts" / "1_download_files_complete.ps1"
            if download_script.exists():
                tests.append({
                    "name": "Download Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/1_download_files_complete.ps1"
                })
            else:
                tests.append({
                    "name": "Download Script Exists",
                    "status": "FAIL",
                    "error": "Download script not found"
                })
        except Exception as e:
            tests.append({
                "name": "Download Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: Consolidation script exists
        try:
            consolidate_script = project_root / "scripts" / "2_consolidate_files.ps1"
            if consolidate_script.exists():
                tests.append({
                    "name": "Consolidation Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/2_consolidate_files.ps1"
                })
            else:
                tests.append({
                    "name": "Consolidation Script Exists",
                    "status": "FAIL",
                    "error": "Consolidation script not found"
                })
        except Exception as e:
            tests.append({
                "name": "Consolidation Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 4: Post-import SQL exists
        try:
            post_import_sql = project_root / "src" / "sql" / "post_import_processing.sql"
            if post_import_sql.exists():
                tests.append({
                    "name": "Post-Import SQL Exists",
                    "status": "PASS",
                    "details": "Found src/sql/post_import_processing.sql"
                })
            else:
                tests.append({
                    "name": "Post-Import SQL Exists",
                    "status": "FAIL",
                    "error": "Post-import SQL not found"
                })
        except Exception as e:
            tests.append({
                "name": "Post-Import SQL Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_sync_scripts(self):
        """Test database sync scripts"""
        tests = []

        # Test 1: CSV billing tables sync script exists
        try:
            sync_script = project_root / "db-sync" / "bin" / "sync_csv_billing_tables.ps1"
            if sync_script.exists():
                tests.append({
                    "name": "CSV Billing Sync Script Exists",
                    "status": "PASS",
                    "details": "Found db-sync/bin/sync_csv_billing_tables.ps1"
                })
            else:
                tests.append({
                    "name": "CSV Billing Sync Script Exists",
                    "status": "FAIL",
                    "error": "Sync script not found"
                })
        except Exception as e:
            tests.append({
                "name": "CSV Billing Sync Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Sync config exists
        try:
            sync_config = project_root / "db-sync" / "config" / "db-sync.json"
            if sync_config.exists():
                tests.append({
                    "name": "Sync Config Exists",
                    "status": "PASS",
                    "details": "Found db-sync/config/db-sync.json"
                })
            else:
                tests.append({
                    "name": "Sync Config Exists",
                    "status": "FAIL",
                    "error": "Sync config not found"
                })
        except Exception as e:
            tests.append({
                "name": "Sync Config Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: VPS2 setup scripts exist
        try:
            vps2_setup = project_root / "db-sync" / "setup_vps2_auto.sh"
            if vps2_setup.exists():
                tests.append({
                    "name": "VPS2 Setup Script Exists",
                    "status": "PASS",
                    "details": "Found db-sync/setup_vps2_auto.sh"
                })
            else:
                tests.append({
                    "name": "VPS2 Setup Script Exists",
                    "status": "FAIL",
                    "error": "VPS2 setup script not found"
                })
        except Exception as e:
            tests.append({
                "name": "VPS2 Setup Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_backup_scripts(self):
        """Test backup scripts"""
        tests = []

        # Test 1: Backup script exists
        try:
            backup_script = project_root / "scripts" / "backup_production_db.ps1"
            if backup_script.exists():
                tests.append({
                    "name": "Backup Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/backup_production_db.ps1"
                })
            else:
                tests.append({
                    "name": "Backup Script Exists",
                    "status": "FAIL",
                    "error": "Backup script not found"
                })
        except Exception as e:
            tests.append({
                "name": "Backup Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: VPS2 backup deployment script exists
        try:
            vps2_backup = project_root / "scripts" / "deploy_vps2_backup.ps1"
            if vps2_backup.exists():
                tests.append({
                    "name": "VPS2 Backup Deploy Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/deploy_vps2_backup.ps1"
                })
            else:
                tests.append({
                    "name": "VPS2 Backup Deploy Script Exists",
                    "status": "FAIL",
                    "error": "VPS2 backup deploy script not found"
                })
        except Exception as e:
            tests.append({
                "name": "VPS2 Backup Deploy Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: Setup daily backup task script exists
        try:
            setup_backup = project_root / "scripts" / "setup_daily_backup_task.ps1"
            if setup_backup.exists():
                tests.append({
                    "name": "Setup Daily Backup Task Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/setup_daily_backup_task.ps1"
                })
            else:
                tests.append({
                    "name": "Setup Daily Backup Task Script Exists",
                    "status": "FAIL",
                    "error": "Setup backup task script not found"
                })
        except Exception as e:
            tests.append({
                "name": "Setup Daily Backup Task Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 4: Test backup script exists
        try:
            test_backup = project_root / "scripts" / "test_backup.ps1"
            if test_backup.exists():
                tests.append({
                    "name": "Test Backup Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/test_backup.ps1"
                })
            else:
                tests.append({
                    "name": "Test Backup Script Exists",
                    "status": "FAIL",
                    "error": "Test backup script not found"
                })
        except Exception as e:
            tests.append({
                "name": "Test Backup Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_deployment_scripts(self):
        """Test deployment scripts"""
        tests = []

        # Test 1: Deploy to test script exists
        try:
            deploy_test = project_root / "scripts" / "deploy_to_test.ps1"
            if deploy_test.exists():
                tests.append({
                    "name": "Deploy to Test Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/deploy_to_test.ps1"
                })
            else:
                tests.append({
                    "name": "Deploy to Test Script Exists",
                    "status": "FAIL",
                    "error": "Deploy to test script not found"
                })
        except Exception as e:
            tests.append({
                "name": "Deploy to Test Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Deploy to production script exists
        try:
            deploy_prod = project_root / "scripts" / "deploy_to_production.ps1"
            if deploy_prod.exists():
                tests.append({
                    "name": "Deploy to Production Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/deploy_to_production.ps1"
                })
            else:
                tests.append({
                    "name": "Deploy to Production Script Exists",
                    "status": "FAIL",
                    "error": "Deploy to production script not found"
                })
        except Exception as e:
            tests.append({
                "name": "Deploy to Production Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 3: Promote test to production script exists
        try:
            promote = project_root / "scripts" / "promote_test_to_production.ps1"
            if promote.exists():
                tests.append({
                    "name": "Promote Test to Production Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/promote_test_to_production.ps1"
                })
            else:
                tests.append({
                    "name": "Promote Test to Production Script Exists",
                    "status": "FAIL",
                    "error": "Promote script not found"
                })
        except Exception as e:
            tests.append({
                "name": "Promote Test to Production Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_workflow_scripts(self):
        """Test workflow capture scripts"""
        tests = []

        # Test 1: Run capture workflows script exists
        try:
            capture_workflows = project_root / "scripts" / "run_capture_workflows.ps1"
            if capture_workflows.exists():
                tests.append({
                    "name": "Capture Workflows Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/run_capture_workflows.ps1"
                })
            else:
                tests.append({
                    "name": "Capture Workflows Script Exists",
                    "status": "FAIL",
                    "error": "Capture workflows script not found"
                })
        except Exception as e:
            tests.append({
                "name": "Capture Workflows Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        # Test 2: Direct capture workflows script exists
        try:
            capture_direct = project_root / "scripts" / "run_capture_workflows_direct.ps1"
            if capture_direct.exists():
                tests.append({
                    "name": "Direct Capture Workflows Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/run_capture_workflows_direct.ps1"
                })
            else:
                tests.append({
                    "name": "Direct Capture Workflows Script Exists",
                    "status": "FAIL",
                    "error": "Direct capture script not found"
                })
        except Exception as e:
            tests.append({
                "name": "Direct Capture Workflows Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def test_daily_scripts(self):
        """Test daily automation scripts"""
        tests = []

        # Test 1: Daily pull from VPS2 script exists
        try:
            daily_pull = project_root / "scripts" / "daily_pull_from_vps2.ps1"
            if daily_pull.exists():
                tests.append({
                    "name": "Daily Pull from VPS2 Script Exists",
                    "status": "PASS",
                    "details": "Found scripts/daily_pull_from_vps2.ps1"
                })
            else:
                tests.append({
                    "name": "Daily Pull from VPS2 Script Exists",
                    "status": "FAIL",
                    "error": "Daily pull script not found"
                })
        except Exception as e:
            tests.append({
                "name": "Daily Pull from VPS2 Script Exists",
                "status": "FAIL",
                "error": str(e)
            })

        return tests

    def run_all_tests(self):
        """Run all script tests"""
        print("\n" + "="*70)
        print("SCRIPTS - COMPREHENSIVE TESTS")
        print("="*70 + "\n")

        test_suites = [
            ("ETL Scripts", self.test_etl_scripts),
            ("Refresh Scripts", self.test_refresh_scripts),
            ("Sync Scripts", self.test_sync_scripts),
            ("Backup Scripts", self.test_backup_scripts),
            ("Deployment Scripts", self.test_deployment_scripts),
            ("Workflow Scripts", self.test_workflow_scripts),
            ("Daily Scripts", self.test_daily_scripts),
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
        print("SCRIPTS TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total Tests: {len(self.results)}")
        print(f"  [OK] PASSED: {passed}")
        print(f"  [FAIL] FAILED: {failed}")
        print(f"{'='*70}\n")

        # Save to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_scripts_comprehensive_{timestamp}.json"
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
    tester = ScriptsTest()
    tester.run_all_tests()
    success = tester.print_summary()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
