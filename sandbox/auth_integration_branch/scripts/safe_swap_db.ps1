param(
    [string]$ProductionDbPath = "production.db",
    [string]$UpdateDbPath = "update_data.db",
    [string]$TransformScript = ".\scripts\4_transform_data_enhanced.ps1",
    [string]$ValidationSql = ".\scripts\validation_checks.sql",
    [switch]$AutoSwap
)

Write-Host "Safe DB update helper"

if (-not (Test-Path $ProductionDbPath)) {
    Write-Error "Production DB not found at $ProductionDbPath"
    exit 1
}

if (-not (Test-Path $UpdateDbPath)) {
    Write-Error "Update DB not found at $UpdateDbPath. Create it first with: sqlite3 $ProductionDbPath \".backup '$UpdateDbPath'\""
    exit 1
}

Write-Host "Running transforms against $UpdateDbPath using $TransformScript"
if (Test-Path $TransformScript) {
    & $TransformScript -DatabasePath $UpdateDbPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Transform script exited with code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}
else {
    Write-Warning "Transform script not found: $TransformScript. Skipping transform run."
}

if (Test-Path $ValidationSql) {
    Write-Host "Running validation SQL against $UpdateDbPath"
    sqlite3 $UpdateDbPath ".read $ValidationSql"
    $valExit = $LASTEXITCODE
    if ($valExit -ne 0) {
        Write-Error "Validation script returned non-zero exit ($valExit). Fix issues before swapping."
        exit $valExit
    }
}
else {
    Write-Warning "Validation SQL not found: $ValidationSql. Skipping validation."
}

if (-not $AutoSwap) {
    $confirm = Read-Host "Ready to swap $UpdateDbPath -> $ProductionDbPath? Type 'YES' to proceed"
    if ($confirm -ne 'YES') {
        Write-Host "Aborting swap. No changes made."
        exit 0
    }
}

Write-Host "Performing atomic swap. Backing up current production DB to production.db.preupdate"
Rename-Item -Path $ProductionDbPath -NewName "$($ProductionDbPath).preupdate" -Force
Rename-Item -Path $UpdateDbPath -NewName $ProductionDbPath -Force

Write-Host "Swap complete. Please start the application and run smoke tests. Keep production.db.preupdate until sign-off."
