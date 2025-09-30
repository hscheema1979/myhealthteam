# Simple Test of Differential Import
# Test the differential coordinator tasks import functionality

param(
    [string]$DatabasePath = "..\production.db"
)

Write-Host "Testing differential import functionality..." -ForegroundColor Cyan
Write-Host "Database: $DatabasePath" -ForegroundColor Yellow

# Check if database exists
if (-not (Test-Path $DatabasePath)) {
    Write-Host "ERROR: Database not found at $DatabasePath" -ForegroundColor Red
    exit 1
}

# Test the differential import SQL script
Write-Host "Running differential import test..." -ForegroundColor Yellow

try {
    $startTime = Get-Date
    $result = Get-Content "..\src\sql\populate_coordinator_tasks_differential.sql" | sqlite3 $DatabasePath
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Differential import completed successfully ($([math]::Round($duration, 2))s)" -ForegroundColor Green
        
        # Show results if any
        if ($result) {
            Write-Host "Results:" -ForegroundColor Cyan
            $result -split "`n" | ForEach-Object { 
                if ($_ -and $_ -notmatch "^\s*$") {
                    Write-Host "  $_" -ForegroundColor White
                }
            }
        }
    }
    else {
        Write-Host "ERROR: Differential import failed (Exit code: $LASTEXITCODE)" -ForegroundColor Red
        if ($result) {
            Write-Host "Error details: $result" -ForegroundColor Red
        }
    }
}
catch {
    Write-Host "EXCEPTION: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Test complete." -ForegroundColor Green