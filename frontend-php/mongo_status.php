<?php
require_once __DIR__ . '/config/database.php';
?>
<!DOCTYPE html>
<html>
<head>
    <title>MongoDB Connection Status</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .success { color: green; }
        .error { color: red; }
        .info { color: blue; }
    </style>
</head>
<body>
    <h1>MongoDB Connection Status</h1>
    
    <?php
    try {
        echo "<p class='info'>Testing MongoDB connection...</p>";
        
        $db = getDB();
        if ($db) {
            echo "<p class='success'>✅ MongoDB connection successful!</p>";
            
            // List collections
            $collections = $db->listCollections();
            $collectionNames = [];
            foreach ($collections as $collection) {
                $collectionNames[] = $collection->getName();
            }
            
            if (empty($collectionNames)) {
                echo "<p class='info'>📄 Database is empty (no collections found)</p>";
            } else {
                echo "<p class='success'>📊 Available collections: " . implode(', ', $collectionNames) . "</p>";
            }
            
            // Show database name and connection details
            echo "<p class='info'>🗄️ Database: " . DB_NAME . "</p>";
            echo "<p class='info'>🔗 MongoDB URL: " . MONGO_URL . "</p>";
            
        } else {
            echo "<p class='error'>❌ MongoDB connection failed</p>";
        }
    } catch (Exception $e) {
        echo "<p class='error'>❌ MongoDB connection error: " . htmlspecialchars($e->getMessage()) . "</p>";
    }
    ?>
    
    <hr>
    <p><a href="/">← Back to Home</a></p>
</body>
</html>