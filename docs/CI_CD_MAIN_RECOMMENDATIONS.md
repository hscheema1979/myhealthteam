# CI/CD Main Branch Recommendations for MyHealthTeam Platform

## Overview

This document outlines the Continuous Integration/Continuous Deployment (CI/CD) strategy from the **main branch and production environment perspective**. This covers production deployment workflows, release management, and maintaining the stable production environment.

## Production Environment Architecture

### Repository Structure from Main Branch Perspective
```
Production Environment: d:\Git\myhealthteam2\Streamlit\
├── main branch (production-ready code - PROTECTED)
├── Runs continuously on Port 8501
├── Only receives tested code from develop branch
└── Source of truth for live application

GitHub Repository:
├── main branch (production releases)
├── develop branch (integration from dev environment)
├── release/* branches (release preparation)
└── hotfix/* branches (emergency production fixes)
```

### Production Port Allocation
- **Port 8501**: Production Environment (d:\Git\myhealthteam2\Streamlit\) - LIVE USERS
- **Port 8502**: Staging Environment (for final testing before production)
- **Port 8503**: Development Environment (development work only)

## Production Deployment Strategy

### Repository-Based Deployment Flow

```
GitHub main branch → Production Environment (Port 8501)
     ↑                        ↓
Pull Requests from      Live Application
develop branch          (d:\Git\myhealthteam2\Streamlit\)
     ↑
Development work
(d:\Git\myhealthteam2\Dev\)
```

**Key Principle:** Production PULLS from GitHub, never receives direct pushes from development.

### Production Deployment Workflow

#### Standard Production Deployment
```powershell
# Execute from: d:\Git\myhealthteam2\Streamlit\
# Purpose: Deploy approved changes to production

# 1. Navigate to production environment
cd d:\Git\myhealthteam2\Streamlit\

# 2. Ensure we're on main branch
git checkout main
git status

# 3. Pull latest approved changes from GitHub
Write-Host "🔄 Pulling latest changes from GitHub main branch..." -ForegroundColor Cyan
git pull origin main

# 4. Verify no uncommitted changes
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "❌ Uncommitted changes detected! Aborting deployment." -ForegroundColor Red
    exit 1
}

# 5. Set production environment
$env:ENVIRONMENT = "production"
$env:PORT = "8501"

# 6. Create deployment backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Write-Host "💾 Creating deployment backup: backup_$timestamp" -ForegroundColor Yellow
git tag "backup_$timestamp"

# 7. Stop current production service
Write-Host "🛑 Stopping current production service..." -ForegroundColor Yellow
Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*8501*"} | Stop-Process -Force
Start-Sleep -Seconds 5

# 8. Start new production service
Write-Host "🚀 Starting production service on Port 8501..." -ForegroundColor Green
Start-Process -FilePath "streamlit" -ArgumentList "run", "app.py", "--server.port", "8501" -WindowStyle Hidden

# 9. Health check
Start-Sleep -Seconds 15
Write-Host "🔍 Performing health check..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 30
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Production deployment successful!" -ForegroundColor Green
        Write-Host "🌐 Application available at: http://localhost:8501" -ForegroundColor Cyan
    } else {
        throw "Health check failed with status: $($response.StatusCode)"
    }
} catch {
    Write-Host "❌ Production deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "🔄 Initiating rollback procedure..." -ForegroundColor Yellow
    # Rollback would be implemented here
}
```

#### Emergency Hotfix Deployment
```powershell
# Execute from: d:\Git\myhealthteam2\Streamlit\
# Purpose: Deploy critical fixes directly to production

# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix-$(Get-Date -Format "yyyyMMdd")

# 2. Apply critical fix (manual code changes)
Write-Host "⚠️ Apply your critical fix now, then press Enter to continue..." -ForegroundColor Red
Read-Host

# 3. Commit hotfix
git add .
git commit -m "hotfix: critical production fix"

# 4. Merge to main and deploy
git checkout main
git merge hotfix/critical-fix-$(Get-Date -Format "yyyyMMdd")
git push origin main

# 5. Deploy using standard deployment workflow
# (Run the standard deployment script above)

# 6. Merge hotfix back to develop
git checkout develop
git merge main
git push origin develop
```

