#!/bin/bash

# Tax Sale Compass - Production Environment Management System
# Handles secure environment variable management and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Environment detection
if [ -d "/var/www/nstaxsales" ]; then
    APP_DIR="/var/www/nstaxsales"
    ENV_CONFIG_DIR="/etc/taxsale"
    SECURE_ENV_DIR="/var/lib/taxsale/secure"
else
    APP_DIR="/app"
    ENV_CONFIG_DIR="/tmp/taxsale-config"
    SECURE_ENV_DIR="/tmp/taxsale-secure"
fi

LOG_FILE="$ENV_CONFIG_DIR/environment.log"

# Create necessary directories
mkdir -p "$ENV_CONFIG_DIR" "$SECURE_ENV_DIR"
chmod 700 "$SECURE_ENV_DIR"  # Secure permissions

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

# Production Environment Templates
create_production_env_template() {
    log "INFO" "Creating production environment templates..."
    
    # Backend environment template
    cat > "$ENV_CONFIG_DIR/backend.env.template" << 'EOF'
# Backend Environment Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="taxsalecompass_production"
CORS_ORIGINS="https://taxsalecompass.ca,https://www.taxsalecompass.ca"

# Authentication Configuration
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="CHANGE_THIS_IN_PRODUCTION"
JWT_SECRET_KEY="GENERATE_SECURE_KEY_IN_PRODUCTION"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Google Maps API
GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY"

# Optional: Additional security settings
# ALLOWED_HOSTS="taxsalecompass.ca,www.taxsalecompass.ca"
# SSL_REDIRECT=true
# SESSION_COOKIE_SECURE=true
EOF

    # Frontend environment template
    cat > "$ENV_CONFIG_DIR/frontend.env.template" << 'EOF'
# Frontend Environment Configuration
REACT_APP_BACKEND_URL="https://taxsalecompass.ca"
REACT_APP_GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY"

# Optional: Analytics and monitoring
# REACT_APP_GOOGLE_ANALYTICS_ID="G-XXXXXXXXXX"
# REACT_APP_SENTRY_DSN="https://your-sentry-dsn"
EOF

    log "SUCCESS" "Environment templates created in $ENV_CONFIG_DIR"
}

