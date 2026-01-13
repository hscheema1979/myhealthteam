$ErrorActionPreference = "Stop"
$masterHost = 'server2'
$masterDbPath = '/opt/myhealthteam/production.db'
$tempDir = 'D:\Git\myhealthteam2\Dev\db-sync\temp'
$tempSql = Join-Path $tempDir 'remote_tables_query.sql'

Write-Host "Creating temp SQL file..."
Set-Content -Path $tempSql -Value 'SELECT name FROM sqlite_master WHERE type="table" ORDER BY name;' -NoNewline

Write-Host "Reading SQL content..."
$sqlContent = Get-Content $tempSql -Raw

Write-Host "About to run SSH..."
$tables = $sqlContent | ssh $masterHost "sqlite3 $masterDbPath" 2>&1

Write-Host "Done!"
Write-Host "Tables:"
$tables | Select-Object -First 10

# Clean up
if (Test-Path $tempSql) {
    Remove-Item $tempSql -Force
}
