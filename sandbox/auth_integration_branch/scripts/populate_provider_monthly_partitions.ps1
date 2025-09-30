# populate_provider_monthly_partitions.ps1
# Script to populate provider monthly partition tables

param(
    [string]$DatabasePath = "..\update_data.db",
    [int]$StartYear = 2024,
    [int]$StartMonth = 1,
    [int]$EndYear = 2025,
    [int]$EndMonth = 12
)

# Function to execute SQL script with replaced placeholders
function Invoke-SQLScriptWithPlaceholders {
    param(
        [string]$ScriptPath,
        [string]$DatabasePath,
        [int]$Year,
        [int]$Month,
        [string]$Description
    )
    
    Write-Host "Executing $Description..." -ForegroundColor Green
    
    # Read the SQL script
    $sqlContent = Get-Content $ScriptPath -Raw
    
    # Replace placeholders with actual values
    $sqlContent = $sqlContent -replace '{YYYY}', $Year
    $sqlContent = $sqlContent -replace '{MM}', ("{0:D2}" -f $Month)
    
    # Create a temporary file with the replaced content
    $tempFile = [System.IO.Path]::GetTempFileName()
    $sqlContent | Out-File -FilePath $tempFile -Encoding UTF8
    
    # Execute the SQL script
    try {
        sqlite3 $DatabasePath ".read '$tempFile'"
        Write-Host "Successfully executed $Description" -ForegroundColor Green
        return $true
    }
    catch {
        $errorMessage = "Error executing " + $Description + ": " + $_.Exception.Message
        Write-Host $errorMessage -ForegroundColor Red
        return $false
    }
    finally {
        # Clean up the temporary file
        if (Test-Path $tempFile) {
            Remove-Item $tempFile -Force
        }
    }
}

# Main execution
Write-Host "Populating provider monthly partition tables..." -ForegroundColor Yellow
Write-Host "Database: $DatabasePath" -ForegroundColor Yellow
Write-Host "Date range: $StartYear-$("{0:D2}" -f $StartMonth) to $EndYear-$("{0:D2}" -f $EndMonth)" -ForegroundColor Yellow

# Check if database exists
if (-not (Test-Path $DatabasePath)) {
    Write-Host "Error: Database file '$DatabasePath' not found." -ForegroundColor Red
    exit 1
}

# Check if SQL template exists
$sqlTemplate = "..\src\sql\transform_provider_tasks_monthly.sql"
if (-not (Test-Path $sqlTemplate)) {
    Write-Host "Error: SQL template '$sqlTemplate' not found." -ForegroundColor Red
    exit 1
}

# Loop through each month in the specified range
$year = $StartYear
while ($year -lt $EndYear -or ($year -eq $EndYear -and $StartMonth -le $EndMonth)) {
    $month = $StartMonth
    
    # For years after the start year, start from January
    if ($year -gt $StartYear) {
        $month = 1
    }
    
    # For the end year, make sure we don't go past the end month
    $endMonthForYear = 12
    if ($year -eq $EndYear) {
        $endMonthForYear = $EndMonth
    }
    
    while ($month -le $endMonthForYear) {
        $description = "provider tasks for $year-$("{0:D2}" -f $month)"
        
        # Execute the SQL script with replaced placeholders
        $success = Invoke-SQLScriptWithPlaceholders -ScriptPath $sqlTemplate -DatabasePath $DatabasePath -Year $year -Month $month -Description $description
        
        if (-not $success) {
            Write-Host "Failed to populate $description. Exiting." -ForegroundColor Red
            exit 1
        }
        
        $month++
    }
    
    $year++
    $StartMonth = 1  # Reset to January for subsequent years
}

Write-Host "Successfully populated all provider monthly partition tables." -ForegroundColor Green