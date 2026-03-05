"""
SuperAdmin Billing Dashboard

Restricted access page for billing reports and financial management.
Only accessible to Justin (user_id 18) and Harpreet (user_id 12).

URL: /superadmin

NOTE: This page is hidden from navigation by default. Access via:
- Direct URL: https://care.myhealthteam.org/superadmin
- Or navigate from Admin Dashboard when authorized
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import get_db_connection
from src.auth_module import AuthenticationManager
from src.config.ui_style_config import apply_custom_css, get_section_title


def check_billing_access(user_id: int) -> bool:
    """
    Check if user has access to billing dashboard.

    Args:
        user_id: Current user ID

    Returns:
        True if user is authorized (user_id in [12, 18])
    """
    return user_id in [12, 18]  # Harpreet=12, Justin=18


# Hide from navigation menu - only accessible via direct URL or button
st.set_page_config(
    page_title="SuperAdmin Billing",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_item=None  # Hide from sidebar navigation
)


def show_superadmin_dashboard():
    """Display the SuperAdmin billing dashboard."""

    # Apply professional styling
    apply_custom_css()

    # Page title
    st.title("💰 SuperAdmin Billing Dashboard")
    st.markdown("---")

    # Get current user
    current_user = st.session_state.get("authenticated_user")

    # Authentication check
    if not current_user or "user_id" not in current_user:
        st.error("Authentication required. Please log in.")
        st.info("Redirecting to login...")
        st.switch_page("app.py")
        return

    user_id = current_user["user_id"]
    user_email = current_user.get("email", "")

    # Authorization check
    if not check_billing_access(user_id):
        st.error("🚫 Access Denied")
        st.warning("You do not have permission to access the SuperAdmin Billing Dashboard.")
        st.info(
            """
            **Access Requirements:**
            - This page is restricted to authorized billing administrators only.
            - If you believe you should have access, please contact your system administrator.

            **Current User:**
            - Email: {}
            - User ID: {}
            """.format(
                user_email if user_email else "Not available", user_id
            )
        )
        st.markdown("---")
        if st.button("← Return to Main Dashboard", key="return_to_main"):
            st.switch_page("app.py")
        return

    # User is authorized - show billing dashboard
    st.success(f"✅ Authorized: {current_user.get('full_name', user_email)}")
    st.markdown("---")

    # Navigation
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("### Billing Reports & Financial Management")
    with col2:
        if st.button("← Back to Admin", key="back_to_admin", use_container_width=True):
            st.switch_page("app.py")

    st.markdown("---")

    # Create tabs for different billing views
    billing_tab1, billing_tab2, billing_tab3 = st.tabs(
        [
            "📊 Monthly Billing (Coordinators)",
            "📈 Weekly Billing (Providers)",
            "💳 Provider Payroll",
        ]
    )

    # Tab 1: Monthly Coordinator Billing
    with billing_tab1:
        st.subheader("Monthly Coordinator Billing Dashboard")
        st.markdown(
            """
            Track coordinator billing by month using patient minutes and billing codes.

            **Features:**
            - Monthly aggregation of coordinator tasks
            - Billing code assignment and validation
            - Minutes of service tracking
            - Performance metrics by coordinator
            """
        )
        st.markdown("---")

        try:
            from src.dashboards.monthly_coordinator_billing_dashboard import (
                display_monthly_coordinator_billing_dashboard,
            )

            display_monthly_coordinator_billing_dashboard()
        except Exception as e:
            st.error(f"Error loading monthly coordinator billing dashboard: {e}")
            st.info(
                "Please ensure the monthly coordinator billing dashboard module is properly configured."
            )

    # Tab 2: Weekly Provider Billing
    with billing_tab2:
        st.subheader("Weekly Provider Billing Dashboard")
        st.markdown(
            """
            Track provider billing by week using provider tasks and billing status.

            **Features:**
            - Weekly aggregation of provider tasks
            - Billing status tracking (Not Billed → Billed → Invoiced → Paid)
            - Visit type breakdown (New, Follow Up, Acute, Cognitive, TCM)
            - Performance metrics by provider
            """
        )
        st.markdown("---")

        try:
            from src.dashboards.weekly_provider_billing_dashboard_v2 import (
                display_weekly_provider_billing_dashboard,
            )

            display_weekly_provider_billing_dashboard()
        except Exception as e:
            st.error(f"Error loading weekly provider billing dashboard: {e}")
            st.info(
                "Please ensure the weekly provider billing dashboard module is properly configured."
            )

    # Tab 3: Weekly Provider Payroll
    with billing_tab3:
        st.subheader("Weekly Provider Payroll Dashboard")
        st.markdown(
            """
            Track provider payroll by week and mark providers as paid.

            **Features:**
            - Weekly payroll summary by provider
            - Payment status tracking (Paid / Unpaid)
            - Bulk payment approval workflow
            - Individual provider task breakdown
            - Payment history and audit trail
            """
        )
        st.markdown("---")

        try:
            from src.dashboards.weekly_provider_payroll_dashboard import (
                display_weekly_provider_payroll_dashboard,
            )

            display_weekly_provider_payroll_dashboard()
        except Exception as e:
            st.error(f"Error loading weekly provider payroll dashboard: {e}")
            st.info(
                "Please ensure the weekly provider payroll dashboard module is properly configured."
            )

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #7f7f7f; font-size: 0.9em;'>
        SuperAdmin Billing Dashboard • Access Restricted • Confidential Financial Data
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Check authentication
    if "authenticated_user" not in st.session_state or not st.session_state.get(
        "authenticated_user"
    ):
        st.switch_page("app.py")
    else:
        # Check authorization (only Justin 18 and Harpreet 12)
        current_user = st.session_state.get("authenticated_user")
        user_id = current_user.get("user_id") if current_user else None

        if not check_billing_access(user_id):
            st.error("🚫 Access Denied")
            st.warning("You do not have permission to access the SuperAdmin Billing Dashboard.")
            st.info("This page is restricted to authorized billing administrators only.")
            st.markdown("---")
            if st.button("← Return to Main Dashboard", key="return_to_main_unauthorized"):
                st.switch_page("app.py")
        else:
            show_superadmin_dashboard()
