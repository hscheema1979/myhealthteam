"""
Dashboard modules package initialization.
This file makes all dashboard modules importable as part of the src.dashboards package.
"""

# Import and expose all dashboard modules
from .admin_dashboard import *
from .care_coordinator_dashboard_enhanced import *
from .care_provider_dashboard_enhanced import *
from .coordinator_manager_dashboard import *
from .data_entry_dashboard import *
from .justin_simple_payment_tracker import *
from .lead_coordinator_dashboard import *
from .monthly_coordinator_billing_dashboard import *
from .onboarding_dashboard import *
from .weekly_provider_billing_dashboard import *
from .weekly_provider_payroll_dashboard import *