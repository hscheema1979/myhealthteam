# Simple PowerShell script to consolidate CSV files
Write-Host "Starting CSV consolidation process..."

# Exclude RVZ from cmlog.csv, create separate rvz.csv
Write-Host "Combining all CMLog_*.csv files in downloads (excluding RVZ) into cmlog.csv..."
$downloadsDir = "../downloads"
$tmpCmlogDir = "$downloadsDir/tmp_cmlog"
if (Test-Path $tmpCmlogDir) { Remove-Item $tmpCmlogDir -Recurse -Force }
New-Item -ItemType Directory -Path $tmpCmlogDir | Out-Null
$cmlogFiles = Get-ChildItem -Path $downloadsDir -Filter "CMLog_*.csv" -File
if ($cmlogFiles.Count -eq 0) {
    Write-Warning "No CMLog_*.csv files found in $downloadsDir."
}
else {
    foreach ($f in $cmlogFiles) { Copy-Item $f.FullName -Destination $tmpCmlogDir }
    python "../src/utils/combine_csvs.py" $tmpCmlogDir -o "$downloadsDir/cmlog.csv" --skip-empty-columns
    Remove-Item $tmpCmlogDir -Recurse -Force
    Write-Host "Combined $($cmlogFiles.Count) files into downloads/cmlog.csv"
}

# Combine all RVZ_ZEN-*.csv files into rvz.csv (no monthly split)
Write-Host "Combining all RVZ_ZEN-*.csv files in downloads into rvz.csv..."
$tmpRvzDir = "$downloadsDir/tmp_rvz"
if (Test-Path $tmpRvzDir) { Remove-Item $tmpRvzDir -Recurse -Force }
New-Item -ItemType Directory -Path $tmpRvzDir | Out-Null
$rvzFiles = Get-ChildItem -Path $downloadsDir -Filter "RVZ_ZEN-*.csv" -File
if ($rvzFiles.Count -eq 0) {
    Write-Warning "No RVZ_ZEN-*.csv files found in $downloadsDir."
}
else {
    foreach ($f in $rvzFiles) { Copy-Item $f.FullName -Destination $tmpRvzDir }
    python "../src/utils/combine_csvs.py" $tmpRvzDir -o "$downloadsDir/rvz.csv" --skip-empty-columns
    Remove-Item $tmpRvzDir -Recurse -Force
    Write-Host "Combined $($rvzFiles.Count) files into downloads/rvz.csv"
}

# Combine all PSL_ZEN-*.csv files in downloads into psl.csv (top-level only)
Write-Host "Combining all PSL_ZEN-*.csv files in downloads (top-level only)..."
$tmpPslDir = "$downloadsDir/tmp_psl"
if (Test-Path $tmpPslDir) { Remove-Item $tmpPslDir -Recurse -Force }
New-Item -ItemType Directory -Path $tmpPslDir | Out-Null
$pslFiles = Get-ChildItem -Path $downloadsDir -Filter "PSL_ZEN-*.csv" -File
if ($pslFiles.Count -eq 0) {
    Write-Warning "No PSL_ZEN-*.csv files found in $downloadsDir."
}
else {
    foreach ($f in $pslFiles) { Copy-Item $f.FullName -Destination $tmpPslDir }
    python "../src/utils/combine_csvs.py" $tmpPslDir -o "$downloadsDir/psl.csv" --skip-empty-columns
    Remove-Item $tmpPslDir -Recurse -Force
    Write-Host "Combined $($pslFiles.Count) files into downloads/psl.csv"
}

# Clean up ZMO_Main.csv in top-level downloads
Write-Host "Cleaning patient file..."
python "../src/utils/clean_csv.py" "../downloads/ZMO_Main.csv" --max-columns 53
Write-Host "Patient file cleaned"





# Split cmlog.csv and psl.csv into monthly partitioned CSVs
$origLocation = Get-Location
Set-Location ..
Write-Host "Splitting cmlog.csv into monthly partitioned files..."
if (Test-Path "scripts/split_cmlog_by_month.py") {
  python "scripts/split_cmlog_by_month.py"
} else {
  Write-Warning "scripts/split_cmlog_by_month.py not found; skipping CM monthly split."
}
Write-Host "Splitting psl.csv into monthly partitioned files..."
if (Test-Path "scripts/split_psl_by_month.py") {
  python "scripts/split_psl_by_month.py"
} else {
  Write-Warning "scripts/split_psl_by_month.py not found; skipping PSL monthly split."
}
Set-Location $origLocation
Write-Host "Monthly partitioned CSVs created in downloads/monthly_CM and downloads/monthly_PSL (if split scripts present)."

# Append rvz.csv to psl.csv (provider data) after monthly split
if (Test-Path "$downloadsDir/rvz.csv" -and (Get-Item "$downloadsDir/rvz.csv").Length -gt 0) {
    Write-Host "Appending rvz.csv to psl.csv (provider data)..."
    Get-Content "$downloadsDir/rvz.csv" | Add-Content "$downloadsDir/psl.csv"
    Write-Host "Appended rvz.csv to psl.csv."
}

Write-Host "Consolidation complete!"
Write-Host ""
Write-Host "Files ready for import:"
Write-Host "  - downloads/cmlog.csv (coordinator data)"
Write-Host "  - downloads/psl.csv (provider data)" 
Write-Host "  - downloads/patients/ZMO_Main.csv (patient data)"