# Auto-sync script for OpenClaw_myClaw
$workspace = "$env:USERPROFILE\.openclaw\workspace"
Set-Location $workspace

# Check for changes (including untracked files)
$untracked = git ls-files --others --exclude-standard
$diff = git diff --quiet 2>$null
$hasChanges = $diff -ne 0 -or $untracked

if (-not $hasChanges) {
    Write-Host "No changes to sync"
    exit 0
}

# Add all changes
git add -A

# Commit with timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
git commit -m "Auto-sync: $timestamp"

# Push to GitHub
git push origin main

Write-Host "Synced at $timestamp"
