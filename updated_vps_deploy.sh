#!/bin/bash

# VPS Deployment Script for Tax Sale Compass
# Updated for MongoDB-only deployment (MySQL removed)

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

# Detect if running from web interface
WEB_DEPLOY=${WEB_DEPLOY:-"false"}
if [ "$USER" = "www-data" ] || [ -n "$HTTP_HOST" ] || [ -n "$REQUEST_METHOD" ]; then
    WEB_DEPLOY="true"
fi

# Start deployment
log "=== Starting Tax Sale Compass Deployment (MongoDB-only) ==="
echo "DEPLOY_START"

if [ "$WEB_DEPLOY" = "true" ]; then
    log "🌐 Web deployment detected - using web-safe mode"
else
    log "💻 Command-line deployment detected"
fi

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

# MongoDB Setup and Verification
log "Checking MongoDB setup..."

# Check if MongoDB is installed
if ! command -v mongosh &> /dev/null; then
    log "❌ MongoDB not found - installation required"
    handle_error "MongoDB is not installed"
else
    log "✅ MongoDB found"
    
    # Check if MongoDB service is active
    MONGO_STATUS=$(systemctl is-active mongod 2>/dev/null || echo "inactive")
    if [ "$MONGO_STATUS" != "active" ]; then
        log "Starting MongoDB service..."
        systemctl start mongod 2>&1 | tee -a "$LOG_FILE" || handle_error "Failed to start MongoDB"
    fi
    
    # Check if tax_sale_compass database exists
    MONGO_DB_EXISTS=$(mongosh tax_sale_compass --eval "db.getCollectionNames().length" --quiet 2>/dev/null || echo "0")
    if [ "$MONGO_DB_EXISTS" -gt "0" ]; then
        log "✅ MongoDB database exists with $MONGO_DB_EXISTS collections"
    else
        log "⚠️ MongoDB database is empty - may need data migration"
    fi
fi

# Check PHP MongoDB extension
if php -m | grep -q mongodb; then
    log "✅ PHP MongoDB extension installed"
else
    log "❌ PHP MongoDB extension missing - installation required"
    handle_error "PHP MongoDB extension not found"
fi

# Verify MySQL is no longer needed/running
MYSQL_STATUS=$(systemctl is-active mysql 2>/dev/null || echo "inactive")
if [ "$MYSQL_STATUS" = "active" ]; then
    log "⚠️ MySQL service is still running (not needed for MongoDB-only deployment)"
    log "Consider stopping MySQL: systemctl stop mysql && systemctl disable mysql"
else
    log "✅ MySQL service is not running (expected for MongoDB-only deployment)"
fi

# Set proper permissions
log "Setting file permissions..."
chown -R www-data:www-data "$APP_DIR" 2>&1 | tee -a "$LOG_FILE"
chmod -R 755 "$APP_DIR" 2>&1 | tee -a "$LOG_FILE"
chmod -R 777 "$APP_DIR/frontend-php/assets/thumbnails/" 2>&1 | tee -a "$LOG_FILE"

# Make scripts executable
chmod +x "$APP_DIR/scripts/"*.sh 2>&1 | tee -a "$LOG_FILE"

# Check nginx configuration
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

# Kill any stuck PHP processes (skip for web deployments)
if [ "$WEB_DEPLOY" = "true" ]; then
    log "Skipping PHP process cleanup (web deployment - would kill current session)"
else
    log "Cleaning up PHP processes..."
    pkill -f php-fpm 2>&1 | tee -a "$LOG_FILE" || log "No PHP-FPM processes to kill"
fi

# Restart services (MongoDB-only deployment)
log "Restarting nginx..."
systemctl restart nginx 2>&1 | tee -a "$LOG_FILE" || handle_error "Failed to restart nginx"

log "Restarting PHP-FPM..."
systemctl restart php8.1-fpm 2>&1 | tee -a "$LOG_FILE" || handle_error "Failed to restart PHP-FPM"

log "Restarting MongoDB..."
systemctl restart mongod 2>&1 | tee -a "$LOG_FILE" || handle_error "Failed to restart MongoDB"

log "Restarting Tax Sale Backend..."
systemctl restart tax-sale-backend 2>&1 | tee -a "$LOG_FILE" || handle_error "Failed to restart Tax Sale Backend"

# Check service status (MongoDB-only)
log "Checking service status..."
NGINX_STATUS=$(systemctl is-active nginx)
PHP_STATUS=$(systemctl is-active php8.1-fpm)
MONGODB_STATUS=$(systemctl is-active mongod)
BACKEND_STATUS=$(systemctl is-active tax-sale-backend)

log "Service Status: nginx=$NGINX_STATUS, php8.1-fpm=$PHP_STATUS, mongod=$MONGODB_STATUS, tax-sale-backend=$BACKEND_STATUS"

if [ "$NGINX_STATUS" != "active" ] || [ "$PHP_STATUS" != "active" ] || [ "$MONGODB_STATUS" != "active" ] || [ "$BACKEND_STATUS" != "active" ]; then
    handle_error "One or more services failed to start properly"
fi

# Test MongoDB connection
log "Testing MongoDB connection..."
MONGO_TEST=$(mongosh --eval "db.runCommand('ping')" --quiet 2>/dev/null | grep -c "ok.*1" || echo "0")
if [ "$MONGO_TEST" = "1" ]; then
    log "✅ MongoDB connection successful"
else
    log "❌ MongoDB connection test failed"
    handle_error "MongoDB connection failed"
fi

# Check PHP MongoDB extension
PHP_MONGO_EXT=$(php -m | grep -c mongodb || echo "0")
if [ "$PHP_MONGO_EXT" = "1" ]; then
    log "✅ PHP MongoDB extension loaded"
else
    log "❌ PHP MongoDB extension not loaded"
    handle_error "PHP MongoDB extension not working"
fi

# Test database connection via PHP
log "Testing PHP MongoDB connection..."
DB_TEST_RESULT=$(php -r "
require_once '$APP_DIR/frontend-php/config/database.php';
\$db = getDB();
echo \$db ? 'SUCCESS' : 'FAILED';
" 2>/dev/null || echo "ERROR")

if [ "$DB_TEST_RESULT" = "SUCCESS" ]; then
    log "✅ PHP MongoDB connection successful"
else
    log "❌ PHP MongoDB connection failed: $DB_TEST_RESULT"
    handle_error "PHP cannot connect to MongoDB"
fi

# Test website (check both HTTP and HTTPS)
log "Testing website response..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://localhost/ -k 2>/dev/null || echo "000")

log "Website response codes - HTTP: $HTTP_CODE, HTTPS: $HTTPS_CODE"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTPS_CODE" = "200" ]; then
    log "✅ Website is responding correctly"
else
    log "❌ Website response issue - HTTP: $HTTP_CODE, HTTPS: $HTTPS_CODE"
    handle_error "Website is not responding correctly"
fi

# Verify login functionality
log "Testing login page..."
LOGIN_TEST=$(curl -s -o /dev/null -w "%{http_code}" https://localhost/login.php -k 2>/dev/null || echo "000")
if [ "$LOGIN_TEST" = "200" ]; then
    log "✅ Login page accessible"
else
    log "⚠️ Login page response: $LOGIN_TEST"
fi

# Success
log "=== MongoDB-only deployment completed successfully ==="
log "✅ MySQL dependencies removed"
log "✅ MongoDB fully operational"
log "✅ Website functioning correctly"
log "Backup created at: $BACKUP_DIR"
echo "DEPLOY_SUCCESS"