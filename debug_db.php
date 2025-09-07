<?php
require_once 'frontend-php/config/database.php';

try {
    $db = getDB();
    
    echo "=== Checking properties table structure ===\n";
    $stmt = $db->query("DESCRIBE properties");
    $columns = $stmt->fetchAll();
    
    $hasThumbnailPath = false;
    foreach ($columns as $column) {
        if ($column['Field'] === 'thumbnail_path') {
            $hasThumbnailPath = true;
            echo "Found thumbnail_path column: " . print_r($column, true) . "\n";
            break;
        }
    }
    
    if (!$hasThumbnailPath) {
        echo "❌ thumbnail_path column NOT FOUND\n";
        echo "Available columns:\n";
        foreach ($columns as $column) {
            echo "- " . $column['Field'] . " (" . $column['Type'] . ")\n";
        }
    }
    
    echo "\n=== Sample property data ===\n";
    $stmt = $db->query("SELECT assessment_number, pid_number, thumbnail_path, latitude, longitude FROM properties LIMIT 5");
    $properties = $stmt->fetchAll();
    
    foreach ($properties as $property) {
        echo "Assessment: " . $property['assessment_number'] . 
             ", PID: " . $property['pid_number'] . 
             ", Thumbnail: " . ($property['thumbnail_path'] ?? 'NULL') . 
             ", Coords: " . ($property['latitude'] ?? 'NULL') . "," . ($property['longitude'] ?? 'NULL') . "\n";
    }
    
    echo "\n=== Thumbnail statistics ===\n";
    $stmt = $db->query("SELECT COUNT(*) as total FROM properties");
    $total = $stmt->fetchColumn();
    echo "Total properties: {$total}\n";
    
    $stmt = $db->query("SELECT COUNT(*) as with_pid FROM properties WHERE pid_number IS NOT NULL AND pid_number != '' AND pid_number != 'N/A'");
    $withPid = $stmt->fetchColumn();
    echo "Properties with PID: {$withPid}\n";
    
    if ($hasThumbnailPath) {
        $stmt = $db->query("SELECT COUNT(*) as with_thumbnails FROM properties WHERE thumbnail_path IS NOT NULL AND thumbnail_path != ''");
        $withThumbnails = $stmt->fetchColumn();
        echo "Properties with thumbnails: {$withThumbnails}\n";
    }
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}