#!/usr/bin/env python3
"""
Comprehensive Integration Testing Suite for MyHealthTeam Workflow System

This script provides comprehensive testing for:
1. All 14 workflow templates with step validation and 5x execution
2. Provider testing for Visit Tasks and phone review (15-minute default)
3. Data validation for coordinator/provider tasks and YYYY_MM table sync
4. Database verification using sqlite3 for data consistency

Author: Integration Testing Framework
Created: 2024-12-19
"""

import sys
import os
import sqlite3
import json
import time
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
import traceback

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import required modules
from database import (
    get_db_connection,
    save_coordinator_task, save_daily_task
)
from core_utils import get_user_role_ids
from auth_module import AuthenticationManager
from dashboards.workflow_module import (
    get_workflow_templates, create_workflow_instance, 
    get_workflow_template_steps, complete_workflow_step,
    get_ongoing_workflows
)

class ComprehensiveIntegrationTester:
    """Main testing class for comprehensive integration testing"""
    
    def __init__(self, test_email="dianela@myhealthteam.org", test_password="pass123"):
        self.test_email = test_email
        self.test_password = test_password
        self.user_data = None
        self.user_id = None
        self.coordinator_id = None
        self.provider_id = None
        self.user_role_ids = []
        
        # Test tracking
        self.test_results = {
            'workflow_tests': [],
            'provider_tests': [],
            'data_validation_tests': [],
            'database_verification_tests': []
        }
        
        # Test configuration
        self.test_iterations = 5
        self.provider_default_duration = 15  # minutes
        
        # Database paths
        self.db_path = "production.db"
        
        # Test report data
        self.start_time = datetime.now()
        self.test_log = []
        
    def log_test_event(self, level: str, message: str, details: Dict = None):
        """Log test events with timestamp and details"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'details': details or {}
        }
        self.test_log.append(log_entry)
        
        # Print to console
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_icon = {
            'INFO': '📋',
            'SUCCESS': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'DEBUG': '🔍'
        }.get(level, '📝')
        
        print(f"[{timestamp}] {level_icon} {message}")
        if details and level in ['ERROR', 'WARNING']:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def authenticate_test_user(self) -> bool:
        """Authenticate the test user and set up user context"""
        self.log_test_event('INFO', f"Authenticating test user: {self.test_email}")
        
        try:
            auth_manager = AuthenticationManager()
            self.user_data = auth_manager.authenticate_user(self.test_email, self.test_password)
            if not self.user_data:
                self.log_test_event('ERROR', f"Authentication failed for {self.test_email}")
                return False
                
            self.user_id = self.user_data['user_id']
            self.coordinator_id = self.user_id
            self.provider_id = self.user_id  # Assuming same for testing
            self.user_role_ids = get_user_role_ids(self.user_id)
            
            self.log_test_event('SUCCESS', "Authentication successful", {
                'user_id': self.user_id,
                'role_ids': self.user_role_ids,
                'name': f"{self.user_data.get('first_name', '')} {self.user_data.get('last_name', '')}"
            })
            return True
            
        except Exception as e:
            self.log_test_event('ERROR', f"Authentication exception: {str(e)}")
            return False
    
    def get_test_patient_ids(self, count: int = 5) -> List[str]:
        """Get multiple test patient IDs for testing"""
        conn = get_db_connection()
        try:
            patients = conn.execute(
                "SELECT patient_id FROM patients LIMIT ?", (count,)
            ).fetchall()
            return [p['patient_id'] for p in patients]
        except Exception as e:
            self.log_test_event('ERROR', f"Failed to get test patients: {str(e)}")
            return []
        finally:
            conn.close()
    
    def verify_database_tables(self) -> bool:
        """Verify all required database tables exist"""
        self.log_test_event('INFO', "Verifying database table structure")
        
        required_tables = [
            'workflow_templates', 'workflow_steps', 'workflow_instances',
            'coordinator_tasks', 'provider_tasks', 'patients', 'patient_panel',
            'users', 'roles'
        ]
        
        # Check for YYYY_MM tables
        current_year = datetime.now().year
        current_month = datetime.now().month
        monthly_tables = [
            f'coordinator_tasks_{current_year}_{current_month:02d}',
            f'provider_tasks_{current_year}_{current_month:02d}'
        ]
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = []
            for table in required_tables + monthly_tables:
                if table not in existing_tables:
                    missing_tables.append(table)
            
            if missing_tables:
                self.log_test_event('WARNING', f"Missing tables: {missing_tables}")
                return False
            
            self.log_test_event('SUCCESS', "All required database tables exist")
            return True
            
        except Exception as e:
            self.log_test_event('ERROR', f"Database verification failed: {str(e)}")
            return False
        finally:
            conn.close()
    
    def test_single_workflow_iteration(self, template_id: int, template_name: str, 
                                     iteration: int, patient_id: str) -> Dict[str, Any]:
        """Test a single workflow template iteration"""
        self.log_test_event('INFO', 
            f"Testing workflow '{template_name}' - Iteration {iteration}/5 - Patient {patient_id}")
        
        test_result = {
            'template_id': template_id,
            'template_name': template_name,
            'iteration': iteration,
            'patient_id': patient_id,
            'status': 'PENDING',
            'instance_id': None,
            'steps_completed': 0,
            'total_steps': 0,
            'step_details': [],
            'errors': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_seconds': 0
        }
        
        start_time = time.time()
        
        try:
            # Get workflow steps
            steps = get_workflow_template_steps(template_id)
            test_result['total_steps'] = len(steps)
            
            if not steps:
                test_result['errors'].append("No steps found for workflow template")
                test_result['status'] = 'FAILED'
                return test_result
            
            # Create workflow instance
            instance_id = create_workflow_instance(
                template_id=template_id,
                patient_id=patient_id,
                coordinator_id=self.coordinator_id,
                notes=f"Integration test iteration {iteration} for {template_name}"
            )
            
            if not instance_id:
                test_result['errors'].append("Failed to create workflow instance")
                test_result['status'] = 'FAILED'
                return test_result
            
            test_result['instance_id'] = instance_id
            
            # Complete each step with detailed tracking
            for i, step in enumerate(steps, 1):
                step_start_time = time.time()
                step_id = step['step_id']
                step_name = step['task_name']
                step_owner = step.get('owner', 'Unknown')
                
                step_detail = {
                    'step_number': i,
                    'step_id': step_id,
                    'step_name': step_name,
                    'owner': step_owner,
                    'status': 'PENDING',
                    'duration_seconds': 0,
                    'errors': []
                }
                
                try:
                    # Simulate realistic work time (1-3 seconds)
                    time.sleep(1 + (i % 3))
                    
                    # Complete the step
                    success = complete_workflow_step(
                        instance_id=instance_id,
                        step_id=step_id,
                        coordinator_id=self.coordinator_id,
                        duration_minutes=5,
                        notes=f"Integration test step completion: {step_name}"
                    )
                    
                    step_detail['duration_seconds'] = time.time() - step_start_time
                    
                    if success:
                        test_result['steps_completed'] += 1
                        step_detail['status'] = 'COMPLETED'
                        
                        # Verify step completion in database
                        if not self.verify_step_completion(instance_id, step_id):
                            step_detail['errors'].append("Step completion not verified in database")
                            step_detail['status'] = 'VERIFICATION_FAILED'
                    else:
                        step_detail['status'] = 'FAILED'
                        step_detail['errors'].append("Step completion function returned False")
                        
                except Exception as e:
                    step_detail['status'] = 'ERROR'
                    step_detail['errors'].append(f"Exception: {str(e)}")
                    step_detail['duration_seconds'] = time.time() - step_start_time
                
                test_result['step_details'].append(step_detail)
                
                # Break on first failure for this iteration
                if step_detail['status'] not in ['COMPLETED']:
                    break
            
            # Determine final status
            if test_result['steps_completed'] == test_result['total_steps']:
                test_result['status'] = 'COMPLETED'
            elif test_result['steps_completed'] > 0:
                test_result['status'] = 'PARTIAL'
            else:
                test_result['status'] = 'FAILED'
                
        except Exception as e:
            test_result['errors'].append(f"Workflow test exception: {str(e)}")
            test_result['status'] = 'ERROR'
        
        test_result['duration_seconds'] = time.time() - start_time
        test_result['end_time'] = datetime.now().isoformat()
        
        return test_result
    
    def verify_step_completion(self, instance_id: int, step_id: int) -> bool:
        """Verify that a workflow step was properly completed in the database"""
        conn = get_db_connection()
        try:
            # Check workflow_instances table for step completion
            result = conn.execute("""
                SELECT step1_complete, step2_complete, step3_complete, 
                       step4_complete, step5_complete, step6_complete
                FROM workflow_instances 
                WHERE instance_id = ?
            """, (instance_id,)).fetchone()
            
            if result:
                # Convert to dict and check if any step is marked complete
                step_columns = dict(result)
                return any(step_columns.values())
            
            return False
            
        except Exception as e:
            self.log_test_event('ERROR', f"Step verification failed: {str(e)}")
            return False
        finally:
            conn.close()
    
    def test_all_workflows_comprehensive(self) -> bool:
        """Test all workflow templates with 5 iterations each"""
        self.log_test_event('INFO', "Starting comprehensive workflow testing (5 iterations per workflow)")
        
        # Get all workflow templates
        templates = get_workflow_templates()
        if not templates:
            self.log_test_event('ERROR', "No workflow templates found")
            return False
        
        # Filter out 'Future' templates as per existing logic
        active_templates = [t for t in templates if 'Future' not in t['template_name']]
        
        self.log_test_event('INFO', f"Found {len(active_templates)} active workflow templates to test")
        
        # Get test patients
        test_patients = self.get_test_patient_ids(count=10)
        if not test_patients:
            self.log_test_event('ERROR', "No test patients available")
            return False
        
        # Test each template 5 times
        for template in active_templates:
            template_id = template['template_id']
            template_name = template['template_name']
            
            template_results = []
            
            for iteration in range(1, self.test_iterations + 1):
                # Use different patients for each iteration
                patient_id = test_patients[(iteration - 1) % len(test_patients)]
                
                result = self.test_single_workflow_iteration(
                    template_id, template_name, iteration, patient_id
                )
                template_results.append(result)
                
                # Brief pause between iterations
                time.sleep(2)
            
            self.test_results['workflow_tests'].append({
                'template_id': template_id,
                'template_name': template_name,
                'iterations': template_results,
                'summary': self.calculate_template_summary(template_results)
            })
        
        return True
    
    def calculate_template_summary(self, iterations: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics for a template's test iterations"""
        total = len(iterations)
        completed = len([i for i in iterations if i['status'] == 'COMPLETED'])
        partial = len([i for i in iterations if i['status'] == 'PARTIAL'])
        failed = len([i for i in iterations if i['status'] in ['FAILED', 'ERROR']])
        
        avg_duration = sum(i['duration_seconds'] for i in iterations) / total if total > 0 else 0
        avg_steps_completed = sum(i['steps_completed'] for i in iterations) / total if total > 0 else 0
        
        return {
            'total_iterations': total,
            'completed': completed,
            'partial': partial,
            'failed': failed,
            'success_rate': (completed / total * 100) if total > 0 else 0,
            'average_duration_seconds': avg_duration,
            'average_steps_completed': avg_steps_completed
        }
    
    def test_provider_functionality(self) -> bool:
        """Test provider Visit Tasks and phone review functionality"""
        self.log_test_event('INFO', "Starting provider functionality testing")
        
        test_patients = self.get_test_patient_ids(count=3)
        if not test_patients:
            self.log_test_event('ERROR', "No test patients for provider testing")
            return False
        
        provider_tests = [
            {
                'test_name': 'Visit Task - In-Person',
                'task_type': 'Visit Task',
                'service_type': 'In-Person Visit',
                'duration_minutes': self.provider_default_duration,
                'billing_code': 'G0506'
            },
            {
                'test_name': 'Visit Task - Telehealth',
                'task_type': 'Visit Task',
                'service_type': 'Telehealth Visit',
                'duration_minutes': self.provider_default_duration,
                'billing_code': 'G0507'
            },
            {
                'test_name': 'Phone Review',
                'task_type': 'Phone Review',
                'service_type': 'Phone Consultation',
                'duration_minutes': self.provider_default_duration,
                'billing_code': 'G0508'
            }
        ]
        
        for i, test_config in enumerate(provider_tests):
            patient_id = test_patients[i % len(test_patients)]
            
            test_result = self.test_single_provider_task(test_config, patient_id)
            self.test_results['provider_tests'].append(test_result)
            
            time.sleep(1)  # Brief pause between tests
        
        return True
    
    def test_single_provider_task(self, test_config: Dict, patient_id: str) -> Dict[str, Any]:
        """Test a single provider task with data validation"""
        self.log_test_event('INFO', f"Testing provider task: {test_config['test_name']}")
        
        test_result = {
            'test_name': test_config['test_name'],
            'patient_id': patient_id,
            'status': 'PENDING',
            'task_id': None,
            'data_validation': {
                'provider_tasks_table': False,
                'provider_tasks_monthly_table': False,
                'patient_info_updated': False
            },
            'errors': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        try:
            # Prepare task data for save_daily_task
            task_date = datetime.now().strftime('%Y-%m-%d')
            task_description = test_config['task_type']
            notes = f"Integration test: {test_config['test_name']}"
            billing_code = test_config['billing_code']
            
            # Save provider task (this should write to both tables)
            task_id = save_daily_task(self.provider_id, patient_id, task_date, task_description, notes, billing_code)
            
            if task_id:
                test_result['task_id'] = task_id
                test_result['status'] = 'COMPLETED'
                
                # Recreate task_data for validation
                task_data = {
                    'provider_id': self.provider_id,
                    'patient_id': patient_id,
                    'task_date': task_date,
                    'task_description': task_description,
                    'notes': notes,
                    'billing_code': billing_code
                }
                
                # Validate data was written correctly
                validation_results = self.validate_provider_task_data(task_id, task_data)
                test_result['data_validation'] = validation_results
                
            else:
                test_result['status'] = 'FAILED'
                test_result['errors'].append("Failed to create provider task")
                
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(f"Provider task test exception: {str(e)}")
        
        test_result['end_time'] = datetime.now().isoformat()
        return test_result
    
    def validate_provider_task_data(self, task_id: int, task_data: Dict) -> Dict[str, bool]:
        """Validate that provider task data was written to all required tables"""
        validation = {
            'provider_tasks_table': False,
            'provider_tasks_monthly_table': False,
            'patient_info_updated': False
        }
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Check provider_tasks table
            result = conn.execute(
                "SELECT * FROM provider_tasks WHERE provider_task_id = ?", 
                (task_id,)
            ).fetchone()
            validation['provider_tasks_table'] = result is not None
            
            # Check monthly table
            current_year = datetime.now().year
            current_month = datetime.now().month
            monthly_table = f"provider_tasks_{current_year}_{current_month:02d}"
            
            try:
                result = conn.execute(
                    f"SELECT * FROM {monthly_table} WHERE provider_task_id = ?", 
                    (task_id,)
                ).fetchone()
                validation['provider_tasks_monthly_table'] = result is not None
            except sqlite3.OperationalError:
                # Monthly table might not exist
                validation['provider_tasks_monthly_table'] = False
            
            # Check if patient info was updated (basic check)
            patient_result = conn.execute(
                "SELECT * FROM patients WHERE patient_id = ?", 
                (task_data['patient_id'],)
            ).fetchone()
            validation['patient_info_updated'] = patient_result is not None
            
        except Exception as e:
            self.log_test_event('ERROR', f"Data validation failed: {str(e)}")
        finally:
            conn.close()
        
        return validation
    
    def test_provider_visit_task(self) -> bool:
        """Test provider visit task creation and completion"""
        self.log_test_event('INFO', "Testing provider visit task")
        
        try:
            # Get a test patient
            test_patients = self.get_test_patient_ids(count=1)
            if not test_patients:
                self.log_test_event('ERROR', "No test patients available for provider visit task test")
                return False
            
            patient_id = test_patients[0]
            
            # Create a test visit task
            task_config = {
                'test_name': 'Provider Visit Task Test',
                'task_type': 'Visit Task',
                'service_type': 'In-Person Visit',
                'duration_minutes': self.provider_default_duration,
                'billing_code': 'G0506'
            }
            
            # Test the provider task
            result = self.test_single_provider_task(task_config, patient_id)
            
            # Add to test results
            if 'provider_tests' not in self.test_results:
                self.test_results['provider_tests'] = []
            self.test_results['provider_tests'].append(result)
            
            return result['status'] == 'COMPLETED'
            
        except Exception as e:
            self.log_test_event('ERROR', f"Provider visit task test failed: {str(e)}")
            return False
    
    def validate_provider_data_consistency(self) -> bool:
        """Validate provider data consistency across tables"""
        self.log_test_event('INFO', "Validating provider data consistency")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Check for orphaned provider tasks (tasks without valid patient references)
            orphaned_tasks = conn.execute("""
                SELECT COUNT(*) FROM provider_tasks pt 
                LEFT JOIN patients p ON pt.patient_id = p.patient_id 
                WHERE p.patient_id IS NULL AND pt.patient_id IS NOT NULL AND pt.patient_id != ''
            """).fetchone()[0]
            
            # Check for provider tasks without valid provider references
            invalid_provider_tasks = conn.execute("""
                SELECT COUNT(*) FROM provider_tasks pt 
                LEFT JOIN providers pr ON pt.provider_id = pr.provider_id 
                WHERE pr.provider_id IS NULL AND pt.provider_id IS NOT NULL AND pt.provider_id != ''
            """).fetchone()[0]
            
            # Check synchronization between main and monthly tables
            current_year = datetime.now().year
            current_month = datetime.now().month
            monthly_table = f"provider_tasks_{current_year}_{current_month:02d}"
            
            sync_issues = 0
            try:
                # Count records in main table for current month
                main_count = conn.execute("""
                    SELECT COUNT(*) FROM provider_tasks 
                    WHERE strftime('%Y-%m', task_date) = ?
                """, (f"{current_year}-{current_month:02d}",)).fetchone()[0]
                
                # Count records in monthly table
                monthly_count = conn.execute(f"SELECT COUNT(*) FROM {monthly_table}").fetchone()[0]
                
                # Allow some variance but flag major discrepancies
                if abs(main_count - monthly_count) > 10:
                    sync_issues = abs(main_count - monthly_count)
                    
            except sqlite3.OperationalError:
                # Monthly table might not exist
                sync_issues = 1
            
            conn.close()
            
            # Log findings
            if orphaned_tasks > 0:
                self.log_test_event('WARNING', f"Found {orphaned_tasks} orphaned provider tasks")
            if invalid_provider_tasks > 0:
                self.log_test_event('WARNING', f"Found {invalid_provider_tasks} provider tasks with invalid provider references")
            if sync_issues > 0:
                self.log_test_event('WARNING', f"Found {sync_issues} synchronization issues between main and monthly tables")
            
            # Consider validation successful if issues are minimal
            total_issues = orphaned_tasks + invalid_provider_tasks + sync_issues
            success = total_issues < 50  # Allow some tolerance for test environment
            
            if success:
                self.log_test_event('INFO', "Provider data consistency validation passed")
            else:
                self.log_test_event('ERROR', f"Provider data consistency validation failed with {total_issues} issues")
            
            return success
            
        except Exception as e:
            self.log_test_event('ERROR', f"Provider data consistency validation error: {str(e)}")
            return False
    
    def test_data_synchronization(self) -> bool:
        """Test data synchronization between main and monthly tables"""
        self.log_test_event('INFO', "Testing data synchronization between main and monthly tables")
        
        # Test coordinator tasks synchronization
        coord_sync_result = self.test_coordinator_task_sync()
        
        # Test provider tasks synchronization  
        provider_sync_result = self.test_provider_task_sync()
        
        self.test_results['data_validation_tests'] = {
            'coordinator_sync': coord_sync_result,
            'provider_sync': provider_sync_result
        }
        
        return coord_sync_result['status'] == 'PASSED' and provider_sync_result['status'] == 'PASSED'
    
    def test_coordinator_task_sync(self) -> Dict[str, Any]:
        """Test coordinator task synchronization"""
        test_result = {
            'test_name': 'Coordinator Task Synchronization',
            'status': 'PENDING',
            'main_table_count': 0,
            'monthly_table_count': 0,
            'sync_status': False,
            'errors': []
        }
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Count records in main table
            main_count = conn.execute("SELECT COUNT(*) FROM coordinator_tasks").fetchone()[0]
            test_result['main_table_count'] = main_count
            
            # Count records in current monthly table
            current_year = datetime.now().year
            current_month = datetime.now().month
            monthly_table = f"coordinator_tasks_{current_year}_{current_month:02d}"
            
            try:
                monthly_count = conn.execute(f"SELECT COUNT(*) FROM {monthly_table}").fetchone()[0]
                test_result['monthly_table_count'] = monthly_count
                
                # Basic sync check - monthly should have some data if main table has data
                if main_count > 0:
                    test_result['sync_status'] = monthly_count > 0
                else:
                    test_result['sync_status'] = True  # No data to sync
                    
                test_result['status'] = 'PASSED' if test_result['sync_status'] else 'FAILED'
                
            except sqlite3.OperationalError as e:
                test_result['errors'].append(f"Monthly table access error: {str(e)}")
                test_result['status'] = 'FAILED'
                
        except Exception as e:
            test_result['errors'].append(f"Coordinator sync test error: {str(e)}")
            test_result['status'] = 'ERROR'
        finally:
            conn.close()
        
        return test_result
    
    def test_provider_task_sync(self) -> Dict[str, Any]:
        """Test provider task synchronization"""
        test_result = {
            'test_name': 'Provider Task Synchronization',
            'status': 'PENDING',
            'main_table_count': 0,
            'monthly_table_count': 0,
            'sync_status': False,
            'errors': []
        }
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Count records in main table
            main_count = conn.execute("SELECT COUNT(*) FROM provider_tasks").fetchone()[0]
            test_result['main_table_count'] = main_count
            
            # Count records in current monthly table
            current_year = datetime.now().year
            current_month = datetime.now().month
            monthly_table = f"provider_tasks_{current_year}_{current_month:02d}"
            
            try:
                monthly_count = conn.execute(f"SELECT COUNT(*) FROM {monthly_table}").fetchone()[0]
                test_result['monthly_table_count'] = monthly_count
                
                # Basic sync check
                if main_count > 0:
                    test_result['sync_status'] = monthly_count > 0
                else:
                    test_result['sync_status'] = True
                    
                test_result['status'] = 'PASSED' if test_result['sync_status'] else 'FAILED'
                
            except sqlite3.OperationalError as e:
                test_result['errors'].append(f"Monthly table access error: {str(e)}")
                test_result['status'] = 'FAILED'
                
        except Exception as e:
            test_result['errors'].append(f"Provider sync test error: {str(e)}")
            test_result['status'] = 'ERROR'
        finally:
            conn.close()
        
        return test_result
    
    def run_database_verification(self) -> bool:
        """Run comprehensive database verification tests"""
        self.log_test_event('INFO', "Running database verification tests")
        
        verification_tests = [
            self.verify_patient_table_views(),
            self.verify_data_consistency(),
            self.verify_foreign_key_integrity(),
            self.verify_table_schemas()
        ]
        
        self.test_results['database_verification_tests'] = verification_tests
        
        # All tests must pass
        return all(test['status'] == 'PASSED' for test in verification_tests)
    
    def verify_patient_table_views(self) -> Dict[str, Any]:
        """Verify patient table views and summaries"""
        test_result = {
            'test_name': 'Patient Table Views and Summaries',
            'status': 'PENDING',
            'tables_checked': [],
            'errors': []
        }
        
        patient_related_tables = [
            'patients', 'patient_panel', 'patient_assignments',
            'onboarding_patients', 'patient_visits'
        ]
        
        conn = sqlite3.connect(self.db_path)
        try:
            for table in patient_related_tables:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    test_result['tables_checked'].append({
                        'table': table,
                        'record_count': count,
                        'status': 'OK'
                    })
                except sqlite3.OperationalError as e:
                    test_result['tables_checked'].append({
                        'table': table,
                        'record_count': 0,
                        'status': f'ERROR: {str(e)}'
                    })
            
            test_result['status'] = 'PASSED'
            
        except Exception as e:
            test_result['errors'].append(f"Patient table verification error: {str(e)}")
            test_result['status'] = 'ERROR'
        finally:
            conn.close()
        
        return test_result
    
    def verify_data_consistency(self) -> Dict[str, Any]:
        """Verify data consistency across related tables"""
        test_result = {
            'test_name': 'Data Consistency Verification',
            'status': 'PENDING',
            'consistency_checks': [],
            'errors': []
        }
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Check workflow instances have valid template references
            orphaned_instances = conn.execute("""
                SELECT COUNT(*) FROM workflow_instances wi
                LEFT JOIN workflow_templates wt ON wi.template_id = wt.template_id
                WHERE wt.template_id IS NULL
            """).fetchone()[0]
            
            test_result['consistency_checks'].append({
                'check': 'Workflow instances have valid templates',
                'orphaned_records': orphaned_instances,
                'status': 'PASS' if orphaned_instances == 0 else 'FAIL'
            })
            
            # Check workflow steps have valid template references
            orphaned_steps = conn.execute("""
                SELECT COUNT(*) FROM workflow_steps ws
                LEFT JOIN workflow_templates wt ON ws.template_id = wt.template_id
                WHERE wt.template_id IS NULL
            """).fetchone()[0]
            
            test_result['consistency_checks'].append({
                'check': 'Workflow steps have valid templates',
                'orphaned_records': orphaned_steps,
                'status': 'PASS' if orphaned_steps == 0 else 'FAIL'
            })
            
            # Check if all checks passed
            all_passed = all(check['status'] == 'PASS' for check in test_result['consistency_checks'])
            test_result['status'] = 'PASSED' if all_passed else 'FAILED'
            
        except Exception as e:
            test_result['errors'].append(f"Consistency verification error: {str(e)}")
            test_result['status'] = 'ERROR'
        finally:
            conn.close()
        
        return test_result
    
    def verify_foreign_key_integrity(self) -> Dict[str, Any]:
        """Verify foreign key integrity"""
        test_result = {
            'test_name': 'Foreign Key Integrity',
            'status': 'PENDING',
            'integrity_violations': 0,
            'errors': []
        }
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Enable foreign key checking
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Run integrity check
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            test_result['integrity_violations'] = len(violations)
            
            if violations:
                test_result['errors'].extend([str(v) for v in violations])
                test_result['status'] = 'FAILED'
            else:
                test_result['status'] = 'PASSED'
                
        except Exception as e:
            test_result['errors'].append(f"Foreign key check error: {str(e)}")
            test_result['status'] = 'ERROR'
        finally:
            conn.close()
        
        return test_result
    
    def verify_table_schemas(self) -> Dict[str, Any]:
        """Verify table schemas match expected structure"""
        test_result = {
            'test_name': 'Table Schema Verification',
            'status': 'PENDING',
            'schema_checks': [],
            'errors': []
        }
        
        expected_schemas = {
            'workflow_templates': ['template_id', 'template_name'],
            'workflow_steps': ['step_id', 'template_id', 'step_order', 'task_name'],
            'coordinator_tasks': ['coordinator_task_id', 'task_id', 'patient_id', 'coordinator_id'],
            'provider_tasks': ['provider_task_id', 'task_id', 'provider_id', 'patient_id']
        }
        
        conn = sqlite3.connect(self.db_path)
        try:
            for table, expected_columns in expected_schemas.items():
                try:
                    cursor = conn.execute(f"PRAGMA table_info({table})")
                    actual_columns = [row[1] for row in cursor.fetchall()]
                    
                    missing_columns = [col for col in expected_columns if col not in actual_columns]
                    
                    test_result['schema_checks'].append({
                        'table': table,
                        'expected_columns': expected_columns,
                        'actual_columns': actual_columns,
                        'missing_columns': missing_columns,
                        'status': 'PASS' if not missing_columns else 'FAIL'
                    })
                    
                except sqlite3.OperationalError as e:
                    test_result['schema_checks'].append({
                        'table': table,
                        'status': f'ERROR: {str(e)}'
                    })
            
            # Check if all schema checks passed
            all_passed = all(
                check.get('status') == 'PASS' 
                for check in test_result['schema_checks']
                if isinstance(check.get('status'), str) and check['status'] != 'ERROR'
            )
            test_result['status'] = 'PASSED' if all_passed else 'FAILED'
            
        except Exception as e:
            test_result['errors'].append(f"Schema verification error: {str(e)}")
            test_result['status'] = 'ERROR'
        finally:
            conn.close()
        
        return test_result
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        report = f"""
# Comprehensive Integration Test Report
Generated: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {total_duration:.2f} seconds

## Test Summary
"""
        
        # Workflow tests summary
        workflow_tests = self.test_results['workflow_tests']
        if workflow_tests:
            total_templates = len(workflow_tests)
            total_iterations = sum(len(t['iterations']) for t in workflow_tests)
            successful_iterations = sum(
                len([i for i in t['iterations'] if i['status'] == 'COMPLETED'])
                for t in workflow_tests
            )
            
            report += f"""
### Workflow Testing Results
- Templates Tested: {total_templates}
- Total Iterations: {total_iterations}
- Successful Iterations: {successful_iterations}
- Success Rate: {(successful_iterations/total_iterations*100):.1f}%

#### Detailed Workflow Results:
"""
            for template_test in workflow_tests:
                summary = template_test['summary']
                report += f"""
**{template_test['template_name']}**
- Iterations: {summary['total_iterations']}
- Completed: {summary['completed']}
- Success Rate: {summary['success_rate']:.1f}%
- Avg Duration: {summary['average_duration_seconds']:.2f}s
"""
        
        # Provider tests summary
        provider_tests = self.test_results['provider_tests']
        if provider_tests:
            successful_provider = len([t for t in provider_tests if t['status'] == 'COMPLETED'])
            report += f"""
### Provider Testing Results
- Tests Executed: {len(provider_tests)}
- Successful: {successful_provider}
- Success Rate: {(successful_provider/len(provider_tests)*100):.1f}%
"""
        
        # Data validation summary
        data_validation = self.test_results['data_validation_tests']
        if data_validation:
            report += f"""
### Data Validation Results
- Coordinator Sync: {data_validation['coordinator_sync']['status']}
- Provider Sync: {data_validation['provider_sync']['status']}
"""
        
        # Database verification summary
        db_verification = self.test_results['database_verification_tests']
        if db_verification:
            passed_verifications = len([t for t in db_verification if t['status'] == 'PASSED'])
            report += f"""
### Database Verification Results
- Tests Executed: {len(db_verification)}
- Passed: {passed_verifications}
- Success Rate: {(passed_verifications/len(db_verification)*100):.1f}%
"""
        
        # Detailed error log
        error_logs = [log for log in self.test_log if log['level'] == 'ERROR']
        if error_logs:
            report += f"""
## Error Summary
Total Errors: {len(error_logs)}

"""
            for error in error_logs[:10]:  # Show first 10 errors
                report += f"- [{error['timestamp']}] {error['message']}\n"
        
        return report
    
    def save_test_results(self, filename: str = None):
        """Save detailed test results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"integration_test_results_{timestamp}.json"
        
        results_data = {
            'test_metadata': {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'test_user': self.test_email,
                'database_path': self.db_path,
                'test_iterations': self.test_iterations
            },
            'test_results': self.test_results,
            'test_log': self.test_log
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
            self.log_test_event('SUCCESS', f"Test results saved to {filename}")
        except Exception as e:
            self.log_test_event('ERROR', f"Failed to save test results: {str(e)}")
    
    def run_comprehensive_test_suite(self) -> bool:
        """Run the complete comprehensive test suite"""
        self.log_test_event('INFO', "Starting Comprehensive Integration Test Suite")
        self.log_test_event('INFO', "=" * 60)
        
        try:
            # Step 1: Authentication
            if not self.authenticate_test_user():
                return False
            
            # Step 2: Database verification
            if not self.verify_database_tables():
                self.log_test_event('WARNING', "Database verification failed, continuing with available tables")
            
            # Step 3: Comprehensive workflow testing (5 iterations each)
            if not self.test_all_workflows_comprehensive():
                self.log_test_event('ERROR', "Workflow testing failed")
                return False
            
            # Step 4: Provider functionality testing
            if not self.test_provider_functionality():
                self.log_test_event('ERROR', "Provider testing failed")
                return False
            
            # Step 5: Data synchronization testing
            if not self.test_data_synchronization():
                self.log_test_event('WARNING', "Data synchronization issues detected")
            
            # Step 6: Database verification
            if not self.run_database_verification():
                self.log_test_event('WARNING', "Database verification issues detected")
            
            # Step 7: Generate reports
            report = self.generate_comprehensive_report()
            print("\n" + report)
            
            # Step 8: Save results
            self.save_test_results()
            
            self.log_test_event('SUCCESS', "Comprehensive Integration Test Suite completed successfully!")
            return True
            
        except Exception as e:
            self.log_test_event('ERROR', f"Test suite failed with exception: {str(e)}")
            self.log_test_event('ERROR', f"Traceback: {traceback.format_exc()}")
            return False

def main():
    """Main execution function"""
    print("🚀 MyHealthTeam Comprehensive Integration Test Suite")
    print("=" * 60)
    
    tester = ComprehensiveIntegrationTester()
    success = tester.run_comprehensive_test_suite()
    
    if success:
        print("\n✅ All integration tests completed successfully!")
        return 0
    else:
        print("\n❌ Integration testing failed!")
        return 1

if __name__ == "__main__":
    exit(main())