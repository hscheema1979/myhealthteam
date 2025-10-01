<#
.SYNOPSIS
    Test script for database packaging and upload functionality

.DESCRIPTION
    This script tests the package_and_upload_db.ps1 script with various scenarios
    including dry runs and different configurations.

.PARAMETER TestType
    Type of test to run: 'dryrun', 'package_only', 'full_test'

.EXAMPLE
    .\test_package_and_upload.ps1 -TestType 'dryrun'
    .\test_package_and_upload.ps1 -TestType 'package_only'
#>

param(
    [ValidateSet('dryrun', 'package_only', 'full_test')]
    [string]$TestType = 'dryrun'
)

Write-Host "=== Testing Database Package and Upload Script ===" -ForegroundColor Cyan
Write-Host "Test Type: $TestType" -ForegroundColor Yellow

$ScriptPath = ".\package_and_upload_db.ps1"

switch ($TestType) {
    'dryrun' {
        Write-Host "`nRunning dry run test..." -ForegroundColor Green
        & $ScriptPath -DryRun $true -CommitMessage "Test database package (dry run)"
    }
    
    'package_only' {
        Write-Host "`nRunning package-only test (no git operations)..." -ForegroundColor Green
        $TestZip = "test_database_package_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
        & $ScriptPath -ZipFileName $TestZip -CommitMessage "Test package only" -DryRun $true
        
        if (Test-Path $TestZip) {
            Write-Host "`nPackage created successfully: $TestZip" -ForegroundColor Green
            Write-Host "Package size: $([math]::Round((Get-Item $TestZip).Length / 1MB, 2)) MB" -ForegroundColor Green
            
            # Clean up test package
            Remove-Item $TestZip -Force
            Write-Host "Test package cleaned up." -ForegroundColor Yellow
        }
    }
    
    'full_test' {
        Write-Host "`nRunning full test with actual commit and push..." -ForegroundColor Green
        Write-Host "WARNING: This will create actual commits and push to the repository!" -ForegroundColor Red
        $Response = Read-Host "Do you want to continue? (yes/no)"
        
        if ($Response -eq 'yes') {
            & $ScriptPath -CommitMessage "Test database package upload"
        } else {
            Write-Host "Full test cancelled by user." -ForegroundColor Yellow
        }
    }
}

Write-Host "`n=== Test Completed ===" -ForegroundColor Cyan