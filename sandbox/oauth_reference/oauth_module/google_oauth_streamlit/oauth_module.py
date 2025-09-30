"""
Google OAuth Module for Streamlit Applications

This module provides a simple interface for Google OAuth authentication
in Streamlit applications.
"""

import os
import requests
from urllib.parse import urlencode, parse_qs
import secrets
import streamlit as st


class GoogleOAuth:
    """
    Google OAuth handler for Streamlit applications.
    
    This class manages the OAuth flow including authorization URL generation,
    token exchange, and user information retrieval.
    """
    
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, scopes=None):
        """
        Initialize the Google OAuth handler.
        
        Args:
            client_id (str, optional): Google OAuth client ID. If None, reads from environment.
            client_secret (str, optional): Google OAuth client secret. If None, reads from environment.
            redirect_uri (str, optional): OAuth redirect URI. If None, reads from environment.
            scopes (str, optional): Comma-separated OAuth scopes. If None, reads from environment.
        """
        self.client_id = client_id or os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = redirect_uri or os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5001/auth/callback')
        
        # Parse scopes from string to list
        scopes_str = scopes or os.getenv('GOOGLE_SCOPES', 'https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile,openid')
        self.scopes = [scope.strip() for scope in scopes_str.split(',')]
        
        # OAuth endpoints
        self.auth_url = "https://accounts.google.com/o/oauth2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate that all required configuration is present."""
        if not self.client_id:
            raise ValueError("Google Client ID is required. Set GOOGLE_CLIENT_ID environment variable.")
        if not self.client_secret:
            raise ValueError("Google Client Secret is required. Set GOOGLE_CLIENT_SECRET environment variable.")
        if not self.redirect_uri:
            raise ValueError("Redirect URI is required. Set GOOGLE_REDIRECT_URI environment variable.")
    
    def get_authorization_url(self):
        """
        Generate the Google OAuth authorization URL.
        
        Returns:
            tuple: (authorization_url, state) where state is used for CSRF protection
        """
        # Generate a random state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state
        }
        
        authorization_url = f"{self.auth_url}?{urlencode(params)}"
        return authorization_url, state
    
    def exchange_code_for_token(self, code, state=None):
        """
        Exchange authorization code for access token.
        
        Args:
            code (str): Authorization code from Google
            state (str, optional): State parameter for CSRF protection
            
        Returns:
            dict: Token response containing access_token, refresh_token, etc.
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_info(self, access_token):
        """
        Get user information using the access token.
        
        Args:
            access_token (str): OAuth access token
            
        Returns:
            dict: User information including email, name, etc.
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(self.userinfo_url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def revoke_token(self, token):
        """
        Revoke an OAuth token.
        
        Args:
            token (str): Token to revoke (access_token or refresh_token)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            revoke_url = f"https://oauth2.googleapis.com/revoke?token={token}"
            response = requests.post(revoke_url)
            return response.status_code == 200
        except Exception:
            return False


def create_oauth_instance():
    """
    Factory function to create a GoogleOAuth instance with environment variables.
    
    Returns:
        GoogleOAuth: Configured OAuth instance
    """
    return GoogleOAuth()


if __name__ == "__main__":
    # Example usage
    oauth = create_oauth_instance()
    auth_url, state = oauth.get_authorization_url()
    print(f"Visit this URL to authorize the application: {auth_url}")