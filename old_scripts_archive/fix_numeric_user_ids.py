#!/usr/bin/env python3
"""
FIX NUMERIC USER IDs - Convert numeric user_ids to proper names in September and November
"""

import sqlite3
import shutil
from datetime import datetime

def backup_production_db():
    """Create backup of production.db before changes"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'production_numeric_fix_backup_{timestamp}.db'
    shutil.copy2('production.db', backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def get_user_id_mappings():
    """Get mapping from numeric user_ids to full names"""
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print("Loading user_id to name mappings...")
    
    # Get all user_id to full_name mappings
    cursor.execute("SELECT user_id, full_name FROM users WHERE full_name IS NOT NULL AND full_name != ''")
    user_mappings = {str(row[0]): row[1] for row in cursor.fetchall()}
    
    print(f"Found {len(user_mappings)} user mappings")
    print("User ID mappings:")
    for user_id, full_name in sorted(user_mappings.items()):
        print(f"  {user_id} -> {full_name}")
    
    conn.close()
    return user_mappings

def update_coordinator_tasks_with_user_ids(user_mappings):
    """Update coordinator_tasks tables to convert numeric user_ids to names"""
    print("\n📝 UPDATING COORDINATOR TASKS - Numeric User IDs")
    print("=" * 60)
    
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    months = ['2025_09', '2025_11']  # September and November have numeric IDs
    total_updated = 0
    
    for month in months:
        table_name = f'coordinator_tasks_{month}'
        print(f"\nProcessing {table_name}...")
        
        try:
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f"  ⚠️  {table_name} not found")
                continue
            
            # Get distinct coordinator_ids to see what needs updating
            cursor.execute(f"SELECT DISTINCT coordinator_id FROM {table_name}")
            coordinator_ids = cursor.fetchall()
            
            numeric_ids_to_update = []
            for row in coordinator_ids:
                coordinator_id = str(row[0])
                if coordinator_id.isdigit() and coordinator_id in user_mappings:
                    numeric_ids_to_update.append(coordinator_id)
            
            if not numeric_ids_to_update:
                print(f"  ✅ No numeric user IDs found to update")
                continue
                
            print(f"  Found {len(numeric_ids_to_update)} numeric user IDs to update: {numeric_ids_to_update}")
            
            # Update each numeric ID
            for user_id in numeric_ids_to_update:
                new_name = user_mappings[user_id]
                
                cursor.execute(f"""
                    UPDATE {table_name} 
                    SET coordinator_id = ? 
                    WHERE coordinator_id = ?
                """, (new_name, user_id))
                
                updated_count = cursor.rowcount
                if updated_count > 0:
                    print(f"  ✅ Updated {updated_count} records: User ID {user_id} -> {new_name}")
                    total_updated += updated_count
            
        except Exception as e:
            print(f"  ❌ Error processing {table_name}: {e}")
    
    conn.commit()
    conn.close()
    return total_updated

def verify_september_november_names():
    """Verify September and November coordinator names are now proper"""
    print("\n🔍 VERIFYING SEPTEMBER & NOVEMBER NAMES")
    print("=" * 60)
    
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Check September coordinator tasks
    print("September 2025 coordinator names:")
    cursor.execute('SELECT DISTINCT coordinator_id FROM coordinator_tasks_2025_09 ORDER BY coordinator_id')
    sept_coordinators = cursor.fetchall()
    print(f"  {len(sept_coordinators)} unique coordinator names:")
    for row in sept_coordinators:
        coordinator_id = row[0]
        cursor.execute('SELECT COUNT(*) FROM coordinator_tasks_2025_09 WHERE coordinator_id = ?', (coordinator_id,))
        task_count = cursor.fetchone()[0]
        print(f"    - {coordinator_id}: {task_count} tasks")
    
    # Check November coordinator tasks  
    print("\nNovember 2025 coordinator names:")
    cursor.execute('SELECT DISTINCT coordinator_id FROM coordinator_tasks_2025_11 ORDER BY coordinator_id')
    nov_coordinators = cursor.fetchall()
    print(f"  {len(nov_coordinators)} unique coordinator names:")
    for row in nov_coordinators:
        coordinator_id = row[0]
        cursor.execute('SELECT COUNT(*) FROM coordinator_tasks_2025_11 WHERE coordinator_id = ?', (coordinator_id,))
        task_count = cursor.fetchone()[0]
        print(f"    - {coordinator_id}: {task_count} tasks")
    
    # Count how many still have numeric IDs
    numeric_count = 0
    for row in sept_coordinators + nov_coordinators:
        if str(row[0]).isdigit():
            numeric_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  Still have numeric IDs: {numeric_count}")
    print(f"  Proper names: {len(sept_coordinators) + len(nov_coordinators) - numeric_count}")
    
    if numeric_count == 0:
        print("  ✅ All coordinator names are now in proper format!")
    else:
        print("  ⚠️  Some coordinator names still need fixing")
    
    conn.close()

def main():
    """Main function to fix numeric user IDs"""
    print("🚀 FIXING NUMERIC USER IDs - September & November 2025")
    print("=" * 60)
    
    # Create backup
    backup_path = backup_production_db()
    
    # Get user ID mappings
    user_mappings = get_user_id_mappings()
    
    if not user_mappings:
        print("❌ No user mappings found!")
        return
    
    # Update coordinator tasks
    coordinator_updated = update_coordinator_tasks_with_user_ids(user_mappings)
    
    # Verify updates
    verify_september_november_names()
    
    print(f"\n✅ NUMERIC USER ID FIX COMPLETE")
    print(f"   Coordinator records updated: {coordinator_updated}")
    print(f"   Backup saved as: {backup_path}")
    
    return coordinator_updated

if __name__ == "__main__":
    main()