"""
Google OAuth Streamlit Integration Package

A simple, reusable package for integrating Google OAuth authentication 
into Streamlit applications.

Usage:
    from google_oauth_streamlit import GoogleOAuth, setup_oauth_ui
    
    # Initialize OAuth
    oauth = GoogleOAuth()
    
    # Setup UI components
    setup_oauth_ui(oauth)
"""

from .oauth_module import GoogleOAuth, create_oauth_instance
from .streamlit_ui import (
    setup_oauth_ui, 
    handle_oauth_callback, 
    initiate_login, 
    logout, 
    get_user_info, 
    is_authenticated, 
    require_authentication
)

__version__ = "1.0.0"
__author__ = "Harpreet Singh"
__email__ = "harpreet@myhealthteam.org"

__all__ = [
    "GoogleOAuth", 
    "create_oauth_instance",
    "setup_oauth_ui", 
    "handle_oauth_callback", 
    "initiate_login", 
    "logout", 
    "get_user_info", 
    "is_authenticated", 
    "require_authentication"
]