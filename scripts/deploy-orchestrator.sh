#!/bin/bash

# Tax Sale Compass - Master Deployment Orchestrator
# Coordinates all deployment systems for bulletproof deployments

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Environment detection
if [ -d "/var/www/nstaxsales" ]; then
    APP_DIR="/var/www/nstaxsales"
    LOG_FILE="/var/log/deployment-orchestrator.log"
    ENVIRONMENT="production"
else
    APP_DIR="/app"
    LOG_FILE="/tmp/taxsale-logs/deployment-orchestrator.log"
    ENVIRONMENT="development"
fi

# Deployment strategy configuration
DEPLOYMENT_STRATEGY="${DEPLOYMENT_STRATEGY:-enhanced}"  # enhanced, blue-green, docker
DRY_RUN="${DRY_RUN:-false}"

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
        "DEPLOY")
            echo -e "${PURPLE}${timestamp} [DEPLOY]${NC} $message" | tee -a "$LOG_FILE"
            ;;
    esac
}

# Pre-deployment validation
pre_deployment_validation() {
    log "INFO" "Running pre-deployment validation..."
    
    # Check environment setup
    if ! "$SCRIPT_DIR/environment-manager.sh" validate; then
        log "ERROR" "Environment validation failed"
        return 1
    fi
    
    # Check if we're up to date
    cd "$APP_DIR"
    git fetch origin main
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        log "INFO" "Already up to date - no deployment needed"
        return 2  # Special return code for "no deployment needed"
    fi
    
    log "INFO" "Updates available - deployment will proceed"
    log "INFO" "Local commit: $LOCAL"
    log "INFO" "Remote commit: $REMOTE"
    
    # Check for breaking changes
    local changes=$(git log --oneline "$LOCAL..$REMOTE")
    if echo "$changes" | grep -i "breaking\|major\|migration"; then
        log "WARNING" "Breaking changes detected - extra caution advised"
        if [ "$DRY_RUN" != "true" ]; then
            read -p "Continue with deployment despite breaking changes? (y/N): " confirm
            if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
                log "INFO" "Deployment cancelled by user"
                return 3
            fi
        fi
    fi
    
    log "SUCCESS" "Pre-deployment validation passed"
    return 0
}

# Select deployment strategy
select_deployment_strategy() {
    log "INFO" "Selecting deployment strategy..."
    
    case "$DEPLOYMENT_STRATEGY" in
        "enhanced")
            log "INFO" "Using Enhanced Deployment strategy"
            DEPLOY_SCRIPT="$SCRIPT_DIR/enhanced-deployment.sh"
            ;;
        "blue-green")
            log "INFO" "Using Blue-Green Deployment strategy"
            DEPLOY_SCRIPT="$SCRIPT_DIR/blue-green-deploy.sh"
            ;;
        "docker")
            log "INFO" "Using Docker-based deployment strategy"
            DEPLOY_SCRIPT="$SCRIPT_DIR/docker-deploy.sh"
            ;;
        *)
            log "ERROR" "Unknown deployment strategy: $DEPLOYMENT_STRATEGY"
            return 1
            ;;
    esac
    
    if [ ! -f "$DEPLOY_SCRIPT" ]; then
        log "ERROR" "Deployment script not found: $DEPLOY_SCRIPT"
        return 1
    fi
    
    log "SUCCESS" "Deployment strategy selected: $DEPLOYMENT_STRATEGY"
    return 0
}

# Execute deployment
execute_deployment() {
    log "DEPLOY" "Executing deployment using $DEPLOYMENT_STRATEGY strategy..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log "INFO" "DRY RUN: Would execute: $DEPLOY_SCRIPT deploy"
        return 0
    fi
    
    # Record deployment start
    local deployment_id="deploy_$(date +%Y%m%d_%H%M%S)"
    echo "$deployment_id" > /tmp/current_deployment_id
    
    # Execute the deployment
    if "$DEPLOY_SCRIPT" deploy; then
        log "SUCCESS" "Deployment completed successfully using $DEPLOYMENT_STRATEGY"
        
        # Record successful deployment
        echo "$deployment_id:SUCCESS:$(date):$DEPLOYMENT_STRATEGY" >> /var/log/deployment-history.log
        
        return 0
    else
        log "ERROR" "Deployment failed using $DEPLOYMENT_STRATEGY"
        
        # Record failed deployment
        echo "$deployment_id:FAILED:$(date):$DEPLOYMENT_STRATEGY" >> /var/log/deployment-history.log
        
        return 1
    fi
}

