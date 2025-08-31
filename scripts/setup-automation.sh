#!/bin/bash

# Tax Sale Compass - Setup Automation Script
# This script sets up the deployment automation system

set -e

# Configuration
SCRIPT_DIR="/var/www/nstaxsales/scripts"
SERVICE_USER="www-data"
LOG_DIR="/var/log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Function to create directories
setup_directories() {
    log "Setting up directories..."
    
    mkdir -p "$SCRIPT_DIR"
    mkdir -p "/var/backups/nstaxsales"
    mkdir -p "/var/backups/mongodb"
    
    # Set proper permissions
    chown -R root:root "$SCRIPT_DIR"
    chmod 755 "$SCRIPT_DIR"
    
    log "Directories created successfully"
}

# Function to copy scripts
copy_scripts() {
    log "Copying automation scripts..."
    
    # Copy scripts to system directory
    cp /app/scripts/deployment.sh "$SCRIPT_DIR/"
    cp /app/scripts/system-health.sh "$SCRIPT_DIR/"
    
    # Make scripts executable
    chmod +x "$SCRIPT_DIR"/*.sh
    
    # Create symlinks in /usr/local/bin for easy access
    ln -sf "$SCRIPT_DIR/deployment.sh" /usr/local/bin/nstaxsales-deploy
    ln -sf "$SCRIPT_DIR/system-health.sh" /usr/local/bin/nstaxsales-health
    
    log "Scripts installed successfully"
}

# Function to setup sudoers for web user
setup_sudoers() {
    log "Setting up sudoers for deployment automation..."
    
    # Create sudoers file for nstaxsales
    cat > /etc/sudoers.d/nstaxsales << 'EOF'
# Allow www-data to run deployment and health scripts
www-data ALL=(root) NOPASSWD: /var/www/nstaxsales/scripts/deployment.sh
www-data ALL=(root) NOPASSWD: /var/www/nstaxsales/scripts/system-health.sh
www-data ALL=(root) NOPASSWD: /usr/local/bin/nstaxsales-deploy
www-data ALL=(root) NOPASSWD: /usr/local/bin/nstaxsales-health
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl restart nginx
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl reload nginx
www-data ALL=(root) NOPASSWD: /usr/bin/pm2 restart *
www-data ALL=(root) NOPASSWD: /usr/bin/pm2 start *
www-data ALL=(root) NOPASSWD: /usr/bin/pm2 stop *
EOF

    # Set proper permissions
    chmod 440 /etc/sudoers.d/nstaxsales
    
    # Validate sudoers file
    if visudo -c -f /etc/sudoers.d/nstaxsales; then
        log "Sudoers configuration created successfully"
    else
        error "Sudoers configuration validation failed"
        rm -f /etc/sudoers.d/nstaxsales
        exit 1
    fi
}

# Function to setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/nstaxsales << 'EOF'
/var/log/tax-sale-*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    create 644 www-data www-data
}
EOF

    log "Log rotation configured"
}

# Function to create deployment status endpoint script
create_status_script() {
    log "Creating deployment status script..."
    
    cat > "$SCRIPT_DIR/deployment-status.sh" << 'EOF'
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

# Check if app directory exists
if [ -d "/var/www/nstaxsales" ]; then
    cd /var/www/nstaxsales
    
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
    "remote_commit": "$remote_commit"
}
EOJ
fi

cat "$status_file"
EOF

    chmod +x "$SCRIPT_DIR/deployment-status.sh"
    
    log "Deployment status script created"
}

# Function to setup cron jobs
setup_cron_jobs() {
    log "Setting up cron jobs..."
    
    # Create cron job for regular health checks
    cat > /etc/cron.d/nstaxsales << 'EOF'
# NST Tax Sales automation cron jobs
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Run health check every 30 minutes
*/30 * * * * root /var/www/nstaxsales/scripts/system-health.sh check >/dev/null 2>&1

# Check for updates daily at 2 AM
0 2 * * * root /var/www/nstaxsales/scripts/deployment.sh check-updates >/dev/null 2>&1
EOF

    log "Cron jobs configured"
}

# Function to test the setup
test_setup() {
    log "Testing setup..."
    
    # Test deployment script access
    if sudo -u www-data sudo /var/www/nstaxsales/scripts/deployment.sh verify 2>/dev/null; then
        log "✓ Deployment script access test passed"
    else
        warn "✗ Deployment script access test failed"
    fi
    
    # Test health script access
    if sudo -u www-data sudo /var/www/nstaxsales/scripts/system-health.sh summary 2>/dev/null; then
        log "✓ Health script access test passed"
    else
        warn "✗ Health script access test failed"
    fi
    
    # Test status script
    if "$SCRIPT_DIR/deployment-status.sh" >/dev/null 2>&1; then
        log "✓ Status script test passed"
    else
        warn "✗ Status script test failed"
    fi
    
    log "Setup testing completed"
}

# Main setup function
main() {
    log "Starting NST Tax Sales automation setup..."
    
    check_root
    setup_directories
    copy_scripts
    setup_sudoers
    setup_log_rotation
    create_status_script
    setup_cron_jobs
    test_setup
    
    log "Automation setup completed successfully!"
    log ""
    log "Available commands:"
    log "  tax-sale-deploy deploy [repo-url]  - Deploy latest version"
    log "  tax-sale-deploy check-updates      - Check for updates"
    log "  tax-sale-health check             - Run health check"
    log ""
    log "The backend API can now trigger deployments via the admin interface."
}

# Run main function
main "$@"