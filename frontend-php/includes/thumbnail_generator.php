<?php
class ThumbnailGenerator {
    private $google_api_key;
    private $thumbnail_dir;
    private $base_url;
    
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
    
    public function getThumbnail($property) {
        $assessment_number = $property['assessment_number'];
        $pid_number = $property['pid_number'];
        $latitude = $property['latitude'];
        $longitude = $property['longitude'];
        
        // Call backend API if no coordinates
        if ($pid_number && (!$latitude || !$longitude)) {
            error_log("Calling backend API for PID: {$pid_number}");
            
            $backend_url = "http://localhost:8001/api/query-ns-government-parcel/{$pid_number}";
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
}
?>
