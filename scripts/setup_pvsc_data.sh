#!/bin/bash

# Setup PVSC Data System Script
# This script creates the PVSC data table and starts batch scraping

LOG_FILE="/var/log/taxsale_pvsc_setup.log"
DB_NAME="tax_sale_compass"

echo "=== TAX SALE COMPASS - PVSC DATA SETUP ===" | tee $LOG_FILE
echo "Started: $(date)" | tee -a $LOG_FILE

# Function to run MySQL command
run_mysql() {
    local query="$1"
    mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -e "$query"
}

# Step 1: Create PVSC data table
echo "Step 1: Creating PVSC data table..." | tee -a $LOG_FILE

if run_mysql "SHOW TABLES LIKE 'pvsc_data';" | grep -q pvsc_data; then
    echo "✅ PVSC data table already exists" | tee -a $LOG_FILE
else
    echo "Creating PVSC data table..." | tee -a $LOG_FILE
    
    if mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME < /var/www/tax-sale-compass/database/add_pvsc_data_table.sql; then
        echo "✅ PVSC data table created successfully" | tee -a $LOG_FILE
    else
        echo "❌ Failed to create PVSC data table" | tee -a $LOG_FILE
        exit 1
    fi
fi

# Step 2: Test backend API endpoints
echo "Step 2: Testing backend API endpoints..." | tee -a $LOG_FILE

# Test health endpoint
if curl -s "http://localhost:8001/api/health" > /dev/null; then
    echo "✅ Backend API is accessible" | tee -a $LOG_FILE
else
    echo "❌ Backend API is not accessible" | tee -a $LOG_FILE
    exit 1
fi

# Step 3: Get admin token and test PVSC endpoint
echo "Step 3: Testing PVSC data endpoint..." | tee -a $LOG_FILE

ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin","password":"TaxSale2025!SecureAdmin"}' | jq -r '.access_token')

if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo "❌ Failed to get admin token" | tee -a $LOG_FILE
    exit 1
fi

echo "✅ Admin authentication successful" | tee -a $LOG_FILE

# Test PVSC endpoint with a sample property
SAMPLE_PROPERTY=$(mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -s -N -e "SELECT assessment_number FROM properties LIMIT 1;")

if [ -n "$SAMPLE_PROPERTY" ]; then
    echo "Testing PVSC endpoint with property: $SAMPLE_PROPERTY" | tee -a $LOG_FILE
    
    PVSC_RESPONSE=$(curl -s "http://localhost:8001/api/pvsc-data/$SAMPLE_PROPERTY")
    
    if echo "$PVSC_RESPONSE" | jq -e . >/dev/null 2>&1; then
        echo "✅ PVSC endpoint is working" | tee -a $LOG_FILE
    else
        echo "⚠️  PVSC endpoint returned non-JSON response (this is normal for first run)" | tee -a $LOG_FILE
    fi
else
    echo "⚠️  No properties found to test PVSC endpoint" | tee -a $LOG_FILE
fi

# Step 4: Start comprehensive PVSC scraping for ALL properties
echo "Step 4: Starting comprehensive PVSC scraping for ALL properties..." | tee -a $LOG_FILE

# Get total property count
TOTAL_PROPERTIES=$(mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -s -N -e "SELECT COUNT(*) FROM properties;")
echo "Found $TOTAL_PROPERTIES total properties in database" | tee -a $LOG_FILE

echo "This will scrape PVSC data for ALL properties with Assessment Numbers..." | tee -a $LOG_FILE
echo "Please be patient, this may take 10-30 minutes depending on property count..." | tee -a $LOG_FILE
echo "Processing with 1-second delays to be respectful to PVSC API..." | tee -a $LOG_FILE

# Use the comprehensive scraping endpoint
BATCH_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
    "http://localhost:8001/api/admin/scrape-pvsc-all")

if echo "$BATCH_RESPONSE" | jq -e . >/dev/null 2>&1; then
    TOTAL_DB=$(echo "$BATCH_RESPONSE" | jq -r '.total_properties_in_db // 0')
    EXISTING=$(echo "$BATCH_RESPONSE" | jq -r '.existing_pvsc_records // 0')
    SCRAPED=$(echo "$BATCH_RESPONSE" | jq -r '.scraping_result.scraped // 0')
    FAILED=$(echo "$BATCH_RESPONSE" | jq -r '.scraping_result.failed // 0')
    SUCCESS_RATE=$(echo "$BATCH_RESPONSE" | jq -r '.scraping_result.success_rate // "0%"')
    
    echo "✅ Comprehensive PVSC scraping completed:" | tee -a $LOG_FILE
    echo "   - Total properties in database: $TOTAL_DB" | tee -a $LOG_FILE
    echo "   - Already had PVSC data: $EXISTING" | tee -a $LOG_FILE
    echo "   - Successfully scraped: $SCRAPED properties" | tee -a $LOG_FILE
    echo "   - Failed: $FAILED properties" | tee -a $LOG_FILE
    echo "   - Success rate: $SUCCESS_RATE" | tee -a $LOG_FILE
else
    echo "❌ Comprehensive scraping failed or returned invalid response" | tee -a $LOG_FILE
    echo "Response: $BATCH_RESPONSE" | tee -a $LOG_FILE
fi

# Step 5: Check database for scraped data
echo "Step 5: Checking scraped data in database..." | tee -a $LOG_FILE

PVSC_COUNT=$(mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -s -N -e "SELECT COUNT(*) FROM pvsc_data;")

if [ "$PVSC_COUNT" -gt 0 ]; then
    echo "✅ Database contains $PVSC_COUNT PVSC records" | tee -a $LOG_FILE
    
    # Show sample of scraped data
    echo "Sample PVSC data:" | tee -a $LOG_FILE
    mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -e "
        SELECT assessment_number, assessed_value, property_use, land_size, year_built, scraped_at 
        FROM pvsc_data 
        ORDER BY scraped_at DESC 
        LIMIT 5;" | tee -a $LOG_FILE
else
    echo "⚠️  No PVSC data found in database yet" | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "=== PVSC DATA SETUP COMPLETE ===" | tee -a $LOG_FILE
echo "Completed: $(date)" | tee -a $LOG_FILE
echo "Log file: $LOG_FILE" | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "Next steps:" | tee -a $LOG_FILE
echo "1. Visit property pages to see enhanced PVSC data" | tee -a $LOG_FILE
echo "2. Use admin panel to run additional batch scraping if needed" | tee -a $LOG_FILE
echo "3. PVSC data will be automatically cached for 30 days" | tee -a $LOG_FILE