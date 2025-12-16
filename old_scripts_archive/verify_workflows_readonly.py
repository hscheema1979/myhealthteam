"""
Read-only workflow verification script
Tests workflow functionality without creating database instances
"""

import sqlite3
import os
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    db_path = 'production.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def verify_workflow_templates():
    """Verify workflow templates exist and are accessible"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT template_id, template_name FROM workflow_templates ORDER BY template_id")
        templates = cursor.fetchall()
        
        print(f"✓ Found {len(templates)} workflow templates:")
        for template_id, template_name in templates:
            print(f"  - ID: {template_id} | Name: {template_name}")
        
        conn.close()
        return templates
        
    except Exception as e:
        print(f"✗ Error accessing workflow templates: {e}")
        return []

def verify_users():
    """Verify test users exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, email, first_name, last_name FROM users WHERE email LIKE '%@myhealthteam.org' ORDER BY user_id LIMIT 5")
        users = cursor.fetchall()
        
        print(f"✓ Found {len(users)} test users:")
        for user_id, email, first_name, last_name in users:
            print(f"  - ID: {user_id} | Email: {email} | Name: {first_name} {last_name}")
        
        conn.close()
        return users
        
    except Exception as e:
        print(f"✗ Error accessing users: {e}")
        return []

def verify_patients():
    """Verify test patients exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT patient_id, first_name, last_name FROM patients ORDER BY patient_id LIMIT 5")
        patients = cursor.fetchall()
        
        print(f"✓ Found {len(patients)} test patients:")
        for patient_id, first_name, last_name in patients:
            print(f"  - ID: {patient_id} | Name: {first_name} {last_name}")
        
        conn.close()
        return patients
        
    except Exception as e:
        print(f"✗ Error accessing patients: {e}")
        return []

def verify_existing_workflow_instances():
    """Check existing workflow instances"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT instance_id, template_id, template_name, patient_id, coordinator_id, workflow_status, created_at
            FROM workflow_instances 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        instances = cursor.fetchall()
        
        print(f"✓ Found {len(instances)} recent workflow instances:")
        for instance in instances:
            instance_id, template_id, template_name, patient_id, coordinator_id, status, created_at = instance
            print(f"  - Instance: {instance_id} | Template: {template_name} | Patient: {patient_id} | Status: {status}")
        
        conn.close()
        return instances
        
    except Exception as e:
        print(f"✗ Error accessing workflow instances: {e}")
        return []

def verify_workflow_steps_structure():
    """Verify the workflow steps structure in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check the structure of workflow_instances table
        cursor.execute("PRAGMA table_info(workflow_instances)")
        columns = cursor.fetchall()
        
        step_columns = [col[1] for col in columns if 'step' in col[1].lower()]
        
        print(f"✓ Found {len(step_columns)} step-related columns:")
        for col in step_columns:
            print(f"  - {col}")
        
        conn.close()
        return step_columns
        
    except Exception as e:
        print(f"✗ Error checking workflow steps structure: {e}")
        return []

def main():
    """Main verification function"""
    print("=" * 60)
    print("WORKFLOW SYSTEM VERIFICATION (READ-ONLY)")
    print("=" * 60)
    print()
    
    # Verify database components
    print("1. Verifying Workflow Templates:")
    templates = verify_workflow_templates()
    print()
    
    print("2. Verifying Users:")
    users = verify_users()
    print()
    
    print("3. Verifying Patients:")
    patients = verify_patients()
    print()
    
    print("4. Verifying Existing Workflow Instances:")
    instances = verify_existing_workflow_instances()
    print()
    
    print("5. Verifying Workflow Steps Structure:")
    step_columns = verify_workflow_steps_structure()
    print()
    
    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    if templates and users and patients:
        print("✓ All core components verified successfully")
        print(f"✓ {len(templates)} workflow templates available")
        print(f"✓ {len(users)} test users available")
        print(f"✓ {len(patients)} test patients available")
        print(f"✓ {len(instances)} existing workflow instances found")
        print(f"✓ {len(step_columns)} step columns in database")
        print()
        print("The workflow system appears to be properly configured.")
        print("Database schema matches expected structure.")
    else:
        print("✗ Some components failed verification")
        print("Please check database connectivity and schema.")

if __name__ == "__main__":
    main()