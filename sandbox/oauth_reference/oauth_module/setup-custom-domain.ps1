#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Set up custom domain for Cloud Run service
.DESCRIPTION
    This script helps you set up a custom domain for your Cloud Run service,
    including domain mapping, DNS configuration, and SSL certificate setup.
.PARAMETER Domain
    Your custom domain (e.g., oauth.yourdomain.com)
.PARAMETER ServiceName
    Cloud Run service name (default: oauth-streamlit)
.PARAMETER Region
    Cloud Run region (default: us-central1)
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Domain,
    
    [string]$ServiceName = "oauth-streamlit",
    [string]$Region = "us-central1",
    [string]$ProjectId = "pcops-470417"
)

Write-Host "=== Custom Domain Setup for Cloud Run ===" -ForegroundColor Green
Write-Host ""

# Get current service URL
$currentUrl = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Could not find Cloud Run service '$ServiceName' in region '$Region'" -ForegroundColor Red
    exit 1
}

Write-Host "Current service URL: $currentUrl" -ForegroundColor Yellow
Write-Host "Setting up custom domain: $Domain" -ForegroundColor Yellow
Write-Host ""

# Step 1: Create domain mapping
Write-Host "🔗 Step 1: Creating domain mapping..." -ForegroundColor Cyan
$mappingResult = gcloud run domain-mappings create --domain=$Domain --service=$ServiceName --region=$Region 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Domain mapping created successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Domain mapping may already exist or needs verification. Output:" -ForegroundColor Yellow
    Write-Host $mappingResult -ForegroundColor Gray
}

# Step 2: Get DNS records needed
Write-Host ""
Write-Host "🌐 Step 2: Getting DNS configuration..." -ForegroundColor Cyan
$dnsInfo = gcloud run domain-mappings describe $Domain --region=$Region --format="value(status.resourceRecords[].name,status.resourceRecords[].rrdata)" 2>$null

if ($dnsInfo) {
    Write-Host "✅ DNS records retrieved!" -ForegroundColor Green
    Write-Host ""
    Write-Host "=== DNS CONFIGURATION REQUIRED ===" -ForegroundColor Yellow
    Write-Host "Add these DNS records to your domain:" -ForegroundColor White
    Write-Host ""
    
    $records = $dnsInfo -split "`n"
    for ($i = 0; $i -lt $records.Length; $i += 2) {
        if ($i + 1 -lt $records.Length) {
            $name = $records[$i]
            $value = $records[$i + 1]
            Write-Host "Record Type: CNAME" -ForegroundColor Cyan
            Write-Host "Name: $name" -ForegroundColor White
            Write-Host "Value: $value" -ForegroundColor White
            Write-Host ""
        }
    }
} else {
    Write-Host "⚠️  Could not retrieve DNS records. You may need to verify domain ownership first." -ForegroundColor Yellow
}

# Step 3: Domain verification (if needed)
Write-Host "🔐 Step 3: Domain verification..." -ForegroundColor Cyan
Write-Host "If this is your first time using this domain with Google Cloud, you may need to verify ownership." -ForegroundColor White
Write-Host "Visit: https://console.cloud.google.com/apis/credentials/domainverification?project=$ProjectId" -ForegroundColor Blue
Write-Host ""

# Step 4: Update OAuth redirect URIs
Write-Host "🔄 Step 4: Update OAuth configuration..." -ForegroundColor Cyan
Write-Host "You'll need to update your OAuth redirect URIs to include:" -ForegroundColor White
Write-Host "  - https://$Domain/auth/callback" -ForegroundColor Yellow
Write-Host ""
Write-Host "Update these in Google Cloud Console:" -ForegroundColor White
Write-Host "  https://console.cloud.google.com/apis/credentials?project=$ProjectId" -ForegroundColor Blue
Write-Host ""

# Step 5: Update environment variables
Write-Host "⚙️  Step 5: Update environment variables..." -ForegroundColor Cyan
$envFile = ".env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile
    $newRedirectUri = "https://$Domain/auth/callback"
    
    # Update the redirect URI in .env file
    $updatedContent = $envContent | ForEach-Object {
        if ($_ -match '^GOOGLE_REDIRECT_URI=') {
            "GOOGLE_REDIRECT_URI=`"$newRedirectUri`""
        } else {
            $_
        }
    }
    
    $updatedContent | Set-Content $envFile
    Write-Host "✅ Updated .env file with new redirect URI: $newRedirectUri" -ForegroundColor Green
} else {
    Write-Host "⚠️  .env file not found. Please manually set GOOGLE_REDIRECT_URI=https://$Domain/auth/callback" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== NEXT STEPS ===" -ForegroundColor Green
Write-Host "1. 🌐 Add the DNS CNAME records shown above to your domain's DNS settings" -ForegroundColor White
Write-Host "2. 🔐 Verify domain ownership if prompted" -ForegroundColor White
Write-Host "3. 🔄 Update OAuth redirect URIs in Google Cloud Console" -ForegroundColor White
Write-Host "4. 🚀 Redeploy your application with updated environment variables" -ForegroundColor White
Write-Host "5. ⏳ Wait for DNS propagation (can take up to 48 hours)" -ForegroundColor White
Write-Host "6. 🔒 SSL certificate will be automatically provisioned by Google" -ForegroundColor White
Write-Host ""
Write-Host "=== MONITORING ===" -ForegroundColor Green
Write-Host "Check domain mapping status:" -ForegroundColor White
Write-Host "  gcloud run domain-mappings describe $Domain --region=$Region" -ForegroundColor Gray
Write-Host ""
Write-Host "Check SSL certificate status:" -ForegroundColor White
Write-Host "  gcloud run domain-mappings describe $Domain --region=$Region --format='value(status.conditions)'" -ForegroundColor Gray
Write-Host ""

Write-Host "🎉 Custom domain setup initiated for: https://$Domain" -ForegroundColor Green
Write-Host "Current service will remain accessible at: $currentUrl" -ForegroundColor Yellow