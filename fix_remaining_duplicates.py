"""
Script to fix remaining duplicates in provider_task_billing_status table.
This handles cases where the same (provider_task_id, billing_week, is_carried_over) 
combination exists multiple times.
"""

import sqlite3
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the database before cleanup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/production_db_remaining_cleanup_{timestamp}.db"
    
    import shutil
    import os
    os.makedirs("backups", exist_ok=True)
    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path

def analyze_remaining_duplicates(conn):
    """Analyze remaining duplicates"""
    print("\n" + "=" * 80)
    print("ANALYZING REMAINING DUPLICATES")
    print("=" * 80)
    
    # Find exact duplicates (same provider_task_id + billing_week + is_carried_over)
    query = """
    SELECT 
        provider_task_id,
        billing_week,
        is_carried_over,
        COUNT(*) as count,
        GROUP_CONCAT(billing_status_id) as status_ids
    FROM provider_task_billing_status
    GROUP BY provider_task_id, billing_week, is_carried_over
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 20
    """
    
    rows = conn.execute(query).fetchall()
    
    if not rows:
        print("✓ No remaining exact duplicates found!")
        return 0
    
    print(f"\nFound {len(rows)} duplicate groups (top 20 shown):")
    print("-" * 80)
    
    for row in rows:
        provider_id = row[0]
        billing_week = row[1]
        is_carried = row[2]
        count = row[3]
        status_ids = row[4]
        print(f"provider_task_id={provider_id}, week={billing_week}, carried_over={is_carried}: {count} copies")
        print(f"  Status IDs: {status_ids[:100]}...")
    
    # Count total remaining duplicates
    total_count = conn.execute("SELECT COUNT(*) FROM provider_task_billing_status").fetchone()[0]
    unique_count = conn.execute("""
        SELECT COUNT(DISTINCT provider_task_id || '|' || billing_week || '|' || is_carried_over)
        FROM provider_task_billing_status
    """).fetchone()[0]
    
    duplicates_to_remove = total_count - unique_count
    
    print("-" * 80)
    print(f"Total rows: {total_count}")
    print(f"Unique rows: {unique_count}")
    print(f"Duplicates to remove: {duplicates_to_remove}")
    
    return duplicates_to_remove

