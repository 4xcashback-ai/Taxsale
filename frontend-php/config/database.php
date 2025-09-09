<?php
// Database configuration
define('DB_HOST', 'localhost');
define('DB_USER', 'taxsale');
define('DB_PASS', 'SecureTaxSale2025!');
define('DB_NAME', 'tax_sale_compass');

// Google Maps API Key
define('GOOGLE_MAPS_API_KEY', 'AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY');

// Backend API URL
define('API_BASE_URL', 'http://localhost:8001/api');

// Site configuration
define('SITE_NAME', 'Tax Sale Compass');
define('SITE_URL', 'http://localhost:3000');

// Database connection function
function getDB() {
    static $pdo = null;
    
    if ($pdo === null) {
        try {
            $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4";
            $pdo = new PDO($dsn, DB_USER, DB_PASS, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ]);
        } catch (PDOException $e) {
            die("Database connection failed: " . $e->getMessage());
        }
    }
    
    return $pdo;
}
?>