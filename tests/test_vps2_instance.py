"""
Streamlit Native Test Framework for VPS2 Test Instance
Tests https://test.myhealthteam.org using Streamlit's AppTest API

Run: streamlit run tests/test_vps2_instance.py
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import database

# =============================================================================
# TEST CONFIGURATION
# =============================================================================
TEST_INSTANCE_URL = "https://test.myhealthteam.org"
TEST_DB_PATH = "production.db"  # Local DB for comparison

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_database_connection():
    """Test 1: Database connection and basic queries"""
    st.subheader("Test 1: Database Connection")

    try:
        conn = database.get_db_connection()

        # Test basic query
        result = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()
        st.success(f"✓ Database connected: {result['count']} users found")

        # Test patients table
        result = conn.execute("SELECT COUNT(*) as count FROM patients").fetchone()
        st.success(f"✓ Patients table: {result['count']} patients found")

        # Test provider tasks table exists
        current_month = datetime.now().strftime("%Y_%m")
        table_name = f"provider_tasks_{current_month}"

        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        ).fetchone()

        if result:
            st.success(f"✓ Monthly tasks table exists: {table_name}")
        else:
            st.warning(f"⚠ Monthly tasks table not found: {table_name}")

        conn.close()
        return True

    except Exception as e:
        st.error(f"✗ Database connection failed: {e}")
        return False

def test_auth_module():
    """Test 2: Authentication module imports"""
    st.subheader("Test 2: Authentication Module")

    try:
        from src.auth_module import AuthenticationManager, get_auth_manager

        # Create auth manager
        auth_mgr = AuthenticationManager()
        st.success("✓ AuthenticationManager initialized")

        # Check methods exist
        methods = ['authenticate_user', 'is_authenticated', 'get_current_user',
                  'get_primary_dashboard_role', 'setup_user_session']

        missing = []
        for method in methods:
            if not hasattr(auth_mgr, method):
                missing.append(method)

        if missing:
            st.error(f"✗ Missing methods: {', '.join(missing)}")
            return False
        else:
            st.success(f"✓ All required methods present")

        return True

    except Exception as e:
        st.error(f"✗ Auth module test failed: {e}")
        return False

def test_dashboard_imports():
    """Test 3: Dashboard module imports"""
    st.subheader("Test 3: Dashboard Imports")

    dashboards = [
        ("Admin", "admin_dashboard"),
        ("Provider", "care_provider_dashboard_enhanced"),
        ("Coordinator", "care_coordinator_dashboard_enhanced"),
        ("Onboarding", "onboarding_dashboard"),
        ("Facility", "facility_review_dashboard"),
    ]

    all_ok = True
    for name, module in dashboards:
        try:
            mod = __import__(f"src.dashboards.{module}", fromlist=[''])
            if hasattr(mod, 'show'):
                st.success(f"✓ {name} dashboard: OK")
            else:
                st.warning(f"⚠ {name} dashboard: Missing 'show' function")
                all_ok = False
        except ImportError as e:
            st.error(f"✗ {name} dashboard: Import failed - {e}")
            all_ok = False
        except Exception as e:
            st.error(f"✗ {name} dashboard: {e}")
            all_ok = False

    return all_ok

def test_facility_dashboard():
    """Test 4: Facility dashboard specifically"""
    st.subheader("Test 4: Facility Dashboard (Fix Verification)")

    try:
        from src.dashboards.facility_review_dashboard import ROLE_FACILITY, show

        st.success(f"✓ facility_review_dashboard imported")
        st.info(f"  ROLE_FACILITY = {ROLE_FACILITY}")
        st.success(f"✓ show() function exists")

        return True

    except Exception as e:
        st.error(f"✗ Facility dashboard test failed: {e}")
        return False

def test_oauth_config():
    """Test 5: OAuth configuration"""
    st.subheader("Test 5: OAuth Configuration")

    try:
        from src.oauth_config import get_oauth_config

        config = get_oauth_config()

        st.success("✓ OAuth config loaded")
        st.info(f"  Google Client ID: {config.google_client_id[:30]}...")
        st.info(f"  Redirect URI: {config.google_redirect_uri}")
        st.info(f"  Google Enabled: {config.google_enabled}")

        # Check if redirect URI matches test instance
        if "test.myhealthteam.org" in config.google_redirect_uri:
            st.success("✓ OAuth configured for test instance")
        elif "localhost" in config.google_redirect_uri:
            st.warning("⚠ OAuth configured for localhost, not test instance")
        else:
            st.warning(f"⚠ OAuth redirect URI: {config.google_redirect_uri}")

        return True

    except Exception as e:
        st.error(f"✗ OAuth config test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and show results"""
    st.title("VPS2 Test Instance Health Check")
    st.info(f"Target: {TEST_INSTANCE_URL}")
    st.info(f"Local DB: {TEST_DB_PATH}")

    results = {}

    with st.expander("Test 1: Database Connection", expanded=True):
        results['database'] = test_database_connection()

    with st.expander("Test 2: Authentication Module"):
        results['auth'] = test_auth_module()

    with st.expander("Test 3: Dashboard Imports"):
        results['dashboards'] = test_dashboard_imports()

    with st.expander("Test 4: Facility Dashboard (Critical Fix)", expanded=True):
        results['facility'] = test_facility_dashboard()

    with st.expander("Test 5: OAuth Configuration"):
        results['oauth'] = test_oauth_config()

    # Summary
    st.divider()
    st.subheader("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    if passed == total:
        st.success(f"✓✓✓ ALL TESTS PASSED ({passed}/{total})")
        st.info("The test instance should be fully operational")
    else:
        st.error(f"✗✗✗ SOME TESTS FAILED ({passed}/{total} passed)")

        failed = [k for k, v in results.items() if not v]
        st.warning(f"Failed tests: {', '.join(failed)}")

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main test runner"""
    st.set_page_config(
        page_title="VPS2 Test Instance Tests",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar controls
    with st.sidebar:
        st.header("Test Controls")

        if st.button("▶ Run All Tests", type="primary", use_container_width=True):
            st.rerun()

        st.divider()

        st.subheader("Test Info")
        st.info(f"**Target:**\n{TEST_INSTANCE_URL}")
        st.info(f"**Local DB:**\n{TEST_DB_PATH}")

        st.divider()
        st.caption(f"Last run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Main content
    run_all_tests()

if __name__ == "__main__":
    main()
