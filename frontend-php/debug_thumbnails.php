<?php
require_once 'config/database.php';
require_once 'includes/thumbnail_generator.php';

echo "<h2>Thumbnail Generator Debug</h2>";

// Test a property
$db = getDB();
$stmt = $db->prepare("SELECT * FROM properties LIMIT 1");
$stmt->execute();
$property = $stmt->fetch();

if (!$property) {
    echo "❌ No properties found in database<br>";
    exit;
}

echo "<h3>Testing Property:</h3>";
echo "Assessment Number: " . $property['assessment_number'] . "<br>";
echo "PID: " . ($property['pid_number'] ?? 'N/A') . "<br>";
echo "Latitude: " . ($property['latitude'] ?? 'N/A') . "<br>";
echo "Longitude: " . ($property['longitude'] ?? 'N/A') . "<br>";
echo "Has Boundary Data: " . ($property['boundary_data'] ? 'Yes' : 'No') . "<br>";

echo "<h3>Debug Info:</h3>";
echo "Document Root: " . $_SERVER['DOCUMENT_ROOT'] . "<br>";
echo "Current Script: " . __FILE__ . "<br>";

// Test thumbnail generator
try {
    $thumbnail_generator = new ThumbnailGenerator(GOOGLE_MAPS_API_KEY);
    echo "✅ ThumbnailGenerator created successfully<br>";
    
    // Test thumbnail generation
    $thumbnail_url = $thumbnail_generator->getThumbnail($property);
    echo "Thumbnail URL: " . $thumbnail_url . "<br>";
    
    // Check if it's a placeholder
    if (strpos($thumbnail_url, 'data:image/svg+xml') !== false) {
        echo "❌ Showing placeholder image<br>";
    } else {
        echo "✅ Generated actual thumbnail<br>";
        
        // Check if file exists
        $file_path = $_SERVER['DOCUMENT_ROOT'] . '/frontend-php/assets/thumbnails/' . $property['assessment_number'] . '.png';
        echo "File path: " . $file_path . "<br>";
        echo "File exists: " . (file_exists($file_path) ? 'Yes' : 'No') . "<br>";
        
        if (file_exists($file_path)) {
            echo "File size: " . filesize($file_path) . " bytes<br>";
        }
    }
    
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "<br>";
}

// Test Google Maps API
echo "<h3>Google Maps API Test:</h3>";
$test_url = 'https://maps.googleapis.com/maps/api/staticmap?center=44.6488,-63.5752&zoom=17&size=300x200&maptype=satellite&format=png&key=' . GOOGLE_MAPS_API_KEY;
echo "Test URL: <a href='{$test_url}' target='_blank'>Click to test Google Maps API</a><br>";

// Test directory permissions
echo "<h3>Directory Check:</h3>";
$thumbnail_dir = $_SERVER['DOCUMENT_ROOT'] . '/frontend-php/assets/thumbnails/';
echo "Thumbnail directory: " . $thumbnail_dir . "<br>";
echo "Directory exists: " . (is_dir($thumbnail_dir) ? 'Yes' : 'No') . "<br>";
echo "Directory writable: " . (is_writable($thumbnail_dir) ? 'Yes' : 'No') . "<br>";

if (is_dir($thumbnail_dir)) {
    $files = scandir($thumbnail_dir);
    echo "Files in directory: " . implode(', ', array_filter($files, fn($f) => $f !== '.' && $f !== '..')) . "<br>";
}
?>