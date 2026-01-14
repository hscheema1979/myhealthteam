"""
Google OAuth Helper Module

This module handles Google OAuth authentication flow including:
- Generating authorization URLs
- Exchanging authorization codes for tokens
- Fetching user information from Google
- Creating or updating users from Google profile data
"""

import json
import secrets
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional, Dict, Any
from src.oauth_config import get_oauth_config
from src.database import get_db_connection


def generate_state_token() -> str:
    """
    Generate a secure random state token for CSRF protection

    Returns:
        Random state token
    """
    return secrets.token_urlsafe(32)


def get_google_auth_url(redirect_uri: Optional[str] = None) -> str:
    """
    Generate Google OAuth authorization URL

    Args:
        redirect_uri: Optional override for redirect URI

    Returns:
        Google OAuth authorization URL with state parameter
    """
    config = get_oauth_config()

    if redirect_uri:
        config.google_redirect_uri = redirect_uri

    state = generate_state_token()
    return config.get_google_auth_url(state=state)


def exchange_code_for_token(code: str, redirect_uri: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Exchange authorization code for access token

    Args:
        code: Authorization code from Google OAuth callback
        redirect_uri: Optional override for redirect URI

    Returns:
        Token response dict with access_token, refresh_token, etc. or None if failed
    """
    config = get_oauth_config()

    if not config.google_client_secret:
        print("Error: GOOGLE_CLIENT_SECRET not configured")
        return None

    token_url = config.get_google_token_url()
    post_uri = redirect_uri or config.google_redirect_uri

    data = {
        "code": code,
        "client_id": config.google_client_id,
        "client_secret": config.google_client_secret,
        "redirect_uri": post_uri,
        "grant_type": "authorization_code",
    }

    try:
        req = urllib.request.Request(
            token_url,
            data=urllib.parse.urlencode(data).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode("utf-8")
            return json.loads(response_data)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP Error exchanging token: {e.code} - {error_body}")
        return None
    except urllib.error.URLError as e:
        print(f"URL Error exchanging token: {e.reason}")
        return None
    except Exception as e:
        print(f"Error exchanging token: {e}")
        return None


def get_google_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user information from Google using access token

    Args:
        access_token: Google OAuth access token

    Returns:
        User info dict with id, email, name, picture, etc. or None if failed
    """
    config = get_oauth_config()
    userinfo_url = config.get_google_userinfo_url()

    try:
        req = urllib.request.Request(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode("utf-8")
            return json.loads(response_data)

    except urllib.error.HTTPError as e:
        print(f"HTTP Error fetching user info: {e.code}")
        return None
    except urllib.error.URLError as e:
        print(f"URL Error fetching user info: {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return None


def get_or_create_user_from_google(user_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get existing user or create new user from Google profile information.

    Google-only authentication: Trusts Google completely.
    - Looks up user by google_id only (NOT by email)
    - Updates user info from Google on each login
    - Creates new user if google_id not found

    This keeps Google logins completely separate from email/password logins.

    Args:
        user_info: Google user info dict containing id, email, name, picture

    Returns:
        User dictionary from database or None if failed
    """
    google_id = user_info.get("id")
    email = user_info.get("email")
    given_name = user_info.get("given_name", "")
    family_name = user_info.get("family_name", "")
    full_name = user_info.get("name", f"{given_name} {family_name}".strip())
    picture_url = user_info.get("picture")

    if not email or not google_id:
        print("Error: Missing required fields from Google user info")
        return None

    conn = get_db_connection()
    try:
        # Look for existing user by google_id ONLY (Google users are independent)
        user = conn.execute("""
            SELECT user_id, username, email, first_name, last_name, full_name, status,
                   oauth_provider, google_id, picture_url
            FROM users
            WHERE google_id = ? AND status = 'active'
        """, (google_id,)).fetchone()

        if user:
            # User exists - update their info from Google (names, picture might have changed)
            conn.execute("""
                UPDATE users
                SET email = ?,
                    first_name = ?,
                    last_name = ?,
                    full_name = ?,
                    picture_url = ?,
                    oauth_provider = 'google',
                    last_login = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (email, given_name, family_name, full_name, picture_url, user['user_id']))
            conn.commit()

            # Return updated user
            user = conn.execute("""
                SELECT user_id, username, email, first_name, last_name, full_name, status,
                       oauth_provider, google_id, picture_url
                FROM users
                WHERE user_id = ?
            """, (user['user_id'],)).fetchone()
            return dict(user)

        # User doesn't exist - create new Google-only user
        # Generate unique username from email
        username = email.split('@')[0]
        # Ensure username is unique
        existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            counter = 1
            while conn.execute("SELECT 1 FROM users WHERE username = ?", (f"{username}{counter}",)).fetchone():
                counter += 1
            username = f"{username}{counter}"

        conn.execute("""
            INSERT INTO users (username, email, first_name, last_name, full_name,
                              oauth_provider, google_id, picture_url, status)
            VALUES (?, ?, ?, ?, ?, 'google', ?, ?, 'active')
        """, (username, email, given_name, family_name, full_name, google_id, picture_url))

        conn.commit()

        # Get the newly created user
        user = conn.execute("""
            SELECT user_id, username, email, first_name, last_name, full_name, status,
                   oauth_provider, google_id, picture_url
            FROM users
            WHERE google_id = ?
        """, (google_id,)).fetchone()

        print(f"Created new Google user: {email}, user_id: {user['user_id'] if user else 'None'}")
        return dict(user) if user else None

    except Exception as e:
        print(f"Error creating/updating user from Google: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def handle_google_oauth_callback(code: str, redirect_uri: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Handle the complete Google OAuth callback flow

    Args:
        code: Authorization code from Google
        redirect_uri: Optional override for redirect URI

    Returns:
        User dictionary if successful, None otherwise
    """
    # Exchange code for token
    token_response = exchange_code_for_token(code, redirect_uri)
    if not token_response:
        print("Failed to exchange authorization code for token")
        return None

    access_token = token_response.get("access_token")
    if not access_token:
        print("No access token in response")
        return None

    # Get user info from Google
    user_info = get_google_user_info(access_token)
    if not user_info:
        print("Failed to fetch user info from Google")
        return None

    # Get or create user in database
    user = get_or_create_user_from_google(user_info)
    return user
