"""
Script to fix duplicates in provider_task_billing_status table.

This script:
1. Identifies duplicate records (same provider_task_id + billing_week + is_carried_over)
2. Keeps the most recent record (highest billing_status_id)
3. Removes older duplicates
4. Adds UNIQUE constraint to prevent future duplicates

WARNING: This will DELETE data. Backup your database before running!
"""

import sqlite3
import sys
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the database before cleanup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/production_db_before_cleanup_{timestamp}.db"
    
    import shutil
    import os
    os.makedirs("backups", exist_ok=True)
    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path

def analyze_duplicates(conn):
    """Analyze and report on duplicates before cleanup"""
    print("\n" + "=" * 80)
    print("ANALYZING DUPLICATES")
    print("=" * 80)
    
    # Count duplicates by provider_task_id
    query = """
    SELECT 
        provider_task_id,
        COUNT(*) as count,
        GROUP_CONCAT(billing_week, ', ') as weeks
    FROM provider_task_billing_status
    GROUP BY provider_task_id
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 20
    """
    
    cursor = conn.execute(query)
    duplicates = cursor.fetchall()
    
    if not duplicates:
        print("✓ No duplicates found!")
        return 0
    
    print(f"\nFound duplicates for {len(duplicates)} provider_task_ids (top 20 shown):")
    print("-" * 80)
    
    for row in duplicates:
        provider_id = row[0]
        count = row[1]
        weeks = row[2]
        print(f"provider_task_id={provider_id}: {count} copies in weeks: {weeks}")
    
    # Count total duplicate rows to remove
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

def cleanup_duplicates(conn, dry_run=True):
    """Remove duplicate records, keeping the most recent one"""
    
    if dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 80)
    
    # Find duplicates to remove (keep highest billing_status_id)
    # SQLite doesn't have DELETE with JOIN, so we need a two-step approach
    
    # Step 1: Identify billing_status_ids to KEEP (max billing_status_id per group)
    keep_ids_query = """
    SELECT MAX(billing_status_id) as keep_id
    FROM provider_task_billing_status
    GROUP BY provider_task_id, billing_week, is_carried_over
    """
    
    cursor = conn.execute(keep_ids_query)
    keep_ids = [row[0] for row in cursor.fetchall()]
    
    # Step 2: Count rows to remove
    if dry_run:
        remove_count_query = f"""
        SELECT COUNT(*) 
        FROM provider_task_billing_status
        WHERE billing_status_id NOT IN ({','.join(['?'] * len(keep_ids))})
        """
        to_remove = conn.execute(remove_count_query, keep_ids).fetchone()[0]
        print(f"Will remove {to_remove} duplicate rows")
        print(f"Will keep {len(keep_ids)} unique rows")
        return to_remove
    
    # Step 3: Remove duplicates
    print("\n" + "=" * 80)
    print("REMOVING DUPLICATES")
    print("=" * 80)
    
    remove_query = f"""
    DELETE FROM provider_task_billing_status
    WHERE billing_status_id NOT IN ({','.join(['?'] * len(keep_ids))})
    """
    
    cursor = conn.execute(remove_query, keep_ids)
    deleted_count = cursor.rowcount
    conn.commit()
    
    print(f"✓ Removed {deleted_count} duplicate rows")
    return deleted_count

