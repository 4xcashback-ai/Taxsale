<?php
// Database diagnostic script for VPS debugging
require_once 'config/database.php';

echo "<h2>Database Diagnostic</h2>";

// Show configuration
echo "<h3>Configuration:</h3>";
echo "DB_HOST: " . DB_HOST . "<br>";
echo "DB_USER: " . DB_USER . "<br>";
echo "DB_NAME: " . DB_NAME . "<br>";
echo "DB_PASS: " . (empty(DB_PASS) ? "NOT SET" : "SET (hidden)") . "<br><br>";

// Test database connection
echo "<h3>Connection Test:</h3>";
try {
    $db = getDB();
    
    if ($db === null) {
        echo "<span style='color: red;'>❌ Database connection is NULL</span><br>";
    } else {
        echo "<span style='color: green;'>✅ Database connection successful</span><br>";
        
        // Test if properties table exists
        echo "<h3>Table Check:</h3>";
        try {
            $stmt = $db->query("SHOW TABLES LIKE 'properties'");
            $table_exists = $stmt->fetch();
            
            if ($table_exists) {
                echo "<span style='color: green;'>✅ Properties table exists</span><br>";
                
                // Count properties
                $stmt = $db->query("SELECT COUNT(*) as count FROM properties");
                $count = $stmt->fetch();
                echo "<span style='color: blue;'>📊 Properties count: " . $count['count'] . "</span><br>";
                
                // Show sample properties
                if ($count['count'] > 0) {
                    echo "<h3>Sample Properties:</h3>";
                    $stmt = $db->query("SELECT assessment_number, civic_address, status FROM properties LIMIT 5");
                    $properties = $stmt->fetchAll();
                    
                    echo "<table border='1' style='border-collapse: collapse;'>";
                    echo "<tr><th>Assessment #</th><th>Address</th><th>Status</th></tr>";
                    foreach ($properties as $prop) {
                        echo "<tr>";
                        echo "<td>" . htmlspecialchars($prop['assessment_number']) . "</td>";
                        echo "<td>" . htmlspecialchars($prop['civic_address']) . "</td>";
                        echo "<td>" . htmlspecialchars($prop['status']) . "</td>";
                        echo "</tr>";
                    }
                    echo "</table>";
                }
                
            } else {
                echo "<span style='color: red;'>❌ Properties table does not exist</span><br>";
            }
            
        } catch (Exception $e) {
            echo "<span style='color: red;'>❌ Table check failed: " . $e->getMessage() . "</span><br>";
        }
    }
    
} catch (Exception $e) {
    echo "<span style='color: red;'>❌ Database connection failed: " . $e->getMessage() . "</span><br>";
}

// Show PHP error log (last 20 lines)
echo "<h3>Recent PHP Error Log:</h3>";
$error_log = shell_exec('tail -n 20 /var/log/php8.2-fpm.log 2>/dev/null || tail -n 20 /var/log/php-fpm.log 2>/dev/null || echo "Error log not found"');
echo "<pre style='background: #f5f5f5; padding: 10px; font-size: 12px;'>" . htmlspecialchars($error_log) . "</pre>";

?>