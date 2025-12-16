#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.dashboards.care_coordinator_dashboard_enhanced import show
import streamlit as st

print("=== Checking Coordinator Dashboard Table Design ===")
print("Go look at the actual coordinator dashboard to see:")
print("1. What do the coordinator task tables look like?")
print("2. Do they use st.dataframe() or custom layouts?") 
print("3. What colors/formatting do they use?")
print("4. How are the columns arranged?")
print("")
print("The workflow reassignment should match this exact design!")
print("")
print("Current coordinator dashboard has these sections:")
print("- My Patients (with patient list)")
print("- Phone Reviews") 
print("- Team Management (with coordinator tasks)")
print("- Patient Info")
print("- Help")
print("")
print("Go check it out and let me know what you see!")