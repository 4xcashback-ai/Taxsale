<?php
session_start();

// Debug info
$is_logged_in = isset($_SESSION['user_id']) && isset($_SESSION['access_token']);

// Check if user is logged in
if ($is_logged_in) {
    // User is logged in, redirect to search page
    header('Location: search.php');
    exit;
} else {
    // User is not logged in, show landing page
    require_once 'landing.php';
    exit;
}
?>