# Automated Git Commit with Database Packaging System

This enhanced system combines automated hourly Git commits with intelligent database packaging, ensuring your database files are regularly backed up and uploaded to your repository as part of the automated workflow.

## 🚀 Features

### Core Functionality
- **Automated Hourly Commits**: Regular commits of all code changes
- **Intelligent Database Packaging**: Automatically packages database files as zip archives
- **Configurable Intervals**: Database packaging every 6 hours (configurable)
- **Backup Integration**: Includes backup files in packages
- **Comprehensive Logging**: Detailed logs for all operations
- **Error Handling**: Robust retry mechanisms and error recovery
- **Dry Run Support**: Test functionality without making changes

### Enhanced Features
- **Smart Scheduling**: Database packaging doesn't interfere with regular commits
- **Package Management**: Automatic cleanup and organization
- **Size Monitoring**: Tracks package sizes and warns of large files
- **Timestamp Tracking**: Prevents redundant packaging
- **Flexible Configuration**: Customize database names, intervals, and inclusion rules

## 📁 Files Created

### Main Scripts
- `auto_git_commit_with_db.ps1` - Enhanced auto-commit script with DB packaging
- `setup_auto_git_commit_with_db.ps1` - Task Scheduler configuration
- `package_and_upload_db.ps1` - Standalone database packaging utility
- `test_package_and_upload.ps1` - Testing utility for packaging functionality

### Documentation
- `AUTO_GIT_COMMIT_WITH_DB_README.md` - This comprehensive guide

## 🛠️ Quick Start

### 1. Initial Setup

```powershell
# Navigate to scripts directory
cd D:\Git\myhealthteam2\Streamlit\scripts

# Run the setup script as Administrator
.\setup_auto_git_commit_with_db.ps1 -Action create
```

### 2. Configuration Options

```powershell
# Create task with custom database name
.\setup_auto_git_commit_with_db.ps1 -Action create -DatabaseName "staging.db"

# Disable database packaging (commits only)
.\setup_auto_git_commit_with_db.ps1 -Action create -IncludeDatabase $false

# Custom interval (every 2 hours)
.\setup_auto_git_commit_with_db.ps1 -Action create -IntervalHours 2
```

### 3. Verification

```powershell
# Check task status
.\setup_auto_git_commit_with_db.ps1 -Action status

# Test packaging functionality
.\test_package_and_upload.ps1 -TestType 'dryrun'
```

## ⚙️ Configuration

### Database Packaging Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `IncludeDatabase` | `$true` | Enable/disable database packaging |
| `DatabaseName` | `"production.db"` | Main database file to package |
| `IncludeBackups` | `$true` | Include backup files in packages |
| `DatabasePackageInterval` | `6` | Hours between database packages |

### Scheduling Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `IntervalHours` | `1` | Hours between commits |
| `Branch` | `"main"` | Git branch for commits |
| `MaxRetries` | `3` | Retry attempts for failed operations |
| `RetryDelay` | `30` | Seconds between retries |

## 📊 Monitoring and Logs

### Log Files
- **Main Log**: `logs\auto_git_commit_with_db.log`
- **Package Timestamps**: `logs\last_db_package_timestamp.txt`
- **Individual Package Logs**: Created with each package

### Monitoring Commands
```powershell
# View recent log entries
Get-Content logs\auto_git_commit_with_db.log -Tail 20

# Check task scheduler status
Get-ScheduledTask -TaskName "MyHealthTeam Auto Git Commit with DB"

# View task history
Get-ScheduledTaskInfo -TaskName "MyHealthTeam Auto Git Commit with DB"
```

## 🔧 Manual Operations

### Standalone Database Packaging
```powershell
# Package database manually
.\package_and_upload_db.ps1

# Package with custom settings
.\package_and_upload_db.ps1 -DatabaseName "staging.db" -IncludeBackups $false

# Dry run test
.\package_and_upload_db.ps1 -DryRun $true
```

### Testing Scenarios
```powershell
# Test dry run
.\test_package_and_upload.ps1 -TestType 'dryrun'

# Test packaging only
.\test_package_and_upload.ps1 -TestType 'package_only'

# Full test with actual commit
.\test_package_and_upload.ps1 -TestType 'full_test'
```

## 📦 Package Structure

