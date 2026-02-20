#!/usr/bin/env python3
"""
Fix workflow current_step values for workflows that have completed steps
but the current_step column was not properly incremented.

This script updates the current_step to point to the next incomplete step.
If all steps are complete, current_step points to the last step.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import database


def fix_workflow_current_step(db_path=None, dry_run=True):
    """
    Fix current_step values for all active workflows.

    Args:
        db_path: Path to database (uses default if None)
        dry_run: If True, print changes without applying them

    Returns:
        Dict with counts of workflows to be fixed
    """
    conn = database.get_db_connection(db_path)

    try:
        # Get all active workflows with LAB/IMAGING templates (1-6)
        workflows = conn.execute("""
            SELECT instance_id, template_id, template_name, current_step
            FROM workflow_instances
            WHERE workflow_status = 'Active'
            AND template_id IN (1, 2, 3, 4, 5, 6)
        """).fetchall()

        fixes_needed = []

        for wf in workflows:
            instance_id = wf['instance_id']
            template_id = wf['template_id']
            current_step = wf['current_step']

            # Get all steps for this workflow instance
            steps = conn.execute("""
                SELECT step1_complete, step2_complete, step3_complete,
                       step4_complete, step5_complete
                FROM workflow_instances
                WHERE instance_id = ?
            """, (instance_id,)).fetchone()

            if not steps:
                continue

            # Find the first incomplete step
            new_current_step = current_step
            for step_num in range(1, 6):  # Check steps 1-5
                step_col = f"step{step_num}_complete"
                if step_col in steps.keys():
                    is_complete = steps[step_col]
                    if is_complete == 1:
                        # Step is complete, move to next
                        continue
                    else:
                        # Found first incomplete step
                        new_current_step = step_num
                        break
            else:
                # All steps 1-5 are complete, check if there's a step 5
                if 'step5_complete' in steps.keys() and steps['step5_complete'] == 1:
                    new_current_step = 5  # Stay at step 5 (RR step for LAB)

            # For IMAGING (templates 4-6), max step is 4
            if template_id in [4, 5, 6]:
                # Check if step 4 is complete
                if 'step4_complete' in steps.keys() and steps['step4_complete'] == 1:
                    new_current_step = 4  # Stay at step 4 (RR step for IMAGING)

            if new_current_step != current_step:
                fixes_needed.append({
                    'instance_id': instance_id,
                    'template_name': wf['template_name'],
                    'old_current_step': current_step,
                    'new_current_step': new_current_step
                })

        # Apply fixes
        if dry_run:
            print(f"DRY RUN - Would fix {len(fixes_needed)} workflows:")
            for fix in fixes_needed:
                print(f"  Instance {fix['instance_id']} ({fix['template_name']}): "
                      f"step {fix['old_current_step']} -> {fix['new_current_step']}")
        else:
            print(f"Applying fixes to {len(fixes_needed)} workflows...")
            for fix in fixes_needed:
                conn.execute(
                    "UPDATE workflow_instances SET current_step = ? WHERE instance_id = ?",
                    (fix['new_current_step'], fix['instance_id'])
                )
                print(f"  Fixed instance {fix['instance_id']} ({fix['template_name']}): "
                      f"step {fix['old_current_step']} -> {fix['new_current_step']}")

            conn.commit()
            print("Done!")

        return {
            'total_workflows': len(workflows),
            'fixes_needed': len(fixes_needed),
            'fixes': fixes_needed
        }

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fix workflow current_step values")
    parser.add_argument('--apply', action='store_true',
                        help='Apply fixes (default is dry-run)')
    parser.add_argument('--db', type=str,
                        help='Path to database file')

    args = parser.parse_args()

    print("=" * 60)
    print("Workflow current_step Fix Utility")
    print("=" * 60)

    result = fix_workflow_current_step(db_path=args.db, dry_run=not args.apply)

    print()
    print(f"Total workflows checked: {result['total_workflows']}")
    print(f"Workflows needing fix: {result['fixes_needed']}")

    if not args.apply and result['fixes_needed'] > 0:
        print()
        print("Run with --apply to apply these fixes")

    print("=" * 60)
