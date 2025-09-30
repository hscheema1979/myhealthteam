"""
Streamlit UI Components for Google OAuth

This module provides ready-to-use Streamlit UI components for Google OAuth integration.
"""

import streamlit as st
from urllib.parse import parse_qs, urlparse
from .oauth_module import GoogleOAuth


def setup_oauth_ui(oauth_instance=None, login_button_text="Login with Google", logout_button_text="Logout"):
    """
    Setup OAuth UI components in Streamlit.
    
    This function handles the complete OAuth flow including:
    - Login button
    - Callback handling
    - User session management
    - Logout functionality
    
    Args:
        oauth_instance (GoogleOAuth, optional): OAuth instance. If None, creates a new one.
        login_button_text (str): Text for the login button
        logout_button_text (str): Text for the logout button
        
    Returns:
        dict: User information if logged in, None otherwise
    """
    if oauth_instance is None:
        oauth_instance = GoogleOAuth()
    
    # Initialize session state
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'oauth_state' not in st.session_state:
        st.session_state.oauth_state = None
    
    # Handle OAuth callback
    user_info = handle_oauth_callback(oauth_instance)
    if user_info:
        st.session_state.user_info = user_info
    
    # Display UI based on authentication status
    if st.session_state.user_info:
        # User is logged in
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.success(f"Welcome, {st.session_state.user_info.get('name', 'User')}!")
            st.write(f"Email: {st.session_state.user_info.get('email', 'N/A')}")
        
        with col2:
            if st.button(logout_button_text):
                logout(oauth_instance)
        
        return st.session_state.user_info
    else:
        # User is not logged in
        if st.button(login_button_text):
            initiate_login(oauth_instance)
        
        return None


def handle_oauth_callback(oauth_instance):
    """
    Handle OAuth callback from Google.
    
    Args:
        oauth_instance (GoogleOAuth): OAuth instance
        
    Returns:
        dict: User information if callback is successful, None otherwise
    """
    # Check for OAuth callback parameters
    query_params = st.query_params
    
    if 'code' in query_params:
        code = query_params['code']
        state = query_params.get('state')
        
        # Verify state for CSRF protection
        if state and st.session_state.oauth_state and state == st.session_state.oauth_state:
            try:
                # Exchange code for token
                token_response = oauth_instance.exchange_code_for_token(code, state)
                access_token = token_response.get('access_token')
                
                if access_token:
                    # Get user information
                    user_info = oauth_instance.get_user_info(access_token)
                    
                    # Store token in session for potential future use
                    st.session_state.access_token = access_token
                    st.session_state.refresh_token = token_response.get('refresh_token')
                    
                    # Clear OAuth state
                    st.session_state.oauth_state = None
                    
                    # Clear query parameters
                    st.query_params.clear()
                    
                    return user_info
                    
            except Exception as e:
                st.error(f"Authentication failed: {str(e)}")
                st.session_state.oauth_state = None
        else:
            st.error("Invalid authentication state. Please try again.")
            st.session_state.oauth_state = None
    
    return None


def initiate_login(oauth_instance):
    """
    Initiate the OAuth login process.
    
    Args:
        oauth_instance (GoogleOAuth): OAuth instance
    """
    try:
        auth_url, state = oauth_instance.get_authorization_url()
        st.session_state.oauth_state = state
        
        # Redirect to Google OAuth
        st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
        st.info("Redirecting to Google for authentication...")
        
    except Exception as e:
        st.error(f"Failed to initiate login: {str(e)}")


def logout(oauth_instance=None):
    """
    Logout the current user.
    
    Args:
        oauth_instance (GoogleOAuth, optional): OAuth instance for token revocation
    """
    # Revoke token if available
    if oauth_instance and 'access_token' in st.session_state:
        try:
            oauth_instance.revoke_token(st.session_state.access_token)
        except Exception:
            pass  # Continue with logout even if revocation fails
    
    # Clear session state
    for key in ['user_info', 'access_token', 'refresh_token', 'oauth_state']:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear query parameters
    st.query_params.clear()
    
    # Rerun to update UI
    st.rerun()


def get_user_info():
    """
    Get the current user's information from session state.
    
    Returns:
        dict: User information if logged in, None otherwise
    """
    return st.session_state.get('user_info')


def is_authenticated():
    """
    Check if user is currently authenticated.
    
    Returns:
        bool: True if user is authenticated, False otherwise
    """
    return st.session_state.get('user_info') is not None


def require_authentication(oauth_instance=None):
    """
    Decorator/function to require authentication for a Streamlit page.
    
    Args:
        oauth_instance (GoogleOAuth, optional): OAuth instance
        
    Returns:
        dict: User information if authenticated, None if not (and shows login UI)
    """
    user_info = setup_oauth_ui(oauth_instance)
    
    if not user_info:
        st.warning("Please log in to access this page.")
        st.stop()
    
    return user_info