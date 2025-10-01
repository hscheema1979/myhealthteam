# Multi-IDE Branch Management Workflow

## Current Setup
Your project has an excellent structure for managing multiple branches simultaneously:

```
d:\Git\myhealthteam2\Streamlit\                    # Main working directory
├── sandbox\auth_integration_branch\               # Auth integration work
├── sandbox\production_branch\                     # Production-ready code
└── [main files]                                   # Current branch files
```

## IDE Workflow Strategies

### Strategy 1: Multiple IDE Instances (Recommended)
Open different IDE instances for different branches:

**IDE Instance 1 - Main Development**
- Path: `d:\Git\myhealthteam2\Streamlit\`
- Branch: `feature/auth-integration` or `main`
- Use for: Primary development work

**IDE Instance 2 - Auth Integration**
- Path: `d:\Git\myhealthteam2\Streamlit\sandbox\auth_integration_branch\`
- Use for: Authentication feature development
- Isolated environment for testing auth changes

**IDE Instance 3 - Production Testing**
- Path: `d:\Git\myhealthteam2\Streamlit\sandbox\production_branch\`
- Use for: Production-ready code testing
- Stable environment for final validation

### Strategy 2: Single IDE with Terminal Management
Use one IDE but manage branches through terminals:

```powershell
# Terminal 1 - Main work
cd d:\Git\myhealthteam2\Streamlit
git checkout main

# Terminal 2 - Auth integration
cd d:\Git\myhealthteam2\Streamlit\sandbox\auth_integration_branch

# Terminal 3 - Production
cd d:\Git\myhealthteam2\Streamlit\sandbox\production_branch
```

## Branch Synchronization

### From Auth Integration to Main
```powershell
# Use the merge script
.\merge_branches.ps1 -SourceBranch "auth-integration" -TargetBranch "main"
```

### From Main to Production
```powershell
# Use the merge script
.\merge_branches.ps1 -SourceBranch "main" -TargetBranch "production"
```

## Git Branch Management

### Current Branch Status
```powershell
git branch -a                    # List all branches
git status                       # Current branch status
git log --oneline -10           # Recent commits
```

### Switching Between Branches
```powershell
git checkout main                           # Switch to main
git checkout feature/auth-integration       # Switch to auth branch
git checkout -b new-feature                # Create new branch
```

### Merging Workflow
```powershell
# 1. Ensure you're on the target branch
git checkout main

# 2. Merge from feature branch
git merge feature/auth-integration

# 3. Push changes
git push origin main
```

## Development Ports
Based on your setup:
- **Port 8501**: Production (do not touch)
- **Port 8502**: Sandbox development
- **Port 8503**: Alternate dev/test environment

## Best Practices

### 1. File Synchronization
- Keep database files separate (*.db files are excluded from copying)
- Use the merge script for controlled file transfers
- Always review changes before committing

### 2. Testing Strategy
- Test in sandbox environment (port 8502) before main
- Use production branch for final validation
- Keep auth integration isolated until ready

### 3. Commit Strategy
- Make frequent small commits in feature branches
- Use descriptive commit messages
- Test thoroughly before merging to main

### 4. IDE Configuration
- Configure each IDE instance with appropriate settings
- Use different terminal profiles for different branches
- Set up branch-specific environment variables if needed

## Troubleshooting

### Database Lock Issues
If you encounter database locks:
```powershell
# Check running processes
netstat -ano | findstr :850
tasklist | findstr python

# Stop specific Streamlit instances if needed
# (Follow port usage rules - don't touch 8501)
```

### Merge Conflicts
```powershell
# View conflicts
git status
git diff

# Resolve manually, then:
git add .
git commit -m "Resolve merge conflicts"
```

### Branch Synchronization
```powershell
# Update from remote
git fetch origin
git pull origin main

# Sync branch directories using merge script
.\merge_branches.ps1 -SourceBranch "main" -TargetBranch "auth-integration"
```