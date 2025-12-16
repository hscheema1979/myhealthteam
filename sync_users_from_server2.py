"""
Sync users from myhealthteam instance on server 2 to local development database.

This script will:
1. Connect to the myhealthteam database on server 2
2. Get all users from the users table
3. Compare with local development database users
4. Add any missing users to local production.db
"""

import sqlite3
import sys
from datetime import datetime


def get_server2_connection():
    """Connect to myhealthteam database on server 2"""
    # TODO: Update with actual server 2 connection details
    # This might be a remote connection, SSH tunnel, or exported database file
    server2_db_path = "path_to_server2_database"  # Update this
    try:
        conn = sqlite3.connect(server2_db_path)
        print(f"✓ Connected to server 2 database: {server2_db_path}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to server 2 database: {e}")
        return None


def get_local_connection():
    """Connect to local development database"""
    local_db_path = "production.db"
    try:
        conn = sqlite3.connect(local_db_path)
        print(f"✓ Connected to local database: {local_db_path}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to local database: {e}")
        return None


def get_users_from_server2(conn):
    """Get all users from server 2 users table"""
    try:
        query = """
        SELECT 
            id,
            username,
            email,
            full_name,
            created_at,
            updated_at,
            is_active,
            role_id
        FROM users
        ORDER BY id
        """
        cursor = conn.cursor()
        cursor.execute(query)
        users = cursor.fetchall()
        
        print(f"✓ Found {len(users)} users in server 2 database")
        return users
    except Exception as e:
        print(f"❌ Error getting users from server 2: {e}")
        return []


def get_local_users(conn):
    """Get all users from local database"""
    try:
        query = """
        SELECT 
            id,
            username,
            email,
            full_name,
            created_at,
            updated_at,
            is_active,
            role_id
        FROM users
        ORDER BY id
        """
        cursor = conn.cursor()
        cursor.execute(query)
        users = cursor.fetchall()
        
        print(f"✓ Found {len(users)} users in local database")
        return users
    except Exception as e:
        print(f"❌ Error getting local users: {e}")
        return []


def compare_users(server_users, local_users):
    """Compare users and identify missing ones"""
    # Create sets for comparison
    server_user_ids = {user[0] for user in server_users}
    local_user_ids = {user[0] for user in local_users}
    
    # Find missing user IDs
    missing_ids = server_user_ids - local_user_ids
    
    # Get full user records for missing users
    missing_users = [user for user in server_users if user[0] in missing_ids]
    
    print(f"📊 Comparison Results:")
    print(f"   Server 2 users: {len(server_users)}")
    print(f"   Local users: {len(local_users)}")
    print(f"   Missing users: {len(missing_users)}")
    
    return missing_users


def add_missing_users(local_conn, missing_users):
    """Add missing users to local database"""
    if not missing_users:
        print("✓ No missing users to add")
        return True
    
    try:
        cursor = local_conn.cursor()
        
        for user in missing_users:
            (user_id, username, email, full_name, created_at, updated_at, is_active, role_id) = user
            
            # Check if user already exists by username to avoid duplicates
            check_query = "SELECT id FROM users WHERE username = ?"
            cursor.execute(check_query, (username,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"⚠️  User {username} already exists locally with ID {existing[0]}, skipping...")
                continue
            
            # Insert the user
            insert_query = """
            INSERT INTO users (
                id, username, email, full_name, created_at, updated_at, is_active, role_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, (
                user_id, username, email, full_name, created_at, updated_at, is_active, role_id
            ))
            
            print(f"✓ Added user: {username} (ID: {user_id})")
        
        local_conn.commit()
        print(f"✅ Successfully added {len(missing_users)} users to local database")
        return True
        
    except Exception as e:
        print(f"❌ Error adding users: {e}")
        local_conn.rollback()
        return False


def main():
    """Main sync process"""
    print("🔄 Starting user sync from server 2 to local development database...")
    print("=" * 60)
    
    # Connect to databases
    server2_conn = get_server2_connection()
    if not server2_conn:
        print("❌ Cannot proceed without server 2 connection")
        return False
    
    local_conn = get_local_connection()
    if not local_conn:
        print("❌ Cannot proceed without local database connection")
        server2_conn.close()
        return False
    
    try:
        # Get users from both databases
        print("\n📥 Getting users from server 2...")
        server_users = get_users_from_server2(server2_conn)
        if not server_users:
            print("❌ No users found in server 2 database")
            return False
        
        print("\n📥 Getting users from local database...")
        local_users = get_local_users(local_conn)
        
        # Compare and find missing users
        print("\n🔍 Comparing users...")
        missing_users = compare_users(server_users, local_users)
        
        if missing_users:
            print(f"\n📋 Missing users to add:")
            for user in missing_users:
                print(f"   - {user[1]} ({user[3]}) - ID: {user[0]}")
            
            # Add missing users
            print(f"\n➕ Adding missing users...")
            success = add_missing_users(local_conn, missing_users)
            
            if success:
                print("\n🎉 User sync completed successfully!")
                return True
            else:
                print("\n❌ User sync failed during user addition")
                return False
        else:
            print("\n✅ All users are already in sync!")
            return True
            
    except Exception as e:
        print(f"❌ Unexpected error during sync: {e}")
        return False
    
    finally:
        # Close connections
        server2_conn.close()
        local_conn.close()
        print("\n🔌 Database connections closed")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
