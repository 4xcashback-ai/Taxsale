#!/bin/bash

# Tax Sale Compass - Enhanced Deployment Automation Script
# Bulletproof deployment with environment management, health checks, and rollback capability

set -e  # Exit on any error

# ANSI color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - Environment Detection
if [ -d "/var/www/nstaxsales" ]; then
    # Production VPS environment
    APP_DIR="/var/www/nstaxsales"
    BACKUP_DIR="/var/backups/nstaxsales"
    LOG_FILE="/var/log/tax-sale-deployment.log"
    DB_BACKUP_DIR="/var/backups/mongodb"
    ENV_BACKUP_DIR="/var/backups/nstaxsales/env-backups"
    FRONTEND_BUILD_REQUIRED="auto"  # auto-detect when frontend rebuild needed
else
    # Development environment
    APP_DIR="/app"
    BACKUP_DIR="/tmp/backups/nstaxsales"
    LOG_FILE="/tmp/tax-sale-deployment.log"
    DB_BACKUP_DIR="/tmp/backups/mongodb"
    ENV_BACKUP_DIR="/tmp/backups/nstaxsales/env-backups"
    FRONTEND_BUILD_REQUIRED="auto"
fi

# Create necessary directories
mkdir -p "$BACKUP_DIR" "$ENV_BACKUP_DIR" "$DB_BACKUP_DIR"

# Enhanced logging with colors and timestamps
log() {
    local level="$1"
    local message="$2"
    local timestamp="[$(date '+%Y-%m-%d %H:%M:%S')]"
    
    case "$level" in
        "INFO")
            echo -e "${BLUE}${timestamp} [INFO]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        "SUCCESS")
            echo -e "${GREEN}${timestamp} [SUCCESS]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        "WARNING")
            echo -e "${YELLOW}${timestamp} [WARNING]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        "ERROR")
            echo -e "${RED}${timestamp} [ERROR]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        *)
            echo "$timestamp $message" | tee -a "$LOG_FILE"
            ;;
    esac
}

# Environment Variable Management
backup_environment_variables() {
    log "INFO" "Backing up environment variables..."
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local env_backup_path="$ENV_BACKUP_DIR/env_backup_$backup_timestamp"
    
    mkdir -p "$env_backup_path"
    
    # Backup backend .env
    if [ -f "$APP_DIR/backend/.env" ]; then
        cp "$APP_DIR/backend/.env" "$env_backup_path/backend.env"
        log "SUCCESS" "Backend .env backed up"
    fi
    
    # Backup frontend .env
    if [ -f "$APP_DIR/frontend/.env" ]; then
        cp "$APP_DIR/frontend/.env" "$env_backup_path/frontend.env"
        log "SUCCESS" "Frontend .env backed up"
    fi
    
    echo "$env_backup_path" > /tmp/latest_env_backup.txt
    log "SUCCESS" "Environment variables backed up to: $env_backup_path"
}

restore_environment_variables() {
    log "INFO" "Restoring environment variables..."
    
    if [ ! -f "/tmp/latest_env_backup.txt" ]; then
        log "WARNING" "No environment backup found to restore"
        return 0
    fi
    
    local env_backup_path=$(cat /tmp/latest_env_backup.txt)
    
    if [ ! -d "$env_backup_path" ]; then
        log "WARNING" "Environment backup directory not found: $env_backup_path"
        return 0
    fi
    
    # Restore backend .env
    if [ -f "$env_backup_path/backend.env" ]; then
        cp "$env_backup_path/backend.env" "$APP_DIR/backend/.env"
        log "SUCCESS" "Backend .env restored"
    fi
    
    # Restore frontend .env
    if [ -f "$env_backup_path/frontend.env" ]; then
        cp "$env_backup_path/frontend.env" "$APP_DIR/frontend/.env"
        log "SUCCESS" "Frontend .env restored"
    fi
    
    # Clean up temp file
    rm -f /tmp/latest_env_backup.txt
}

