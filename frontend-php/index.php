<?php
session_start();

// Debug: Add a simple check
$is_logged_in = isset($_SESSION['user_id']) && isset($_SESSION['access_token']);

// For debugging - let's add a simple way to force landing page
if (isset($_GET['debug']) && $_GET['debug'] === 'landing') {
    echo "<!-- DEBUG: Forcing landing page -->";
    require_once 'landing.php';
    exit;
}

// Check if user is logged in
if ($is_logged_in) {
    // User is logged in, redirect to search page
    echo "<!-- DEBUG: User is logged in, redirecting to search page -->";
    header('Location: search.php');
    exit;
} else {
    // User is not logged in, show landing page content
    echo "<!-- DEBUG: User is not logged in, showing landing page -->";
    require_once 'landing.php';
    exit;
}
?>