<?php
/**
 * Batch Thumbnail Generator for Tax Sale Compass
 * Generates thumbnails for all properties with PID numbers
 * Should run after scraping new properties
 */

require_once dirname(__DIR__) . '/frontend-php/config/database.php';
require_once dirname(__DIR__) . '/frontend-php/includes/thumbnail_generator.php';

class BatchThumbnailGenerator {
    private $pdo;
    private $thumbnailGenerator;
    private $logFile;
    private $batchSize = 50; // Process properties in batches
    private $delayBetweenBatches = 2; // Seconds between batches (API rate limiting)
    
    public function __construct() {
        $this->pdo = getDB();
        $this->thumbnailGenerator = new ThumbnailGenerator('AIzaSyBqJZiAhODPGKf6NLZSUOc6BQmMJtVg7bA'); // Google Maps API key
        $this->logFile = '/var/log/thumbnail_generation.log';
        
        $this->log("=== Batch Thumbnail Generation Started ===");
    }
    
    public function generateMissingThumbnails() {
        $this->log("Scanning for properties needing thumbnails...");
        
        // Get properties that don't have thumbnails yet and have PID numbers
        $sql = "SELECT id, assessment_number, pid_number, latitude, longitude, civic_address, municipality 
                FROM properties 
                WHERE pid_number IS NOT NULL 
                AND pid_number != '' 
                AND pid_number != 'N/A'
                AND (thumbnail_path IS NULL OR thumbnail_path = '')
                ORDER BY id";
        
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute();
        $properties = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        $totalProperties = count($properties);
        $this->log("Found {$totalProperties} properties needing thumbnails");
        
        if ($totalProperties === 0) {
            $this->log("No thumbnails to generate. Exiting.");
            return;
        }
        
        $processed = 0;
        $successful = 0;
        $failed = 0;
        
        // Process in batches
        $batches = array_chunk($properties, $this->batchSize);
        
        foreach ($batches as $batchIndex => $batch) {
            $this->log("Processing batch " . ($batchIndex + 1) . "/" . count($batches) . " (" . count($batch) . " properties)");
            
            foreach ($batch as $property) {
                $result = $this->generateThumbnailForProperty($property);
                
                if ($result['success']) {
                    $successful++;
                    $this->updatePropertyThumbnail($property['id'], $result['thumbnail_path'], $result['coordinates']);
                } else {
                    $failed++;
                    $this->log("Failed: {$property['assessment_number']} - {$result['error']}");
                }
                
                $processed++;
                
                // Progress indicator
                if ($processed % 10 === 0) {
                    $this->log("Progress: {$processed}/{$totalProperties} ({$successful} successful, {$failed} failed)");
                }
                
                // Small delay between individual requests
                usleep(500000); // 0.5 seconds
            }
            
            // Delay between batches to avoid overwhelming APIs
            if ($batchIndex < count($batches) - 1) {
                $this->log("Batch completed. Waiting {$this->delayBetweenBatches} seconds before next batch...");
                sleep($this->delayBetweenBatches);
            }
        }
        
        $this->log("=== Batch Generation Complete ===");
        $this->log("Total processed: {$processed}");
        $this->log("Successful: {$successful}");
        $this->log("Failed: {$failed}");
        $this->log("Success rate: " . round(($successful / $processed) * 100, 2) . "%");
    }
    
