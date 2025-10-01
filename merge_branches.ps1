# Branch Management Script
# This script helps manage merging between different branch directories

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("auth-integration", "production", "main")]
    [string]$SourceBranch,
    
    [Parameter(Mandatory=$true)]
    [ValidateSet("auth-integration", "production", "main")]
    [string]$TargetBranch
)

Write-Host "=== Branch Merge Helper ===" -ForegroundColor Green

# Define paths
$MainPath = "."
$AuthPath = "sandbox\auth_integration_branch"
$ProdPath = "sandbox\production_branch"

# Map branch names to paths
$BranchPaths = @{
    "main" = $MainPath
    "auth-integration" = $AuthPath
    "production" = $ProdPath
}

$SourcePath = $BranchPaths[$SourceBranch]
$TargetPath = $BranchPaths[$TargetBranch]

Write-Host "Source: $SourceBranch ($SourcePath)" -ForegroundColor Yellow
Write-Host "Target: $TargetBranch ($TargetPath)" -ForegroundColor Yellow

# Step 1: Copy files from source to target
Write-Host "`nStep 1: Copying files..." -ForegroundColor Cyan
if ($SourceBranch -eq "main") {
    # Copy from main to branch directory
    robocopy $SourcePath $TargetPath /E /XD .git sandbox .benchmarks /XF *.db *.log
} else {
    # Copy from branch directory to main or another branch
    robocopy $SourcePath $TargetPath /E /XF *.db *.log
}

# Step 2: Git operations
Write-Host "`nStep 2: Git operations..." -ForegroundColor Cyan

# Switch to appropriate branch
switch ($TargetBranch) {
    "main" { 
        git checkout main
        Write-Host "Switched to main branch" -ForegroundColor Green
    }
    "auth-integration" { 
        git checkout feature/auth-integration
        Write-Host "Switched to auth-integration branch" -ForegroundColor Green
    }
    "production" { 
        git checkout main  # or your production branch name
        Write-Host "Switched to production branch" -ForegroundColor Green
    }
}

# Step 3: Add and commit changes
Write-Host "`nStep 3: Staging changes..." -ForegroundColor Cyan
git add .

Write-Host "`nStep 4: Review changes before commit..." -ForegroundColor Cyan
git status

Write-Host "`nReady to commit. Run: git commit -m 'Merge $SourceBranch to $TargetBranch'" -ForegroundColor Green
Write-Host "Then run: git push origin <branch-name>" -ForegroundColor Green