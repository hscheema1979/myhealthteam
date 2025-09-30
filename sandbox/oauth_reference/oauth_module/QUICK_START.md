# 🚀 Quick Start - Deploy to Google Cloud

Get your OAuth Streamlit app running on Google Cloud in under 10 minutes!

## 🎯 Choose Your Deployment Method

### Option A: Cloud Run (Recommended)
**Best for**: Scalable, cost-effective applications

```powershell
# 1. Setup Google Cloud
.\gcp-setup.ps1

# 2. Set OAuth secrets
echo "YOUR_CLIENT_ID" | gcloud secrets versions add google-client-id --data-file=-
echo "YOUR_CLIENT_SECRET" | gcloud secrets versions add google-client-secret --data-file=-

# 3. Deploy
.\deploy-cloudrun.ps1
```

### Option B: App Engine
**Best for**: Enterprise applications with integrated Google services

```powershell
# 1. Setup Google Cloud
.\gcp-setup.ps1

# 2. Set OAuth secrets
echo "YOUR_CLIENT_ID" | gcloud secrets versions add google-client-id --data-file=-
echo "YOUR_CLIENT_SECRET" | gcloud secrets versions add google-client-secret --data-file=-

# 3. Deploy
.\deploy-appengine.ps1
```

## 📝 Prerequisites Checklist

- [ ] Google Cloud SDK installed
- [ ] Docker Desktop installed (for Cloud Run)
- [ ] Authenticated with `gcloud auth login`
- [ ] Project "PCOPs" exists and billing is enabled
- [ ] OAuth credentials from Google Cloud Console

## 🔧 Get OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** > **Credentials**
3. Create **OAuth 2.0 Client ID**
4. Add redirect URI: `https://YOUR_DEPLOYED_URL/auth/callback`

## ⚡ One-Command Deployment

For the fastest deployment:

```powershell
# Cloud Run (recommended)
.\gcp-setup.ps1 && .\deploy-cloudrun.ps1

# App Engine
.\gcp-setup.ps1 && .\deploy-appengine.ps1
```

## 🎉 After Deployment

1. **Update OAuth Settings**: Add your deployed URL to Google Cloud Console
2. **Test the App**: Visit your deployed URL and try logging in
3. **Monitor**: Check logs with `gcloud logs tail`

## 🆘 Need Help?

- **Full Guide**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **OAuth Setup**: See [oauth-config-guide.md](oauth-config-guide.md)
- **Troubleshooting**: Check the troubleshooting section in the deployment guide

---

**Your app will be live in minutes! 🚀**