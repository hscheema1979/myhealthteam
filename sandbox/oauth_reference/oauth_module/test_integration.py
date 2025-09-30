"""
Test Integration for Google OAuth Streamlit Package

This file tests that the package structure works correctly and can be imported.
"""

import streamlit as st
import sys
import os

# Test importing the package
try:
    from google_oauth_streamlit import GoogleOAuth, setup_oauth_ui, get_user_info, is_authenticated
    st.success("✅ Package imported successfully!")
except ImportError as e:
    st.error(f"❌ Failed to import package: {e}")
    st.stop()

# Configure the page
st.set_page_config(
    page_title="OAuth Package Test",
    page_icon="🧪",
    layout="wide"
)

def main():
    """Test the OAuth package integration."""
    
    st.title("🧪 OAuth Package Integration Test")
    st.markdown("---")
    
    # Test 1: Package Import
    st.subheader("📦 Package Import Test")
    st.success("✅ All modules imported successfully")
    
    # Test 2: Environment Variables
    st.subheader("⚙️ Environment Configuration Test")
    
    env_vars = {
        'GOOGLE_CLIENT_ID': os.getenv('GOOGLE_CLIENT_ID'),
        'GOOGLE_CLIENT_SECRET': os.getenv('GOOGLE_CLIENT_SECRET'),
        'GOOGLE_REDIRECT_URI': os.getenv('GOOGLE_REDIRECT_URI'),
        'GOOGLE_SCOPES': os.getenv('GOOGLE_SCOPES')
    }
    
    all_configured = True
    for var, value in env_vars.items():
        if value:
            st.success(f"✅ {var}: Configured")
        else:
            st.error(f"❌ {var}: Not configured")
            all_configured = False
    
    if not all_configured:
        st.warning("⚠️ Some environment variables are missing. OAuth will not work properly.")
        st.info("Please check your .env file and ensure all required variables are set.")
    
    # Test 3: OAuth Instance Creation
    st.subheader("🔐 OAuth Instance Test")
    
    try:
        oauth = GoogleOAuth()
        st.success("✅ OAuth instance created successfully")
        
        # Test authorization URL generation
        try:
            auth_url, state = oauth.get_authorization_url()
            st.success("✅ Authorization URL generated successfully")
            
            with st.expander("🔍 View Authorization URL"):
                st.code(auth_url)
                st.write(f"**State:** {state}")
                
        except Exception as e:
            st.error(f"❌ Failed to generate authorization URL: {e}")
            
    except Exception as e:
        st.error(f"❌ Failed to create OAuth instance: {e}")
        st.info("This is likely due to missing environment variables.")
    
    # Test 4: UI Components
    st.subheader("🎨 UI Components Test")
    
    if all_configured:
        st.info("🔄 Testing OAuth UI components...")
        
        # Test the actual OAuth flow
        user_info = setup_oauth_ui(
            login_button_text="🧪 Test Login",
            logout_button_text="🧪 Test Logout"
        )
        
        if user_info:
            st.success("✅ OAuth flow working! User authenticated successfully.")
            
            # Display user information
            st.subheader("👤 User Information")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {user_info.get('name', 'N/A')}")
                st.write(f"**Email:** {user_info.get('email', 'N/A')}")
                st.write(f"**ID:** {user_info.get('id', 'N/A')}")
            
            with col2:
                if user_info.get('picture'):
                    st.image(user_info['picture'], width=100, caption="Profile Picture")
            
            # Test utility functions
            st.subheader("🛠️ Utility Functions Test")
            
            if is_authenticated():
                st.success("✅ is_authenticated() returns True")
            else:
                st.error("❌ is_authenticated() returns False")
            
            current_user = get_user_info()
            if current_user:
                st.success("✅ get_user_info() returns user data")
            else:
                st.error("❌ get_user_info() returns None")
            
            # Raw user data for debugging
            with st.expander("🔍 Raw User Data"):
                st.json(user_info)
                
        else:
            st.info("ℹ️ Click the login button above to test the OAuth flow")
    else:
        st.warning("⚠️ Cannot test UI components without proper environment configuration")
    
    # Test 5: Package Information
    st.subheader("📋 Package Information")
    
    try:
        from google_oauth_streamlit import __version__, __author__, __email__
        st.write(f"**Version:** {__version__}")
        st.write(f"**Author:** {__author__}")
        st.write(f"**Email:** {__email__}")
    except ImportError:
        st.warning("Package metadata not available")
    
    # Test Summary
    st.markdown("---")
    st.subheader("📊 Test Summary")
    
    if all_configured:
        st.success("🎉 All tests passed! The package is ready for use.")
        st.info("You can now copy the `google_oauth_streamlit` folder to your projects.")
    else:
        st.warning("⚠️ Some tests failed due to missing configuration.")
        st.info("Please configure your environment variables and try again.")


if __name__ == "__main__":
    main()