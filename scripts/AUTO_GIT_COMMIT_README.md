# Automated Git Commit System

This system automatically commits and pushes changes to your git repository every hour, ensuring your work is regularly backed up to the remote repository.

## Features

- **Automated Hourly Commits**: Commits and pushes changes every hour
- **Comprehensive Logging**: Detailed logs of all operations
- **Error Handling**: Robust error handling with retry logic
- **Dry Run Mode**: Test functionality without making changes
- **Windows Task Scheduler Integration**: Seamless integration with Windows Task Scheduler
- **RASM Compliant**: Follows Reliability, Availability, Scalability, and Maintainability principles

## Files

- `auto_git_commit.ps1` - Main automation script
- `setup_auto_git_commit.ps1` - Setup script for Windows Task Scheduler
- `test_auto_git_commit.ps1` - Test script to verify functionality
- `AUTO_GIT_COMMIT_README.md` - This documentation file

## Quick Start

### 1. Test the Functionality

Before setting up the scheduled task, test the auto-commit functionality:

```powershell
# Test with dry run (no actual changes)
.\scripts\test_auto_git_commit.ps1 -DryRun

# Test with actual commit
.\scripts\test_auto_git_commit.ps1
```

### 2. Set Up Automated Task

Run the setup script as Administrator to create the scheduled task:

```powershell
# Run as Administrator
.\scripts\setup_auto_git_commit.ps1
```

### 3. Manual Execution

You can also run the auto-commit script manually:

```powershell
# Basic execution
.\scripts\auto_git_commit.ps1

# With custom commit message
.\scripts\auto_git_commit.ps1 -CommitMessage "Your custom message"

# Dry run mode
.\scripts\auto_git_commit.ps1 -DryRun
```

## Configuration

### Script Parameters

The `auto_git_commit.ps1` script accepts the following parameters:

- `-CommitMessage`: Custom commit message (default: "Automated hourly commit - [timestamp]")
- `-Branch`: Target branch (default: "main")
- `-Force`: Allow empty commits
- `-DryRun`: Test mode without making changes

### Task Scheduler Configuration

The scheduled task is configured with:

- **Schedule**: Runs every hour
- **Retry**: 3 retries with 5-minute intervals
- **Timeout**: 1-hour execution limit
- **Requirements**: Network connection required
- **Power**: Runs on battery power
- **User**: Runs as current user

## Monitoring

### Log Files

All operations are logged to: `logs\auto_git_commit.log`

Check the logs for:
- Commit success/failure
- Files changed
- Error messages
- Retry attempts

### Task Scheduler

Monitor the scheduled task:

1. Open Task Scheduler (`taskschd.msc`)
2. Find "MHT Auto Git Commit" task
3. Check "Last Run Time" and "Next Run Time"
4. View task history for detailed execution logs

### Command Line

Check task status via PowerShell:

```powershell
# Get task information
Get-ScheduledTask -TaskName "MHT Auto Git Commit" | Get-ScheduledTaskInfo

# Check recent logs
Get-Content "logs\auto_git_commit.log" -Tail 50
```

## Troubleshooting

### Common Issues

1. **Task Not Running**
   - Verify Task Scheduler service is running
   - Check if task is enabled
   - Verify user permissions

2. **Git Authentication Issues**
   - Ensure git credentials are configured
   - Check if SSH keys or PAT tokens are set up
   - Verify remote repository access

3. **Network Issues**
   - Check internet connectivity
   - Verify firewall settings
   - Ensure VPN connection if required

4. **Permission Issues**
   - Run setup script as Administrator
   - Check file system permissions
   - Verify git repository access

### Error Codes

- `0`: Success
- `1`: General error
- `2`: Not a git repository
- `3`: No changes to commit
- `4`: Git command failed

## Maintenance

### Updating the System

1. Stop the scheduled task
2. Update the scripts as needed
3. Test with dry run mode
4. Restart the scheduled task

### Removing the System

```powershell
# Remove the scheduled task (run as Administrator)
.\scripts\setup_auto_git_commit.ps1 -Remove
```

### Log Rotation

The log file will grow over time. Consider implementing log rotation:

```powershell
# Manual log rotation
$LogFile = "logs\auto_git_commit.log"
if (Test-Path $LogFile) {
    $ArchiveFile = "logs\auto_git_commit_$(Get-Date -Format 'yyyyMMdd').log"
    Move-Item $LogFile $ArchiveFile
}
```

## Security Considerations

- **Git Credentials**: Ensure secure storage of git credentials
- **File Permissions**: Restrict access to log files
- **Network Security**: Use secure connections for git operations
- **Audit Trail**: Regular review of commit logs

## RASM Compliance

This system follows RASM principles:

- **Reliability**: Robust error handling and retry logic
- **Availability**: Automatic failover and recovery
- **Scalability**: Efficient resource usage and logging
- **Maintainability**: Clear documentation and modular design

## Best Practices

1. **Regular Monitoring**: Check logs and task status regularly
2. **Test Changes**: Use dry run mode before major changes
3. **Backup Strategy**: Don't rely solely on automated commits
4. **Commit Messages**: Use descriptive commit messages when possible
5. **Branch Strategy**: Ensure you're committing to the correct branch

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review the log files
3. Test with dry run mode
4. Verify git repository status
5. Check Task Scheduler event logs

## Version History

- **v1.0**: Initial implementation with hourly automated commits
- **v1.1**: Added comprehensive error handling and logging
- **v1.2**: Enhanced RASM compliance and monitoring capabilities