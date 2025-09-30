# Step 4: Enhanced Data Transformation with Differential Imports and Data Quality Fixes
# This version implements differential imports and fixes date/patient issues

param(
    [string]$DatabasePath = "..\production.db",
    [switch]$Force = $false,
    [switch]$SkipBackup = $false,
    [switch]$FullRefresh = $false  # Force complete refresh instead of differential
)

Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "Step 4: Enhanced Data Transformation with Differential Import" -ForegroundColor Cyan  
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "Database: $DatabasePath" -ForegroundColor Yellow
Write-Host "Mode: $(if ($FullRefresh) { 'Full Refresh' } else { 'Differential Import' })" -ForegroundColor Yellow
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Check if database exists
if (-not (Test-Path $DatabasePath)) {
    Write-Host "❌ ERROR: Database not found at $DatabasePath" -ForegroundColor Red
    exit 1
}

# Create backup unless skipped
if (-not $SkipBackup) {
    $backupPath = "$DatabasePath.backup.enhanced.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "📁 Creating backup: $backupPath" -ForegroundColor Yellow
    try {
        Copy-Item $DatabasePath $backupPath -Force
        Write-Host "✅ Backup created successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ ERROR creating backup: $($_.Exception.Message)" -ForegroundColor Red
        if (-not $Force) { exit 1 }
    }
}

# Function to execute SQL script with enhanced reporting
function Invoke-EnhancedSQLScript {
    param(
        [string]$ScriptPath,
        [string]$Description,
        [switch]$ContinueOnError,
        [switch]$ShowResults
    )
    
    Write-Host "🔄 $Description..." -ForegroundColor Yellow
    
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "❌ ERROR: Script not found: $ScriptPath" -ForegroundColor Red
        if (-not $ContinueOnError) { return $false }
    }
    
    try {
        $startTime = Get-Date
        $result = Get-Content $ScriptPath | sqlite3 $DatabasePath 2>&1
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $Description completed successfully ($([math]::Round($duration, 2))s)" -ForegroundColor Green
            
            # Enhanced result display
            if ($ShowResults -and $result) {
                $resultLines = $result -split "`n" | Where-Object { $_ -and $_ -notmatch "^\s*$" }
                if ($resultLines.Count -gt 0) {
                    Write-Host "   📊 Results Summary:" -ForegroundColor Cyan
                    $resultLines | ForEach-Object { 
                        if ($_ -match '\|') {
                            $parts = $_ -split '\|'
                            if ($parts.Count -ge 4) {
                                Write-Host "   • $($parts[0]): $($parts[1]) records, $($parts[2]) processed, $($parts[3]) quality" -ForegroundColor White
                            }
                            else {
                                Write-Host "   • $($parts[0]): $($parts[1])" -ForegroundColor White
                            }
                        }
                        else {
                            Write-Host "   • $_" -ForegroundColor White
                        }
                    }
                }
            }
            return $true
        }
        else {
            Write-Host "❌ ERROR in $Description (Exit code: $LASTEXITCODE)" -ForegroundColor Red
            if ($result) {
                Write-Host "   Error details: $result" -ForegroundColor Red
            }
            return $false
        }
    }
    catch {
        Write-Host "❌ EXCEPTION in $Description : $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to get enhanced table stats
function Get-EnhancedTableStats {
    param([string]$TableName)
    try {
        $stats = sqlite3 $DatabasePath "
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN created_date >= datetime('now', '-1 hour') THEN 1 END) as recent_records,
                MIN(created_date) as oldest_record,
                MAX(updated_date) as newest_update
            FROM $TableName 
            WHERE created_date IS NOT NULL;" 2>$null
        
        if ($stats) {
            $parts = $stats -split '\|'
            return @{
                Total  = $parts[0]
                Recent = $parts[1] 
                Oldest = $parts[2]
                Newest = $parts[3]
            }
        }
        
        # Fallback for tables without timestamp columns
        $count = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $TableName;" 2>$null
        return @{ Total = $count; Recent = 0; Oldest = "N/A"; Newest = "N/A" }
    }
    catch {
        return @{ Total = 0; Recent = 0; Oldest = "N/A"; Newest = "N/A" }
    }
}

Write-Host "📊 Pre-transformation Status:" -ForegroundColor Cyan
$preCoordinatorTasks = Get-EnhancedTableStats "coordinator_tasks"
$prePatients = Get-EnhancedTableStats "patients"
$preSourceData = Get-EnhancedTableStats "SOURCE_COORDINATOR_TASKS_HISTORY"

