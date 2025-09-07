<?php
require_once 'frontend-php/config/database.php';
require_once 'frontend-php/includes/thumbnail_generator.php';

echo "🔧 Fixing Missing Thumbnail Files\n";
echo "================================\n\n";

try {
    $db = getDB();
    $thumbnailGenerator = new ThumbnailGenerator(GOOGLE_MAPS_API_KEY);
    
    // Find properties that have thumbnail_path in DB but missing files
    $stmt = $db->query("SELECT assessment_number, pid_number, thumbnail_path, latitude, longitude, civic_address 
                        FROM properties 
                        WHERE thumbnail_path IS NOT NULL 
                        AND thumbnail_path != ''
                        ORDER BY assessment_number");
    $properties = $stmt->fetchAll();
    
    echo "Found " . count($properties) . " properties with thumbnail paths in database\n\n";
    
    $missing = 0;
    $existing = 0;
    $regenerated = 0;
    $failed = 0;
    
    foreach ($properties as $property) {
        $assessment = $property['assessment_number'];
        $thumbnailPath = $property['thumbnail_path'];
        $fullPath = dirname(__FILE__) . '/frontend-php' . $thumbnailPath;
        
        if (!file_exists($fullPath)) {
            $missing++;
            echo "❌ Missing: {$assessment} -> {$thumbnailPath}\n";
            
            // Try to regenerate
            if ($property['latitude'] && $property['longitude']) {
                // Generate thumbnail with boundary overlay if possible
                if ($property['pid_number']) {
                    echo "   🔄 Regenerating with PID {$property['pid_number']}...\n";
                    
                    // Call backend API for boundary data
                    $backend_url = API_BASE_URL . "/query-ns-government-parcel/{$property['pid_number']}";
                    $response = @file_get_contents($backend_url);
                    
                    if ($response) {
                        $data = json_decode($response, true);
                        if ($data && $data['found'] && isset($data['geometry'])) {
                            echo "   📍 Got boundary data, creating overlay...\n";
                            
                            // Generate with boundary overlay
                            $result = $thumbnailGenerator->generateBoundaryOverlayThumbnail(
                                $assessment, 
                                $data, 
                                $property['latitude'], 
                                $property['longitude']
                            );
                            
                            if ($result && file_exists(dirname(__FILE__) . '/frontend-php' . $result)) {
                                echo "   ✅ Generated boundary overlay: {$result}\n";
                                $regenerated++;
                                continue;
                            }
                        }
                    }
                }
                
                // Fallback to basic satellite image
                echo "   🗺️  Generating basic satellite image...\n";
                $params = [
                    'key' => GOOGLE_MAPS_API_KEY,
                    'center' => $property['latitude'] . ',' . $property['longitude'],
                    'zoom' => '18',
                    'size' => '300x200',
                    'maptype' => 'satellite',
                    'format' => 'png',
                    'markers' => 'color:red|size:mid|' . $property['latitude'] . ',' . $property['longitude']
                ];
                
                $url = 'https://maps.googleapis.com/maps/api/staticmap?' . http_build_query($params);
                $image_data = @file_get_contents($url);
                
                if ($image_data && file_put_contents($fullPath, $image_data)) {
                    echo "   ✅ Generated basic thumbnail\n";
                    $regenerated++;
                } else {
                    echo "   ❌ Failed to generate thumbnail\n";
                    $failed++;
                }
            } else {
                echo "   ❌ No coordinates available\n";
                $failed++;
            }
            
        } else {
            $existing++;
            echo "✅ Exists: {$assessment} -> " . filesize($fullPath) . " bytes\n";
        }
    }
    
    echo "\n" . str_repeat("=", 40) . "\n";
    echo "SUMMARY:\n";
    echo "Total properties checked: " . count($properties) . "\n";
    echo "Files already existing: {$existing}\n";
    echo "Files missing: {$missing}\n";
    echo "Successfully regenerated: {$regenerated}\n";
    echo "Failed to regenerate: {$failed}\n";
    
    if ($regenerated > 0) {
        echo "\n🎉 Regenerated {$regenerated} thumbnail files!\n";
        echo "The search page should now show proper images.\n";
    }
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>