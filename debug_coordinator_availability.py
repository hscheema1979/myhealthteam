#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.workflow_utils import get_available_coordinators

print("=== Debugging Coordinator Availability ===")

coordinators = get_available_coordinators()

print(f"Found {len(coordinators)} available coordinators")

if coordinators:
    print("Available coordinators:")
    for coord in coordinators:
        print(f"  - ID: {coord['user_id']}, Name: {coord['full_name']}, Email: {coord['email']}")
else:
    print("ERROR: No coordinators available for reassignment!")

print("\n=== Coordinator Availability Check Complete ===")