<?php
session_start();

// Force output - this should appear in page source
echo "<!-- DEBUG: index.php loaded at " . date('Y-m-d H:i:s') . " -->\n";

// Check session variables
$user_id = $_SESSION['user_id'] ?? null;
$access_token = $_SESSION['access_token'] ?? null;

echo "<!-- DEBUG: user_id = " . ($user_id ? $user_id : 'NULL') . " -->\n";
echo "<!-- DEBUG: access_token = " . ($access_token ? 'SET' : 'NULL') . " -->\n";

$is_logged_in = isset($_SESSION['user_id']) && isset($_SESSION['access_token']);
echo "<!-- DEBUG: is_logged_in = " . ($is_logged_in ? 'true' : 'false') . " -->\n";

// For debugging - let's add a simple way to force landing page
if (isset($_GET['debug']) && $_GET['debug'] === 'landing') {
    echo "<!-- DEBUG: Forcing landing page via debug parameter -->\n";
    require_once 'landing.php';
    exit;
}

// Check if user is logged in
if ($is_logged_in) {
    // User is logged in, redirect to search page
    echo "<!-- DEBUG: User is logged in, redirecting to search page -->\n";
    header('Location: search.php');
    exit;
} else {
    // User is not logged in, show landing page content
    echo "<!-- DEBUG: User is not logged in, including landing.php -->\n";
    require_once 'landing.php';
    exit;
}
?>