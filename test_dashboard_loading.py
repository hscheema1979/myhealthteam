#!/usr/bin/env python3
"""
Test script to verify all dashboard roles can load without database errors
"""

import sqlite3
import sys
import importlib.util

def test_dashboard_loading():
    """Test loading each dashboard role to check for database errors"""
    
    db_path = "production.db"
    
    # Get current year and month for table names
    from datetime import datetime
    current_date = datetime.now()
    year_month = f"{current_date.year}_{current_date.month:02d}"
    
    # Test queries that each dashboard would typically execute
    dashboard_queries = {
        'Provider': [
            f"SELECT COUNT(*) as count FROM provider_tasks_{year_month}",
            "SELECT COUNT(*) as count FROM patients",
            "SELECT COUNT(*) as count FROM patient_assignments"
        ],
        'Coordinator': [
            f"SELECT COUNT(*) as count FROM coordinator_tasks_{year_month}",
            "SELECT COUNT(*) as count FROM patients",
            "SELECT COUNT(*) as count FROM coordinator_monthly_summary"
        ],
        'Admin': [
            "SELECT COUNT(*) as count FROM users",
            "SELECT COUNT(*) as count FROM user_roles",
            "SELECT COUNT(*) as count FROM facilities"
        ],
        'Onboarding': [
            "SELECT COUNT(*) as count FROM onboarding_patients",
            "SELECT COUNT(*) as count FROM onboarding_tasks",
            "SELECT COUNT(*) as count FROM workflow_instances"
        ],
        'Data Entry': [
            "SELECT COUNT(*) as count FROM patients",
            "SELECT COUNT(*) as count FROM patient_panel",
            "SELECT COUNT(*) as count FROM facilities"
        ]
    }
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("Testing Dashboard Loading for All Roles")
        print("=" * 50)
        
        all_passed = True
        
        for role, queries in dashboard_queries.items():
            print(f"\nTesting {role} Dashboard:")
            role_passed = True
            
            for query in queries:
                try:
                    result = cursor.execute(query).fetchone()
                    table_name = query.split("FROM ")[1].split(" ")[0]
                    count = result['count']
                    print(f"   ✅ {table_name}: {count} records")
                except Exception as e:
                    print(f"   ❌ {table_name}: {e}")
                    role_passed = False
                    all_passed = False
            
            if role_passed:
                print(f"   ✅ {role} dashboard queries successful")
            else:
                print(f"   ❌ {role} dashboard has query errors")
        
        # Test role-specific complex queries
        print(f"\nTesting Complex Dashboard Queries:")
        
        # Provider complex query
        try:
            query = f"""
                SELECT
                    u.user_id,
                    u.full_name,
                    COUNT(DISTINCT pa.patient_id) as assigned_patients,
                    COUNT(DISTINCT CASE WHEN pt.status = 'pending' THEN pt.provider_task_id END) as pending_tasks,
                    COUNT(DISTINCT CASE WHEN pt.status = 'completed' THEN pt.provider_task_id END) as completed_tasks
                FROM users u
                LEFT JOIN patient_assignments pa ON u.user_id = pa.provider_id
                LEFT JOIN provider_tasks_{year_month} pt ON u.user_id = pt.provider_id
                WHERE u.user_id IN (SELECT user_id FROM user_roles WHERE role_id = 33)
                GROUP BY u.user_id, u.full_name
                LIMIT 5
            """
            results = cursor.execute(query).fetchall()
            print(f"   ✅ Provider performance query: {len(results)} providers found")
        except Exception as e:
            print(f"   ❌ Provider performance query: {e}")
            all_passed = False
        
        # Coordinator complex query
        try:
            query = f"""
                SELECT
                    u.user_id,
                    u.full_name,
                    COUNT(DISTINCT pa.patient_id) as assigned_patients,
                    COUNT(DISTINCT CASE WHEN ct.submission_status = 'pending' THEN ct.coordinator_task_id END) as pending_tasks,
                    COUNT(DISTINCT CASE WHEN ct.submission_status = 'completed' THEN ct.coordinator_task_id END) as completed_tasks
                FROM users u
                LEFT JOIN patient_assignments pa ON u.user_id = pa.coordinator_id
                LEFT JOIN coordinator_tasks_{year_month} ct ON u.user_id = ct.coordinator_id
                WHERE u.user_id IN (SELECT user_id FROM user_roles WHERE role_id = 36)
                GROUP BY u.user_id, u.full_name
                LIMIT 5
            """
            results = cursor.execute(query).fetchall()
            print(f"   ✅ Coordinator performance query: {len(results)} coordinators found")
        except Exception as e:
            print(f"   ❌ Coordinator performance query: {e}")
            all_passed = False
        
        # Onboarding complex query
        try:
            query = """
                SELECT 
                    op.patient_id,
                    op.first_name,
                    op.last_name,
                    op.eligibility_status,
                    COUNT(ot.task_id) as total_tasks,
                    COUNT(CASE WHEN ot.status = 'completed' THEN 1 END) as completed_tasks
                FROM onboarding_patients op
                LEFT JOIN onboarding_tasks ot ON op.onboarding_id = ot.onboarding_id
                GROUP BY op.patient_id, op.first_name, op.last_name, op.eligibility_status
                LIMIT 5
            """
            results = cursor.execute(query).fetchall()
            print(f"   ✅ Onboarding patient query: {len(results)} patients found")
        except Exception as e:
            print(f"   ❌ Onboarding patient query: {e}")
            all_passed = False
        
        print("\n" + "=" * 50)
        if all_passed:
            print("✅ All dashboard loading tests passed!")
            print("✅ All role-based dashboards should load successfully")
            return True
        else:
            print("❌ Some dashboard queries failed")
            print("❌ Dashboard loading may have issues")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = test_dashboard_loading()
    sys.exit(0 if success else 1)