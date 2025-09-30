# 🔐 Google OAuth Streamlit Integration

A simple, reusable package for integrating Google OAuth authentication into Streamlit applications.

## ✨ Features

- 🚀 **Easy Integration** - Just a few lines of code to add OAuth
- 🔒 **Secure** - Implements OAuth 2.0 best practices
- 🎨 **Customizable** - Custom button text and styling options
- 👥 **Role-Based Access** - Support for admin/user roles
- 🏢 **Domain Restrictions** - Control access by email domain
- 📱 **Responsive** - Works on desktop and mobile
- 🛡️ **CSRF Protection** - Built-in security features
- 📊 **Session Management** - Proper session handling

## 🚀 Quick Start

### 1. Copy the Package

Copy the `google_oauth_streamlit` folder to your project:

```
your_project/
├── google_oauth_streamlit/
├── app.py
├── .env
└── requirements.txt
```

### 2. Install Dependencies

```bash
pip install streamlit requests python-dotenv
```

### 3. Configure Environment

Create a `.env` file:

```env
GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-client-secret"
GOOGLE_REDIRECT_URI="http://localhost:5001/auth/callback"
GOOGLE_SCOPES="https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile,openid"
```

### 4. Create Your App

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
        # Your app content here
    else:
        st.info("Please log in to access the application.")

if __name__ == "__main__":
    main()
```

### 5. Run Your App

```bash
streamlit run app.py --server.port 5001
```

## 📚 Documentation

- **[Integration Guide](INTEGRATION_GUIDE.md)** - Complete setup and usage guide
- **[Examples](examples/)** - Sample applications
  - `simple_app.py` - Basic integration example
  - `advanced_app.py` - Advanced features and patterns

## 🔧 API Reference

### Core Functions

#### `setup_oauth_ui(oauth_instance=None, login_button_text="Login with Google", logout_button_text="Logout")`

Sets up the complete OAuth UI with login/logout functionality.

**Parameters:**
- `oauth_instance` (GoogleOAuth, optional): Custom OAuth instance
- `login_button_text` (str): Text for the login button
- `logout_button_text` (str): Text for the logout button

**Returns:**
- `dict`: User information if logged in, `None` otherwise

#### `require_authentication(oauth_instance=None)`

Requires authentication to access a page. Shows login UI if not authenticated.

**Returns:**
- `dict`: User information (only if authenticated)

#### `is_authenticated()`

Check if user is currently authenticated.

**Returns:**
- `bool`: `True` if authenticated, `False` otherwise

#### `get_user_info()`

Get current user's information from session.

**Returns:**
- `dict`: User information if logged in, `None` otherwise

### GoogleOAuth Class

#### `GoogleOAuth(client_id=None, client_secret=None, redirect_uri=None, scopes=None)`

Main OAuth handler class.

**Methods:**
- `get_authorization_url()` - Generate authorization URL
- `exchange_code_for_token(code, state)` - Exchange code for token
- `get_user_info(access_token)` - Get user information
- `revoke_token(token)` - Revoke access token

## 🎯 Usage Examples

### Basic Authentication

```python
from google_oauth_streamlit import setup_oauth_ui

user_info = setup_oauth_ui()
if user_info:
    st.write(f"Hello, {user_info['name']}!")
```

### Custom Button Text

```python
user_info = setup_oauth_ui(
    login_button_text="🔐 Sign in with Google",
    logout_button_text="👋 Sign out"
)
```

### Require Authentication

```python
from google_oauth_streamlit import require_authentication

# This will show login UI if not authenticated
user_info = require_authentication()
st.write(f"Welcome, {user_info['name']}!")
```

### Role-Based Access

```python
def is_admin(user_info):
    admin_emails = ["admin@company.com"]
    return user_info.get('email') in admin_emails

user_info = setup_oauth_ui()
if user_info:
    if is_admin(user_info):
        st.write("Admin Panel")
    else:
        st.write("User Dashboard")
```

### Domain Restrictions

```python
def check_domain(user_info):
    allowed_domains = ["company.com"]
    email = user_info.get('email', '')
    domain = email.split('@')[-1] if '@' in email else ''
    return domain in allowed_domains

user_info = setup_oauth_ui()
if user_info and check_domain(user_info):
    st.write("Access granted")
else:
    st.error("Access denied")
