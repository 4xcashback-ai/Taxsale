<?php
session_start();

// Check if user is logged in
if (isset($_SESSION['user_id']) && isset($_SESSION['access_token'])) {
    // User is logged in, redirect to search page
    header('Location: search.php');
    exit;
} else {
    // User is not logged in, show landing page
    include 'landing.php';
    exit;
}
?>