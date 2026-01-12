# Google OAuth Setup Guide

## Overview

Google OAuth has been enabled for the application. Users can now sign in using their Google account in addition to the traditional email/password method.

## Configuration

### Environment Variables

The following environment variables need to be set:

```bash
# Google OAuth Credentials
GOOGLE_CLIENT_ID=298448117337-5eno2h0163etcl9vnqjjj524k48ae0d2.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<your_client_secret_from_google_console>
GOOGLE_REDIRECT_URI=http://localhost:8501

# For production, use your production URL:
# GOOGLE_REDIRECT_URI=https://your-production-domain.com

# JWT Configuration (already set)
JWT_SECRET_KEY=uAPL2jp2IcmEN5vz-NAR_-Y2pThujnFNolRa2XW0Enk
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 days
```

### Setting Environment Variables

#### Option 1: Using .env file (Development)

1. Copy `.env.example` to `.env`
2. Fill in your `GOOGLE_CLIENT_SECRET`
3. Install python-dotenv: `pip install python-dotenv`

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_CLIENT_SECRET
```

#### Option 2: System Environment Variables

**Windows (Command Prompt):**
```cmd
set GOOGLE_CLIENT_ID=298448117337-5eno2h0163etcl9vnqjjj524k48ae0d2.apps.googleusercontent.com
set GOOGLE_CLIENT_SECRET=your_secret_here
set GOOGLE_REDIRECT_URI=http://localhost:8501
```

**Windows (PowerShell):**
```powershell
$env:GOOGLE_CLIENT_ID="298448117337-5eno2h0163etcl9vnqjjj524k48ae0d2.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET="your_secret_here"
$env:GOOGLE_REDIRECT_URI="http://localhost:8501"
```

**Linux/Mac:**
```bash
export GOOGLE_CLIENT_ID=298448117337-5eno2h0163etcl9vnqjjj524k48ae0d2.apps.googleusercontent.com
export GOOGLE_CLIENT_SECRET=your_secret_here
export GOOGLE_REDIRECT_URI=http://localhost:8501
```

## Files Created/Modified

### New Files:
- `src/oauth_config.py` - OAuth configuration module
- `src/google_oauth.py` - Google OAuth helper functions
- `.env.example` - Example environment variables file

### Modified Files:
- `src/auth_module.py` - Added Google OAuth authentication methods and updated login UI
- `production.db` - Database schema updated with OAuth columns

### Database Changes

The `users` table now has the following new columns:
- `oauth_provider` - Stores the OAuth provider (e.g., 'google')
- `google_id` - Stores the unique Google user ID
- `picture_url` - Stores the user's profile picture URL

## How It Works

1. **User clicks "Sign in with Google"**
   - Application generates a Google OAuth authorization URL
   - User is redirected to Google's sign-in page

2. **Google callback**
   - After authentication, Google redirects back with an authorization code
   - The code is in the URL query parameters (`?code=...&state=...`)

3. **Token exchange**
   - Application exchanges the authorization code for an access token
   - Fetches user information from Google

4. **User creation/login**
   - If the user's Google ID exists in the database, they're logged in
   - If the email exists but no Google ID, the account is linked
   - If neither exists, a new user account is created

5. **Session management**
   - User session is created same as email/password login
   - "Remember Me" functionality works with OAuth too

## Google Console Setup

To get your `GOOGLE_CLIENT_SECRET`:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Navigate to: APIs & Services > Credentials
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs:
     - Development: `http://localhost:8501`
     - Production: `https://your-production-domain.com`
5. Copy the Client ID and Client Secret

## Security Notes

- The `GOOGLE_CLIENT_SECRET` should never be committed to version control
- Always use HTTPS for OAuth redirects in production
- The JWT secret key should be unique and kept secure
- OAuth tokens are not stored permanently - only the Google ID is saved

## Troubleshooting

### Google Sign-In button not showing
- Check that `GOOGLE_CLIENT_ID` environment variable is set
- Verify the value matches your Google Console credentials

### "Google OAuth configuration error" message
- Ensure the redirect URI in Google Console matches exactly (including protocol and port)
- Check browser console for additional error messages

### Authentication fails after Google sign-in
- Verify `GOOGLE_CLIENT_SECRET` is correct
- Check that the redirect URI matches between code and Google Console

### Database errors
- Run the OAuth migration if you haven't:
  ```sql
  ALTER TABLE users ADD COLUMN oauth_provider TEXT DEFAULT NULL;
  ALTER TABLE users ADD COLUMN google_id TEXT DEFAULT NULL;
  ALTER TABLE users ADD COLUMN picture_url TEXT DEFAULT NULL;
  ```
