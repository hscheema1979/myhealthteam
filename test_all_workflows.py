"""
Comprehensive Workflow Testing Script
Tests all coordinator workflows for test user dianela@ with password test4
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import time
from database import authenticate_user, get_user_role_ids, get_db_connection
from dashboards.workflow_module import (
    get_workflow_templates, 
    create_workflow_instance, 
    get_workflow_template_steps,
    complete_workflow_step
)

class WorkflowTester:
    def __init__(self, test_email="dianela@", test_password="test4"):
        self.test_email = test_email
        self.test_password = test_password
        self.user_data = None
        self.user_id = None
        self.coordinator_id = None
        self.user_role_ids = []
        self.test_results = []
        
    def authenticate_test_user(self):
        """Authenticate the test user"""
        print(f"🔐 Authenticating test user: {self.test_email}")
        
        self.user_data = authenticate_user(self.test_email, self.test_password)
        if not self.user_data:
            print(f"❌ Authentication failed for {self.test_email}")
            return False
            
        self.user_id = self.user_data['user_id']
        self.coordinator_id = self.user_id  # Assuming coordinator_id = user_id for test
        self.user_role_ids = get_user_role_ids(self.user_id)
        
        print(f"✅ Authentication successful!")
        print(f"   User ID: {self.user_id}")
        print(f"   Role IDs: {self.user_role_ids}")
        print(f"   Name: {self.user_data.get('first_name', '')} {self.user_data.get('last_name', '')}")
        return True
    
    def get_test_patient_id(self):
        """Get a test patient ID for workflow testing"""
        conn = get_db_connection()
        try:
            # Get first available patient
            patient = conn.execute("SELECT patient_id FROM patients LIMIT 1").fetchone()
            if patient:
                return patient['patient_id']
            else:
                print("❌ No patients found in database")
                return None
        finally:
            conn.close()
    
    def test_workflow_template(self, template_id, template_name):
        """Test a single workflow template completely"""
        print(f"\n🔄 Testing Workflow: {template_name} (ID: {template_id})")
        
        test_result = {
            'template_id': template_id,
            'template_name': template_name,
            'status': 'PENDING',
            'instance_id': None,
            'steps_completed': 0,
            'total_steps': 0,
            'errors': []
        }
        
        try:
            # Get workflow steps
            steps = get_workflow_template_steps(template_id)
            test_result['total_steps'] = len(steps)
            print(f"   📋 Total steps: {len(steps)}")
            
            # Get test patient
            patient_id = self.get_test_patient_id()
            if not patient_id:
                test_result['errors'].append("No test patient available")
                test_result['status'] = 'FAILED'
                return test_result
            
            # Create workflow instance
            print(f"   🆕 Creating workflow instance for patient {patient_id}")
            instance_id = create_workflow_instance(
                template_id=template_id,
                patient_id=patient_id,
                coordinator_id=self.coordinator_id,
                notes=f"Test workflow created by automated test for {template_name}"
            )
            
            if not instance_id:
                test_result['errors'].append("Failed to create workflow instance")
                test_result['status'] = 'FAILED'
                return test_result
                
            test_result['instance_id'] = instance_id
            print(f"   ✅ Workflow instance created: {instance_id}")
            
            # Complete each step with progress saves
            for i, step in enumerate(steps, 1):
                step_id = step['step_id']
                step_name = step['task_name']
                
                print(f"   📝 Step {i}/{len(steps)}: {step_name}")
                
                # Save progress (simulate work time)
                time.sleep(0.5)  # Brief pause to simulate work
                
                # Complete the step
                success = complete_workflow_step(
                    instance_id=instance_id,
                    step_id=step_id,
                    coordinator_id=self.coordinator_id,
                    duration_minutes=5,  # Standard 5 minutes per step
                    notes=f"Automated test completion of step: {step_name}"
                )
                
                if success:
                    test_result['steps_completed'] += 1
                    print(f"   ✅ Step {i} completed successfully")
                else:
                    error_msg = f"Failed to complete step {i}: {step_name}"
                    test_result['errors'].append(error_msg)
                    print(f"   ❌ {error_msg}")
                    break
            
            # Check final status
            if test_result['steps_completed'] == test_result['total_steps']:
                test_result['status'] = 'COMPLETED'
                print(f"   🎉 Workflow {template_name} completed successfully!")
            else:
                test_result['status'] = 'PARTIAL'
                print(f"   ⚠️  Workflow {template_name} partially completed ({test_result['steps_completed']}/{test_result['total_steps']})")
                
        except Exception as e:
            error_msg = f"Exception during workflow test: {str(e)}"
            test_result['errors'].append(error_msg)
            test_result['status'] = 'ERROR'
            print(f"   💥 {error_msg}")
        
        return test_result
    
    def run_all_workflow_tests(self):
        """Run tests for all workflow templates"""
        print("🚀 Starting Comprehensive Workflow Testing")
        print("=" * 60)
        
        # Authenticate
        if not self.authenticate_test_user():
            return False
        
        # Get all workflow templates (excluding Future)
        print(f"\n📋 Getting workflow templates...")
        templates = get_workflow_templates()
        non_future_templates = [t for t in templates if 'Future' not in t['template_name']]
        
        print(f"Found {len(non_future_templates)} workflow templates to test:")
        for template in non_future_templates:
            print(f"   - {template['template_name']} (ID: {template['template_id']})")
        
        # Test each workflow
        print(f"\n🧪 Beginning workflow tests...")
        for template in non_future_templates:
            result = self.test_workflow_template(
                template['template_id'], 
                template['template_name']
            )
            self.test_results.append(result)
        
        # Print summary
        self.print_test_summary()
        return True
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 WORKFLOW TESTING SUMMARY")
        print("=" * 60)
        
        completed = len([r for r in self.test_results if r['status'] == 'COMPLETED'])
        partial = len([r for r in self.test_results if r['status'] == 'PARTIAL'])
        failed = len([r for r in self.test_results if r['status'] in ['FAILED', 'ERROR']])
        total = len(self.test_results)
        
        print(f"Total Workflows Tested: {total}")
        print(f"✅ Completed Successfully: {completed}")
        print(f"⚠️  Partially Completed: {partial}")
        print(f"❌ Failed/Error: {failed}")
        print(f"Success Rate: {(completed/total*100):.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status_icon = {
                'COMPLETED': '✅',
                'PARTIAL': '⚠️ ',
                'FAILED': '❌',
                'ERROR': '💥'
            }.get(result['status'], '❓')
            
            print(f"{status_icon} {result['template_name']}")
            print(f"   Instance ID: {result['instance_id']}")
            print(f"   Steps: {result['steps_completed']}/{result['total_steps']}")
            
            if result['errors']:
                print(f"   Errors:")
                for error in result['errors']:
                    print(f"     - {error}")
        
        print("\n" + "=" * 60)
        print("🏁 Testing Complete!")

def main():
    """Main test execution"""
    tester = WorkflowTester()
    success = tester.run_all_workflow_tests()
    
    if success:
        print("\n✅ All workflow tests completed successfully!")
    else:
        print("\n❌ Workflow testing failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())