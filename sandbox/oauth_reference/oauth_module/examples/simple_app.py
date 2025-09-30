"""
Simple Streamlit App with Google OAuth Integration

This is a basic example of how to integrate Google OAuth into your Streamlit application
using the google_oauth_streamlit package.

To use this template:
1. Copy the google_oauth_streamlit folder to your project
2. Copy this file as your app.py
3. Set up your .env file with Google OAuth credentials
4. Run: streamlit run app.py
"""

import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the package
# In your actual project, you would install the package or copy it to your project directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from the parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

from google_oauth_streamlit import setup_oauth_ui, require_authentication, get_user_info, is_authenticated

# Configure the Streamlit page
st.set_page_config(
    page_title="My App with Google OAuth",
    page_icon="🔐",
    layout="wide"
)

def main():
    """Main application function."""
    
    st.title("🔐 My Secure Application")
    st.markdown("---")
    
    # Setup OAuth UI - this handles login/logout automatically
    user_info = setup_oauth_ui()
    
    if user_info:
        # User is authenticated - show your main application
        show_authenticated_content(user_info)
    else:
        # User is not authenticated - show public content or login prompt
        show_public_content()


def show_authenticated_content(user_info):
    """Content to show when user is authenticated."""
    
    st.header("Welcome to the Secure Area!")
    
    # Display user information
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Your Profile")
        st.write(f"**Name:** {user_info.get('name', 'N/A')}")
        st.write(f"**Email:** {user_info.get('email', 'N/A')}")
        st.write(f"**User ID:** {user_info.get('id', 'N/A')}")
    
    with col2:
        if user_info.get('picture'):
            st.subheader("Profile Picture")
            st.image(user_info['picture'], width=100)
    
    st.markdown("---")
    
    # Your main application content goes here
    st.subheader("🚀 Your Application Features")
    
    # Example features
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Settings", "Data"])
    
    with tab1:
        st.write("This is your dashboard content.")
        st.info("Add your dashboard widgets, charts, and data here.")
        
        # Example: Simple counter
        if 'counter' not in st.session_state:
            st.session_state.counter = 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("➕ Increment"):
                st.session_state.counter += 1
        with col2:
            if st.button("➖ Decrement"):
                st.session_state.counter -= 1
        with col3:
            if st.button("🔄 Reset"):
                st.session_state.counter = 0
        
        st.metric("Counter", st.session_state.counter)
    
    with tab2:
        st.write("User settings and preferences.")
        st.info("Add user-specific settings and configuration options here.")
        
        # Example settings
        theme = st.selectbox("Choose Theme", ["Light", "Dark", "Auto"])
        notifications = st.checkbox("Enable Notifications", value=True)
        language = st.selectbox("Language", ["English", "Spanish", "French"])
        
        if st.button("Save Settings"):
            st.success("Settings saved successfully!")
    
    with tab3:
        st.write("User data and analytics.")
        st.info("Display user-specific data, reports, and analytics here.")
        
        # Example data display
        import pandas as pd
        import numpy as np
        
        # Generate sample data
        data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=30),
            'Value': np.random.randn(30).cumsum()
        })
        
        st.line_chart(data.set_index('Date'))


def show_public_content():
    """Content to show when user is not authenticated."""
    
    st.header("Welcome to My Application")
    
    st.markdown("""
    This is a secure application that requires Google authentication.
    
    **Features:**
    - 🔐 Secure Google OAuth login
    - 👤 User profile management
    - 📊 Personalized dashboard
    - ⚙️ Custom settings
    - 📈 Data analytics
    
    Please click the "Login with Google" button above to access the full application.
    """)
    
    # You can add public content here that doesn't require authentication
    st.info("💡 This content is visible to everyone, even without logging in.")


# Alternative: Require authentication for the entire app
def protected_app():
    """
    Alternative main function that requires authentication for the entire app.
    Use this if you want to force login before showing any content.
    """
    
    st.title("🔐 Protected Application")
    
    # This will show login UI and stop execution if user is not authenticated
    user_info = require_authentication()
    
    # If we reach here, user is authenticated
    st.success(f"Welcome back, {user_info['name']}!")
    
    # Your protected application content here
    st.write("This entire application is protected and requires authentication.")


if __name__ == "__main__":
    # Choose which version to run:
    
    # Option 1: Mixed public/private content (recommended)
    main()
    
    # Option 2: Fully protected app (uncomment to use)
    # protected_app()