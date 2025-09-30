# Deploy OAuth Streamlit App to Google Cloud Run
param(
    [string]$ProjectId = "PCOPs",
    [string]$Region = "us-central1",
    [string]$ServiceName = "oauth-streamlit",
    [string]$ImageTag = "latest"
)

Write-Host "Deploying OAuth Streamlit App to Cloud Run..." -ForegroundColor Green
Write-Host "Project: $ProjectId" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Service: $ServiceName" -ForegroundColor Yellow

# Set project and region
gcloud config set project $ProjectId
gcloud config set run/region $Region

# Build and push Docker image
$ImageName = "$Region-docker.pkg.dev/$ProjectId/oauth-streamlit-repo/oauth-streamlit:$ImageTag"

Write-Host "Building Docker image..." -ForegroundColor Cyan
docker build -t $ImageName -f Dockerfile .

Write-Host "Pushing image to Artifact Registry..." -ForegroundColor Cyan
docker push $ImageName

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Cyan
gcloud run deploy $ServiceName `
    --image $ImageName `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --port 8080 `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10 `
    --timeout 300 `
    --concurrency 80 `
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$ProjectId" `
    --set-secrets "GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest"

# Get the service URL
$ServiceUrl = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"

Write-Host "`nDeployment completed!" -ForegroundColor Green
Write-Host "Service URL: $ServiceUrl" -ForegroundColor Yellow
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Update your OAuth redirect URI to: $ServiceUrl/auth/callback" -ForegroundColor White
Write-Host "2. Test the application at: $ServiceUrl" -ForegroundColor White
Write-Host "3. Monitor logs with: gcloud logs tail --follow --resource=cloud_run_revision --filter=resource.labels.service_name=$ServiceName" -ForegroundColor White