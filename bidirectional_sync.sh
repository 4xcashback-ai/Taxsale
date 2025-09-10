#!/bin/bash

# Bidirectional File Synchronization Script
# Local Dev Environment <-> VPS

VPS_HOST="5.252.52.41"
VPS_USER="root"
VPS_PASS="527iDUjHGHjx8"
VPS_PATH="/var/www/tax-sale-compass"
LOCAL_PATH="/app"

echo "=== BIDIRECTIONAL FILE SYNCHRONIZATION ==="
echo "Local Dev: $LOCAL_PATH"
echo "VPS: $VPS_USER@$VPS_HOST:$VPS_PATH"
echo

# Rsync options:
# -a = archive mode (preserves permissions, timestamps, etc.)
# -v = verbose
# -z = compress during transfer
# -u = update (only transfer newer files)
# --delete = delete files that don't exist in source
# --exclude = exclude patterns

RSYNC_OPTS="-avzu --progress"
EXCLUDES="--exclude='.env' --exclude='*.log' --exclude='vendor/' --exclude='node_modules/' --exclude='__pycache__/' --exclude='.git/' --exclude='*.pyc' --exclude='venv/' --exclude='.DS_Store' --exclude='*.tmp'"

echo "🔄 PHASE 1: VPS → Local Dev (Downloading newer VPS files)"
echo "------------------------------------------------------------"

# Sync VPS to Local (download newer files from VPS)
sshpass -p "$VPS_PASS" rsync $RSYNC_OPTS $EXCLUDES \
    -e "ssh -o StrictHostKeyChecking=no" \
    "$VPS_USER@$VPS_HOST:$VPS_PATH/" "$LOCAL_PATH/"

echo
echo "🔄 PHASE 2: Local Dev → VPS (Uploading newer local files)"
echo "------------------------------------------------------------"

# Sync Local to VPS (upload newer files to VPS)
sshpass -p "$VPS_PASS" rsync $RSYNC_OPTS $EXCLUDES \
    -e "ssh -o StrictHostKeyChecking=no" \
    "$LOCAL_PATH/" "$VPS_USER@$VPS_HOST:$VPS_PATH/"

echo
echo "🔄 PHASE 3: Final VPS → Local sync (Ensure consistency)"
echo "------------------------------------------------------------"

# Final sync from VPS to Local to ensure consistency
sshpass -p "$VPS_PASS" rsync $RSYNC_OPTS $EXCLUDES \
    -e "ssh -o StrictHostKeyChecking=no" \
    "$VPS_USER@$VPS_HOST:$VPS_PATH/" "$LOCAL_PATH/"

echo
echo "✅ BIDIRECTIONAL SYNC COMPLETED!"
echo
echo "=== VERIFICATION ==="