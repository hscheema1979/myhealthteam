#!/usr/bin/env python3
"""
FIX NAME FORMATS - Convert alphanumeric IDs to proper "last,first" format
"""

import sqlite3
import shutil
from datetime import datetime

def backup_production_db():
    """Create backup of production.db before changes"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'production_name_fix_backup_{timestamp}.db'
    shutil.copy2('production.db', backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def get_name_mappings():
    """Get mapping from staff_codes table"""
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print("Loading name mappings from staff_codes table...")
    
    # Get coordinator mappings (coordinator_code -> proper name)
    cursor.execute("""
        SELECT coordinator_code, provider_code 
        FROM staff_codes 
        WHERE coordinator_code IS NOT NULL AND coordinator_code != ''
    """)
    coordinator_mappings = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Get provider mappings (this is trickier - need to map ZEN codes to proper names)
    cursor.execute("""
        SELECT full_name, email, provider_code 
        FROM staff_codes 
        WHERE provider_code IS NOT NULL AND provider_code != ''
    """)
    staff_data = cursor.fetchall()
    
    # Create mapping for providers
    provider_mappings = {}
    
    # Also check staff_code_mapping for ZEN codes
    cursor.execute("""
        SELECT staff_code, notes 
        FROM staff_code_mapping 
        WHERE staff_code LIKE 'ZEN-%'
    """)
    zen_mappings_raw = cursor.fetchall()
    
    # Process ZEN mappings from staff_code_mapping
    for zen_code, notes in zen_mappings_raw:
        # Extract name from notes field
        if ' - ' in notes:
            name_part = notes.split(' - ')[0]
            # Convert to last, first format
            parts = name_part.strip().split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = ' '.join(parts[1:])
                provider_mappings[zen_code] = f"{last_name}, {first_name}"
                print(f"    Added mapping: {zen_code} -> {provider_mappings[zen_code]}")
    
    print(f"Found {len(coordinator_mappings)} coordinator mappings")
    print(f"Found {len(provider_mappings)} provider mappings")
    
    print("\nCoordinator mappings:")
    for code, name in coordinator_mappings.items():
        print(f"  {code} -> {name}")
    
    print("\nProvider mappings:")
    for code, name in provider_mappings.items():
        print(f"  {code} -> {name}")
    
    conn.close()
    return coordinator_mappings, provider_mappings

def update_coordinator_tasks(coordinator_mappings):
    """Update coordinator_tasks tables to use proper name format"""
    print("\n📝 UPDATING COORDINATOR TASKS")
    print("=" * 50)
    
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    months = ['2025_09', '2025_10', '2025_11']
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
            
            # Update coordinator_ids
            for old_code, new_name in coordinator_mappings.items():
                cursor.execute(f"""
                    UPDATE {table_name} 
                    SET coordinator_id = ? 
                    WHERE coordinator_id = ?
                """, (new_name, old_code))
                
                updated_count = cursor.rowcount
                if updated_count > 0:
                    print(f"  ✅ Updated {updated_count} records: {old_code} -> {new_name}")
                    total_updated += updated_count
            
        except Exception as e:
            print(f"  ❌ Error processing {table_name}: {e}")
    
    conn.commit()
    conn.close()
    return total_updated

def update_provider_tasks(provider_mappings):
    """Update provider_tasks tables to use proper name format"""
    print("\n👩‍⚕️ UPDATING PROVIDER TASKS")
    print("=" * 50)
    
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    months = ['2025_09', '2025_10', '2025_11']
    total_updated = 0
    
    for month in months:
        table_name = f'provider_tasks_{month}'
        print(f"\nProcessing {table_name}...")
        
        try:
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f"  ⚠️  {table_name} not found")
                continue
            
            # Update provider_name column
            for old_code, new_name in provider_mappings.items():
                cursor.execute(f"""
                    UPDATE {table_name} 
                    SET provider_name = ? 
                    WHERE provider_name = ?
                """, (new_name, old_code))
                
                updated_count = cursor.rowcount
                if updated_count > 0:
                    print(f"  ✅ Updated {updated_count} records: {old_code} -> {new_name}")
                    total_updated += updated_count
            
        except Exception as e:
            print(f"  ❌ Error processing {table_name}: {e}")
    
    conn.commit()
    conn.close()
    return total_updated

def verify_updates():
    """Verify the updates worked correctly"""
    print("\n🔍 VERIFYING UPDATES")
    print("=" * 50)
    
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Check coordinator tasks
    print("Coordinator task names:")
    for month in ['2025_09', '2025_10', '2025_11']:
        table_name = f'coordinator_tasks_{month}'
        try:
            cursor.execute(f"SELECT DISTINCT coordinator_id FROM {table_name} ORDER BY coordinator_id")
            names = cursor.fetchall()
            print(f"  {table_name}: {len(names)} unique names")
            for name in names:
                print(f"    - {name[0]}")
        except Exception as e:
            print(f"  {table_name}: Error - {e}")
    
    # Check provider tasks
    print("\nProvider task names:")
    for month in ['2025_09', '2025_10', '2025_11']:
        table_name = f'provider_tasks_{month}'
        try:
            cursor.execute(f"SELECT DISTINCT provider_name FROM {table_name} ORDER BY provider_name")
            names = cursor.fetchall()
            print(f"  {table_name}: {len(names)} unique names")
            for name in names:
                print(f"    - {name[0]}")
        except Exception as e:
            print(f"  {table_name}: Error - {e}")
    
    conn.close()

def main():
    """Main function to fix name formats"""
    print("🚀 FIXING NAME FORMATS - Converting to 'last,first' format")
    print("=" * 60)
    
    # Create backup
    backup_path = backup_production_db()
    
    # Get name mappings
    coordinator_mappings, provider_mappings = get_name_mappings()
    
    if not coordinator_mappings and not provider_mappings:
        print("❌ No mappings found!")
        return
    
    # Update coordinator tasks
    coordinator_updated = update_coordinator_tasks(coordinator_mappings)
    
    # Update provider tasks
    provider_updated = update_provider_tasks(provider_mappings)
    
    # Verify updates
    verify_updates()
    
    print(f"\n✅ NAME FORMAT FIX COMPLETE")
    print(f"   Coordinator records updated: {coordinator_updated}")
    print(f"   Provider records updated: {provider_updated}")
    print(f"   Total records updated: {coordinator_updated + provider_updated}")
    print(f"   Backup saved as: {backup_path}")
    
    return coordinator_updated + provider_updated

if __name__ == "__main__":
    main()