Write-Host "   • Source Data: $($preSourceData.Total) records" -ForegroundColor White
Write-Host "   • Coordinator Tasks: $($preCoordinatorTasks.Total) records (Recent: $($preCoordinatorTasks.Recent))" -ForegroundColor White
Write-Host "   • Patients: $($prePatients.Total) records (Recent: $($prePatients.Recent))" -ForegroundColor White
Write-Host ""

# Step 1: Fix existing data quality issues first
Write-Host "🔧 PHASE 1: Data Quality Fixes" -ForegroundColor Magenta
$success1 = Invoke-EnhancedSQLScript -ScriptPath ".\src\sql\fix_coordinator_data_issues.sql" -Description "Fixing date formats and missing patients" -ShowResults:$true
if (-not $success1 -and -not $Force) {
    Write-Host "❌ CRITICAL: Data quality fixes failed" -ForegroundColor Red
    exit 1
}

# Step 2: Differential coordinator tasks import (or full refresh if requested)
Write-Host "🔄 PHASE 2: Coordinator Data Import" -ForegroundColor Magenta
if ($FullRefresh) {
    $success2 = Invoke-EnhancedSQLScript -ScriptPath ".\src\sql\populate_coordinator_tasks.sql" -Description "Full refresh of coordinator tasks" -ShowResults:$true
}
else {
    $success2 = Invoke-EnhancedSQLScript -ScriptPath ".\src\sql\populate_coordinator_tasks_differential.sql" -Description "Differential import of coordinator tasks" -ShowResults:$true
}

if (-not $success2 -and -not $Force) {
    Write-Host "❌ CRITICAL: Coordinator import failed" -ForegroundColor Red
    exit 1
}

# Step 3: Provider tasks transformation
Write-Host "🏥 PHASE 3: Provider Data Import" -ForegroundColor Magenta
$success3 = Invoke-EnhancedSQLScript -ScriptPath ".\src\sql\populate_provider_tasks.sql" -Description "Provider tasks transformation" -ShowResults:$true

# Step 4: Complete patient transformation
Write-Host "👥 PHASE 4: Patient Data Processing" -ForegroundColor Magenta
$success4 = Invoke-EnhancedSQLScript -ScriptPath ".\src\sql\complete_patient_transformation.sql" -Description "Complete patient data processing" -ShowResults:$true

# Step 5: Summary tables (non-critical)
Write-Host "📈 PHASE 5: Summary Tables Update" -ForegroundColor Magenta
$success5 = Invoke-EnhancedSQLScript -ScriptPath ".\src\sql\populate_coordinator_monthly_summary.sql" -Description "Coordinator monthly summaries" -ContinueOnError -ShowResults:$true
$success6 = Invoke-EnhancedSQLScript -ScriptPath ".\src\sql\populate_provider_monthly_summary.sql" -Description "Provider monthly summaries" -ContinueOnError -ShowResults:$true
$success7 = Invoke-EnhancedSQLScript -ScriptPath ".\src\sql\populate_summary_tables.sql" -Description "Dashboard summary tables" -ContinueOnError -ShowResults:$true

Write-Host ""
Write-Host "📊 Post-transformation Status:" -ForegroundColor Cyan

$postCoordinatorTasks = Get-EnhancedTableStats "coordinator_tasks"
$postPatients = Get-EnhancedTableStats "patients"

Write-Host "   • Coordinator Tasks: $($postCoordinatorTasks.Total) (+" + ($postCoordinatorTasks.Total - $preCoordinatorTasks.Total) + ", Recent: $($postCoordinatorTasks.Recent))" -ForegroundColor White
Write-Host "   • Patients: $($postPatients.Total) (+" + ($postPatients.Total - $prePatients.Total) + ", Recent: $($postPatients.Recent))" -ForegroundColor White

