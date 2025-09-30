import sys
sys.path.append('src')
import database

print("=== TESTING COORDINATOR FUNCTIONS WITH ACTUAL DATA ===")

# Test without date filtering first to see if we get any data
coordinator_id = '11'  # Known coordinator with lots of tasks

# Create a test function without date filtering
conn = database.get_db_connection()
try:
    # Simple test - get tasks for coordinator without date filter
    simple_query = """
        SELECT
            coordinator_id,
            patient_id,
            task_date,
            duration_minutes,
            task_type,
            COUNT(*) as task_count
        FROM coordinator_tasks
        WHERE coordinator_id = ?
        AND duration_minutes > 0
        GROUP BY coordinator_id, patient_id
        ORDER BY task_count DESC
        LIMIT 5
    """
    
    results = conn.execute(simple_query, (coordinator_id,)).fetchall()
    print(f"Tasks for coordinator {coordinator_id} (no date filter):")
    for row in results:
        print(f"  Patient: {row['patient_id'][:30]}... - {row['task_count']} tasks")
    
    # Test with staff code coordinator
    staff_code_coordinator = 'SobMa000'
    results2 = conn.execute(simple_query, (staff_code_coordinator,)).fetchall()
    print(f"\nTasks for coordinator {staff_code_coordinator} (no date filter):")
    for row in results2:
        print(f"  Patient: {row['patient_id'][:30]}... - {row['task_count']} tasks")
        
finally:
    conn.close()

# Test the monthly summary function
print(f"\n=== TESTING MONTHLY SUMMARY ===")
try:
    monthly_data = database.get_coordinator_monthly_summary_current_month(coordinator_id)
    print(f"Monthly summary for coordinator {coordinator_id}: {len(monthly_data)} entries")
    
    if monthly_data:
        for i, entry in enumerate(monthly_data[:3]):  # Show first 3
            print(f"  {entry['patient_name']}: {entry['total_minutes']} min - {entry['billing_code']}")
except Exception as e:
    print(f"Monthly summary error: {e}")
    import traceback
    traceback.print_exc()

print("\n✓ Basic function testing completed!")