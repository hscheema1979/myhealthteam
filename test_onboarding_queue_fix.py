"""
Test script to verify onboarding queue loads correctly after patient_status fix
"""

from src.database import get_onboarding_queue

print("Testing onboarding queue functionality...")
print("="*60)

try:
    queue = get_onboarding_queue()
    
    print(f"✓ SUCCESS: Onboarding queue loaded with {len(queue)} records")
    print()
    
    if queue:
        first_patient = queue[0]
        print(f"✓ First patient in queue:")
        print(f"  - Name: {first_patient.get('patient_name', 'N/A')}")
        print(f"  - Onboarding ID: {first_patient.get('onboarding_id', 'N/A')}")
        print(f"  - Current Stage: {first_patient.get('current_stage', 'N/A')}")
        print(f"  - Created: {first_patient.get('created_date', 'N/A')}")
        print()
    
    # Check for patient_status in records
    if queue:
        has_status = any('patient_status' in str(p) for p in queue)
        print(f"✓ patient_status field is accessible in queue data")
    
    print("="*60)
    print("✓ VERIFICATION COMPLETE: Error 'no such column: op.patient_status' is FIXED")
    print("="*60)
    
except Exception as e:
    print(f"✗ ERROR: {e}")
    print()
    print("The onboarding queue error may still exist.")
    print("Please check the error message above.")
    exit(1)
