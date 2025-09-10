<?php
require_once __DIR__ . '/config/database.php';

echo "Creating test users for Tax Sale Compass...\n";

try {
    $db = getDB();
    if (!$db) {
        die("❌ MongoDB connection failed\n");
    }
    
    echo "✅ MongoDB connection successful\n";
    
    // Clear existing users
    $result = $db->users->deleteMany([]);
    echo "🗑️ Cleared " . $result->getDeletedCount() . " existing users\n";
    
    // Sample users data
    $sample_users = [
        [
            'id' => 'admin_user_123',
            'username' => 'admin',
            'email' => 'admin@taxsalecompass.ca',
            'password_hash' => password_hash('TaxSale2025!SecureAdmin', PASSWORD_DEFAULT),
            'subscription_tier' => 'paid',
            'is_admin' => true,
            'created_at' => new MongoDB\BSON\UTCDateTime(),
            'updated_at' => new MongoDB\BSON\UTCDateTime()
        ],
        [
            'id' => 'paid_user_456',
            'username' => 'paiduser',
            'email' => 'paid@taxsalecompass.ca',
            'password_hash' => password_hash('testpass123', PASSWORD_DEFAULT),
            'subscription_tier' => 'paid',
            'is_admin' => false,
            'created_at' => new MongoDB\BSON\UTCDateTime(),
            'updated_at' => new MongoDB\BSON\UTCDateTime()
        ],
        [
            'id' => 'free_user_789',
            'username' => 'freeuser',
            'email' => 'free@taxsalecompass.ca',
            'password_hash' => password_hash('testpass123', PASSWORD_DEFAULT),
            'subscription_tier' => 'free',
            'is_admin' => false,
            'created_at' => new MongoDB\BSON\UTCDateTime(),
            'updated_at' => new MongoDB\BSON\UTCDateTime()
        ]
    ];
    
    // Insert sample users
    $result = $db->users->insertMany($sample_users);
    echo "✅ Inserted " . $result->getInsertedCount() . " sample users\n";
    
    // Create some sample favorites for testing
    $sample_favorites = [
        [
            'user_id' => 'paid_user_456',
            'assessment_number' => '04023269',
            'created_at' => new MongoDB\BSON\UTCDateTime()
        ],
        [
            'user_id' => 'paid_user_456',
            'assessment_number' => '04435834',
            'created_at' => new MongoDB\BSON\UTCDateTime()
        ]
    ];
    
    // Clear existing favorites
    $result = $db->user_favorites->deleteMany([]);
    echo "🗑️ Cleared " . $result->getDeletedCount() . " existing favorites\n";
    
    // Insert sample favorites
    $result = $db->user_favorites->insertMany($sample_favorites);
    echo "✅ Inserted " . $result->getInsertedCount() . " sample favorites\n";
    
    echo "\n🎉 Test users created successfully!\n";
    echo "\nTest Credentials:\n";
    echo "Admin: admin / TaxSale2025!SecureAdmin\n";
    echo "Paid User: paiduser / testpass123\n";
    echo "Free User: freeuser / testpass123\n";
    
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
}
?>