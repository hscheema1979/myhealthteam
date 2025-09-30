# Deploy Cloud Run with Environment Variables
Write-Host "Deploying OAuth Streamlit to Cloud Run with Environment Variables..." -ForegroundColor Green

# Read environment variables from .env file
$envVars = @{}
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim('"')
            $envVars[$key] = $value
        }
    }
}

# Build environment variables string for gcloud
$envVarString = ""
foreach ($key in $envVars.Keys) {
    if ($envVarString -ne "") {
        $envVarString += ","
    }
    $envVarString += "$key=$($envVars[$key])"
}

Write-Host "Environment variables to set:" -ForegroundColor Yellow
foreach ($key in $envVars.Keys) {
    if ($key -like "*SECRET*") {
        Write-Host "  $key=***HIDDEN***" -ForegroundColor Cyan
    } else {
        Write-Host "  $key=$($envVars[$key])" -ForegroundColor Cyan
    }
}

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Green
gcloud run deploy oauth-streamlit --source . --region=us-central1 --allow-unauthenticated --platform=managed --set-env-vars="$envVarString"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deployment successful!" -ForegroundColor Green
    Write-Host "Service URL: https://oauth-streamlit-746ljoo2pa-uc.a.run.app" -ForegroundColor Cyan
} else {
    Write-Host "Deployment failed!" -ForegroundColor Red
}