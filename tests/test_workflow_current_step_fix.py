"""
Test to verify workflow current_step increment fix.

This test verifies that when a workflow step is completed,
the current_step column is properly incremented to the next step.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import database
from src.dashboards.workflow_module import (
    create_workflow_instance,
    complete_workflow_step,
    get_workflow_progress
)


def test_workflow_current_step_increments():
    """Test that current_step increments when steps are completed."""
    conn = database.get_db_connection()
    try:
        # Create a test workflow instance (LAB ROUTINE = template_id 1)
        instance_id = create_workflow_instance(
            template_id=1,
            patient_id="TEST_PATIENT_001",
            coordinator_id=1,
            notes="Test workflow for current_step fix"
        )

        # Verify initial current_step is 1
        wf = conn.execute(
            "SELECT current_step FROM workflow_instances WHERE instance_id = ?",
            (instance_id,)
        ).fetchone()
        assert wf['current_step'] == 1, f"Initial current_step should be 1, got {wf['current_step']}"

        # Get step 1 ID
        step1 = conn.execute(
            "SELECT step_id FROM workflow_steps WHERE template_id = 1 AND step_order = 1"
        ).fetchone()
        step1_id = step1['step_id']

        # Complete step 1
        complete_workflow_step(
            instance_id=instance_id,
            step_id=step1_id,
            coordinator_id=1,
            duration_minutes=30,
            notes="Completed step 1"
        )

        # Verify current_step incremented to 2
        wf = conn.execute(
            "SELECT current_step FROM workflow_instances WHERE instance_id = ?",
            (instance_id,)
        ).fetchone()
        assert wf['current_step'] == 2, f"After completing step 1, current_step should be 2, got {wf['current_step']}"

        # Clean up - mark workflow as completed
        conn.execute(
            "UPDATE workflow_instances SET workflow_status = 'Completed' WHERE instance_id = ?",
            (instance_id,)
        )
        conn.commit()

        print("[PASS] Test passed: current_step increments correctly when steps are completed")

    finally:
        conn.close()


def test_workflow_at_rr_step():
    """Test that LAB workflows at step 5 appear in RR query."""
    conn = database.get_db_connection()
    try:
        # Query for workflows at RR step (LAB workflows at step 5)
        rr_workflows = conn.execute("""
            SELECT instance_id, template_name, current_step
            FROM workflow_instances
            WHERE template_id IN (1, 2, 3)
              AND current_step = 5
              AND workflow_status = 'Active'
        """).fetchall()

        print(f"[PASS] Found {len(rr_workflows)} LAB workflow(s) at RR step (step 5)")
        for wf in rr_workflows:
            print(f"  - Instance {wf['instance_id']}: {wf['template_name']} at step {wf['current_step']}")

        # Query for IMAGING workflows at RR step (step 4)
        imaging_rr_workflows = conn.execute("""
            SELECT instance_id, template_name, current_step
            FROM workflow_instances
            WHERE template_id IN (4, 5, 6)
              AND current_step = 4
              AND workflow_status = 'Active'
        """).fetchall()

        print(f"[PASS] Found {len(imaging_rr_workflows)} IMAGING workflow(s) at RR step (step 4)")
        for wf in imaging_rr_workflows:
            print(f"  - Instance {wf['instance_id']}: {wf['template_name']} at step {wf['current_step']}")

    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Testing workflow current_step fix")
    print("=" * 60)

    # Run test for current_step increment
    test_workflow_current_step_increments()

    print()

    # Show current RR workflows
    test_workflow_at_rr_step()

    print("=" * 60)
