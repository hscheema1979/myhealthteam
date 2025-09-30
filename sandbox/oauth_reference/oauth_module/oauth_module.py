import os
import requests
import json
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

class GoogleOAuth:
    """
    A class to handle Google OAuth 2.0 authentication flow.

    Adheres to RASM principles by:
    - Centralizing configuration via environment variables for maintainability and security.
    - Providing clear methods for each step of the OAuth flow for reliability and maintainability.
    - Implementing basic error handling for API calls.
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scopes: list):
        """
        Initializes the GoogleOAuth client.

        Args:
            client_id: The Google OAuth client ID.
            client_secret: The Google OAuth client secret.
            redirect_uri: The authorized redirect URI for your application.
            scopes: A list of scopes requested by the application.
        """
        if not all([client_id, client_secret, redirect_uri, scopes]):
            raise ValueError("All OAuth parameters (client_id, client_secret, redirect_uri, scopes) must be provided.")

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = " ".join(scopes) # Scopes are space-separated in the URL

        self.AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
        self.TOKEN_URL = "https://oauth2.googleapis.com/token"
        self.USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def get_authorization_url(self) -> str:
        """
        Generates the Google OAuth authorization URL.

        Returns:
            The authorization URL string.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes,
            "response_type": "code",
            "access_type": "offline", # Request refresh token
            "prompt": "consent" # Always show consent screen
        }
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str) -> dict:
        """
        Exchanges the authorization code for access and ID tokens.

        Args:
            code: The authorization code received from Google.

        Returns:
            A dictionary containing the access token, ID token, and other token information.
            Raises an exception if the token exchange fails.
        """
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(self.TOKEN_URL, data=data, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

    def get_user_info(self, access_token: str) -> dict:
        """
        Retrieves user information using the access token.

        Args:
            access_token: The access token obtained from Google.

        Returns:
            A dictionary containing user profile information.
            Raises an exception if retrieving user info fails.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USERINFO_URL, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

if __name__ == "__main__":
    # Example Usage (for testing purposes)
    # In a real application, these would be loaded from environment variables
    # or a secure configuration management system.
    CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "YOUR_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
    REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:5001/auth/callback")
    SCOPES = os.environ.get("GOOGLE_SCOPES", "openid email profile").split(" ")

    # Replace with your actual credentials for testing
    if CLIENT_ID == "YOUR_CLIENT_ID" or CLIENT_SECRET == "YOUR_CLIENT_SECRET":
        print("WARNING: Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, and GOOGLE_SCOPES environment variables.")
        print("Using placeholder values for demonstration.")
        print("Also, ensure you have installed the required packages: pip install -r requirements.txt")

    oauth_client = GoogleOAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES)

    print(f"Authorization URL: {oauth_client.get_authorization_url()}")
    print("Please visit the URL above to authorize the application.")
    print("After authorization, you will be redirected to your REDIRECT_URI with a 'code' parameter.")
    print("Copy the 'code' value from the URL and paste it here:")

    # In a real application, this code would be handled by your web server
    # or Streamlit app's callback route.
    auth_code = input("Enter the authorization code: ")
    if auth_code:
        try:
            tokens = oauth_client.exchange_code_for_tokens(auth_code)
            print("Tokens:", json.dumps(tokens, indent=2))
            user_info = oauth_client.get_user_info(tokens["access_token"])
            print("User Info:", json.dumps(user_info, indent=2))
        except requests.exceptions.RequestException as e:
            print(f"Error during OAuth flow: {e}")
    else:
        print("No authorization code provided.")

    # Ensure environment variables are loaded for the command-line example
    load_dotenv()

    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
    scopes_str = os.environ.get("GOOGLE_SCOPES", "openid email profile")
    scopes = scopes_str.split(",")

    if not all([client_id, client_secret, redirect_uri]):
        print("Error: Missing Google OAuth environment variables. Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, and GOOGLE_SCOPES.")
        exit(1)

    oauth_client = GoogleOAuth(client_id, client_secret, redirect_uri, scopes)

    print("\n--- Command-Line OAuth Example ---")
    auth_url = oauth_client.get_authorization_url()
    print(f"Please go to this URL to authorize: {auth_url}")

    authorization_code = input("Enter the authorization code from the redirect URL: ")

    if authorization_code:
        try:
            tokens = oauth_client.exchange_code_for_tokens(authorization_code)
            access_token = tokens["access_token"]
            user_info = oauth_client.get_user_info(access_token)
            print("Authentication successful!")
            print("User Info:", user_info)
        except Exception as e:
            print(f"Authentication failed: {e}")
    else:
        print("No authorization code received.")