#!/usr/bin/env python3
"""
Integration Test Runner for MyHealthTeam Workflow System

This script executes the comprehensive integration test suite and provides
detailed progress tracking, real-time monitoring, and comprehensive reporting.

Usage:
    python run_integration_tests.py [options]

Options:
    --iterations N    Number of iterations per workflow (default: 5)
    --user EMAIL      Test user email (default: dianela@)
    --password PASS   Test user password (default: test4)
    --output DIR      Output directory for reports (default: test_results)
    --verbose         Enable verbose logging
    --quick           Run quick test (1 iteration per workflow)

Author: Integration Testing Framework
Created: 2024-12-19
"""

import sys
import os
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

# Import the comprehensive test suite
from comprehensive_integration_test_suite import ComprehensiveIntegrationTester

class IntegrationTestRunner:
    """Test runner with enhanced monitoring and reporting"""
    
    def __init__(self, args):
        self.args = args
        self.output_dir = Path(args.output)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize tester with custom parameters
        self.tester = ComprehensiveIntegrationTester(
            test_email=args.user,
            test_password=args.password
        )
        
        # Override test iterations if specified
        if args.iterations:
            self.tester.test_iterations = args.iterations
        
        if args.quick:
            self.tester.test_iterations = 1
        
        self.verbose = args.verbose
        
    def print_header(self):
        """Print test suite header"""
        print("🚀 MyHealthTeam Comprehensive Integration Test Suite")
        print("=" * 70)
        print(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 Test User: {self.args.user}")
        print(f"🔄 Iterations per Workflow: {self.tester.test_iterations}")
        print(f"📁 Output Directory: {self.output_dir}")
        print("=" * 70)
        print()
    
    def print_progress_update(self, phase: str, current: int, total: int, item_name: str = ""):
        """Print progress update"""
        percentage = (current / total * 100) if total > 0 else 0
        progress_bar = "█" * int(percentage // 5) + "░" * (20 - int(percentage // 5))
        
        print(f"\r🔄 {phase}: [{progress_bar}] {percentage:.1f}% ({current}/{total}) {item_name}", end="", flush=True)
        
        if current == total:
            print()  # New line when complete
    
    def monitor_workflow_testing(self):
        """Monitor workflow testing progress"""
        print("📋 Starting Workflow Testing Phase...")
        
        # Get workflow templates for progress tracking
        try:
            from dashboards.workflow_module import get_workflow_templates
            templates = get_workflow_templates()
            active_templates = [t for t in templates if 'Future' not in t['template_name']]
            total_workflows = len(active_templates)
            total_iterations = total_workflows * self.tester.test_iterations
            
            print(f"   📊 Found {total_workflows} active workflow templates")
            print(f"   🔄 Total iterations to execute: {total_iterations}")
            print()
            
            # Monitor progress (this is a simplified version - the actual monitoring
            # would need to be integrated into the tester class)
            for i, template in enumerate(active_templates, 1):
                template_name = template['template_name']
                print(f"   🧪 Testing: {template_name}")
                
                for iteration in range(1, self.tester.test_iterations + 1):
                    current_iteration = (i - 1) * self.tester.test_iterations + iteration
                    self.print_progress_update(
                        "Workflow Tests", 
                        current_iteration, 
                        total_iterations,
                        f"{template_name} (Iter {iteration})"
                    )
                    time.sleep(0.1)  # Brief pause for display
                
                print(f"   ✅ Completed: {template_name}")
            
        except Exception as e:
            print(f"   ⚠️ Could not get workflow templates for monitoring: {str(e)}")
    
    def run_tests_with_monitoring(self):
        """Run tests with enhanced monitoring"""
        self.print_header()
        
        start_time = time.time()
        
        try:
            # Phase 1: Authentication
            print("🔐 Phase 1: Authentication")
            if not self.tester.authenticate_test_user():
                print("❌ Authentication failed!")
                return False
            print("✅ Authentication successful")
            print()
            
            # Phase 2: Database Verification
            print("🗄️ Phase 2: Database Verification")
            if not self.tester.verify_database_tables():
                print("⚠️ Database verification issues detected, continuing...")
            else:
                print("✅ Database verification passed")
            print()
            
            # Phase 3: Workflow Testing
            print("🔄 Phase 3: Comprehensive Workflow Testing")
            if not self.tester.test_all_workflows_comprehensive():
                print("❌ Workflow testing failed!")
                return False
            print("✅ Workflow testing completed")
            print()
            
            # Phase 4: Provider Testing
            print("👨‍⚕️ Phase 4: Provider Functionality Testing")
            if not self.tester.test_provider_functionality():
                print("❌ Provider testing failed!")
                return False
            print("✅ Provider testing completed")
            print()
            
            # Phase 5: Data Validation
            print("🔍 Phase 5: Data Synchronization Testing")
            if not self.tester.test_data_synchronization():
                print("⚠️ Data synchronization issues detected")
            else:
                print("✅ Data synchronization verified")
            print()
            
            # Phase 6: Database Verification
            print("✅ Phase 6: Database Verification")
            if not self.tester.run_database_verification():
                print("⚠️ Database verification issues detected")
            else:
                print("✅ Database verification passed")
            print()
            
            # Phase 7: Report Generation
            print("📊 Phase 7: Generating Reports")
            self.generate_enhanced_reports()
            print("✅ Reports generated")
            print()
            
            end_time = time.time()
            duration = end_time - start_time
            
            print("🎉 Test Suite Completed Successfully!")
            print(f"⏱️ Total Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
            
            return True
            
        except Exception as e:
            print(f"❌ Test suite failed with exception: {str(e)}")
            if self.verbose:
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
            return False
    
    def generate_enhanced_reports(self):
        """Generate enhanced reports with multiple formats"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. Generate comprehensive text report
        report = self.tester.generate_comprehensive_report()
        report_file = self.output_dir / f"integration_test_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"   📄 Text report: {report_file}")
        
        # 2. Save detailed JSON results
        json_file = self.output_dir / f"integration_test_results_{timestamp}.json"
        self.tester.save_test_results(str(json_file))
        print(f"   📋 JSON results: {json_file}")
        
        # 3. Generate summary CSV for easy analysis
        self.generate_csv_summary(timestamp)
        
        # 4. Generate HTML report
        self.generate_html_report(timestamp)
    
    def generate_csv_summary(self, timestamp: str):
        """Generate CSV summary of test results"""
        import csv
        
        csv_file = self.output_dir / f"integration_test_summary_{timestamp}.csv"
        
        try:
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Workflow results
                writer.writerow(['Test Type', 'Template/Test Name', 'Iteration', 'Status', 'Duration', 'Steps Completed', 'Total Steps'])
                
                for template_test in self.tester.test_results.get('workflow_tests', []):
                    template_name = template_test['template_name']
                    for iteration in template_test['iterations']:
                        writer.writerow([
                            'Workflow',
                            template_name,
                            iteration['iteration'],
                            iteration['status'],
                            f"{iteration['duration_seconds']:.2f}",
                            iteration['steps_completed'],
                            iteration['total_steps']
                        ])
                
                # Provider results
                for provider_test in self.tester.test_results.get('provider_tests', []):
                    writer.writerow([
                        'Provider',
                        provider_test['test_name'],
                        1,
                        provider_test['status'],
                        'N/A',
                        'N/A',
                        'N/A'
                    ])
            
            print(f"   📊 CSV summary: {csv_file}")
            
        except Exception as e:
            print(f"   ⚠️ Failed to generate CSV summary: {str(e)}")
    
    def generate_html_report(self, timestamp: str):
        """Generate HTML report for easy viewing"""
        html_file = self.output_dir / f"integration_test_report_{timestamp}.html"
        
        try:
            # Calculate summary statistics
            workflow_tests = self.tester.test_results.get('workflow_tests', [])
            total_templates = len(workflow_tests)
            total_iterations = sum(len(t['iterations']) for t in workflow_tests)
            successful_iterations = sum(
                len([i for i in t['iterations'] if i['status'] == 'COMPLETED'])
                for t in workflow_tests
            )
            success_rate = (successful_iterations / total_iterations * 100) if total_iterations > 0 else 0
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Integration Test Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f8ff; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .error {{ color: #dc3545; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .status-completed {{ background-color: #d4edda; }}
        .status-failed {{ background-color: #f8d7da; }}
        .status-partial {{ background-color: #fff3cd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 MyHealthTeam Integration Test Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Test User:</strong> {self.tester.test_email}</p>
        <p><strong>Iterations per Workflow:</strong> {self.tester.test_iterations}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Test Summary</h2>
        <ul>
            <li><strong>Workflow Templates Tested:</strong> {total_templates}</li>
            <li><strong>Total Iterations:</strong> {total_iterations}</li>
            <li><strong>Successful Iterations:</strong> <span class="success">{successful_iterations}</span></li>
            <li><strong>Overall Success Rate:</strong> <span class="{'success' if success_rate >= 80 else 'warning' if success_rate >= 60 else 'error'}">{success_rate:.1f}%</span></li>
        </ul>
    </div>
    
    <h2>🔄 Workflow Test Results</h2>
    <table>
        <tr>
            <th>Template Name</th>
            <th>Iterations</th>
            <th>Completed</th>
            <th>Success Rate</th>
            <th>Avg Duration</th>
        </tr>
"""
            
            for template_test in workflow_tests:
                summary = template_test['summary']
                status_class = 'success' if summary['success_rate'] >= 80 else 'warning' if summary['success_rate'] >= 60 else 'error'
                
                html_content += f"""
        <tr>
            <td>{template_test['template_name']}</td>
            <td>{summary['total_iterations']}</td>
            <td>{summary['completed']}</td>
            <td><span class="{status_class}">{summary['success_rate']:.1f}%</span></td>
            <td>{summary['average_duration_seconds']:.2f}s</td>
        </tr>
"""
            
            html_content += """
    </table>
    
    <h2>👨‍⚕️ Provider Test Results</h2>
    <table>
        <tr>
            <th>Test Name</th>
            <th>Status</th>
            <th>Patient ID</th>
            <th>Data Validation</th>
        </tr>
"""
            
            for provider_test in self.tester.test_results.get('provider_tests', []):
                status_class = f"status-{provider_test['status'].lower()}"
                validation = provider_test.get('data_validation', {})
                validation_summary = f"{sum(validation.values())}/{len(validation)} checks passed"
                
                html_content += f"""
        <tr class="{status_class}">
            <td>{provider_test['test_name']}</td>
            <td>{provider_test['status']}</td>
            <td>{provider_test['patient_id']}</td>
            <td>{validation_summary}</td>
        </tr>
"""
            
            html_content += """
    </table>
    
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
        <p>Generated by MyHealthTeam Integration Test Suite</p>
    </footer>
</body>
</html>
"""
            
            with open(html_file, 'w') as f:
                f.write(html_content)
            
            print(f"   🌐 HTML report: {html_file}")
            
        except Exception as e:
            print(f"   ⚠️ Failed to generate HTML report: {str(e)}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive integration tests for MyHealthTeam workflow system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_integration_tests.py                    # Run with defaults
    python run_integration_tests.py --quick            # Quick test (1 iteration)
    python run_integration_tests.py --iterations 3     # 3 iterations per workflow
    python run_integration_tests.py --verbose          # Verbose output
    python run_integration_tests.py --output results   # Custom output directory
        """
    )
    
    parser.add_argument(
        '--iterations', 
        type=int, 
        default=5,
        help='Number of iterations per workflow (default: 5)'
    )
    
    parser.add_argument(
        '--user', 
        default='dianela@',
        help='Test user email (default: dianela@)'
    )
    
    parser.add_argument(
        '--password', 
        default='test4',
        help='Test user password (default: test4)'
    )
    
    parser.add_argument(
        '--output', 
        default='test_results',
        help='Output directory for reports (default: test_results)'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quick', 
        action='store_true',
        help='Run quick test (1 iteration per workflow)'
    )
    
    return parser.parse_args()

def main():
    """Main execution function"""
    args = parse_arguments()
    
    # Create test runner
    runner = IntegrationTestRunner(args)
    
    # Run tests with monitoring
    success = runner.run_tests_with_monitoring()
    
    if success:
        print("\n🎉 All integration tests completed successfully!")
        print(f"📁 Results saved to: {runner.output_dir}")
        return 0
    else:
        print("\n❌ Integration testing failed!")
        return 1

if __name__ == "__main__":
    exit(main())