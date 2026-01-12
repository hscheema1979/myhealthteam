"""
Migration script to standardize workflow step owner names

Standardize "Care Coordinator" to "CC" for consistency

Usage:
    python -m src.migrations.standardize_workflow_owners
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database import get_db_connection


def standardize_workflow_owners():
    """Standardize workflow step owner names to abbreviations."""
    conn = get_db_connection()
    try:
        # Show current owner distribution
        print("Current owner values in workflow_steps:")
        owners = conn.execute(
            "SELECT DISTINCT owner FROM workflow_steps ORDER BY owner"
        ).fetchall()

        for o in owners:
            owner = o['owner']
            count = conn.execute(
                f"SELECT COUNT(*) as cnt FROM workflow_steps WHERE owner = '{owner}'"
            ).fetchone()['cnt']
            print(f"  \"{owner}\": {count} steps")

        # Standardize "Care Coordinator" -> "CC"
        print("\nStandardizing owner names...")
        updates_made = 0

        # Update "Care Coordinator" to "CC"
        care_coord_steps = conn.execute(
            "SELECT step_id, task_name FROM workflow_steps WHERE owner = 'Care Coordinator'"
        ).fetchall()

        if care_coord_steps:
            for step in care_coord_steps:
                conn.execute(
                    "UPDATE workflow_steps SET owner = 'CC' WHERE step_id = ?",
                    (step['step_id'],)
                )
                print(f"  [CHANGED] Step \"{step['task_name']}\": \"Care Coordinator\" -> \"CC\"")
                updates_made += 1
        else:
            print("  [OK] No \"Care Coordinator\" found (already standardized)")

        conn.commit()

        # Show final owner distribution
        print("\n" + "="*50)
        print("Updated owner values in workflow_steps:")
        owners_final = conn.execute(
            "SELECT DISTINCT owner FROM workflow_steps ORDER BY owner"
        ).fetchall()

        for o in owners_final:
            owner = o['owner']
            count = conn.execute(
                f"SELECT COUNT(*) as cnt FROM workflow_steps WHERE owner = '{owner}'"
            ).fetchone()['cnt']
            print(f"  \"{owner}\": {count} steps")

        print(f"\n[SUCCESS] Standardized {updates_made} workflow step owner(s)!")

    except Exception as e:
        conn.rollback()
        print(f"Error standardizing workflow owners: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    standardize_workflow_owners()
