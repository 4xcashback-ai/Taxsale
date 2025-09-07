#!/bin/bash

# VPS Deployment Script for Tax Sale Compass
# This script handles git updates and service restarts with proper logging

LOG_FILE="/var/log/taxsale_deploy.log"
APP_DIR="/var/www/tax-sale-compass"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to handle errors
handle_error() {
    log "ERROR: $1"
    echo "DEPLOY_ERROR: $1"
    exit 1
}

# Start deployment
log "=== Starting Tax Sale Compass Deployment ==="
echo "DEPLOY_START"

# Pre-deployment safety checks
log "Running pre-deployment safety checks..."

# Check if nginx is currently working
CURRENT_NGINX_STATUS=$(systemctl is-active nginx 2>/dev/null || echo "inactive")
CURRENT_SITE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://localhost/ -k 2>/dev/null || curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")

log "Current status - Nginx: $CURRENT_NGINX_STATUS, Site response: $CURRENT_SITE_RESPONSE"

if [ "$CURRENT_NGINX_STATUS" = "active" ] && ([ "$CURRENT_SITE_RESPONSE" = "200" ] || [ "$CURRENT_SITE_RESPONSE" = "301" ]); then
    log "✅ Website is currently working - will preserve configuration"
    PRESERVE_NGINX="true"
else
    log "⚠️ Website not responding correctly - nginx fixes may be applied if needed"
    PRESERVE_NGINX="false"
fi

# Check if we're in the right directory
if [ ! -d "$APP_DIR" ]; then
    handle_error "Application directory $APP_DIR not found"
fi

cd "$APP_DIR" || handle_error "Failed to change to application directory"

# Show current git status
log "Current git status:"
git status --porcelain 2>&1 | tee -a "$LOG_FILE"

# Backup current state
BACKUP_DIR="/tmp/taxsale_backup_$(date +%Y%m%d_%H%M%S)"
log "Creating backup at $BACKUP_DIR"
cp -r "$APP_DIR" "$BACKUP_DIR" || log "Warning: Backup creation failed"

# Handle git conflicts automatically
log "Stashing local changes..."
git stash push -m "Auto-stash before deployment $(date)" 2>&1 | tee -a "$LOG_FILE"

# Fetch latest changes
log "Fetching latest changes from remote..."
git fetch origin 2>&1 | tee -a "$LOG_FILE" || handle_error "Git fetch failed"

# Reset to latest remote state
log "Resetting to latest remote state..."
git reset --hard origin/main 2>&1 | tee -a "$LOG_FILE" || handle_error "Git reset failed"

# Clean untracked files (except important directories)
log "Cleaning untracked files..."
git clean -fd -e "frontend-php/assets/thumbnails/" -e "backend/backend.log" 2>&1 | tee -a "$LOG_FILE"

# Show what was updated
log "Recent commits:"
git log --oneline -5 2>&1 | tee -a "$LOG_FILE"

# Set proper permissions
log "Setting file permissions..."
chown -R www-data:www-data "$APP_DIR" 2>&1 | tee -a "$LOG_FILE"
chmod -R 755 "$APP_DIR" 2>&1 | tee -a "$LOG_FILE"
chmod -R 777 "$APP_DIR/frontend-php/assets/thumbnails/" 2>&1 | tee -a "$LOG_FILE"

# Make scripts executable
chmod +x "$APP_DIR/scripts/"*.sh 2>&1 | tee -a "$LOG_FILE"

# Check nginx configuration (smart check for HTTP/HTTPS)
log "Checking nginx configuration..."
NGINX_STATUS=$(systemctl is-active nginx 2>/dev/null || echo "inactive")

if [ "$NGINX_STATUS" = "active" ]; then
    # Test if nginx is responding (either HTTP 200 or 301 redirect to HTTPS is OK)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
    HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://localhost/ -k 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTPS_CODE" = "200" ]; then
        log "✅ Nginx is working correctly (HTTP: $HTTP_CODE, HTTPS: $HTTPS_CODE)"
    else
        log "⚠️ Nginx is running but not responding correctly (HTTP: $HTTP_CODE, HTTPS: $HTTPS_CODE)"
        log "Skipping nginx auto-fix to preserve existing configuration"
    fi
else
    log "❌ Nginx is not running, but skipping auto-fix to preserve SSL configuration"
    log "Manual nginx restart may be needed after deployment"
fi

# Kill any stuck PHP processes
log "Cleaning up PHP processes..."
pkill -f php-fpm 2>&1 | tee -a "$LOG_FILE" || log "No PHP-FPM processes to kill"

# Restart services
log "Restarting nginx..."
systemctl restart nginx 2>&1 | tee -a "$LOG_FILE" || handle_error "Failed to restart nginx"

log "Restarting PHP-FPM..."
systemctl restart php8.1-fpm 2>&1 | tee -a "$LOG_FILE" || handle_error "Failed to restart PHP-FPM"

log "Restarting MySQL..."
systemctl restart mysql 2>&1 | tee -a "$LOG_FILE" || handle_error "Failed to restart MySQL"

# Check service status
log "Checking service status..."
NGINX_STATUS=$(systemctl is-active nginx)
PHP_STATUS=$(systemctl is-active php8.1-fpm)
MYSQL_STATUS=$(systemctl is-active mysql)

log "Service Status: nginx=$NGINX_STATUS, php8.1-fpm=$PHP_STATUS, mysql=$MYSQL_STATUS"

if [ "$NGINX_STATUS" != "active" ] || [ "$PHP_STATUS" != "active" ] || [ "$MYSQL_STATUS" != "active" ]; then
    handle_error "One or more services failed to start properly"
fi

# Test website (check both HTTP and HTTPS)
log "Testing website response..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://localhost/ -k 2>/dev/null || echo "000")

log "Website response codes - HTTP: $HTTP_CODE, HTTPS: $HTTPS_CODE"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTPS_CODE" = "200" ]; then
    log "✅ Website is responding correctly"
else
    log "⚠️ Website response issue - HTTP: $HTTP_CODE, HTTPS: $HTTPS_CODE"
fi

# Success
log "=== Deployment completed successfully ==="
log "Backup created at: $BACKUP_DIR"
echo "DEPLOY_SUCCESS"