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
            mkdir($this->thumbnail_dir, 0755, true);
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
                }
            }
        }
        
        if (!$latitude || !$longitude) {
            return 'data:image/svg+xml;base64,' . base64_encode('<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="200" fill="#667eea"/><text x="150" y="100" font-family="Arial" font-size="16" fill="white" text-anchor="middle">Property Location</text></svg>');
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
            return '/assets/thumbnails/' . $assessment_number . '.png';
        }
        
        return 'data:image/svg+xml;base64,' . base64_encode('<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="200" fill="#667eea"/><text x="150" y="100" font-family="Arial" font-size="16" fill="white" text-anchor="middle">Property Location</text></svg>');
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
