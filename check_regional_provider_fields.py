import sys
sys.path.append('src')
import database

# Check for regional provider related fields in onboarding_patients table
conn = database.get_db_connection()
cursor = conn.cursor()

# Get table structure
cursor.execute('PRAGMA table_info(onboarding_patients)')
columns = cursor.fetchall()

print('=== ONBOARDING_PATIENTS TABLE STRUCTURE ===')
regional_fields = []
for col in columns:
    col_name = col[1].lower()
    if any(term in col_name for term in ['regional', 'provider', 'assign']):
        regional_fields.append(col[1])
        print(f'{col[1]} - {col[2]}')

print(f'\n=== REGIONAL/PROVIDER RELATED FIELDS ===')
for field in regional_fields:
    print(field)

# Check Test11 data for these fields
print(f'\n=== TEST11 DATA FOR PROVIDER FIELDS ===')
query = """SELECT patient_id, facility_assignment, assigned_pot_user_id, 
           assigned_provider_user_id, assigned_coordinator_user_id 
           FROM onboarding_patients WHERE patient_id LIKE '%Test11%'"""
cursor.execute(query)
test11_data = cursor.fetchone()
if test11_data:
    print(f'Patient ID: {test11_data[0]}')
    print(f'Facility Assignment: {test11_data[1]}')
    print(f'POT User ID: {test11_data[2]}')
    print(f'Provider User ID: {test11_data[3]}')
    print(f'Coordinator User ID: {test11_data[4]}')

# Check if there's an assigned_regional_provider_user_id field
try:
    cursor.execute("SELECT assigned_regional_provider_user_id FROM onboarding_patients WHERE patient_id LIKE '%Test11%' LIMIT 1")
    regional_data = cursor.fetchone()
    print(f'Regional Provider User ID: {regional_data[0] if regional_data else "Field exists but no data"}')
except Exception as e:
    print(f'No assigned_regional_provider_user_id field found: {e}')

# Check what users have role "CP" (Care Provider)
print(f'\n=== USERS WITH ROLE CP (CARE PROVIDERS) ===')
try:
    cp_users = database.get_users_by_role("CP")
    for user in cp_users:
        print(f"User ID: {user['user_id']}, Name: {user['full_name']}, Username: {user['username']}")
except Exception as e:
    print(f'Error getting CP users: {e}')

conn.close()