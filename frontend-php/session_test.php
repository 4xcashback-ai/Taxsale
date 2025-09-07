<?php
session_start();
echo "<h1>Session Test</h1>";
echo "<p>Time: " . date('Y-m-d H:i:s') . "</p>";
echo "<pre>";
echo "Session ID: " . session_id() . "\n";
echo "Session variables:\n";
print_r($_SESSION);
echo "\n";
echo "user_id isset: " . (isset($_SESSION['user_id']) ? 'YES' : 'NO') . "\n";
echo "access_token isset: " . (isset($_SESSION['access_token']) ? 'YES' : 'NO') . "\n";
echo "is_logged_in: " . ((isset($_SESSION['user_id']) && isset($_SESSION['access_token'])) ? 'YES' : 'NO') . "\n";
echo "</pre>";
?>