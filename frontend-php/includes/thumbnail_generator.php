<?php
class ThumbnailGenerator {
    private $google_api_key;
    private $thumbnail_dir;
    private $base_url;
    private $lastLatitude = null;
    private $lastLongitude = null;
    
    public function __construct($api_key) {
        $this->google_api_key = $api_key;
        // Use relative path from current file location
        $this->thumbnail_dir = dirname(__DIR__) . '/assets/thumbnails/';
        $this->base_url = 'https://maps.googleapis.com/maps/api/staticmap';
        
        // Debug logging
        error_log("ThumbnailGenerator: Using thumbnail directory: " . $this->thumbnail_dir);
        
        if (!is_dir($this->thumbnail_dir)) {
            error_log("ThumbnailGenerator: Creating thumbnail directory");
            mkdir($this->thumbnail_dir, 0777, true);
        }
        
        // Ensure directory is writable
        if (!is_writable($this->thumbnail_dir)) {
            error_log("ThumbnailGenerator: Setting directory permissions to 777");
            chmod($this->thumbnail_dir, 0777);
        }
    }
    
    public function getLastLatitude() {
        return $this->lastLatitude;
    }
    
    public function getLastLongitude() {
        return $this->lastLongitude;
    }
    
    public function getThumbnail($property) {
        $assessment_number = $property['assessment_number'];
        $property_type = $property['property_type'] ?? '';
        
        // First check if we already have a pre-generated thumbnail path in the database
        if (isset($property['thumbnail_path']) && !empty($property['thumbnail_path'])) {
            $thumbnail_file = dirname(__DIR__) . $property['thumbnail_path'];
            // Verify the file actually exists
            if (file_exists($thumbnail_file)) {
                return $property['thumbnail_path'];
            }
        }
        
        // Handle mobile homes specially - they may not have coordinates but still need thumbnails
        if ($property_type === 'mobile_home_only') {
            return $this->getMobileHomeThumbnail($property);
        }
        
        // Handle apartments/condos - they should generate thumbnails based on address
        if ($property_type === 'apartment' && empty($property['latitude'])) {
            return $this->getAddressBasedThumbnail($property);
        }
        
        // For search page performance, return a simple placeholder for properties without thumbnails
        return 'data:image/svg+xml;base64,' . base64_encode('
            <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
                <rect width="300" height="200" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
                <text x="150" y="85" font-family="Arial" font-size="14" fill="#6c757d" text-anchor="middle">Property Image</text>
                <text x="150" y="105" font-family="Arial" font-size="14" fill="#6c757d" text-anchor="middle">Not Available</text>
                <text x="150" y="125" font-family="Arial" font-size="14" fill="#6c757d" text-anchor="middle">At This Time</text>
                <circle cx="150" cy="140" r="8" fill="#6c757d" opacity="0.3"/>
            </svg>
        ');
    }
    
    public function generateBoundaryOverlayThumbnail($assessment_number, $boundary_data, $center_lat, $center_lon) {
        error_log("ThumbnailGenerator: Generating boundary overlay for {$assessment_number}");
        
        try {
            // Extract geometry rings for path overlay - try ALL rings, not just first
            $geometry = $boundary_data['geometry'];
            if (!$geometry || !isset($geometry['rings']) || empty($geometry['rings'])) {
                error_log("ThumbnailGenerator: No valid rings in geometry data");
                return null;
            }
            
            error_log("ThumbnailGenerator: Found " . count($geometry['rings']) . " rings in boundary data");
            
            // Build path parameter for Google Maps Static API - USE ALL POINTS FROM ALL RINGS
            $path_points = [];
            foreach ($geometry['rings'] as $ringIndex => $ring) {
                error_log("ThumbnailGenerator: Processing ring {$ringIndex} with " . count($ring) . " points");
                foreach ($ring as $coord) {
                    $path_points[] = $coord[1] . ',' . $coord[0]; // lat,lon format
                }
                // For now, still use only first ring, but let's see what we get
                break;
            }
            
            // Always close the path properly
            if (count($path_points) > 2 && end($path_points) !== $path_points[0]) {
                $path_points[] = $path_points[0];
            }
            
            if (count($path_points) < 3) {
                error_log("ThumbnailGenerator: Not enough path points for boundary");
                return null;
            }
            
            error_log("ThumbnailGenerator: Using " . count($path_points) . " boundary points for complete shape");
            
            $path_string = 'color:0xff0000ff|weight:3|' . implode('|', $path_points);
            
            // Calculate optimal zoom level based on property bounding box
            $bbox = $boundary_data['bbox'];
            $lat_span = $bbox['maxLat'] - $bbox['minLat'];
            $lon_span = $bbox['maxLon'] - $bbox['minLon'];
            
            // Use the larger span to determine zoom level
            $max_span = max($lat_span, $lon_span);
            
            // Calculate zoom level - add MORE padding so boundaries aren't at edge  
            $padded_span = $max_span * 1.8; // Increased from 1.3 to 1.8 for more context
            
            // Determine zoom level based on span (approximate degrees per zoom level)
            if ($padded_span > 0.015) {
                $zoom = 13; // Large properties with more context
            } elseif ($padded_span > 0.01) {
                $zoom = 14; // Large properties (rural, big lots)
            } elseif ($padded_span > 0.005) {
                $zoom = 15; // Medium-large properties
            } elseif ($padded_span > 0.003) {
                $zoom = 16; // Medium properties - reduced threshold
            } elseif ($padded_span > 0.0015) {
                $zoom = 17; // Small-medium properties - reduced threshold
            } else {
                $zoom = 18; // Small properties
            }
            
            error_log("ThumbnailGenerator: Property span: {$max_span}, calculated zoom: {$zoom}");
            
            // Generate map with boundary overlay
            $params = [
                'key' => $this->google_api_key,
                'center' => $center_lat . ',' . $center_lon,
                'zoom' => $zoom, // Dynamic zoom based on property size
                'size' => '300x200',
                'maptype' => 'satellite',
                'format' => 'png',
                'path' => $path_string,
                'markers' => 'color:red|size:small|' . $center_lat . ',' . $center_lon
            ];
            
            $url = $this->base_url . '?' . http_build_query($params);
            error_log("ThumbnailGenerator: Boundary URL length: " . strlen($url));
            
            // If URL is too long, try triangle corner detection first
            if (strlen($url) > 2000) {
                error_log("ThumbnailGenerator: URL too long, trying triangle corner detection");
                
                // Try to identify triangle corners
                $triangle_points = $this->findTriangleCorners($path_points);
                $triangle_path_string = 'color:0xff0000ff|weight:3|' . implode('|', $triangle_points);
                
                $triangle_params = $params;
                $triangle_params['path'] = $triangle_path_string;
                $triangle_url = $this->base_url . '?' . http_build_query($triangle_params);
                
                error_log("ThumbnailGenerator: Triangle URL length: " . strlen($triangle_url));
                
                if (strlen($triangle_url) <= 2000) {
                    $path_string = $triangle_path_string;
                    $params['path'] = $path_string;
                    $url = $triangle_url;
                } else {
                    // Fallback to progressive simplification
                    $attempts = [60, 40, 25, 15];
                    
                    foreach ($attempts as $maxPoints) {
                        $simplified_points = $this->simplifyPathConservative($path_points, $maxPoints);
                        $test_path_string = 'color:0xff0000ff|weight:3|' . implode('|', $simplified_points);
                        
                        $test_params = $params;
                        $test_params['path'] = $test_path_string;
                        $test_url = $this->base_url . '?' . http_build_query($test_params);
                        
                        if (strlen($test_url) <= 2000) {
                            error_log("ThumbnailGenerator: Using {$maxPoints} points, URL length: " . strlen($test_url));
                            $path_string = $test_path_string;
                            $params['path'] = $path_string;
                            $url = $test_url;
                            break;
                        }
                    }
                }
            }
            
            $image_data = @file_get_contents($url);
            
            if ($image_data) {
                $filename = $this->thumbnail_dir . $assessment_number . '_boundary.png';
                $result = file_put_contents($filename, $image_data);
                if ($result) {
                    error_log("ThumbnailGenerator: Saved boundary overlay to {$filename}");
                    
                    // Update database to use boundary version
                    try {
                        require_once dirname(__DIR__) . '/config/database.php';
                        $db = getDB();
                        $stmt = $db->prepare("UPDATE properties SET thumbnail_path = ? WHERE assessment_number = ?");
                        $stmt->execute(['/assets/thumbnails/' . $assessment_number . '_boundary.png', $assessment_number]);
                        error_log("ThumbnailGenerator: Updated database with boundary thumbnail path");
                    } catch (Exception $e) {
                        error_log("ThumbnailGenerator: Database update failed: " . $e->getMessage());
                    }
                    
                    return '/assets/thumbnails/' . $assessment_number . '_boundary.png';
                }
            }
            
        } catch (Exception $e) {
            error_log("ThumbnailGenerator: Error generating boundary overlay: " . $e->getMessage());
        }
        
        return null; // Fall back to regular thumbnail generation
    }
    
    private function findTriangleCorners($points) {
        // For triangular properties, find the 3 main corner points
        if (count($points) < 10) {
            return $points; // Too few points to analyze
        }
        
        // Convert lat,lon strings back to coordinates for analysis
        $coords = [];
        foreach ($points as $point) {
            $parts = explode(',', $point);
            if (count($parts) == 2) {
                $coords[] = ['lat' => floatval($parts[0]), 'lon' => floatval($parts[1]), 'point' => $point];
            }
        }
        
        if (count($coords) < 10) {
            return $points;
        }
        
        // Find 3 points that are furthest apart (triangle corners)
        $corners = [];
        
        // Start with first point
        $corners[] = $coords[0];
        
        // Find point furthest from first point
        $maxDist1 = 0;
        $corner2Index = 0;
        for ($i = 1; $i < count($coords); $i++) {
            $dist = $this->calculateDistance($coords[0], $coords[$i]);
            if ($dist > $maxDist1) {
                $maxDist1 = $dist;
                $corner2Index = $i;
            }
        }
        $corners[] = $coords[$corner2Index];
        
        // Find point furthest from the line between first two corners
        $maxDist2 = 0;
        $corner3Index = 0;
        for ($i = 1; $i < count($coords); $i++) {
            if ($i == $corner2Index) continue;
            
            $dist = $this->calculateDistanceFromLine($coords[$i], $corners[0], $corners[1]);
            if ($dist > $maxDist2) {
                $maxDist2 = $dist;
                $corner3Index = $i;
            }
        }
        $corners[] = $coords[$corner3Index];
        
        // Add a few points along each edge for better shape
        $trianglePoints = [];
        foreach ($corners as $corner) {
            $trianglePoints[] = $corner['point'];
        }
        
        // Add the first point again to close the triangle
        $trianglePoints[] = $corners[0]['point'];
        
        error_log("ThumbnailGenerator: Identified triangle with " . count($trianglePoints) . " key points");
        return $trianglePoints;
    }
    
    private function calculateDistance($point1, $point2) {
        $latDiff = $point1['lat'] - $point2['lat'];
        $lonDiff = $point1['lon'] - $point2['lon'];
        return sqrt($latDiff * $latDiff + $lonDiff * $lonDiff);
    }
    
    private function calculateDistanceFromLine($point, $lineStart, $lineEnd) {
        // Calculate perpendicular distance from point to line
        $A = $point['lat'] - $lineStart['lat'];
        $B = $point['lon'] - $lineStart['lon'];
        $C = $lineEnd['lat'] - $lineStart['lat'];
        $D = $lineEnd['lon'] - $lineStart['lon'];
        
        $dot = $A * $C + $B * $D;
        $lenSq = $C * $C + $D * $D;
        
        if ($lenSq == 0) return sqrt($A * $A + $B * $B);
        
        $param = $dot / $lenSq;
        
        if ($param < 0) {
            return sqrt($A * $A + $B * $B);
        } elseif ($param > 1) {
            $dx = $point['lat'] - $lineEnd['lat'];
            $dy = $point['lon'] - $lineEnd['lon'];
            return sqrt($dx * $dx + $dy * $dy);
        } else {
            $projX = $lineStart['lat'] + $param * $C;
            $projY = $lineStart['lon'] + $param * $D;
            $dx = $point['lat'] - $projX;
            $dy = $point['lon'] - $projY;
            return sqrt($dx * $dx + $dy * $dy);
        }
    }
    
    private function simplifyPathConservative($points, $maxPoints) {
        // Fallback simplification method
        if (count($points) <= $maxPoints) {
            return $points;
        }
        
        $simplified = [$points[0]]; // Keep first
        $step = max(1, floor(count($points) / ($maxPoints - 2)));
        
        for ($i = $step; $i < count($points) - 1; $i += $step) {
            $simplified[] = $points[$i];
        }
        
        // Keep last if different from first
        if (end($points) !== $points[0]) {
            $simplified[] = end($points);
        }
        
        return $simplified;
    }
    
    public function getMobileHomeThumbnail($property) {
        $assessment_number = $property['assessment_number'];
        $address = $property['civic_address'] ?? '';
        
        // Try to get coordinates for mobile home
        $latitude = $property['latitude'] ?? null;
        $longitude = $property['longitude'] ?? null;
        
        // If no coordinates, try to geocode the address
        if (!$latitude || !$longitude) {
            $coordinates = $this->geocodeMobileHomeAddress($address);
            if ($coordinates) {
                $latitude = $coordinates['lat'];
                $longitude = $coordinates['lng'];
            }
        }
        
        // If still no coordinates, return mobile home placeholder
        if (!$latitude || !$longitude) {
            return $this->generateMobileHomePlaceholder($property);
        }
        
        // Generate mobile home thumbnail with special styling
        $filename = "{$assessment_number}_mobile_home.png";
        $thumbnail_file = $this->thumbnail_dir . $filename;
        
        // Check if file already exists
        if (file_exists($thumbnail_file)) {
            return "/assets/thumbnails/" . $filename;
        }
        
        try {
            // Build Google Maps Static API URL for mobile home
            $params = [
                'center' => "{$latitude},{$longitude}",
                'zoom' => '16', // Closer zoom for mobile home parks
                'size' => '300x200',
                'format' => 'png',
                'maptype' => 'hybrid', // Hybrid view shows more detail for mobile home parks
                'key' => $this->google_api_key
            ];
            
            // Add mobile home marker
            $params['markers'] = "color:orange|label:M|{$latitude},{$longitude}";
            
            $url = $this->base_url . '?' . http_build_query($params);
            
            error_log("Generating mobile home thumbnail: {$url}");
            
            // Download the image
            $context = stream_context_create([
                'http' => [
                    'timeout' => 30,
                    'user_agent' => 'Mozilla/5.0 (compatible; PHP ThumbnailGenerator)'
                ]
            ]);
            
            $image_data = file_get_contents($url, false, $context);
            
            if (!$image_data) {
                error_log("Failed to download mobile home thumbnail from Google Maps");
                return $this->generateMobileHomePlaceholder($property);
            }
            
            // Add mobile home overlay/badge
            $image_data = $this->addMobileHomeBadge($image_data);
            
            if (file_put_contents($thumbnail_file, $image_data)) {
                error_log("Mobile home thumbnail saved: {$thumbnail_file}");
                return "/assets/thumbnails/" . $filename;
            } else {
                error_log("Failed to save mobile home thumbnail: {$thumbnail_file}");
                return $this->generateMobileHomePlaceholder($property);
            }
            
        } catch (Exception $e) {
            error_log("Error generating mobile home thumbnail: " . $e->getMessage());
            return $this->generateMobileHomePlaceholder($property);
        }
    }
    
    private function geocodeMobileHomeAddress($address) {
        if (empty($address)) {
            return null;
        }
        
        try {
            // Clean up address for geocoding
            $address_clean = trim($address);
            
            // Extract trailer park name
            $park_patterns = [
                '/(.+?trailer park)/i',
                '/(.+?mobile park)/i',
                '/(.+?rv park)/i',
                '/(.+?mobile home park)/i'
            ];
            
            $search_addresses = [];
            
            foreach ($park_patterns as $pattern) {
                if (preg_match($pattern, $address_clean, $matches)) {
                    $park_name = trim($matches[1]);
                    $search_addresses[] = "{$park_name}, Nova Scotia, Canada";
                    break;
                }
            }
            
            // Add full address as fallback
            $search_addresses[] = "{$address_clean}, Nova Scotia, Canada";
            
            // Use Google Geocoding API
            foreach ($search_addresses as $search_address) {
                $geocode_url = "https://maps.googleapis.com/maps/api/geocode/json?" . http_build_query([
                    'address' => $search_address,
                    'key' => $this->google_api_key
                ]);
                
                $geocode_response = file_get_contents($geocode_url);
                if ($geocode_response) {
                    $geocode_data = json_decode($geocode_response, true);
                    
                    if ($geocode_data['status'] === 'OK' && !empty($geocode_data['results'])) {
                        $location = $geocode_data['results'][0]['geometry']['location'];
                        error_log("Geocoded mobile home address '{$search_address}': {$location['lat']}, {$location['lng']}");
                        return ['lat' => $location['lat'], 'lng' => $location['lng']];
                    }
                }
            }
            
            // Default Nova Scotia coordinates if geocoding fails
            error_log("Geocoding failed for mobile home address: {$address}");
            return ['lat' => 44.6820, 'lng' => -63.7443];
            
        } catch (Exception $e) {
            error_log("Error geocoding mobile home address: " . $e->getMessage());
            return null;
        }
    }
    
    private function addMobileHomeBadge($image_data) {
        try {
            // Create image from data
            $image = imagecreatefromstring($image_data);
            if (!$image) {
                return $image_data; // Return original if processing fails
            }
            
            // Add "Mobile Home" badge in bottom right corner
            $badge_color = imagecolorallocate($image, 255, 140, 0); // Orange
            $text_color = imagecolorallocate($image, 255, 255, 255); // White
            $border_color = imagecolorallocate($image, 0, 0, 0); // Black
            
            // Badge dimensions
            $badge_width = 80;
            $badge_height = 20;
            $image_width = imagesx($image);
            $image_height = imagesy($image);
            
            $badge_x = $image_width - $badge_width - 5;
            $badge_y = $image_height - $badge_height - 5;
            
            // Draw badge background
            imagefilledrectangle($image, $badge_x, $badge_y, $badge_x + $badge_width, $badge_y + $badge_height, $badge_color);
            imagerectangle($image, $badge_x, $badge_y, $badge_x + $badge_width, $badge_y + $badge_height, $border_color);
            
            // Add text
            $font_size = 2;
            $text = "MOBILE HOME";
            $text_width = imagefontwidth($font_size) * strlen($text);
            $text_x = $badge_x + ($badge_width - $text_width) / 2;
            $text_y = $badge_y + ($badge_height - imagefontheight($font_size)) / 2;
            
            imagestring($image, $font_size, $text_x, $text_y, $text, $text_color);
            
            // Convert back to PNG data
            ob_start();
            imagepng($image);
            $modified_image_data = ob_get_contents();
            ob_end_clean();
            
            imagedestroy($image);
            
            return $modified_image_data;
            
        } catch (Exception $e) {
            error_log("Error adding mobile home badge: " . $e->getMessage());
            return $image_data; // Return original if processing fails
        }
    }
    
    private function generateMobileHomePlaceholder($property) {
        // Generate SVG placeholder for mobile homes
        $assessment_number = $property['assessment_number'] ?? 'Unknown';
        $address = $property['civic_address'] ?? 'Mobile Home Property';
        
        // Truncate address if too long
        if (strlen($address) > 30) {
            $address = substr($address, 0, 27) . '...';
        }
        
        $svg = '
            <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
                <rect width="300" height="200" fill="#fff3cd" stroke="#ffc107" stroke-width="2"/>
                <rect x="50" y="80" width="200" height="40" fill="#ffc107" rx="5"/>
                <text x="150" y="60" font-family="Arial" font-size="12" fill="#856404" text-anchor="middle" font-weight="bold">MOBILE HOME</text>
                <text x="150" y="105" font-family="Arial" font-size="10" fill="#ffffff" text-anchor="middle">' . htmlspecialchars($assessment_number) . '</text>
                <text x="150" y="140" font-family="Arial" font-size="8" fill="#856404" text-anchor="middle">' . htmlspecialchars($address) . '</text>
                <text x="150" y="155" font-family="Arial" font-size="8" fill="#856404" text-anchor="middle">Location coordinates needed</text>
                <circle cx="75" cy="100" r="8" fill="#ffffff" opacity="0.8"/>
                <text x="75" y="105" font-family="Arial" font-size="10" fill="#ffc107" text-anchor="middle">🏠</text>
            </svg>
        ';
        
        return 'data:image/svg+xml;base64,' . base64encode($svg);
    }

    public function generateThumbnail($assessment_number, $latitude = null, $longitude = null, $pid_number = null, $address = null, $municipality = null) {
        error_log("ThumbnailGenerator: Generating thumbnail for {$assessment_number}");
        
        // Check if thumbnail already exists
        $thumbnail_path = '/assets/thumbnails/' . $assessment_number . '.png';
        $thumbnail_file = $this->thumbnail_dir . $assessment_number . '.png';
        
        if (file_exists($thumbnail_file)) {
            return $thumbnail_path;
        }
        
        // Call backend API if no coordinates
        if ($pid_number && (!$latitude || !$longitude)) {
            error_log("Calling backend API for PID: {$pid_number}");
            
            // Use backend URL (fallback to localhost if API_BASE_URL not defined)
            $backend_base = defined('API_BASE_URL') ? API_BASE_URL : 'http://localhost:8001/api';
            $backend_url = $backend_base . "/query-ns-government-parcel/{$pid_number}";
            $response = @file_get_contents($backend_url);
            
            if ($response) {
                $data = json_decode($response, true);
                if ($data && $data['found'] && $data['center']) {
                    $latitude = $data['center']['lat'];
                    $longitude = $data['center']['lon'];
                    
                    error_log("Updated {$assessment_number} with coordinates: {$latitude}, {$longitude}");
                    
                    // If we have boundary geometry, try to create a boundary overlay
                    if (isset($data['geometry']) && isset($data['bbox'])) {
                        $boundary_thumbnail = $this->generateBoundaryOverlayThumbnail($assessment_number, $data, $latitude, $longitude);
                        if ($boundary_thumbnail) {
                            return $boundary_thumbnail;
                        }
                    }
                }
            }
        }
        
        // Store the coordinates for later retrieval
        $this->lastLatitude = $latitude;
        $this->lastLongitude = $longitude;
        
        if (!$latitude || !$longitude) {
            return '/assets/images/placeholder-property.jpg';
        }
        
        // Generate Google Maps thumbnail
        $params = [
            'key' => $this->google_api_key,
            'center' => $latitude . ',' . $longitude,
            'zoom' => '17',
            'size' => '300x200',
            'maptype' => 'satellite',
            'format' => 'png',
            'markers' => 'color:red|size:small|' . $latitude . ',' . $longitude
        ];
        
        $url = $this->base_url . '?' . http_build_query($params);
        $image_data = @file_get_contents($url);
        
        if ($image_data) {
            $filename = $this->thumbnail_dir . $assessment_number . '.png';
            $result = file_put_contents($filename, $image_data);
            error_log("ThumbnailGenerator: Saved image to {$filename}, bytes written: " . ($result ?: 'FAILED'));
            return $thumbnail_path;
        }
        
        return '/assets/images/placeholder-property.jpg';
    }
}
?>
