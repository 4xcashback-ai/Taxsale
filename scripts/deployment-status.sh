#!/bin/bash

# Get current deployment status
status_file="/tmp/deployment-status.json"

# Default status
cat > "$status_file" << 'EOJ'
{
    "status": "idle",
    "last_deployment": null,
    "last_check": null,
    "updates_available": false,
    "health_status": "unknown",
    "current_commit": null,
    "remote_commit": null
}
EOJ

# Environment detection
if [ -d "/var/www/tax-sale-compass" ]; then
    APP_DIR="/var/www/tax-sale-compass"
elif [ -d "/var/www/nstaxsales" ]; then
    APP_DIR="/var/www/nstaxsales"
elif [ -d "/app" ]; then
    APP_DIR="/app"
else
    echo '{"status": "error", "message": "Application directory not found", "last_check": "'$(date -Iseconds)'"}'
    exit 1
fi

# Check if app directory exists
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    
    # Get current and remote commits
    current_commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    git fetch origin main 2>/dev/null || true
    remote_commit=$(git rev-parse --short origin/main 2>/dev/null || echo "unknown")
    
    # Check if updates available
    updates_available="false"
    if [ "$current_commit" != "$remote_commit" ] && [ "$current_commit" != "unknown" ] && [ "$remote_commit" != "unknown" ]; then
        updates_available="true"
    fi
    
    # Get last deployment time
    last_deployment=""
    if [ -f "/var/log/tax-sale-deployment.log" ]; then
        last_deployment=$(grep "Deployment completed successfully" /var/log/tax-sale-deployment.log | tail -1 | cut -d']' -f1 | tr -d '[' || echo "")
    fi
    
    # Create status JSON
    cat > "$status_file" << EOJ
{
    "status": "idle",
    "last_deployment": "$last_deployment",
    "last_check": "$(date -Iseconds)",
    "updates_available": $updates_available,
    "health_status": "unknown",
    "current_commit": "$current_commit",
    "remote_commit": "$remote_commit",
    "message": "Deployment is operational"
}
EOJ
fi

cat "$status_file"
