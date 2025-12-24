#!/usr/bin/env python3
"""
Create user account for Andrea Rubio on both local and vps2 instances

User details:
- Name: Andrea Rubio
- Email: andrea@myhealthteam.org
- Role: Care Coordinator (role_id: 36)
- Password: pass123 (default)
"""

import sys
import os
import sqlite3
import hashlib
from datetime import datetime

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_connection, add_user

def create_user_in_database(db_path, description):
    """Create Andrea Rubio user in the specified database"""
    print(f"\n🔧 Creating user in {description} database...")
    print(f"   Database path: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Check if user already exists
        existing_user = conn.execute(
            "SELECT user_id, email, full_name FROM users WHERE email = ?",
            ("andrea@myhealthteam.org",)
        ).fetchone()
        
        if existing_user:
            print(f"⚠️  User already exists in {description}:")
            print(f"   ID: {existing_user['user_id']}")
            print(f"   Email: {existing_user['email']}")
            print(f"   Name: {existing_user['full_name']}")
            return False
        
        # Hash the password
        hashed_password = hashlib.sha256("pass123".encode()).hexdigest()
        
        # Insert the user
        cursor = conn.execute("""
            INSERT INTO users (
                username, password, first_name, last_name, email, full_name, 
                status, hire_date, created_date, updated_date
            ) VALUES (?, ?, ?, ?, ?, ?, 'active', CURRENT_DATE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            "andrea.rubio",  # username
            hashed_password,  # password
            "Andrea",  # first_name
            "Rubio",  # last_name
            "andrea@myhealthteam.org",  # email
            "Andrea Rubio",  # full_name
        ))
        
        # Get the new user_id
        user_id = cursor.lastrowid
        
        # Assign Care Coordinator role (role_id = 36)
        conn.execute("""
            INSERT INTO user_roles (user_id, role_id, is_primary) VALUES (?, ?, 1)
        """, (user_id, 36))
        
        conn.commit()
        print(f"✅ Successfully created user in {description}:")
        print(f"   ID: {user_id}")
        print(f"   Username: andrea.rubio")
        print(f"   Email: andrea@myhealthteam.org")
        print(f"   Name: Andrea Rubio")
        print(f"   Role: Care Coordinator (role_id: 36)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating user in {description}: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function to create Andrea Rubio user in both databases"""
    print("=" * 60)
    print("🚀 Creating Andrea Rubio User Account")
    print("=" * 60)
    
    # User details
    print("\n📋 User Details:")
    print("   Name: Andrea Rubio")
    print("   Email: andrea@myhealthteam.org")
    print("   Role: Care Coordinator (role_id: 36)")
    print("   Password: pass123 (default)")
    
    # Create user in local database
    local_db_path = os.path.join(os.path.dirname(__file__), "production.db")
    local_success = create_user_in_database(local_db_path, "LOCAL")
    
    # Create user in vps2 database
    # Note: Update this path to match your actual vps2 database location
    vps2_db_path = os.path.join(os.path.dirname(__file__), "server2_production.db")
    
    # Check if vps2 database exists
    if not os.path.exists(vps2_db_path):
        print(f"\n⚠️  VPS2 database not found at: {vps2_db_path}")
        print("   Please update the vps2_db_path variable in this script")
        print("   Or ensure the database file exists")
        vps2_success = False
    else:
        vps2_success = create_user_in_database(vps2_db_path, "VPS2")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   Local database: {'✅ SUCCESS' if local_success else '❌ FAILED'}")
    print(f"   VPS2 database: {'✅ SUCCESS' if vps2_success else '❌ FAILED'}")
    
    if local_success and vps2_success:
        print("\n🎉 User account created successfully in both databases!")
        print("\n📝 Next steps:")
        print("   1. Andrea can now log in with:")
        print("      - Email: andrea@myhealthteam.org")
        print("      - Password: pass123")
        print("   2. Consider changing the default password for security")
    else:
        print("\n⚠️  Some operations failed. Please check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()