def add_unique_constraint(conn):
    """Add UNIQUE constraint to prevent future duplicates"""
    print("\n" + "=" * 80)
    print("ADDING UNIQUE CONSTRAINT")
    print("=" * 80)
    
    # SQLite doesn't support ALTER TABLE ADD UNIQUE constraint directly
    # We need to recreate the table
    
    # Get current schema
    cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='provider_task_billing_status'")
    schema = cursor.fetchone()[0]
    
    # Create new table with UNIQUE constraint
    new_schema = schema.replace(
        "CREATE TABLE IF NOT EXISTS provider_task_billing_status (",
        "CREATE TABLE provider_task_billing_status_new ("
    )
    new_schema = new_schema.replace(
        "billing_week TEXT NOT NULL,",
        "billing_week TEXT NOT NULL,"
    )
    
    # Find the position to insert UNIQUE constraint (after is_carried_over)
    if "is_carried_over INTEGER DEFAULT 0 NOT NULL," in new_schema:
        unique_constraint = ", UNIQUE(provider_task_id, billing_week, is_carried_over)"
        new_schema = new_schema.replace(
            "is_carried_over INTEGER DEFAULT 0 NOT NULL,",
            "is_carried_over INTEGER DEFAULT 0 NOT NULL" + unique_constraint + ","
        )
    
    # Create new table
    conn.execute(new_schema)
    
    # Copy data
    conn.execute("""
        INSERT INTO provider_task_billing_status_new
        SELECT * FROM provider_task_billing_status
    """)
    
    # Drop old table and rename new one
    conn.execute("DROP TABLE provider_task_billing_status")
    conn.execute("ALTER TABLE provider_task_billing_status_new RENAME TO provider_task_billing_status")
    
    # Recreate indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_provider_id ON provider_task_billing_status(provider_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_billing_week ON provider_task_billing_status(billing_week)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_task_date ON provider_task_billing_status(task_date)")
    
    conn.commit()
    print("✓ UNIQUE constraint added: (provider_task_id, billing_week, is_carried_over)")

def verify_cleanup(conn):
    """Verify no duplicates remain after cleanup"""
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    query = """
    SELECT 
        provider_task_id,
        COUNT(*) as count
    FROM provider_task_billing_status
    GROUP BY provider_task_id
    HAVING COUNT(*) > 1
    """
    
    duplicates = conn.execute(query).fetchall()
    
    if not duplicates:
        print("✓ No duplicates found - cleanup successful!")
        return True
    else:
        print(f"⚠ WARNING: Still found {len(duplicates)} duplicate groups")
        return False

def main():
    db_path = "production.db"
    
    print("=" * 80)
    print("BILLING DUPLICATES CLEANUP TOOL")
    print("=" * 80)
    print(f"Database: {db_path}")
    print(f"Timestamp: {datetime.now()}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Step 1: Analyze duplicates
        duplicates_count = analyze_duplicates(conn)
        
        if duplicates_count == 0:
            print("\n✓ No cleanup needed!")
            conn.close()
            return
        
        # Step 2: Ask for confirmation
        print("\n" + "=" * 80)
        print("PROCEED TO CLEANUP?")
        print("=" * 80)
        print("WARNING: This will DELETE duplicate rows from the database!")
        print()
        
        choice = input("Type 'yes' to proceed with cleanup, or 'dryrun' to see what would be deleted: ").strip().lower()
        
        if choice == 'dryrun':
            # Dry run - show what would happen
            cleanup_duplicates(conn, dry_run=True)
            print("\n✓ Dry run complete. Run again with 'yes' to actually remove duplicates.")
            
        elif choice == 'yes':
            # Create backup first
            backup_path = backup_database(db_path)
            
            # Actually cleanup
            removed_count = cleanup_duplicates(conn, dry_run=False)
            
            # Verify cleanup
            success = verify_cleanup(conn)
            
            # Add unique constraint
            if success:
                add_unique_constraint(conn)
                
            print("\n" + "=" * 80)
            print("CLEANUP COMPLETE")
            print("=" * 80)
            print(f"Backup saved to: {backup_path}")
            print(f"Removed {removed_count} duplicate rows")
            print(f"UNIQUE constraint added to prevent future duplicates")
            print("\nNext steps:")
            print("1. Test billing reports in dashboard")
            print("2. Review WEEKLY_BILLING_FIXES.md for code changes needed")
            
        else:
            print("\n✓ Cleanup cancelled. No changes made.")
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
