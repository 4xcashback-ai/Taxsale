#!/bin/bash

echo "=== FIXING GIT DUBIOUS OWNERSHIP ISSUE ==="

# Set global Git configuration
git config --global --unset-all safe.directory 2>/dev/null || true
git config --global --add safe.directory '*'

# Set local Git configuration
cd /app
git config --local --add safe.directory . 2>/dev/null || true

# Set environment variables
export GIT_CONFIG_GLOBAL=/root/.gitconfig
export GIT_CONFIG_SYSTEM=/etc/gitconfig

# Test Git operations
echo "Testing Git status..."
git status --porcelain

echo "✅ Git ownership issue fixed!"
echo "You can now safely push to GitHub"

# Show current configuration
echo
echo "Current Git safe directories:"
git config --list | grep safe.directory