"""
Advanced Streamlit App with Google OAuth Integration

This example demonstrates more advanced patterns for OAuth integration including:
- Custom OAuth configuration
- Role-based access control
- Session management
- Error handling
- Multi-page applications
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from the parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

from google_oauth_streamlit import GoogleOAuth, setup_oauth_ui, get_user_info, is_authenticated

# Configure the Streamlit page
st.set_page_config(
    page_title="Advanced OAuth App",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom configuration
ADMIN_EMAILS = [
    "harpreet@myhealthteam.org",
    "admin@example.com"
]

ALLOWED_DOMAINS = [
    "myhealthteam.org",
    "example.com"
]

def main():
    """Main application with advanced OAuth features."""
    
    st.title("🚀 Advanced OAuth Application")
    
    # Custom OAuth instance with specific configuration
    oauth = GoogleOAuth()
    
    # Setup OAuth with custom styling
    user_info = setup_oauth_ui(
        oauth_instance=oauth,
        login_button_text="🔐 Sign in with Google",
        logout_button_text="👋 Sign out"
    )
    
    if user_info:
        # Check access permissions
        if not check_access_permissions(user_info):
            show_access_denied()
            return
        
        # Show main application
        show_main_application(user_info)
    else:
        show_landing_page()


def check_access_permissions(user_info):
    """
    Check if user has permission to access the application.
    
    Args:
        user_info (dict): User information from Google
        
    Returns:
        bool: True if user has access, False otherwise
    """
    email = user_info.get('email', '').lower()
    
    # Check if email is in admin list
    if email in [admin.lower() for admin in ADMIN_EMAILS]:
        st.session_state.user_role = 'admin'
        return True
    
    # Check if email domain is allowed
    domain = email.split('@')[-1] if '@' in email else ''
    if domain in [d.lower() for d in ALLOWED_DOMAINS]:
        st.session_state.user_role = 'user'
        return True
    
    # Check if user has been explicitly granted access
    if check_user_whitelist(email):
        st.session_state.user_role = 'user'
        return True
    
    st.session_state.user_role = 'denied'
    return False


def check_user_whitelist(email):
    """
    Check if user is in the whitelist.
    In a real application, this would check a database.
    
    Args:
        email (str): User email
        
    Returns:
        bool: True if user is whitelisted
    """
    # In a real app, you would check a database here
    whitelisted_users = st.session_state.get('whitelisted_users', set())
    return email in whitelisted_users


def show_access_denied():
    """Show access denied message."""
    st.error("🚫 Access Denied")
    st.markdown("""
    Sorry, you don't have permission to access this application.
    
    **Possible reasons:**
    - Your email domain is not authorized
    - You haven't been granted access by an administrator
    - This is a private application
    
    Please contact your administrator if you believe this is an error.
    """)


def show_main_application(user_info):
    """Show the main application interface."""
    
    # Sidebar with user info and navigation
    setup_sidebar(user_info)
    
    # Main content area
    page = st.session_state.get('current_page', 'dashboard')
    
    if page == 'dashboard':
        show_dashboard(user_info)
    elif page == 'profile':
        show_profile(user_info)
    elif page == 'admin' and st.session_state.get('user_role') == 'admin':
        show_admin_panel(user_info)
    elif page == 'settings':
        show_settings(user_info)
    else:
        show_dashboard(user_info)


def setup_sidebar(user_info):
    """Setup the sidebar with navigation and user info."""
    
    with st.sidebar:
        st.markdown("### 👤 User Info")
        
        # User avatar and basic info
        if user_info.get('picture'):
            st.image(user_info['picture'], width=80)
        
        st.write(f"**{user_info.get('name', 'Unknown')}**")
        st.write(f"📧 {user_info.get('email', 'N/A')}")
        st.write(f"🏷️ {st.session_state.get('user_role', 'user').title()}")
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 🧭 Navigation")
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.current_page = 'profile'
            st.rerun()
        
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_page = 'settings'
            st.rerun()
        
        # Admin panel (only for admins)
        if st.session_state.get('user_role') == 'admin':
            if st.button("🔧 Admin Panel", use_container_width=True):
                st.session_state.current_page = 'admin'
                st.rerun()
        
        st.markdown("---")
        
        # Session info
        st.markdown("### 📊 Session Info")
        login_time = st.session_state.get('login_time', datetime.now())
        session_duration = datetime.now() - login_time
        st.write(f"⏱️ Session: {str(session_duration).split('.')[0]}")
        
        # Store login time if not already stored
        if 'login_time' not in st.session_state:
            st.session_state.login_time = datetime.now()


def show_dashboard(user_info):
    """Show the main dashboard."""
    
    st.header("📊 Dashboard")
    
    # Welcome message
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting = "Good morning"
    elif current_hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    
    st.markdown(f"### {greeting}, {user_info.get('given_name', user_info.get('name', 'User'))}! 👋")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", "1,234", "12")
    
    with col2:
        st.metric("Active Sessions", "89", "-3")
    
    with col3:
        st.metric("Success Rate", "98.5%", "0.2%")
    
    with col4:
        st.metric("Response Time", "245ms", "-12ms")
    
    # Charts and data
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Activity Trend")
        # Sample chart data
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range('2024-01-01', periods=30)
        data = pd.DataFrame({
            'Date': dates,
            'Users': np.random.randint(50, 200, 30),
            'Sessions': np.random.randint(100, 400, 30)
        })
        
        st.line_chart(data.set_index('Date'))
    
    with col2:
        st.subheader("🎯 User Distribution")
        
        # Sample pie chart data
        distribution_data = pd.DataFrame({
            'Role': ['Admin', 'User', 'Guest'],
            'Count': [5, 45, 20]
        })
        
        st.bar_chart(distribution_data.set_index('Role'))


def show_profile(user_info):
    """Show user profile page."""
    
    st.header("👤 User Profile")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if user_info.get('picture'):
            st.image(user_info['picture'], width=200)
        else:
            st.info("No profile picture available")
    
    with col2:
        st.subheader("Profile Information")
        
        # Display user information
        info_data = {
            "Full Name": user_info.get('name', 'N/A'),
            "Given Name": user_info.get('given_name', 'N/A'),
            "Family Name": user_info.get('family_name', 'N/A'),
            "Email": user_info.get('email', 'N/A'),
            "Email Verified": "✅ Yes" if user_info.get('verified_email') else "❌ No",
            "Google ID": user_info.get('id', 'N/A'),
            "Locale": user_info.get('locale', 'N/A'),
            "Role": st.session_state.get('user_role', 'user').title()
        }
        
        for key, value in info_data.items():
            st.write(f"**{key}:** {value}")
    
    st.markdown("---")
    
    # Raw user data (for debugging)
    with st.expander("🔍 Raw User Data (Debug)"):
        st.json(user_info)


def show_settings(user_info):
    """Show application settings."""
    
    st.header("⚙️ Settings")
    
    # User preferences
    st.subheader("User Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark", "Auto"],
            index=0
        )
        
        language = st.selectbox(
            "Language",
            ["English", "Spanish", "French", "German"],
            index=0
        )
        
        timezone = st.selectbox(
            "Timezone",
            ["UTC", "EST", "PST", "GMT"],
            index=0
        )
    
    with col2:
        notifications = st.checkbox("Enable Notifications", value=True)
        email_updates = st.checkbox("Email Updates", value=False)
        analytics = st.checkbox("Analytics Tracking", value=True)
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")
    
    st.markdown("---")
    
    # Session management
    st.subheader("Session Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Current Session:**")
        st.write(f"Login Time: {st.session_state.get('login_time', 'Unknown')}")
        st.write(f"Role: {st.session_state.get('user_role', 'user').title()}")
    
    with col2:
        if st.button("🔄 Refresh Session"):
            st.info("Session refreshed!")
        
        if st.button("🚪 End Session", type="secondary"):
            # This will trigger logout
            st.session_state.clear()
            st.rerun()


def show_admin_panel(user_info):
    """Show admin panel (only for admins)."""
    
    st.header("🔧 Admin Panel")
    
    if st.session_state.get('user_role') != 'admin':
        st.error("Access denied. Admin privileges required.")
        return
    
    # Admin tabs
    tab1, tab2, tab3 = st.tabs(["User Management", "System Settings", "Analytics"])
    
    with tab1:
        st.subheader("👥 User Management")
        
        # Add user to whitelist
        st.write("**Add User to Whitelist:**")
        new_email = st.text_input("Email Address")
        if st.button("➕ Add User"):
            if new_email:
                if 'whitelisted_users' not in st.session_state:
                    st.session_state.whitelisted_users = set()
                st.session_state.whitelisted_users.add(new_email.lower())
                st.success(f"Added {new_email} to whitelist")
        
        # Show current whitelist
        st.write("**Current Whitelist:**")
        whitelist = st.session_state.get('whitelisted_users', set())
        if whitelist:
            for email in whitelist:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(email)
                with col2:
                    if st.button("🗑️", key=f"remove_{email}"):
                        st.session_state.whitelisted_users.discard(email)
                        st.rerun()
        else:
            st.info("No users in whitelist")
    
    with tab2:
        st.subheader("⚙️ System Settings")
        
        # System configuration
        max_sessions = st.number_input("Max Concurrent Sessions", min_value=1, value=100)
        session_timeout = st.number_input("Session Timeout (minutes)", min_value=5, value=60)
        
        st.checkbox("Enable Debug Mode", value=False)
        st.checkbox("Maintenance Mode", value=False)
        
        if st.button("💾 Save System Settings"):
            st.success("System settings saved!")
    
    with tab3:
        st.subheader("📊 System Analytics")
        
        # Mock analytics data
        st.metric("Total Logins Today", "156", "23")
        st.metric("Active Users", "89", "12")
        st.metric("Error Rate", "0.2%", "-0.1%")
        
        # Sample analytics chart
        import pandas as pd
        import numpy as np
        
        analytics_data = pd.DataFrame({
            'Hour': range(24),
            'Logins': np.random.randint(0, 20, 24),
            'Errors': np.random.randint(0, 3, 24)
        })
        
        st.line_chart(analytics_data.set_index('Hour'))


def show_landing_page():
    """Show landing page for non-authenticated users."""
    
    st.markdown("""
    # 🚀 Welcome to Advanced OAuth App
    
    This application demonstrates advanced Google OAuth integration patterns including:
    
    ## ✨ Features
    - 🔐 **Secure Authentication** - Google OAuth 2.0
    - 👥 **Role-Based Access** - Admin and user roles
    - 🏢 **Domain Restrictions** - Control access by email domain
    - 📊 **Rich Dashboard** - Interactive data visualization
    - ⚙️ **User Settings** - Customizable preferences
    - 🔧 **Admin Panel** - User and system management
    
    ## 🛡️ Security Features
    - Email domain validation
    - User whitelisting
    - Session management
    - CSRF protection
    - Token revocation
    
    ## 🎯 Access Control
    - **Admins**: Full access to all features
    - **Users**: Access to dashboard and profile
    - **Domain-based**: Automatic access for approved domains
    - **Whitelist**: Manual approval for specific users
    
    ---
    
    **Ready to get started?** Click the login button above! 👆
    """)


if __name__ == "__main__":
    main()