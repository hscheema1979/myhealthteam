#!/usr/bin/env python3
"""
Test script to verify onboarding dashboard can access the newly copied workflow tables
"""

import sqlite3
import sys

def test_onboarding_dashboard_queries():
    """Test the key queries that onboarding dashboard would execute"""
    
    db_path = "production.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("Testing Onboarding Dashboard Database Access")
        print("=" * 50)
        
        # Test 1: Check if onboarding_tasks table exists and has data
        print("1. Testing onboarding_tasks table access...")
        try:
            result = cursor.execute("SELECT COUNT(*) as count FROM onboarding_tasks").fetchone()
            print(f"   ✅ onboarding_tasks accessible: {result['count']} rows")
        except Exception as e:
            print(f"   ❌ onboarding_tasks error: {e}")
            return False
            
        # Test 2: Check if workflow_instances table exists and has data
        print("2. Testing workflow_instances table access...")
        try:
            result = cursor.execute("SELECT COUNT(*) as count FROM workflow_instances").fetchone()
            print(f"   ✅ workflow_instances accessible: {result['count']} rows")
        except Exception as e:
            print(f"   ❌ workflow_instances error: {e}")
            return False
            
        # Test 3: Check if workflow_steps table exists and has data
        print("3. Testing workflow_steps table access...")
        try:
            result = cursor.execute("SELECT COUNT(*) as count FROM workflow_steps").fetchone()
            print(f"   ✅ workflow_steps accessible: {result['count']} rows")
        except Exception as e:
            print(f"   ❌ workflow_steps error: {e}")
            return False
            
        # Test 4: Test a typical onboarding dashboard query
        print("4. Testing typical onboarding dashboard query...")
        try:
            query = """
                SELECT
                    op.patient_id,
                    op.first_name,
                    op.last_name,
                    op.eligibility_status as patient_status,
                    COUNT(ot.task_id) as pending_tasks,
                    COUNT(CASE WHEN ot.status = 'completed' THEN 1 END) as completed_tasks
                FROM onboarding_patients op
                LEFT JOIN onboarding_tasks ot ON op.onboarding_id = ot.onboarding_id
                WHERE op.eligibility_status = 'Active'
                GROUP BY op.patient_id, op.first_name, op.last_name, op.eligibility_status
                LIMIT 5
            """
            results = cursor.execute(query).fetchall()
            print(f"   ✅ Onboarding query successful: {len(results)} patients found")
            for row in results:
                print(f"      Patient: {row['first_name']} {row['last_name']} - Pending: {row['pending_tasks']}, Completed: {row['completed_tasks']}")
        except Exception as e:
            print(f"   ❌ Onboarding query error: {e}")
            return False
            
        # Test 5: Test workflow tracking query
        print("5. Testing workflow tracking query...")
        try:
            query = """
                SELECT
                    wi.instance_id,
                    wi.patient_id,
                    wi.workflow_status,
                    COUNT(ws.step_id) as total_steps,
                    (wi.step1_complete + wi.step2_complete + wi.step3_complete +
                     wi.step4_complete + wi.step5_complete + wi.step6_complete) as completed_steps
                FROM workflow_instances wi
                LEFT JOIN workflow_steps ws ON wi.current_step = ws.step_id
                WHERE wi.workflow_status = 'Active'
                GROUP BY wi.instance_id, wi.patient_id, wi.workflow_status
                LIMIT 3
            """
            results = cursor.execute(query).fetchall()
            print(f"   ✅ Workflow tracking query successful: {len(results)} active workflows")
            for row in results:
                print(f"      Workflow {row['instance_id']}: Patient {row['patient_id']} - {row['completed_steps']}/{row['total_steps']} steps completed")
        except Exception as e:
            print(f"   ❌ Workflow tracking query error: {e}")
            return False
            
        print("\n" + "=" * 50)
        print("✅ All onboarding dashboard access tests passed!")
        print("✅ Critical workflow infrastructure tables are accessible")
        print("✅ Onboarding dashboard should now load successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = test_onboarding_dashboard_queries()
    sys.exit(0 if success else 1)