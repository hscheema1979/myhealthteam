# Test Auto Git Commit Script
# This script tests the auto git commit functionality

param(
    [switch]$DryRun = $false,
    [string]$TestMessage = "Test auto commit - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
)

# Configuration
$ScriptPath = Join-Path $PSScriptRoot "auto_git_commit.ps1"

function Write-Status {
    param(
        [string]$Message,
        [string]$Status = "INFO"
    )
    $StatusIcon = switch ($Status) {
        "SUCCESS" { "✅" }
        "ERROR" { "❌" }
        "WARNING" { "⚠️" }
        default { "ℹ️" }
    }
    Write-Host "$StatusIcon $Message"
}

function Test-AutoGitCommit {
    param([switch]$DryRun)
    
    Write-Status "Testing auto git commit functionality..." "INFO"
    
    # Verify script exists
    if (!(Test-Path $ScriptPath)) {
        Write-Status "Auto git commit script not found: $ScriptPath" "ERROR"
        return $false
    }
    
    # Create a test file to ensure there are changes to commit
    $TestFile = Join-Path (Split-Path -Parent $PSScriptRoot) "test_auto_commit.txt"
    
    try {
        # Create test file with timestamp
        $TestContent = @"
Auto Git Commit Test
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
This file is used to test the automated git commit functionality.
"@
        
        if ($DryRun) {
            Write-Status "DRY RUN: Would create test file: $TestFile" "WARNING"
        } else {
            Set-Content -Path $TestFile -Value $TestContent -Force
            Write-Status "Created test file: $TestFile" "SUCCESS"
        }
        
        # Run the auto commit script
        Write-Status "Running auto git commit script..." "INFO"
        
        $arguments = @{
            FilePath = "PowerShell.exe"
            ArgumentList = @(
                "-ExecutionPolicy Bypass",
                "-File `"$ScriptPath`"",
                "-CommitMessage `"$TestMessage`""
            )
            WorkingDirectory = Split-Path -Parent $ScriptPath
            Wait = $true
            PassThru = $true
            NoNewWindow = $true
        }
        
        if ($DryRun) {
            $arguments.ArgumentList += "-DryRun"
            Write-Status "DRY RUN: Would execute: $($arguments.FilePath) $($arguments.ArgumentList -join ' ')" "WARNING"
            
            # Simulate success for dry run
            Write-Status "DRY RUN: Auto git commit test completed successfully!" "SUCCESS"
            return $true
        }
        
        $process = Start-Process @arguments
        
        if ($process.ExitCode -eq 0) {
            Write-Status "Auto git commit script executed successfully!" "SUCCESS"
            
            # Clean up test file
            if (Test-Path $TestFile) {
                Remove-Item $TestFile -Force
                Write-Status "Cleaned up test file" "SUCCESS"
            }
            
            return $true
        } else {
            Write-Status "Auto git commit script failed with exit code: $($process.ExitCode)" "ERROR"
            return $false
        }
        
    } catch {
        Write-Status "Error during test: $($_.Exception.Message)" "ERROR"
        
        # Clean up test file on error
        if (Test-Path $TestFile) {
            Remove-Item $TestFile -Force -ErrorAction SilentlyContinue
        }
        
        return $false
    }
}

function Show-TestInstructions {
    Write-Status "" "INFO"
    Write-Status "Test Instructions:" "INFO"
    Write-Status "1. This test will create a temporary file and run the auto commit script" "INFO"
    Write-Status "2. Check your git repository for the new commit" "INFO"
    Write-Status "3. Verify the commit message: $TestMessage" "INFO"
    Write-Status "4. Check the log file: logs\auto_git_commit.log" "INFO"
    Write-Status "5. The test file will be automatically cleaned up" "INFO"
    Write-Status ""
    Write-Status "To run the actual scheduled task:" "INFO"
    Write-Status "1. Run: .\scripts\setup_auto_git_commit.ps1" "INFO"
    Write-Status "2. Or open Task Scheduler and run the task manually" "INFO"
    Write-Status ""
}

# Main execution
try {
    Write-Status "========================================" "INFO"
    Write-Status "Auto Git Commit Test Started" "INFO"
    Write-Status "========================================" "INFO"
    
    Show-TestInstructions
    
    # Run the test
    $success = Test-AutoGitCommit -DryRun:$DryRun
    
    if ($success) {
        Write-Status "Test completed successfully!" "SUCCESS"
        
        if (!$DryRun) {
            Write-Status "Check your git repository and remote for the new commit" "INFO"
            Write-Status "Check the log file for detailed information: logs\auto_git_commit.log" "INFO"
        }
        
        exit 0
    } else {
        Write-Status "Test failed!" "ERROR"
        exit 1
    }
    
} catch {
    Write-Status "Unexpected error: $($_.Exception.Message)" "ERROR"
    Write-Status "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    exit 1
} finally {
    Write-Status "========================================" "INFO"
    Write-Status "Auto Git Commit Test Finished" "INFO"
    Write-Status "========================================" "INFO"
}