<?php
session_start();
$_SESSION = array(); // Clear all session data
session_destroy();
// Redirect to index.php to trigger the proper routing
header('Location: index.php');
exit;
?>