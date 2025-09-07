<?php
echo "<h2>Path Test Debug</h2>";

echo "<h3>From debug_thumbnails.php perspective:</h3>";
echo "Current file: " . __FILE__ . "<br>";
echo "Directory: " . dirname(__FILE__) . "<br>";
echo "Computed assets path: " . dirname(__FILE__) . '/assets/thumbnails/' . "<br>";
echo "Assets path exists: " . (is_dir(dirname(__FILE__) . '/assets/thumbnails/') ? 'Yes' : 'No') . "<br>";

echo "<h3>From ThumbnailGenerator perspective (includes/thumbnail_generator.php):</h3>";
$includes_dir = dirname(__FILE__) . '/includes';
echo "Includes directory: " . $includes_dir . "<br>";
echo "Parent from includes: " . dirname($includes_dir) . "<br>";
echo "Computed thumbnail dir: " . dirname($includes_dir) . '/assets/thumbnails/' . "<br>";
echo "Path exists: " . (is_dir(dirname($includes_dir) . '/assets/thumbnails/') ? 'Yes' : 'No') . "<br>";

echo "<h3>Directory contents:</h3>";
$thumbnails_dir = dirname(__FILE__) . '/assets/thumbnails/';
if (is_dir($thumbnails_dir)) {
    $files = scandir($thumbnails_dir);
    echo "Files: " . implode(', ', array_filter($files, fn($f) => $f !== '.' && $f !== '..')) . "<br>";
} else {
    echo "Directory doesn't exist<br>";
}

echo "<h3>Test creating a file:</h3>";
$test_file = $thumbnails_dir . 'test.txt';
$result = file_put_contents($test_file, 'test');
echo "Test file creation result: " . ($result ? 'Success' : 'Failed') . "<br>";
if ($result && file_exists($test_file)) {
    echo "Test file exists: Yes<br>";
    unlink($test_file); // Clean up
    echo "Test file cleaned up<br>";
}
?>