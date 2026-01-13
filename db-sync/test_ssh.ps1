# Test SSH command with table name
$ErrorActionPreference = "Continue"

$masterHost = 'server2'
$masterDbPath = '/opt/myhealthteam/production.db'
$slaveDbPath = 'D:\Git\myhealthteam2\Dev\production.db'

$table = 'audit_log'

Write-Host "Testing remote SSH command..."
Write-Host "Table: $table"
Write-Host "Command: ssh $masterHost `"sqlite3 '$masterDbPath' `\"SELECT COUNT(*) FROM $table;`\"`""

$remoteCount = ssh $masterHost "sqlite3 '$masterDbPath' \"SELECT COUNT(*) FROM $table;\"" 2>$null

Write-Host "Remote count: $remoteCount"
Write-Host "Exit code: $LASTEXITCODE"

Write-Host ""
Write-Host "Testing local SQLite command..."
$localCount = sqlite3 $slaveDbPath "SELECT COUNT(*) FROM $table;" 2>$null
Write-Host "Local count: $localCount"
Write-Host "Exit code: $LASTEXITCODE"
