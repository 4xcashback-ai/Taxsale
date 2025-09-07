<?php
/**
 * Property Boundary Thumbnail Generator
 * Generates Google Maps Static API images with property boundaries
 */

class ThumbnailGenerator {
    private $google_api_key;
    private $thumbnail_dir;
    private $base_url;
    
    public function __construct($api_key) {
        $this->google_api_key = $api_key;
        $this->thumbnail_dir = $_SERVER['DOCUMENT_ROOT'] . '/assets/thumbnails/';
        $this->base_url = 'https://maps.googleapis.com/maps/api/staticmap';
        
        // Create thumbnails directory if it doesn't exist
        if (!is_dir($this->thumbnail_dir)) {
            mkdir($this->thumbnail_dir, 0755, true);
        }
    }
    
    /**
     * Generate or get existing thumbnail for a property
     */
    public function getThumbnail($property) {
        $assessment_number = $property['assessment_number'];
        $thumbnail_file = $this->thumbnail_dir . $assessment_number . '.png';
        $thumbnail_url = '/assets/thumbnails/' . $assessment_number . '.png';
        
        // Check if thumbnail already exists and is recent (less than 30 days old)
        if (file_exists($thumbnail_file) && (time() - filemtime($thumbnail_file)) < (30 * 24 * 60 * 60)) {
            return $thumbnail_url;
        }
        
        // Generate new thumbnail
        return $this->generateThumbnail($property);
    }
    
    /**
     * Generate a new thumbnail using Google Maps Static API
     */
    private function generateThumbnail($property) {
        $assessment_number = $property['assessment_number'];
        $pid_number = $property['pid_number'];
        $latitude = $property['latitude'];
        $longitude = $property['longitude'];
        $boundary_data = $property['boundary_data'];
        
        // Try to get boundary data from ArcGIS if we have a PID but no boundary data
        if ($pid_number && (!$boundary_data || empty($boundary_data))) {
            $boundary_data = $this->fetchBoundaryFromArcGIS($pid_number, $property);
            if ($boundary_data) {
                // Update the database with the fetched boundary data
                $this->updatePropertyBoundary($assessment_number, $boundary_data);
            }
        }
        
        // If still no coordinates after ArcGIS fetch, return placeholder
        if (!$latitude || !$longitude) {
            return $this->getPlaceholderImage();
        }
        
        // Build Google Maps Static API URL
        $params = [
            'key' => $this->google_api_key,
            'center' => $latitude . ',' . $longitude,
            'zoom' => '17',
            'size' => '300x200',
            'maptype' => 'satellite',
            'format' => 'png'
        ];
        
        // Add property boundary overlay if available
        if ($boundary_data && !empty($boundary_data)) {
            $boundary_json = is_string($boundary_data) ? json_decode($boundary_data, true) : $boundary_data;
            if ($boundary_json && isset($boundary_json['coordinates'])) {
                $path_string = $this->buildPathString($boundary_json['coordinates']);
                if ($path_string) {
                    $params['path'] = 'color:0xff0000ff|weight:3|fillcolor:0xff000033|' . $path_string;
                }
            }
        }
        
        // Add center marker
        $params['markers'] = 'color:red|size:small|' . $latitude . ',' . $longitude;
        
        // Build URL
        $url = $this->base_url . '?' . http_build_query($params);
        
        // Download and save image
        try {
            $image_data = file_get_contents($url);
            if ($image_data) {
                $thumbnail_file = $this->thumbnail_dir . $assessment_number . '.png';
                file_put_contents($thumbnail_file, $image_data);
                return '/assets/thumbnails/' . $assessment_number . '.png';
            }
        } catch (Exception $e) {
            error_log("Thumbnail generation failed for {$assessment_number}: " . $e->getMessage());
        }
        
        return $this->getPlaceholderImage();
    }
    
