#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.auth_module import get_auth_manager

# Check what primary dashboard role Jan gets
auth_manager = get_auth_manager()

# Simulate Jan's login
if auth_manager.login("estomo.jan", "jan"):  # Assuming password is "jan"
    primary_role = auth_manager.get_primary_dashboard_role()
    user_roles = auth_manager.get_user_roles()
    user_id = auth_manager.get_user_id()
    
    print(f"Jan login successful")
    print(f"User ID: {user_id}")
    print(f"Primary dashboard role: {primary_role}")
    print(f"All roles: {user_roles}")
    
    # Check what dashboard this would send Jan to
    if primary_role == 33:  # Provider
        print("Would send to: Provider Dashboard")
    elif primary_role == 34:  # Admin
        print("Would send to: Admin Dashboard")
    elif primary_role == 36:  # Care Coordinator
        print("Would send to: Care Coordinator Dashboard")
    elif primary_role == 40:  # Coordinator Manager
        print("Would send to: Admin Dashboard (should have workflow reassignment)")
    else:
        print(f"Would send to: Unknown dashboard for role {primary_role}")
        
    auth_manager.logout()
else:
    print("Jan login failed - check credentials")