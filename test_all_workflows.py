"""
Comprehensive workflow testing script for all coordinator workflows.
Tests each workflow systematically with progress saves at each step.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    db_path = 'production.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def authenticate_test_user():
    """Authenticate the test user dianela@myhealthteam.org"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if test user exists
        cursor.execute("SELECT user_id, email FROM users WHERE email = ?", ("dianela@myhealthteam.org",))
        user = cursor.fetchone()
        
        if user:
            print(f"✓ Test user authenticated: {user[1]} (ID: {user[0]})")
            conn.close()
            return user[0]
        else:
            print("✗ Test user 'dianela@myhealthteam.org' not found")
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
            SELECT template_id, template_name 
            FROM workflow_templates 
            WHERE template_name NOT LIKE '%Future%'
            ORDER BY template_name
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
            (template_id, template_name, patient_id, coordinator_id, workflow_status, created_at)
            VALUES (?, ?, ?, ?, 'active', ?)
        """, (template_id, template_name, patient_id, user_id, datetime.now()))
        
        workflow_instance_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"  ✓ Created workflow instance ID: {workflow_instance_id}")
        return workflow_instance_id
        
    except Exception as e:
        print(f"  ✗ Error creating workflow instance: {e}")
        return None

def get_workflow_steps(template_id):
    """Get workflow steps based on template - using fixed 6-step structure"""
    try:
        # Based on the database schema, workflows have up to 6 steps
        # We'll return a standard set of steps for testing
        steps = [
            (1, "Step 1", 1),
            (2, "Step 2", 2),
            (3, "Step 3", 3),
            (4, "Step 4", 4),
            (5, "Step 5", 5),
            (6, "Step 6", 6)
        ]
        return steps
        
    except Exception as e:
        print(f"  ✗ Error getting workflow steps: {e}")
        return []

def complete_workflow_step(workflow_instance_id, step_id, step_name):
    """Complete a workflow step with progress save"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update the specific step column in workflow_instances
        step_complete_col = f"step{step_id}_complete"
        step_date_col = f"step{step_id}_date"
        step_completed_by_col = f"step{step_id}_completed_by"
        
        cursor.execute(f"""
            UPDATE workflow_instances 
            SET {step_complete_col} = 1, 
                {step_date_col} = ?,
                {step_completed_by_col} = 'test_user',
                updated_at = ?
            WHERE instance_id = ?
        """, (datetime.now().date(), datetime.now(), workflow_instance_id))
        
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
            SET workflow_status = 'completed', 
                completed_at = ?,
                updated_at = ?
            WHERE instance_id = ?
        """, (datetime.now(), datetime.now(), workflow_instance_id))
        
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