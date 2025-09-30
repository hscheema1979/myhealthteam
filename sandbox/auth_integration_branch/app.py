import streamlit as st
import sqlite3
from src.database import (
    get_db_connection, get_user_roles, get_users, add_user, get_user_by_id,
    get_users_by_role, get_tasks_by_user, get_user_patient_assignments,
    get_coordinator_performance_metrics, get_provider_performance_metrics,
    get_tasks_billing_codes, get_all_users, get_user_roles_by_user_id,
    get_care_plan, update_care_plan, get_provider_id_from_user_id, get_patient_details_by_id
)
from src import database
from src.core_utils import get_user_role_ids
from src.dashboards import admin_dashboard, onboarding_dashboard, data_entry_dashboard, care_provider_dashboard_enhanced, care_coordinator_dashboard_enhanced
from src.auth_module import get_auth_manager, render_login_sidebar

def main():
    st.set_page_config(
        page_title="PCOPS - Primary Care Operations System",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Set sidebar title
    st.sidebar.title("🏥 PCOPS")
    
    # Initialize authentication manager
    auth_manager = get_auth_manager()
    
    # Render login sidebar (includes impersonation controls)
    render_login_sidebar(auth_manager)
    
    st.sidebar.markdown("---")
    
    # Display Current User Info (when authenticated)
    if auth_manager.is_authenticated():
        st.sidebar.markdown("### 👤 Current User")
        
        # Get user details from the authenticated user
        users = database.get_users()
        if users:
            authenticated_email = auth_manager.get_current_user()['email']
            current_user = next((user for user in users if user['email'] == authenticated_email), None)
            
            if current_user:
                # Display current user info (read-only)
                st.sidebar.info(f"**{current_user['full_name']}** ({current_user['username']})")
                
                # Set the user session state automatically based on authenticated user
                if 'user_id' not in st.session_state or st.session_state['user_id'] != current_user['user_id']:
                    st.session_state['user_id'] = current_user['user_id']
                    st.session_state['user_full_name'] = current_user['full_name']
                    # Get all role IDs for the user
                    user_role_ids = get_user_role_ids(current_user['user_id'])
                    st.session_state['user_role_ids'] = user_role_ids 

    # Display dashboard based on user and their roles
    if auth_manager.is_authenticated():
        user_id = auth_manager.get_user_id()
        user_role_ids = auth_manager.get_user_roles()
        
        # Get primary dashboard role based on role precedence
        primary_role = auth_manager.get_primary_dashboard_role()
        
        if primary_role:
            # Route to appropriate dashboard based on primary role
            if primary_role == 33:  # Provider
                care_provider_dashboard_enhanced.show(user_id, user_role_ids)
            elif primary_role == 36:  # Coordinator
                care_coordinator_dashboard_enhanced.show(user_id, user_role_ids)
            elif primary_role == 34:  # Admin
                admin_dashboard.show()
            elif primary_role == 35:  # Onboarding
                onboarding_dashboard.show()
            elif primary_role == 39:  # Data Entry
                data_entry_dashboard.show()
            else:
                st.error(f"Unrecognized primary role: {primary_role}")
                st.info("Please contact your administrator.")
        else:
            st.error(f"User has no recognized dashboard role. Roles: {user_role_ids}")
            st.info("Please contact your administrator.")
    else:
        # Landing page for users not logged in
        st.markdown("# 🏥 PCOPS - Primary Care Operations System")
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 50px; background-color: #f8f9fa; border-radius: 10px; border: 2px solid #e9ecef;">
                <h2 style="color: #495057;">🔐 Please Login for Access</h2>
                <p style="font-size: 18px; color: #6c757d; margin: 20px 0;">
                    Welcome to PCOPS! To access the system and view your dashboard, please login using one of the following methods:
                </p>
                <div style="text-align: left; margin: 30px 0;">
                    <h4 style="color: #495057;">Login Options:</h4>
                    <ul style="font-size: 16px; color: #6c757d;">
                        <li>🔑 <strong>Email/Password Login</strong> - Use the login form in the sidebar</li>
                        <li>🔓 <strong>Email-Only Login</strong> - For testing, just enter your email (no password required)</li>
                    </ul>
                </div>
                <div style="background-color: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="color: #1976d2; font-weight: bold;">
                        💡 Tip: If you're new to the system, try using the email-only login for quick testing
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        st.markdown("### 🎯 System Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <h3 style="color: #495057;">📊 Dashboards</h3>
                <p style="color: #6c757d;">Personalized dashboards based on your role</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <h3 style="color: #495057;">📈 Analytics</h3>
                <p style="color: #6c757d;">Real-time performance metrics and insights</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <h3 style="color: #495057;">🔒 Security</h3>
                <p style="color: #6c757d;">Secure access with role-based permissions</p>
            </div>
            """, unsafe_allow_html=True)

# Initialize the database

def init_database():
    """Initialize the database with required tables and data."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if database is already initialized
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            return
        
        # Initialize database schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                password_hash TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                role_id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (role_id) REFERENCES roles (role_id)
            )
        ''')
        
        # Insert default roles
        roles = [
            ('Admin', 'System Administrator'),
            ('Provider', 'Healthcare Provider'),
            ('Care Coordinator', 'Care Coordinator'),
            ('Onboarding', 'Onboarding Staff'),
            ('Data Entry', 'Data Entry Staff')
        ]
        cursor.executemany('INSERT INTO roles (role_name, description) VALUES (?, ?)', roles)
        
        # Insert default users
        users = [
            ('admin_user', 'admin@example.com', 'Admin User', 'admin123'),
            ('provider1', 'provider1@example.com', 'Dr. John Smith', 'provider123'),
            ('coordinator1', 'coordinator1@example.com', 'Sarah Johnson', 'coordinator123'),
            ('onboarding1', 'onboarding1@example.com', 'Mike Davis', 'onboarding123'),
            ('dataentry1', 'dataentry1@example.com', 'Lisa Wilson', 'dataentry123')
        ]
        cursor.executemany('INSERT INTO users (username, email, full_name, password_hash) VALUES (?, ?, ?, ?)', users)
        
        # Assign roles to users
        user_roles = [
            (1, 1),  # admin_user -> Admin
            (2, 2),  # provider1 -> Provider
            (3, 3),  # coordinator1 -> Care Coordinator
            (4, 4),  # onboarding1 -> Onboarding
            (5, 5)   # dataentry1 -> Data Entry
        ]
        cursor.executemany('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', user_roles)
        
        conn.commit()
        conn.close()
        
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    # Initialize database on first run
    init_database()
    main()