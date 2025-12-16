"""
Add patient_id to provider_task_billing_status by joining from source provider_tasks tables.

This script:
1. Adds patient_id column to provider_task_billing_status if missing
2. Joins with provider_tasks_YYYY_MM tables to get actual patient_id
3. Updates all records with patient_id from source tasks
4. Verifies the data integrity
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = "production.db"


def add_patient_id_column():
    """Add patient_id column if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute("PRAGMA table_info(provider_task_billing_status);")
        cols = [row[1] for row in cursor.fetchall()]

        if "patient_id" not in cols:
            print("Adding patient_id column to provider_task_billing_status...")
            conn.execute("""
                ALTER TABLE provider_task_billing_status
                ADD COLUMN patient_id TEXT;
            """)
            conn.commit()
            print("✓ Column added successfully")
            return True
        else:
            print("✓ patient_id column already exists")
            return False
    except Exception as e:
        print(f"✗ Error adding column: {e}")
        return False
    finally:
        conn.close()


def get_all_provider_task_tables():
    """Get list of all provider_tasks_YYYY_MM tables"""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'provider_tasks_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    finally:
        conn.close()


def populate_patient_ids():
    """Update provider_task_billing_status with patient_id from source tables"""
    conn = sqlite3.connect(DB_PATH)
    try:
        tables = get_all_provider_task_tables()

        if not tables:
            print("✗ No provider_tasks tables found")
            return 0

        total_updated = 0

        for table_name in tables:
            print(f"\nProcessing {table_name}...")

            try:
                # Update using JOIN with source table
                cursor = conn.execute(f"""
                    UPDATE provider_task_billing_status
                    SET patient_id = (
                        SELECT pt.patient_id
                        FROM {table_name} pt
                        WHERE pt.provider_task_id = provider_task_billing_status.provider_task_id
                    )
                    WHERE provider_task_id IN (
                        SELECT provider_task_id FROM {table_name}
                    )
                    AND patient_id IS NULL
                """)

                updated = cursor.rowcount
                total_updated += updated
                print(f"  → Updated {updated} records")

            except Exception as e:
                print(f"  ✗ Error processing {table_name}: {e}")
                continue

        conn.commit()
        print(f"\n✓ Total records updated: {total_updated}")
        return total_updated

    except Exception as e:
        print(f"✗ Error: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


def verify_patient_ids():
    """Verify that patient_id is populated correctly"""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN patient_id IS NOT NULL THEN 1 END) as with_patient_id,
                COUNT(CASE WHEN patient_id IS NULL THEN 1 END) as without_patient_id
            FROM provider_task_billing_status
        """)

        row = cursor.fetchone()
        total = row[0]
        with_id = row[1]
        without_id = row[2]

        print("\nVerification Results:")
        print(f"  Total records: {total:,}")
        print(f"  With patient_id: {with_id:,}")
        print(f"  Without patient_id: {without_id:,}")

        if without_id > 0:
            print(f"\n⚠️  Warning: {without_id:,} records still missing patient_id")

            # Show sample of missing records
            cursor = conn.execute("""
                SELECT billing_status_id, provider_name, patient_name, provider_task_id
                FROM provider_task_billing_status
                WHERE patient_id IS NULL
                LIMIT 5
            """)

            print("\nSample of missing records:")
            for rec in cursor.fetchall():
                print(
                    f"  ID: {rec[0]}, Provider: {rec[1]}, Patient: {rec[2]}, Task ID: {rec[3]}"
                )
        else:
            print("\n✓ All records successfully populated with patient_id")

        return without_id == 0

    except Exception as e:
        print(f"✗ Verification error: {e}")
        return False
    finally:
        conn.close()


def main():
    """Main execution"""
    print("=" * 70)
    print("Add patient_id to provider_task_billing_status")
    print("=" * 70)

    # Step 1: Add column if needed
    print("\nStep 1: Checking/adding patient_id column...")
    add_patient_id_column()

    # Step 2: Populate patient_ids
    print("\nStep 2: Populating patient_id from source tables...")
    updated = populate_patient_ids()

    # Step 3: Verify
    print("\nStep 3: Verifying data integrity...")
    success = verify_patient_ids()

    # Summary
    print("\n" + "=" * 70)
    if success and updated > 0:
        print("✅ SUCCESS: patient_id column populated successfully")
    elif success:
        print("✅ SUCCESS: patient_id column already populated")
    else:
        print("⚠️  PARTIAL: Some records may still need patient_id")
    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
