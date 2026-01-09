# ============================================================================
# Migration Script: Contact Columns + created_at_pst
# ============================================================================
# Purpose: Run database migrations on local Windows dev PC
# Date: 2025-01-08
# ============================================================================

$ErrorActionPreference = "Stop"

$ProjectRoot = "D:\Git\myhealthteam2\Dev"
$DatabasePath = "$ProjectRoot\production.db"
$MigrationScript = "$ProjectRoot\src\sql\add_appointment_contact_columns.sql"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Running Database Migration on Local Windows Dev PC" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if database exists
if (-not (Test-Path $DatabasePath)) {
    Write-Host "ERROR: Database not found at: $DatabasePath" -ForegroundColor Red
    exit 1
}

# Check if migration script exists
if (-not (Test-Path $MigrationScript)) {
    Write-Host "ERROR: Migration script not found at: $MigrationScript" -ForegroundColor Red
    exit 1
}

Write-Host "Database: $DatabasePath" -ForegroundColor Green
Write-Host "Migration: $MigrationScript" -ForegroundColor Green
Write-Host ""

# Read migration SQL
$SqlContent = Get-Content $MigrationScript -Raw

# Split into individual statements (each ALTER TABLE is a separate statement)
$Statements = $SqlContent -split '\r?\n(?=ALTER TABLE)'

Write-Host "Found $($Statements.Count) SQL statements to execute" -ForegroundColor Yellow
Write-Host ""

# Execute each statement
$SuccessCount = 0
$SkippedCount = 0
$ErrorCount = 0

foreach ($Stmt in $Statements) {
    $Stmt = $Stmt.Trim()
    if ([string]::IsNullOrWhiteSpace($Stmt) -or $Stmt.StartsWith('--')) {
        continue
    }

    # Extract first line for display
    $FirstLine = ($Stmt -split '\r?\n')[0]
    Write-Host "Executing: $FirstLine ..." -ForegroundColor Gray

    try {
        # Use sqlite3 via PowerShell
        $Result = sqlite3 $DatabasePath "$Stmt" 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK]" -ForegroundColor Green
            $SuccessCount++
        } elseif ($Result -match "duplicate column") {
            Write-Host "  [SKIPPED - Column already exists]" -ForegroundColor Yellow
            $SkippedCount++
        } else {
            Write-Host "  [ERROR] $Result" -ForegroundColor Red
            $ErrorCount++
        }
    } catch {
        Write-Host "  [ERROR] $_" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Migration Complete" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Success: $SuccessCount" -ForegroundColor Green
Write-Host "Skipped (already exists): $SkippedCount" -ForegroundColor Yellow
Write-Host "Errors: $ErrorCount" -ForegroundColor Red
Write-Host ""

# Verify new columns exist
Write-Host "Verifying new columns in onboarding_patients table..." -ForegroundColor Cyan
$CheckColumns = @(
    "appointment_contact_name",
    "appointment_contact_phone",
    "appointment_contact_email",
    "medical_contact_name",
    "medical_contact_phone",
    "medical_contact_email",
    "facility_nurse_name",
    "facility_nurse_phone",
    "facility_nurse_email"
)

$PragmaResult = sqlite3 $DatabasePath "PRAGMA table_info(onboarding_patients);"
$ExistingCols = $PragmaResult -split '\r?\n' | ForEach-Object {
    if ($_ -match '\|(\w+)\|') {
        $matches[1]
    }
}

$MissingCols = $CheckColumns | Where-Object { $_ -notin $ExistingCols }

if ($MissingCols) {
    Write-Host "WARNING: Missing columns: $($MissingCols -join ', ')" -ForegroundColor Yellow
} else {
    Write-Host "All contact columns verified in onboarding_patients table" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