# Generate secure secrets
generate_secure_secrets() {
    log "INFO" "Generating secure secrets..."
    
    # Generate JWT secret key
    local jwt_secret=$(openssl rand -base64 64 | tr -d '\n')
    
    # Generate admin password
    local admin_password=$(openssl rand -base64 24 | tr -d '\n')
    
    # Save secrets securely
    cat > "$SECURE_ENV_DIR/jwt_secret.key" << EOF
$jwt_secret
EOF
    
    cat > "$SECURE_ENV_DIR/admin_password.key" << EOF
$admin_password
EOF
    
    chmod 600 "$SECURE_ENV_DIR"/*.key
    
    log "SUCCESS" "Secure secrets generated and stored in $SECURE_ENV_DIR"
    log "WARNING" "Admin password: $admin_password"
    log "WARNING" "Please save this password securely and change the default!"
}

# Initialize production environment
initialize_production_environment() {
    log "INFO" "Initializing production environment configuration..."
    
    # Create templates
    create_production_env_template
    
    # Generate secrets if not exist
    if [ ! -f "$SECURE_ENV_DIR/jwt_secret.key" ]; then
        generate_secure_secrets
    fi
    
    # Create actual environment files from templates
    local jwt_secret=$(cat "$SECURE_ENV_DIR/jwt_secret.key" 2>/dev/null || echo "PLEASE_GENERATE_SECURE_KEY")
    local admin_password=$(cat "$SECURE_ENV_DIR/admin_password.key" 2>/dev/null || echo "PLEASE_CHANGE_PASSWORD")
    
    # Create backend .env (using different delimiter to handle special characters)
    sed -e "s|GENERATE_SECURE_KEY_IN_PRODUCTION|$jwt_secret|g" \
        -e "s|CHANGE_THIS_IN_PRODUCTION|$admin_password|g" \
        "$ENV_CONFIG_DIR/backend.env.template" > "$ENV_CONFIG_DIR/backend.env.production"
    
    # Create frontend .env (no secrets to replace)
    cp "$ENV_CONFIG_DIR/frontend.env.template" "$ENV_CONFIG_DIR/frontend.env.production"
    
    log "SUCCESS" "Production environment files created"
}

# Deploy environment configuration
deploy_environment_config() {
    log "INFO" "Deploying environment configuration to application..."
    
    if [ ! -f "$ENV_CONFIG_DIR/backend.env.production" ] || [ ! -f "$ENV_CONFIG_DIR/frontend.env.production" ]; then
        log "ERROR" "Production environment files not found. Run 'initialize' first."
        return 1
    fi
    
    # Backup existing environment files
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    if [ -f "$APP_DIR/backend/.env" ]; then
        cp "$APP_DIR/backend/.env" "$ENV_CONFIG_DIR/backend.env.backup.$backup_timestamp"
        log "INFO" "Backed up existing backend .env"
    fi
    
    if [ -f "$APP_DIR/frontend/.env" ]; then
        cp "$APP_DIR/frontend/.env" "$ENV_CONFIG_DIR/frontend.env.backup.$backup_timestamp"
        log "INFO" "Backed up existing frontend .env"
    fi
    
    # Deploy new environment files
    cp "$ENV_CONFIG_DIR/backend.env.production" "$APP_DIR/backend/.env"
    cp "$ENV_CONFIG_DIR/frontend.env.production" "$APP_DIR/frontend/.env"
    
    # Set appropriate permissions
    chmod 600 "$APP_DIR/backend/.env"
    chmod 644 "$APP_DIR/frontend/.env"
    
    log "SUCCESS" "Environment configuration deployed successfully"
}

# Validate environment configuration
validate_environment_config() {
    log "INFO" "Validating environment configuration..."
    
    local validation_failed=0
    
    # Validate backend environment
    if [ -f "$APP_DIR/backend/.env" ]; then
        log "INFO" "Validating backend environment..."
        
        # Check required variables
        local required_vars=("MONGO_URL" "DB_NAME" "ADMIN_USERNAME" "ADMIN_PASSWORD" "JWT_SECRET_KEY")
        for var in "${required_vars[@]}"; do
            if ! grep -q "^$var=" "$APP_DIR/backend/.env"; then
                log "ERROR" "Missing required backend variable: $var"
                validation_failed=1
            fi
        done
        
        # Check for default/insecure values
        if grep -q "CHANGE_THIS_IN_PRODUCTION" "$APP_DIR/backend/.env"; then
            log "ERROR" "Backend contains default insecure values"
            validation_failed=1
        fi
        
        if grep -q "GENERATE_SECURE_KEY_IN_PRODUCTION" "$APP_DIR/backend/.env"; then
            log "ERROR" "Backend contains placeholder values"
            validation_failed=1
        fi
        
        # Validate JWT secret strength
        local jwt_secret=$(grep "^JWT_SECRET_KEY=" "$APP_DIR/backend/.env" | cut -d'=' -f2)
        if [ ${#jwt_secret} -lt 32 ]; then
            log "ERROR" "JWT secret key is too short (minimum 32 characters)"
            validation_failed=1
        fi
        
        log "SUCCESS" "Backend environment validation completed"
    else
        log "ERROR" "Backend .env file not found"
        validation_failed=1
    fi
    
    # Validate frontend environment
    if [ -f "$APP_DIR/frontend/.env" ]; then
        log "INFO" "Validating frontend environment..."
        
        # Check required variables
        if ! grep -q "^REACT_APP_BACKEND_URL=" "$APP_DIR/frontend/.env"; then
            log "ERROR" "Missing REACT_APP_BACKEND_URL in frontend .env"
            validation_failed=1
        fi
        
        # Validate backend URL format
        local backend_url=$(grep "^REACT_APP_BACKEND_URL=" "$APP_DIR/frontend/.env" | cut -d'=' -f2)
        if [[ ! "$backend_url" =~ ^https?://[a-zA-Z0-9.-]+$ ]]; then
            log "ERROR" "Invalid REACT_APP_BACKEND_URL format: $backend_url"
            validation_failed=1
        fi
        
        # Check for development URLs in production
        if echo "$backend_url" | grep -q -E "(localhost|127\.0\.0\.1|preview\.emergentagent\.com)"; then
            log "WARNING" "Frontend backend URL appears to be for development: $backend_url"
        fi
        
        log "SUCCESS" "Frontend environment validation completed"
    else
        log "ERROR" "Frontend .env file not found"
        validation_failed=1
    fi
    
    if [ $validation_failed -eq 1 ]; then
        log "ERROR" "Environment validation failed"
        return 1
    fi
    
    log "SUCCESS" "All environment validation checks passed"
    return 0
}

# Monitor environment drift
monitor_environment_drift() {
    log "INFO" "Monitoring environment configuration drift..."
    
    # Check if current environment matches production templates
    if [ -f "$ENV_CONFIG_DIR/backend.env.production" ] && [ -f "$APP_DIR/backend/.env" ]; then
        if ! cmp -s "$ENV_CONFIG_DIR/backend.env.production" "$APP_DIR/backend/.env"; then
            log "WARNING" "Backend environment has drifted from production configuration"
            log "INFO" "Differences found:"
            diff "$ENV_CONFIG_DIR/backend.env.production" "$APP_DIR/backend/.env" | head -10 | tee -a "$LOG_FILE"
        else
            log "SUCCESS" "Backend environment matches production configuration"
        fi
    fi
    
    if [ -f "$ENV_CONFIG_DIR/frontend.env.production" ] && [ -f "$APP_DIR/frontend/.env" ]; then
        if ! cmp -s "$ENV_CONFIG_DIR/frontend.env.production" "$APP_DIR/frontend/.env"; then
            log "WARNING" "Frontend environment has drifted from production configuration"
            log "INFO" "Differences found:"
            diff "$ENV_CONFIG_DIR/frontend.env.production" "$APP_DIR/frontend/.env" | head -10 | tee -a "$LOG_FILE"
        else
            log "SUCCESS" "Frontend environment matches production configuration"
        fi
    fi
}

# Show environment status
show_environment_status() {
    log "INFO" "Environment Configuration Status"
    echo "=================================="
    
    echo -e "${BLUE}Configuration Directory:${NC} $ENV_CONFIG_DIR"
    echo -e "${BLUE}Secure Directory:${NC} $SECURE_ENV_DIR"
    echo -e "${BLUE}Application Directory:${NC} $APP_DIR"
    echo ""
    
    echo -e "${BLUE}Templates:${NC}"
    [ -f "$ENV_CONFIG_DIR/backend.env.template" ] && echo "  ✓ Backend template" || echo "  ✗ Backend template"
    [ -f "$ENV_CONFIG_DIR/frontend.env.template" ] && echo "  ✓ Frontend template" || echo "  ✗ Frontend template"
    echo ""
    
    echo -e "${BLUE}Production Files:${NC}"
    [ -f "$ENV_CONFIG_DIR/backend.env.production" ] && echo "  ✓ Backend production" || echo "  ✗ Backend production"
    [ -f "$ENV_CONFIG_DIR/frontend.env.production" ] && echo "  ✓ Frontend production" || echo "  ✗ Frontend production"
    echo ""
    
    echo -e "${BLUE}Deployed Files:${NC}"
    [ -f "$APP_DIR/backend/.env" ] && echo "  ✓ Backend deployed" || echo "  ✗ Backend deployed"
    [ -f "$APP_DIR/frontend/.env" ] && echo "  ✓ Frontend deployed" || echo "  ✗ Frontend deployed"
    echo ""
    
    echo -e "${BLUE}Security:${NC}"
    [ -f "$SECURE_ENV_DIR/jwt_secret.key" ] && echo "  ✓ JWT secret generated" || echo "  ✗ JWT secret missing"
    [ -f "$SECURE_ENV_DIR/admin_password.key" ] && echo "  ✓ Admin password generated" || echo "  ✗ Admin password missing"
    echo ""
    
    if [ -f "$APP_DIR/backend/.env" ]; then
        echo -e "${BLUE}Current Backend URL:${NC}"
        grep "^REACT_APP_BACKEND_URL=" "$APP_DIR/frontend/.env" 2>/dev/null | cut -d'=' -f2 || echo "  Not configured"
    fi
}

# Command handling
case "${1:-status}" in
    "initialize")
        initialize_production_environment
        ;;
    "deploy")
        deploy_environment_config
        ;;
    "validate")
        validate_environment_config
        ;;
    "monitor")
        monitor_environment_drift
        ;;
    "status")
        show_environment_status
        ;;
    "generate-secrets")
        generate_secure_secrets
        ;;
    *)
        echo "Usage: $0 {initialize|deploy|validate|monitor|status|generate-secrets}"
        echo ""
        echo "Commands:"
        echo "  initialize      - Create production environment templates and secrets"
        echo "  deploy          - Deploy environment configuration to application"
        echo "  validate        - Validate current environment configuration"
        echo "  monitor         - Check for environment configuration drift"
        echo "  status          - Show environment configuration status"
        echo "  generate-secrets - Generate new secure secrets"
        exit 1
        ;;
esac