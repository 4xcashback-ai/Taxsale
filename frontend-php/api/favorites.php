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
    $user = $db->users->findOne(['_id' => new MongoDB\BSON\ObjectId($user_id)]);
    
    if (!$user || ($user['subscription_status'] ?? 'free') !== 'paid') {
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
        // Get user's favorites with property details
        $pipeline = [
            ['$match' => ['user_id' => $user_id]],
            ['$lookup' => [
                'from' => 'properties',
                'localField' => 'assessment_number',
                'foreignField' => 'assessment_number', 
                'as' => 'property'
            ]],
            ['$unwind' => '$property'],
            ['$sort' => ['favorited_at' => -1]]
        ];
        
        $favorites = $db->user_favorites->aggregate($pipeline)->toArray();
        
        // Convert to array and merge property data
        $favoritesArray = [];
        foreach ($favorites as $favorite) {
            $property = mongoToArray($favorite['property']);
            $property['favorited_at'] = $favorite['favorited_at']->toDateTime()->format('Y-m-d H:i:s');
            $property['favorite_count'] = $property['favorite_count'] ?? 0;
            $favoritesArray[] = $property;
        }
        
        // Get total count
        $count = $db->user_favorites->countDocuments(['user_id' => $user_id]);
        
        echo json_encode([
            'success' => true, 
            'favorites' => $favoritesArray,
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
        $property = $db->properties->findOne(['assessment_number' => $assessment_number]);
        if (!$property) {
            http_response_code(404);
            echo json_encode(['success' => false, 'message' => 'Property not found']);
            return;
        }
        
        // Check current favorite count for user
        $current_count = $db->user_favorites->countDocuments(['user_id' => $user_id]);
        
        if ($current_count >= 50) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'Maximum of 50 favorites allowed']);
            return;
        }
        
        // Check if already favorited
        $existing = $db->user_favorites->findOne([
            'user_id' => $user_id,
            'assessment_number' => $assessment_number
        ]);
        
        if ($existing) {
            echo json_encode(['success' => false, 'message' => 'Property already in favorites']);
            return;
        }
        
        // Add to favorites
        $db->user_favorites->insertOne([
            'user_id' => $user_id,
            'assessment_number' => $assessment_number,
            'favorited_at' => new MongoDB\BSON\UTCDateTime()
        ]);
        
        // Update favorite count for property
        $new_count = $db->user_favorites->countDocuments(['assessment_number' => $assessment_number]);
        $db->properties->updateOne(
            ['assessment_number' => $assessment_number],
            ['$set' => ['favorite_count' => $new_count]]
        );
        
        echo json_encode([
            'success' => true, 
            'message' => 'Added to favorites',
            'favorite_count' => $new_count
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
        $result = $db->user_favorites->deleteOne([
            'user_id' => $user_id,
            'assessment_number' => $assessment_number
        ]);
        
        if ($result->getDeletedCount() === 0) {
            echo json_encode(['success' => false, 'message' => 'Property not in favorites']);
            return;
        }
        
        // Update favorite count for property
        $new_count = $db->user_favorites->countDocuments(['assessment_number' => $assessment_number]);
        $db->properties->updateOne(
            ['assessment_number' => $assessment_number],
            ['$set' => ['favorite_count' => $new_count]]
        );
        
        echo json_encode([
            'success' => true, 
            'message' => 'Removed from favorites',
            'favorite_count' => $new_count
        ]);
        
    } catch (Exception $e) {
        error_log("Remove favorite error: " . $e->getMessage());
        http_response_code(500);
        echo json_encode(['success' => false, 'message' => 'Failed to remove favorite']);
    }
}
?>