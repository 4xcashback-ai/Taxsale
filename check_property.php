<?php
require_once 'frontend-php/config/database.php';

try {
    $pdo = getDB();
    
    $stmt = $pdo->prepare("SELECT assessment_number, property_type, civic_address, owner_name, municipality FROM properties WHERE assessment_number = ?");
    $stmt->execute(['01999184']);
    
    $property = $stmt->fetch();
    
    if ($property) {
        echo "Property found:\n";
        echo "Assessment Number: " . $property['assessment_number'] . "\n";
        echo "Property Type: " . $property['property_type'] . "\n";
        echo "Civic Address: " . $property['civic_address'] . "\n";
        echo "Owner Name: " . $property['owner_name'] . "\n";
        echo "Municipality: " . $property['municipality'] . "\n";
    } else {
        echo "Property 01999184 not found in database.\n";
    }
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>