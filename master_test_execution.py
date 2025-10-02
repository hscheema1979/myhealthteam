#!/usr/bin/env python3
"""
Master Test Execution Script for MyHealthTeam System

This script orchestrates comprehensive testing of all system components including:
- Workflow template testing (all 14 templates, 5 iterations each)
- Provider functionality testing (Visit Tasks, phone reviews)
- Database verification and consistency checks
- Data synchronization validation

Features:
- Coordinated test execution
- Progress tracking across all test suites
- Comprehensive reporting
- Error handling and recovery
- Performance monitoring

Author: Master Test Framework
Created: 2024-12-19
"""

import sys
import os
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from comprehensive_integration_test_suite import ComprehensiveIntegrationTester
    from run_integration_tests import IntegrationTestRunner
    from database_verification_suite import DatabaseVerificationSuite
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all test suite files are in the same directory")
    sys.exit(1)

class MasterTestExecutor:
    """Master test execution coordinator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.start_time = datetime.now()
        self.test_results = {
            'execution_info': {
                'start_time': self.start_time.isoformat(),
                'config': config
            },
            'workflow_tests': {},
            'provider_tests': {},
            'database_verification': {},
            'summary': {}
        }
        
        # Create output directory
        self.output_dir = Path(config.get('output_dir', 'test_results'))
        self.output_dir.mkdir(exist_ok=True)
        
        print("🚀 Master Test Execution Framework")
        print("=" * 60)
        print(f"📁 Output Directory: {self.output_dir}")
        print(f"🔄 Iterations per test: {config.get('iterations', 5)}")
        print(f"🗄️ Database: {config.get('database', 'production.db')}")
        print("=" * 60)
    
    def log_phase(self, phase: str, status: str, details: Dict = None):
        """Log test phase results"""
        timestamp = datetime.now().isoformat()
        
        status_icon = {
            'STARTED': '🟡',
            'COMPLETED': '✅',
            'FAILED': '❌',
            'SKIPPED': '⏭️'
        }.get(status, '📝')
        
        print(f"\n{status_icon} {phase}: {status}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
        
        # Store in results
        if phase not in self.test_results:
            self.test_results[phase] = {}
        
        self.test_results[phase]['status'] = status
        self.test_results[phase]['timestamp'] = timestamp
        self.test_results[phase]['details'] = details or {}
    
    def run_database_verification(self) -> bool:
        """Run comprehensive database verification"""
        self.log_phase("Database Verification", "STARTED")
        
        try:
            verifier = DatabaseVerificationSuite(self.config.get('database', 'production.db'))
            success = verifier.run_comprehensive_verification()
            
            # Store results
            self.test_results['database_verification'] = verifier.verification_results
            
            if success:
                self.log_phase("Database Verification", "COMPLETED", 
                             {'verification_passed': True})
                return True
            else:
                self.log_phase("Database Verification", "FAILED", 
                             {'verification_passed': False})
                return False
                
        except Exception as e:
            self.log_phase("Database Verification", "FAILED", 
                         {'error': str(e)})
            return False
    
    def run_workflow_tests(self) -> bool:
        """Run comprehensive workflow testing"""
        self.log_phase("Workflow Testing", "STARTED")
        
        try:
            # Create args object for integration test runner
            class Args:
                def __init__(self, config, output_dir):
                    self.iterations = config.get('iterations', 5)
                    self.user = config.get('username', 'test_user')
                    self.password = config.get('password', 'test_password')
                    self.output = str(output_dir)
                    self.verbose = config.get('verbose', True)
            
            args = Args(self.config, self.output_dir)
            runner = IntegrationTestRunner(args)
            
            # Run workflow tests
            success = runner.run_comprehensive_tests()
            
            # Store results
            self.test_results['workflow_tests'] = runner.test_results
            
            if success:
                total_tests = sum(len(results) for results in runner.test_results.values())
                self.log_phase("Workflow Testing", "COMPLETED", 
                             {'total_tests_run': total_tests, 'success': True})
                return True
            else:
                self.log_phase("Workflow Testing", "FAILED", 
                             {'success': False})
                return False
                
        except Exception as e:
            self.log_phase("Workflow Testing", "FAILED", 
                         {'error': str(e)})
            return False
    
    def run_provider_tests(self) -> bool:
        """Run provider-specific testing"""
        self.log_phase("Provider Testing", "STARTED")
        
        try:
            # Create comprehensive test suite for provider testing
            test_suite = ComprehensiveIntegrationTester(
                test_email=self.config.get('username', 'test_user'),
                test_password=self.config.get('password', 'test_password')
            )
            
            provider_results = {
                'visit_tasks': [],
                'phone_reviews': [],
                'data_validation': []
            }
            
            # Test provider visit tasks
            print("\n📋 Testing Provider Visit Tasks...")
            for i in range(self.config.get('iterations', 5)):
                print(f"  Iteration {i+1}/{self.config.get('iterations', 5)}")
                
                try:
                    # Test visit task creation and completion
                    result = test_suite.test_provider_visit_task()
                    provider_results['visit_tasks'].append({
                        'iteration': i + 1,
                        'timestamp': datetime.now().isoformat(),
                        'success': result,
                        'details': 'Visit task test completed'
                    })
                    
                    time.sleep(1)  # Brief pause between iterations
                    
                except Exception as e:
                    provider_results['visit_tasks'].append({
                        'iteration': i + 1,
                        'timestamp': datetime.now().isoformat(),
                        'success': False,
                        'error': str(e)
                    })
            
            # Test provider phone reviews
            print("\n📞 Testing Provider Phone Reviews...")
            for i in range(self.config.get('iterations', 5)):
                print(f"  Iteration {i+1}/{self.config.get('iterations', 5)}")
                
                try:
                    # Test phone review functionality
                    result = test_suite.test_provider_phone_review()
                    provider_results['phone_reviews'].append({
                        'iteration': i + 1,
                        'timestamp': datetime.now().isoformat(),
                        'success': result,
                        'details': 'Phone review test completed'
                    })
                    
                    time.sleep(1)  # Brief pause between iterations
                    
                except Exception as e:
                    provider_results['phone_reviews'].append({
                        'iteration': i + 1,
                        'timestamp': datetime.now().isoformat(),
                        'success': False,
                        'error': str(e)
                    })
            
            # Test data validation
            print("\n🔍 Testing Provider Data Validation...")
            try:
                validation_result = test_suite.validate_provider_data_consistency()
                provider_results['data_validation'].append({
                    'timestamp': datetime.now().isoformat(),
                    'success': validation_result,
                    'details': 'Provider data validation completed'
                })
            except Exception as e:
                provider_results['data_validation'].append({
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                })
            
            # Store results
            self.test_results['provider_tests'] = provider_results
            
            # Calculate success rate
            all_tests = (provider_results['visit_tasks'] + 
                        provider_results['phone_reviews'] + 
                        provider_results['data_validation'])
            
            successful_tests = len([t for t in all_tests if t.get('success', False)])
            total_tests = len(all_tests)
            success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
            
            if success_rate >= 80:  # 80% success threshold
                self.log_phase("Provider Testing", "COMPLETED", 
                             {'total_tests': total_tests, 'successful': successful_tests, 
                              'success_rate': f"{success_rate:.1f}%"})
                return True
            else:
                self.log_phase("Provider Testing", "FAILED", 
                             {'total_tests': total_tests, 'successful': successful_tests, 
                              'success_rate': f"{success_rate:.1f}%"})
                return False
                
        except Exception as e:
            self.log_phase("Provider Testing", "FAILED", 
                         {'error': str(e)})
            return False
    
    def generate_master_report(self) -> str:
        """Generate comprehensive master test report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        report = f"""
# Master Test Execution Report
Generated: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {str(duration).split('.')[0]}
Configuration: {json.dumps(self.config, indent=2)}

## Executive Summary
"""
        
        # Calculate overall statistics
        phases = ['Database Verification', 'Workflow Testing', 'Provider Testing']
        completed_phases = 0
        failed_phases = 0
        
        for phase in phases:
            phase_key = phase.lower().replace(' ', '_')
            if phase_key in self.test_results:
                status = self.test_results[phase_key].get('status', 'UNKNOWN')
                if status == 'COMPLETED':
                    completed_phases += 1
                elif status == 'FAILED':
                    failed_phases += 1
        
        overall_success_rate = (completed_phases / len(phases) * 100) if phases else 0
        
        report += f"""
- Total Test Phases: {len(phases)}
- Completed Successfully: {completed_phases}
- Failed: {failed_phases}
- Overall Success Rate: {overall_success_rate:.1f}%
- Test Duration: {str(duration).split('.')[0]}
"""
        
        # Database Verification Summary
        if 'database_verification' in self.test_results:
            db_results = self.test_results['database_verification']
            report += f"""
## Database Verification Results
"""
            for category, results in db_results.items():
                if results and isinstance(results, list):
                    total = len(results)
                    passed = len([r for r in results if r.get('status') == 'PASS'])
                    failed = len([r for r in results if r.get('status') == 'FAIL'])
                    
                    report += f"""
### {category.replace('_', ' ').title()}
- Total: {total}
- Passed: {passed}
- Failed: {failed}
- Success Rate: {(passed/total*100):.1f}%
"""
        
        # Workflow Testing Summary
        if 'workflow_tests' in self.test_results:
            workflow_results = self.test_results['workflow_tests']
            report += f"""
## Workflow Testing Results
"""
            for test_type, results in workflow_results.items():
                if results and isinstance(results, list):
                    total = len(results)
                    successful = len([r for r in results if r.get('success', False)])
                    
                    report += f"""
### {test_type.replace('_', ' ').title()}
- Total Tests: {total}
- Successful: {successful}
- Success Rate: {(successful/total*100):.1f}%
"""
        
        # Provider Testing Summary
        if 'provider_tests' in self.test_results:
            provider_results = self.test_results['provider_tests']
            report += f"""
## Provider Testing Results
"""
            for test_type, results in provider_results.items():
                if results and isinstance(results, list):
                    total = len(results)
                    successful = len([r for r in results if r.get('success', False)])
                    
                    report += f"""
### {test_type.replace('_', ' ').title()}
- Total Tests: {total}
- Successful: {successful}
- Success Rate: {(successful/total*100):.1f}%
"""
        
        # Recommendations
        report += f"""
## Recommendations

Based on the test results:
"""
        
        if overall_success_rate >= 90:
            report += "✅ System is performing excellently. All major components are functioning correctly.\n"
        elif overall_success_rate >= 75:
            report += "⚠️ System is performing well but some issues were identified. Review failed tests.\n"
        else:
            report += "❌ System has significant issues. Immediate attention required for failed components.\n"
        
        if failed_phases > 0:
            report += f"🔧 {failed_phases} test phase(s) failed. Review detailed logs for specific issues.\n"
        
        report += """
## Next Steps
1. Review detailed test logs for any failed tests
2. Address identified issues based on priority
3. Re-run tests after fixes are implemented
4. Update documentation based on test findings
"""
        
        return report
    
    def save_master_results(self):
        """Save comprehensive test results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON results
        json_file = self.output_dir / f"master_test_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        # Save master report
        report = self.generate_master_report()
        report_file = self.output_dir / f"master_test_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Save summary CSV
        csv_file = self.output_dir / f"master_test_summary_{timestamp}.csv"
        with open(csv_file, 'w') as f:
            f.write("Phase,Status,Details\n")
            for phase, data in self.test_results.items():
                if isinstance(data, dict) and 'status' in data:
                    status = data['status']
                    details = str(data.get('details', {})).replace(',', ';')
                    f.write(f"{phase},{status},{details}\n")
        
        print(f"\n📁 Master test results saved:")
        print(f"   📋 JSON: {json_file}")
        print(f"   📄 Report: {report_file}")
        print(f"   📊 CSV: {csv_file}")
    
    def run_comprehensive_testing(self) -> bool:
        """Run comprehensive testing of all system components"""
        try:
            print(f"🕐 Test execution started at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Phase 1: Database Verification
            print(f"\n{'='*20} PHASE 1: DATABASE VERIFICATION {'='*20}")
            db_success = self.run_database_verification()
            
            if not db_success and not self.config.get('continue_on_failure', True):
                print("❌ Database verification failed. Stopping execution.")
                return False
            
            # Phase 2: Workflow Testing
            print(f"\n{'='*20} PHASE 2: WORKFLOW TESTING {'='*20}")
            workflow_success = self.run_workflow_tests()
            
            if not workflow_success and not self.config.get('continue_on_failure', True):
                print("❌ Workflow testing failed. Stopping execution.")
                return False
            
            # Phase 3: Provider Testing
            print(f"\n{'='*20} PHASE 3: PROVIDER TESTING {'='*20}")
            provider_success = self.run_provider_tests()
            
            # Generate final results
            self.save_master_results()
            
            # Final summary
            end_time = datetime.now()
            duration = end_time - self.start_time
            
            overall_success = db_success and workflow_success and provider_success
            
            print(f"\n{'='*60}")
            print(f"🏁 Master Test Execution {'COMPLETED' if overall_success else 'COMPLETED WITH ISSUES'}")
            print(f"⏱️ Total Duration: {str(duration).split('.')[0]}")
            print(f"🗄️ Database Verification: {'✅' if db_success else '❌'}")
            print(f"🔄 Workflow Testing: {'✅' if workflow_success else '❌'}")
            print(f"👨‍⚕️ Provider Testing: {'✅' if provider_success else '❌'}")
            print(f"📁 Results saved to: {self.output_dir}")
            print(f"{'='*60}")
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Master test execution failed with exception: {str(e)}")
            self.log_phase("Master Execution", "FAILED", {'error': str(e)})
            return False

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Run comprehensive system testing")
    parser.add_argument('--iterations', type=int, default=5, help='Number of iterations per test')
    parser.add_argument('--username', default='test_user', help='Test username')
    parser.add_argument('--password', default='test_password', help='Test password')
    parser.add_argument('--database', default='production.db', help='Database file path')
    parser.add_argument('--output', default='test_results', help='Output directory')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--continue-on-failure', action='store_true', 
                       help='Continue testing even if a phase fails')
    parser.add_argument('--quick', action='store_true', help='Run quick test mode (fewer iterations)')
    
    args = parser.parse_args()
    
    # Adjust iterations for quick mode
    if args.quick:
        args.iterations = 2
    
    config = {
        'iterations': args.iterations,
        'username': args.username,
        'password': args.password,
        'database': args.database,
        'output_dir': args.output,
        'verbose': args.verbose,
        'continue_on_failure': args.continue_on_failure,
        'quick_mode': args.quick
    }
    
    executor = MasterTestExecutor(config)
    success = executor.run_comprehensive_testing()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())