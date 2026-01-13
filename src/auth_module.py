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
from src import database
from src.database import get_db_connection
from src.core_utils import get_user_role_ids
from src.oauth_config import get_oauth_config
from src.google_oauth import (
    get_google_auth_url,
    handle_google_oauth_callback,
)
from streamlit_js_eval import streamlit_js_eval

# Optional CookieManager from extra_streamlit_components
try:
    import extra_streamlit_components as stx
    CookieManager = stx.CookieManager
except Exception:
    CookieManager = None


class AuthenticationManager:
    """Manages user authentication and session handling"""
    
    def __init__(self):
        self.session_state = st.session_state
        # Initialize a single CookieManager instance with a unique key if available
        self.cookie_manager = None
        if CookieManager is not None:
            try:
                self.cookie_manager = CookieManager(key="auth_cookie_manager")
            except Exception:
                self.cookie_manager = None
        # Key counter for streamlit_js_eval to avoid duplicate keys
        if '_sje_counter' not in self.session_state:
            self.session_state['_sje_counter'] = 0
        
        self._init_session_state()

    def _next_sje_key(self, base: str) -> str:
        c = int(self.session_state.get('_sje_counter', 0))
        key = f"{base}_{c}"
        self.session_state['_sje_counter'] = c + 1
        return key
    
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

        # Defer persistent login restore to UI mount to avoid duplicate component keys
    
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
        print(f"Authenticating email: {email}")
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        print(f"Hashed password for {email}: {hashed_password}")
        
        conn = get_db_connection()
        print(f"DB connection obtained in auth_module for {email}")
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

    def authenticate_with_google_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user using Google OAuth authorization code

        Args:
            code: Authorization code from Google OAuth callback

        Returns:
            User dictionary if authenticated, None otherwise
        """
        try:
            user = handle_google_oauth_callback(code)
            if user:
                # Update last login timestamp
                conn = get_db_connection()
                try:
                    conn.execute("""
                        UPDATE users
                        SET last_login = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (user['user_id'],))
                    conn.commit()
                except sqlite3.Error as e:
                    print(f"Error updating last login: {e}")
                finally:
                    conn.close()
            return user
        except Exception as e:
            print(f"Google authentication error: {e}")
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
            js_code = f"localStorage.setItem('persistent_login', '{json.dumps(persistent_data)}')"
            streamlit_js_eval(js_expressions=js_code, key=self._next_sje_key("persistent_set"))
            
            # Also keep a copy in session state for immediate access
            st.session_state['_persistent_login_data'] = persistent_data

            try:
                sid = database.create_user_session(user['user_id'], days_valid=30)
                st.session_state['_persistent_session_id'] = sid
                persistent_data['session_id'] = sid
                try:
                    st.query_params['session_id'] = sid
                except Exception:
                    pass
            except Exception as e:
                print(f"Error creating server session: {e}")

            if self.cookie_manager is not None:
                try:
                    self.cookie_manager.set('persistent_login', json.dumps(persistent_data), key=self._next_sje_key("cookie_set"))
                except Exception as cookie_error:
                    print(f"Error setting persistent login cookie: {cookie_error}")
            
        except Exception as e:
            print(f"Error saving persistent login: {e}")

    def _check_persistent_login(self):
        """Check for and restore persistent login state from browser storage"""
        try:
            # Prevent multiple component instantiations within a single render
            if not st.session_state.get('_persistent_read_guard'):
                st.session_state['_persistent_read_guard'] = True
            else:
                return False
            # Server-side session via query param or cookie first
            session_id = None
            try:
                params = st.query_params
                if 'session_id' in params:
                    session_id = params['session_id']
            except Exception:
                pass
            if self.cookie_manager is not None:
                try:
                    cookie_val = self.cookie_manager.get(cookie='session_id')
                    if isinstance(cookie_val, dict):
                        session_id = cookie_val.get('session_id') or next(iter(cookie_val.values()), None)
                    else:
                        session_id = cookie_val
                except Exception as cookie_error:
                    print(f"Error reading session_id cookie: {cookie_error}")
            if session_id and not self.is_authenticated():
                try:
                    user = database.get_user_by_session(session_id)
                    if user:
                        self.setup_user_session(user, 'persistent', True)
                        self.session_state['remember_me'] = True
                        return True
                except Exception as e:
                    print(f"Error restoring server session: {e}")

            # Fallback: client-side persistent data in session state
            persistent_data = st.session_state.get('_persistent_login_data')
            
            # If not in session state, check browser cookies (if component available)
            if not persistent_data and self.cookie_manager is not None:
                try:
                    cookie_data = self.cookie_manager.get(cookie='persistent_login')
                    if isinstance(cookie_data, dict):
                        cookie_data = cookie_data.get('persistent_login') or next(iter(cookie_data.values()), None)
                    if cookie_data:
                        # If the cookie value is a JSON string, parse it
                        try:
                            persistent_data = json.loads(cookie_data)
                        except Exception:
                            persistent_data = cookie_data
                        # Store in session state for this session
                        st.session_state['_persistent_login_data'] = persistent_data
                        try:
                            session_id = persistent_data.get('session_id') if isinstance(persistent_data, dict) else None
                        except Exception:
                            session_id = None
                except Exception as cookie_error:
                    print(f"Error reading cookie: {cookie_error}")
                    # Fall back to no persistent cookie
                    pass

            # If still not found, attempt to read from browser localStorage
            if not persistent_data:
                try:
                    local_storage_value = streamlit_js_eval(js_expressions="localStorage.getItem('persistent_login')", key=self._next_sje_key("persistent_get"))
                    if local_storage_value:
                        try:
                            persistent_data = json.loads(local_storage_value)
                        except Exception:
                            persistent_data = None
                        if persistent_data:
                            st.session_state['_persistent_login_data'] = persistent_data
                            try:
                                session_id = persistent_data.get('session_id') if isinstance(persistent_data, dict) else None
                            except Exception:
                                session_id = None
                except Exception as ls_error:
                    print(f"Error reading localStorage: {ls_error}")
            
            if session_id and not self.is_authenticated():
                try:
                    user = database.get_user_by_session(session_id)
                    if user:
                        self.setup_user_session(user, 'persistent', True)
                        self.session_state['remember_me'] = True
                        return True
                except Exception as e:
                    print(f"Error restoring server session: {e}")
            elif persistent_data and not self.is_authenticated():
                try:
                    login_time = datetime.fromisoformat(persistent_data['timestamp'])
                    if (datetime.now() - login_time).days <= 30:
                        user = self.get_user_by_email_simple(persistent_data['email'])
                        if user and user['user_id'] == persistent_data['user_id']:
                            self.setup_user_session(user, 'persistent', True)
                            self.session_state['remember_me'] = True
                            return True
                    else:
                        self._clear_persistent_login()
                except Exception:
                    pass
            
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

            # Clear from browser cookie if CookieManager is available
            if self.cookie_manager is not None:
                try:
                    self.cookie_manager.delete('persistent_login', key=self._next_sje_key("cookie_del"))
                    sid = None
                    try:
                        sid_val = self.cookie_manager.get(cookie='session_id')
                        if isinstance(sid_val, dict):
                            sid = sid_val.get('session_id') or next(iter(sid_val.values()), None)
                        else:
                            sid = sid_val
                    except Exception:
                        sid = st.session_state.get('_persistent_session_id')
                    if sid:
                        try:
                            database.delete_user_session(sid)
                        except Exception:
                            pass
                    self.cookie_manager.delete('session_id', key=self._next_sje_key("cookie_del"))
                except Exception as e:
                    print(f"Error clearing persistent login cookie: {e}")

            # Clear from browser localStorage (including OAuth processed states)
            try:
                clear_all_js = """
                (function() {
                    localStorage.removeItem('persistent_login');
                    // Clear all OAuth processed states
                    const keys = Object.keys(localStorage);
                    keys.forEach(key => {
                        if (key.startsWith('oauth_processed_')) {
                            localStorage.removeItem(key);
                        }
                    });
                })()
                """
                streamlit_js_eval(js_expressions=clear_all_js, key=self._next_sje_key("clear_all_local"))
            except Exception as ls_error:
                print(f"Error clearing localStorage persistent login: {ls_error}")

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

        Role precedence: Case Manager (40) > Lead Coordinator (37) > Admin (34) > Provider (33) > Coordinator (36) > Onboarding (35) > Data Entry (39)

        Special cases:
        - Justin (Admin + Provider): Uses role switcher to choose - defaults to Provider if selected, Admin otherwise
        - Jan (Case Manager primary): CM dashboard with full management tabs
        - Jose (Lead Coordinator primary): LC dashboard with full management tabs

        Returns:
            Primary role ID or None if no recognized role
        """
        user_roles = self.get_user_roles()

        # Check for specific user overrides first
        current_user = self.get_current_user()
        if current_user:
            full_name = (current_user.get('full_name') or '').lower()
            username = (current_user.get('username') or '').lower()

            # Jan should use Case Manager dashboard (keep current setup)
            if 'jan' in full_name or 'jan' in username:
                if 40 in user_roles:  # Case Manager role
                    return 40

            # Jose should use Lead Coordinator dashboard (keep current setup)
            elif 'jose' in full_name or 'jose' in username:
                if 37 in user_roles:  # Lead Coordinator role
                    return 37

        # Users with both Provider (33) and Admin (34) roles should use Admin dashboard
        # The role switcher in Admin dashboard allows switching to Provider view

        # Define general role precedence (higher priority first)
        role_precedence = [40, 37, 34, 33, 36, 35, 39]  # Case Manager, Lead Coordinator, Admin, Provider, Coordinator, Onboarding, Data Entry

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
        """Get all users formatted for dropdown selection (excluding manager roles CPM=38, CM=40)"""
        conn = get_db_connection()
        try:
            users = conn.execute("""
                SELECT DISTINCT u.user_id, u.username, u.email, u.first_name, u.last_name, u.full_name, 
                       u.status, r.role_name, r.role_id
                FROM users u
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN roles r ON ur.role_id = r.role_id
                WHERE u.status = 'active'
                  AND ur.role_id NOT IN (38)  -- Exclude CPM (38) manager role only
                ORDER BY u.full_name
            """).fetchall()
            
            user_list = []
            for user in users:
                user_dict = dict(user)
                # Create display name with role info
                display_name = f"{user_dict['full_name']} ({user_dict['role_name']}) - {user_dict['email']}"
                user_dict['display_name'] = display_name
                user_list.append(user_dict)
            
            return user_list
        except sqlite3.Error as e:
            print(f"Error getting users for dropdown: {e}")
            return []
        finally:
            conn.close()


def get_auth_manager() -> AuthenticationManager:
    """Get a singleton AuthenticationManager for the current session"""
    if '_auth_manager' not in st.session_state or st.session_state['_auth_manager'] is None:
        st.session_state['_auth_manager'] = AuthenticationManager()
    return st.session_state['_auth_manager']


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

    # Handle pending rerun from impersonation stop
    if auth_manager.session_state.get('_pending_rerun'):
        auth_manager.session_state['_pending_rerun'] = False
        st.rerun()

    # Re-check persistence after UI mount if not yet checked
    if not auth_manager.session_state.get('persistent_login_checked', False):
        if auth_manager._check_persistent_login():
            auth_manager.session_state['persistent_login_checked'] = True
            st.rerun()

    # Check for OAuth callback
    query_params = st.query_params
    if 'code' in query_params and 'state' in query_params:
        code = query_params['code']
        state = query_params['state']

        # Check if this state was recently processed using localStorage (persists across refresh)
        check_state_js = f"""
        (function() {{
            const key = 'oauth_processed_' + '{state}';
            const timestamp = localStorage.getItem(key);
            if (!timestamp) return 'new';
            // Check if processed within last 2 minutes (120000 ms)
            const age = Date.now() - parseInt(timestamp);
            return age < 120000 ? 'recent' : 'expired';
        }})()
        """
        state_status = streamlit_js_eval(
            js_expressions=check_state_js,
            key=auth_manager._next_sje_key("oauth_check_state")
        )

        # Handle different scenarios based on authentication state and state status
        if auth_manager.is_authenticated() and state_status == 'recent':
            # User is authenticated + state was recently processed = page refresh after login
            # Just clear the URL silently
            query_params.clear()
            streamlit_js_eval(
                js_expressions="window.history.replaceState({}, '', window.location.pathname);",
                key=auth_manager._next_sje_key("oauth_url_cleanup_refresh")
            )
        elif auth_manager.is_authenticated() and state_status in ['new', None, 'expired']:
            # User is authenticated but this is a new/old state
            # Either re-login attempt or race condition - just clear URL
            query_params.clear()
            streamlit_js_eval(
                js_expressions="window.history.replaceState({}, '', window.location.pathname);",
                key=auth_manager._next_sje_key("oauth_url_cleanup_authenticated")
            )
        elif not auth_manager.is_authenticated() and state_status == 'recent':
            # User is NOT authenticated but state was recently processed
            # This shouldn't happen - might be session loss. Clear state and try processing.
            clear_state_js = f"localStorage.removeItem('oauth_processed_' + '{state}');"
            streamlit_js_eval(js_expressions=clear_state_js, key=auth_manager._next_sje_key("oauth_clear_state"))
            # Fall through to process the OAuth callback
            user = auth_manager.authenticate_with_google_code(code)
        else:
            # User is NOT authenticated + state is new/expired/unknown = normal login flow
            # Mark this state as processed BEFORE processing (in case of refresh during processing)
            mark_processed_js = f"localStorage.setItem('oauth_processed_' + '{state}', Date.now());"
            streamlit_js_eval(
                js_expressions=mark_processed_js,
                key=auth_manager._next_sje_key("oauth_mark_processed")
            )

            user = auth_manager.authenticate_with_google_code(code)

        # Handle the result of OAuth processing (if we attempted it)
        if not auth_manager.is_authenticated():
            if 'user' in locals() and user:
                auth_manager.setup_user_session(user, "google_oauth", True)
                st.session_state['login_email_prefill'] = user.get('email')
                query_params.clear()
                streamlit_js_eval(
                    js_expressions="window.history.replaceState({}, '', window.location.pathname);",
                    key=auth_manager._next_sje_key("oauth_url_cleanup_success")
                )
                st.sidebar.success(f"Welcome, {auth_manager.get_user_full_name()}!")
                st.rerun()
            else:
                st.sidebar.error("Google authentication failed. The authorization code may have expired.")
                query_params.clear()
                clear_state_js = f"localStorage.removeItem('oauth_processed_' + '{state}');"
                streamlit_js_eval(
                    js_expressions=f"window.history.replaceState({{}}, '', window.location.pathname); {clear_state_js}",
                    key=auth_manager._next_sje_key("oauth_url_cleanup_error")
                )

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
            auth_manager.session_state['_pending_rerun'] = True
            st.rerun()

    st.sidebar.markdown("### Login")

    # Check if Google OAuth is configured
    oauth_config = get_oauth_config()
    google_oauth_enabled = oauth_config.google_enabled

    if not auth_manager.is_authenticated():
        # Show Google Sign-In button if configured
        if google_oauth_enabled:
            # Generate Google OAuth URL
            try:
                google_auth_url = get_google_auth_url()

                # Google Sign-In Button
                st.sidebar.markdown("""
                <style>
                div[data-testid="stSidebar"] > div:first-child {
                    background-color: #f8f9fa;
                }
                .google-signin-btn {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background-color: #fff;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    padding: 10px 16px;
                    margin: 8px 0;
                    text-decoration: none;
                    font-family: 'Roboto', sans-serif;
                    font-size: 14px;
                    font-weight: 500;
                    color: #3c4043;
                    width: 100%;
                    box-sizing: border-box;
                    transition: background-color 0.2s, box-shadow 0.2s;
                    cursor: pointer;
                }
                .google-signin-btn:hover {
                    background-color: #f7f8f8;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .google-icon {
                    width: 18px;
                    height: 18px;
                    margin-right: 12px;
                }
                .btn-text {
                    flex-grow: 1;
                    text-align: center;
                }
                </style>
                """, unsafe_allow_html=True)

                st.sidebar.markdown(
                    f'<a href="{google_auth_url}" class="google-signin-btn" target="_self">'
                    '<svg class="google-icon" viewBox="0 0 48 48">'
                    '<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>'
                    '<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>'
                    '<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>'
                    '<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>'
                    '</svg>'
                    '<span class="btn-text">Sign in with Google</span></a>',
                    unsafe_allow_html=True
                )

                st.sidebar.markdown("<div style='text-align: center; color: #666; font-size: 12px; margin: 8px 0;'>— or —</div>", unsafe_allow_html=True)
            except Exception as e:
                st.sidebar.error(f"Google OAuth configuration error: {e}")

        # Email/password login in an expander
        with st.sidebar.expander("Sign in with Email"):
            with st.form("login_form"):
                prefill_email = st.session_state.get('login_email_prefill', '')
                email = st.text_input("Email", value=prefill_email, placeholder="user@example.com")

                # Password is required by default - no checkbox needed
                password = st.text_input("Password", type="password", placeholder="Enter your password")

                # Remember Me checkbox for persistent login
                remember_me = st.checkbox("Remember Me", value=True, help="Stay logged in for 30 days")

                login_button = st.form_submit_button("Login")

                if login_button:
                    if email:
                        # Always use password authentication
                        user = auth_manager.authenticate_user(email, password, "email_password")

                        if user:
                            auth_manager.setup_user_session(user, "email_password", remember_me)
                            st.session_state['login_email_prefill'] = user.get('email')
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
            user = auth_manager.get_current_user()
            display_name = auth_manager.get_user_full_name()
            # Show OAuth indicator if applicable
            if user and user.get('oauth_provider') == 'google':
                display_name = f"{display_name} (Google)"
            st.sidebar.success(f"Logged in as: {display_name}")

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

        st.sidebar.markdown("---")
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