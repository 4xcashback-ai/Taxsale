#!/bin/bash

# Apply Scraper Configuration Migration
# This script applies the database migration for the scraper configuration system

set -e  # Exit on any error

echo "🚀 Applying Scraper Configuration Migration..."
echo "=================================================="

# Configuration
DB_NAME="tax_sale_compass"
MIGRATION_FILE="/app/database/add_scraper_config.sql"
BACKUP_DIR="/tmp"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Function to check if MySQL is running
check_mysql() {
    if ! mysql --version > /dev/null 2>&1; then
        echo "❌ MySQL client not found. Please install MySQL client."
        exit 1
    fi
    
    if ! mysql -e "SELECT 1;" > /dev/null 2>&1; then
        echo "❌ Cannot connect to MySQL. Please check your MySQL credentials."
        echo "   Make sure MySQL is running and credentials are correct."
        exit 1
    fi
    
    echo "✅ MySQL connection successful"
}

# Function to backup existing data (if table exists)
backup_existing_config() {
    echo "📦 Checking for existing scraper_config table..."
    
    if mysql -e "USE $DB_NAME; DESCRIBE scraper_config;" > /dev/null 2>&1; then
        echo "⚠️  scraper_config table already exists. Creating backup..."
        
        BACKUP_FILE="$BACKUP_DIR/scraper_config_backup_$TIMESTAMP.sql"
        mysqldump $DB_NAME scraper_config > "$BACKUP_FILE"
        
        echo "✅ Backup created: $BACKUP_FILE"
        return 0
    else
        echo "✅ No existing scraper_config table found. Proceeding with fresh installation."
        return 1
    fi
}

# Function to apply migration
apply_migration() {
    echo "🔧 Applying migration: $MIGRATION_FILE"
    
    if [ ! -f "$MIGRATION_FILE" ]; then
        echo "❌ Migration file not found: $MIGRATION_FILE"
        exit 1
    fi
    
    # Apply the migration
    mysql $DB_NAME < "$MIGRATION_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Migration applied successfully"
    else
        echo "❌ Migration failed"
        exit 1
    fi
}

# Function to verify migration
verify_migration() {
    echo "🔍 Verifying migration..."
    
    # Check table exists
    if ! mysql -e "USE $DB_NAME; DESCRIBE scraper_config;" > /dev/null 2>&1; then
        echo "❌ scraper_config table not found after migration"
        exit 1
    fi
    
    # Check record count
    RECORD_COUNT=$(mysql -N -e "USE $DB_NAME; SELECT COUNT(*) FROM scraper_config;")
    
    if [ "$RECORD_COUNT" -ge 3 ]; then
        echo "✅ Migration verified: $RECORD_COUNT configurations found"
        
        # Show the configurations
        echo "📋 Default configurations:"
        mysql -e "USE $DB_NAME; SELECT municipality, base_url, enabled FROM scraper_config ORDER BY municipality;"
    else
        echo "⚠️  Migration completed but expected default configurations not found"
        echo "   Found $RECORD_COUNT records, expected at least 3"
    fi
}

# Function to restart backend service
restart_backend() {
    echo "🔄 Restarting backend service..."
    
    if command -v supervisorctl > /dev/null 2>&1; then
        sudo supervisorctl restart backend
        
        # Wait a moment for service to start
        sleep 3
        
        # Check service status
        if sudo supervisorctl status backend | grep -q "RUNNING"; then
            echo "✅ Backend service restarted successfully"
        else
            echo "⚠️  Backend service may not have started properly"
            echo "   Check logs: sudo supervisorctl tail backend"
        fi
    else
        echo "⚠️  supervisorctl not found. Please restart backend service manually."
    fi
}

# Function to test configuration
test_configuration() {
    echo "🧪 Testing scraper configuration system..."
    
    # Test backend API (if curl is available)
    if command -v curl > /dev/null 2>&1; then
        echo "   Testing backend API endpoint..."
        
        # Simple health check first
        if curl -s -f http://localhost:8001/api/health > /dev/null; then
            echo "✅ Backend API is responding"
        else
            echo "⚠️  Backend API not responding on localhost:8001"
            echo "   This may be normal if running on different host/port"
        fi
    fi
    
    echo "✅ Basic tests completed"
}

# Main execution
main() {
    echo "Starting migration process..."
    echo
    
    # Step 1: Check MySQL
    check_mysql
    echo
    
    # Step 2: Backup existing data
    backup_existing_config
    echo
    
    # Step 3: Apply migration
    apply_migration
    echo
    
    # Step 4: Verify migration
    verify_migration
    echo
    
    # Step 5: Restart backend
    restart_backend
    echo
    
    # Step 6: Test configuration
    test_configuration
    echo
    
    echo "🎉 Migration completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Login to admin panel at /admin.php"
    echo "2. Navigate to 'Scraper Configuration' section"
    echo "3. Test each municipality configuration"
    echo "4. Update URLs and patterns as needed"
    echo
    echo "For detailed instructions, see: /app/database/MIGRATION_INSTRUCTIONS.md"
}

# Run main function
main "$@"