    /**
     * Fetch boundary data from ArcGIS service using PID
     */
    private function fetchBoundaryFromArcGIS($pid_number, $property) {
        try {
            // ArcGIS REST API endpoint for Nova Scotia property parcels
            $arcgis_url = 'https://services1.arcgis.com/mCp8h70YF1NUbmGD/arcgis/rest/services/Property_Parcel_Boundaries/FeatureServer/0/query';
            
            $params = [
                'where' => "PID = '{$pid_number}'",
                'outFields' => '*',
                'geometryType' => 'esriGeometryPolygon',
                'spatialRel' => 'esriSpatialRelIntersects',
                'f' => 'json',
                'returnGeometry' => 'true',
                'outSR' => '4326' // WGS84 coordinate system
            ];
            
            $url = $arcgis_url . '?' . http_build_query($params);
            
            $context = stream_context_create([
                'http' => [
                    'method' => 'GET',
                    'timeout' => 30,
                    'header' => [
                        'User-Agent: Tax Sale Compass/1.0',
                        'Accept: application/json'
                    ]
                ]
            ]);
            
            $response = file_get_contents($url, false, $context);
            
            if ($response === false) {
                error_log("Failed to fetch ArcGIS data for PID: {$pid_number}");
                return null;
            }
            
            $data = json_decode($response, true);
            
            if (!$data || !isset($data['features']) || empty($data['features'])) {
                error_log("No ArcGIS features found for PID: {$pid_number}");
                return null;
            }
            
            $feature = $data['features'][0];
            $geometry = $feature['geometry'];
            
            if (!$geometry || !isset($geometry['rings'])) {
                error_log("No geometry rings found for PID: {$pid_number}");
                return null;
            }
            
            // Convert ArcGIS geometry to our format
            $coordinates = [];
            foreach ($geometry['rings'][0] as $point) {
                $coordinates[] = [$point[0], $point[1]]; // [longitude, latitude]
            }
            
            // Calculate center point if not available
            if (!$property['latitude'] || !$property['longitude']) {
                $center = $this->calculatePolygonCenter($coordinates);
                $this->updatePropertyCoordinates($property['assessment_number'], $center['lat'], $center['lng']);
            }
            
            return json_encode([
                'type' => 'Polygon',
                'coordinates' => [$coordinates]
            ]);
            
        } catch (Exception $e) {
            error_log("ArcGIS API error for PID {$pid_number}: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Calculate the center point of a polygon
     */
    private function calculatePolygonCenter($coordinates) {
        $lat_sum = 0;
        $lng_sum = 0;
        $count = count($coordinates);
        
        foreach ($coordinates as $coord) {
            $lng_sum += $coord[0];
            $lat_sum += $coord[1];
        }
        
        return [
            'lat' => $lat_sum / $count,
            'lng' => $lng_sum / $count
        ];
    }
    
    /**
     * Update property with boundary data in database
     */
    private function updatePropertyBoundary($assessment_number, $boundary_data) {
        try {
            require_once dirname(__DIR__) . '/config/database.php';
            $db = getDB();
            
            $stmt = $db->prepare("UPDATE properties SET boundary_data = ?, updated_at = NOW() WHERE assessment_number = ?");
            return $stmt->execute([$boundary_data, $assessment_number]);
        } catch (Exception $e) {
            error_log("Failed to update boundary data for {$assessment_number}: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Update property coordinates in database
     */
    private function updatePropertyCoordinates($assessment_number, $latitude, $longitude) {
        try {
            require_once dirname(__DIR__) . '/config/database.php';
            $db = getDB();
            
            $stmt = $db->prepare("UPDATE properties SET latitude = ?, longitude = ?, updated_at = NOW() WHERE assessment_number = ?");
            return $stmt->execute([$latitude, $longitude, $assessment_number]);
        } catch (Exception $e) {
            error_log("Failed to update coordinates for {$assessment_number}: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Build path string for Google Maps overlay
     */
    /**
     * Build path string for Google Maps overlay
     */
    private function buildPathString($coordinates) {
        if (!is_array($coordinates) || empty($coordinates)) {
            return null;
        }
        
        $path_points = [];
        
        // Handle GeoJSON format: coordinates[0] contains the ring
        if (isset($coordinates[0]) && is_array($coordinates[0])) {
            $ring = $coordinates[0];
            foreach ($ring as $coord) {
                if (is_array($coord) && count($coord) >= 2) {
                    // coord[0] = longitude, coord[1] = latitude
                    $path_points[] = $coord[1] . ',' . $coord[0]; // Google Maps wants lat,lng
                }
            }
        } else {
            // Handle simple coordinate array
            foreach ($coordinates as $coord) {
                if (is_array($coord) && count($coord) >= 2) {
                    $path_points[] = $coord[1] . ',' . $coord[0]; // lat,lng format
                }
            }
        }
        
        if (empty($path_points)) {
            return null;
        }
        
        // Close the polygon by adding first point at the end if not already closed
        if (count($path_points) > 2 && $path_points[0] !== $path_points[count($path_points) - 1]) {
            $path_points[] = $path_points[0];
        }
        
        return implode('|', $path_points);
    }
    
    /**
     * Get placeholder image for properties without coordinates
     */
    private function getPlaceholderImage() {
        return 'data:image/svg+xml;base64,' . base64_encode('
            <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
                <rect width="300" height="200" fill="#667eea"/>
                <text x="150" y="100" font-family="Arial, sans-serif" font-size="16" 
                      fill="white" text-anchor="middle" dy="0.3em">Property Location</text>
                <text x="150" y="120" font-family="Arial, sans-serif" font-size="12" 
                      fill="white" text-anchor="middle" dy="0.3em">Map Not Available</text>
            </svg>
        ');
    }
    
    /**
     * Clean old thumbnails (older than 60 days)
     */
    public function cleanOldThumbnails() {
        $files = glob($this->thumbnail_dir . '*.png');
        $cutoff_time = time() - (60 * 24 * 60 * 60); // 60 days
        
        foreach ($files as $file) {
            if (filemtime($file) < $cutoff_time) {
                unlink($file);
            }
        }
    }
}
?>