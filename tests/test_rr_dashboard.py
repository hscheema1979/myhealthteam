"""
Simple test runner for Results Reviewer dashboard
Run without Streamlit for quick validation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test_results_reviewer_apptest import tracker, run_all_tests

if __name__ == "__main__":
    print("\n" + "="*70)
    print("RESULTS REVIEWER DASHBOARD - AUTOMATED TESTS")
    print("="*70 + "\n")

    result = run_all_tests()

    print("\n" + "="*70)
    if result == 0:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*70 + "\n")

    sys.exit(result)
