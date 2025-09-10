<?php
session_start();
require_once 'config/database.php';
require_once 'includes/thumbnail_generator.php';

// Check session variables
$user_id = $_SESSION['user_id'] ?? null;
$access_token = $_SESSION['access_token'] ?? null;
$is_logged_in = isset($_SESSION['user_id']) && isset($_SESSION['access_token']);

// Check if user is logged in
if ($is_logged_in) {
    // User is logged in, redirect to search page
    header('Location: search.php');
    exit;
} else {
    // User is not logged in, show landing page content with featured properties
    $landing_properties = [];
    $db_error = null;
    
    // Debug logging for VPS troubleshooting
    error_log("=== INDEX/LANDING PAGE DEBUG START ===");
    error_log("MONGO_URL: " . MONGO_URL);
    error_log("DB_NAME: " . DB_NAME);
    
    try {
        // Get 6 random properties for landing page preview
        $db = getDB();
        
        if ($db === null) {
            $db_error = "Database connection failed - getDB() returned null";
            error_log("Landing page: Database connection is null");
        } else {
            error_log("Landing page: MongoDB connection successful");
            
            // Test if properties collection exists
            $collections = $db->listCollections();
            $has_properties = false;
            foreach ($collections as $collection) {
                if ($collection->getName() === 'properties') {
                    $has_properties = true;
                    break;
                }
            }
            
            if (!$has_properties) {
                $db_error = "Properties collection does not exist";
                error_log("Landing page: Properties collection not found");
            } else {
                error_log("Landing page: Properties collection exists");
                
                // Get random properties using MongoDB aggregation
                $pipeline = [
                    ['$sample' => ['size' => 6]]
                ];
                
                $cursor = $db->properties->aggregate($pipeline);
                $landing_properties = mongoArrayToArray($cursor);
                
                error_log("Landing page: Found " . count($landing_properties) . " properties");
                
                // Log each property for debugging
                foreach ($landing_properties as $i => $prop) {
                    error_log("Property $i: " . $prop['assessment_number'] . " - " . ($prop['civic_address'] ?? 'No address'));
                }
            }
        }
        
        // Initialize thumbnail generator for landing page
        $thumbnail_generator = new ThumbnailGenerator(GOOGLE_MAPS_API_KEY);
        error_log("Landing page: Thumbnail generator initialized");
        
    } catch (Exception $e) {
        $db_error = $e->getMessage();
        error_log("Landing page error: " . $e->getMessage());
        error_log("Landing page error trace: " . $e->getTraceAsString());
        $landing_properties = [];
        $thumbnail_generator = new ThumbnailGenerator(GOOGLE_MAPS_API_KEY);
    }
    
    error_log("=== INDEX/LANDING PAGE DEBUG END (Properties: " . count($landing_properties) . ") ===");
    
    // Include the landing page template
    require_once 'landing.php';
    exit;
}
?>