Generated packages include:
```
database_package_YYYYMMDD_HHmmss.zip
├── production.db              # Main database file
├── backups\                   # Backup files (if enabled)
│   ├── production.db.backup.enhanced.20250925_001734
│   ├── production.db.backup.enhanced.20250925_001736
│   └── ...
└── package_info.txt           # Package metadata
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Task Not Running
```powershell
# Check task status
.\setup_auto_git_commit_with_db.ps1 -Action status

# Re-create task
.\setup_auto_git_commit_with_db.ps1 -Action remove
.\setup_auto_git_commit_with_db.ps1 -Action create
```

#### 2. Database Packaging Fails
```powershell
# Test packaging manually
.\package_and_upload_db.ps1 -DryRun $true

# Check database file exists
Test-Path "production.db"

# Verify git configuration
git status
```

#### 3. Large Repository Issues
```powershell
# Check package size
Get-ChildItem "database_package_*.zip" | Select-Object Name, @{Name="Size(MB)";Expression={[math]::Round($_.Length/1MB,2)}}

# Consider excluding backups
.\package_and_upload_db.ps1 -IncludeBackups $false
```

### Log Analysis
```powershell
# Check for errors
Select-String -Path "logs\auto_git_commit_with_db.log" -Pattern "ERROR" -Tail 10

# Check package creation
Select-String -Path "logs\auto_git_commit_with_db.log" -Pattern "Package created" -Tail 5

# Monitor file sizes
Select-String -Path "logs\auto_git_commit_with_db.log" -Pattern "Size:" -Tail 5
```

## 🔒 Security Considerations

### Best Practices
1. **Repository Size**: Monitor repository size growth due to binary files
2. **Sensitive Data**: Ensure no sensitive data is included in database packages
3. **Access Control**: Limit access to scheduled task and log files
4. **Backup Verification**: Regularly test package integrity

### Size Management
- Packages are created every 6 hours by default
- Monitor total repository size growth
- Consider `.gitignore` rules for very large backup files
- Implement retention policies for old packages

## 📈 Performance Optimization

### Repository Size Management
```powershell
# Check repository size
git count-objects -vH

# Check large files
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | grep '^blob' | sort -k3 -n -r | head -20
```

### Package Cleanup
```powershell
# Remove old packages (keep last 10)
Get-ChildItem "database_package_*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -Skip 10 | Remove-Item -Force
```

## 🔄 Maintenance

### Regular Tasks
1. **Weekly**: Review logs for errors or warnings
2. **Monthly**: Check repository size and package retention
3. **Quarterly**: Validate package integrity and restore procedures

### Updates and Changes
```powershell
# Update task configuration
.\setup_auto_git_commit_with_db.ps1 -Action remove
.\setup_auto_git_commit_with_db.ps1 -Action create -IncludeDatabase $true -DatabaseName "new_production.db"
```

## 📋 Integration with CI/CD

The system integrates with your existing GitHub Actions workflow:
- Database packages are committed and pushed like regular files
- CI/CD pipeline will process packages as part of normal workflow
- Consider adding package validation steps to your CI/CD pipeline

## 🎯 Best Practices

1. **Monitor Package Sizes**: Keep individual packages under 100MB when possible
2. **Regular Cleanup**: Implement retention policies for old packages
3. **Test Restores**: Periodically test package extraction and database restoration
4. **Log Review**: Regularly review logs for performance and error patterns
5. **Backup Strategy**: Don't rely solely on Git - maintain separate backup strategies

## 📞 Support

### Quick Diagnostics
```powershell
# System health check
.\setup_auto_git_commit_with_db.ps1 -Action status
Get-Content "logs\auto_git_commit_with_db.log" -Tail 10

# Test functionality
.\test_package_and_upload.ps1 -TestType 'package_only'
```

### Common Commands Reference
```powershell
# Create task with database packaging
.\setup_auto_git_commit_with_db.ps1 -Action create -IncludeDatabase $true

# Remove task
.\setup_auto_git_commit_with_db.ps1 -Action remove

# Check status
.\setup_auto_git_commit_with_db.ps1 -Action status

# Manual package creation
.\package_and_upload_db.ps1

# Test packaging
.\test_package_and_upload.ps1 -TestType 'dryrun'
```

---

**Last Updated**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Version**: 1.0.0