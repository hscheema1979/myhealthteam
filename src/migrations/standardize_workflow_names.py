"""
Migration script to standardize all workflow template names to UPPERCASE

Before: Mixed case (LAB ROUTINE, Closing Care Gap, Medication Reconciliation, etc.)
After: All uppercase (LAB ROUTINE, CLOSING CARE GAP, MEDICATION RECONCILIATION, etc.)

Usage:
    python -m src.migrations.standardize_workflow_names
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database import get_db_connection


def standardize_workflow_names():
    """Standardize all workflow template names to uppercase."""
    conn = get_db_connection()
    try:
        # Get all workflows
        workflows = conn.execute(
            "SELECT template_id, template_name FROM workflow_templates ORDER BY template_id"
        ).fetchall()

        print("Current workflow templates:")
        for w in workflows:
            print(f"  ID {w['template_id']:2d}: {w['template_name']}")

        # Update all to uppercase
        print("\nStandardizing to uppercase...")
        updates_made = 0

        for w in workflows:
            template_id = w['template_id']
            old_name = w['template_name']
            new_name = old_name.upper()

            if old_name != new_name:
                conn.execute(
                    "UPDATE workflow_templates SET template_name = ? WHERE template_id = ?",
                    (new_name, template_id)
                )
                print(f"  [CHANGED] ID {template_id}: \"{old_name}\" -> \"{new_name}\"")
                updates_made += 1
            else:
                print(f"  [OK] ID {template_id}: \"{old_name}\" already uppercase")

        conn.commit()

        # Show final state
        print("\n" + "="*50)
        print("Updated workflow templates (all uppercase):")
        updated = conn.execute(
            "SELECT template_id, template_name FROM workflow_templates ORDER BY template_id"
        ).fetchall()
        for w in updated:
            print(f"  ID {w['template_id']:2d}: {w['template_name']}")

        print(f"\n[SUCCESS] Standardized {updates_made} workflow name(s) to uppercase!")

    except Exception as e:
        conn.rollback()
        print(f"Error standardizing workflow names: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    standardize_workflow_names()
