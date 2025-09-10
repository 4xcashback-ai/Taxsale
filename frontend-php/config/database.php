<?php
// Load Composer autoloader
require_once __DIR__ . '/../vendor/autoload.php';

// MongoDB configuration - Use environment variables with fallbacks
define('MONGO_URL', $_ENV['MONGO_URL'] ?? getenv('MONGO_URL') ?: 'mongodb://localhost:27017');
define('DB_NAME', $_ENV['DB_NAME'] ?? getenv('DB_NAME') ?: 'tax_sale_compass');

// Google Maps API Key
define('GOOGLE_MAPS_API_KEY', $_ENV['GOOGLE_MAPS_API_KEY'] ?? getenv('GOOGLE_MAPS_API_KEY') ?: 'AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY');

// Backend API URL
define('API_BASE_URL', $_ENV['API_BASE_URL'] ?? getenv('API_BASE_URL') ?: 'http://localhost:8001/api');

// Site configuration
define('SITE_NAME', 'Tax Sale Compass');
define('SITE_URL', $_ENV['SITE_URL'] ?? getenv('SITE_URL') ?: 'http://localhost:3000');

// MongoDB connection function
function getDB() {
    static $client = null;
    static $database = null;
    
    if ($client === null) {
        try {
            // Debug info for VPS troubleshooting
            error_log("MongoDB Connection attempt: URL=" . MONGO_URL . ", DB=" . DB_NAME);
            
            $client = new MongoDB\Client(MONGO_URL);
            $database = $client->selectDatabase(DB_NAME);
            
            // Test connection
            $database->command(['ping' => 1]);
            
            error_log("MongoDB Connection successful");
            
        } catch (Exception $e) {
            error_log("MongoDB connection failed: " . $e->getMessage());
            return null;
        }
    }
    
    return $database;
}

// Helper function to convert MongoDB document to array
function mongoToArray($document) {
    if ($document === null) return null;
    
    // Convert BSONDocument to array
    if ($document instanceof MongoDB\Model\BSONDocument) {
        $array = $document->toArray();
    } elseif ($document instanceof MongoDB\BSON\Document) {
        $array = $document->toArray();  
    } elseif (is_array($document)) {
        $array = $document;
    } else {
        // Convert to array using iterator
        $array = [];
        foreach ($document as $key => $value) {
            $array[$key] = $value;
        }
    }
    
    // Convert ObjectId to string for assessment_number compatibility
    if (isset($array['_id'])) {
        if ($array['_id'] instanceof MongoDB\BSON\ObjectId) {
            $array['id'] = (string)$array['_id'];
        }
        unset($array['_id']);
    }
    
    return $array;
}

// Helper function to convert array of MongoDB documents
function mongoArrayToArray($cursor) {
    $result = [];
    foreach ($cursor as $document) {
        $result[] = mongoToArray($document);
    }
    return $result;
}
?>