"""
Authentication Module for PCOPS

This module handles user authentication, session management, and user-related operations.
It supports both email/password and OAuth authentication methods.
"""

import streamlit as st
import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from src.database import get_db_connection
from src.core_utils import get_user_role_ids
from streamlit_js_eval import streamlit_js_eval


class AuthenticationManager:
    """Manages user authentication and session handling"""
    
    def __init__(self):
        self.session_state = st.session_state
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables"""
        if 'authenticated_user' not in self.session_state:
            self.session_state['authenticated_user'] = None
        if 'login_method' not in self.session_state:
            self.session_state['login_method'] = None
        if 'user_id' not in self.session_state:
            self.session_state['user_id'] = None
        if 'user_role_ids' not in self.session_state:
            self.session_state['user_role_ids'] = []
        if 'impersonating_user' not in self.session_state:
            self.session_state['impersonating_user'] = None
        if 'original_user' not in self.session_state:
            self.session_state['original_user'] = None
        if 'remember_me' not in self.session_state:
            self.session_state['remember_me'] = False
        if 'persistent_login_checked' not in self.session_state:
            self.session_state['persistent_login_checked'] = False
        
        # Check for persistent login on first load
        if not self.session_state['persistent_login_checked']:
            self._check_persistent_login()
            self.session_state['persistent_login_checked'] = True
    
    def authenticate_by_email_only(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user by email only (for testing purposes)
        
        Args:
            email: User's email address
            
        Returns:
            User dictionary if authenticated, None otherwise
        """
        conn = get_db_connection()
        try:
            user = conn.execute("""
                SELECT user_id, username, email, first_name, last_name, full_name, status 
                FROM users 
                WHERE email = ? AND status = 'active'
            """, (email,)).fetchone()
            
            if user:
                # Update last login timestamp
                conn.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                """, (user['user_id'],))
                conn.commit()
                return dict(user)
            return None
        except sqlite3.Error as e:
            print(f"Authentication error: {e}")
            return None
        finally:
            conn.close()
    
    def authenticate_by_email_and_password(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user by email and password
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            User dictionary if authenticated, None otherwise
        """
        import hashlib
        
        # Hash the input password for comparison
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        try:
            user = conn.execute("""
                SELECT user_id, username, email, first_name, last_name, full_name, status 
                FROM users 
                WHERE email = ? AND password = ? AND status = 'active'
            """, (email, hashed_password)).fetchone()
            
            if user:
                # Update last login timestamp
                conn.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                """, (user['user_id'],))
                conn.commit()
                return dict(user)
            return None
        except sqlite3.Error as e:
            print(f"Authentication error: {e}")
            return None
        finally:
            conn.close()
    
    def authenticate_user(self, email: str, password: Optional[str] = None, 
                         auth_method: str = "email_password") -> Optional[Dict[str, Any]]:
        """
        Main authentication method that requires password by default
        
        Args:
            email: User's email address
            password: User's password (required)
            auth_method: "email_password" (default) or "email_only" 
            
        Returns:
            User dictionary if authenticated, None otherwise
        """
        # Password is required by default
        if auth_method == "email_password":
            if password is None:
                return None
            return self.authenticate_by_email_and_password(email, password)
        elif auth_method == "email_only":
            # Only allow email-only if explicitly requested (for backward compatibility)
            return self.authenticate_by_email_only(email)
        else:
            return None
    
    def _save_persistent_login(self, user: Dict[str, Any]):
        """Save login state for persistence using browser localStorage"""
        try:
            # Create persistent data for localStorage
            persistent_data = {
                'user_id': user['user_id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in browser localStorage
            js_code = f"""
            localStorage.setItem('persistent_login', '{json.dumps(persistent_data)}');
            """
            streamlit_js_eval(js_code)
            
            # Also keep a copy in session state for immediate access
            st.session_state['_persistent_login_data'] = persistent_data
            
        except Exception as e:
            print(f"Error saving persistent login: {e}")

    def _check_persistent_login(self):
        """Check for and restore persistent login state from browser cookies"""
        try:
            # First check session state for immediate access
            persistent_data = st.session_state.get('_persistent_login_data')
            
            # If not in session state, check browser cookies
            if not persistent_data:
                try:
                    cookie_manager = cookies.CookieManager()
                    cookie_data = cookie_manager.get('persistent_login')
                    if cookie_data:
                        persistent_data = json.loads(cookie_data)
                        # Store in session state for this session
                        st.session_state['_persistent_login_data'] = persistent_data
                except Exception as cookie_error:
                    print(f"Error reading cookie: {cookie_error}")
                    return False
            
            if persistent_data and not self.is_authenticated():
                # Check if the persistent login is still valid (within 30 days)
                login_time = datetime.fromisoformat(persistent_data['timestamp'])
                if (datetime.now() - login_time).days <= 30:
                    
                    # Verify the user still exists and is active
                    user = self.get_user_by_email_simple(persistent_data['email'])
                    if user and user['user_id'] == persistent_data['user_id']:
                        # Restore the session
                        self.setup_user_session(user, 'persistent', True)
                        self.session_state['remember_me'] = True
                        return True
                else:
                    # Clear expired persistent login
                    self._clear_persistent_login()
            
        except Exception as e:
            print(f"Error checking persistent login: {e}")
            self._clear_persistent_login()
        
        return False

    def _clear_persistent_login(self):
        """Clear persistent login data from both session state and browser cookies"""
        try:
            # Clear from session state
            if '_persistent_login_data' in st.session_state:
                del st.session_state['_persistent_login_data']
            
            # Clear from browser cookie
            cookie_manager = cookies.CookieManager()
            if 'persistent_login' in cookie_manager:
                del cookie_manager['persistent_login']
                
        except Exception as e:
            print(f"Error clearing persistent login: {e}")
    
    def setup_user_session(self, user: Dict[str, Any], login_method: str, remember_me: bool = False):
        """
        Setup user session after successful authentication
        
        Args:
            user: User dictionary from authentication
            login_method: Method used for login ("email_only" or "email_password")
            remember_me: Whether to save persistent login data
        """
        self.session_state['authenticated_user'] = user
        self.session_state['login_method'] = login_method
        self.session_state['user_id'] = user['user_id']
        self.session_state['user_full_name'] = user['full_name'] or f"{user['first_name']} {user['last_name']}"
        self.session_state['remember_me'] = remember_me
        
        # Get user role IDs
        user_role_ids = get_user_role_ids(user['user_id'])
        self.session_state['user_role_ids'] = user_role_ids
        
        # Save persistent login if remember_me is enabled
        if remember_me and login_method != 'persistent':
            self._save_persistent_login(user)
    
    def logout_user(self, clear_persistent: bool = True):
        """
        Clear user session and logout
        
        Args:
            clear_persistent: Whether to clear persistent login data (default: True)
        """
        self.session_state['authenticated_user'] = None
        self.session_state['login_method'] = None
        self.session_state['remember_me'] = False
        
        # Clear user-related session data
        keys_to_clear = ['user_id', 'user_full_name', 'user_role_ids']
        for key in keys_to_clear:
            if key in self.session_state:
                del self.session_state[key]
        
        # Clear persistent login if requested
        if clear_persistent:
            self._clear_persistent_login()
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return self.session_state.get('authenticated_user') is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        return self.session_state.get('authenticated_user')
    
    def get_user_roles(self) -> List[int]:
        """Get current user's role IDs"""
        return self.session_state.get('user_role_ids', [])
    
    def get_user_id(self) -> Optional[int]:
        """Get current user's ID"""
        return self.session_state.get('user_id')
    
    def get_user_full_name(self) -> Optional[str]:
        """Get current user's full name"""
        return self.session_state.get('user_full_name')
    
    def has_role(self, role_id: int) -> bool:
        """Check if user has a specific role"""
        return role_id in self.get_user_roles()
    
    def has_any_role(self, role_ids: List[int]) -> bool:
        """Check if user has any of the specified roles"""
        user_roles = self.get_user_roles()
        return any(role_id in user_roles for role_id in role_ids)
    
    def get_primary_dashboard_role(self) -> Optional[int]:
        """
        Get the primary dashboard role for the user based on role precedence
        
        Role precedence: Provider (33) > Coordinator (36) > Admin (34) > Onboarding (35) > Data Entry (39)
        
        Returns:
            Primary role ID or None if no recognized role
        """
        user_roles = self.get_user_roles()
        
        # Define role precedence (higher priority first)
        role_precedence = [33, 36, 34, 35, 39]  # Provider, Coordinator, Admin, Onboarding, Data Entry
        
        for role_id in role_precedence:
            if role_id in user_roles:
                return role_id
        
        return None
    
    def get_user_by_email_simple(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email for simple lookup (no authentication)
        
        Args:
            email: User's email address
            
        Returns:
            User dictionary if found, None otherwise
        """
        conn = get_db_connection()
        try:
            user = conn.execute("""
                SELECT user_id, username, email, first_name, last_name, full_name, status 
                FROM users 
                WHERE email = ? AND status = 'active'
            """, (email,)).fetchone()
            return dict(user) if user else None
        except sqlite3.Error as e:
            print(f"Error getting user by email: {e}")
            return None
        finally:
            conn.close()
    
    def start_impersonation(self, target_user_id: int) -> bool:
        """
        Start impersonating another user (admin only)
        
        Args:
            target_user_id: ID of the user to impersonate
            
        Returns:
            True if impersonation started successfully, False otherwise
        """
        # Only allow impersonation if current user is admin
        if not self.has_role(34):  # Admin role ID
            return False
        
        # Get the target user
        conn = get_db_connection()
        try:
            target_user = conn.execute("""
                SELECT user_id, username, email, first_name, last_name, full_name, status 
                FROM users 
                WHERE user_id = ? AND status = 'active'
            """, (target_user_id,)).fetchone()
            
            if not target_user:
                return False
            
            # Store original user before switching
            original_user = self.get_current_user()
            
            # Switch to target user
            target_user_dict = dict(target_user)
            self.session_state['impersonating_user'] = target_user_dict
            self.session_state['original_user'] = original_user
            
            # Setup session for target user
            self.setup_user_session(target_user_dict, 'impersonation')
            
            return True
            
        except sqlite3.Error as e:
            print(f"Impersonation error: {e}")
            return False
        finally:
            conn.close()
    
    def stop_impersonation(self) -> bool:
        """
        Stop impersonation and return to original user
        
        Returns:
            True if impersonation stopped successfully, False otherwise
        """
        if not self.is_impersonating():
            return False
        
        # Restore original user
        original_user = self.session_state.get('original_user')
        if original_user:
            self.setup_user_session(original_user, self.session_state.get('login_method', 'email_only'))
        else:
            # Fallback: logout completely
            self.logout_user()
        
        # Clear impersonation state
        self.session_state['impersonating_user'] = None
        self.session_state['original_user'] = None
        
        return True
    
    def is_impersonating(self) -> bool:
        """Check if currently impersonating another user"""
        return self.session_state.get('impersonating_user') is not None
    
    def get_original_user(self) -> Optional[Dict[str, Any]]:
        """Get the original user (before impersonation)"""
        return self.session_state.get('original_user')
    
    def get_all_active_users(self) -> List[Dict[str, Any]]:
        """Get all active users"""
        conn = get_db_connection()
        try:
            users = conn.execute("""
                SELECT user_id, username, email, first_name, last_name, full_name, status 
                FROM users 
                WHERE status = 'active'
                ORDER BY full_name
            """).fetchall()
            return [dict(user) for user in users]
        except sqlite3.Error as e:
            print(f"Error getting active users: {e}")
            return []
        finally:
            conn.close()
    
    def get_all_users_for_dropdown(self) -> List[Dict[str, Any]]:
        """Get all users formatted for dropdown selection"""
        conn = get_db_connection()
        try:
            users = conn.execute("""
                SELECT u.user_id, u.username, u.email, u.first_name, u.last_name, u.full_name, 
                       u.status, r.role_name
                FROM users u
                LEFT JOIN user_roles ur ON u.user_id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.role_id
                WHERE u.status = 'active'
                ORDER BY u.full_name
            """).fetchall()
            
            user_list = []
            for user in users:
                user_dict = dict(user)
                # Create display name with role info
                display_name = f"{user_dict['full_name']} ({user_dict['role_name'] or 'No Role'}) - {user_dict['email']}"
                user_dict['display_name'] = display_name
                user_list.append(user_dict)
            
            return user_list
        except sqlite3.Error as e:
            print(f"Error getting users for dropdown: {e}")
            return []
        finally:
            conn.close()


def get_auth_manager() -> AuthenticationManager:
    """Get an instance of the authentication manager"""
    return AuthenticationManager()


def require_authentication(auth_manager: Optional[AuthenticationManager] = None) -> Dict[str, Any]:
    """
    Decorator/function to require authentication for a page
    
    Args:
        auth_manager: AuthenticationManager instance (optional)
        
    Returns:
        User information if authenticated
        
    Raises:
        st.stop(): Stops execution if not authenticated
    """
    if auth_manager is None:
        auth_manager = get_auth_manager()
    
    if not auth_manager.is_authenticated():
        st.warning("Please log in to access this page.")
        st.stop()
    
    return auth_manager.get_current_user()


def render_login_sidebar(auth_manager: Optional[AuthenticationManager] = None):
    """
    Render login UI in the sidebar
    
    Args:
        auth_manager: AuthenticationManager instance (optional)
    """
    if auth_manager is None:
        auth_manager = get_auth_manager()
    
    # Show impersonation warning if active
    if auth_manager.is_impersonating():
        original_user = auth_manager.get_original_user()
        current_user = auth_manager.get_current_user()
        if current_user:
            st.sidebar.warning(f"🔍 Impersonating: {current_user.get('full_name', 'Unknown')}")
        else:
            st.sidebar.warning("🔍 Impersonating: Unknown User")
        if st.sidebar.button("⏹️ Stop Impersonating", key="stop_impersonation"):
            auth_manager.stop_impersonation()
            st.rerun()
    
    st.sidebar.markdown("### Login")
    
    if not auth_manager.is_authenticated():
        with st.sidebar.form("login_form"):
            email = st.text_input("Email", placeholder="user@example.com")
            
            # Password is required by default - no checkbox needed
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            require_password = True
            
            # Remember Me checkbox for persistent login
            remember_me = st.checkbox("Remember Me", value=False, help="Stay logged in for 30 days")
            
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if email:
                    # Always use password authentication
                    user = auth_manager.authenticate_user(email, password, "email_password")
                    
                    if user:
                        auth_manager.setup_user_session(user, "email_password", remember_me)
                        st.sidebar.success(f"Welcome, {auth_manager.get_user_full_name()}!")
                        st.rerun()
                    else:
                        st.sidebar.error("Authentication failed. Please check your credentials.")
                else:
                    st.sidebar.error("Please enter your email")
    else:
        # Show logged in user info and logout button
        if auth_manager.is_impersonating():
            original_user = auth_manager.get_original_user()
            if original_user:
                st.sidebar.info(f"Original: {original_user.get('full_name', 'Unknown')}")
            else:
                st.sidebar.info("Original: Unknown User")
        else:
            st.sidebar.success(f"Logged in as: {auth_manager.get_user_full_name()}")
        
        # Admin impersonation dropdown
        if auth_manager.has_role(34) and not auth_manager.is_impersonating():  # Admin role ID
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 🔍 User Impersonation")
            
            # Get all users for dropdown
            all_users = auth_manager.get_all_users_for_dropdown()
            if all_users:
                user_options = {user['display_name']: user['user_id'] for user in all_users}
                selected_user_display = st.sidebar.selectbox(
                    "Select User to Test:",
                    options=list(user_options.keys()),
                    key="impersonate_dropdown"
                )
                
                if st.sidebar.button("🎭 Start Impersonating", key="start_impersonation"):
                    if selected_user_display:
                        target_user_id = user_options[selected_user_display]
                        if auth_manager.start_impersonation(target_user_id):
                            st.sidebar.success(f"Now impersonating {selected_user_display}")
                            st.rerun()
                        else:
                            st.sidebar.error("Failed to start impersonation")
        
        # Show logout options
        st.sidebar.markdown("---")
        
        # Show if user has persistent login enabled
        if auth_manager.session_state.get('remember_me', False):
            st.sidebar.info("🔒 Persistent login enabled")
            
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("Logout", key="logout_temp", help="Logout but keep persistent login"):
                    auth_manager.logout_user(clear_persistent=False)
                    st.rerun()
            with col2:
                if st.button("Full Logout", key="logout_full", help="Logout and clear persistent login"):
                    auth_manager.logout_user(clear_persistent=True)
                    st.rerun()
        else:
            if st.sidebar.button("Logout"):
                auth_manager.logout_user()
                st.rerun()


def get_dashboard_for_user(auth_manager: Optional[AuthenticationManager] = None) -> Optional[int]:
    """
    Get the appropriate dashboard for the current user based on their roles
    
    Args:
        auth_manager: AuthenticationManager instance (optional)
        
    Returns:
        Dashboard role ID or None if no appropriate dashboard
    """
    if auth_manager is None:
        auth_manager = get_auth_manager()
    
    return auth_manager.get_primary_dashboard_role()