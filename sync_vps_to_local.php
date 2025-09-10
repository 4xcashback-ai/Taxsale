<?php
require_once __DIR__ . '/frontend-php/config/database.php';

echo "=== SYNCING VPS DATA TO LOCAL DEV ===\n";

try {
    // Connect to local MongoDB
    $local_mongodb = getDB();
    if (!$local_mongodb) {
        die("❌ Local MongoDB connection failed\n");
    }
    echo "✅ Local MongoDB connected\n";
    
    // Clear local collections first
    echo "\n🗑️ Clearing local MongoDB data...\n";
    $local_mongodb->properties->deleteMany([]);
    $local_mongodb->users->deleteMany([]);
    $local_mongodb->user_favorites->deleteMany([]);
    $local_mongodb->pvsc_data->deleteMany([]);
    echo "✅ Cleared local MongoDB collections\n";
    
    // SSH connection details for VPS
    $vps_host = '5.252.52.41';
    $vps_user = 'root';
    $vps_pass = '527iDUjHGHjx8';
    
    // Export data from VPS MongoDB and import to local
    $collections = ['properties', 'users', 'user_favorites', 'pvsc_data'];
    
    foreach ($collections as $collection) {
        echo "\n📊 Syncing $collection...\n";
        
        // Export from VPS
        $export_cmd = "sshpass -p '$vps_pass' ssh -o StrictHostKeyChecking=no $vps_user@$vps_host 'mongoexport --db=tax_sale_compass --collection=$collection --jsonArray'";
        $json_data = shell_exec($export_cmd);
        
        if ($json_data) {
            $data = json_decode($json_data, true);
            if ($data && count($data) > 0) {
                // Convert MongoDB ObjectId strings back to proper format for local insertion
                foreach ($data as &$doc) {
                    if (isset($doc['_id']['$oid'])) {
                        unset($doc['_id']); // Let MongoDB generate new ObjectId
                    }
                    // Convert date strings back to MongoDB date objects
                    foreach ($doc as $key => &$value) {
                        if (is_array($value) && isset($value['$date'])) {
                            $value = new MongoDB\BSON\UTCDateTime($value['$date']);
                        }
                    }
                }
                
                $result = $local_mongodb->$collection->insertMany($data);
                echo "✅ Imported " . $result->getInsertedCount() . " documents to $collection\n";
            } else {
                echo "ℹ️ No data found in $collection\n";
            }
        } else {
            echo "❌ Failed to export $collection from VPS\n";
        }
    }
    
    echo "\n🎉 SYNC COMPLETED!\n";
    echo "\n=== LOCAL DEV SUMMARY ===\n";
    echo "Properties: " . $local_mongodb->properties->countDocuments([]) . "\n";
    echo "PVSC Data: " . $local_mongodb->pvsc_data->countDocuments([]) . "\n";
    echo "Users: " . $local_mongodb->users->countDocuments([]) . "\n";
    echo "Favorites: " . $local_mongodb->user_favorites->countDocuments([]) . "\n";
    
} catch (Exception $e) {
    echo "❌ Sync failed: " . $e->getMessage() . "\n";
    echo "Stack trace: " . $e->getTraceAsString() . "\n";
}
?>