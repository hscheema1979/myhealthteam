# OAuth Configuration Guide for Production Deployment

## Overview
This guide helps you configure Google OAuth for your production deployment on Google Cloud Platform.

## Step 1: Update OAuth Consent Screen

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: **PCOPs**
3. Navigate to **APIs & Services** > **OAuth consent screen**
4. Update the following fields:

### App Information
- **App name**: OAuth Streamlit App
- **User support email**: Your email address
- **App logo**: (Optional) Upload your app logo
- **App domain**: Your production domain
- **Developer contact information**: Your email address

### Authorized Domains
Add your production domains:
- `PCOPs.uc.r.appspot.com` (for App Engine)
- `run.app` (for Cloud Run)

## Step 2: Update OAuth 2.0 Client ID

1. Navigate to **APIs & Services** > **Credentials**
2. Click on your existing OAuth 2.0 Client ID or create a new one
3. Update the **Authorized redirect URIs**:

### For App Engine Deployment
```
https://PCOPs.uc.r.appspot.com/auth/callback
https://oauth-streamlit-dot-PCOPs.uc.r.appspot.com/auth/callback
```

### For Cloud Run Deployment
```
https://oauth-streamlit-[HASH]-uc.a.run.app/auth/callback
```
*Note: Replace [HASH] with the actual hash from your Cloud Run URL*

### For Development (keep these for testing)
```
http://localhost:5001/auth/callback
http://localhost:8501/auth/callback
```

## Step 3: Update Authorized JavaScript Origins

Add these origins:

### For App Engine
```
https://PCOPs.uc.r.appspot.com
https://oauth-streamlit-dot-PCOPs.uc.r.appspot.com
```

### For Cloud Run
```
https://oauth-streamlit-[HASH]-uc.a.run.app
```

### For Development
```
http://localhost:5001
http://localhost:8501
```

## Step 4: Configure Secrets in Google Cloud

Run these commands to set your OAuth credentials:

```powershell
# Set your OAuth Client ID
echo "YOUR_ACTUAL_CLIENT_ID" | gcloud secrets versions add google-client-id --data-file=-

# Set your OAuth Client Secret
echo "YOUR_ACTUAL_CLIENT_SECRET" | gcloud secrets versions add google-client-secret --data-file=-
```

## Step 5: Verify Configuration

After deployment, verify your configuration:

1. **Check redirect URIs**: Ensure they match exactly (including https://)
2. **Test OAuth flow**: Try logging in from your production app
3. **Check logs**: Monitor Cloud Logging for any OAuth errors

## Common Issues and Solutions

### Issue: "redirect_uri_mismatch" Error
**Solution**: Ensure the redirect URI in your Google Cloud Console exactly matches the one your app is using.

### Issue: "invalid_client" Error
**Solution**: Verify your Client ID and Client Secret are correctly set in Secret Manager.

### Issue: "access_denied" Error
**Solution**: Check if your OAuth consent screen is properly configured and published.

## Security Best Practices

1. **Use HTTPS only** in production
2. **Restrict domains** in OAuth consent screen
3. **Monitor access logs** regularly
4. **Rotate secrets** periodically
5. **Use least privilege** for service accounts

## Testing Your Configuration

Use this checklist to verify everything works:

- [ ] OAuth consent screen is configured
- [ ] Redirect URIs are correctly set
- [ ] Secrets are stored in Secret Manager
- [ ] App deploys successfully
- [ ] Login flow works end-to-end
- [ ] User information is displayed correctly
- [ ] Logout works properly

## Support

If you encounter issues:

1. Check the [Google OAuth 2.0 documentation](https://developers.google.com/identity/protocols/oauth2)
2. Review Cloud Logging for detailed error messages
3. Verify all URLs use HTTPS in production
4. Test with a simple OAuth flow first