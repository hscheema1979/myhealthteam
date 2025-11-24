#!/usr/bin/env python3
"""
Auto-commit script for git repository
Commits changes every hour with timestamp
"""

import subprocess
import datetime
import os
import sys

def run_git_command(command):
    """Run git command and return output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_git_status():
    """Check if there are any changes to commit"""
    success, stdout, stderr = run_git_command("git status --porcelain")
    if not success:
        return False, f"Error checking git status: {stderr}"
    
    if not stdout.strip():
        return False, "No changes to commit"
    
    return True, stdout

def commit_changes():
    """Add all changes and commit them"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Add all changes
    success, stdout, stderr = run_git_command("git add .")
    if not success:
        return False, f"Error adding files: {stderr}"
    
    # Check if there are any staged changes
    success, stdout, stderr = run_git_command("git diff --cached --name-only")
    if not success or not stdout.strip():
        return False, "No changes to commit after adding files"
    
    # Commit with timestamp
    commit_message = f"Auto-commit: {timestamp}"
    success, stdout, stderr = run_git_command(f'git commit -m "{commit_message}"')
    
    if success:
        return True, f"Committed changes: {commit_message}\n{stdout}"
    else:
        return False, f"Error committing: {stderr}"

def main():
    """Main function"""
    # Get current working directory
    try:
        os.getcwd()
    except Exception as e:
        print(f"Error getting current directory: {e}")
        sys.exit(1)
    
    # Check for changes
    has_changes, status_output = get_git_status()
    if not has_changes:
        if "No changes to commit" in status_output:
            print(f"No changes to commit at {datetime.datetime.now()}")
            sys.exit(0)
        else:
            print(f"Error checking git status: {status_output}")
            sys.exit(1)
    
    # Commit changes
    success, message = commit_changes()
    if success:
        print(f"SUCCESS: {message}")
    else:
        print(f"FAILED: {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()