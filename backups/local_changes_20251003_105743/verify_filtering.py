#!/usr/bin/env python3
"""
Verification script to check that completed patients are filtered out of the onboarding queue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import get_onboarding_queue

def main():
    print("Checking onboarding queue for completed patients...")
    
    # Get the current onboarding queue
    queue = get_onboarding_queue()
    
    print(f"\nTotal patients in onboarding queue: {len(queue)}")
    
    # Check if any completed patients are in the queue
    completed_patients = []
    for patient in queue:
        if patient.get('stage5_complete') == 1:
            completed_patients.append(patient)
    
    print(f"Completed patients in queue (should be 0): {len(completed_patients)}")
    
    if completed_patients:
        print("\nWARNING: Found completed patients in queue:")
        for patient in completed_patients:
            print(f"  - {patient.get('first_name')} {patient.get('last_name')} (ID: {patient.get('onboarding_id')})")
    else:
        print("\n✓ SUCCESS: No completed patients found in queue")
    
    # Show first few patients in queue for verification
    print(f"\nFirst 5 patients in queue:")
    for i, patient in enumerate(queue[:5]):
        stage5_status = "Complete" if patient.get('stage5_complete') == 1 else "Incomplete"
        print(f"  {i+1}. {patient.get('first_name')} {patient.get('last_name')} - Stage 5: {stage5_status}")

if __name__ == "__main__":
    main()