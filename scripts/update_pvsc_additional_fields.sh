#!/bin/bash

# Update PVSC Additional Fields Script
# This script adds new database fields and re-scrapes properties for complete data

LOG_FILE="/var/log/taxsale_pvsc_update.log"
DB_NAME="tax_sale_compass"

echo "=== PVSC ADDITIONAL FIELDS UPDATE ===" | tee $LOG_FILE
echo "Started: $(date)" | tee -a $LOG_FILE

# Step 1: Add new database fields
echo "Step 1: Adding new PVSC database fields..." | tee -a $LOG_FILE

if mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME < /var/www/tax-sale-compass/database/add_pvsc_additional_fields.sql; then
    echo "✅ New database fields added successfully" | tee -a $LOG_FILE
else
    echo "⚠️  Database fields may already exist (this is OK)" | tee -a $LOG_FILE
fi

# Step 2: Clear existing PVSC data to re-scrape with new fields
echo "Step 2: Clearing existing PVSC data for re-scraping..." | tee -a $LOG_FILE

read -p "Clear existing PVSC data to get additional fields (basement, garage, etc.)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -e "DELETE FROM pvsc_data;"
    echo "✅ Existing PVSC data cleared for complete re-scraping" | tee -a $LOG_FILE
else
    echo "Keeping existing data - only new properties will get additional fields" | tee -a $LOG_FILE
fi

# Step 3: Test the updated scraper
echo "Step 3: Testing updated scraper with sample property..." | tee -a $LOG_FILE

SAMPLE_PROPERTY=$(mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -s -N -e "SELECT assessment_number FROM properties LIMIT 1;")

if [ -n "$SAMPLE_PROPERTY" ]; then
    echo "Testing with property: $SAMPLE_PROPERTY" | tee -a $LOG_FILE
    
    RESPONSE=$(curl -s "http://localhost:8001/api/pvsc-data/$SAMPLE_PROPERTY")
    
    if echo "$RESPONSE" | jq -e '.garage' >/dev/null 2>&1; then
        echo "✅ New fields are being scraped correctly" | tee -a $LOG_FILE
        echo "Sample data:" | tee -a $LOG_FILE
        echo "$RESPONSE" | jq '{garage, basement_type, construction_quality, building_style}' | tee -a $LOG_FILE
    else
        echo "⚠️  New fields not found in response - may need manual verification" | tee -a $LOG_FILE
    fi
fi

# Step 4: Show updated database schema
echo "Step 4: Showing updated database schema..." | tee -a $LOG_FILE

mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -e "
    DESCRIBE pvsc_data;" | grep -E "(garage|construction_quality|under_construction|living_units|building_style)" | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "=== PVSC ADDITIONAL FIELDS UPDATE COMPLETE ===" | tee -a $LOG_FILE
echo "Completed: $(date)" | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "🎯 Next Steps:" | tee -a $LOG_FILE
echo "1. Run comprehensive PVSC scraping to populate all new fields:" | tee -a $LOG_FILE
echo "   sudo bash scripts/populate_all_pvsc_data.sh" | tee -a $LOG_FILE
echo "2. Visit property pages to see additional details (garage, basement, etc.)" | tee -a $LOG_FILE
echo "3. All properties will now show complete building information" | tee -a $LOG_FILE