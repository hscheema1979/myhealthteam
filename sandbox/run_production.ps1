# Production Startup Script for PCOPS (Port 8501)
# Sets environment variables and starts Streamlit on production port

Write-Host "Starting PCOPS in PRODUCTION mode on port 8501..." -ForegroundColor Green

# Set environment variables for production
$env:ENVIRONMENT = "production"
$env:STREAMLIT_SERVER_PORT = "8501"

# Copy production secrets if they exist
if (Test-Path ".streamlit\secrets.prod.toml") {
    Copy-Item ".streamlit\secrets.prod.toml" ".streamlit\secrets.toml" -Force
    Write-Host "Using production secrets configuration" -ForegroundColor Yellow
}

# Start Streamlit on production port
Write-Host "Starting Streamlit on http://localhost:8501" -ForegroundColor Cyan
streamlit run app.py --server.port 8501 --server.headless true