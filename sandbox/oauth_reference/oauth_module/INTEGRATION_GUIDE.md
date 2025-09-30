# Google OAuth Streamlit Integration Guide

This guide will help you integrate Google OAuth authentication into your Streamlit applications using the `google_oauth_streamlit` package.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Google Cloud Setup](#google-cloud-setup)
3. [Package Installation](#package-installation)
4. [Environment Configuration](#environment-configuration)
5. [Basic Integration](#basic-integration)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Security Best Practices](#security-best-practices)

## 🚀 Quick Start

### 1. Copy the Package

Copy the `google_oauth_streamlit` folder to your project directory:

```
your_project/
├── google_oauth_streamlit/
│   ├── __init__.py
│   ├── oauth_module.py
│   └── streamlit_ui.py
├── app.py
├── .env
└── requirements.txt
```

### 2. Install Dependencies

Add these to your `requirements.txt`:

```
streamlit>=1.28.0
requests>=2.31.0
python-dotenv>=1.0.0
```

Install with:
```bash
pip install -r requirements.txt
```

### 3. Basic App Example

Create your `app.py`:

```python
import streamlit as st
from google_oauth_streamlit import setup_oauth_ui

st.set_page_config(page_title="My App", page_icon="🔐")

def main():
    st.title("🔐 My Secure App")
    
    # This handles the entire OAuth flow
    user_info = setup_oauth_ui()
    
    if user_info:
        st.success(f"Welcome, {user_info['name']}!")
        st.write(f"Email: {user_info['email']}")
        # Your app content here
    else:
        st.info("Please log in to access the application.")

if __name__ == "__main__":
    main()
```

## ☁️ Google Cloud Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API (or Google Identity API)

### 2. Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** user type (unless using Google Workspace)
3. Fill in required fields:
   - **App name**: Your application name
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Add scopes:
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `openid`
5. Save and continue

### 3. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth 2.0 Client IDs**
3. Choose **Web application**
4. Add **Authorized redirect URIs**:
   - For local development: `http://localhost:5001/auth/callback`
   - For production: `https://yourdomain.com/auth/callback`
5. Add **Authorized JavaScript origins**:
   - For local development: `http://localhost:5001`
   - For production: `https://yourdomain.com`
6. Save and note your **Client ID** and **Client Secret**

## 📦 Package Installation

### Option 1: Copy Package (Recommended for now)

Simply copy the `google_oauth_streamlit` folder to your project.

### Option 2: Install as Package (Future)

```bash
pip install google-oauth-streamlit
```

## ⚙️ Environment Configuration

### 1. Create .env File

Copy `.env.template` to `.env` and fill in your values:

```env
GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-client-secret"
GOOGLE_REDIRECT_URI="http://localhost:5001/auth/callback"
GOOGLE_SCOPES="https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile,openid"
```

### 2. Load Environment Variables

The package automatically loads environment variables. If you need custom loading:

```python
from dotenv import load_dotenv
load_dotenv()
```

## 🔧 Basic Integration

### Simple Login/Logout

```python
import streamlit as st
from google_oauth_streamlit import setup_oauth_ui

# Basic OAuth UI
user_info = setup_oauth_ui()

if user_info:
    st.write(f"Hello, {user_info['name']}!")
else:
    st.write("Please log in.")
```

### Custom Button Text

```python
user_info = setup_oauth_ui(
    login_button_text="🔐 Sign in with Google",
    logout_button_text="👋 Sign out"
)
```

### Check Authentication Status

```python
from google_oauth_streamlit import is_authenticated, get_user_info

if is_authenticated():
    user = get_user_info()
    st.write(f"Logged in as: {user['email']}")
else:
    st.write("Not logged in")
```

### Require Authentication

```python
from google_oauth_streamlit import require_authentication

# This will show login UI and stop execution if not authenticated
user_info = require_authentication()

# Code here only runs for authenticated users
st.write(f"Welcome, {user_info['name']}!")
```

## 🚀 Advanced Features

### Custom OAuth Configuration

```python
from google_oauth_streamlit import GoogleOAuth, setup_oauth_ui

# Custom OAuth instance
oauth = GoogleOAuth(
    client_id="custom-client-id",
    client_secret="custom-secret",
    redirect_uri="https://myapp.com/auth/callback",
    scopes="openid,email,profile"
)

user_info = setup_oauth_ui(oauth_instance=oauth)
```

### Role-Based Access Control

```python
def check_admin_access(user_info):
    admin_emails = ["admin@company.com"]
    return user_info.get('email') in admin_emails

user_info = setup_oauth_ui()
if user_info:
    if check_admin_access(user_info):
        st.write("Admin panel")
    else:
        st.write("Regular user content")
```

### Domain-Based Access

```python
def check_domain_access(user_info):
    allowed_domains = ["company.com", "partner.com"]
    email = user_info.get('email', '')
    domain = email.split('@')[-1] if '@' in email else ''
    return domain in allowed_domains

user_info = setup_oauth_ui()
if user_info and check_domain_access(user_info):
    st.write("Access granted")
else:
    st.error("Access denied")
```

### Multi-Page Applications

```python
# pages/main.py
import streamlit as st
from google_oauth_streamlit import require_authentication

def show_main_page():
    user_info = require_authentication()
    st.write(f"Main page for {user_info['name']}")

# pages/admin.py
def show_admin_page():
    user_info = require_authentication()
    if not is_admin(user_info):
        st.error("Admin access required")
        return
    st.write("Admin panel")
```

## 🐛 Troubleshooting

### Common Issues

#### 1. `redirect_uri_mismatch` Error

**Problem**: OAuth redirect URI doesn't match Google Cloud Console configuration.

**Solution**:
- Check your `.env` file `GOOGLE_REDIRECT_URI`
- Verify Google Cloud Console **Authorized redirect URIs**
- Ensure exact match including protocol (http/https) and port

#### 2. `invalid_scope` Error

**Problem**: OAuth scopes are not properly configured.

**Solution**:
- Use full scope URLs in `.env`:
  ```
  GOOGLE_SCOPES="https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile,openid"
  ```
- Configure scopes in Google Cloud Console OAuth consent screen

#### 3. `Access blocked` Error

**Problem**: OAuth consent screen not properly configured.

**Solution**:
- Complete OAuth consent screen setup in Google Cloud Console
- Add required scopes
- Publish the app (for external users)

#### 4. Environment Variables Not Loading

**Problem**: `.env` file not being read.

**Solution**:
```python
from dotenv import load_dotenv
load_dotenv()  # Add this before importing the OAuth module
```

### Debug Mode

Enable debug information:

```python
import streamlit as st

# Show session state for debugging
if st.checkbox("Debug Mode"):
    st.write("Session State:", st.session_state)
    st.write("Query Params:", st.query_params)
```

## 🔒 Security Best Practices

### 1. Environment Variables

- Never commit `.env` files to version control
- Use different credentials for development/production
- Rotate secrets regularly

### 2. HTTPS in Production

- Always use HTTPS in production
- Update redirect URIs to use `https://`
- Configure proper SSL certificates

### 3. Domain Restrictions

```python
# Restrict access by email domain
ALLOWED_DOMAINS = ["yourcompany.com"]

def validate_user_domain(user_info):
    email = user_info.get('email', '')
    domain = email.split('@')[-1] if '@' in email else ''
    return domain in ALLOWED_DOMAINS
```

### 4. Session Security

```python
# Set session timeout
import datetime

def check_session_timeout():
    login_time = st.session_state.get('login_time')
    if login_time:
        elapsed = datetime.datetime.now() - login_time
        if elapsed > datetime.timedelta(hours=8):  # 8 hour timeout
            st.session_state.clear()
            st.rerun()
```

### 5. Token Management

```python
# Revoke tokens on logout
from google_oauth_streamlit import GoogleOAuth

def secure_logout():
    oauth = GoogleOAuth()
    if 'access_token' in st.session_state:
        oauth.revoke_token(st.session_state.access_token)
    st.session_state.clear()
```

## 📝 Example Project Structure

```
my_streamlit_app/
├── google_oauth_streamlit/          # OAuth package
│   ├── __init__.py
│   ├── oauth_module.py
│   └── streamlit_ui.py
├── pages/                           # Streamlit pages
│   ├── 01_dashboard.py
│   ├── 02_profile.py
│   └── 03_admin.py
├── utils/                           # Utility functions
│   ├── __init__.py
│   ├── auth_helpers.py
│   └── data_helpers.py
├── static/                          # Static files
│   ├── css/
│   └── images/
├── .env                            # Environment variables (not in git)
├── .env.template                   # Template for .env
├── .gitignore                      # Git ignore file
├── app.py                          # Main application
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

## 🎯 Next Steps

1. **Test the Integration**: Start with the simple example
2. **Customize UI**: Modify button text and styling
3. **Add Access Control**: Implement role-based or domain-based restrictions
4. **Enhance Security**: Add session timeouts and token management
5. **Deploy**: Configure for production with HTTPS

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Verify your Google Cloud Console configuration
3. Review the example applications in the `examples/` folder
4. Check Streamlit logs for detailed error messages

---

**Happy coding! 🚀**