```

## 🔒 Security Features

- **CSRF Protection** - State parameter validation
- **Token Management** - Secure token storage and revocation
- **Session Security** - Proper session handling
- **Domain Validation** - Email domain restrictions
- **HTTPS Support** - Production-ready security

## 🛠️ Development

### Project Structure

```
oauth_module/
├── google_oauth_streamlit/          # Main package
│   ├── __init__.py                  # Package initialization
│   ├── oauth_module.py              # Core OAuth functionality
│   └── streamlit_ui.py              # UI components
├── examples/                        # Example applications
│   ├── simple_app.py               # Basic example
│   └── advanced_app.py             # Advanced example
├── .env.template                   # Environment template
├── INTEGRATION_GUIDE.md            # Detailed guide
├── README.md                       # This file
├── requirements.txt                # Dependencies
├── setup.py                        # Package setup
└── pyproject.toml                  # Modern package config
```

### Testing

Run the test integration:

```bash
streamlit run test_integration.py --server.port 5002
```

### Building the Package

```bash
# Install build tools
pip install build

# Build the package
python -m build

# Install locally
pip install -e .
```

## 📋 Requirements

- Python 3.8+
- Streamlit 1.28.0+
- Requests 2.31.0+
- python-dotenv 1.0.0+

## 🔧 Google Cloud Setup

1. **Create OAuth 2.0 Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to APIs & Services > Credentials
   - Create OAuth 2.0 Client ID

2. **Configure OAuth Consent Screen**
   - Set up app information
   - Add required scopes
   - Add test users (for development)

3. **Set Authorized URIs**
   - Redirect URIs: `http://localhost:5001/auth/callback`
   - JavaScript origins: `http://localhost:5001`

See the [Integration Guide](INTEGRATION_GUIDE.md) for detailed setup instructions.

## 🐛 Troubleshooting

### Common Issues

- **`redirect_uri_mismatch`** - Check Google Cloud Console redirect URIs
- **`invalid_scope`** - Use full scope URLs in environment variables
- **`Access blocked`** - Complete OAuth consent screen setup

See the [Integration Guide](INTEGRATION_GUIDE.md) for detailed troubleshooting.

## 📄 License

MIT License - see LICENSE file for details.

## 👨‍💻 Author

**Harpreet Singh**
- Email: harpreet@myhealthteam.org
- Organization: MyHealthTeam

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

