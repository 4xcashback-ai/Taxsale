#!/bin/bash

# Tax Sale Compass - System Health Check Script
# This script checks the health of all system components

set -e

# Configuration
APP_DIR="/var/www/nstaxsales"
LOG_FILE="/var/log/tax-sale-health.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check system resources
check_system_resources() {
    log "=== System Resources ==="
    
    # Check disk space
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    log "Disk usage: ${disk_usage}%"
    
    if [ "$disk_usage" -gt 90 ]; then
        log "WARNING: Disk usage is high (${disk_usage}%)"
    fi
    
    # Check memory usage
    local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    log "Memory usage: ${mem_usage}%"
    
    # Check load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}')
    log "Load average:$load_avg"
}

# Function to check services
check_services() {
    log "=== Service Status ==="
    
    # Check MongoDB
    if systemctl is-active --quiet mongod; then
        log "✓ MongoDB is running"
        # Check if we can connect
        if mongo --eval "db.adminCommand('ismaster')" >/dev/null 2>&1; then
            log "✓ MongoDB connection successful"
        else
            log "✗ MongoDB connection failed"
        fi
    else
        log "✗ MongoDB is not running"
    fi
    
    # Check Nginx
    if systemctl is-active --quiet nginx; then
        log "✓ Nginx is running"
        # Check configuration
        if nginx -t >/dev/null 2>&1; then
            log "✓ Nginx configuration is valid"
        else
            log "✗ Nginx configuration has errors"
        fi
    else
        log "✗ Nginx is not running"
    fi
    
    # Check PM2 processes
    if command -v pm2 >/dev/null 2>&1; then
        local pm2_status=$(pm2 jlist 2>/dev/null | jq -r '.[] | "\(.name): \(.pm2_env.status)"' 2>/dev/null || echo "PM2 status check failed")
        log "PM2 processes:"
        echo "$pm2_status" | while read line; do
            if [[ "$line" == *"online"* ]]; then
                log "✓ $line"
            else
                log "✗ $line"
            fi
        done
    else
        log "✗ PM2 is not installed"
    fi
}

# Function to check application endpoints
check_application_endpoints() {
    log "=== Application Endpoints ==="
    
    # Check backend health
    if curl -f -s -m 10 http://localhost:8001/api/health >/dev/null 2>&1; then
        log "✓ Backend health endpoint responding"
    else
        log "✗ Backend health endpoint not responding"
    fi
    
    # Check frontend
    if curl -f -s -m 10 http://localhost:3000 >/dev/null 2>&1; then
        log "✓ Frontend responding"
    else
        log "✗ Frontend not responding"
    fi
    
    # Check database connectivity through API
    if curl -f -s -m 10 http://localhost:8001/api/stats >/dev/null 2>&1; then
        log "✓ Database connectivity through API working"
    else
        log "✗ Database connectivity through API failed"
    fi
}

# Function to check SSL certificates
check_ssl_certificates() {
    log "=== SSL Certificates ==="
    
    local cert_path="/etc/letsencrypt/live/taxsalecompass.ca/cert.pem"
    
    if [ -f "$cert_path" ]; then
        local expiry_date=$(openssl x509 -enddate -noout -in "$cert_path" | cut -d= -f2)
        local expiry_epoch=$(date -d "$expiry_date" +%s)
        local current_epoch=$(date +%s)
        local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        log "SSL certificate expires in $days_until_expiry days ($expiry_date)"
        
        if [ "$days_until_expiry" -lt 30 ]; then
            log "WARNING: SSL certificate expires soon (${days_until_expiry} days)"
        elif [ "$days_until_expiry" -lt 7 ]; then
            log "CRITICAL: SSL certificate expires very soon (${days_until_expiry} days)"
        else
            log "✓ SSL certificate is valid"
        fi
    else
        log "✗ SSL certificate not found"
    fi
}

# Function to check log files for errors
check_logs_for_errors() {
    log "=== Recent Log Errors ==="
    
    # Check for recent errors in PM2 logs
    if ls /var/log/tax-sale-*.log >/dev/null 2>&1; then
        local recent_errors=$(grep -i "error\|failed\|exception" /var/log/tax-sale-*.log | tail -5)
        if [ -n "$recent_errors" ]; then
            log "Recent errors found in application logs:"
            echo "$recent_errors" | while read line; do
                log "  $line"
            done
        else
            log "✓ No recent errors in application logs"
        fi
    fi
    
    # Check nginx error log
    if [ -f "/var/log/nginx/error.log" ]; then
        local nginx_errors=$(tail -10 /var/log/nginx/error.log | grep -i "error" | tail -3)
        if [ -n "$nginx_errors" ]; then
            log "Recent Nginx errors:"
            echo "$nginx_errors" | while read line; do
                log "  $line"
            done
        else
            log "✓ No recent Nginx errors"
        fi
    fi
}

# Function to generate health summary
generate_health_summary() {
    log "=== Health Summary ==="
    
    local issues=0
    
    # Count issues from the log
    local error_count=$(grep -c "✗" "$LOG_FILE" 2>/dev/null || echo 0)
    local warning_count=$(grep -c "WARNING\|CRITICAL" "$LOG_FILE" 2>/dev/null || echo 0)
    
    if [ "$error_count" -eq 0 ] && [ "$warning_count" -eq 0 ]; then
        log "✓ System health: EXCELLENT - No issues detected"
        echo "EXCELLENT"
    elif [ "$error_count" -eq 0 ] && [ "$warning_count" -gt 0 ]; then
        log "⚠ System health: GOOD - $warning_count warnings detected"
        echo "GOOD"
    elif [ "$error_count" -gt 0 ] && [ "$error_count" -lt 3 ]; then
        log "⚠ System health: FAIR - $error_count errors, $warning_count warnings"
        echo "FAIR"
    else
        log "✗ System health: POOR - $error_count errors, $warning_count warnings"
        echo "POOR"
    fi
}

# Function to get system info
get_system_info() {
    log "=== System Information ==="
    
    log "Hostname: $(hostname)"
    log "OS: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Unknown")"
    log "Kernel: $(uname -r)"
    log "Uptime: $(uptime -p)"
    
    if [ -f "$APP_DIR/.git/refs/heads/main" ]; then
        local current_commit=$(git -C "$APP_DIR" rev-parse --short HEAD 2>/dev/null || echo "Unknown")
        log "Current commit: $current_commit"
    fi
}

# Main health check function
run_health_check() {
    # Clear previous log
    > "$LOG_FILE"
    
    log "Starting system health check..."
    
    get_system_info
    check_system_resources
    check_services
    check_application_endpoints
    check_ssl_certificates
    check_logs_for_errors
    
    local health_status=$(generate_health_summary)
    
    log "Health check completed. Status: $health_status"
    
    # Return appropriate exit code
    case "$health_status" in
        "EXCELLENT"|"GOOD")
            exit 0
            ;;
        "FAIR")
            exit 1
            ;;
        "POOR")
            exit 2
            ;;
    esac
}

# Function to show usage
usage() {
    echo "Usage: $0 {check|summary|info}"
    echo ""
    echo "Commands:"
    echo "  check    - Run complete health check"
    echo "  summary  - Show health summary only"
    echo "  info     - Show system information only"
}

# Main script logic
case "$1" in
    check)
        run_health_check
        ;;
    summary)
        generate_health_summary
        ;;
    info)
        get_system_info
        ;;
    *)
        usage
        exit 1
        ;;
esac