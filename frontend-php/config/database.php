<?php
// Load Composer autoloader
require_once __DIR__ . '/../vendor/autoload.php';

// MongoDB configuration
define('MONGO_URL', $_ENV['MONGO_URL'] ?? getenv('MONGO_URL') ?: 'mongodb://localhost:27017');
define('DB_NAME', $_ENV['DB_NAME'] ?? getenv('DB_NAME') ?: 'tax_sale_compass');
define('GOOGLE_MAPS_API_KEY', $_ENV['GOOGLE_MAPS_API_KEY'] ?? getenv('GOOGLE_MAPS_API_KEY') ?: 'AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY');
define('API_BASE_URL', $_ENV['API_BASE_URL'] ?? getenv('API_BASE_URL') ?: 'http://localhost:8001/api');
define('SITE_NAME', 'Tax Sale Compass');
define('SITE_URL', $_ENV['SITE_URL'] ?? getenv('SITE_URL') ?: 'https://taxsalecompass.ca');

function getDB() {
    static $client = null;
    static $database = null;
    
    if ($client === null) {
        try {
            error_log("MongoDB Connection attempt: URL=" . MONGO_URL . ", DB=" . DB_NAME);
            $client = new MongoDB\Client(MONGO_URL);
            $database = $client->selectDatabase(DB_NAME);
            $database->command(['ping' => 1]);
            error_log("MongoDB Connection successful");
        } catch (Exception $e) {
            error_log("MongoDB connection failed: " . $e->getMessage());
            return null;
        }
    }
    return $database;
}

function mongoToArray($document) {
    if ($document === null) return null;
    
    if (is_array($document)) {
        $array = $document;
    } else {
        $array = [];
        foreach ($document as $key => $value) {
            if ($value instanceof MongoDB\BSON\UTCDateTime) {
                $array[$key] = $value->toDateTime()->format('Y-m-d H:i:s');
            } elseif ($value instanceof MongoDB\BSON\ObjectId) {
                $array[$key] = (string)$value;
            } else {
                $array[$key] = $value;
            }
        }
    }
    
    if (isset($array['_id'])) {
        if ($array['_id'] instanceof MongoDB\BSON\ObjectId) {
            $array['id'] = (string)$array['_id'];
        }
        unset($array['_id']);
    }
    
    return $array;
}

function mongoArrayToArray($cursor) {
    $result = [];
    foreach ($cursor as $document) {
        $result[] = mongoToArray($document);
    }
    return $result;
}
?>