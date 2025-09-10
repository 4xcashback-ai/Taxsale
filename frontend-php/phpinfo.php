<?php
echo "<!-- PHP is working! -->";
echo "<h1>PHP Info Test</h1>";
echo "<p>Current time: " . date('Y-m-d H:i:s') . "</p>";
echo "<p>Session status: ";
session_start();
if (isset($_SESSION['user_id'])) {
    echo "User logged in as: " . $_SESSION['user_id'];
} else {
    echo "No user session found";
}
echo "</p>";
echo "<pre>";
print_r($_SESSION);
echo "</pre>";
?>