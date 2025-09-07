<?php
// Simple manual thumbnail generation for immediate fix
require_once 'frontend-php/config/database.php';

echo "Manually creating thumbnail for property 08968373...\n";

// Property details from debug
$assessment = '08968373';
$lat = 44.66587406;
$lon = -63.90296149;
$pid = '40199820';

// Create Google Maps Static API URL with better styling
$params = [
    'key' => GOOGLE_MAPS_API_KEY,
    'center' => $lat . ',' . $lon,
    'zoom' => '18',
    'size' => '300x200',
    'maptype' => 'satellite',
    'format' => 'png',
    'markers' => 'color:red|size:mid|' . $lat . ',' . $lon
];

$url = 'https://maps.googleapis.com/maps/api/staticmap?' . http_build_query($params);
echo "Google Maps URL: " . substr($url, 0, 100) . "...\n";

// Download image
$image_data = file_get_contents($url);

if ($image_data) {
    $thumbnail_path = '/app/frontend-php/assets/thumbnails/' . $assessment . '.png';
    $result = file_put_contents($thumbnail_path, $image_data);
    
    if ($result) {
        echo "✅ Successfully created thumbnail: {$thumbnail_path}\n";
        echo "File size: " . strlen($image_data) . " bytes\n";
        echo "File exists: " . (file_exists($thumbnail_path) ? 'YES' : 'NO') . "\n";
    } else {
        echo "❌ Failed to write file\n";
    }
} else {
    echo "❌ Failed to download image from Google Maps API\n";
}

// Let's also try to get boundary data and create a proper boundary overlay
echo "\nTrying to get boundary data for PID {$pid}...\n";

$backend_url = API_BASE_URL . "/query-ns-government-parcel/{$pid}";
echo "Backend URL: {$backend_url}\n";

$response = file_get_contents($backend_url);
if ($response) {
    $data = json_decode($response, true);
    if ($data && $data['found']) {
        echo "✅ Got boundary data from backend\n";
        
        if (isset($data['geometry']) && isset($data['geometry']['rings'])) {
            echo "✅ Has geometry rings - can create boundary overlay\n";
            
            // Build path for boundary overlay
            $rings = $data['geometry']['rings'];
            $path_points = [];
            
            foreach ($rings as $ring) {
                foreach ($ring as $coord) {
                    $path_points[] = $coord[1] . ',' . $coord[0]; // lat,lon format
                }
            }
            
            // Limit points to avoid URL length issues
            if (count($path_points) > 50) {
                $step = ceil(count($path_points) / 50);
                $reduced_points = [];
                for ($i = 0; $i < count($path_points); $i += $step) {
                    $reduced_points[] = $path_points[$i];
                }
                $path_points = $reduced_points;
            }
            
            // Close the path
            if (count($path_points) > 0) {
                $path_points[] = $path_points[0];
            }
            
            $path_string = 'color:0xff0000ff|weight:2|' . implode('|', $path_points);
            
            // Create boundary overlay version
            $boundary_params = [
                'key' => GOOGLE_MAPS_API_KEY,
                'center' => $lat . ',' . $lon,
                'zoom' => '17',
                'size' => '300x200',
                'maptype' => 'satellite',
                'format' => 'png',
                'path' => $path_string,
                'markers' => 'color:red|size:small|' . $lat . ',' . $lon
            ];
            
            $boundary_url = 'https://maps.googleapis.com/maps/api/staticmap?' . http_build_query($boundary_params);
            echo "Boundary URL length: " . strlen($boundary_url) . " chars\n";
            
            if (strlen($boundary_url) < 2048) { // Google Maps URL limit
                $boundary_image = file_get_contents($boundary_url);
                
                if ($boundary_image) {
                    $boundary_path = '/app/frontend-php/assets/thumbnails/' . $assessment . '_boundary.png';
                    $boundary_result = file_put_contents($boundary_path, $boundary_image);
                    
                    if ($boundary_result) {
                        echo "✅ Successfully created boundary overlay: {$boundary_path}\n";
                        echo "Boundary file size: " . strlen($boundary_image) . " bytes\n";
                        
                        // Update database to use boundary version
                        try {
                            $db = getDB();
                            $stmt = $db->prepare("UPDATE properties SET thumbnail_path = ? WHERE assessment_number = ?");
                            $stmt->execute(['/assets/thumbnails/' . $assessment . '_boundary.png', $assessment]);
                            echo "✅ Updated database to use boundary thumbnail\n";
                        } catch (Exception $e) {
                            echo "❌ Failed to update database: " . $e->getMessage() . "\n";
                        }
                    } else {
                        echo "❌ Failed to write boundary file\n";
                    }
                } else {
                    echo "❌ Failed to download boundary image\n";
                }
            } else {
                echo "❌ Boundary URL too long (" . strlen($boundary_url) . " chars), using basic thumbnail\n";
            }
        } else {
            echo "❌ No geometry rings in boundary data\n";
        }
    } else {
        echo "❌ No boundary data found for PID {$pid}\n";
    }
} else {
    echo "❌ Failed to call backend API\n";
}
?>