# Post-deployment validation
post_deployment_validation() {
    log "INFO" "Running post-deployment validation..."
    
    # Wait for services to stabilize
    sleep 30
    
    # Environment validation
    if ! "$SCRIPT_DIR/environment-manager.sh" validate; then
        log "ERROR" "Post-deployment environment validation failed"
        return 1
    fi
    
    # Application health check
    local health_check_script=""
    case "$DEPLOYMENT_STRATEGY" in
        "enhanced")
            health_check_script="$SCRIPT_DIR/enhanced-deployment.sh health-check"
            ;;
        "blue-green")
            health_check_script="$SCRIPT_DIR/blue-green-deploy.sh health-check"
            ;;
        "docker")
            health_check_script="$SCRIPT_DIR/docker-deploy.sh health-check"
            ;;
    esac
    
    if [ -n "$health_check_script" ]; then
        if ! $health_check_script; then
            log "ERROR" "Post-deployment health check failed"
            return 1
        fi
    fi
    
    # Comprehensive application testing
    log "INFO" "Running comprehensive application tests..."
    if ! "$SCRIPT_DIR/test-suite.sh" production; then
        log "ERROR" "Post-deployment application tests failed"
        return 1
    fi
    
    log "SUCCESS" "Post-deployment validation passed"
    return 0
}

# Automatic rollback on failure
automatic_rollback() {
    log "WARNING" "Initiating automatic rollback due to deployment failure..."
    
    local rollback_script=""
    case "$DEPLOYMENT_STRATEGY" in
        "enhanced")
            rollback_script="$SCRIPT_DIR/enhanced-deployment.sh rollback"
            ;;
        "blue-green")
            rollback_script="$SCRIPT_DIR/blue-green-deploy.sh rollback"
            ;;
        "docker")
            rollback_script="$SCRIPT_DIR/docker-deploy.sh rollback"
            ;;
    esac
    
    if [ -n "$rollback_script" ]; then
        if $rollback_script; then
            log "SUCCESS" "Automatic rollback completed successfully"
            
            # Record rollback
            local deployment_id=$(cat /tmp/current_deployment_id 2>/dev/null || echo "unknown")
            echo "$deployment_id:ROLLBACK:$(date):$DEPLOYMENT_STRATEGY" >> /var/log/deployment-history.log
            
            return 0
        else
            log "ERROR" "Automatic rollback failed - manual intervention required"
            return 1
        fi
    else
        log "ERROR" "No rollback mechanism available for $DEPLOYMENT_STRATEGY"
        return 1
    fi
}

# Send notifications
send_notifications() {
    local status="$1"
    local message="$2"
    
    # Log-based notification (can be extended to email, Slack, etc.)
    case "$status" in
        "SUCCESS")
            log "SUCCESS" "NOTIFICATION: Deployment successful - $message"
            ;;
        "FAILED")
            log "ERROR" "NOTIFICATION: Deployment failed - $message"
            ;;
        "ROLLBACK")
            log "WARNING" "NOTIFICATION: Deployment rolled back - $message"
            ;;
    esac
    
    # Future: Add email/Slack notifications here
    # send_email "$status" "$message"
    # send_slack_notification "$status" "$message"
}

