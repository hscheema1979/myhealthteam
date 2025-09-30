"""
Comprehensive workflow testing script for all coordinator workflows.
Tests each workflow systematically with progress saves at each step.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_connection
import sqlite3
from datetime import datetime

def authenticate_test_user():
    """Authenticate the test user dianela@"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if test user exists
        cursor.execute("SELECT user_id, email FROM users WHERE email = ?", ("dianela@",))
        user = cursor.fetchone()
        
        if user:
            print(f"✓ Test user authenticated: {user[1]} (ID: {user[0]})")
            conn.close()
            return user[0]
        else:
            print("✗ Test user 'dianela@' not found")
            conn.close()
            return None
            
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return None

def get_test_patient():
    """Get a test patient ID for workflow testing"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get first available patient
        cursor.execute("SELECT patient_id, first_name, last_name FROM patients LIMIT 1")
        patient = cursor.fetchone()
        
        if patient:
            print(f"✓ Test patient: {patient[1]} {patient[2]} (ID: {patient[0]})")
            conn.close()
            return patient[0]
        else:
            print("✗ No test patients found")
            conn.close()
            return None
            
    except Exception as e:
        print(f"✗ Error getting test patient: {e}")
        return None

def get_workflow_templates():
    """Get all workflow templates excluding Future workflows"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT workflow_template_id, workflow_name 
            FROM workflow_templates 
            WHERE workflow_name NOT LIKE '%Future%'
            ORDER BY workflow_name
        """)
        
        templates = cursor.fetchall()
        conn.close()
        return templates
        
    except Exception as e:
        print(f"✗ Error getting workflow templates: {e}")
        return []

def create_workflow_instance(user_id, patient_id, template_id, template_name):
    """Create a new workflow instance"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create workflow instance
        cursor.execute("""
            INSERT INTO workflow_instances 
            (workflow_template_id, patient_id, assigned_user_id, status, created_at)
            VALUES (?, ?, ?, 'active', ?)
        """, (template_id, patient_id, user_id, datetime.now()))
        
        workflow_instance_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"  ✓ Created workflow instance ID: {workflow_instance_id}")
        return workflow_instance_id
        
    except Exception as e:
        print(f"  ✗ Error creating workflow instance: {e}")
        return None

def get_workflow_steps(template_id):
    """Get all steps for a workflow template"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT step_id, step_name, step_order 
            FROM workflow_steps 
            WHERE workflow_template_id = ?
            ORDER BY step_order
        """, (template_id,))
        
        steps = cursor.fetchall()
        conn.close()
        return steps
        
    except Exception as e:
        print(f"  ✗ Error getting workflow steps: {e}")
        return []

def complete_workflow_step(workflow_instance_id, step_id, step_name):
    """Complete a workflow step with progress save"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if step instance already exists
        cursor.execute("""
            SELECT step_instance_id FROM workflow_step_instances 
            WHERE workflow_instance_id = ? AND step_id = ?
        """, (workflow_instance_id, step_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing step instance
            cursor.execute("""
                UPDATE workflow_step_instances 
                SET status = 'completed', completed_at = ?
                WHERE step_instance_id = ?
            """, (datetime.now(), existing[0]))
        else:
            # Create new step instance
            cursor.execute("""
                INSERT INTO workflow_step_instances 
                (workflow_instance_id, step_id, status, started_at, completed_at)
                VALUES (?, ?, 'completed', ?, ?)
            """, (workflow_instance_id, step_id, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
        
        print(f"    ✓ Completed step: {step_name}")
        return True
        
    except Exception as e:
        print(f"    ✗ Error completing step '{step_name}': {e}")
        return False

def complete_workflow(workflow_instance_id):
    """Mark workflow as completed"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE workflow_instances 
            SET status = 'completed', completed_at = ?
            WHERE workflow_instance_id = ?
        """, (datetime.now(), workflow_instance_id))
        
        conn.commit()
        conn.close()
        
        print(f"  ✓ Workflow marked as completed")
        return True
        
    except Exception as e:
        print(f"  ✗ Error completing workflow: {e}")
        return False

def test_workflow(user_id, patient_id, template_id, template_name):
    """Test a complete workflow from start to finish"""
    print(f"\n{'='*60}")
    print(f"Testing Workflow: {template_name}")
    print(f"{'='*60}")
    
    # Create workflow instance
    workflow_instance_id = create_workflow_instance(user_id, patient_id, template_id, template_name)
    if not workflow_instance_id:
        return {"success": False, "error": "Failed to create workflow instance"}
    
    # Get workflow steps
    steps = get_workflow_steps(template_id)
    if not steps:
        return {"success": False, "error": "No workflow steps found"}
    
    print(f"  Found {len(steps)} steps to complete")
    
    # Complete each step
    completed_steps = 0
    failed_steps = []
    
    for step_id, step_name, step_order in steps:
        success = complete_workflow_step(workflow_instance_id, step_id, step_name)
        if success:
            completed_steps += 1
        else:
            failed_steps.append(step_name)
    
    # Mark workflow as completed if all steps succeeded
    workflow_completed = False
    if completed_steps == len(steps):
        workflow_completed = complete_workflow(workflow_instance_id)
    
    result = {
        "success": workflow_completed,
        "workflow_instance_id": workflow_instance_id,
        "total_steps": len(steps),
        "completed_steps": completed_steps,
        "failed_steps": failed_steps,
        "workflow_completed": workflow_completed
    }
    
    print(f"  Result: {completed_steps}/{len(steps)} steps completed")
    if failed_steps:
        print(f"  Failed steps: {', '.join(failed_steps)}")
    
    return result

def main():
    """Main testing function"""
    print("Starting Comprehensive Workflow Testing")
    print("=" * 60)
    
    # Authenticate test user
    user_id = authenticate_test_user()
    if not user_id:
        print("Cannot proceed without valid test user")
        return
    
    # Get test patient
    patient_id = get_test_patient()
    if not patient_id:
        print("Cannot proceed without valid test patient")
        return
    
    # Get workflow templates
    templates = get_workflow_templates()
    if not templates:
        print("No workflow templates found")
        return
    
    print(f"\nFound {len(templates)} workflow templates to test")
    
    # Test each workflow
    results = []
    successful_workflows = 0
    
    for template_id, template_name in templates:
        result = test_workflow(user_id, patient_id, template_id, template_name)
        result["template_name"] = template_name
        result["template_id"] = template_id
        results.append(result)
        
        if result["success"]:
            successful_workflows += 1
    
    # Print comprehensive summary
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE TESTING SUMMARY")
    print(f"{'='*60}")
    print(f"Total workflows tested: {len(templates)}")
    print(f"Successful workflows: {successful_workflows}")
    print(f"Failed workflows: {len(templates) - successful_workflows}")
    print(f"Success rate: {(successful_workflows/len(templates)*100):.1f}%")
    
    print(f"\nDetailed Results:")
    print("-" * 60)
    
    for result in results:
        status = "✓ PASS" if result["success"] else "✗ FAIL"
        print(f"{status} | {result['template_name']}")
        print(f"     Steps: {result['completed_steps']}/{result['total_steps']}")
        if result['failed_steps']:
            print(f"     Failed: {', '.join(result['failed_steps'])}")
        print(f"     Instance ID: {result['workflow_instance_id']}")
        print()

if __name__ == "__main__":
    main()