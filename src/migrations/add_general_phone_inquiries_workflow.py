"""
Migration script to add General Phone Inquiries workflow

This script adds a simple single-step workflow for handling general phone calls
that don't fall under other existing workflow categories.

Usage:
    python -m src.migrations.add_general_phone_inquiries_workflow
"""

import sys
import os

# Add the parent directory to the path so we can import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database import get_db_connection


def add_general_phone_inquiries_workflow():
    """Add the General Phone Inquiries workflow to the database."""
    conn = get_db_connection()
    try:
        # Check if workflow already exists
        existing = conn.execute(
            "SELECT template_id, template_name FROM workflow_templates WHERE template_name = 'General Phone Inquiries'"
        ).fetchone()

        if existing:
            print(f"Workflow 'General Phone Inquiries' already exists (template_id: {existing['template_id']})")
            return

        # Insert template
        cursor = conn.execute(
            "INSERT INTO workflow_templates (template_name) VALUES ('General Phone Inquiries')"
        )
        template_id = cursor.lastrowid
        print(f"Created workflow template: {template_id}")

        # Insert the single step
        conn.execute(
            """INSERT INTO workflow_steps (template_id, step_order, task_name, owner, deliverable, cycle_time)
            VALUES (?, 1, 'General Phone Inquiries', 'CC', 'Progress notes added if needed', NULL)""",
            (template_id,)
        )
        conn.commit()

        print("Successfully added 'General Phone Inquiries' workflow:")
        print(f"  - Template ID: {template_id}")
        print(f"  - Template Name: General Phone Inquiries")
        print(f"  - Step 1: General Phone Inquiries (Owner: CC)")
        print(f"  - Deliverable: Progress notes added if needed")

    except Exception as e:
        conn.rollback()
        print(f"Error adding workflow: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    add_general_phone_inquiries_workflow()
