#!/bin/bash

# Tax Sale Compass - VPS Deployment Automation Script
# This script handles automated deployment updates

set -e  # Exit on any error

# Configuration - Environment Detection
if [ -d "/var/www/tax-sale-compass" ]; then
    # Production VPS environment
    APP_DIR="/var/www/tax-sale-compass"
    BACKUP_DIR="/var/backups/tax-sale-compass"
    LOG_FILE="/var/log/tax-sale-deployment.log"
    DB_BACKUP_DIR="/var/backups/mongodb"
else
    # Development environment
    APP_DIR="/app"
    BACKUP_DIR="/tmp/backups/nstaxsales"
    LOG_FILE="/tmp/tax-sale-deployment.log"
    DB_BACKUP_DIR="/tmp/backups/mongodb"
fi
GITHUB_REPO=""  # Will be set dynamically

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if we're running as root/sudo
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        log "ERROR: This script must be run as root or with sudo"
        exit 1
    fi
}

# Function to backup current deployment
backup_current_deployment() {
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/backup_$backup_timestamp"
    
    log "Creating backup at: $backup_path"
    
    mkdir -p "$backup_path"
    
    # Backup application files
    if [ -d "$APP_DIR" ]; then
        cp -r "$APP_DIR" "$backup_path/"
        log "Application files backed up"
    fi
    
    # Backup database
    mkdir -p "$DB_BACKUP_DIR"
    mongodump --db taxsalecompass --out "$DB_BACKUP_DIR/backup_$backup_timestamp" 2>/dev/null || log "Warning: MongoDB backup failed"
    
    # Keep only last 5 backups
    find "$BACKUP_DIR" -maxdepth 1 -name "backup_*" -type d | sort -r | tail -n +6 | xargs rm -rf
    
    echo "$backup_path"
}

# Function to pull latest code from GitHub
pull_latest_code() {
    log "Pulling latest code from GitHub..."
    
    cd "$APP_DIR"
    
    # Stash any local changes
    git stash push -m "Auto-stash before deployment $(date)"
    
    # Pull latest changes
    git pull origin main || {
        log "ERROR: Failed to pull from GitHub"
        return 1
    }
    
    log "Latest code pulled successfully"
    return 0
}

# Function to update backend dependencies
update_backend() {
    log "Updating backend dependencies..."
    
    cd "$APP_DIR/backend"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Update pip packages
    pip install -r requirements.txt --upgrade
    
    # Run any database migrations if needed
    # python migrate.py || log "Warning: Database migration failed or not needed"
    
    log "Backend updated successfully"
}

# Function to update frontend
update_frontend() {
    log "Updating frontend..."
    
    cd "$APP_DIR/frontend"
    
    # Install/update dependencies
    yarn install
    
    # Build production bundle
    yarn build
    
    log "Frontend updated and built successfully"
}

# Function to restart services
restart_services() {
    log "Restarting services..."
    
    # Restart PM2 processes
    cd "$APP_DIR"
    pm2 restart tax-sale-backend tax-sale-frontend || {
        log "PM2 restart failed, trying individual restarts..."
        pm2 restart tax-sale-backend || log "Backend restart failed"
        pm2 restart tax-sale-frontend || log "Frontend restart failed"
    }
    
    # Restart nginx
    nginx -t && systemctl reload nginx || {
        log "ERROR: Nginx configuration test failed"
        return 1
    }
    
    log "Services restarted successfully"
}

# Function to verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    sleep 10  # Wait for services to start
    
    # Check if backend is responding
    if curl -f -s http://localhost:8001/api/health >/dev/null 2>&1; then
        log "✓ Backend is responding"
    else
        log "✗ Backend health check failed"
        return 1
    fi
    
    # Check if frontend is responding
    if curl -f -s http://localhost:3000 >/dev/null 2>&1; then
        log "✓ Frontend is responding"
    else
        log "✗ Frontend health check failed"
        return 1
    fi
    
    # Check PM2 status
    if pm2 list | grep -q "online"; then
        log "✓ PM2 processes are running"
    else
        log "✗ PM2 processes are not running properly"
        return 1
    fi
    
    log "Deployment verification completed successfully"
}

# Function to rollback deployment
rollback_deployment() {
    local backup_path="$1"
    
    log "Rolling back deployment to: $backup_path"
    
    if [ ! -d "$backup_path" ]; then
        log "ERROR: Backup path does not exist: $backup_path"
        return 1
    fi
    
    # Stop services
    pm2 delete all 2>/dev/null || true
    
    # Restore files
    rm -rf "$APP_DIR"
    cp -r "$backup_path/nstaxsales" "$APP_DIR"
    
    # Restart services
    restart_services
    
    log "Rollback completed"
}

# Function to check for updates
check_for_updates() {
    cd "$APP_DIR"
    
    # Fetch latest from remote
    git fetch origin main
    
    # Check if there are updates
    local local_commit=$(git rev-parse HEAD)
    local remote_commit=$(git rev-parse origin/main)
    
    if [ "$local_commit" != "$remote_commit" ]; then
        log "Updates available"
        log "Local commit: $local_commit"
        log "Remote commit: $remote_commit"
        return 0
    else
        log "No updates available"
        return 1
    fi
}

# Main deployment function
deploy() {
    local github_repo_url="$1"
    
    log "Starting deployment process..."
    log "GitHub Repository: $github_repo_url"
    
    # Set GitHub repo if provided
    if [ -n "$github_repo_url" ]; then
        GITHUB_REPO="$github_repo_url"
        cd "$APP_DIR"
        git remote set-url origin "$GITHUB_REPO"
    fi
    
    # Create backup
    backup_path=$(backup_current_deployment)
    
    # Pull latest code
    if ! pull_latest_code; then
        log "Code pull failed, aborting deployment"
        return 1
    fi
    
    # Update backend
    if ! update_backend; then
        log "Backend update failed, rolling back..."
        rollback_deployment "$backup_path"
        return 1
    fi
    
    # Update frontend
    if ! update_frontend; then
        log "Frontend update failed, rolling back..."
        rollback_deployment "$backup_path"
        return 1
    fi
    
    # Restart services
    if ! restart_services; then
        log "Service restart failed, rolling back..."
        rollback_deployment "$backup_path"
        return 1
    fi
    
    # Verify deployment
    if ! verify_deployment; then
        log "Deployment verification failed, rolling back..."
        rollback_deployment "$backup_path"
        return 1
    fi
    
    log "Deployment completed successfully!"
    log "Backup location: $backup_path"
    
    return 0
}

# Function to show usage
usage() {
    echo "Usage: $0 {deploy|check-updates|rollback|verify} [github-repo-url]"
    echo ""
    echo "Commands:"
    echo "  deploy [repo-url]    - Deploy latest code from GitHub"
    echo "  check-updates        - Check if updates are available"
    echo "  rollback [backup]    - Rollback to a specific backup"
    echo "  verify              - Verify current deployment"
    echo ""
    echo "Examples:"
    echo "  $0 deploy https://github.com/user/nstaxsales.git"
    echo "  $0 check-updates"
    echo "  $0 verify"
}

# Main script logic
main() {
    # Check permissions
    check_permissions
    
    # Create necessary directories
    mkdir -p "$BACKUP_DIR" "$DB_BACKUP_DIR"
    touch "$LOG_FILE"
    
    case "$1" in
        deploy)
            deploy "$2"
            ;;
        check-updates)
            check_for_updates
            ;;
        rollback)
            rollback_deployment "$2"
            ;;
        verify)
            verify_deployment
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"