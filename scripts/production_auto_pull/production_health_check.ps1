# Production Health Check Script
# Verifies that the production deployment is healthy and functional
# Version: 1.0
# Last Updated: $(Get-Date -Format "yyyy-MM-dd")

param(
    [int]$Port = 8501,
    [int]$TimeoutSeconds = 30,
    [switch]$Verbose = $false
)

# Configuration
$RepoPath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$LogFile = Join-Path $RepoPath "logs\production_health_check.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    
    if ($Verbose) {
        Write-Host $LogEntry -ForegroundColor $(
            switch ($Level) {
                "ERROR" { "Red" }
                "WARNING" { "Yellow" }
                "SUCCESS" { "Green" }
                "INFO" { "Cyan" }
                default { "White" }
            }
        )
    }
    
    Add-Content -Path $LogFile -Value $LogEntry -ErrorAction SilentlyContinue
}

function Test-StreamlitProcess {
    try {
        $StreamlitProcesses = Get-Process -Name "streamlit" -ErrorAction SilentlyContinue
        if ($StreamlitProcesses) {
            Write-Log "Streamlit process found (PID: $($StreamlitProcesses[0].Id))" "SUCCESS"
            return $true
        } else {
            Write-Log "No Streamlit process running" "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "Error checking Streamlit process: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-PortListening {
    try {
        $Connection = Test-NetConnection -ComputerName "localhost" -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($Connection) {
            Write-Log "Port $Port is listening" "SUCCESS"
            return $true
        } else {
            Write-Log "Port $Port is not responding" "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "Error testing port $Port : $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-DatabaseConnection {
    try {
        # Check if database file exists
        $DatabasePath = Join-Path $RepoPath "production.db"
        if (Test-Path $DatabasePath) {
            Write-Log "Production database file found" "SUCCESS"
            
            # Try to connect using Python if available
            $TestScript = @"
import sqlite3
import sys
try:
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table"')
    table_count = cursor.fetchone()[0]
    conn.close()
    print(f'Database connection successful. Tables: {table_count}')
    sys.exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
"@
            
            $TempScript = Join-Path $env:TEMP "db_health_check.py"
            $TestScript | Out-File -FilePath $TempScript -Encoding UTF8
            
            $Result = python $TempScript 2>&1
            Remove-Item $TempScript -ErrorAction SilentlyContinue
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Database health check passed: $Result" "SUCCESS"
                return $true
            } else {
                Write-Log "Database health check failed: $Result" "ERROR"
                return $false
            }
        } else {
            Write-Log "Production database file not found at: $DatabasePath" "WARNING"
            return $false
        }
    }
    catch {
        Write-Log "Database health check error: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-ApplicationEndpoint {
    try {
        $Url = "http://localhost:$Port"
        Write-Log "Testing application endpoint: $Url" "INFO"
        
        # Use Invoke-WebRequest with timeout
        $Response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds -UseBasicParsing -ErrorAction Stop
        
        if ($Response.StatusCode -eq 200) {
            Write-Log "Application endpoint responding (Status: $($Response.StatusCode))" "SUCCESS"
            return $true
        } else {
            Write-Log "Application endpoint returned status: $($Response.StatusCode)" "WARNING"
            return $false
        }
    }
    catch {
        Write-Log "Application endpoint test failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-RequiredFiles {
    try {
        $RequiredFiles = @(
            "app.py",
            "src\database.py",
            "src\auth_module.py"
        )
        
        $MissingFiles = @()
        foreach ($File in $RequiredFiles) {
            $FilePath = Join-Path $RepoPath $File
            if (-not (Test-Path $FilePath)) {
                $MissingFiles += $File
            }
        }
        
        if ($MissingFiles.Count -eq 0) {
            Write-Log "All required files present" "SUCCESS"
            return $true
        } else {
            Write-Log "Missing required files: $($MissingFiles -join ', ')" "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "Required files check failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Get-SystemResources {
    try {
        # Get memory usage
        $Memory = Get-WmiObject -Class Win32_OperatingSystem
        $TotalMemory = [math]::Round($Memory.TotalVisibleMemorySize / 1MB, 2)
        $FreeMemory = [math]::Round($Memory.FreePhysicalMemory / 1MB, 2)
        $MemoryUsage = [math]::Round((($TotalMemory - $FreeMemory) / $TotalMemory) * 100, 2)
        
        # Get CPU usage
        $CPU = Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average
        $CPUUsage = [math]::Round($CPU.Average, 2)
        
        Write-Log "System Resources - Memory: $MemoryUsage% used, CPU: $CPUUsage% used" "INFO"
        
        # Check if resources are within acceptable limits
        if ($MemoryUsage -lt 90 -and $CPUUsage -lt 90) {
            Write-Log "System resources within normal limits" "SUCCESS"
            return $true
        } else {
            Write-Log "System resources may be constrained" "WARNING"
            return $false
        }
    }
    catch {
        Write-Log "System resource check failed: $($_.Exception.Message)" "WARNING"
        return $true  # Don't fail health check for this
    }
}

# Main health check function
function Invoke-ProductionHealthCheck {
    Write-Log "=== Production Health Check Started ===" "INFO"
    
    $HealthChecks = @()
    
    # Change to repository directory
    Set-Location $RepoPath
    
    # Run health checks
    $HealthChecks += @{ Name = "Streamlit Process"; Result = Test-StreamlitProcess }
    $HealthChecks += @{ Name = "Port Listening"; Result = Test-PortListening }
    $HealthChecks += @{ Name = "Database Connection"; Result = Test-DatabaseConnection }
    $HealthChecks += @{ Name = "Application Endpoint"; Result = Test-ApplicationEndpoint }
    $HealthChecks += @{ Name = "Required Files"; Result = Test-RequiredFiles }
    $HealthChecks += @{ Name = "System Resources"; Result = Get-SystemResources }
    
    # Evaluate results
    $PassedChecks = ($HealthChecks | Where-Object { $_.Result -eq $true }).Count
    $TotalChecks = $HealthChecks.Count
    $FailedChecks = $HealthChecks | Where-Object { $_.Result -eq $false }
    
    Write-Log "Health Check Summary: $PassedChecks/$TotalChecks checks passed" "INFO"
    
    if ($FailedChecks) {
        Write-Log "Failed checks:" "ERROR"
        foreach ($Check in $FailedChecks) {
            Write-Log "  - $($Check.Name)" "ERROR"
        }
    }
    
    # Determine overall health status
    $CriticalChecks = @("Streamlit Process", "Port Listening", "Required Files")
    $CriticalFailures = $FailedChecks | Where-Object { $_.Name -in $CriticalChecks }
    
    if ($CriticalFailures) {
        Write-Log "=== Production Health Check FAILED ===" "ERROR"
        Write-Log "Critical systems are not functioning properly" "ERROR"
        return $false
    } elseif ($PassedChecks -eq $TotalChecks) {
        Write-Log "=== Production Health Check PASSED ===" "SUCCESS"
        Write-Log "All systems are functioning normally" "SUCCESS"
        return $true
    } else {
        Write-Log "=== Production Health Check PASSED with WARNINGS ===" "WARNING"
        Write-Log "Core systems are functional but some issues detected" "WARNING"
        return $true
    }
}

# Execute health check
try {
    $HealthStatus = Invoke-ProductionHealthCheck
    if ($HealthStatus) {
        exit 0
    } else {
        exit 1
    }
}
catch {
    Write-Log "Unexpected error during health check: $($_.Exception.Message)" "ERROR"
    exit 1
}