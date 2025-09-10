<?php
// Test MongoDB connection
require_once __DIR__ . '/config/database.php';

echo "Testing MongoDB connection...\n";

try {
    $db = getDB();
    if ($db) {
        echo "✅ MongoDB connection successful!\n";
        
        // Test a simple query
        $collections = $db->listCollections();
        $collectionNames = [];
        foreach ($collections as $collection) {
            $collectionNames[] = $collection->getName();
        }
        
        echo "✅ Available collections: " . implode(', ', $collectionNames) . "\n";
        
        // Test inserting and finding a test document
        $testCollection = $db->test_connection;
        $result = $testCollection->insertOne([
            'test' => true,
            'timestamp' => new MongoDB\BSON\UTCDateTime(),
            'message' => 'MongoDB connection test successful'
        ]);
        
        if ($result->getInsertedId()) {
            echo "✅ Test document inserted successfully\n";
            
            // Clean up test document
            $testCollection->deleteOne(['_id' => $result->getInsertedId()]);
            echo "✅ Test document cleaned up\n";
        }
        
    } else {
        echo "❌ MongoDB connection failed\n";
    }
} catch (Exception $e) {
    echo "❌ MongoDB connection error: " . $e->getMessage() . "\n";
}
?>