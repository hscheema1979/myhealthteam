# Step 4: Post-Import Data Transformation - Complete Patient Processing
# Enhanced version that handles all patient-related foreign key relationships

param(
    [string]$DatabasePath = ".\production.db",
    [switch]$Force = $false,
    [switch]$SkipBackup = $false
)

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Step 4: Complete Post-Import Data Transformation" -ForegroundColor Cyan  
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Database: $DatabasePath" -ForegroundColor Yellow
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Check if database exists
if (-not (Test-Path $DatabasePath)) {
    Write-Host "❌ ERROR: Database not found at $DatabasePath" -ForegroundColor Red
    exit 1
}

# Create backup unless skipped
if (-not $SkipBackup) {
    $backupPath = "$DatabasePath.backup.step4.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
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

# Function to execute SQL script with error handling
function Invoke-SQLScript {
    param(
        [string]$ScriptPath,
        [string]$Description,
        [switch]$ContinueOnError = $false
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
            
            # Display result summary if available
            if ($result) {
                $resultLines = $result -split "`n" | Where-Object { $_ -and $_ -notmatch "^\s*$" }
                if ($resultLines.Count -gt 0) {
                    Write-Host "   Summary:" -ForegroundColor Cyan
                    $resultLines | ForEach-Object { 
                        if ($_ -match '\|') {
                            $parts = $_ -split '\|', 2
                            Write-Host "   • $($parts[0]): $($parts[1])" -ForegroundColor White
                        } else {
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

# Function to get table counts
function Get-TableCount {
    param([string]$TableName)
    try {
        $count = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $TableName;" 2>$null
        return [int]$count
    }
    catch {
        return 0
    }
}

Write-Host "📊 Pre-transformation Status:" -ForegroundColor Cyan
$prePatients = Get-TableCount "patients"
$preFacilities = Get-TableCount "facilities" 
$preAssignments = Get-TableCount "patient_assignments"
$preUserAssignments = Get-TableCount "user_patient_assignments"
$preCarePlans = Get-TableCount "care_plans"

Write-Host "   • Patients: $prePatients" -ForegroundColor White
Write-Host "   • Facilities: $preFacilities" -ForegroundColor White
Write-Host "   • Patient Assignments: $preAssignments" -ForegroundColor White
Write-Host "   • User-Patient Assignments: $preUserAssignments" -ForegroundColor White
Write-Host "   • Care Plans: $preCarePlans" -ForegroundColor White
Write-Host ""

# Step 1: Transform Coordinators 
$success1 = Invoke-SQLScript -ScriptPath ".\src\sql\populate_coordinator_tasks.sql" -Description "Transforming coordinator tasks"
if (-not $success1 -and -not $Force) {
    Write-Host "❌ CRITICAL: Coordinator transformation failed" -ForegroundColor Red
    exit 1
}

# Step 2: Transform Providers
$success2 = Invoke-SQLScript -ScriptPath ".\src\sql\populate_provider_tasks.sql" -Description "Transforming provider tasks" 
if (-not $success2 -and -not $Force) {
    Write-Host "❌ CRITICAL: Provider transformation failed" -ForegroundColor Red
    exit 1
}

# Step 3: Complete Patient Transformation (NEW - comprehensive)
Write-Host "🏥 Starting Complete Patient Transformation..." -ForegroundColor Magenta

$success3 = Invoke-SQLScript -ScriptPath ".\src\sql\complete_patient_transformation.sql" -Description "Complete patient data transformation with all foreign keys"
if (-not $success3 -and -not $Force) {
    Write-Host "❌ CRITICAL: Complete patient transformation failed" -ForegroundColor Red
    exit 1
}

# Step 4: Update Summary Tables
$success4 = Invoke-SQLScript -ScriptPath ".\src\sql\populate_summary_tables.sql" -Description "Updating summary tables" -ContinueOnError
$success5 = Invoke-SQLScript -ScriptPath ".\src\sql\populate_coordinator_monthly_summary.sql" -Description "Updating coordinator monthly summaries" -ContinueOnError
$success6 = Invoke-SQLScript -ScriptPath ".\src\sql\populate_provider_monthly_summary.sql" -Description "Updating provider monthly summaries" -ContinueOnError

Write-Host ""
Write-Host "📊 Post-transformation Status:" -ForegroundColor Cyan

$postPatients = Get-TableCount "patients"
$postFacilities = Get-TableCount "facilities"
$postAssignments = Get-TableCount "patient_assignments" 
$postUserAssignments = Get-TableCount "user_patient_assignments"
$postCarePlans = Get-TableCount "care_plans"
$postDashboardAssignments = Get-TableCount "dashboard_patient_assignment_summary"
$postCountyMappings = Get-TableCount "dashboard_patient_county_map"
$postZipMappings = Get-TableCount "dashboard_patient_zip_map"

Write-Host "   • Patients: $postPatients (+" + ($postPatients - $prePatients) + ")" -ForegroundColor White
Write-Host "   • Facilities: $postFacilities (+" + ($postFacilities - $preFacilities) + ")" -ForegroundColor White  
Write-Host "   • Patient Assignments: $postAssignments (+" + ($postAssignments - $preAssignments) + ")" -ForegroundColor White
Write-Host "   • User-Patient Assignments: $postUserAssignments (+" + ($postUserAssignments - $preUserAssignments) + ")" -ForegroundColor White
Write-Host "   • Care Plans: $postCarePlans (+" + ($postCarePlans - $preCarePlans) + ")" -ForegroundColor White
Write-Host "   • Dashboard Assignments: $postDashboardAssignments" -ForegroundColor White
Write-Host "   • County Mappings: $postCountyMappings" -ForegroundColor White
Write-Host "   • ZIP Code Mappings: $postZipMappings" -ForegroundColor White

Write-Host ""

# Check staff mapping effectiveness
Write-Host "👥 Staff Mapping Analysis:" -ForegroundColor Cyan
try {
    $mappingStats = sqlite3 $DatabasePath "SELECT confidence_level, COUNT(*) as count FROM staff_code_mapping GROUP BY confidence_level;" 2>$null
    if ($mappingStats) {
        $mappingStats -split "`n" | ForEach-Object {
            if ($_ -match '(.+)\|(.+)') {
                Write-Host "   • $($matches[1]) confidence: $($matches[2]) mappings" -ForegroundColor White
            }
        }
    }
    
    $unmappedCoordinators = sqlite3 $DatabasePath "SELECT COUNT(DISTINCT spd.`"Assigned CM`") FROM SOURCE_PATIENT_DATA spd WHERE spd.`"Assigned CM`" IS NOT NULL AND spd.`"Assigned CM`" != '' AND NOT EXISTS (SELECT 1 FROM staff_code_mapping scm WHERE LOWER(TRIM(spd.`"Assigned CM`")) = LOWER(TRIM(scm.staff_name)) AND scm.confidence_level = 'HIGH');" 2>$null
    if ($unmappedCoordinators) {
        Write-Host "   • Unmapped coordinators: $unmappedCoordinators" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   • Unable to analyze staff mappings" -ForegroundColor Yellow
}

Write-Host ""

# Final status check
$allSuccessful = $success1 -and $success2 -and $success3
if ($allSuccessful) {
    Write-Host "🎉 TRANSFORMATION COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "   All critical transformations completed:" -ForegroundColor Green
    Write-Host "   ✅ Coordinator tasks transformed" -ForegroundColor Green
    Write-Host "   ✅ Provider tasks transformed" -ForegroundColor Green  
    Write-Host "   ✅ Complete patient data transformation with foreign keys" -ForegroundColor Green
    Write-Host "   ✅ All patient relationships established" -ForegroundColor Green
    
    if (-not ($success4 -and $success5 -and $success6)) {
        Write-Host "   ⚠️ Some summary table updates had issues (non-critical)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "⚠️ TRANSFORMATION COMPLETED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "   Some transformations failed - check logs above" -ForegroundColor Yellow
    
    if ($Force) {
        Write-Host "   Continuing due to -Force flag" -ForegroundColor Yellow
    } else {
        Write-Host "   Use -Force flag to continue despite errors" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Review transformation results above" -ForegroundColor White
Write-Host "   2. Check unmapped staff codes if any" -ForegroundColor White
Write-Host "   3. Verify patient assignments are correct" -ForegroundColor White
Write-Host "   4. Test dashboard functionality" -ForegroundColor White
Write-Host "   5. Run application to verify all data relationships" -ForegroundColor White

Write-Host ""
Write-Host "🏁 Step 4 Complete - Enhanced Patient Processing" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Cyan