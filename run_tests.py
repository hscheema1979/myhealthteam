#!/usr/bin/env python3
"""
Simple Test Runner for MyHealthTeam System

This script provides an easy way to run comprehensive testing with sensible defaults.
It serves as a simplified interface to the master test execution framework.

Usage:
    python run_tests.py                    # Run full test suite
    python run_tests.py --quick            # Run quick test (2 iterations)
    python run_tests.py --db-only          # Run database verification only
    python run_tests.py --workflows-only   # Run workflow tests only
    python run_tests.py --providers-only   # Run provider tests only

Author: Test Runner Framework
Created: 2024-12-19
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Print test runner banner"""
    print("🧪 MyHealthTeam Test Runner")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

def run_database_verification():
    """Run database verification only"""
    try:
        from database_verification_suite import DatabaseVerificationSuite
        
        print("🗄️ Running Database Verification...")
        verifier = DatabaseVerificationSuite()
        success = verifier.run_comprehensive_verification()
        
        if success:
            print("✅ Database verification completed successfully")
        else:
            print("❌ Database verification failed")
        
        return success
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def run_workflow_tests(iterations=5, quick=False):
    """Run workflow tests only"""
    try:
        from run_integration_tests import IntegrationTestRunner
        
        if quick:
            iterations = 2
        
        print(f"🔄 Running Workflow Tests ({iterations} iterations)...")
        runner = IntegrationTestRunner(
            iterations=iterations,
            username='test_user',
            password='test_password',
            verbose=True
        )
        
        success = runner.run_comprehensive_tests()
        
        if success:
            print("✅ Workflow tests completed successfully")
        else:
            print("❌ Workflow tests failed")
        
        return success
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Workflow tests failed: {e}")
        return False

def run_provider_tests(iterations=5, quick=False):
    """Run provider tests only"""
    try:
        from comprehensive_integration_test_suite import ComprehensiveIntegrationTester
        
        if quick:
            iterations = 2
        
        print(f"👨‍⚕️ Running Provider Tests ({iterations} iterations)...")
        
        test_suite = ComprehensiveIntegrationTester(
            test_email='test_user',
            test_password='test_password'
        )
        
        success_count = 0
        total_tests = 0
        
        # Test visit tasks
        print("  📋 Testing visit tasks...")
        for i in range(iterations):
            try:
                result = test_suite.test_provider_visit_task()
                if result:
                    success_count += 1
                total_tests += 1
            except Exception as e:
                print(f"    ❌ Visit task test {i+1} failed: {e}")
                total_tests += 1
        
        # Test phone reviews
        print("  📞 Testing phone reviews...")
        for i in range(iterations):
            try:
                result = test_suite.test_provider_phone_review()
                if result:
                    success_count += 1
                total_tests += 1
            except Exception as e:
                print(f"    ❌ Phone review test {i+1} failed: {e}")
                total_tests += 1
        
        # Test data validation
        print("  🔍 Testing data validation...")
        try:
            result = test_suite.validate_provider_data_consistency()
            if result:
                success_count += 1
            total_tests += 1
        except Exception as e:
            print(f"    ❌ Data validation failed: {e}")
            total_tests += 1
        
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate >= 80:
            print(f"✅ Provider tests completed successfully ({success_rate:.1f}% success rate)")
            return True
        else:
            print(f"❌ Provider tests failed ({success_rate:.1f}% success rate)")
            return False
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Provider tests failed: {e}")
        return False

def run_full_test_suite(iterations=5, quick=False):
    """Run complete test suite"""
    try:
        from master_test_execution import MasterTestExecutor
        
        if quick:
            iterations = 2
        
        config = {
            'iterations': iterations,
            'username': 'test_user',
            'password': 'test_password',
            'database': 'production.db',
            'output_dir': 'test_results',
            'verbose': True,
            'continue_on_failure': True,
            'quick_mode': quick
        }
        
        print(f"🚀 Running Full Test Suite ({iterations} iterations)...")
        executor = MasterTestExecutor(config)
        success = executor.run_comprehensive_testing()
        
        if success:
            print("✅ Full test suite completed successfully")
        else:
            print("❌ Full test suite completed with issues")
        
        return success
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Full test suite failed: {e}")
        return False

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Run MyHealthTeam tests")
    parser.add_argument('--quick', action='store_true', help='Run quick tests (2 iterations)')
    parser.add_argument('--iterations', type=int, default=5, help='Number of iterations (default: 5)')
    parser.add_argument('--db-only', action='store_true', help='Run database verification only')
    parser.add_argument('--workflows-only', action='store_true', help='Run workflow tests only')
    parser.add_argument('--providers-only', action='store_true', help='Run provider tests only')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Determine iterations
    iterations = 2 if args.quick else args.iterations
    
    success = False
    
    try:
        if args.db_only:
            success = run_database_verification()
        elif args.workflows_only:
            success = run_workflow_tests(iterations, args.quick)
        elif args.providers_only:
            success = run_provider_tests(iterations, args.quick)
        else:
            success = run_full_test_suite(iterations, args.quick)
        
        # Final summary
        print("\n" + "=" * 50)
        if success:
            print("🎉 Testing completed successfully!")
        else:
            print("⚠️ Testing completed with issues. Check logs for details.")
        print("=" * 50)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n❌ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Testing failed with exception: {e}")
        return 1

if __name__ == "__main__":
    exit(main())