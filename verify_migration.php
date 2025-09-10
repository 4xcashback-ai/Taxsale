<?php
require_once __DIR__ . '/frontend-php/config/database.php';

echo "=== MIGRATION VERIFICATION ===\n";

try {
    $mongodb = getDB();
    if (!$mongodb) {
        die("❌ MongoDB connection failed\n");
    }
    
    echo "✅ MongoDB connected\n\n";
    
    // Count documents in each collection
    $properties_count = $mongodb->properties->countDocuments([]);
    $pvsc_count = $mongodb->pvsc_data->countDocuments([]);
    $users_count = $mongodb->users->countDocuments([]);
    $favorites_count = $mongodb->user_favorites->countDocuments([]);
    
    echo "=== COLLECTION COUNTS ===\n";
    echo "Properties: $properties_count\n";
    echo "PVSC Data: $pvsc_count\n";
    echo "Users: $users_count\n";
    echo "Favorites: $favorites_count\n\n";
    
    // Check properties with PID numbers
    $with_pid = $mongodb->properties->countDocuments(['pid_number' => ['$exists' => true, '$ne' => null, '$ne' => '']]);
    $without_pid = $properties_count - $with_pid;
    
    echo "=== PID NUMBER CHECK ===\n";
    echo "Properties WITH pid_number: $with_pid\n";
    echo "Properties WITHOUT pid_number: $without_pid\n\n";
    
    // Sample property data
    echo "=== SAMPLE PROPERTY ===\n";
    $sample_property = $mongodb->properties->findOne();
    if ($sample_property) {
        $prop = mongoToArray($sample_property);
        echo "Assessment: " . ($prop['assessment_number'] ?? 'NULL') . "\n";
        echo "PID: " . ($prop['pid_number'] ?? 'NULL') . "\n";
        echo "Address: " . ($prop['civic_address'] ?? 'NULL') . "\n";
        echo "Thumbnail: " . ($prop['thumbnail_path'] ?? 'NULL') . "\n";
        echo "Coordinates: " . ($prop['latitude'] ?? 'NULL') . ", " . ($prop['longitude'] ?? 'NULL') . "\n";
        echo "Boundary Data: " . (isset($prop['boundary_data']) ? 'YES' : 'NO') . "\n";
    }
    
    // Sample PVSC data
    echo "\n=== SAMPLE PVSC DATA ===\n";
    $sample_pvsc = $mongodb->pvsc_data->findOne();
    if ($sample_pvsc) {
        $pvsc = mongoToArray($sample_pvsc);
        echo "Assessment: " . ($pvsc['assessment_number'] ?? 'NULL') . "\n";
        echo "Assessed Value: " . ($pvsc['assessed_value'] ?? 'NULL') . "\n";
        echo "Property Type: " . ($pvsc['property_type'] ?? 'NULL') . "\n";
        echo "Year Built: " . ($pvsc['year_built'] ?? 'NULL') . "\n";
        echo "Bedrooms: " . ($pvsc['number_of_bedrooms'] ?? 'NULL') . "\n";
        echo "Bathrooms: " . ($pvsc['number_of_bathrooms'] ?? 'NULL') . "\n";
    } else {
        echo "No PVSC data found\n";
    }
    
    // Check thumbnails
    echo "\n=== THUMBNAIL CHECK ===\n";
    $with_thumbnails = $mongodb->properties->countDocuments(['thumbnail_path' => ['$exists' => true, '$ne' => null, '$ne' => '']]);
    echo "Properties with thumbnail paths: $with_thumbnails\n";
    
    // Sample thumbnails
    $properties_with_thumbs = $mongodb->properties->find(['thumbnail_path' => ['$exists' => true, '$ne' => null, '$ne' => '']], ['limit' => 3]);
    foreach ($properties_with_thumbs as $prop_doc) {
        $prop = mongoToArray($prop_doc);
        $thumbnail_file = "/var/www/tax-sale-compass/frontend-php" . $prop['thumbnail_path'];
        $exists = file_exists($thumbnail_file) ? "EXISTS" : "MISSING";
        echo "  " . $prop['assessment_number'] . ": " . $prop['thumbnail_path'] . " ($exists)\n";
    }
    
    echo "\n✅ Verification complete!\n";
    
} catch (Exception $e) {
    echo "❌ Verification failed: " . $e->getMessage() . "\n";
}
?>