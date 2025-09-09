#!/bin/bash

# Populate All PVSC Data Script
# This script runs comprehensive PVSC scraping for ALL properties

LOG_FILE="/var/log/taxsale_pvsc_population.log"
API_BASE_URL="http://localhost:8001/api"

echo "=== COMPREHENSIVE PVSC DATA POPULATION ===" | tee $LOG_FILE
echo "Started: $(date)" | tee -a $LOG_FILE

# Step 1: Get admin authentication
echo "Getting admin authentication..." | tee -a $LOG_FILE
ADMIN_TOKEN=$(curl -s -X POST "$API_BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin","password":"TaxSale2025!SecureAdmin"}' | jq -r '.access_token')

if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo "❌ Failed to get admin token" | tee -a $LOG_FILE
    exit 1
fi

echo "✅ Admin authentication successful" | tee -a $LOG_FILE

# Step 2: Check current database status
echo "Checking current PVSC data status..." | tee -a $LOG_FILE

TOTAL_PROPERTIES=$(mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass -s -N -e "SELECT COUNT(*) FROM properties;")
EXISTING_PVSC=$(mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass -s -N -e "SELECT COUNT(*) FROM pvsc_data;")

echo "📊 Current Status:" | tee -a $LOG_FILE
echo "   - Total properties: $TOTAL_PROPERTIES" | tee -a $LOG_FILE
echo "   - Properties with PVSC data: $EXISTING_PVSC" | tee -a $LOG_FILE

# Step 3: Clear existing test data (optional)
read -p "Do you want to clear existing PVSC test data and start fresh? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Clearing existing PVSC test data..." | tee -a $LOG_FILE
    mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass -e "DELETE FROM pvsc_data WHERE raw_json LIKE '%test%' OR scraped_at < DATE_SUB(NOW(), INTERVAL 1 HOUR);"
    echo "✅ Test data cleared" | tee -a $LOG_FILE
fi

# Step 4: Run comprehensive PVSC scraping
echo "🚀 Starting comprehensive PVSC data population..." | tee -a $LOG_FILE
echo "⏱️  This will process ALL $TOTAL_PROPERTIES properties" | tee -a $LOG_FILE
echo "⏱️  Estimated time: 2-3 seconds per property" | tee -a $LOG_FILE
echo "⏱️  Total estimated time: $((TOTAL_PROPERTIES * 3 / 60)) minutes" | tee -a $LOG_FILE

START_TIME=$(date +%s)

RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$API_BASE_URL/admin/scrape-pvsc-all")

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo "⏰ Scraping completed in ${MINUTES}m ${SECONDS}s" | tee -a $LOG_FILE

if echo "$RESPONSE" | jq -e . >/dev/null 2>&1; then
    # Parse results
    TOTAL_DB=$(echo "$RESPONSE" | jq -r '.total_properties_in_db // 0')
    EXISTING=$(echo "$RESPONSE" | jq -r '.existing_pvsc_records // 0')
    SCRAPED=$(echo "$RESPONSE" | jq -r '.scraping_result.scraped // 0')
    FAILED=$(echo "$RESPONSE" | jq -r '.scraping_result.failed // 0')
    SUCCESS_RATE=$(echo "$RESPONSE" | jq -r '.scraping_result.success_rate // "0%"')
    BATCHES=$(echo "$RESPONSE" | jq -r '.scraping_result.batches_processed // 0')
    
    echo "" | tee -a $LOG_FILE
    echo "🎉 COMPREHENSIVE PVSC POPULATION RESULTS:" | tee -a $LOG_FILE
    echo "   ✅ Total properties in database: $TOTAL_DB" | tee -a $LOG_FILE
    echo "   ✅ Already had PVSC data: $EXISTING" | tee -a $LOG_FILE
    echo "   ✅ Successfully scraped: $SCRAPED properties" | tee -a $LOG_FILE
    echo "   ❌ Failed to scrape: $FAILED properties" | tee -a $LOG_FILE
    echo "   📊 Success rate: $SUCCESS_RATE" | tee -a $LOG_FILE
    echo "   📦 Batches processed: $BATCHES" | tee -a $LOG_FILE
    
    # Final database check
    FINAL_PVSC_COUNT=$(mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass -s -N -e "SELECT COUNT(*) FROM pvsc_data;")
    echo "   🗄️  Total PVSC records now in database: $FINAL_PVSC_COUNT" | tee -a $LOG_FILE
    
    # Show sample of newly scraped data
    echo "" | tee -a $LOG_FILE
    echo "📋 Sample of recently scraped PVSC data:" | tee -a $LOG_FILE
    mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass -e "
        SELECT assessment_number, assessed_value, property_use, land_size, year_built, 
               DATE_FORMAT(scraped_at, '%Y-%m-%d %H:%i') as scraped
        FROM pvsc_data 
        WHERE scraped_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        ORDER BY scraped_at DESC 
        LIMIT 10;" | tee -a $LOG_FILE
    
    if [ "$SCRAPED" -gt 0 ]; then
        echo "" | tee -a $LOG_FILE
        echo "✅ SUCCESS: $SCRAPED new PVSC records added!" | tee -a $LOG_FILE
        echo "🎯 All property pages now have comprehensive PVSC data tables" | tee -a $LOG_FILE
    fi
else
    echo "❌ Scraping failed or returned invalid response" | tee -a $LOG_FILE
    echo "Response: $RESPONSE" | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "=== PVSC DATA POPULATION COMPLETE ===" | tee -a $LOG_FILE
echo "Completed: $(date)" | tee -a $LOG_FILE
echo "Log file: $LOG_FILE" | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "🎯 Next Steps:" | tee -a $LOG_FILE
echo "1. Visit property pages to see comprehensive PVSC data" | tee -a $LOG_FILE
echo "2. All properties now have detailed assessment information" | tee -a $LOG_FILE
echo "3. Data includes: assessed values, building details, sale history" | tee -a $LOG_FILE
echo "4. PVSC data is cached for 30 days - run monthly for updates" | tee -a $LOG_FILE