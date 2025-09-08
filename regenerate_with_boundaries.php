<?php
require_once 'frontend-php/config/database.php';
require_once 'frontend-php/includes/thumbnail_generator.php';

echo "🔄 Regenerating thumbnails with property boundaries\n";
echo "=================================================\n\n";

try {
    $db = getDB();
    $thumbnailGenerator = new ThumbnailGenerator(GOOGLE_MAPS_API_KEY);
    
    // Get properties that have PID numbers (needed for boundary data)
    $stmt = $db->query("SELECT assessment_number, pid_number, latitude, longitude, civic_address 
                        FROM properties 
                        WHERE pid_number IS NOT NULL 
                        AND pid_number != '' 
                        AND pid_number != 'N/A'
                        LIMIT 20"); // Process more properties
    $properties = $stmt->fetchAll();
    
    echo "Found " . count($properties) . " properties with PID numbers\n\n";
    
    $success = 0;
    $failed = 0;
    
    foreach ($properties as $property) {
        $assessment = $property['assessment_number'];
        $pid = $property['pid_number'];
        
        echo "Processing: {$assessment} (PID: {$pid})\n";
        
        // Call backend API for boundary data
        $backend_url = API_BASE_URL . "/query-ns-government-parcel/{$pid}";
        echo "  Calling: {$backend_url}\n";
        
        $response = @file_get_contents($backend_url);
        
        if ($response) {
            $data = json_decode($response, true);
            if ($data && $data['found'] && isset($data['geometry'])) {
                echo "  ✅ Got boundary data\n";
                
                $center = $data['center'];
                $result = $thumbnailGenerator->generateBoundaryOverlayThumbnail(
                    $assessment, 
                    $data, 
                    $center['lat'], 
                    $center['lon']
                );
                
                if ($result) {
                    echo "  ✅ Generated boundary thumbnail: {$result}\n";
                    $success++;
                } else {
                    echo "  ❌ Failed to generate boundary thumbnail\n";
                    $failed++;
                }
            } else {
                echo "  ❌ No boundary data found\n";
                $failed++;
            }
        } else {
            echo "  ❌ Backend API call failed\n";
            $failed++;
        }
        
        echo "\n";
        sleep(1); // Don't overwhelm the APIs
    }
    
    echo "Summary:\n";
    echo "Success: {$success}\n";
    echo "Failed: {$failed}\n";
    
    if ($success > 0) {
        echo "\n🎉 Refresh your browser to see thumbnails with property boundaries!\n";
    }
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>