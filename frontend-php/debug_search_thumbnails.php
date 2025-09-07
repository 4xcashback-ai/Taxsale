<?php
// Add this to the top of your search.php temporarily for debugging
if (isset($_GET['debug_thumbnails']) && $_SESSION['is_admin']) {
    echo "<div style='background: #f8f9fa; padding: 20px; margin: 20px; border: 1px solid #ddd; border-radius: 5px;'>";
    echo "<h4>🔍 Thumbnail Debug Info</h4>";
    
    // Show what properties we're loading
    foreach (array_slice($properties, 0, 3) as $property) {
        echo "<div style='border: 1px solid #ccc; padding: 10px; margin: 10px 0; background: white;'>";
        echo "<strong>Assessment: " . htmlspecialchars($property['assessment_number']) . "</strong><br>";
        echo "PID: " . htmlspecialchars($property['pid_number'] ?? 'NULL') . "<br>";
        echo "DB thumbnail_path: " . htmlspecialchars($property['thumbnail_path'] ?? 'NULL') . "<br>";
        echo "Coordinates: " . htmlspecialchars(($property['latitude'] ?? 'NULL') . ', ' . ($property['longitude'] ?? 'NULL')) . "<br>";
        
        // Test what getThumbnail returns
        $thumbnail_url = $thumbnail_generator->getThumbnail($property);
        echo "getThumbnail() returns: " . htmlspecialchars($thumbnail_url) . "<br>";
        
        // Check if file exists
        if (strpos($thumbnail_url, '/assets/thumbnails/') === 0) {
            $file_path = dirname(__DIR__) . $thumbnail_url;
            echo "File path: " . htmlspecialchars($file_path) . "<br>";
            echo "File exists: " . (file_exists($file_path) ? '✅ Yes' : '❌ No') . "<br>";
            if (file_exists($file_path)) {
                echo "File size: " . filesize($file_path) . " bytes<br>";
            }
        }
        echo "</div>";
    }
    echo "</div>";
}
?>