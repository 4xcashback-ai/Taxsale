<?php
// Database configuration - Use environment variables with fallbacks
define('DB_HOST', $_ENV['DB_HOST'] ?? getenv('DB_HOST') ?: 'localhost');
define('DB_USER', $_ENV['DB_USER'] ?? getenv('DB_USER') ?: 'taxsale');
define('DB_PASS', $_ENV['DB_PASS'] ?? getenv('DB_PASS') ?: 'SecureTaxSale2025!');
define('DB_NAME', $_ENV['DB_NAME'] ?? getenv('DB_NAME') ?: 'tax_sale_compass');

// Google Maps API Key
define('GOOGLE_MAPS_API_KEY', $_ENV['GOOGLE_MAPS_API_KEY'] ?? getenv('GOOGLE_MAPS_API_KEY') ?: 'AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY');

// Backend API URL
define('API_BASE_URL', $_ENV['API_BASE_URL'] ?? getenv('API_BASE_URL') ?: 'http://localhost:8001/api');

// Site configuration
define('SITE_NAME', 'Tax Sale Compass');
define('SITE_URL', $_ENV['SITE_URL'] ?? getenv('SITE_URL') ?: 'http://localhost:3000');

// Database connection function
function getDB() {
    static $pdo = null;
    
    if ($pdo === null) {
        try {
            $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4";
            
            // Debug info for VPS troubleshooting
            error_log("DB Connection attempt: Host=" . DB_HOST . ", User=" . DB_USER . ", DB=" . DB_NAME);
            
            $pdo = new PDO($dsn, DB_USER, DB_PASS, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
                PDO::ATTR_TIMEOUT => 10, // 10 second connection timeout
            ]);
            
            error_log("DB Connection successful");
            
        } catch (PDOException $e) {
            error_log("Database connection failed: " . $e->getMessage());
            
            // Don't die immediately, return null to handle gracefully
            return null;
        }
    }
    
    return $pdo;
}
?>