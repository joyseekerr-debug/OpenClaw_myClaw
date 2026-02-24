#!/bin/bash
# Auto-sync script for OpenClaw_myClaw

cd "$HOME/.openclaw/workspace" || exit 1

# Check if there are changes
if git diff --quiet && git diff --staged --quiet; then
    echo "No changes to sync"
    exit 0
fi

# Add all changes
git add -A

# Commit with timestamp
git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')"

# Push to GitHub
git push origin main

echo "Synced at $(date)"
