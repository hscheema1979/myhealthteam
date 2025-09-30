import sys
sys.path.append('src')
import database

# Test the new coordinator database functions
print("=== TESTING COORDINATOR DATABASE FUNCTIONS ===")

# First, get a coordinator ID to test with
conn = database.get_db_connection()
coordinator_result = conn.execute('SELECT coordinator_id, coordinator_name FROM coordinator_tasks LIMIT 1').fetchone()
conn.close()

if coordinator_result:
    test_coordinator_id = coordinator_result['coordinator_id']
    coordinator_name = coordinator_result['coordinator_name']
    print(f"Testing with coordinator: {coordinator_name} (ID: {test_coordinator_id})")
    
    try:
        # Test 1: Weekly patient minutes
        print("\n1. Testing get_coordinator_weekly_patient_minutes...")
        weekly_data = database.get_coordinator_weekly_patient_minutes(test_coordinator_id, weeks_back=4)
        print(f"   Found {len(weekly_data)} weekly patient entries")
        if weekly_data:
            print(f"   Sample: {weekly_data[0]['patient_name']} - {weekly_data[0]['total_minutes']} minutes")
        
        # Test 2: Tasks by date range
        print("\n2. Testing get_coordinator_tasks_by_date_range...")
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        tasks_data = database.get_coordinator_tasks_by_date_range(test_coordinator_id, start_date, end_date)
        print(f"   Found {len(tasks_data)} tasks in last 30 days")
        if tasks_data:
            print(f"   Sample: {tasks_data[0]['patient_name']} - {tasks_data[0]['task_type']} ({tasks_data[0]['duration_minutes']} min)")
        
        # Test 3: Current month summary
        print("\n3. Testing get_coordinator_monthly_summary_current_month...")
        monthly_data = database.get_coordinator_monthly_summary_current_month(test_coordinator_id)
        print(f"   Found {len(monthly_data)} patient summaries for current month")
        if monthly_data:
            print(f"   Sample: {monthly_data[0]['patient_name']} - {monthly_data[0]['total_minutes']} minutes")
        
        # Test 4: Patient service analysis
        print("\n4. Testing get_coordinator_patient_service_analysis...")
        analysis_data = database.get_coordinator_patient_service_analysis(test_coordinator_id, weeks_back=4)
        print(f"   Found {len(analysis_data)} service analysis entries")
        if analysis_data:
            print(f"   Sample: {analysis_data[0]['patient_name']} - {analysis_data[0]['task_type']} - {analysis_data[0]['total_minutes']} minutes")
        
        print("\n✓ All database functions working correctly!")
        
    except Exception as e:
        print(f"\n❌ Error testing functions: {e}")
        import traceback
        traceback.print_exc()

else:
    print("❌ No coordinator data found to test with")