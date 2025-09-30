# populate_coordinator_monthly_partitions.ps1
# Script to populate coordinator monthly partition tables

param(
    [string]$DatabasePath = "..\update_data.db",
    [int]$StartYear = 2024,
    [int]$StartMonth = 1,
    [int]$EndYear = 2025,
    [int]$EndMonth = 12
)

# Function to check if a table has a specific column
function Test-TableHasColumn {
    param(
        [string]$DatabasePath,
        [string]$TableName,
        [string]$ColumnName
    )
    
    try {
        $result = sqlite3 $DatabasePath ".schema $TableName" | Select-String -Pattern "\b$ColumnName\b"
        return $result -ne $null
    }
    catch {
        $exceptionMessage = $_.Exception.Message
        Write-Host ("Error checking schema for {0}: {1}" -f $TableName, $exceptionMessage) -ForegroundColor Red
        return $false
    }
}

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
Write-Host "Populating coordinator monthly partition tables..." -ForegroundColor Yellow
Write-Host "Database: $DatabasePath" -ForegroundColor Yellow
Write-Host "Date range: $StartYear-$("{0:D2}" -f $StartMonth) to $EndYear-$("{0:D2}" -f $EndMonth)" -ForegroundColor Yellow

# Check if database exists
if (-not (Test-Path $DatabasePath)) {
    Write-Host "Error: Database file '$DatabasePath' not found." -ForegroundColor Red
    exit 1
}

# Check if SQL templates exist
$sqlTemplateOld = "..\src\sql\transform_coordinator_tasks_monthly.sql"
$sqlTemplateNew = "..\src\sql\transform_coordinator_tasks_monthly_new_schema.sql"

if (-not (Test-Path $sqlTemplateOld)) {
    Write-Host "Error: SQL template '$sqlTemplateOld' not found." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $sqlTemplateNew)) {
    Write-Host "Error: SQL template '$sqlTemplateNew' not found." -ForegroundColor Red
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
        $tableName = "coordinator_tasks_{0}_{1:00}" -f $year, $month
        $description = "coordinator tasks for {0}-{1:00}" -f $year, $month
        
        # Check if the table exists
        Write-Host "Debug: year=$year, month=$month, tableName=$tableName" -ForegroundColor Cyan
        try {
            $tables = sqlite3 $DatabasePath ".tables"
            $tableExists = $tables -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_.Trim() -eq $tableName }
            if (-not $tableExists) {
                Write-Host "Warning: Table $tableName does not exist. Skipping." -ForegroundColor Yellow
                $month++
                continue
            }
        }
        catch {
            $exceptionMessage = $_.Exception.Message
            Write-Host ("Error checking if table {0} exists: {1}" -f $tableName, $exceptionMessage) -ForegroundColor Red
            $month++
            continue
        }
        
        # Determine which SQL template to use based on the table schema
        $hasTaskIdColumn = Test-TableHasColumn -DatabasePath $DatabasePath -TableName $tableName -ColumnName "task_id"
        
        if ($hasTaskIdColumn) {
            $sqlTemplate = $sqlTemplateOld
            Write-Host "Using old schema template for $tableName" -ForegroundColor Cyan
        }
        else {
            $sqlTemplate = $sqlTemplateNew
            Write-Host "Using new schema template for $tableName" -ForegroundColor Cyan
        }
        
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

Write-Host "Successfully populated all coordinator monthly partition tables." -ForegroundColor Green