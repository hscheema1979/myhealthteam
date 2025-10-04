#!/usr/bin/env python3

import sqlite3
import sys
import os

# Add the src directory to the path so we can import database
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import database

def check_users_table():
    """Check the structure of the users table"""
    conn = database.get_db_connection()
    try:
        # Get table schema
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("Users table structure:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Get a sample of users
        cursor = conn.execute("SELECT * FROM users LIMIT 5")
        users = cursor.fetchall()
        
        print(f"\nSample users (first 5):")
        for user in users:
            print(f"  {user}")
            
        # Search for Eden specifically
        cursor = conn.execute("""
            SELECT * FROM users 
            WHERE LOWER(full_name) LIKE '%eden%' OR LOWER(username) LIKE '%eden%'
        """)
        eden_users = cursor.fetchall()
        
        print(f"\nUsers matching 'Eden':")
        for user in eden_users:
            print(f"  {user}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    check_users_table()