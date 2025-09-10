<?php
require_once __DIR__ . '/frontend-php/config/database.php';

echo "=== ADDING FRESH ADMIN USER TO MONGODB ===\n";

try {
    $db = getDB();
    if (!$db) {
        die("❌ MongoDB connection failed\n");
    }
    
    echo "✅ MongoDB connected\n";
    
    // Admin user details
    $admin_email = 'admin@taxsalecompass.ca';
    $admin_username = 'admin';
    $admin_password = 'admin123'; // Change this to whatever you want
    
    echo "Creating admin user:\n";
    echo "- Email: $admin_email\n";
    echo "- Username: $admin_username\n";
    echo "- Password: $admin_password\n";
    
    // Remove existing admin user if exists
    $result = $db->users->deleteMany([
        '$or' => [
            ['email' => $admin_email],
            ['username' => $admin_username],
            ['email' => 'admin'],
            ['username' => 'admin']
        ]
    ]);
    
    if ($result->getDeletedCount() > 0) {
        echo "✅ Removed " . $result->getDeletedCount() . " existing admin user(s)\n";
    }
    
    // Create new admin user
    $admin_user = [
        'id' => 'admin_' . uniqid(),
        'email' => $admin_email,
        'username' => $admin_username,
        'password_hash' => password_hash($admin_password, PASSWORD_DEFAULT),
        'subscription_tier' => 'premium',
        'is_admin' => true,
        'created_at' => new MongoDB\BSON\UTCDateTime(),
        'updated_at' => new MongoDB\BSON\UTCDateTime()
    ];
    
    $result = $db->users->insertOne($admin_user);
    
    if ($result->getInsertedId()) {
        echo "✅ Admin user created successfully!\n";
        echo "\n=== LOGIN CREDENTIALS ===\n";
        echo "Email/Username: $admin_username\n";
        echo "Password: $admin_password\n";
        echo "\nYou can now login at: https://taxsalecompass.ca/frontend-php/login.php\n";
    } else {
        echo "❌ Failed to create admin user\n";
    }
    
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
}
?>