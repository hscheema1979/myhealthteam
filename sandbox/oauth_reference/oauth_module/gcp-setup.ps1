# Google Cloud Platform Setup Script for OAuth Streamlit App
# This script sets up the necessary GCP services for deploying to Cloud Run or App Engine

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId = "PCOPs",
    [string]$Region = "us-central1"
)

Write-Host "Setting up Google Cloud Project: $ProjectId" -ForegroundColor Green

# Set the project
Write-Host "Setting project to $ProjectId..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Enable necessary APIs
Write-Host "Enabling required APIs..." -ForegroundColor Yellow
$apis = @(
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "appengine.googleapis.com",
    "secretmanager.googleapis.com",
    "iamcredentials.googleapis.com",
    "containerregistry.googleapis.com",
    "artifactregistry.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "Enabling $api..." -ForegroundColor Cyan
    gcloud services enable $api
}

# Set default region
Write-Host "Setting default region to $Region..." -ForegroundColor Yellow
gcloud config set run/region $Region
gcloud config set compute/region $Region

# Create Artifact Registry repository for Docker images (for Cloud Run)
Write-Host "Creating Artifact Registry repository..." -ForegroundColor Yellow
gcloud artifacts repositories create oauth-streamlit-repo `
    --repository-format=docker `
    --location=$Region `
    --description="Repository for OAuth Streamlit application"

# Create secrets for OAuth credentials
Write-Host "Creating secrets for OAuth credentials..." -ForegroundColor Yellow
Write-Host "You'll need to set these values manually after running this script:" -ForegroundColor Red
Write-Host "  gcloud secrets create google-client-id --data-file=-" -ForegroundColor White
Write-Host "  gcloud secrets create google-client-secret --data-file=-" -ForegroundColor White

# Create the secrets (empty for now)
gcloud secrets create google-client-id --replication-policy="automatic" 2>$null
gcloud secrets create google-client-secret --replication-policy="automatic" 2>$null

Write-Host "`nSetup complete! Next steps:" -ForegroundColor Green
Write-Host "1. Set your OAuth secrets:" -ForegroundColor Yellow
Write-Host "   echo 'YOUR_CLIENT_ID' | gcloud secrets versions add google-client-id --data-file=-" -ForegroundColor White
Write-Host "   echo 'YOUR_CLIENT_SECRET' | gcloud secrets versions add google-client-secret --data-file=-" -ForegroundColor White
Write-Host "`n2. Choose deployment method:" -ForegroundColor Yellow
Write-Host "   - For Cloud Run: Run deploy-cloudrun.ps1" -ForegroundColor White
Write-Host "   - For App Engine: Run deploy-appengine.ps1" -ForegroundColor White