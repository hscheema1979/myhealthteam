# PowerShell script to download all Google Sheets tabs listed in the index tab's ImportRange column
param(
    [string]$spreadsheetId = "1-heDIbBHykxfwGl7U9YYIjQo7o5PbOVZL-VahyvG8_k",
    [string[]]$Months = @() # e.g. 2025_10,2025_11,2025_12 to filter specific monthly tabs
)

Write-Host "Starting dynamic CSV download process using index tab..."

# Create downloads directory in the Dev folder
$downloadsDir = "downloads"
New-Item -ItemType Directory -Force -Path $downloadsDir | Out-Null

# Download the index tab as CSV
$indexGid = 1086316693
$indexCsvPath = "$downloadsDir/index.csv"
$indexUrl = "https://docs.google.com/spreadsheets/d/$spreadsheetId/export?format=csv&gid=$indexGid"
Write-Host "Downloading index tab..."
try {
    Invoke-WebRequest -Uri $indexUrl -OutFile $indexCsvPath
    Write-Host "Index tab downloaded to $indexCsvPath"
}
catch {
    Write-Error "Failed to download index tab: $_"
    exit 1
}

# Debug: Print first few lines of the downloaded index file
if (Test-Path $indexCsvPath) {
    Write-Host "First 10 lines of index.csv:"
    Get-Content $indexCsvPath -TotalCount 10 | ForEach-Object { Write-Host $_ }
}
else {
    Write-Error "index.csv not found at $indexCsvPath after download."
    exit 1
}

# Parse the index CSV to get GIDs and names
Write-Host "Parsing index CSV for ImportRange GIDs..."
$tabList = @()
try {
    $csv = Import-Csv -Path $indexCsvPath
    Write-Host "CSV headers: $($csv | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name | Out-String)"
    foreach ($row in $csv) {
        $gid = $row.'GID ImportRange Tab (Local VALUE)'
        $tabName = $row.'Tab Name (Local)'
        if (![string]::IsNullOrWhiteSpace($gid)) {
            $tabList += [PSCustomObject]@{ GID = $gid; TabName = $tabName }
        }
    }
    if ($tabList.Count -eq 0) {
        Write-Error "No GIDs found in 'GID ImportRange Tab (Local VALUE)' column."
        exit 1
    }
    Write-Host "Found $($tabList.Count) tabs to download (before filtering)."
}
catch {
    Write-Error "Failed to parse index CSV: $_"
    exit 1
}

# Optional filter: restrict to tabs containing specified month tokens (e.g., 2025_10, 2025_11, 2025_12)
if ($Months -and $Months.Count -gt 0) {
    $monthsLower = $Months | ForEach-Object { $_.ToLower() }
    $tabList = $tabList | Where-Object {
        $nameLower = ($_.TabName.ToString().ToLower())
        $match = $false
        foreach ($m in $monthsLower) {
            if ($nameLower -like "*${m}*") { $match = $true; break }
        }
        $match
    }
    Write-Host ("Filtered tabs to months [{0}] - {1} tabs remain." -f ($Months -join ', '), $tabList.Count)
    if ($tabList.Count -eq 0) {
        Write-Warning "No tabs matched the specified Months filter. Exiting without downloads."
        exit 0
    }
}

# Download each tab as CSV
$successCount = 0
$failCount = 0
foreach ($tab in $tabList) {
    $gid = $tab.GID
    $tabName = $tab.TabName
    if ([string]::IsNullOrWhiteSpace($tabName)) {
        $tabName = "Tab_$gid"
    }
    # Clean filename: remove invalid chars
    $safeTabName = ($tabName -replace '[\\/:*?"<>|]', '_')
    $outFile = "$downloadsDir/${safeTabName}.csv"
    $url = "https://docs.google.com/spreadsheets/d/$spreadsheetId/export?format=csv&gid=$gid"
    Write-Host ("Downloading tab {0} (GID: {1})..." -f $tabName, $gid)
    try {
        Invoke-WebRequest -Uri $url -OutFile $outFile
        Write-Host "Downloaded: $outFile"
        $successCount++
    }
    catch {
        Write-Warning ("Failed to download tab '{0}' (GID: {1}): {2}" -f $tabName, $gid, $_)
        $failCount++
    }
}

Write-Host "Download complete! $successCount tabs downloaded, $failCount failed. Files saved to $downloadsDir."
exit 0