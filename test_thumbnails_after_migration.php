<?php
require_once __DIR__ . '/frontend-php/config/database.php';
require_once __DIR__ . '/frontend-php/includes/thumbnail_generator.php';

echo "=== THUMBNAIL TEST AFTER MIGRATION ===\n";

try {
    $db = getDB();
    if (!$db) {
        die("❌ Database connection failed\n");
    }
    
    $thumbnail_generator = new ThumbnailGenerator(GOOGLE_MAPS_API_KEY);
    
    // Test properties with thumbnail paths
    $properties = $db->properties->find(['thumbnail_path' => ['$exists' => true, '$ne' => null, '$ne' => '']], ['limit' => 5]);
    
    foreach ($properties as $property_doc) {
        $property = mongoToArray($property_doc);
        
        echo "\n--- Testing Property: " . $property['assessment_number'] . " ---\n";
        echo "Address: " . ($property['civic_address'] ?? 'N/A') . "\n";
        echo "PID: " . ($property['pid_number'] ?? 'NULL') . "\n";
        echo "Database thumbnail_path: " . ($property['thumbnail_path'] ?? 'NULL') . "\n";
        
        // Check if file exists using the corrected path
        $thumbnail_file = "/var/www/tax-sale-compass/frontend-php" . $property['thumbnail_path'];
        $file_exists = file_exists($thumbnail_file);
        echo "File exists: " . ($file_exists ? '✅ YES' : '❌ NO') . "\n";
        
        if ($file_exists) {
            echo "File size: " . number_format(filesize($thumbnail_file)) . " bytes\n";
        }
        
        // Test thumbnail generation
        $thumbnail_url = $thumbnail_generator->getThumbnail($property);
        
        if (strpos($thumbnail_url, 'data:image/svg+xml') !== false) {
            echo "Result: ❌ SVG placeholder\n";
        } elseif (strpos($thumbnail_url, '/assets/thumbnails/') !== false) {
            echo "Result: ✅ Real thumbnail URL\n";
        } else {
            echo "Result: ? Unknown type\n";
        }
        
        echo "Generated URL: " . substr($thumbnail_url, 0, 80) . "...\n";
    }
    
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
}
?>