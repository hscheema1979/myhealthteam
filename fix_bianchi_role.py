#!/usr/bin/env python3

import sqlite3
from datetime import datetime

def assign_admin_role_to_user(username):
    """Assign Admin role (role_id: 34) to a user"""
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    try:
        # Get user ID
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if not result:
            print(f"User {username} not found")
            return False
            
        user_id = result[0]
        print(f"Found user {username} with user_id: {user_id}")
        
        # Check if user already has admin role
        cursor.execute(
            "SELECT * FROM user_roles WHERE user_id = ? AND role_id = 34", 
            (user_id,)
        )
        existing_role = cursor.fetchone()
        
        if existing_role:
            print(f"User {username} already has Admin role")
            return True
        
        # Assign Admin role
        cursor.execute(
            "INSERT INTO user_roles (user_id, role_id, created_date) VALUES (?, 34, ?)",
            (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        
        conn.commit()
        print(f"✅ Successfully assigned Admin role to {username}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error assigning Admin role: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    assign_admin_role_to_user("sanchez.bianchi")