## Release Management

### Release Preparation Process

#### 1. Pre-Release Checklist
- [ ] All features in develop branch tested via BrowserStack
- [ ] No critical bugs in develop branch
- [ ] Documentation updated
- [ ] Performance testing completed
- [ ] Security review completed (if applicable)

#### 2. Release Branch Creation
```powershell
# Execute from: d:\Git\myhealthteam2\Dev\ (development environment)

# Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v1.0.0

# Final testing and bug fixes in release branch
# (No new features, only bug fixes)

# When ready, merge to main
git checkout main
git merge release/v1.0.0
git tag v1.0.0
git push origin main --tags

# Merge back to develop
git checkout develop
git merge release/v1.0.0
git push origin develop
```

### Production Monitoring and Maintenance

#### Daily Production Health Check
```powershell
# Execute from: d:\Git\myhealthteam2\Streamlit\
# Purpose: Verify production environment health

Write-Host "🔍 Daily Production Health Check" -ForegroundColor Cyan

# 1. Check service status
$streamlitProcess = Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*8501*"}
if ($streamlitProcess) {
    Write-Host "✅ Streamlit service running (PID: $($streamlitProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Streamlit service not running!" -ForegroundColor Red
}

# 2. Check application response
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ Application responding (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Application not responding: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Check Git status
git status
$behind = git rev-list HEAD..origin/main --count
if ($behind -gt 0) {
    Write-Host "⚠️ Production is $behind commits behind GitHub main branch" -ForegroundColor Yellow
} else {
    Write-Host "✅ Production is up to date with GitHub main branch" -ForegroundColor Green
}

# 4. Check disk space and resources
$disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 2)
Write-Host "💾 Free disk space: $freeSpaceGB GB" -ForegroundColor Cyan
```

## Production Security and Compliance

### Security Protocols
- **Environment Isolation**: Production environment completely separate from development
- **Access Control**: Only authorized personnel can deploy to production
- **Audit Trail**: All deployments logged and tagged in Git
- **Backup Strategy**: Automatic Git tags before each deployment
- **Rollback Capability**: Quick rollback to previous stable version

### Compliance Requirements
- **Change Management**: All production changes must go through Pull Request process
- **Testing Requirements**: All code must pass BrowserStack testing before production
- **Documentation**: All releases must be documented with changelog
- **Approval Process**: Production deployments require explicit approval

## Emergency Procedures

### Production Incident Response
1. **Immediate Response**: Stop problematic service if necessary
2. **Assessment**: Determine if rollback is needed
3. **Communication**: Notify stakeholders of issue and resolution plan
4. **Resolution**: Apply hotfix or rollback to stable version
5. **Post-Incident**: Document incident and implement preventive measures

### Rollback Procedure
```powershell
# Execute from: d:\Git\myhealthteam2\Streamlit\
# Purpose: Rollback to previous stable version

# 1. List recent deployment tags
git tag --sort=-creatordate | Select-Object -First 5

# 2. Rollback to specific tag
$rollbackTag = Read-Host "Enter tag to rollback to"
git checkout $rollbackTag

# 3. Restart service
Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*8501*"} | Stop-Process -Force
Start-Sleep -Seconds 5
Start-Process -FilePath "streamlit" -ArgumentList "run", "app.py", "--server.port", "8501" -WindowStyle Hidden

# 4. Verify rollback
Start-Sleep -Seconds 15
$response = Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing
Write-Host "✅ Rollback completed. Status: $($response.StatusCode)" -ForegroundColor Green
```

## Integration with Development Environment

### Coordination with Dev Environment
- Development work happens in `d:\Git\myhealthteam2\Dev\`
- Production receives only tested, approved code via GitHub
- Clear separation of concerns and responsibilities
- Regular synchronization through Git repository

### Communication Protocols
- Development team notifies when features are ready for production
- Production team schedules deployments during maintenance windows
- All deployments communicated to stakeholders
- Post-deployment verification and sign-off required

---

**Last Updated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Document Owner:** Production Team
**Related Documents:** CI_CD_DEV_RECOMMENDATIONS.md