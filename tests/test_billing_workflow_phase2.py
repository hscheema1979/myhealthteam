"""
Test Script for Phase 2 Billing Workflow Functions
Tests the four new database helper functions and dashboard integration
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import database


def test_mark_provider_tasks_as_billed():
    """Test marking provider tasks as billed"""
    print("\n" + "=" * 70)
    print("TEST 1: Mark Provider Tasks as Billed")
    print("=" * 70)

    try:
        # Get some pending tasks first
        conn = database.get_db_connection()
        pending = conn.execute("""
            SELECT billing_status_id FROM provider_task_billing_status
            WHERE is_billed = FALSE
            LIMIT 3
        """).fetchall()
        conn.close()

        if not pending:
            print("✗ No pending tasks found in database")
            return False

        task_ids = [row[0] for row in pending]
        print(f"Found {len(task_ids)} pending tasks: {task_ids}")

        # Mark as billed
        success, message, updated_count = database.mark_provider_tasks_as_billed(
            task_ids,
            user_id=1,  # Justin's user_id
        )

        if success:
            print(f"✓ {message}")
            print(f"  Updated: {updated_count} records")

            # Verify
            conn = database.get_db_connection()
            billed = conn.execute(
                """
                SELECT COUNT(*) FROM provider_task_billing_status
                WHERE billing_status_id IN ({})
                AND is_billed = TRUE
            """.format(",".join("?" * len(task_ids))),
                task_ids,
            ).fetchone()
            conn.close()

            if billed[0] == len(task_ids):
                print(f"✓ Verification: All {len(task_ids)} tasks marked as billed")
                return True
            else:
                print(
                    f"✗ Verification failed: Only {billed[0]} of {len(task_ids)} marked"
                )
                return False
        else:
            print(f"✗ {message}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_mark_coordinator_tasks_as_billed():
    """Test marking coordinator tasks as billed"""
    print("\n" + "=" * 70)
    print("TEST 2: Mark Coordinator Tasks as Billed")
    print("=" * 70)

    try:
        # Get some pending coordinator tasks
        conn = database.get_db_connection()
        pending = conn.execute("""
            SELECT summary_id FROM coordinator_monthly_summary
            WHERE is_billed = FALSE
            LIMIT 2
        """).fetchall()
        conn.close()

        if not pending:
            print("✗ No pending coordinator tasks found in database")
            return False

        summary_ids = [row[0] for row in pending]
        print(f"Found {len(summary_ids)} pending coordinator tasks: {summary_ids}")

        # Mark as billed
        success, message, updated_count = database.mark_coordinator_tasks_as_billed(
            summary_ids,
            user_id=1,  # Harpreet/Admin
        )

        if success:
            print(f"✓ {message}")
            print(f"  Updated: {updated_count} records")

            # Verify
            conn = database.get_db_connection()
            billed = conn.execute(
                """
                SELECT COUNT(*) FROM coordinator_monthly_summary
                WHERE summary_id IN ({})
                AND is_billed = TRUE
            """.format(",".join("?" * len(summary_ids))),
                summary_ids,
            ).fetchone()
            conn.close()

            if billed[0] == len(summary_ids):
                print(
                    f"✓ Verification: All {len(summary_ids)} coordinator tasks marked as billed"
                )
                return True
            else:
                print(
                    f"✗ Verification failed: Only {billed[0]} of {len(summary_ids)} marked"
                )
                return False
        else:
            print(f"✗ {message}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_approve_provider_payroll():
    """Test approving provider payroll"""
    print("\n" + "=" * 70)
    print("TEST 3: Approve Provider Payroll")
    print("=" * 70)

    try:
        # Get some pending payroll records
        conn = database.get_db_connection()
        pending = conn.execute("""
            SELECT payroll_id FROM provider_weekly_payroll_status
            WHERE is_approved = FALSE
            LIMIT 2
        """).fetchall()
        conn.close()

        if not pending:
            print("✗ No pending payroll records found in database")
            return False

        payroll_ids = [row[0] for row in pending]
        print(f"Found {len(payroll_ids)} pending payroll records: {payroll_ids}")

        # Approve
        success, message, updated_count = database.approve_provider_payroll(
            payroll_ids,
            user_id=1,  # Justin only
        )

        if success:
            print(f"✓ {message}")
            print(f"  Updated: {updated_count} records")

            # Verify
            conn = database.get_db_connection()
            approved = conn.execute(
                """
                SELECT COUNT(*) FROM provider_weekly_payroll_status
                WHERE payroll_id IN ({})
                AND is_approved = TRUE
            """.format(",".join("?" * len(payroll_ids))),
                payroll_ids,
            ).fetchone()
            conn.close()

            if approved[0] == len(payroll_ids):
                print(
                    f"✓ Verification: All {len(payroll_ids)} payroll records approved"
                )
                return True
            else:
                print(
                    f"✗ Verification failed: Only {approved[0]} of {len(payroll_ids)} approved"
                )
                return False
        else:
            print(f"✗ {message}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_mark_provider_payroll_as_paid():
    """Test marking provider payroll as paid"""
    print("\n" + "=" * 70)
    print("TEST 4: Mark Provider Payroll as Paid")
    print("=" * 70)

    try:
        # Get some approved but unpaid payroll records
        conn = database.get_db_connection()
        unpaid = conn.execute("""
            SELECT payroll_id FROM provider_weekly_payroll_status
            WHERE is_approved = TRUE
            AND is_paid = FALSE
            LIMIT 2
        """).fetchall()
        conn.close()

        if not unpaid:
            print("✗ No approved unpaid payroll records found in database")
            return False

        payroll_ids = [row[0] for row in unpaid]
        print(
            f"Found {len(payroll_ids)} approved unpaid payroll records: {payroll_ids}"
        )

        # Mark as paid
        success, message, updated_count = database.mark_provider_payroll_as_paid(
            payroll_ids,
            user_id=1,  # Justin
            payment_method="ACH",
            payment_reference="TEST_ACH_001",
        )

        if success:
            print(f"✓ {message}")
            print(f"  Updated: {updated_count} records")
            print(f"  Payment Method: ACH")
            print(f"  Reference: TEST_ACH_001")

            # Verify
            conn = database.get_db_connection()
            paid = conn.execute(
                """
                SELECT COUNT(*) FROM provider_weekly_payroll_status
                WHERE payroll_id IN ({})
                AND is_paid = TRUE
            """.format(",".join("?" * len(payroll_ids))),
                payroll_ids,
            ).fetchone()
            conn.close()

            if paid[0] == len(payroll_ids):
                print(
                    f"✓ Verification: All {len(payroll_ids)} payroll records marked as paid"
                )
                return True
            else:
                print(
                    f"✗ Verification failed: Only {paid[0]} of {len(payroll_ids)} marked as paid"
                )
                return False
        else:
            print(f"✗ {message}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_billing_workflow_status():
    """Test querying billing workflow status"""
    print("\n" + "=" * 70)
    print("TEST 5: Query Billing Workflow Status")
    print("=" * 70)

    try:
        conn = database.get_db_connection()

        # Query provider billing status
        provider_stats = conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN is_billed = TRUE THEN 1 END) as billed,
                COUNT(CASE WHEN is_invoiced = TRUE THEN 1 END) as invoiced,
                COUNT(CASE WHEN is_paid = TRUE THEN 1 END) as paid
            FROM provider_task_billing_status
        """).fetchone()

        print("\nProvider Task Billing Status:")
        print(f"  Total Tasks: {provider_stats[0]}")
        print(f"  Billed: {provider_stats[1]}")
        print(f"  Invoiced: {provider_stats[2]}")
        print(f"  Paid: {provider_stats[3]}")

        # Query coordinator billing status
        coordinator_stats = conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN is_billed = TRUE THEN 1 END) as billed,
                COUNT(CASE WHEN is_invoiced = TRUE THEN 1 END) as invoiced,
                COUNT(CASE WHEN is_paid = TRUE THEN 1 END) as paid
            FROM coordinator_monthly_summary
        """).fetchone()

        print("\nCoordinator Monthly Billing Status:")
        print(f"  Total Records: {coordinator_stats[0]}")
        print(f"  Billed: {coordinator_stats[1]}")
        print(f"  Invoiced: {coordinator_stats[2]}")
        print(f"  Paid: {coordinator_stats[3]}")

        # Query payroll status
        payroll_stats = conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN is_approved = TRUE THEN 1 END) as approved,
                COUNT(CASE WHEN is_paid = TRUE THEN 1 END) as paid
            FROM provider_weekly_payroll_status
        """).fetchone()

        print("\nProvider Weekly Payroll Status:")
        print(f"  Total Records: {payroll_stats[0]}")
        print(f"  Approved: {payroll_stats[1]}")
        print(f"  Paid: {payroll_stats[2]}")

        conn.close()

        if provider_stats[0] > 0 and coordinator_stats[0] > 0 and payroll_stats[0] > 0:
            print("\n✓ All workflow tables have data")
            return True
        else:
            print("\n✗ Some workflow tables are empty")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("=" * 70)
    print("PHASE 2 BILLING WORKFLOW TEST SUITE")
    print("=" * 70)

    results = {
        "Mark Provider Tasks as Billed": test_mark_provider_tasks_as_billed(),
        "Mark Coordinator Tasks as Billed": test_mark_coordinator_tasks_as_billed(),
        "Approve Provider Payroll": test_approve_provider_payroll(),
        "Mark Payroll as Paid": test_mark_provider_payroll_as_paid(),
        "Billing Workflow Status": test_billing_workflow_status(),
    }

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    print("\n" + "-" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("-" * 70)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
