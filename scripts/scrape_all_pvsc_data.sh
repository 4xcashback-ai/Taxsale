#!/bin/bash

# Comprehensive PVSC Data Scraping Script
# This script scrapes PVSC data for ALL properties in the database

LOG_FILE="/var/log/taxsale_pvsc_comprehensive.log"
API_BASE_URL="http://localhost:8001/api"

echo "=== COMPREHENSIVE PVSC DATA SCRAPING ===" | tee $LOG_FILE
echo "Started: $(date)" | tee -a $LOG_FILE

# Function to get admin token
get_admin_token() {
    echo "Getting admin authentication..." | tee -a $LOG_FILE
    ADMIN_TOKEN=$(curl -s -X POST "$API_BASE_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"email":"admin","password":"TaxSale2025!SecureAdmin"}' | jq -r '.access_token')
    
    if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
        echo "❌ Failed to get admin token" | tee -a $LOG_FILE
        return 1
    fi
    
    echo "✅ Admin authentication successful" | tee -a $LOG_FILE
    return 0
}

# Function to get current database stats
get_database_stats() {
    echo "Getting database statistics..." | tee -a $LOG_FILE
    
    TOTAL_PROPERTIES=$(mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass -s -N -e "SELECT COUNT(*) FROM properties;")
    EXISTING_PVSC=$(mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass -s -N -e "SELECT COUNT(*) FROM pvsc_data;")
    MISSING_PVSC=$(mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass -s -N -e "
        SELECT COUNT(*) FROM properties p 
        LEFT JOIN pvsc_data pd ON p.assessment_number = pd.assessment_number 
        WHERE pd.assessment_number IS NULL;")
    
    echo "📊 Database Statistics:" | tee -a $LOG_FILE
    echo "   - Total properties: $TOTAL_PROPERTIES" | tee -a $LOG_FILE
    echo "   - Properties with PVSC data: $EXISTING_PVSC" | tee -a $LOG_FILE
    echo "   - Properties missing PVSC data: $MISSING_PVSC" | tee -a $LOG_FILE
    
    if [ "$MISSING_PVSC" -eq 0 ]; then
        echo "✅ All properties already have PVSC data!" | tee -a $LOG_FILE
        return 1
    fi
    
    return 0
}

# Function to run comprehensive scraping
run_comprehensive_scraping() {
    echo "🚀 Starting comprehensive PVSC scraping..." | tee -a $LOG_FILE
    echo "⏱️  This will process ALL properties with Assessment Numbers" | tee -a $LOG_FILE
    echo "⏱️  Estimated time: 1-2 seconds per property (respectful API usage)" | tee -a $LOG_FILE
    echo "⏱️  For $TOTAL_PROPERTIES properties, expect 10-30 minutes" | tee -a $LOG_FILE
    
    # Start the scraping
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
        echo "🎉 COMPREHENSIVE SCRAPING RESULTS:" | tee -a $LOG_FILE
        echo "   ✅ Total properties in database: $TOTAL_DB" | tee -a $LOG_FILE
        echo "   ✅ Already had PVSC data: $EXISTING" | tee -a $LOG_FILE
        echo "   ✅ Successfully scraped: $SCRAPED properties" | tee -a $LOG_FILE
        echo "   ❌ Failed to scrape: $FAILED properties" | tee -a $LOG_FILE
        echo "   📊 Success rate: $SUCCESS_RATE" | tee -a $LOG_FILE
        echo "   📦 Batches processed: $BATCHES" | tee -a $LOG_FILE
        
        # Final database check
        FINAL_PVSC_COUNT=$(mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass -s -N -e "SELECT COUNT(*) FROM pvsc_data;")
        echo "   🗄️  Total PVSC records now in database: $FINAL_PVSC_COUNT" | tee -a $LOG_FILE
        
        if [ "$SCRAPED" -gt 0 ]; then
            echo "" | tee -a $LOG_FILE
            echo "✅ SUCCESS: $SCRAPED new PVSC records added to database!" | tee -a $LOG_FILE
        fi
        
        return 0
    else
        echo "❌ Scraping failed or returned invalid response" | tee -a $LOG_FILE
        echo "Response: $RESPONSE" | tee -a $LOG_FILE
        return 1
    fi
}

# Function to show sample results
show_sample_results() {
    echo "" | tee -a $LOG_FILE
    echo "📋 Sample of recently scraped PVSC data:" | tee -a $LOG_FILE
    
    mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass -e "
        SELECT assessment_number, assessed_value, property_use, land_size, year_built, 
               DATE_FORMAT(scraped_at, '%Y-%m-%d %H:%i') as scraped
        FROM pvsc_data 
        ORDER BY scraped_at DESC 
        LIMIT 10;" | tee -a $LOG_FILE
}

# Main execution
echo "🏠 Tax Sale Compass - Comprehensive PVSC Data Scraping" | tee -a $LOG_FILE
echo "This script will scrape PVSC data for ALL properties in the database" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Step 1: Authenticate
if ! get_admin_token; then
    exit 1
fi

# Step 2: Check database stats
if ! get_database_stats; then
    echo "No scraping needed. Exiting." | tee -a $LOG_FILE
    exit 0
fi

# Step 3: Run comprehensive scraping
if ! run_comprehensive_scraping; then
    echo "❌ Comprehensive scraping failed" | tee -a $LOG_FILE
    exit 1
fi

# Step 4: Show sample results
show_sample_results

echo "" | tee -a $LOG_FILE
echo "=== COMPREHENSIVE PVSC SCRAPING COMPLETE ===" | tee -a $LOG_FILE
echo "Completed: $(date)" | tee -a $LOG_FILE
echo "Log file: $LOG_FILE" | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "🎯 Next Steps:" | tee -a $LOG_FILE
echo "1. Visit property pages to see comprehensive PVSC data" | tee -a $LOG_FILE
echo "2. All apartments and regular properties now have detailed information" | tee -a $LOG_FILE
echo "3. Data is cached for 30 days - re-run this script monthly for updates" | tee -a $LOG_FILE
echo "4. Individual properties will auto-refresh stale data when viewed" | tee -a $LOG_FILE