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
        $pid_number = $property['pid_number'];
        $latitude = $property['latitude'];
        $longitude = $property['longitude'];
        
        // Debug: Log what we received
        error_log("=== THUMBNAIL DEBUG START for {$assessment_number} ===");
        error_log("ThumbnailGenerator: PID={$pid_number}, Coords={$latitude},{$longitude}");
        error_log("ThumbnailGenerator: DB thumbnail_path=" . ($property['thumbnail_path'] ?? 'NULL'));
        error_log("ThumbnailGenerator: Thumbnail directory=" . $this->thumbnail_dir);
        error_log("ThumbnailGenerator: Directory exists=" . (is_dir($this->thumbnail_dir) ? 'YES' : 'NO'));
        error_log("ThumbnailGenerator: Directory writable=" . (is_writable($this->thumbnail_dir) ? 'YES' : 'NO'));
        
        // First check if we already have a pre-generated thumbnail path in the database
        if (isset($property['thumbnail_path']) && !empty($property['thumbnail_path'])) {
            $thumbnail_file = dirname(__DIR__) . $property['thumbnail_path'];
            error_log("ThumbnailGenerator: Checking pre-generated file: {$thumbnail_file}");
            
            // Verify the file actually exists
            if (file_exists($thumbnail_file)) {
                error_log("ThumbnailGenerator: Using pre-generated thumbnail: {$property['thumbnail_path']}");
                error_log("=== THUMBNAIL DEBUG END - USING PRE-GENERATED ===");
                return $property['thumbnail_path'];
            } else {
                error_log("ThumbnailGenerator: Pre-generated thumbnail file missing: {$thumbnail_file}");
            }
        }
        
        error_log("ThumbnailGenerator: No pre-generated thumbnail found, falling back to on-demand generation");
        
        // Fallback to on-demand generation
        // Call backend API if no coordinates
        if ($pid_number && (!$latitude || !$longitude)) {
            error_log("ThumbnailGenerator: Calling backend API for PID: {$pid_number}");
            
            // Use backend URL (fallback to localhost if API_BASE_URL not defined)
            $backend_base = defined('API_BASE_URL') ? API_BASE_URL : 'http://localhost:8001/api';
            $backend_url = $backend_base . "/query-ns-government-parcel/{$pid_number}";
            error_log("ThumbnailGenerator: Backend URL: {$backend_url}");
            
            $response = @file_get_contents($backend_url);
            
            if ($response) {
                error_log("ThumbnailGenerator: Backend API response received, length=" . strlen($response));
                $data = json_decode($response, true);
                if ($data && $data['found'] && $data['center']) {
                    $latitude = $data['center']['lat'];
                    $longitude = $data['center']['lon'];
                    error_log("ThumbnailGenerator: Got coordinates from API: {$latitude},{$longitude}");
                    
                    // Update database
                    try {
                        require_once dirname(__DIR__) . '/config/database.php';
                        $db = getDB();
                        $stmt = $db->prepare("UPDATE properties SET latitude = ?, longitude = ? WHERE assessment_number = ?");
                        $stmt->execute([$latitude, $longitude, $assessment_number]);
                        error_log("ThumbnailGenerator: Updated coordinates in database");
                    } catch (Exception $e) {
                        error_log("ThumbnailGenerator: Database update failed: " . $e->getMessage());
                    }
                    
                    // If we have boundary geometry, try to create a boundary overlay
                    if (isset($data['geometry']) && isset($data['bbox'])) {
                        error_log("ThumbnailGenerator: Attempting boundary overlay generation");
                        $boundary_result = $this->generateBoundaryOverlayThumbnail($assessment_number, $data, $latitude, $longitude);
                        if ($boundary_result) {
                            error_log("ThumbnailGenerator: Boundary overlay created: {$boundary_result}");
                            error_log("=== THUMBNAIL DEBUG END - BOUNDARY OVERLAY ===");
                            return $boundary_result;
                        } else {
                            error_log("ThumbnailGenerator: Boundary overlay failed, falling back to basic thumbnail");
                        }
                    }
                } else {
                    error_log("ThumbnailGenerator: Backend API returned no valid data");
                }
            } else {
                error_log("ThumbnailGenerator: Backend API call failed");
            }
        }
        
        if (!$latitude || !$longitude) {
            error_log("ThumbnailGenerator: No coordinates available, returning placeholder SVG");
            error_log("=== THUMBNAIL DEBUG END - NO COORDINATES ===");
            return 'data:image/svg+xml;base64,' . base64_encode('<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="200" fill="#667eea"/><text x="150" y="100" font-family="Arial" font-size="16" fill="white" text-anchor="middle">Property Location</text></svg>');
        }
        
        // Generate thumbnail file if it doesn't exist
        $filename = $this->thumbnail_dir . $assessment_number . '.png';
        error_log("ThumbnailGenerator: Target filename: {$filename}");
        error_log("ThumbnailGenerator: File exists: " . (file_exists($filename) ? 'YES' : 'NO'));
        
        if (!file_exists($filename)) {
            error_log("ThumbnailGenerator: Creating missing thumbnail file");
            
            // Check if directory is writable
            if (!is_writable($this->thumbnail_dir)) {
                error_log("ThumbnailGenerator: Directory not writable, attempting to fix permissions");
                $chmod_result = @chmod($this->thumbnail_dir, 0777);
                error_log("ThumbnailGenerator: chmod result: " . ($chmod_result ? 'SUCCESS' : 'FAILED'));
            }
            
            // Generate enhanced Google Maps thumbnail
            $params = [
                'key' => $this->google_api_key,
                'center' => $latitude . ',' . $longitude,
                'zoom' => '18',
                'size' => '300x200',
                'maptype' => 'satellite',
                'format' => 'png',
                'markers' => 'color:red|size:mid|' . $latitude . ',' . $longitude
            ];
            
            $url = $this->base_url . '?' . http_build_query($params);
            error_log("ThumbnailGenerator: Google Maps URL: " . substr($url, 0, 150) . "...");
            
            $image_data = @file_get_contents($url);
            
            if ($image_data) {
                error_log("ThumbnailGenerator: Downloaded image data, size: " . strlen($image_data) . " bytes");
                $result = @file_put_contents($filename, $image_data);
                if ($result) {
                    error_log("ThumbnailGenerator: Successfully wrote file, bytes: {$result}");
                    
                    // Update database with correct path
                    try {
                        require_once dirname(__DIR__) . '/config/database.php';
                        $db = getDB();
                        $stmt = $db->prepare("UPDATE properties SET thumbnail_path = ? WHERE assessment_number = ?");
                        $stmt->execute(['/assets/thumbnails/' . $assessment_number . '.png', $assessment_number]);
                        error_log("ThumbnailGenerator: Updated database thumbnail_path");
                    } catch (Exception $e) {
                        error_log("ThumbnailGenerator: Database update failed: " . $e->getMessage());
                    }
                    
                    error_log("=== THUMBNAIL DEBUG END - FILE CREATED ===");
                    return '/assets/thumbnails/' . $assessment_number . '.png';
                } else {
                    error_log("ThumbnailGenerator: FAILED to write file - check permissions");
                    error_log("ThumbnailGenerator: Directory info - " . ls_info($this->thumbnail_dir));
                    error_log("=== THUMBNAIL DEBUG END - WRITE FAILED ===");
                    return 'data:image/svg+xml;base64,' . base64_encode('<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="200" fill="#dc3545"/><text x="150" y="100" font-family="Arial" font-size="12" fill="white" text-anchor="middle">Write Error</text></svg>');
                }
            } else {
                error_log("ThumbnailGenerator: FAILED to download from Google Maps API");
                error_log("ThumbnailGenerator: API Key present: " . (empty($this->google_api_key) ? 'NO' : 'YES'));
                error_log("=== THUMBNAIL DEBUG END - DOWNLOAD FAILED ===");
                return 'data:image/svg+xml;base64,' . base64_encode('<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="200" fill="#ffc107"/><text x="150" y="100" font-family="Arial" font-size="12" fill="black" text-anchor="middle">API Error</text></svg>');
            }
        }
        
        error_log("=== THUMBNAIL DEBUG END - RETURNING EXISTING FILE ===");
        return '/assets/thumbnails/' . $assessment_number . '.png';
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
            
            // Calculate zoom level - add some padding so boundaries aren't at edge
            $padded_span = $max_span * 1.3; // 30% padding
            
            // Determine zoom level based on span (approximate degrees per zoom level)
            if ($padded_span > 0.01) {
                $zoom = 14; // Large properties (rural, big lots)
            } elseif ($padded_span > 0.005) {
                $zoom = 15; // Medium-large properties
            } elseif ($padded_span > 0.002) {
                $zoom = 16; // Medium properties
            } elseif ($padded_span > 0.001) {
                $zoom = 17; // Small-medium properties
            } elseif ($padded_span > 0.0005) {
                $zoom = 18; // Small properties (typical residential)
            } else {
                $zoom = 19; // Very small properties
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
