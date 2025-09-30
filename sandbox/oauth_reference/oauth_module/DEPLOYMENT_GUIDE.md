# 🚀 Google Cloud Deployment Guide

This guide provides step-by-step instructions for deploying your OAuth Streamlit application to Google Cloud Platform using either Cloud Run or App Engine.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Cloud Run Deployment](#cloud-run-deployment)
4. [App Engine Deployment](#app-engine-deployment)
5. [CI/CD Setup](#cicd-setup)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### Required Tools
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Cloud Run)
- PowerShell 7+ (Windows)
- Git

### Google Cloud Project
- Project ID: **PCOPs**
- Billing enabled
- Owner or Editor permissions

## 🏗️ Initial Setup

### 1. Clone and Prepare Repository
```powershell
cd d:\Git\oauth_module
```

### 2. Authenticate with Google Cloud
```powershell
gcloud auth login
gcloud auth application-default login
```

### 3. Run Initial Setup
```powershell
.\gcp-setup.ps1 -ProjectId "PCOPs" -Region "us-central1"
```

This script will:
- Enable required APIs
- Create Artifact Registry repository
- Set up Secret Manager
- Configure default regions

### 4. Configure OAuth Secrets
```powershell
# Set your OAuth credentials
echo "YOUR_GOOGLE_CLIENT_ID" | gcloud secrets versions add google-client-id --data-file=-
echo "YOUR_GOOGLE_CLIENT_SECRET" | gcloud secrets versions add google-client-secret --data-file=-
```

### 5. Update OAuth Configuration
Follow the [OAuth Configuration Guide](oauth-config-guide.md) to update your Google Cloud Console settings.

## ☁️ Cloud Run Deployment

### Advantages
- ✅ Automatic scaling to zero
- ✅ Pay-per-request pricing
- ✅ Fast cold starts
- ✅ Easy rollbacks
- ✅ Custom domains

### Deploy to Cloud Run
```powershell
.\deploy-cloudrun.ps1 -ProjectId "PCOPs" -Region "us-central1" -ServiceName "oauth-streamlit"
```

### Manual Deployment Steps
If you prefer manual deployment:

1. **Build Docker Image**
   ```powershell
   docker build -t us-central1-docker.pkg.dev/PCOPs/oauth-streamlit-repo/oauth-streamlit:latest .
   ```

2. **Push to Artifact Registry**
   ```powershell
   docker push us-central1-docker.pkg.dev/PCOPs/oauth-streamlit-repo/oauth-streamlit:latest
   ```

3. **Deploy to Cloud Run**
   ```powershell
   gcloud run deploy oauth-streamlit `
       --image us-central1-docker.pkg.dev/PCOPs/oauth-streamlit-repo/oauth-streamlit:latest `
       --region us-central1 `
       --allow-unauthenticated `
       --set-secrets "GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest"
   ```

### Expected Output
```
Service URL: https://oauth-streamlit-[hash]-uc.a.run.app
```

## 🏢 App Engine Deployment

### Advantages
- ✅ Integrated with Google services
- ✅ Automatic SSL certificates
- ✅ Traffic splitting
- ✅ Version management
- ✅ Cron jobs support

### Deploy to App Engine
```powershell
.\deploy-appengine.ps1 -ProjectId "PCOPs" -Version "v1" -Promote
```

### Manual Deployment Steps
If you prefer manual deployment:

1. **Prepare Production Files**
   ```powershell
   Copy-Item "requirements-production.txt" "requirements.txt" -Force
   Copy-Item "streamlit_app_production.py" "streamlit_app.py" -Force
   ```

2. **Deploy to App Engine**
   ```powershell
   gcloud app deploy app.yaml --version v1 --promote
   ```

3. **Restore Original Files**
   ```powershell
   git checkout -- requirements.txt streamlit_app.py
   ```

### Expected Output
```
Service URL: https://PCOPs.uc.r.appspot.com
```

## 🔄 CI/CD Setup

### Automatic Deployment with Cloud Build

1. **Connect Repository**
   ```powershell
   gcloud builds triggers create github `
       --repo-name="oauth_module" `
       --repo-owner="YOUR_GITHUB_USERNAME" `
       --branch-pattern="^main$" `
       --build-config="cloudbuild.yaml"
   ```

2. **Manual Trigger**
   ```powershell
   gcloud builds submit --config cloudbuild.yaml .
   ```

### GitHub Actions (Alternative)
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Google Cloud
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: PCOPs
      - run: gcloud builds submit --config cloudbuild.yaml .
```

## 📊 Monitoring and Maintenance

### View Logs
```powershell
# Cloud Run logs
gcloud logs tail --follow --resource=cloud_run_revision --filter="resource.labels.service_name=oauth-streamlit"

# App Engine logs
gcloud app logs tail -s default
```

### Monitor Performance
- **Cloud Run**: [Cloud Run Console](https://console.cloud.google.com/run)
- **App Engine**: [App Engine Console](https://console.cloud.google.com/appengine)

### Update Secrets
```powershell
echo "NEW_CLIENT_ID" | gcloud secrets versions add google-client-id --data-file=-
echo "NEW_CLIENT_SECRET" | gcloud secrets versions add google-client-secret --data-file=-
```

### Scale Configuration

#### Cloud Run
```powershell
gcloud run services update oauth-streamlit `
    --region us-central1 `
    --min-instances 1 `
    --max-instances 20 `
    --memory 2Gi `
    --cpu 2
```

#### App Engine
Update `app.yaml`:
```yaml
automatic_scaling:
  min_instances: 1
  max_instances: 20
  target_cpu_utilization: 0.6
```

## 🔧 Troubleshooting

### Common Issues

#### 1. "redirect_uri_mismatch" Error
**Cause**: OAuth redirect URI doesn't match Google Cloud Console configuration.

**Solution**:
1. Check your deployed URL
2. Update OAuth configuration in Google Cloud Console
3. Ensure exact match including `https://` and `/auth/callback`

#### 2. "Permission Denied" Error
**Cause**: Service account lacks necessary permissions.

**Solution**:
```powershell
gcloud projects add-iam-policy-binding PCOPs `
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT@PCOPs.iam.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor"
```

#### 3. "Secret Not Found" Error
**Cause**: Secrets not properly configured.

**Solution**:
```powershell
# Verify secrets exist
gcloud secrets list

# Check secret versions
gcloud secrets versions list google-client-id
gcloud secrets versions list google-client-secret
```

#### 4. Container Build Failures
**Cause**: Docker build issues or missing dependencies.

**Solution**:
1. Test Docker build locally:
   ```powershell
   docker build -t test-oauth-app .
   docker run -p 8080:8080 test-oauth-app
   ```
2. Check build logs in Cloud Build console

#### 5. App Engine Deployment Timeout
**Cause**: App takes too long to start.

**Solution**:
Update `app.yaml`:
```yaml
readiness_check:
  app_start_timeout_sec: 600
```

### Debug Commands

```powershell
# Check service status
gcloud run services describe oauth-streamlit --region us-central1

# View recent deployments
gcloud app versions list

# Check IAM permissions
gcloud projects get-iam-policy PCOPs

# Test secret access
gcloud secrets versions access latest --secret="google-client-id"
```

### Performance Optimization

#### Cloud Run
- Use multi-stage Docker builds
- Implement health checks
- Configure appropriate CPU/memory
- Use connection pooling

#### App Engine
- Enable instance warmup
- Configure appropriate instance class
- Use memcache for session storage
- Optimize startup time

### Security Best Practices

1. **Use HTTPS only** in production
2. **Rotate secrets** regularly
3. **Monitor access logs**
4. **Implement rate limiting**
5. **Use least privilege IAM**

### Cost Optimization

#### Cloud Run
- Set appropriate min/max instances
- Use CPU allocation efficiently
- Monitor request patterns

#### App Engine
- Use automatic scaling
- Monitor instance hours
- Consider scheduled scaling

## 📞 Support

### Resources
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [App Engine Documentation](https://cloud.google.com/appengine/docs)
- [OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)

### Getting Help
1. Check Cloud Logging for detailed errors
2. Review this troubleshooting guide
3. Consult Google Cloud documentation
4. Contact your system administrator

---

## 🎉 Success Checklist

After deployment, verify:

- [ ] Application loads successfully
- [ ] OAuth login works
- [ ] User information displays correctly
- [ ] Logout functionality works
- [ ] HTTPS is enforced
- [ ] Logs are being generated
- [ ] Monitoring is active
- [ ] Secrets are secure

**Congratulations! Your OAuth Streamlit app is now running on Google Cloud! 🚀**