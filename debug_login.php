<?php
session_start();
require_once 'config/database.php';

echo "<h2>Debug Login Test</h2>";

if ($_POST) {
    $username = $_POST['username'] ?? $_POST['email'] ?? '';
    $password = $_POST['password'] ?? '';
    
    echo "<p><strong>Input:</strong></p>";
    echo "<ul>";
    echo "<li>Username: " . htmlspecialchars($username) . "</li>";
    echo "<li>Password length: " . strlen($password) . "</li>";
    echo "</ul>";
    
    if ($username && $password) {
        // MongoDB authentication
        $db = getDB();
        if ($db) {
            echo "<p>✅ MongoDB connected</p>";
            
            // Find user by username or email
            $user_doc = $db->users->findOne([
                '$or' => [
                    ['username' => $username],
                    ['email' => $username]
                ]
            ]);
            
            if ($user_doc) {
                $user = mongoToArray($user_doc);
                
                echo "<p><strong>User found:</strong></p>";
                echo "<ul>";
                echo "<li>ID: " . ($user['id'] ?? 'N/A') . "</li>";
                echo "<li>Username: " . ($user['username'] ?? 'N/A') . "</li>";
                echo "<li>Email: " . ($user['email'] ?? 'N/A') . "</li>";
                echo "<li>Admin: " . ($user['is_admin'] ? 'Yes' : 'No') . "</li>";
                echo "</ul>";
                
                // Check password hash
                $password_hash = $user['password_hash'] ?? $user['password'] ?? '';
                echo "<p><strong>Password Hash Info:</strong></p>";
                echo "<ul>";
                echo "<li>Hash exists: " . ($password_hash ? 'Yes' : 'No') . "</li>";
                echo "<li>Hash length: " . strlen($password_hash) . "</li>";
                echo "<li>Hash start: " . substr($password_hash, 0, 10) . "...</li>";
                echo "<li>Is bcrypt: " . (strpos($password_hash, '$2y$') === 0 ? 'Yes' : 'No') . "</li>";
                echo "</ul>";
                
                // Test password verification
                echo "<p><strong>Password Verification Tests:</strong></p>";
                echo "<ul>";
                
                if (password_verify($password, $password_hash)) {
                    echo "<li>✅ Bcrypt verification: SUCCESS</li>";
                } else {
                    echo "<li>❌ Bcrypt verification: FAILED</li>";
                    
                    // Test legacy hashes
                    $md5_test = md5($password);
                    $sha1_test = sha1($password);
                    $sha256_test = hash('sha256', $password);
                    
                    echo "<li>MD5 test: " . ($md5_test === $password_hash ? '✅ MATCH' : '❌ No match') . "</li>";
                    echo "<li>SHA1 test: " . ($sha1_test === $password_hash ? '✅ MATCH' : '❌ No match') . "</li>";
                    echo "<li>SHA256 test: " . ($sha256_test === $password_hash ? '✅ MATCH' : '❌ No match') . "</li>";
                }
                echo "</ul>";
                
            } else {
                echo "<p>❌ User not found</p>";
            }
        } else {
            echo "<p>❌ MongoDB connection failed</p>";
        }
    } else {
        echo "<p>❌ Missing username or password</p>";
    }
} else {
    echo "<p>No POST data received</p>";
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>Debug Login</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        ul { background: #f5f5f5; padding: 10px; }
    </style>
</head>
<body>
    <form method="POST">
        <p>
            <label>Username/Email:</label><br>
            <input type="text" name="username" value="<?php echo htmlspecialchars($_POST['username'] ?? ''); ?>" style="width: 300px;">
        </p>
        <p>
            <label>Password:</label><br>
            <input type="password" name="password" style="width: 300px;">
        </p>
        <p>
            <button type="submit">Test Login</button>
        </p>
    </form>
</body>
</html>