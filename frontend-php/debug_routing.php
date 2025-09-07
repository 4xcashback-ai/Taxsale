<?php
session_start();

echo "<h1>Debug Routing</h1>";
echo "<pre>";
echo "Session data:\n";
print_r($_SESSION);

echo "\nSession variables:\n";
echo "user_id: " . (isset($_SESSION['user_id']) ? $_SESSION['user_id'] : 'NOT SET') . "\n";
echo "access_token: " . (isset($_SESSION['access_token']) ? $_SESSION['access_token'] : 'NOT SET') . "\n";

echo "\nIs logged in check: ";
if (isset($_SESSION['user_id']) && isset($_SESSION['access_token'])) {
    echo "YES - Should redirect to search.php\n";
} else {
    echo "NO - Should show landing.php\n";
}

echo "</pre>";

echo '<p><a href="logout.php">Logout</a> | <a href="index.php">Go to Index</a></p>';
?>