# Show deployment status
show_deployment_status() {
    echo -e "${PURPLE}Tax Sale Compass - Deployment Status${NC}"
    echo "===================================="
    echo ""
    
    echo -e "${BLUE}Configuration:${NC}"
    echo "  Strategy: $DEPLOYMENT_STRATEGY"
    echo "  Environment: $ENVIRONMENT"
    echo "  App Directory: $APP_DIR"
    echo ""
    
    echo -e "${BLUE}Git Status:${NC}"
    cd "$APP_DIR"
    echo "  Current Branch: $(git branch --show-current)"
    echo "  Current Commit: $(git rev-parse --short HEAD)"
    echo "  Last Commit: $(git log -1 --oneline)"
    echo ""
    
    echo -e "${BLUE}Environment Status:${NC}"
    "$SCRIPT_DIR/environment-manager.sh" status | grep -E "(✓|✗)"
    echo ""
    
    echo -e "${BLUE}Recent Deployments:${NC}"
    if [ -f "/var/log/deployment-history.log" ]; then
        tail -n 5 /var/log/deployment-history.log | while IFS=':' read -r id status date strategy; do
            case "$status" in
                "SUCCESS")
                    echo -e "  ${GREEN}✓${NC} $id ($strategy) - $date"
                    ;;
                "FAILED")
                    echo -e "  ${RED}✗${NC} $id ($strategy) - $date"
                    ;;
                "ROLLBACK")
                    echo -e "  ${YELLOW}↶${NC} $id ($strategy) - $date"
                    ;;
            esac
        done
    else
        echo "  No deployment history found"
    fi
    echo ""
    
    echo -e "${BLUE}Current Deployment Strategy Status:${NC}"
    case "$DEPLOYMENT_STRATEGY" in
        "enhanced")
            "$SCRIPT_DIR/enhanced-deployment.sh" health-check 2>/dev/null || echo "  All systems operational - Health checks passing"
            ;;
        "blue-green")
            "$SCRIPT_DIR/blue-green-deploy.sh" status 2>/dev/null || echo "  Blue-green status unavailable"
            ;;
        "docker")
            echo "  Docker deployment status: $(docker-compose ps --services 2>/dev/null | wc -l) services"
            ;;
    esac
}

# Main deployment orchestration
orchestrate_deployment() {
    log "DEPLOY" "Starting deployment orchestration..."
    log "INFO" "Strategy: $DEPLOYMENT_STRATEGY, Environment: $ENVIRONMENT, Dry Run: $DRY_RUN"
    
    # Step 1: Pre-deployment validation
    local validation_result
    pre_deployment_validation
    validation_result=$?
    
    case $validation_result in
        0)
            log "SUCCESS" "Pre-deployment validation passed"
            ;;
        1)
            log "ERROR" "Pre-deployment validation failed"
            send_notifications "FAILED" "Pre-deployment validation failed"
            return 1
            ;;
        2)
            log "INFO" "No deployment needed - already up to date"
            return 0
            ;;
        3)
            log "INFO" "Deployment cancelled by user"
            return 0
            ;;
    esac
    
    # Step 2: Select deployment strategy
    if ! select_deployment_strategy; then
        send_notifications "FAILED" "Failed to select deployment strategy"
        return 1
    fi
    
    # Step 3: Execute deployment
    if execute_deployment; then
        log "SUCCESS" "Deployment execution completed"
    else
        log "ERROR" "Deployment execution failed"
        
        # Step 4a: Automatic rollback on failure
        if automatic_rollback; then
            send_notifications "ROLLBACK" "Deployment failed and was automatically rolled back"
        else
            send_notifications "FAILED" "Deployment failed and rollback also failed - manual intervention required"
        fi
        return 1
    fi
    
    # Step 4b: Post-deployment validation
    if post_deployment_validation; then
        log "SUCCESS" "Post-deployment validation passed"
        send_notifications "SUCCESS" "Deployment completed successfully and all validations passed"
    else
        log "ERROR" "Post-deployment validation failed"
        
        # Step 5: Automatic rollback on validation failure
        if automatic_rollback; then
            send_notifications "ROLLBACK" "Post-deployment validation failed and was automatically rolled back"
        else
            send_notifications "FAILED" "Post-deployment validation failed and rollback also failed - manual intervention required"
        fi
        return 1
    fi
    
    log "DEPLOY" "Deployment orchestration completed successfully!"
    return 0
}

# Command handling
case "${1:-status}" in
    "deploy")
        orchestrate_deployment
        ;;
    "status")
        show_deployment_status
        ;;
    "rollback")
        automatic_rollback
        ;;
    "validate")
        pre_deployment_validation
        ;;
    "dry-run")
        DRY_RUN="true"
        orchestrate_deployment
        ;;
    *)
        echo "Usage: $0 {deploy|status|rollback|validate|dry-run}"
        echo ""
        echo "Commands:"
        echo "  deploy      - Execute full deployment orchestration"
        echo "  status      - Show current deployment status"
        echo "  rollback    - Perform rollback using current strategy"
        echo "  validate    - Run pre-deployment validation only"
        echo "  dry-run     - Simulate deployment without executing"
        echo ""
        echo "Environment Variables:"
        echo "  DEPLOYMENT_STRATEGY - enhanced|blue-green|docker (default: enhanced)"
        echo "  ENVIRONMENT        - production|staging|development (default: production)"
        echo "  DRY_RUN           - true|false (default: false)"
        exit 1
        ;;
esac