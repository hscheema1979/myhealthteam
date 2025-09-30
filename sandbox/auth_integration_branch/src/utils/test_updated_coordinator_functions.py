import sys
sys.path.append('src')
import database

print("=== TESTING UPDATED COORDINATOR DATABASE FUNCTIONS ===")

# Test with numeric coordinator_id
numeric_coordinator_id = '11'
print(f"\n1. Testing with NUMERIC coordinator_id: {numeric_coordinator_id}")

try:
    weekly_data = database.get_coordinator_weekly_patient_minutes(numeric_coordinator_id, weeks_back=4)
    print(f"   Weekly patient minutes: {len(weekly_data)} entries")
    if weekly_data:
        print(f"   Sample: {weekly_data[0]['patient_name']} - {weekly_data[0]['total_minutes']} minutes")
except Exception as e:
    print(f"   Error: {e}")

# Test with staff code coordinator_id  
staff_code_coordinator_id = 'SobMa000'
print(f"\n2. Testing with STAFF CODE coordinator_id: {staff_code_coordinator_id}")

try:
    weekly_data = database.get_coordinator_weekly_patient_minutes(staff_code_coordinator_id, weeks_back=4)
    print(f"   Weekly patient minutes: {len(weekly_data)} entries")
    if weekly_data:
        print(f"   Sample: {weekly_data[0]['patient_name']} - {weekly_data[0]['total_minutes']} minutes")
except Exception as e:
    print(f"   Error: {e}")

# Test the service analysis function
print(f"\n3. Testing service analysis with mixed coordinator types:")

try:
    # Test with numeric ID
    analysis_numeric = database.get_coordinator_patient_service_analysis(numeric_coordinator_id, weeks_back=4)
    print(f"   Numeric coordinator analysis: {len(analysis_numeric)} entries")
    
    # Test with staff code
    analysis_staff = database.get_coordinator_patient_service_analysis(staff_code_coordinator_id, weeks_back=4)
    print(f"   Staff code coordinator analysis: {len(analysis_staff)} entries")
    
    if analysis_numeric:
        print(f"   Sample numeric: {analysis_numeric[0]['coordinator_name']} - {analysis_numeric[0]['patient_name']}")
    if analysis_staff:
        print(f"   Sample staff code: {analysis_staff[0]['coordinator_name']} - {analysis_staff[0]['patient_name']}")
        
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✓ Testing completed!")