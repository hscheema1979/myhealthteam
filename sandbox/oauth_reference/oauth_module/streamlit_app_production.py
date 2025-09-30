"""
Production Streamlit App with Google OAuth Integration
This version uses Google Secret Manager for secure credential management
"""

import streamlit as st
import os
from urllib.parse import urlparse, parse_qs
from oauth_module import GoogleOAuth
from dotenv import load_dotenv

# Try to import Google Secret Manager (for production)
try:
    from google.cloud import secretmanager
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    st.warning("Google Cloud Secret Manager not available. Using environment variables.")

# Load environment variables for local development
load_dotenv()

def get_secret(secret_name, project_id="PCOPs"):
    """
    Retrieve a secret from Google Secret Manager
    Falls back to environment variables if Secret Manager is not available
    """
    if GOOGLE_CLOUD_AVAILABLE:
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            st.error(f"Error accessing secret {secret_name}: {e}")
            # Fall back to environment variable
            return os.environ.get(secret_name.upper().replace('-', '_'))
    else:
        # Use environment variables for local development
        return os.environ.get(secret_name.upper().replace('-', '_'))

def get_oauth_config():
    """Get OAuth configuration from secrets or environment variables"""
    
    # Determine if we're running in production
    is_production = os.environ.get('GAE_ENV', '').startswith('standard') or \
                   os.environ.get('K_SERVICE') is not None  # Cloud Run
    
    if is_production:
        # Production: use the deployed URL
        base_url = f"https://{os.environ.get('GAE_SERVICE', 'oauth-streamlit')}-dot-{os.environ.get('GOOGLE_CLOUD_PROJECT', 'PCOPs')}.uc.r.appspot.com"
        if os.environ.get('K_SERVICE'):  # Cloud Run
            base_url = f"https://{os.environ.get('K_SERVICE')}-{os.environ.get('K_REVISION', 'latest')}-{os.environ.get('K_CONFIGURATION', 'default')}.a.run.app"
        redirect_uri = f"{base_url}/auth/callback"
    else:
        # Development: use localhost
        redirect_uri = "http://localhost:5001/auth/callback"
    
    config = {
        'client_id': get_secret('google-client-id'),
        'client_secret': get_secret('google-client-secret'),
        'redirect_uri': redirect_uri,
        'scopes': os.environ.get('GOOGLE_SCOPES', 'openid email profile').split(',')
    }
    
    return config

# --- Configuration ---
try:
    oauth_config = get_oauth_config()
    
    if not all([oauth_config['client_id'], oauth_config['client_secret']]):
        st.error("Missing Google OAuth credentials. Please configure secrets in Google Cloud Secret Manager.")
        st.stop()
    
    oauth_client = GoogleOAuth(
        oauth_config['client_id'],
        oauth_config['client_secret'],
        oauth_config['redirect_uri'],
        oauth_config['scopes']
    )
    
except Exception as e:
    st.error(f"Error initializing OAuth client: {e}")
    st.stop()

# --- Streamlit App ---
def login_button():
    """Display login button"""
    auth_url = oauth_client.get_authorization_url()
    st.link_button("🔐 Login with Google", url=auth_url, use_container_width=True)

def handle_callback():
    """Handle OAuth callback"""
    query_params = st.query_params
    code = query_params.get("code")

    if code:
        try:
            tokens = oauth_client.exchange_code_for_tokens(code)
            st.session_state["access_token"] = tokens["access_token"]
            st.session_state["user_info"] = oauth_client.get_user_info(tokens["access_token"])
            st.success("✅ Successfully logged in!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error during OAuth flow: {e}")
    elif "error" in query_params:
        st.error(f"❌ OAuth Error: {query_params.get('error_description', query_params['error'])}")

def logout_button():
    """Display logout button and handle logout"""
    if st.button("🚪 Logout", use_container_width=True):
        if "access_token" in st.session_state:
            del st.session_state["access_token"]
        if "user_info" in st.session_state:
            del st.session_state["user_info"]
        st.success("✅ Logged out successfully!")
        st.rerun()

def main():
    """Main application"""
    st.set_page_config(
        page_title="OAuth Streamlit App",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔐 Secure Streamlit App with Google OAuth")
    
    # Display environment info
    with st.expander("🔧 Environment Information"):
        is_production = os.environ.get('GAE_ENV', '').startswith('standard') or \
                       os.environ.get('K_SERVICE') is not None
        st.write(f"**Environment:** {'Production' if is_production else 'Development'}")
        st.write(f"**Redirect URI:** {oauth_config['redirect_uri']}")
        st.write(f"**Secret Manager Available:** {GOOGLE_CLOUD_AVAILABLE}")
    
    if "user_info" not in st.session_state:
        st.info("👋 Welcome! Please log in to access the application.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            login_button()
        
        handle_callback()
    else:
        user_info = st.session_state["user_info"]
        
        # User info sidebar
        with st.sidebar:
            st.header("👤 User Profile")
            if user_info.get("picture"):
                st.image(user_info["picture"], width=100)
            st.write(f"**Name:** {user_info.get('name', 'Unknown')}")
            st.write(f"**Email:** {user_info.get('email', 'Unknown')}")
            st.write(f"**ID:** {user_info.get('sub', 'Unknown')}")
            
            st.divider()
            logout_button()
        
        # Main content
        st.success(f"🎉 Welcome back, {user_info.get('name', 'User')}!")
        
        # Sample application content
        st.header("📊 Application Dashboard")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Users", "1,234", "12%")
        
        with col2:
            st.metric("Active Sessions", "89", "5%")
        
        with col3:
            st.metric("Success Rate", "98.5%", "0.2%")
        
        # Sample chart
        import pandas as pd
        import numpy as np
        
        chart_data = pd.DataFrame(
            np.random.randn(20, 3),
            columns=['A', 'B', 'C']
        )
        
        st.subheader("📈 Sample Data Visualization")
        st.line_chart(chart_data)
        
        # User data display
        st.subheader("🔍 Your Profile Data")
        st.json(user_info)

if __name__ == "__main__":
    main()