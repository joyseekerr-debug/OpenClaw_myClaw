# Auto-sync script for OpenClaw_myClaw
$workspace = "$env:USERPROFILE\.openclaw\workspace"
Set-Location $workspace

# Check if there are changes
$diff = git diff --quiet 2>$null
$staged = git diff --staged --quiet 2>$null

if ($LASTEXITCODE -eq 0) {
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