- 📖 [Integration Guide](INTEGRATION_GUIDE.md)
- 💡 [Examples](examples/)
- 🐛 [Issues](https://github.com/yourusername/google-oauth-streamlit/issues)

---

**Happy coding! 🚀**

This module provides a streamlined way to integrate Google OAuth into Streamlit and other Python applications, specifically for `myhealthteam.org`.

## Features

- Handles Google OAuth 2.0 authorization flow.
- Exchanges authorization codes for access and ID tokens.
- Extracts user profile information from ID tokens.

## Setup

### Google Cloud Project Configuration

Before using this module, you need to configure your Google Cloud Project to obtain the necessary OAuth credentials:

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Select your project or create a new one.
3.  Navigate to "APIs & Services" > "Credentials".
4.  Create an "OAuth client ID" of type "Web application".
5.  Configure the following:
    *   **Authorized JavaScript origins:** (e.g., `http://localhost:5001`, `https://patients-app-746ljoo2pa-uc.a.run.app`)
    *   **Authorized redirect URIs:** (e.g., `http://localhost:5001/auth/callback`, `https://patients-app-223722902991.us-central1.run.app/auth/callback`)
6.  Note down your **Client ID** and **Client Secret**.
7.  Ensure the following **scopes** are enabled for your OAuth consent screen:
    *   `openid`
    *   `email`
    *   `profile`

### Module Configuration

This module requires the following environment variables to be set. You can set these in your shell or in a `.env` file that you load at the start of your application.

*   `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID.
*   `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret.
*   `GOOGLE_REDIRECT_URI`: The primary authorized redirect URI your application will use (e.g., `http://localhost:5001/auth/callback`).
*   `GOOGLE_SCOPES`: Comma-separated string of scopes (e.g., `openid,email,profile`).

### Installation

First, install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

### 1. Command-Line Example

You can test the basic OAuth flow from the command line. Make sure your environment variables are set as described above.

```bash
python oauth_module.py
```

Follow the instructions in the console to authorize the application and paste the authorization code back.

### 2. Streamlit Application Example

To run the sample Streamlit application, ensure your environment variables are set and then execute:

```bash
streamlit run streamlit_app.py --server.port 5000
```

Open your browser to the address provided by Streamlit (e.g., `http://localhost:5000`). Click the "Login with Google" button to initiate the OAuth flow.

### 3. Integrating with Other Python Applications

You can integrate the `oauth_module` into any Python application by importing the `GoogleOAuth` class and using its methods. Here's a general example:

```python
import os
from oauth_module import GoogleOAuth

# Load credentials from environment variables
client_id = os.environ.get("GOOGLE_CLIENT_ID")
client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
scopes = os.environ.get("GOOGLE_SCOPES", "openid email profile").split(" ")

if not all([client_id, client_secret, redirect_uri]):
    raise ValueError("Missing Google OAuth environment variables.")

oauth_client = GoogleOAuth(client_id, client_secret, redirect_uri, scopes)

def authenticate_user():
    # Step 1: Get the authorization URL and redirect the user
    auth_url = oauth_client.get_authorization_url()
    print(f"Please go to this URL to authorize: {auth_url}")

    # In a web application, you would redirect the user's browser to auth_url.
    # After authorization, Google redirects back to your redirect_uri with a 'code'.

    # Step 2: Handle the callback and exchange the code for tokens
    # This part depends on your application's framework (e.g., Flask, Django, FastAPI)
    # For demonstration, let's assume you get the code from a request parameter.
    authorization_code = input("Enter the authorization code from the redirect URL: ")

    if authorization_code:
        try:
            tokens = oauth_client.exchange_code_for_tokens(authorization_code)
            access_token = tokens["access_token"]
            user_info = oauth_client.get_user_info(access_token)
            print("Authentication successful!")
            print("User Info:", user_info)
            return user_info
        except Exception as e:
            print(f"Authentication failed: {e}")
            return None
    else:
        print("No authorization code received.")
        return None

if __name__ == "__main__":
    user = authenticate_user()
    if user:
        print(f"Hello, {user.get('name')}!")

```

## Adherence to Integrated Software Design Framework (RASM)

This module is developed with a strong emphasis on the RASM principles:

*   **Reliability:**
    *   **Error Handling:** The `GoogleOAuth` class includes `response.raise_for_status()` for API calls, ensuring that network or API errors are explicitly caught and handled. This prevents silent failures and promotes robust operation.
    *   **Explicit Dependencies:** The module clearly defines its dependency on the `requests` library in `requirements.txt`, ensuring a consistent and reliable environment.
    *   **Idempotency:** The OAuth flow itself is designed to be largely idempotent for token exchange, allowing for safe retries in case of transient network issues.

*   **Availability:**
    *   **Centralized Configuration:** Credentials and scopes are managed via environment variables, allowing for easy updates and consistent deployment across different environments, which is crucial for maintaining service availability.
    *   **Graceful Degradation:** The Streamlit example includes checks for missing environment variables, preventing the application from starting in an unconfigured state and providing clear feedback to the user.

*   **Scalability:**
    *   **Modular Design:** The `GoogleOAuth` class encapsulates the OAuth logic, making it reusable across various Python applications (Streamlit, Flask, Django, etc.) without tight coupling. This promotes horizontal scalability by allowing the authentication mechanism to be easily integrated into multiple service instances.
    *   **Stateless Operations:** The core OAuth flow (generating URLs, exchanging codes) is largely stateless, relying on standard OAuth protocols, which inherently supports scalable architectures.

*   **Maintainability:**
    *   **Documentation-First:** This `README.md` and the docstrings within `oauth_module.py` provide clear, up-to-date documentation on setup, usage, and design choices.
    *   **Clear Code Structure:** The `GoogleOAuth` class is well-organized with distinct methods for each step of the OAuth process, making the code easy to understand, debug, and extend.
    *   **Explicit Dependencies:** All external libraries are explicitly listed in `requirements.txt`, simplifying dependency management.
    *   **Configuration Management:** The reliance on environment variables for configuration simplifies deployment and reduces the risk of hardcoded values, improving maintainability.
    *   **Readability:** The code is written with clear variable names, comments, and type hints to enhance readability and reduce cognitive load for future developers.