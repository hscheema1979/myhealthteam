# Development Startup Script for PCOPS (Port 8503)
# Sets environment variables and starts Streamlit on development port

Write-Host "Starting PCOPS in DEVELOPMENT mode on port 8503..." -ForegroundColor Cyan

# Set environment variables for development
$env:ENVIRONMENT = "development"
$env:STREAMLIT_SERVER_PORT = "8503"

# Use default secrets.toml for development
Write-Host "Using development secrets configuration" -ForegroundColor Yellow
Write-Host "OAuth Redirect URI: http://localhost:8503/oauth/callback" -ForegroundColor Cyan

# Start Streamlit on development port
Write-Host "Starting Streamlit on http://localhost:8503" -ForegroundColor Cyan
streamlit run app.py --server.port 8503