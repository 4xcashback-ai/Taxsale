<?php
require_once __DIR__ . '/frontend-php/config/database.php';

echo "=== FIXING PASSWORD HASHES IN MONGODB ===\n";

try {
    $db = getDB();
    if (!$db) {
        die("❌ MongoDB connection failed\n");
    }
    
    echo "✅ MongoDB connected\n";
    
    // Get all users
    $users = $db->users->find()->toArray();
    echo "Found " . count($users) . " users\n\n";
    
    foreach ($users as $user) {
        $user_id = $user['id'] ?? $user['_id'];
        $email = $user['email'] ?? 'N/A';
        $current_hash = $user['password_hash'] ?? $user['password'] ?? '';
        
        echo "Processing user: $email (ID: $user_id)\n";
        echo "Current hash: " . substr($current_hash, 0, 30) . "...\n";
        
        // Check if it's already a proper bcrypt hash
        if (strpos($current_hash, '$2y$') === 0) {
            echo "✅ Already properly hashed\n\n";
            continue;
        }
        
        // If it's a hex hash (MD5/SHA), we need to ask for the plain password
        // For now, let's create a default password for non-bcrypt hashes
        if (preg_match('/^[a-f0-9]{32,64}$/', $current_hash)) {
            echo "⚠️  Detected hex hash (MD5/SHA) - needs conversion\n";
            
            // For demonstration, I'll set a default password
            // In production, you'd want to force password reset
            $default_password = 'password123'; // You should change this
            $new_hash = password_hash($default_password, PASSWORD_DEFAULT);
            
            // Update the user
            $result = $db->users->updateOne(
                ['id' => $user_id],
                ['$set' => ['password_hash' => $new_hash]]
            );
            
            if ($result->getModifiedCount() > 0) {
                echo "✅ Updated to bcrypt hash (temp password: $default_password)\n";
            } else {
                echo "❌ Failed to update\n";
            }
        } else {
            echo "❓ Unknown hash format - skipping\n";
        }
        echo "\n";
    }
    
    echo "🎉 Password hash fixing completed!\n";
    
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
}
?>