# Enhanced Environment Variable Validation
validate_environment_variables() {
    log "INFO" "Validating environment variables..."
    local validation_failed=0
    
    # Check backend .env
    if [ -f "$APP_DIR/backend/.env" ]; then
        # Check for required backend variables
        if ! grep -q "MONGO_URL=" "$APP_DIR/backend/.env"; then
            log "ERROR" "Missing MONGO_URL in backend .env"
            validation_failed=1
        fi
        
        if ! grep -q "ADMIN_USERNAME=" "$APP_DIR/backend/.env"; then
            log "ERROR" "Missing ADMIN_USERNAME in backend .env"
            validation_failed=1
        fi
        
        if ! grep -q "JWT_SECRET_KEY=" "$APP_DIR/backend/.env"; then
            log "ERROR" "Missing JWT_SECRET_KEY in backend .env"
            validation_failed=1
        fi
        
        log "SUCCESS" "Backend environment variables validated"
    else
        log "ERROR" "Backend .env file not found"
        validation_failed=1
    fi
    
    # Check frontend .env
    if [ -f "$APP_DIR/frontend/.env" ]; then
        # Check for required frontend variables
        if ! grep -q "REACT_APP_BACKEND_URL=" "$APP_DIR/frontend/.env"; then
            log "ERROR" "Missing REACT_APP_BACKEND_URL in frontend .env"
            validation_failed=1
        fi
        
        # Validate backend URL format
        local backend_url=$(grep "REACT_APP_BACKEND_URL=" "$APP_DIR/frontend/.env" | cut -d'=' -f2)
        if [[ ! "$backend_url" =~ ^https?:// ]]; then
            log "ERROR" "Invalid REACT_APP_BACKEND_URL format: $backend_url"
            validation_failed=1
        fi
        
        log "SUCCESS" "Frontend environment variables validated"
    else
        log "ERROR" "Frontend .env file not found"
        validation_failed=1
    fi
    
    if [ $validation_failed -eq 1 ]; then
        log "ERROR" "Environment variable validation failed"
        return 1
    fi
    
    log "SUCCESS" "All environment variables validated successfully"
    return 0
}

# Automatic Frontend Build Detection
detect_frontend_changes() {
    log "INFO" "Detecting if frontend rebuild is required..."
    
    local git_log_output=$(git log --name-only -1)
    
    # Check if any frontend files were changed
    if echo "$git_log_output" | grep -q "frontend/"; then
        log "INFO" "Frontend changes detected - rebuild required"
        return 0  # Rebuild needed
    fi
    
    # Check if .env files were restored (different from git)
    if [ -f "$APP_DIR/frontend/.env" ]; then
        local current_backend_url=$(grep "REACT_APP_BACKEND_URL=" "$APP_DIR/frontend/.env" 2>/dev/null | cut -d'=' -f2 || echo "")
        if [ -n "$current_backend_url" ]; then
            # Check if the current build has the right backend URL
            if [ -f "$APP_DIR/frontend/build/static/js/main."*.js ]; then
                local build_file=$(ls "$APP_DIR/frontend/build/static/js/main."*.js | head -1)
                if ! grep -q "$current_backend_url" "$build_file" 2>/dev/null; then
                    log "INFO" "Frontend build doesn't match current environment - rebuild required"
                    return 0  # Rebuild needed
                fi
            fi
        fi
    fi
    
    log "SUCCESS" "No frontend rebuild required"
    return 1  # No rebuild needed
}

# Enhanced Frontend Build Process
build_frontend_with_validation() {
    log "INFO" "Building frontend with environment validation..."
    
    cd "$APP_DIR/frontend"
    
    # Validate environment before build
    if [ ! -f ".env" ]; then
        log "ERROR" "Frontend .env file missing - cannot build"
        return 1
    fi
    
    # Show environment being used for build
    log "INFO" "Building with environment:"
    while IFS= read -r line; do
        if [[ "$line" =~ ^REACT_APP_ ]]; then
            log "INFO" "  $line"
        fi
    done < .env
    
    # Clean previous build
    rm -rf build/ node_modules/.cache/ 2>/dev/null || true
    
    # Build with timeout and error handling
    log "INFO" "Starting frontend build..."
    timeout 300 yarn build 2>&1 | while IFS= read -r line; do
        echo "$line" | tee -a "$LOG_FILE"
    done
    
    if [ $? -eq 0 ] && [ -d "build" ]; then
        log "SUCCESS" "Frontend build completed successfully"
        
        # Validate build contains correct environment variables
        local build_file=$(ls build/static/js/main.*.js 2>/dev/null | head -1)
        if [ -f "$build_file" ]; then
            local backend_url=$(grep "REACT_APP_BACKEND_URL=" .env | cut -d'=' -f2)
            if grep -q "$backend_url" "$build_file" 2>/dev/null; then
                log "SUCCESS" "Build validation passed - correct environment variables embedded"
            else
                log "WARNING" "Build validation warning - environment variables may not be embedded correctly"
            fi
        fi
        
        cd "$APP_DIR"
        return 0
    else
        log "ERROR" "Frontend build failed"
        cd "$APP_DIR"
        return 1
    fi
}

# Enhanced Service Health Checks
comprehensive_health_check() {
    log "INFO" "Performing comprehensive health checks..."
    local health_failed=0
    
    # Check if PM2 processes are running
    if command -v pm2 &> /dev/null; then
        log "INFO" "Checking PM2 services..."
        local pm2_status=$(pm2 jlist 2>/dev/null)
        
        # Check backend
        if echo "$pm2_status" | jq -e '.[] | select(.name=="taxsale-backend" and .pm2_env.status=="online")' &> /dev/null; then
            log "SUCCESS" "Backend service is online"
        else
            log "ERROR" "Backend service is not running"
            health_failed=1
        fi
        
        # Check frontend
        if echo "$pm2_status" | jq -e '.[] | select(.name=="taxsale-frontend" and .pm2_env.status=="online")' &> /dev/null; then
            log "SUCCESS" "Frontend service is online"
        else
            log "ERROR" "Frontend service is not running"
            health_failed=1
        fi
    else
        log "WARNING" "PM2 not found - skipping PM2 service checks"
    fi
    
    # Test backend endpoints
    log "INFO" "Testing backend endpoints..."
    local backend_url=""
    if [ -f "$APP_DIR/frontend/.env" ]; then
        backend_url=$(grep "REACT_APP_BACKEND_URL=" "$APP_DIR/frontend/.env" | cut -d'=' -f2 | sed 's/^"//' | sed 's/"$//')
    fi
    
    if [ -n "$backend_url" ]; then
        # Test health endpoint
        if curl -s -f --max-time 10 "$backend_url/api/health" &> /dev/null; then
            log "SUCCESS" "Backend health endpoint responding"
        else
            log "ERROR" "Backend health endpoint not responding"
            health_failed=1
        fi
        
        # Test authentication endpoint
        if curl -s -f --max-time 10 -X POST "$backend_url/api/auth/login" \
           -H "Content-Type: application/json" \
           -d '{"username":"test","password":"test"}' 2>&1 | grep -q "Incorrect username"; then
            log "SUCCESS" "Backend authentication endpoint responding"
        else
            log "ERROR" "Backend authentication endpoint not responding correctly"
            health_failed=1
        fi
    else
        log "WARNING" "Backend URL not found - skipping endpoint tests"
    fi
    
    # Test frontend
    log "INFO" "Testing frontend..."
    if [ -d "$APP_DIR/frontend/build" ]; then
        if [ -f "$APP_DIR/frontend/build/index.html" ]; then
            log "SUCCESS" "Frontend build exists and contains index.html"
        else
            log "ERROR" "Frontend build missing index.html"
            health_failed=1
        fi
    else
        log "ERROR" "Frontend build directory not found"
        health_failed=1
    fi
    
    if [ $health_failed -eq 1 ]; then
        log "ERROR" "Health check failed"
        return 1
    fi
    
    log "SUCCESS" "All health checks passed"
    return 0
}

# Rollback Capability
create_rollback_point() {
    log "INFO" "Creating rollback point..."
    local rollback_timestamp=$(date '+%Y%m%d_%H%M%S')
    local rollback_path="$BACKUP_DIR/rollback_$rollback_timestamp"
    
    mkdir -p "$rollback_path"
    
    # Backup current state
    if [ -d "$APP_DIR/frontend/build" ]; then
        cp -r "$APP_DIR/frontend/build" "$rollback_path/frontend_build" 2>/dev/null || true
    fi
    
    # Backup current git commit
    cd "$APP_DIR"
    git rev-parse HEAD > "$rollback_path/git_commit.txt"
    
    # Backup environment files
    if [ -f "$APP_DIR/backend/.env" ]; then
        cp "$APP_DIR/backend/.env" "$rollback_path/backend.env"
    fi
    if [ -f "$APP_DIR/frontend/.env" ]; then
        cp "$APP_DIR/frontend/.env" "$rollback_path/frontend.env"
    fi
    
    echo "$rollback_path" > /tmp/latest_rollback.txt
    log "SUCCESS" "Rollback point created: $rollback_path"
}

perform_rollback() {
    log "WARNING" "Performing rollback..."
    
    if [ ! -f "/tmp/latest_rollback.txt" ]; then
        log "ERROR" "No rollback point found"
        return 1
    fi
    
    local rollback_path=$(cat /tmp/latest_rollback.txt)
    
    if [ ! -d "$rollback_path" ]; then
        log "ERROR" "Rollback directory not found: $rollback_path"
        return 1
    fi
    
    cd "$APP_DIR"
    
    # Restore git commit
    if [ -f "$rollback_path/git_commit.txt" ]; then
        local previous_commit=$(cat "$rollback_path/git_commit.txt")
        git reset --hard "$previous_commit"
        log "SUCCESS" "Git state rolled back to: $previous_commit"
    fi
    
    # Restore frontend build
    if [ -d "$rollback_path/frontend_build" ]; then
        rm -rf "$APP_DIR/frontend/build"
        cp -r "$rollback_path/frontend_build" "$APP_DIR/frontend/build"
        log "SUCCESS" "Frontend build rolled back"
    fi
    
    # Restore environment files
    if [ -f "$rollback_path/backend.env" ]; then
        cp "$rollback_path/backend.env" "$APP_DIR/backend/.env"
    fi
    if [ -f "$rollback_path/frontend.env" ]; then
        cp "$rollback_path/frontend.env" "$APP_DIR/frontend/.env"
    fi
    
    # Restart services
    if command -v pm2 &> /dev/null; then
        pm2 restart all
        sleep 5
    fi
    
    # Verify rollback worked
    if comprehensive_health_check; then
        log "SUCCESS" "Rollback completed successfully"
        rm -f /tmp/latest_rollback.txt
        return 0
    else
        log "ERROR" "Rollback verification failed"
        return 1
    fi
}

# Main deployment function
enhanced_deploy() {
    log "INFO" "Starting enhanced deployment process..."
    
    # Change to app directory
    cd "$APP_DIR"
    
    # Step 1: Create rollback point
    create_rollback_point
    
    # Step 2: Backup environment variables
    backup_environment_variables
    
    # Step 3: Pull latest code
    log "INFO" "Pulling latest code from GitHub..."
    if git pull origin main; then
        log "SUCCESS" "Code pulled successfully"
    else
        log "ERROR" "Failed to pull code from GitHub"
        perform_rollback
        return 1
    fi
    
    # Step 4: Restore environment variables
    restore_environment_variables
    
    # Step 5: Validate environment variables
    if ! validate_environment_variables; then
        log "ERROR" "Environment validation failed"
        perform_rollback
        return 1
    fi
    
    # Step 6: Install backend dependencies (if requirements.txt changed)
    log "INFO" "Checking backend dependencies..."
    cd "$APP_DIR/backend"
    if [ -f "requirements.txt" ]; then
        if [ -f "venv/bin/pip" ]; then
            ./venv/bin/pip install -r requirements.txt --quiet
            log "SUCCESS" "Backend dependencies updated"
        else
            log "WARNING" "Virtual environment not found - skipping dependency installation"
        fi
    fi
    cd "$APP_DIR"
    
    # Step 7: Check if frontend rebuild is needed
    if detect_frontend_changes; then
        log "INFO" "Frontend rebuild required"
        if ! build_frontend_with_validation; then
            log "ERROR" "Frontend build failed"
            perform_rollback
            return 1
        fi
    else
        log "INFO" "Frontend rebuild not required"
    fi
    
    # Step 8: Restart services
    log "INFO" "Restarting services..."
    if command -v pm2 &> /dev/null; then
        pm2 restart all
        sleep 10  # Give services time to start
        log "SUCCESS" "Services restarted with PM2"
    else
        log "WARNING" "PM2 not found - manual service restart may be required"
    fi
    
    # Step 9: Comprehensive health check
    if ! comprehensive_health_check; then
        log "ERROR" "Post-deployment health check failed"
        perform_rollback
        return 1
    fi
    
    # Step 10: Cleanup old backups (keep last 5)
    log "INFO" "Cleaning up old backups..."
    find "$BACKUP_DIR" -name "rollback_*" -type d | sort -r | tail -n +6 | xargs rm -rf 2>/dev/null || true
    find "$ENV_BACKUP_DIR" -name "env_backup_*" -type d | sort -r | tail -n +6 | xargs rm -rf 2>/dev/null || true
    
    log "SUCCESS" "Enhanced deployment completed successfully!"
    return 0
}

# Command handling
case "${1:-deploy}" in
    "deploy")
        enhanced_deploy
        ;;
    "check-updates")
        cd "$APP_DIR"
        git fetch origin main
        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse origin/main)
        if [ "$LOCAL" != "$REMOTE" ]; then
            log "INFO" "Updates available"
            log "INFO" "Local commit: $LOCAL"
            log "INFO" "Remote commit: $REMOTE"
        else
            log "INFO" "No updates available"
        fi
        ;;
    "rollback")
        perform_rollback
        ;;
    "health-check")
        comprehensive_health_check
        ;;
    "validate-env")
        validate_environment_variables
        ;;
    *)
        echo "Usage: $0 {deploy|check-updates|rollback|health-check|validate-env}"
        exit 1
        ;;
esac