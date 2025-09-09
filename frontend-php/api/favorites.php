<?php
session_start();
require_once '../config/database.php';

// Set JSON response headers
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, DELETE');
header('Access-Control-Allow-Headers: Content-Type');

// Check if user is logged in
if (!isset($_SESSION['user_id'])) {
    http_response_code(401);
    echo json_encode(['success' => false, 'message' => 'User not logged in']);
    exit;
}

$user_id = $_SESSION['user_id'];

// Check if user is a paying customer
$db = getDB();
if (!$db) {
    http_response_code(500);
    echo json_encode(['success' => false, 'message' => 'Database connection failed']);
    exit;
}

try {
    // Check user subscription status
    $stmt = $db->prepare("SELECT subscription_status FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $user = $stmt->fetch();
    
    if (!$user || $user['subscription_status'] !== 'paid') {
        http_response_code(403);
        echo json_encode(['success' => false, 'message' => 'Favorites feature requires a paid subscription']);
        exit;
    }

    $method = $_SERVER['REQUEST_METHOD'];
    
    switch ($method) {
        case 'GET':
            // Get user's favorites
            handleGetFavorites($db, $user_id);
            break;
            
        case 'POST':
            // Add to favorites
            $input = json_decode(file_get_contents('php://input'), true);
            $assessment_number = $input['assessment_number'] ?? null;
            
            if (!$assessment_number) {
                http_response_code(400);
                echo json_encode(['success' => false, 'message' => 'Assessment number required']);
                exit;
            }
            
            handleAddFavorite($db, $user_id, $assessment_number);
            break;
            
        case 'DELETE':
            // Remove from favorites
            $input = json_decode(file_get_contents('php://input'), true);
            $assessment_number = $input['assessment_number'] ?? null;
            
            if (!$assessment_number) {
                http_response_code(400);
                echo json_encode(['success' => false, 'message' => 'Assessment number required']);
                exit;
            }
            
            handleRemoveFavorite($db, $user_id, $assessment_number);
            break;
            
        default:
            http_response_code(405);
            echo json_encode(['success' => false, 'message' => 'Method not allowed']);
            break;
    }

} catch (Exception $e) {
    error_log("Favorites API error: " . $e->getMessage());
    http_response_code(500);
    echo json_encode(['success' => false, 'message' => 'Internal server error']);
}

function handleGetFavorites($db, $user_id) {
    try {
        $stmt = $db->prepare("
            SELECT p.*, uf.favorited_at,
                   COALESCE(p.favorite_count, 0) as favorite_count
            FROM user_favorites uf 
            JOIN properties p ON uf.assessment_number = p.assessment_number 
            WHERE uf.user_id = ? 
            ORDER BY uf.favorited_at DESC
        ");
        $stmt->execute([$user_id]);
        $favorites = $stmt->fetchAll();
        
        // Get total count
        $stmt = $db->prepare("SELECT COUNT(*) as count FROM user_favorites WHERE user_id = ?");
        $stmt->execute([$user_id]);
        $count = $stmt->fetch()['count'];
        
        echo json_encode([
            'success' => true, 
            'favorites' => $favorites,
            'count' => $count,
            'max_allowed' => 50
        ]);
        
    } catch (Exception $e) {
        error_log("Get favorites error: " . $e->getMessage());
        http_response_code(500);
        echo json_encode(['success' => false, 'message' => 'Failed to get favorites']);
    }
}

function handleAddFavorite($db, $user_id, $assessment_number) {
    try {
        // Check if property exists
        $stmt = $db->prepare("SELECT assessment_number FROM properties WHERE assessment_number = ?");
        $stmt->execute([$assessment_number]);
        if (!$stmt->fetch()) {
            http_response_code(404);
            echo json_encode(['success' => false, 'message' => 'Property not found']);
            return;
        }
        
        // Check current favorite count for user
        $stmt = $db->prepare("SELECT COUNT(*) as count FROM user_favorites WHERE user_id = ?");
        $stmt->execute([$user_id]);
        $current_count = $stmt->fetch()['count'];
        
        if ($current_count >= 50) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'Maximum of 50 favorites allowed']);
            return;
        }
        
        // Check if already favorited
        $stmt = $db->prepare("SELECT id FROM user_favorites WHERE user_id = ? AND assessment_number = ?");
        $stmt->execute([$user_id, $assessment_number]);
        if ($stmt->fetch()) {
            echo json_encode(['success' => false, 'message' => 'Property already in favorites']);
            return;
        }
        
        // Add to favorites
        $stmt = $db->prepare("INSERT INTO user_favorites (user_id, assessment_number) VALUES (?, ?)");
        $stmt->execute([$user_id, $assessment_number]);
        
        // Get updated favorite count for this property
        $stmt = $db->prepare("SELECT favorite_count FROM properties WHERE assessment_number = ?");
        $stmt->execute([$assessment_number]);
        $property = $stmt->fetch();
        
        echo json_encode([
            'success' => true, 
            'message' => 'Added to favorites',
            'favorite_count' => $property['favorite_count'] ?? 0
        ]);
        
    } catch (Exception $e) {
        error_log("Add favorite error: " . $e->getMessage());
        http_response_code(500);
        echo json_encode(['success' => false, 'message' => 'Failed to add favorite']);
    }
}

function handleRemoveFavorite($db, $user_id, $assessment_number) {
    try {
        // Remove from favorites
        $stmt = $db->prepare("DELETE FROM user_favorites WHERE user_id = ? AND assessment_number = ?");
        $stmt->execute([$user_id, $assessment_number]);
        
        if ($stmt->rowCount() === 0) {
            echo json_encode(['success' => false, 'message' => 'Property not in favorites']);
            return;
        }
        
        // Get updated favorite count for this property
        $stmt = $db->prepare("SELECT favorite_count FROM properties WHERE assessment_number = ?");
        $stmt->execute([$assessment_number]);
        $property = $stmt->fetch();
        
        echo json_encode([
            'success' => true, 
            'message' => 'Removed from favorites',
            'favorite_count' => $property['favorite_count'] ?? 0
        ]);
        
    } catch (Exception $e) {
        error_log("Remove favorite error: " . $e->getMessage());
        http_response_code(500);
        echo json_encode(['success' => false, 'message' => 'Failed to remove favorite']);
    }
}
?>