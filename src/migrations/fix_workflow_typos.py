"""
Migration script to fix workflow template spelling and formatting issues

Issues to fix:
1. Template ID 18: "Closing caregap" -> "Closing Care Gap"
2. Template ID 19: "Closing Encoungters" -> "Closing Encounters"

Usage:
    python -m src.migrations.fix_workflow_typos
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database import get_db_connection


def fix_workflow_typos():
    """Fix spelling and formatting issues in workflow_templates table."""
    conn = get_db_connection()
    try:
        # Show current state
        print("Current workflow templates:")
        current = conn.execute(
            "SELECT template_id, template_name FROM workflow_templates WHERE template_id IN (18, 19) ORDER BY template_id"
        ).fetchall()
        for row in current:
            print(f"  ID {row['template_id']}: \"{row['template_name']}\"")

        # Fix Issue 1: Template ID 18 - "Closing caregap" -> "Closing Care Gap"
        conn.execute(
            "UPDATE workflow_templates SET template_name = 'Closing Care Gap' WHERE template_id = 18"
        )
        print(f"\n[OK] Fixed: Template ID 18 renamed to \"Closing Care Gap\"")

        # Fix Issue 2: Template ID 19 - "Closing Encoungters" -> "Closing Encounters"
        conn.execute(
            "UPDATE workflow_templates SET template_name = 'Closing Encounters' WHERE template_id = 19"
        )
        print(f"[OK] Fixed: Template ID 19 renamed to \"Closing Encounters\"")

        conn.commit()

        # Show updated state
        print("\nUpdated workflow templates:")
        updated = conn.execute(
            "SELECT template_id, template_name FROM workflow_templates WHERE template_id IN (18, 19) ORDER BY template_id"
        ).fetchall()
        for row in updated:
            print(f"  ID {row['template_id']}: \"{row['template_name']}\"")

        print("\n[SUCCESS] All workflow typos fixed!")

    except Exception as e:
        conn.rollback()
        print(f"Error fixing workflow typos: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    fix_workflow_typos()
