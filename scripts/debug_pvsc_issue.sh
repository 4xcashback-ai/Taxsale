#!/bin/bash

# Debug PVSC Loading Issue Script
# This script helps diagnose why PVSC data is showing "loading" instead of database data

LOG_FILE="/tmp/pvsc_debug.log"
DB_NAME="tax_sale_compass"

echo "=== PVSC LOADING ISSUE DEBUG ===" | tee $LOG_FILE
echo "Started: $(date)" | tee -a $LOG_FILE

echo "1. Checking if PVSC table exists..." | tee -a $LOG_FILE
if mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -e "SHOW TABLES LIKE 'pvsc_data';" | grep -q pvsc_data; then
    echo "✅ PVSC table exists" | tee -a $LOG_FILE
    
    # Check table structure
    echo "   Table structure:" | tee -a $LOG_FILE
    mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -e "DESCRIBE pvsc_data;" | head -10 | tee -a $LOG_FILE
    
    # Check data count
    PVSC_COUNT=$(mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -s -N -e "SELECT COUNT(*) FROM pvsc_data;")
    echo "   Records in PVSC table: $PVSC_COUNT" | tee -a $LOG_FILE
    
    if [ "$PVSC_COUNT" -gt 0 ]; then
        echo "   Sample PVSC data:" | tee -a $LOG_FILE
        mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -e "
            SELECT assessment_number, assessed_value, property_use, scraped_at 
            FROM pvsc_data 
            LIMIT 3;" | tee -a $LOG_FILE
    fi
else
    echo "❌ PVSC table does not exist!" | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "2. Checking backend service..." | tee -a $LOG_FILE
if curl -s "http://localhost:8001/api/health" > /dev/null; then
    echo "✅ Backend API is responding" | tee -a $LOG_FILE
else
    echo "❌ Backend API is not responding" | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "3. Testing PVSC endpoint directly..." | tee -a $LOG_FILE

# Get a sample assessment number
SAMPLE_AN=$(mysql -u taxsale -p'SecureTaxSale2025!' $DB_NAME -s -N -e "SELECT assessment_number FROM properties LIMIT 1;")

if [ -n "$SAMPLE_AN" ]; then
    echo "   Testing with Assessment Number: $SAMPLE_AN" | tee -a $LOG_FILE
    
    # Test the PVSC endpoint
    PVSC_RESPONSE=$(curl -s "http://localhost:8001/api/pvsc-data/$SAMPLE_AN")
    
    if echo "$PVSC_RESPONSE" | jq -e . >/dev/null 2>&1; then
        echo "   ✅ PVSC endpoint returned valid JSON" | tee -a $LOG_FILE
        
        # Check if it's an error response
        if echo "$PVSC_RESPONSE" | jq -e '.error' >/dev/null 2>&1; then
            ERROR_MSG=$(echo "$PVSC_RESPONSE" | jq -r '.error')
            echo "   ❌ API returned error: $ERROR_MSG" | tee -a $LOG_FILE
        else
            echo "   ✅ API returned valid data" | tee -a $LOG_FILE
            # Show a few fields from the response
            echo "$PVSC_RESPONSE" | jq '{assessment_number, assessed_value, property_use}' | tee -a $LOG_FILE
        fi
    else
        echo "   ❌ PVSC endpoint returned non-JSON response:" | tee -a $LOG_FILE
        echo "   Response: $PVSC_RESPONSE" | tee -a $LOG_FILE
    fi
else
    echo "   ❌ No properties found to test with" | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "4. Checking database connection from PHP..." | tee -a $LOG_FILE

# Create a temporary PHP test script
cat > /tmp/test_pvsc_php.php << 'EOF'
<?php
require_once '/var/www/tax-sale-compass/frontend-php/config/database.php';

try {
    $db = getDB();
    echo "✅ PHP database connection successful\n";
    
    // Test PVSC table query
    $stmt = $db->prepare("SELECT COUNT(*) as count FROM pvsc_data");
    $stmt->execute();
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    echo "✅ PVSC table accessible from PHP: " . $result['count'] . " records\n";
    
    // Test API_BASE_URL constant
    if (defined('API_BASE_URL')) {
        echo "✅ API_BASE_URL defined: " . API_BASE_URL . "\n";
    } else {
        echo "❌ API_BASE_URL not defined\n";
    }
    
    // Test API call
    $test_an = $db->query("SELECT assessment_number FROM properties LIMIT 1")->fetchColumn();
    if ($test_an) {
        echo "Testing API call for: $test_an\n";
        $api_url = API_BASE_URL . '/pvsc-data/' . $test_an;
        echo "API URL: $api_url\n";
        
        $response = @file_get_contents($api_url);
        if ($response) {
            echo "✅ API call successful\n";
            $data = json_decode($response, true);
            if (isset($data['error'])) {
                echo "❌ API returned error: " . $data['error'] . "\n";
            } else {
                echo "✅ API returned valid data\n";
            }
        } else {
            echo "❌ API call failed\n";
        }
    }
    
} catch (Exception $e) {
    echo "❌ PHP error: " . $e->getMessage() . "\n";
}
?>
EOF

php /tmp/test_pvsc_php.php | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "5. Checking PHP error logs..." | tee -a $LOG_FILE
if [ -f /var/log/php_errors.log ]; then
    echo "   Recent PHP errors:" | tee -a $LOG_FILE
    tail -10 /var/log/php_errors.log | tee -a $LOG_FILE
else
    echo "   No PHP error log found" | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "=== DEBUG COMPLETE ===" | tee -a $LOG_FILE
echo "Log saved to: $LOG_FILE" | tee -a $LOG_FILE

# Clean up
rm -f /tmp/test_pvsc_php.php