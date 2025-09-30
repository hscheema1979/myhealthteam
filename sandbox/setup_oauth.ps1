# Quick OAuth Setup Script for PCOPS
# This script helps you set up Google OAuth credentials quickly

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "PCOPS Google OAuth Quick Setup" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Google Cloud Console Setup" -ForegroundColor Yellow
Write-Host "1. Go to: https://console.cloud.google.com/" -ForegroundColor White
Write-Host "2. Create/Select a project" -ForegroundColor White
Write-Host "3. Enable Google+ API (APIs & Services > Library > Google+ API)" -ForegroundColor White
Write-Host "4. Go to APIs & Services > Credentials" -ForegroundColor White
Write-Host "5. Click 'Create Credentials' > 'OAuth 2.0 Client IDs'" -ForegroundColor White
Write-Host "6. Choose 'Web application'" -ForegroundColor White
Write-Host ""

Write-Host "Step 2: Add these Redirect URIs:" -ForegroundColor Yellow
Write-Host "   http://localhost:8501/oauth/callback  (Production)" -ForegroundColor Green
Write-Host "   http://localhost:8502/oauth/callback  (Sandbox)" -ForegroundColor Green
Write-Host "   http://localhost:8503/oauth/callback  (Development)" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Enter your credentials below:" -ForegroundColor Yellow
Write-Host ""

# Get credentials from user
$clientId = Read-Host "Enter your Google Client ID"
$clientSecret = Read-Host "Enter your Google Client Secret" -AsSecureString
$clientSecretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($clientSecret))

Write-Host ""
Write-Host "Updating configuration files..." -ForegroundColor Yellow

# Update development secrets
$devSecretsPath = ".\.streamlit\secrets.toml"
$devContent = @"
# Development OAuth Configuration for PCOPS Application (Port 8503)
[google]
client_id = "$clientId"
client_secret = "$clientSecretPlain"
redirect_uri = "http://localhost:8503"

# Database Configuration
[database]
path = "development.db"  # Use separate database for development

# Application Configuration
[app]
secret_key = "dev-secret-key-$(Get-Random)"
session_timeout = 7200  # Longer timeout for development
require_email_verification = false  # Relaxed for development
allowed_domains = ""  # Allow any domain for development

# Environment
[environment]
name = "development"
"@

$devContent | Out-File -FilePath $devSecretsPath -Encoding UTF8
Write-Host "✓ Updated $devSecretsPath" -ForegroundColor Green

# Update sandbox secrets
$sandboxSecretsPath = ".\.streamlit\secrets.sandbox.toml"
$sandboxContent = @"
# Sandbox/Testing OAuth Configuration for PCOPS Application (Port 8502)
[google]
client_id = "$clientId"
client_secret = "$clientSecretPlain"
redirect_uri = "http://localhost:8502"

# Database Configuration
[database]
path = "sandbox.db"  # Use separate database for testing

# Application Configuration
[app]
secret_key = "sandbox-secret-key-$(Get-Random)"
session_timeout = 7200  # Longer timeout for testing
require_email_verification = false  # Relaxed for testing
allowed_domains = ""  # Allow any domain for testing

# Environment
[environment]
name = "sandbox"
"@

$sandboxContent | Out-File -FilePath $sandboxSecretsPath -Encoding UTF8
Write-Host "✓ Updated $sandboxSecretsPath" -ForegroundColor Green

# Update production secrets
$prodSecretsPath = ".\.streamlit\secrets.prod.toml"
$prodContent = @"
# Production OAuth Configuration for PCOPS Application (Port 8501)
[google]
client_id = "$clientId"
client_secret = "$clientSecretPlain"
redirect_uri = "http://localhost:8501"

# Database Configuration
[database]
path = "production.db"

# Application Configuration
[app]
secret_key = "prod-secret-key-$(Get-Random)"
session_timeout = 3600  # 1 hour for production
require_email_verification = true
allowed_domains = "yourdomain.com"  # Restrict to your domain

# Environment
[environment]
name = "production"
"@

$prodContent | Out-File -FilePath $prodSecretsPath -Encoding UTF8
Write-Host "✓ Updated $prodSecretsPath" -ForegroundColor Green

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "OAuth Setup Complete!" -ForegroundColor Green
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart your Streamlit application" -ForegroundColor White
Write-Host "2. Test OAuth login on your chosen port" -ForegroundColor White
Write-Host "3. Development: .\run_development.ps1 (Port 8503)" -ForegroundColor White
Write-Host "4. Sandbox: .\run_sandbox.ps1 (Port 8502)" -ForegroundColor White
Write-Host "5. Production: .\run_production.ps1 (Port 8501)" -ForegroundColor White
Write-Host ""