    private function generateThumbnailForProperty($property) {
        try {
            $assessmentNumber = $property['assessment_number'];
            $pidNumber = $property['pid_number'];
            
            $this->log("Generating thumbnail for {$assessmentNumber} (PID: {$pidNumber})");
            
            // Check if we already have coordinates
            $latitude = $property['latitude'];
            $longitude = $property['longitude'];
            
            // Generate thumbnail (this will fetch boundary data if needed)
            $thumbnailPath = $this->thumbnailGenerator->generateThumbnail(
                $assessmentNumber,
                $latitude,
                $longitude,
                $pidNumber,
                $property['civic_address'],
                $property['municipality']
            );
            
            if ($thumbnailPath && $thumbnailPath !== '/assets/images/placeholder-property.jpg') {
                return [
                    'success' => true,
                    'thumbnail_path' => $thumbnailPath,
                    'coordinates' => [
                        'latitude' => $this->thumbnailGenerator->getLastLatitude(),
                        'longitude' => $this->thumbnailGenerator->getLastLongitude()
                    ]
                ];
            } else {
                return [
                    'success' => false,
                    'error' => 'Failed to generate thumbnail or returned placeholder'
                ];
            }
            
        } catch (Exception $e) {
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }
    
    private function updatePropertyThumbnail($propertyId, $thumbnailPath, $coordinates) {
        try {
            $sql = "UPDATE properties 
                    SET thumbnail_path = ?, 
                        latitude = COALESCE(?, latitude), 
                        longitude = COALESCE(?, longitude),
                        updated_at = NOW()
                    WHERE id = ?";
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([
                $thumbnailPath,
                $coordinates['latitude'],
                $coordinates['longitude'],
                $propertyId
            ]);
            
        } catch (Exception $e) {
            $this->log("Database update failed for property {$propertyId}: " . $e->getMessage());
        }
    }
    
    public function cleanupOldThumbnails() {
        $this->log("Cleaning up thumbnails for removed properties...");
        
        $thumbnailDir = dirname(__DIR__) . '/frontend-php/assets/thumbnails/';
        
        if (!is_dir($thumbnailDir)) {
            $this->log("Thumbnail directory not found: {$thumbnailDir}");
            return;
        }
        
        // Get all thumbnail files
        $files = glob($thumbnailDir . '*.png');
        $cleaned = 0;
        
        foreach ($files as $file) {
            $filename = basename($file, '.png');
            
            // Check if property still exists
            $sql = "SELECT COUNT(*) FROM properties WHERE assessment_number = ?";
            $stmt = $this->pdo->prepare($sql);
            $stmt->execute([$filename]);
            
            if ($stmt->fetchColumn() === 0) {
                // Property no longer exists, remove thumbnail
                if (unlink($file)) {
                    $cleaned++;
                    $this->log("Removed orphaned thumbnail: {$filename}.png");
                }
            }
        }
        
        $this->log("Cleaned up {$cleaned} orphaned thumbnails");
    }
    
    public function generateStatsReport() {
        // Count total properties
        $totalProperties = $this->pdo->query("SELECT COUNT(*) FROM properties")->fetchColumn();
        
        // Count properties with PID
        $propertiesWithPID = $this->pdo->query("SELECT COUNT(*) FROM properties WHERE pid_number IS NOT NULL AND pid_number != '' AND pid_number != 'N/A'")->fetchColumn();
        
        // Count properties with thumbnails
        $propertiesWithThumbnails = $this->pdo->query("SELECT COUNT(*) FROM properties WHERE thumbnail_path IS NOT NULL AND thumbnail_path != '' AND thumbnail_path != '/assets/images/placeholder-property.jpg'")->fetchColumn();
        
        // Count properties needing thumbnails
        $needingThumbnails = $this->pdo->query("SELECT COUNT(*) FROM properties WHERE pid_number IS NOT NULL AND pid_number != '' AND pid_number != 'N/A' AND (thumbnail_path IS NULL OR thumbnail_path = '')")->fetchColumn();
        
        $this->log("=== Thumbnail Generation Stats ===");
        $this->log("Total properties: {$totalProperties}");
        $this->log("Properties with PID: {$propertiesWithPID}");
        $this->log("Properties with thumbnails: {$propertiesWithThumbnails}");
        $this->log("Properties needing thumbnails: {$needingThumbnails}");
        
        if ($propertiesWithPID > 0) {
            $completionRate = round(($propertiesWithThumbnails / $propertiesWithPID) * 100, 2);
            $this->log("Completion rate: {$completionRate}%");
        }
    }
    
    private function log($message) {
        $timestamp = date('Y-m-d H:i:s');
        $logMessage = "[{$timestamp}] {$message}\n";
        
        // Write to log file
        file_put_contents($this->logFile, $logMessage, FILE_APPEND | LOCK_EX);
        
        // Also output to console if running from CLI
        if (php_sapi_name() === 'cli') {
            echo $logMessage;
        }
    }
}

// Check if running from command line
if (php_sapi_name() === 'cli') {
    $generator = new BatchThumbnailGenerator();
    
    // Parse command line arguments
    $options = getopt('', ['cleanup', 'stats', 'help']);
    
    if (isset($options['help'])) {
        echo "Usage: php batch_thumbnail_generator.php [options]\n";
        echo "Options:\n";
        echo "  --cleanup    Clean up orphaned thumbnails\n";
        echo "  --stats      Show thumbnail generation statistics\n";
        echo "  --help       Show this help message\n";
        echo "\nDefault: Generate missing thumbnails\n";
        exit(0);
    }
    
    if (isset($options['cleanup'])) {
        $generator->cleanupOldThumbnails();
    } elseif (isset($options['stats'])) {
        $generator->generateStatsReport();
    } else {
        $generator->generateMissingThumbnails();
    }
}
?>