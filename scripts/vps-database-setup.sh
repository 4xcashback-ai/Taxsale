#!/bin/bash

# VPS Database Setup Script for Tax Sale Compass
# Ensures production database has all necessary indexes and structure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Configuration
PROJECT_ROOT="/var/www/tax-sale-compass"
BACKEND_DIR="$PROJECT_ROOT/backend"
PYTHON_VENV="$PROJECT_ROOT/.venv"

# Check if we're on VPS
check_vps_environment() {
    log "Checking VPS environment..."
    
    if [ ! -d "$PROJECT_ROOT" ]; then
        error "VPS project directory not found: $PROJECT_ROOT"
    fi
    
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        error "VPS environment file not found: $BACKEND_DIR/.env"
    fi
    
    success "VPS environment detected"
}

# Create database backup before changes
create_backup() {
    log "Creating database backup..."
    
    BACKUP_DIR="$PROJECT_ROOT/backups"
    BACKUP_FILE="$BACKUP_DIR/database_backup_$(date +%Y%m%d_%H%M%S).json"
    
    mkdir -p "$BACKUP_DIR"
    
    # Export database using mongodump (if available) or through Python script
    if command -v mongodump &> /dev/null; then
        log "Using mongodump for backup..."
        source "$BACKEND_DIR/.env"
        mongodump --uri="$MONGO_URL" --db="$DB_NAME" --out="$BACKUP_DIR/$(date +%Y%m%d_%H%M%S)"
        success "Database backup created with mongodump"
    else
        log "mongodump not available, creating Python backup..."
        cd "$BACKEND_DIR"
        source "$PYTHON_VENV/bin/activate"
        python -c "
import pymongo
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = pymongo.MongoClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]

backup_data = {}
for collection_name in db.list_collection_names():
    collection = db[collection_name]
    backup_data[collection_name] = list(collection.find())

with open('$BACKUP_FILE', 'w') as f:
    json.dump(backup_data, f, default=str, indent=2)

print('Backup created: $BACKUP_FILE')
"
        success "Database backup created: $BACKUP_FILE"
    fi
}

# Run index creation script
create_indexes() {
    log "Creating database indexes..."
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment
    if [ -f "$PYTHON_VENV/bin/activate" ]; then
        source "$PYTHON_VENV/bin/activate"
        success "Activated Python virtual environment"
    else
        warning "Virtual environment not found, using system Python"
    fi
    
    # Run index creation script
    if [ -f "create_database_indexes.py" ]; then
        python create_database_indexes.py
        success "Database indexes created successfully"
    else
        error "Index creation script not found: create_database_indexes.py"
    fi
}

# Verify database structure
verify_database() {
    log "Verifying database structure..."
    
    cd "$BACKEND_DIR"
    
    # Create verification script
    cat > verify_database.py << 'EOF'
import pymongo
import os
from dotenv import load_dotenv

load_dotenv()

def verify_database():
    client = pymongo.MongoClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # Expected collections
    expected_collections = ['tax_sales', 'municipalities', 'users', 'favorites']
    actual_collections = db.list_collection_names()
    
    print("📋 Database Verification Report")
    print("=" * 50)
    
    # Check collections
    for collection_name in expected_collections:
        if collection_name in actual_collections:
            collection = db[collection_name]
            doc_count = collection.count_documents({})
            index_count = len(list(collection.list_indexes()))
            print(f"✅ {collection_name}: {doc_count} docs, {index_count} indexes")
        else:
            print(f"❌ Missing collection: {collection_name}")
    
    # Check indexes on tax_sales (most critical)
    tax_sales = db.tax_sales
    indexes = [idx['name'] for idx in tax_sales.list_indexes()]
    expected_indexes = ['assessment_number_1', 'municipality_name_1', 'status_1']
    
    print("\n📊 Critical Indexes Check:")
    for index_name in expected_indexes:
        if index_name in indexes:
            print(f"✅ {index_name}")
        else:
            print(f"❌ Missing: {index_name}")
    
    # Test query performance
    print("\n⚡ Performance Test:")
    import time
    start_time = time.time()
    result = tax_sales.find_one({"assessment_number": {"$exists": True}})
    end_time = time.time()
    
    if result and (end_time - start_time) < 0.1:
        print("✅ Query performance: Excellent")
    elif result:
        print("⚠️ Query performance: Acceptable")
    else:
        print("❌ Query performance: Poor")
    
    print("\n🎉 Database verification complete!")

if __name__ == "__main__":
    verify_database()
EOF
    
    python verify_database.py
    rm verify_database.py
    
    success "Database verification completed"
}

# Test API endpoints to ensure everything is working
test_api_endpoints() {
    log "Testing API endpoints..."
    
    # Wait for services to restart
    sleep 5
    
    # Test basic endpoint
    if curl -f http://localhost:8001/api/ > /dev/null 2>&1; then
        success "API endpoint responding"
    else
        warning "API endpoint not responding, may need service restart"
    fi
    
    # Test municipalities endpoint (uses database)
    if curl -f http://localhost:8001/api/municipalities > /dev/null 2>&1; then
        success "Municipalities endpoint working"
    else
        warning "Municipalities endpoint issue detected"
    fi
}

# Restart services
restart_services() {
    log "Restarting services..."
    
    # Try PM2 first (VPS uses PM2)
    if command -v pm2 &> /dev/null; then
        pm2 restart tax-sale-backend || warning "PM2 backend restart failed"
        pm2 restart tax-sale-frontend || warning "PM2 frontend restart failed"
        success "Services restarted with PM2"
    # Try supervisor as fallback
    elif command -v supervisorctl &> /dev/null; then
        sudo supervisorctl restart backend || warning "Supervisor backend restart failed"
        sudo supervisorctl restart frontend || warning "Supervisor frontend restart failed"
        success "Services restarted with Supervisor"
    else
        warning "No service manager found, manual restart may be needed"
    fi
}

# Main execution
main() {
    log "🚀 Starting VPS Database Setup for Tax Sale Compass"
    echo ""
    
    check_vps_environment
    create_backup
    create_indexes
    verify_database
    restart_services
    test_api_endpoints
    
    echo ""
    success "🎉 VPS Database Setup Complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Verify application is working: https://your-domain.com"
    echo "  2. Test property search performance"
    echo "  3. Monitor database performance with new indexes"
    echo ""
    echo "Backup location: $PROJECT_ROOT/backups/"
    echo ""
}

# Print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-backup    Skip database backup creation"
    echo "  --verify-only    Only run database verification"
    echo "  --help           Show this help message"
    echo ""
    echo "This script sets up the production database with:"
    echo "  - Performance indexes on all collections"
    echo "  - Database structure verification"
    echo "  - Backup creation before changes"
    echo "  - Service restart after changes"
}

# Parse arguments
SKIP_BACKUP=false
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Execute based on options
if [ "$VERIFY_ONLY" = true ]; then
    check_vps_environment
    verify_database
else
    if [ "$SKIP_BACKUP" = false ]; then
        main
    else
        log "Skipping backup as requested"
        check_vps_environment
        create_indexes
        verify_database
        restart_services
        test_api_endpoints
        success "🎉 VPS Database Setup Complete (no backup)!"
    fi
fi