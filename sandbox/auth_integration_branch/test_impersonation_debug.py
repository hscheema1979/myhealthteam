#!/usr/bin/env python3
"""
Debug script to test impersonation functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.auth_module import get_auth_manager

def test_impersonation():
    """Test impersonation functionality step by step"""
    print("=== Testing Impersonation Debug ===")
    
    auth_manager = get_auth_manager()
    
    # First, let's check if we're authenticated
    print(f"Is authenticated: {auth_manager.is_authenticated()}")
    
    if not auth_manager.is_authenticated():
        print("Not authenticated. Please login first.")
        return
    
    # Get current user info
    current_user = auth_manager.get_current_user()
    print(f"Current user: {current_user}")
    
    if current_user:
        print(f"Current user email: {current_user.get('email', 'Unknown')}")
        print(f"Current user full_name: {current_user.get('full_name', 'Unknown')}")
        print(f"Current user roles: {auth_manager.get_user_roles()}")
    
    # Check if we're impersonating
    print(f"Is impersonating: {auth_manager.is_impersonating()}")
    
    if auth_manager.is_impersonating():
        original_user = auth_manager.get_original_user()
        print(f"Original user: {original_user}")
        if original_user:
            print(f"Original user email: {original_user.get('email', 'Unknown')}")
            print(f"Original user full_name: {original_user.get('full_name', 'Unknown')}")
    
    # Test impersonating dianela (user_id 8)
    print("\n=== Testing impersonation of dianela ===")
    result = auth_manager.start_impersonation(8)
    print(f"Impersonation result: {result}")
    
    if result:
        print(f"Is impersonating after start: {auth_manager.is_impersonating()}")
        
        # Get current user after impersonation
        impersonated_user = auth_manager.get_current_user()
        print(f"Impersonated user: {impersonated_user}")
        
        if impersonated_user:
            print(f"Impersonated user email: {impersonated_user.get('email', 'Unknown')}")
            print(f"Impersonated user full_name: {impersonated_user.get('full_name', 'Unknown')}")
            print(f"Impersonated user roles: {auth_manager.get_user_roles()}")
        else:
            print("ERROR: get_current_user() returned None after impersonation!")
        
        # Test stopping impersonation
        print("\n=== Testing stop impersonation ===")
        stop_result = auth_manager.stop_impersonation()
        print(f"Stop impersonation result: {stop_result}")
        print(f"Is impersonating after stop: {auth_manager.is_impersonating()}")
        
        # Get current user after stopping
        final_user = auth_manager.get_current_user()
        print(f"Final user: {final_user}")
        if final_user:
            print(f"Final user email: {final_user.get('email', 'Unknown')}")

if __name__ == "__main__":
    test_impersonation()