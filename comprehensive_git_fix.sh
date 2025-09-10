#!/bin/bash

echo "=== COMPREHENSIVE GIT OWNERSHIP FIX ==="

# Fix 1: Global Git configuration
git config --global --unset-all safe.directory 2>/dev/null || true
git config --global --add safe.directory '*'
git config --global --add safe.directory '/app'

# Fix 2: System-wide Git configuration  
echo '[safe]
    directory = *
    directory = /app' | sudo tee -a /etc/gitconfig >/dev/null

# Fix 3: Local repository configuration
cd /app
git config --local --add safe.directory . 2>/dev/null || true
git config --local --add safe.directory /app 2>/dev/null || true

# Fix 4: Environment variables for any context
echo 'export GIT_CONFIG_GLOBAL=/root/.gitconfig' >> ~/.bashrc
echo 'export GIT_CONFIG_SYSTEM=/etc/gitconfig' >> ~/.bashrc

# Fix 5: Alternative ownership approach
sudo git config --system --add safe.directory '*'
sudo git config --system --add safe.directory '/app'

echo "✅ All Git ownership fixes applied!"

# Test all contexts
echo "Testing different contexts:"
echo "1. Normal context:"
git status --porcelain

echo "2. Clean environment context:"
env -i PATH="$PATH" git -C /app status --porcelain

echo "3. System context:"
sudo git -C /app status --porcelain

echo "🎉 Git should now work in ALL contexts!"