<?php
require_once __DIR__ . '/config/database.php';

echo "Populating sample data for Tax Sale Compass...\n";

try {
    $db = getDB();
    if (!$db) {
        die("❌ MongoDB connection failed\n");
    }
    
    echo "✅ MongoDB connection successful\n";
    
    // Sample properties data
    $sample_properties = [
        [
            'assessment_number' => '07737947',
            'pid_number' => '40498370',
            'civic_address' => '80 Spinnaker Dr Unit 209 Halifax',
            'municipality' => 'Halifax',
            'status' => 'active',
            'min_bid' => 15000.00,
            'auction_date' => '2025-12-15',
            'property_type' => 'apartment',
            'latitude' => 44.6379021,
            'longitude' => -63.61754689999999,
            'boundary_data' => null,
            'thumbnail_path' => null,
            'created_at' => new MongoDB\BSON\UTCDateTime(),
            'updated_at' => new MongoDB\BSON\UTCDateTime()
        ],
        [
            'assessment_number' => '09192891',
            'pid_number' => '40180606',
            'civic_address' => 'Lot 60-X Halifax - Land',
            'municipality' => 'Halifax',
            'status' => 'active',
            'min_bid' => 25000.00,
            'auction_date' => '2025-12-15',
            'property_type' => 'land',
            'latitude' => null,
            'longitude' => null,
            'boundary_data' => null,
            'thumbnail_path' => null,
            'created_at' => new MongoDB\BSON\UTCDateTime(),
            'updated_at' => new MongoDB\BSON\UTCDateTime()
        ],
        [
            'assessment_number' => '12345678',
            'pid_number' => '12345678',
            'civic_address' => '123 Main Street Victoria',
            'municipality' => 'Victoria County',
            'status' => 'sold',
            'min_bid' => 50000.00,
            'auction_date' => '2025-10-15',
            'property_type' => 'residential',
            'latitude' => 46.0878,
            'longitude' => -60.9545,
            'boundary_data' => null,
            'thumbnail_path' => null,
            'created_at' => new MongoDB\BSON\UTCDateTime(),
            'updated_at' => new MongoDB\BSON\UTCDateTime()
        ],
        [
            'assessment_number' => '23456789',
            'pid_number' => '23456789',
            'civic_address' => '456 Oak Avenue Cumberland',
            'municipality' => 'Cumberland',
            'status' => 'withdrawn',
            'min_bid' => 30000.00,
            'auction_date' => '2025-11-20',
            'property_type' => 'residential',
            'latitude' => 45.6318,
            'longitude' => -64.1486,
            'boundary_data' => null,
            'thumbnail_path' => null,
            'created_at' => new MongoDB\BSON\UTCDateTime(),
            'updated_at' => new MongoDB\BSON\UTCDateTime()
        ],
        [
            'assessment_number' => '34567890',
            'pid_number' => '34567890',
            'civic_address' => '789 Pine Street Halifax',
            'municipality' => 'Halifax',
            'status' => 'active',
            'min_bid' => 75000.00,
            'auction_date' => '2025-12-30',
            'property_type' => 'residential',
            'latitude' => 44.6488,
            'longitude' => -63.5752,
            'boundary_data' => null,
            'thumbnail_path' => null,
            'created_at' => new MongoDB\BSON\UTCDateTime(),
            'updated_at' => new MongoDB\BSON\UTCDateTime()
        ]
    ];
    
    // Clear existing properties
    $result = $db->properties->deleteMany([]);
    echo "🗑️ Cleared " . $result->getDeletedCount() . " existing properties\n";
    
    // Insert sample properties
    $result = $db->properties->insertMany($sample_properties);
    echo "✅ Inserted " . $result->getInsertedCount() . " sample properties\n";
    
    // Create sample users for testing
    $sample_users = [
        [
            'id' => 'admin_user_123',
            'username' => 'admin',
            'email' => 'admin@example.com',
            'password_hash' => password_hash('TaxSale2025!SecureAdmin', PASSWORD_DEFAULT),
            'subscription_tier' => 'paid',
            'is_admin' => true,
            'created_at' => new MongoDB\BSON\UTCDateTime(),
            'updated_at' => new MongoDB\BSON\UTCDateTime()
        ],
        [
            'id' => 'paid_user_456',
            'username' => 'paiduser',
            'email' => 'paid@example.com',
            'password_hash' => password_hash('testpass123', PASSWORD_DEFAULT),
            'subscription_tier' => 'paid',
            'is_admin' => false,
            'created_at' => new MongoDB\BSON\UTCDateTime(),
            'updated_at' => new MongoDB\BSON\UTCDateTime()
        ],
        [
            'id' => 'free_user_789',
            'username' => 'freeuser',
            'email' => 'free@example.com',
            'password_hash' => password_hash('testpass123', PASSWORD_DEFAULT),
            'subscription_tier' => 'free',
            'is_admin' => false,
            'created_at' => new MongoDB\BSON\UTCDateTime(),
            'updated_at' => new MongoDB\BSON\UTCDateTime()
        ]
    ];
    
    // Clear existing users
    $result = $db->users->deleteMany([]);
    echo "🗑️ Cleared " . $result->getDeletedCount() . " existing users\n";
    
    // Insert sample users
    $result = $db->users->insertMany($sample_users);
    echo "✅ Inserted " . $result->getInsertedCount() . " sample users\n";
    
    // Create sample favorites for testing
    $sample_favorites = [
        [
            'user_id' => 'paid_user_456',
            'assessment_number' => '07737947',
            'created_at' => new MongoDB\BSON\UTCDateTime()
        ],
        [
            'user_id' => 'paid_user_456',
            'assessment_number' => '34567890',
            'created_at' => new MongoDB\BSON\UTCDateTime()
        ]
    ];
    
    // Clear existing favorites
    $result = $db->user_favorites->deleteMany([]);
    echo "🗑️ Cleared " . $result->getDeletedCount() . " existing favorites\n";
    
    // Insert sample favorites
    $result = $db->user_favorites->insertMany($sample_favorites);
    echo "✅ Inserted " . $result->getInsertedCount() . " sample favorites\n";
    
    echo "\n🎉 Sample data population completed successfully!\n";
    echo "\nTest Credentials:\n";
    echo "Admin: admin / TaxSale2025!SecureAdmin\n";
    echo "Paid User: paiduser / testpass123\n";
    echo "Free User: freeuser / testpass123\n";
    
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
}
?>