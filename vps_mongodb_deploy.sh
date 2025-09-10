#!/bin/bash

echo "🚀 Deploying MongoDB Migration to VPS..."

# Navigate to VPS directory
cd /var/www/tax-sale-compass/frontend-php

# Copy the fixed files
echo "📂 Copying database.php..."
cat > config/database.php << 'EOF'
<?php
// Load Composer autoloader
require_once __DIR__ . '/../vendor/autoload.php';

// MongoDB configuration
define('MONGO_URL', $_ENV['MONGO_URL'] ?? getenv('MONGO_URL') ?: 'mongodb://localhost:27017');
define('DB_NAME', $_ENV['DB_NAME'] ?? getenv('DB_NAME') ?: 'tax_sale_compass');
define('GOOGLE_MAPS_API_KEY', $_ENV['GOOGLE_MAPS_API_KEY'] ?? getenv('GOOGLE_MAPS_API_KEY') ?: 'AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY');
define('API_BASE_URL', $_ENV['API_BASE_URL'] ?? getenv('API_BASE_URL') ?: 'http://localhost:8001/api');
define('SITE_NAME', 'Tax Sale Compass');
define('SITE_URL', $_ENV['SITE_URL'] ?? getenv('SITE_URL') ?: 'https://taxsalecompass.ca');

function getDB() {
    static $client = null;
    static $database = null;
    
    if ($client === null) {
        try {
            error_log("MongoDB Connection attempt: URL=" . MONGO_URL . ", DB=" . DB_NAME);
            $client = new MongoDB\Client(MONGO_URL);
            $database = $client->selectDatabase(DB_NAME);
            $database->command(['ping' => 1]);
            error_log("MongoDB Connection successful");
        } catch (Exception $e) {
            error_log("MongoDB connection failed: " . $e->getMessage());
            return null;
        }
    }
    return $database;
}

function mongoToArray($document) {
    if ($document === null) return null;
    
    if (is_array($document)) {
        $array = $document;
    } else {
        $array = [];
        foreach ($document as $key => $value) {
            if ($value instanceof MongoDB\BSON\UTCDateTime) {
                $array[$key] = $value->toDateTime()->format('Y-m-d H:i:s');
            } elseif ($value instanceof MongoDB\BSON\ObjectId) {
                $array[$key] = (string)$value;
            } else {
                $array[$key] = $value;
            }
        }
    }
    
    if (isset($array['_id'])) {
        if ($array['_id'] instanceof MongoDB\BSON\ObjectId) {
            $array['id'] = (string)$array['_id'];
        }
        unset($array['_id']);
    }
    
    return $array;
}

function mongoArrayToArray($cursor) {
    $result = [];
    foreach ($cursor as $document) {
        $result[] = mongoToArray($document);
    }
    return $result;
}
?>
EOF

echo "📂 Creating test users script..."
cat > create_test_users.php << 'EOF'
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
EOF

echo "📂 Updating composer.json..."
cat > composer.json << 'EOF'
{
    "require": {
        "mongodb/mongodb": "1.11.*"
    },
    "config": {
        "platform": {
            "php": "8.1"
        }
    }
}
EOF

echo "📦 Installing composer dependencies..."
composer install

echo "👥 Creating test users..."
php create_test_users.php

echo "🔄 Restarting services..."
sudo systemctl restart php8.1-fpm
sudo systemctl restart nginx

echo "🧪 Testing connection..."
curl -s -o /dev/null -w "Website Status: %{http_code}\n" https://taxsalecompass.ca/

echo "✅ MongoDB migration deployment complete!"
echo ""
echo "Test Credentials:"
echo "Admin: admin / TaxSale2025!SecureAdmin"
echo "Paid User: paiduser / testpass123"
echo "Free User: freeuser / testpass123"