#!/usr/bin/env python3
"""
Debug the role caching issue
"""

import streamlit as st
from src import database as db
from src.core_utils import get_user_role_ids

def debug_role_caching():
    """Debug the role caching mechanism"""
    
    user_id = 12  # Harpreet's user_id
    
    print(f"=== Debugging Role Caching for user_id: {user_id} ===\n")
    
    # Check what's in session state
    print("Session State Check:")
    session_user_id = st.session_state.get('user_id', 'NOT_FOUND')
    session_role_ids = st.session_state.get('user_role_ids', 'NOT_FOUND')
    print(f"  st.session_state['user_id']: {session_user_id}")
    print(f"  st.session_state['user_role_ids']: {session_role_ids}")
    
    # Check what the condition evaluates to
    condition1 = 'user_role_ids' not in st.session_state
    condition2 = 'user_id' not in st.session_state
    condition3 = st.session_state.get('user_id') != user_id
    
    print(f"\nCaching Condition Check:")
    print(f"  'user_role_ids' not in st.session_state: {condition1}")
    print(f"  'user_id' not in st.session_state: {condition2}")
    print(f"  st.session_state.get('user_id') != {user_id}: {condition3}")
    print(f"  Overall condition (should refresh): {condition1 or condition2 or condition3}")
    
    # Check database directly
    print(f"\nDatabase Check:")
    conn = db.get_db_connection()
    try:
        db_roles = conn.execute("SELECT role_id FROM user_roles WHERE user_id = ?", (user_id,)).fetchall()
        db_role_ids = [r['role_id'] for r in db_roles]
        print(f"  Database roles for user {user_id}: {db_role_ids}")
        
        # Check core_utils function
        core_utils_roles = get_user_role_ids(user_id)
        print(f"  core_utils.get_user_role_ids({user_id}): {core_utils_roles}")
        
        if db_role_ids != core_utils_roles:
            print(f"  ❌ MISMATCH: DB={db_role_ids}, core_utils={core_utils_roles}")
        else:
            print(f"  ✅ MATCH: Both return {db_role_ids}")
            
    finally:
        conn.close()
    
    # Test the admin dashboard function logic
    print(f"\nAdmin Dashboard Function Logic:")
    
    def test_get_user_role_ids(user_id):
        """Test version of the admin dashboard function"""
        if 'user_role_ids' not in st.session_state or 'user_id' not in st.session_state or st.session_state.get('user_id') != user_id:
            print(f"    Condition triggered - refreshing from database")
            try:
                user_roles = db.get_user_roles_by_user_id(user_id)
                role_ids = [r["role_id"] for r in user_roles]
                st.session_state['user_role_ids'] = role_ids
                st.session_state['user_id'] = user_id
                print(f"    Set session['user_role_ids'] = {role_ids}")
                return role_ids
            except Exception as e:
                st.session_state['user_role_ids'] = []
                st.session_state['user_id'] = user_id
                print(f"    Error: {e}")
                return []
        else:
            cached = st.session_state.get('user_role_ids', [])
            print(f"    Using cached value: {cached}")
            return cached
    
    result = test_get_user_role_ids(user_id)
    print(f"  Final result: {result}")

if __name__ == "__main__":
    debug_role_caching()