<?php
// VPS Debug Script - Upload this to your VPS and access via browser
require_once 'config/database.php';

echo "<!DOCTYPE html><html><head><title>VPS Debug</title></head><body>";
echo "<h1>VPS Featured Properties Debug</h1>";

// Check configuration
echo "<h2>Configuration Check</h2>";
echo "<table border='1' style='border-collapse: collapse;'>";
echo "<tr><th>Setting</th><th>Value</th><th>Status</th></tr>";

$config_checks = [
    'DB_HOST' => DB_HOST,
    'DB_USER' => DB_USER,
    'DB_NAME' => DB_NAME,
    'DB_PASS' => empty(DB_PASS) ? 'NOT SET' : 'SET (hidden)',
    'GOOGLE_MAPS_API_KEY' => empty(GOOGLE_MAPS_API_KEY) ? 'NOT SET' : 'SET (hidden)',
    'API_BASE_URL' => API_BASE_URL,
    'SITE_URL' => SITE_URL
];

foreach ($config_checks as $key => $value) {
    $status = empty($value) || $value == 'NOT SET' ? '❌' : '✅';
    echo "<tr><td>$key</td><td>$value</td><td>$status</td></tr>";
}
echo "</table>";

// Test database connection
echo "<h2>Database Connection Test</h2>";
try {
    $db = getDB();
    
    if ($db === null) {
        echo "<p style='color: red;'>❌ Database connection is NULL</p>";
    } else {
        echo "<p style='color: green;'>✅ Database connection successful</p>";
        
        // Check if properties table exists
        echo "<h3>Properties Table Check</h3>";
        try {
            $stmt = $db->query("SHOW TABLES LIKE 'properties'");
            $table_exists = $stmt->fetch();
            
            if ($table_exists) {
                echo "<p style='color: green;'>✅ Properties table exists</p>";
                
                // Count properties
                $stmt = $db->query("SELECT COUNT(*) as count FROM properties");
                $count = $stmt->fetch();
                echo "<p><strong>Properties count: " . $count['count'] . "</strong></p>";
                
                if ($count['count'] > 0) {
                    echo "<h3>Sample Properties</h3>";
                    $stmt = $db->query("SELECT assessment_number, civic_address, status, property_type FROM properties LIMIT 5");
                    $properties = $stmt->fetchAll();
                    
                    echo "<table border='1' style='border-collapse: collapse;'>";
                    echo "<tr><th>Assessment #</th><th>Address</th><th>Status</th><th>Type</th></tr>";
                    foreach ($properties as $prop) {
                        echo "<tr>";
                        echo "<td>" . htmlspecialchars($prop['assessment_number']) . "</td>";
                        echo "<td>" . htmlspecialchars($prop['civic_address'] ?? 'N/A') . "</td>";
                        echo "<td>" . htmlspecialchars($prop['status']) . "</td>";
                        echo "<td>" . htmlspecialchars($prop['property_type'] ?? 'N/A') . "</td>";
                        echo "</tr>";
                    }
                    echo "</table>";
                    
                    // Test the exact query used in landing page
                    echo "<h3>Landing Page Query Test</h3>";
                    $stmt = $db->query("SELECT * FROM properties ORDER BY RAND() LIMIT 6");
                    $landing_properties = $stmt->fetchAll();
                    echo "<p><strong>Landing query result: " . count($landing_properties) . " properties</strong></p>";
                    
                } else {
                    echo "<p style='color: red;'>❌ No properties found in database</p>";
                }
                
            } else {
                echo "<p style='color: red;'>❌ Properties table does not exist</p>";
                echo "<p><strong>Available tables:</strong></p>";
                $stmt = $db->query("SHOW TABLES");
                $tables = $stmt->fetchAll();
                echo "<ul>";
                foreach ($tables as $table) {
                    echo "<li>" . array_values($table)[0] . "</li>";
                }
                echo "</ul>";
            }
            
        } catch (Exception $e) {
            echo "<p style='color: red;'>❌ Table check failed: " . $e->getMessage() . "</p>";
        }
    }
    
} catch (Exception $e) {
    echo "<p style='color: red;'>❌ Database connection failed: " . $e->getMessage() . "</p>";
}

// Test session status
echo "<h2>Session Check</h2>";
if (session_status() == PHP_SESSION_NONE) {
    session_start();
}
echo "<p>Session ID: " . session_id() . "</p>";
echo "<p>User logged in: " . (isset($_SESSION['user_id']) ? 'YES (ID: ' . $_SESSION['user_id'] . ')' : 'NO') . "</p>";

// Environment info
echo "<h2>Environment Info</h2>";
echo "<p>PHP Version: " . phpversion() . "</p>";
echo "<p>Server: " . $_SERVER['SERVER_SOFTWARE'] ?? 'Unknown' . "</p>";
echo "<p>Document Root: " . $_SERVER['DOCUMENT_ROOT'] ?? 'Unknown' . "</p>";

echo "</body></html>";
?>