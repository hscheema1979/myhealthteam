#!/usr/bin/env python3
"""
EMERGENCY FIX: Restore Missing Coordinator Users and Staff Code Mapping
This script fixes the critical coordinator billing dashboard issue where only 1 coordinator appears.
"""

import sqlite3
import shutil
from datetime import datetime

def backup_production():
    """Create backup of production database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/production_backup_emergency_{timestamp}.db"
    shutil.copy2("production.db", backup_path)
    print(f"✅ Created emergency backup: {backup_path}")
    return backup_path

def copy_missing_users_and_mapping():
    """Copy missing users and staff_code_mapping table from backup to production"""
    
    print("🔧 Starting emergency coordinator data restoration...")
    
    # Connect to both databases
    backup_conn = sqlite3.connect('production_backup_prototype_test.db')
    prod_conn = sqlite3.connect('production.db')
    
    try:
        # Step 1: Create staff_code_mapping table in production if it doesn't exist
        print("\n📋 Step 1: Creating staff_code_mapping table...")
        prod_conn.execute('''
            CREATE TABLE IF NOT EXISTS staff_code_mapping (
                staff_code TEXT PRIMARY KEY,
                user_id INTEGER,
                confidence_level TEXT CHECK (confidence_level IN ('HIGH', 'MEDIUM', 'LOW', 'UNMATCHED')),
                mapping_type TEXT CHECK (mapping_type IN ('PROVIDER', 'COORDINATOR', 'SPECIAL_CASE')),
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES "users"(user_id)
            )
        ''')
        
        # Step 2: Copy staff_code_mapping data
        print("📋 Step 2: Copying staff code mappings...")
        backup_cursor = backup_conn.execute('SELECT * FROM staff_code_mapping')
        mappings = backup_cursor.fetchall()
        
        prod_conn.execute('DELETE FROM staff_code_mapping')  # Clear existing
        for mapping in mappings:
            prod_conn.execute('''
                INSERT INTO staff_code_mapping (staff_code, user_id, confidence_level, mapping_type, notes, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', mapping)
        
        print(f"✅ Copied {len(mappings)} staff code mappings")
        
        # Step 3: Copy missing users
        print("\n👥 Step 3: Copying missing coordinator users...")
        
        # Get missing users from backup (Dianela and Hector)
        backup_cursor = backup_conn.execute('''
            SELECT * FROM users WHERE user_id IN (13, 14) OR full_name LIKE "%Atevalo%" OR full_name LIKE "%Hernandez%"
        ''')
        missing_users = backup_cursor.fetchall()
        
        print(f"Found {len(missing_users)} missing users in backup:")
        for user in missing_users:
            print(f"  - {user[2]} (User ID: {user[0]})")
        
        # Insert missing users (skip if already exists)
        for user in missing_users:
            try:
                prod_conn.execute('''
                    INSERT INTO users (user_id, username, password, first_name, last_name, full_name, email, phone, status, role_id, created_date, updated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', user)
                print(f"✅ Added user: {user[2]}")
            except sqlite3.IntegrityError:
                print(f"⚠️  User {user[2]} already exists, skipping")
        
        # Step 4: Copy user roles for missing users
        print("\n🎭 Step 4: Copying user roles...")
        backup_cursor = backup_conn.execute('''
            SELECT ur.* FROM user_roles ur
            JOIN users u ON ur.user_id = u.user_id
            WHERE u.user_id IN (13, 14) OR u.full_name LIKE "%Atevalo%" OR u.full_name LIKE "%Hernandez%"
        ''')
        missing_roles = backup_cursor.fetchall()
        
        for role in missing_roles:
            try:
                prod_conn.execute('''
                    INSERT INTO user_roles (user_id, role_id, assigned_date)
                    VALUES (?, ?, ?)
                ''', role)
                print(f"✅ Added role for User ID {role[0]}")
            except sqlite3.IntegrityError:
                print(f"⚠️  Role already exists for User ID {role[0]}, skipping")
        
        # Commit all changes
        prod_conn.commit()
        print("\n✅ All changes committed successfully!")
        
    except Exception as e:
        prod_conn.rollback()
        print(f"❌ Error during restoration: {e}")
        raise
    finally:
        backup_conn.close()
        prod_conn.close()

def verify_restoration():
    """Verify that the restoration worked"""
    
    print("\n🔍 Verifying restoration...")
    
    conn = sqlite3.connect('production.db')
    
    try:
        # Check staff_code_mapping table
        cursor = conn.execute('SELECT COUNT(*) FROM staff_code_mapping')
        mapping_count = cursor.fetchone()[0]
        print(f"✅ staff_code_mapping table: {mapping_count} mappings")
        
        # Check for Dianela and Hector
        cursor = conn.execute('SELECT user_id, full_name, username FROM users WHERE full_name LIKE "%Atevalo%" OR full_name LIKE "%Hernandez%"')
        missing_users = cursor.fetchall()
        print(f"✅ Missing users restored: {len(missing_users)}")
        for user in missing_users:
            print(f"  - User ID {user[0]}: {user[1]} ({user[2]})")
        
        # Check coordinator count
        cursor = conn.execute('SELECT COUNT(*) FROM users WHERE role_id = 36')
        coord_count = cursor.fetchone()[0]
        print(f"✅ Total coordinators: {coord_count}")
        
        # Check specific staff code mappings
        staff_codes = ['AteDi000', 'HerHe000', 'SobJo000']
        for code in staff_codes:
            cursor = conn.execute('SELECT * FROM staff_code_mapping WHERE staff_code = ?', (code,))
            mapping = cursor.fetchone()
            if mapping:
                print(f"✅ {code}: Maps to User ID {mapping[1]}")
            else:
                print(f"❌ {code}: No mapping found")
                
    except Exception as e:
        print(f"❌ Verification error: {e}")
    finally:
        conn.close()

def main():
    """Main execution function"""
    
    print("🚨 EMERGENCY COORDINATOR DATA RESTORATION 🚨")
    print("=" * 60)
    print("This will fix the coordinator billing dashboard issue where only 1 coordinator appears.")
    print("Root cause: Missing users (Dianela, Hector) and staff_code_mapping table")
    print("=" * 60)
    
    # Step 1: Create backup
    backup_path = backup_production()
    
    # Step 2: Restore missing data
    copy_missing_users_and_mapping()
    
    # Step 3: Verify restoration
    verify_restoration()
    
    print("\n🎉 EMERGENCY RESTORATION COMPLETE!")
    print(f"✅ Backup saved: {backup_path}")
    print("✅ Missing users restored: Dianela Atevalo, Hector Hernandez")
    print("✅ staff_code_mapping table restored")
    print("✅ All coordinator data should now appear in billing dashboard")
    
    print("\n📋 NEXT STEPS:")
    print("1. Re-run data transformation to process all CM_log files")
    print("2. Verify coordinator billing dashboard shows all coordinators")
    print("3. Test provider billing month selection functionality")

if __name__ == "__main__":
    main()