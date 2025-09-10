#!/bin/bash

# VPS Geocoding Update Script
# This script deploys the enhanced geocoding functionality and updates all properties
# Run this on your VPS after deploying the code changes

LOG_FILE="/var/log/taxsale_geocode_update.log"
VPS_API_BASE="http://localhost:8001/api"

echo "=== TAX SALE COMPASS - VPS GEOCODING UPDATE ===" | tee $LOG_FILE
echo "Started: $(date)" | tee -a $LOG_FILE
echo "Host: $(hostname)" | tee -a $LOG_FILE

# Function to check if backend is running
check_backend() {
    echo "Checking backend service..." | tee -a $LOG_FILE
    if curl -s "$VPS_API_BASE/health" > /dev/null 2>&1; then
        echo "✅ Backend service is running" | tee -a $LOG_FILE
        return 0
    else
        echo "❌ Backend service is not responding" | tee -a $LOG_FILE
        return 1
    fi
}

# Function to get admin token
get_admin_token() {
    echo "Getting admin authentication..." | tee -a $LOG_FILE
    ADMIN_TOKEN=$(curl -s -X POST "$VPS_API_BASE/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"email":"admin","password":"TaxSale2025!SecureAdmin"}' | jq -r '.access_token')
    
    if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
        echo "❌ Failed to get admin token" | tee -a $LOG_FILE
        return 1
    fi
    
    echo "✅ Admin authentication successful" | tee -a $LOG_FILE
    return 0
}

# Function to batch geocode properties
batch_geocode_properties() {
    echo "Finding properties that need geocoding..." | tee -a $LOG_FILE
    
    # Get all properties that need geocoding (no coordinates but have addresses)
    PROPERTIES_NEEDING_GEOCODING=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$VPS_API_BASE/tax-sales" | \
      jq -r '.[] | select(.latitude == null and .civic_address != null and .civic_address != "") | .assessment_number')
    
    if [ -z "$PROPERTIES_NEEDING_GEOCODING" ]; then
        echo "✅ All properties already have coordinates" | tee -a $LOG_FILE
        return 0
    fi
    
    # Count properties
    TOTAL_COUNT=$(echo "$PROPERTIES_NEEDING_GEOCODING" | wc -l)
    echo "Found $TOTAL_COUNT properties that need geocoding" | tee -a $LOG_FILE
    
    # Process each property
    PROCESSED_COUNT=0
    SUCCESS_COUNT=0
    FAILED_COUNT=0
    
    for ASSESSMENT_NUMBER in $PROPERTIES_NEEDING_GEOCODING; do
        PROCESSED_COUNT=$((PROCESSED_COUNT + 1))
        echo "Processing $PROCESSED_COUNT/$TOTAL_COUNT: $ASSESSMENT_NUMBER" | tee -a $LOG_FILE
        
        # Call the generate-boundary-thumbnail endpoint to trigger geocoding
        RESPONSE=$(curl -s -w "%{http_code}" -X POST "$VPS_API_BASE/generate-boundary-thumbnail/$ASSESSMENT_NUMBER")
        HTTP_CODE="${RESPONSE: -3}"
        RESPONSE_BODY="${RESPONSE%???}"
        
        if [ "$HTTP_CODE" == "200" ]; then
            # Check if geocoding was successful
            METHOD=$(echo "$RESPONSE_BODY" | jq -r '.method // "unknown"')
            if [ "$METHOD" == "address_based" ] || [ "$METHOD" == "pid_based" ]; then
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
                echo "  ✅ SUCCESS ($METHOD): $ASSESSMENT_NUMBER" | tee -a $LOG_FILE
            else
                FAILED_COUNT=$((FAILED_COUNT + 1))
                MESSAGE=$(echo "$RESPONSE_BODY" | jq -r '.message // "Unknown error"')
                echo "  ❌ FAILED: $ASSESSMENT_NUMBER - $MESSAGE" | tee -a $LOG_FILE
            fi
        else
            FAILED_COUNT=$((FAILED_COUNT + 1))
            ERROR_MSG=$(echo "$RESPONSE_BODY" | jq -r '.detail // "HTTP Error"')
            echo "  ❌ HTTP ERROR $HTTP_CODE: $ASSESSMENT_NUMBER - $ERROR_MSG" | tee -a $LOG_FILE
        fi
        
        # Add small delay to avoid overwhelming the API
        sleep 0.5
    done
    
    echo "" | tee -a $LOG_FILE
    echo "=== GEOCODING RESULTS ===" | tee -a $LOG_FILE
    echo "Total processed: $PROCESSED_COUNT" | tee -a $LOG_FILE
    echo "Successful: $SUCCESS_COUNT" | tee -a $LOG_FILE
    echo "Failed: $FAILED_COUNT" | tee -a $LOG_FILE
    
    return $FAILED_COUNT
}

# Function to get final statistics
get_final_stats() {
    echo "Getting final property statistics..." | tee -a $LOG_FILE
    
    TOTAL_PROPERTIES=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$VPS_API_BASE/tax-sales" | jq '. | length')
    PROPERTIES_WITH_COORDINATES=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$VPS_API_BASE/tax-sales" | jq '[.[] | select(.latitude != null)] | length')
    PROPERTIES_STILL_NEEDING=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$VPS_API_BASE/tax-sales" | jq '[.[] | select(.latitude == null and .civic_address != null and .civic_address != "")] | length')
    
    echo "" | tee -a $LOG_FILE
    echo "=== FINAL STATISTICS ===" | tee -a $LOG_FILE
    echo "Total properties: $TOTAL_PROPERTIES" | tee -a $LOG_FILE
    echo "Properties with coordinates: $PROPERTIES_WITH_COORDINATES" | tee -a $LOG_FILE
    echo "Properties still needing geocoding: $PROPERTIES_STILL_NEEDING" | tee -a $LOG_FILE
    
    if [ "$PROPERTIES_STILL_NEEDING" -eq 0 ]; then
        echo "🎉 SUCCESS: All properties now have coordinates for map display!" | tee -a $LOG_FILE
    else
        echo "⚠️  Warning: $PROPERTIES_STILL_NEEDING properties still need geocoding" | tee -a $LOG_FILE
    fi
}

# Main execution
echo "Step 1: Checking backend service..." | tee -a $LOG_FILE
if ! check_backend; then
    echo "❌ Backend service check failed. Make sure backend is deployed and running." | tee -a $LOG_FILE
    exit 1
fi

echo "Step 2: Getting admin authentication..." | tee -a $LOG_FILE
if ! get_admin_token; then
    echo "❌ Admin authentication failed. Check admin credentials." | tee -a $LOG_FILE
    exit 1
fi

echo "Step 3: Running batch geocoding..." | tee -a $LOG_FILE
batch_geocode_properties
GEOCODE_EXIT_CODE=$?

echo "Step 4: Getting final statistics..." | tee -a $LOG_FILE
get_final_stats

echo "" | tee -a $LOG_FILE
echo "=== VPS GEOCODING UPDATE COMPLETE ===" | tee -a $LOG_FILE
echo "Completed: $(date)" | tee -a $LOG_FILE
echo "Log file: $LOG_FILE" | tee -a $LOG_FILE

if [ $GEOCODE_EXIT_CODE -eq 0 ]; then
    echo "🎉 VPS geocoding update completed successfully!" | tee -a $LOG_FILE
    echo "All properties now have coordinates and will display on Google Maps." | tee -a $LOG_FILE
else
    echo "⚠️  Some properties could not be geocoded. Check the log for details." | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "Next steps:" | tee -a $LOG_FILE
echo "1. Visit your website to verify properties display on maps" | tee -a $LOG_FILE
echo "2. Check individual property pages for interactive maps" | tee -a $LOG_FILE
echo "3. Use admin panel to manage any remaining issues" | tee -a $LOG_FILE