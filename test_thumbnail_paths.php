<?php
// Test script to verify thumbnail path logic works correctly

// Simulate the ThumbnailGenerator constructor logic
echo "=== ThumbnailGenerator Path Test ===\n";

// This simulates what would happen in includes/thumbnail_generator.php
$includes_dir = __DIR__ . '/frontend-php/includes';
$thumbnail_dir_from_includes = dirname($includes_dir) . '/assets/thumbnails/';

echo "Includes directory: $includes_dir\n";
echo "Parent of includes: " . dirname($includes_dir) . "\n";  
echo "Computed thumbnail directory: $thumbnail_dir_from_includes\n";
echo "Directory exists: " . (is_dir($thumbnail_dir_from_includes) ? 'YES' : 'NO') . "\n";
echo "Directory writable: " . (is_writable($thumbnail_dir_from_includes) ? 'YES' : 'NO') . "\n";

echo "\n=== Debug Script Path Test ===\n";

// This simulates what would happen in debug_thumbnails.php  
$debug_dir = __DIR__ . '/frontend-php';
$thumbnail_dir_from_debug = $debug_dir . '/assets/thumbnails/';

echo "Debug script directory: $debug_dir\n";
echo "Computed thumbnail directory: $thumbnail_dir_from_debug\n"; 
echo "Directory exists: " . (is_dir($thumbnail_dir_from_debug) ? 'YES' : 'NO') . "\n";
echo "Directory writable: " . (is_writable($thumbnail_dir_from_debug) ? 'YES' : 'NO') . "\n";

echo "\n=== Testing File Creation ===\n";

// Test creating a file in the thumbnail directory
$test_file = $thumbnail_dir_from_includes . 'test_' . time() . '.txt';
$result = file_put_contents($test_file, 'test content');

if ($result) {
    echo "✅ Successfully created test file: $test_file\n";
    echo "File size: " . filesize($test_file) . " bytes\n";
    
    // Clean up
    unlink($test_file);
    echo "✅ Test file cleaned up\n";
} else {
    echo "❌ Failed to create test file: $test_file\n";
}

echo "\n=== Directory Listing ===\n";
if (is_dir($thumbnail_dir_from_includes)) {
    $files = scandir($thumbnail_dir_from_includes);
    $real_files = array_filter($files, fn($f) => $f !== '.' && $f !== '..');
    echo "Files in thumbnail directory: " . (count($real_files) > 0 ? implode(', ', $real_files) : 'EMPTY') . "\n";
} else {
    echo "❌ Thumbnail directory does not exist\n";
}
?>