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
        error_log("ThumbnailGenerator: getThumbnail called for {$assessment_number}, thumbnail_path: " . ($property['thumbnail_path'] ?? 'NULL'));
        
        // First check if we already have a pre-generated thumbnail path in the database
        if (isset($property['thumbnail_path']) && !empty($property['thumbnail_path'])) {
            $thumbnail_file = dirname(__DIR__) . $property['thumbnail_path'];
            // Verify the file actually exists
            if (file_exists($thumbnail_file)) {
                error_log("ThumbnailGenerator: Using pre-generated thumbnail: {$property['thumbnail_path']}");
                return $property['thumbnail_path'];
            } else {
                error_log("ThumbnailGenerator: Pre-generated thumbnail file missing: {$thumbnail_file}");
            }
        }
        
        error_log("ThumbnailGenerator: No pre-generated thumbnail found, falling back to on-demand generation for {$assessment_number}");
        
        // Fallback to on-demand generation
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
                    
                    // Update database
                    require_once dirname(__DIR__) . '/config/database.php';
                    $db = getDB();
                    $stmt = $db->prepare("UPDATE properties SET latitude = ?, longitude = ? WHERE assessment_number = ?");
                    $stmt->execute([$latitude, $longitude, $assessment_number]);
                    
                    error_log("Updated {$assessment_number} with coordinates: {$latitude}, {$longitude}");
                    
                    // If we have boundary geometry, try to create a boundary overlay
                    if (isset($data['geometry']) && isset($data['bbox'])) {
                        return $this->generateBoundaryOverlayThumbnail($assessment_number, $data, $latitude, $longitude);
                    }
                }
            }
        }
        
        if (!$latitude || !$longitude) {
            return 'data:image/svg+xml;base64,' . base64_encode('<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="200" fill="#667eea"/><text x="150" y="100" font-family="Arial" font-size="16" fill="white" text-anchor="middle">Property Location</text></svg>');
        }
        
        // Generate thumbnail file if it doesn't exist
        $filename = $this->thumbnail_dir . $assessment_number . '.png';
        if (!file_exists($filename)) {
            error_log("ThumbnailGenerator: Creating missing thumbnail file for {$assessment_number}");
            
            // Check if directory is writable
            if (!is_writable($this->thumbnail_dir)) {
                error_log("ThumbnailGenerator: Directory not writable, attempting to fix permissions");
                @chmod($this->thumbnail_dir, 0777);
            }
            
            // Generate enhanced Google Maps thumbnail with better zoom and styling
            $params = [
                'key' => $this->google_api_key,
                'center' => $latitude . ',' . $longitude,
                'zoom' => '18',  // Higher zoom for better detail
                'size' => '300x200',
                'maptype' => 'satellite',
                'format' => 'png',
                'markers' => 'color:red|size:mid|' . $latitude . ',' . $longitude
            ];
            
            $url = $this->base_url . '?' . http_build_query($params);
            $image_data = @file_get_contents($url);
            
            if ($image_data) {
                $result = @file_put_contents($filename, $image_data);
                if ($result) {
                    error_log("ThumbnailGenerator: Created thumbnail file, bytes written: {$result}");
                    
                    // Update database with correct path
                    try {
                        require_once dirname(__DIR__) . '/config/database.php';
                        $db = getDB();
                        $stmt = $db->prepare("UPDATE properties SET thumbnail_path = ? WHERE assessment_number = ?");
                        $stmt->execute(['/assets/thumbnails/' . $assessment_number . '.png', $assessment_number]);
                        error_log("ThumbnailGenerator: Updated database thumbnail_path for {$assessment_number}");
                    } catch (Exception $e) {
                        error_log("ThumbnailGenerator: Database update failed: " . $e->getMessage());
                    }
                } else {
                    error_log("ThumbnailGenerator: FAILED to write thumbnail file - check directory permissions: " . $this->thumbnail_dir);
                    // Return a fallback image URL instead of file path if we can't create the file
                    return 'data:image/svg+xml;base64,' . base64_encode('<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="200" fill="#dc3545"/><text x="150" y="100" font-family="Arial" font-size="12" fill="white" text-anchor="middle">Thumbnail Error</text></svg>');
                }
            } else {
                error_log("ThumbnailGenerator: FAILED to download image from Google Maps API");
                return 'data:image/svg+xml;base64,' . base64_encode('<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="200" fill="#ffc107"/><text x="150" y="100" font-family="Arial" font-size="12" fill="black" text-anchor="middle">API Error</text></svg>');
            }
        }
        
        return '/assets/thumbnails/' . $assessment_number . '.png';
    }
    
    private function generateBoundaryOverlayThumbnail($assessment_number, $boundary_data, $center_lat, $center_lon) {
        error_log("ThumbnailGenerator: Generating boundary overlay for {$assessment_number}");
        
        try {
            // Extract geometry rings for path overlay
            $geometry = $boundary_data['geometry'];
            if (!$geometry || !isset($geometry['rings']) || empty($geometry['rings'])) {
                error_log("ThumbnailGenerator: No valid rings in geometry data");
                return null;
            }
            
            // Build path parameter for Google Maps Static API
            $path_points = [];
            foreach ($geometry['rings'] as $ring) {
                foreach ($ring as $coord) {
                    $path_points[] = $coord[1] . ',' . $coord[0]; // lat,lon format
                }
            }
            
            // Limit path points to avoid URL length issues (Google Maps has limits)
            if (count($path_points) > 100) {
                // Take every nth point to reduce complexity
                $step = ceil(count($path_points) / 100);
                $reduced_points = [];
                for ($i = 0; $i < count($path_points); $i += $step) {
                    $reduced_points[] = $path_points[$i];
                }
                $path_points = $reduced_points;
            }
            
            // Close the path by adding first point at the end
            if (count($path_points) > 0) {
                $path_points[] = $path_points[0];
            }
            
            $path_string = 'color:0xff0000ff|weight:2|' . implode('|', $path_points);
            
            // Generate map with boundary overlay
            $params = [
                'key' => $this->google_api_key,
                'center' => $center_lat . ',' . $center_lon,
                'zoom' => '17',
                'size' => '300x200',
                'maptype' => 'satellite',
                'format' => 'png',
                'path' => $path_string,
                'markers' => 'color:red|size:small|' . $center_lat . ',' . $center_lon
            ];
            
            $url = $this->base_url . '?' . http_build_query($params);
            error_log("ThumbnailGenerator: Boundary overlay URL: " . substr($url, 0, 200) . '...');
            
            $image_data = @file_get_contents($url);
            
            if ($image_data) {
                $filename = $this->thumbnail_dir . $assessment_number . '_boundary.png';
                $result = file_put_contents($filename, $image_data);
                if ($result) {
                    error_log("ThumbnailGenerator: Saved boundary overlay to {$filename}");
                    return '/assets/thumbnails/' . $assessment_number . '_boundary.png';
                }
            }
            
        } catch (Exception $e) {
            error_log("ThumbnailGenerator: Error generating boundary overlay: " . $e->getMessage());
        }
        
        return null; // Fall back to regular thumbnail generation
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