def cleanup_remaining_duplicates(conn):
    """Remove exact duplicates (same provider_task_id + billing_week + is_carried_over)"""
    
    print("\n" + "=" * 80)
    print("REMOVING REMAINING DUPLICATES")
    print("=" * 80)
    
    # Find all duplicates and delete older ones, keeping the one with highest billing_status_id
    # This is a multi-step process for SQLite
    
    # Step 1: Get the IDs to keep (max billing_status_id per unique combination)
    keep_ids_query = """
    SELECT MAX(billing_status_id) as keep_id
    FROM provider_task_billing_status
    GROUP BY provider_task_id, billing_week, is_carried_over
    """
    
    cursor = conn.execute(keep_ids_query)
    keep_ids = [row[0] for row in cursor.fetchall()]
    
    # Step 2: Delete all records NOT in the keep list
    # We need to handle this carefully to avoid hitting SQLite limits
    deleted_total = 0
    batch_size = 1000
    
    for i in range(0, len(keep_ids), batch_size):
        batch = keep_ids[i:i+batch_size]
        
        # Count records NOT in this batch
        count_query = f"""
        SELECT COUNT(*) 
        FROM provider_task_billing_status
        WHERE billing_status_id NOT IN ({','.join(['?'] * len(batch))})
        """
        to_delete = conn.execute(count_query, batch).fetchone()[0]
        
        if to_delete > 0:
            # Delete records NOT in keep_ids (this deletes everything, then we'll re-insert)
            # Actually, let's use a different approach: create temp table
            break
    
    # Better approach: Create temp table with unique records
    conn.execute("DROP TABLE IF EXISTS temp_unique_billing")
    conn.execute("""
        CREATE TABLE temp_unique_billing AS
        SELECT * FROM provider_task_billing_status
        WHERE billing_status_id IN (
            SELECT MAX(billing_status_id)
            FROM provider_task_billing_status
            GROUP BY provider_task_id, billing_week, is_carried_over
        )
    """)
    
    # Count records to be deleted
    current_count = conn.execute("SELECT COUNT(*) FROM provider_task_billing_status").fetchone()[0]
    temp_count = conn.execute("SELECT COUNT(*) FROM temp_unique_billing").fetchone()[0]
    to_delete = current_count - temp_count
    
    # Replace original table
    conn.execute("DROP TABLE provider_task_billing_status")
    conn.execute("ALTER TABLE temp_unique_billing RENAME TO provider_task_billing_status")
    
    # Recreate indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_provider_id ON provider_task_billing_status(provider_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_billing_week ON provider_task_billing_status(billing_week)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_task_date ON provider_task_billing_status(task_date)")
    
    # Recreate UNIQUE constraint
    conn.execute("DROP TABLE IF EXISTS temp_constraint_billing")
    conn.execute("""
        CREATE TABLE temp_constraint_billing (
            billing_status_id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_task_id INTEGER NOT NULL,
            provider_id INTEGER,
            provider_name TEXT,
            patient_id TEXT,
            patient_name TEXT,
            task_date TEXT NOT NULL,
            billing_week TEXT NOT NULL,
            week_start_date TEXT,
            week_end_date TEXT,
            task_description TEXT,
            minutes_of_service INTEGER,
            billing_code TEXT,
            billing_code_description TEXT,
            billing_status TEXT DEFAULT 'Pending',
            is_billed INTEGER DEFAULT 0,
            billed_date TEXT,
            billed_by INTEGER,
            billing_company TEXT,
            is_invoiced INTEGER DEFAULT 0,
            invoiced_date TEXT,
            is_claim_submitted INTEGER DEFAULT 0,
            claim_submitted_date TEXT,
            is_insurance_processed INTEGER DEFAULT 0,
            insurance_processed_date TEXT,
            is_approved_to_pay INTEGER DEFAULT 0,
            approved_to_pay_date TEXT,
            is_paid INTEGER DEFAULT 0,
            paid_date TEXT,
            is_carried_over INTEGER DEFAULT 0 NOT NULL,
            original_billing_week TEXT,
            carryover_reason TEXT,
            billing_notes TEXT,
            created_date TEXT,
            updated_date TEXT,
            UNIQUE(provider_task_id, billing_week, is_carried_over)
        )
    """)
    
    # Copy data
    conn.execute("""
        INSERT INTO temp_constraint_billing
        SELECT * FROM provider_task_billing_status
    """)
    
    # Replace table
    conn.execute("DROP TABLE provider_task_billing_status")
    conn.execute("ALTER TABLE temp_constraint_billing RENAME TO provider_task_billing_status")
    
    # Recreate indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_provider_id ON provider_task_billing_status(provider_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_billing_week ON provider_task_billing_status(billing_week)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_task_date ON provider_task_billing_status(task_date)")
    
    conn.commit()
    
    print(f"✓ Removed {to_delete} remaining duplicate rows")
    return to_delete

def verify_cleanup(conn):
    """Verify no duplicates remain"""
    print("\n" + "=" * 80)
    print("FINAL VERIFICATION")
    print("=" * 80)
    
    query = """
    SELECT COUNT(*) as count
    FROM (
        SELECT provider_task_id, billing_week, is_carried_over, COUNT(*) as cnt
        FROM provider_task_billing_status
        GROUP BY provider_task_id, billing_week, is_carried_over
        HAVING COUNT(*) > 1
    )
    """
    
    result = conn.execute(query).fetchone()[0]
    
    if result == 0:
        print("✓ No duplicates found - cleanup successful!")
        return True
    else:
        print(f"⚠ WARNING: Still found {result} duplicate groups")
        return False

def main():
    db_path = "production.db"
    
    print("=" * 80)
    print("REMAINING DUPLICATES CLEANUP TOOL")
    print("=" * 80)
    print(f"Database: {db_path}")
    print(f"Timestamp: {datetime.now()}")
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Analyze remaining duplicates
        duplicates_count = analyze_remaining_duplicates(conn)
        
        if duplicates_count == 0:
            print("\n✓ No cleanup needed!")
            conn.close()
            return
        
        # Create backup
        print("\n" + "=" * 80)
        print("PROCEEDING WITH CLEANUP")
        print("=" * 80)
        print("Creating backup before cleanup...")
        backup_path = backup_database(db_path)
        
        # Cleanup
        removed_count = cleanup_remaining_duplicates(conn)
        
        # Verify
        success = verify_cleanup(conn)
        
        print("\n" + "=" * 80)
        print("CLEANUP COMPLETE")
        print("=" * 80)
        print(f"Backup saved to: {backup_path}")
        print(f"Removed {removed_count} duplicate rows")
        print(f"UNIQUE constraint: (provider_task_id, billing_week, is_carried_over)")
        
        if success:
            print("\n✓ All duplicates removed successfully!")
        else:
            print("\n⚠ Some duplicates remain - may need another run")
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
