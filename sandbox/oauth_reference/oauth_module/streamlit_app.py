import streamlit as st
import os
from urllib.parse import urlparse, parse_qs
from oauth_module import GoogleOAuth
from dotenv import load_dotenv

load_dotenv()

# --- Configuration from Environment Variables ---
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")
SCOPES_STR = os.environ.get("GOOGLE_SCOPES", "openid email profile")
SCOPES = SCOPES_STR.split(",")

if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
    st.error("Missing Google OAuth environment variables. Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, and GOOGLE_SCOPES.")
    st.stop()

oauth_client = GoogleOAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES)

# --- Streamlit App ---
def login_button():
    auth_url = oauth_client.get_authorization_url()
    st.link_button("Login with Google", url=auth_url)

def handle_callback():
    query_params = st.query_params
    code = query_params.get("code")

    if code:
        try:
            tokens = oauth_client.exchange_code_for_tokens(code)
            st.session_state["access_token"] = tokens["access_token"]
            st.session_state["user_info"] = oauth_client.get_user_info(tokens["access_token"])
            st.success("Successfully logged in!")
            st.rerun()
        except Exception as e:
            st.error(f"Error during OAuth flow: {e}")
    elif "error" in query_params:
        st.error(f"OAuth Error: {query_params.get('error_description', query_params['error'])}")

def logout_button():
    if "access_token" in st.session_state:
        del st.session_state["access_token"]
    if "user_info" in st.session_state:
        del st.session_state["user_info"]
    st.success("Logged out.")
    st.rerun()

st.title("Streamlit Google OAuth Example")

if "user_info" not in st.session_state:
    st.write("Please log in to continue.")
    login_button()
    handle_callback()
else:
    user_info = st.session_state["user_info"]
    st.write(f"Welcome, {user_info.get('name', 'User')}!")
    st.write(f"Email: {user_info.get('email')}")
    st.image(user_info.get("picture"), width=100)
    logout_button()