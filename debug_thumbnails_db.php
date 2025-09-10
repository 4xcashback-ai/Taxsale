<?php
require_once 'frontend-php/config/database.php';

echo "<h2>Thumbnail Database Debug</h2>\n";

try {
    $db = getDB();
    
    // Check if thumbnail_path column exists
    echo "<h3>1. Database Schema Check</h3>\n";
    $stmt = $db->query("DESCRIBE properties");
    $columns = $stmt->fetchAll();
    
    $hasThumbnailPath = false;
    foreach ($columns as $column) {
        if ($column['Field'] === 'thumbnail_path') {
            $hasThumbnailPath = true;
            echo "✅ thumbnail_path column exists: " . $column['Type'] . " " . ($column['Null'] === 'YES' ? 'NULL' : 'NOT NULL') . "\n";
            break;
        }
    }
    
    if (!$hasThumbnailPath) {
        echo "❌ thumbnail_path column NOT FOUND!\n";
        echo "Available columns: " . implode(', ', array_column($columns, 'Field')) . "\n";
    }
    
    // Check sample properties
    echo "\n<h3>2. Sample Properties with Thumbnail Data</h3>\n";
    $stmt = $db->query("SELECT assessment_number, pid_number, thumbnail_path, latitude, longitude, civic_address FROM properties LIMIT 10");
    $properties = $stmt->fetchAll();
    
    echo "<table border='1' cellpadding='5' cellspacing='0'>\n";
    echo "<tr><th>Assessment #</th><th>PID</th><th>Thumbnail Path</th><th>Coords</th><th>Address</th><th>File Exists?</th></tr>\n";
    
    foreach ($properties as $property) {
        $thumbnailPath = $property['thumbnail_path'] ?? 'NULL';
        $fileExists = 'N/A';
        
        if ($thumbnailPath && $thumbnailPath !== 'NULL') {
            $fullPath = dirname(__FILE__) . '/frontend-php' . $thumbnailPath;
            $fileExists = file_exists($fullPath) ? '✅ Yes' : '❌ No';
        }
        
        echo "<tr>";
        echo "<td>" . htmlspecialchars($property['assessment_number']) . "</td>";
        echo "<td>" . htmlspecialchars($property['pid_number'] ?? 'NULL') . "</td>";
        echo "<td>" . htmlspecialchars($thumbnailPath) . "</td>";
        echo "<td>" . htmlspecialchars(($property['latitude'] ?? 'NULL') . ',' . ($property['longitude'] ?? 'NULL')) . "</td>";
        echo "<td>" . htmlspecialchars(substr($property['civic_address'] ?? 'NULL', 0, 30)) . "</td>";
        echo "<td>" . $fileExists . "</td>";
        echo "</tr>\n";
    }
    echo "</table>\n";
    
    // Statistics
    echo "\n<h3>3. Thumbnail Statistics</h3>\n";
    
    $totalProperties = $db->query("SELECT COUNT(*) FROM properties")->fetchColumn();
    echo "Total properties: {$totalProperties}\n";
    
    $propertiesWithPID = $db->query("SELECT COUNT(*) FROM properties WHERE pid_number IS NOT NULL AND pid_number != '' AND pid_number != 'N/A'")->fetchColumn();
    echo "Properties with PID: {$propertiesWithPID}\n";
    
    if ($hasThumbnailPath) {
        $propertiesWithThumbnails = $db->query("SELECT COUNT(*) FROM properties WHERE thumbnail_path IS NOT NULL AND thumbnail_path != ''")->fetchColumn();
        echo "Properties with thumbnail paths: {$propertiesWithThumbnails}\n";
        
        $needingThumbnails = $db->query("SELECT COUNT(*) FROM properties WHERE pid_number IS NOT NULL AND pid_number != '' AND pid_number != 'N/A' AND (thumbnail_path IS NULL OR thumbnail_path = '')")->fetchColumn();
        echo "Properties needing thumbnails: {$needingThumbnails}\n";
        
        if ($propertiesWithPID > 0) {
            $completionRate = round(($propertiesWithThumbnails / $propertiesWithPID) * 100, 2);
            echo "Completion rate: {$completionRate}%\n";
        }
    }
    
    // Check specific property (the one from your HTML)
    echo "\n<h3>4. Specific Property Check (10706807)</h3>\n";
    $stmt = $db->prepare("SELECT * FROM properties WHERE assessment_number = ?");
    $stmt->execute(['10706807']);
    $specificProperty = $stmt->fetch();
    
    if ($specificProperty) {
        echo "Assessment Number: " . htmlspecialchars($specificProperty['assessment_number']) . "\n";
        echo "PID Number: " . htmlspecialchars($specificProperty['pid_number'] ?? 'NULL') . "\n";
        echo "Thumbnail Path: " . htmlspecialchars($specificProperty['thumbnail_path'] ?? 'NULL') . "\n";
        echo "Coordinates: " . htmlspecialchars(($specificProperty['latitude'] ?? 'NULL') . ', ' . ($specificProperty['longitude'] ?? 'NULL')) . "\n";
        echo "Address: " . htmlspecialchars($specificProperty['civic_address'] ?? 'NULL') . "\n";
        
        // Check if thumbnail file exists
        if ($specificProperty['thumbnail_path']) {
            $fullPath = dirname(__FILE__) . '/frontend-php' . $specificProperty['thumbnail_path'];
            echo "Full thumbnail path: " . $fullPath . "\n";
            echo "File exists: " . (file_exists($fullPath) ? '✅ Yes' : '❌ No') . "\n";
            if (file_exists($fullPath)) {
                echo "File size: " . filesize($fullPath) . " bytes\n";
                echo "File modified: " . date('Y-m-d H:i:s', filemtime($fullPath)) . "\n";
            }
        }
    } else {
        echo "❌ Property 10706807 not found in database!\n";
    }
    
    // Check thumbnail directory
    echo "\n<h3>5. Thumbnail Directory Check</h3>\n";
    $thumbnailDir = dirname(__FILE__) . '/frontend-php/assets/thumbnails/';
    echo "Thumbnail directory: {$thumbnailDir}\n";
    echo "Directory exists: " . (is_dir($thumbnailDir) ? '✅ Yes' : '❌ No') . "\n";
    
    if (is_dir($thumbnailDir)) {
        $files = glob($thumbnailDir . '*.png');
        echo "PNG files found: " . count($files) . "\n";
        
        if (count($files) > 0) {
            echo "Sample files:\n";
            foreach (array_slice($files, 0, 5) as $file) {
                $filename = basename($file);
                $size = filesize($file);
                echo "- {$filename} ({$size} bytes)\n";
            }
        }
        
        // Check for the specific file
        $specificFile = $thumbnailDir . '10706807.png';
        echo "Specific file (10706807.png): " . (file_exists($specificFile) ? '✅ Exists' : '❌ Missing') . "\n";
        if (file_exists($specificFile)) {
            echo "File size: " . filesize($specificFile) . " bytes\n";
        }
    }
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>