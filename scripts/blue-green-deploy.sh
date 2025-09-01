#!/bin/bash

# Tax Sale Compass - Blue-Green Deployment System
# Zero-downtime deployments with automatic rollback

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
APP_NAME="taxsale-compass"
DOCKER_COMPOSE_FILE="/var/www/nstaxsales/docker/docker-compose.production.yml"
NGINX_CONFIG_DIR="/etc/nginx/sites-available"
LOG_FILE="/var/log/blue-green-deployment.log"

# Current deployment tracking
CURRENT_COLOR_FILE="/var/lib/taxsale/current_color"
mkdir -p "$(dirname "$CURRENT_COLOR_FILE")"

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
    esac
}

# Get current deployment color
get_current_color() {
    if [ -f "$CURRENT_COLOR_FILE" ]; then
        cat "$CURRENT_COLOR_FILE"
    else
        echo "blue"  # Default to blue for first deployment
    fi
}

# Get next deployment color
get_next_color() {
    local current=$(get_current_color)
    if [ "$current" = "blue" ]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Set current deployment color
set_current_color() {
    echo "$1" > "$CURRENT_COLOR_FILE"
}

# Health check function
health_check() {
    local service_name="$1"
    local max_attempts=30
    local attempt=1
    
    log "INFO" "Performing health check for $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" -p "${APP_NAME}-${service_name}" \
           exec -T taxsale-app curl -f -s http://localhost/api/health > /dev/null 2>&1; then
            log "SUCCESS" "Health check passed for $service_name (attempt $attempt)"
            return 0
        fi
        
        log "INFO" "Health check attempt $attempt/$max_attempts for $service_name..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log "ERROR" "Health check failed for $service_name after $max_attempts attempts"
    return 1
}

# Comprehensive application test
comprehensive_test() {
    local service_name="$1"
    local base_url="http://localhost:$(get_service_port $service_name)"
    
    log "INFO" "Running comprehensive tests for $service_name..."
    
    # Test 1: Health endpoint
    if ! curl -f -s "$base_url/api/health" > /dev/null; then
        log "ERROR" "Health endpoint test failed"
        return 1
    fi
    
    # Test 2: Authentication endpoint
    local auth_response=$(curl -s -X POST "$base_url/api/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"test","password":"test"}' || echo "")
    
    if ! echo "$auth_response" | grep -q "Incorrect username"; then
        log "ERROR" "Authentication endpoint test failed"
        return 1
    fi
    
    # Test 3: Database connectivity
    if ! curl -f -s "$base_url/api/municipalities" > /dev/null; then
        log "ERROR" "Database connectivity test failed"
        return 1
    fi
    
    # Test 4: Frontend serving
    if ! curl -f -s "$base_url/" | grep -q "<!DOCTYPE html>"; then
        log "ERROR" "Frontend serving test failed"
        return 1
    fi
    
    log "SUCCESS" "All comprehensive tests passed for $service_name"
    return 0
}

# Get service port for testing
get_service_port() {
    local color="$1"
    if [ "$color" = "blue" ]; then
        echo "8001"
    else
        echo "8002"
    fi
}

# Deploy new version
deploy_new_version() {
    local next_color=$(get_next_color)
    local current_color=$(get_current_color)
    
    log "INFO" "Starting blue-green deployment: $current_color -> $next_color"
    
    # Step 1: Build new version
    log "INFO" "Building $next_color deployment..."
    
    # Create environment-specific docker-compose file
    local compose_file="/tmp/docker-compose.${next_color}.yml"
    sed "s/taxsale-app/${APP_NAME}-${next_color}-app/g" "$DOCKER_COMPOSE_FILE" > "$compose_file"
    sed -i "s/80:80/$(get_service_port $next_color):80/g" "$compose_file"
    
    # Pull latest code and build
    cd /var/www/nstaxsales
    git pull origin main
    
    # Build new version
    if ! docker-compose -f "$compose_file" -p "${APP_NAME}-${next_color}" build; then
        log "ERROR" "Failed to build $next_color deployment"
        return 1
    fi
    
    # Step 2: Start new version
    log "INFO" "Starting $next_color deployment..."
    if ! docker-compose -f "$compose_file" -p "${APP_NAME}-${next_color}" up -d; then
        log "ERROR" "Failed to start $next_color deployment"
        return 1
    fi
    
    # Step 3: Wait for service to be ready
    sleep 30
    
    # Step 4: Health check
    if ! health_check "$next_color"; then
        log "ERROR" "Health check failed for $next_color deployment"
        log "INFO" "Rolling back..."
        docker-compose -f "$compose_file" -p "${APP_NAME}-${next_color}" down
        return 1
    fi
    
    # Step 5: Comprehensive testing
    if ! comprehensive_test "$next_color"; then
        log "ERROR" "Comprehensive tests failed for $next_color deployment"
        log "INFO" "Rolling back..."
        docker-compose -f "$compose_file" -p "${APP_NAME}-${next_color}" down
        return 1
    fi
    
    # Step 6: Switch traffic (update nginx configuration)
    log "INFO" "Switching traffic to $next_color deployment..."
    update_nginx_config "$next_color"
    
    # Step 7: Verify traffic switch worked
    sleep 10
    if ! curl -f -s "http://localhost/api/health" > /dev/null; then
        log "ERROR" "Traffic switch verification failed"
        log "INFO" "Rolling back nginx configuration..."
        update_nginx_config "$current_color"
        docker-compose -f "$compose_file" -p "${APP_NAME}-${next_color}" down
        return 1
    fi
    
    # Step 8: Shutdown old version (after delay for connection draining)
    log "INFO" "Draining connections from $current_color deployment..."
    sleep 60  # Allow existing connections to complete
    
    local old_compose_file="/tmp/docker-compose.${current_color}.yml"
    if [ -f "$old_compose_file" ]; then
        docker-compose -f "$old_compose_file" -p "${APP_NAME}-${current_color}" down
    fi
    
    # Step 9: Update current color
    set_current_color "$next_color"
    
    # Step 10: Cleanup
    rm -f "$compose_file" "$old_compose_file"
    
    log "SUCCESS" "Blue-green deployment completed successfully: $current_color -> $next_color"
    return 0
}

# Update nginx configuration for traffic switching
update_nginx_config() {
    local active_color="$1"
    local port=$(get_service_port "$active_color")
    
    log "INFO" "Updating nginx configuration for $active_color deployment on port $port"
    
    # Create nginx configuration
    cat > "$NGINX_CONFIG_DIR/taxsale-compass" << EOF
upstream taxsale_backend {
    server 127.0.0.1:$port;
}

server {
    listen 80;
    server_name taxsalecompass.ca www.taxsalecompass.ca;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Proxy to active deployment
    location / {
        proxy_pass http://taxsale_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check endpoint (bypass proxy)
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Enable site and reload nginx
    ln -sf "$NGINX_CONFIG_DIR/taxsale-compass" /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
}

# Status command
show_status() {
    local current_color=$(get_current_color)
    
    echo -e "${BLUE}Blue-Green Deployment Status${NC}"
    echo "============================"
    echo -e "${BLUE}Current Active:${NC} $current_color"
    echo -e "${BLUE}Next Deployment:${NC} $(get_next_color)"
    echo ""
    
    echo -e "${BLUE}Running Services:${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" -p "${APP_NAME}-blue" ps 2>/dev/null || echo "  Blue: Not running"
    docker-compose -f "$DOCKER_COMPOSE_FILE" -p "${APP_NAME}-green" ps 2>/dev/null || echo "  Green: Not running"
    echo ""
    
    echo -e "${BLUE}Nginx Configuration:${NC}"
    if [ -f "$NGINX_CONFIG_DIR/taxsale-compass" ]; then
        local active_port=$(grep "server 127.0.0.1:" "$NGINX_CONFIG_DIR/taxsale-compass" | grep -o "[0-9]*")
        if [ "$active_port" = "8001" ]; then
            echo "  Traffic routed to: Blue (port 8001)"
        elif [ "$active_port" = "8002" ]; then
            echo "  Traffic routed to: Green (port 8002)"
        else
            echo "  Traffic routing: Unknown"
        fi
    else
        echo "  Nginx config: Not found"
    fi
}

# Rollback to previous version
rollback() {
    local current_color=$(get_current_color)
    local previous_color=$(get_next_color)  # Since next is actually previous in this context
    
    log "WARNING" "Performing rollback: $current_color -> $previous_color"
    
    # Check if previous version is still running
    local prev_compose_file="/tmp/docker-compose.${previous_color}.yml"
    if ! docker-compose -f "$prev_compose_file" -p "${APP_NAME}-${previous_color}" ps | grep -q "Up"; then
        log "ERROR" "Previous version ($previous_color) is not running - cannot rollback"
        return 1
    fi
    
    # Switch traffic back
    update_nginx_config "$previous_color"
    
    # Verify rollback worked
    sleep 10
    if health_check "$previous_color"; then
        set_current_color "$previous_color"
        log "SUCCESS" "Rollback completed successfully"
        return 0
    else
        log "ERROR" "Rollback verification failed"
        return 1
    fi
}

# Command handling
case "${1:-status}" in
    "deploy")
        deploy_new_version
        ;;
    "status")
        show_status
        ;;
    "rollback")
        rollback
        ;;
    "health-check")
        current_color=$(get_current_color)
        health_check "$current_color"
        ;;
    "test")
        current_color=$(get_current_color)
        comprehensive_test "$current_color"
        ;;
    *)
        echo "Usage: $0 {deploy|status|rollback|health-check|test}"
        echo ""
        echo "Commands:"
        echo "  deploy      - Deploy new version using blue-green strategy"
        echo "  status      - Show current deployment status"
        echo "  rollback    - Rollback to previous version"
        echo "  health-check - Check health of current deployment"
        echo "  test        - Run comprehensive tests on current deployment"
        exit 1
        ;;
esac