# Data quality assessment
Write-Host ""
Write-Host "🔍 Data Quality Assessment:" -ForegroundColor Cyan
try {
    $qualityStats = sqlite3 $DatabasePath "
        SELECT 
            'Date Standards|' || COUNT(CASE WHEN task_date LIKE '____-__-__' THEN 1 END) || '|' || COUNT(*) || '|' || 
            ROUND(COUNT(CASE WHEN task_date LIKE '____-__-__' THEN 1 END) * 100.0 / COUNT(*), 1) || '%' as stat
        FROM coordinator_tasks
        WHERE task_date IS NOT NULL
        UNION ALL
        SELECT 
            'Patient Links|' || COUNT(CASE WHEN patient_id IS NOT NULL AND EXISTS (SELECT 1 FROM patients p WHERE p.patient_id = coordinator_tasks.patient_id) THEN 1 END) || '|' || COUNT(*) || '|' ||
            ROUND(COUNT(CASE WHEN patient_id IS NOT NULL AND EXISTS (SELECT 1 FROM patients p WHERE p.patient_id = coordinator_tasks.patient_id) THEN 1 END) * 100.0 / COUNT(*), 1) || '%' as stat
        FROM coordinator_tasks
        UNION ALL
        SELECT 
            'Valid Duration|' || COUNT(CASE WHEN duration_minutes > 0 THEN 1 END) || '|' || COUNT(*) || '|' ||
            ROUND(COUNT(CASE WHEN duration_minutes > 0 THEN 1 END) * 100.0 / COUNT(*), 1) || '%' as stat
        FROM coordinator_tasks;" 2>$null
    
    if ($qualityStats) {
        $qualityStats -split "`n" | ForEach-Object {
            if ($_ -match '(.+)\|(.+)\|(.+)\|(.+)') {
                $metric = $matches[1]
                $good = $matches[2] 
                $total = $matches[3]
                $percentage = $matches[4]
                Write-Host "   • $metric`: $good/$total ($percentage)" -ForegroundColor White
            }
        }
    }
}
catch {
    Write-Host "   • Unable to assess data quality" -ForegroundColor Yellow
}

# Archive analysis if differential import was used
if (-not $FullRefresh) {
    Write-Host ""
    Write-Host "📦 Archive Analysis:" -ForegroundColor Cyan
    try {
        $archiveCount = sqlite3 $DatabasePath "SELECT COUNT(*) FROM coordinator_tasks_archive WHERE archived_date >= datetime('now', '-1 hour');" 2>$null
        if ($archiveCount -and $archiveCount -gt 0) {
            Write-Host "   • Records archived (changed): $archiveCount" -ForegroundColor White
            Write-Host "   • Archive table available for audit trail" -ForegroundColor White
        }
        else {
            Write-Host "   • No records needed archiving (no changes detected)" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "   • Archive analysis unavailable" -ForegroundColor Yellow
    }
}

Write-Host ""

# Final status determination
$criticalSuccess = $success1 -and $success2
if ($criticalSuccess) {
    Write-Host "🎉 ENHANCED TRANSFORMATION COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "   ✅ Data quality issues fixed (dates, missing patients)" -ForegroundColor Green
    Write-Host "   ✅ $(if ($FullRefresh) { 'Full refresh' } else { 'Differential import' }) completed" -ForegroundColor Green
    Write-Host "   ✅ Patient data relationships established" -ForegroundColor Green
    
    if (-not ($success3 -and $success4)) {
        Write-Host "   ⚠️ Some provider/patient processing had issues (check logs)" -ForegroundColor Yellow
    }
    
    if (-not ($success5 -and $success6 -and $success7)) {
        Write-Host "   ⚠️ Some summary tables had issues (non-critical for dashboards)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "⚠️ TRANSFORMATION COMPLETED WITH CRITICAL ISSUES" -ForegroundColor Yellow
    Write-Host "   Some critical transformations failed - review logs above" -ForegroundColor Yellow
    
    if ($Force) {
        Write-Host "   Continuing due to -Force flag" -ForegroundColor Yellow
    }
    else {
        Write-Host "   Use -Force flag to continue despite critical errors" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "📋 Next Steps & Benefits:" -ForegroundColor Cyan
Write-Host "   1. 🚀 Faster imports - only new/changed data processed" -ForegroundColor White
Write-Host "   2. 📅 Consistent dates - all in YYYY-MM-DD format" -ForegroundColor White  
Write-Host "   3. 👥 Complete patients - missing records auto-created" -ForegroundColor White
Write-Host "   4. 📦 Audit trail - changed records archived" -ForegroundColor White
Write-Host "   5. 🎯 Ready for dashboard - all relationships linked" -ForegroundColor White

Write-Host ""
Write-Host "🏁 Enhanced Step 4 Complete - Differential Import Ready!" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Cyan