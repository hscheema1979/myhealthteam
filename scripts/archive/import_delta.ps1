param(
    [string]$Date = "",
    [string]$RangeStart = "",
    [string]$RangeEnd = "",
    [switch]$SinceLast = $true,
    [string]$ProdDb = "..\production.db",
    [string]$StagingDb = ".\sheets_data.db"
)

function Get-MinWatermark {
    sqlite3 $ProdDb "CREATE TABLE IF NOT EXISTS etl_watermarks (source_name TEXT PRIMARY KEY, last_import_date TEXT);" 2>$null
    sqlite3 $ProdDb "INSERT OR IGNORE INTO etl_watermarks(source_name,last_import_date) VALUES ('patients','2025-09-26'),('provider_tasks','2025-09-26'),('coordinator_tasks','2025-09-26');" 2>$null
    $wm = sqlite3 $ProdDb "SELECT MIN(last_import_date) FROM etl_watermarks;" 2>$null
    return $wm.Trim()
}

function To-StartDate($s) {
    $d = [DateTime]::Parse($s)
    return $d.AddDays(1).ToString('yyyy-MM-dd')
}

function Get-StartDate {
    if ($Date) { return ([DateTime]::Parse($Date)).ToString('yyyy-MM-dd') }
    if ($RangeStart) { return ([DateTime]::Parse($RangeStart)).ToString('yyyy-MM-dd') }
    if ($SinceLast) { return (To-StartDate (Get-MinWatermark)) }
    return (To-StartDate '2025-09-26')
}

function Update-Watermark {
    $maxProv = sqlite3 $StagingDb "SELECT IFNULL(MAX(activity_date),'1900-01-01') FROM staging_provider_tasks;" 2>$null
    $maxCoord = sqlite3 $StagingDb "SELECT IFNULL(MAX(activity_date),'1900-01-01') FROM staging_coordinator_tasks;" 2>$null
    $dp = [DateTime]::Parse($maxProv.Trim())
    $dc = [DateTime]::Parse($maxCoord.Trim())
    $maxDate = ($dp,$dc | Measure-Object -Maximum).Maximum.ToString('yyyy-MM-dd')
    sqlite3 $ProdDb "UPDATE etl_watermarks SET last_import_date='$maxDate' WHERE source_name IN ('provider_tasks','coordinator_tasks','patients');" 2>$null
}

$startDate = Get-StartDate
Write-Host ("Import delta starting at {0}" -f $startDate)

powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\3_import_to_database.ps1" -StartDate $startDate
powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\4a-transform.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\4b-transform.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\4c-transform.ps1"

Update-Watermark

python "$PSScriptRoot\verify_normalization_linkage.py" --quick

sqlite3 $StagingDb ".read $PSScriptRoot\define_sheets_normalized_views.sql" 2>$null
sqlite3 $ProdDb ".read $PSScriptRoot\compare_production_vs_sheets_using_views.sql" 2>$null
sqlite3 $ProdDb ".read $PSScriptRoot\validate_curated_staff_ids.sql" 2>$null

Write-Host "Delta import complete"