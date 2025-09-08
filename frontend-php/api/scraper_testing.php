<?php
session_start();
require_once '../config/database.php';

// Check if user is admin
if (!isset($_SESSION['is_admin']) || !$_SESSION['is_admin']) {
    http_response_code(403);
    echo json_encode(['error' => 'Admin access required']);
    exit;
}

$action = $_GET['action'] ?? $_POST['action'] ?? '';

try {
    $db = getDB();
    
    if ($action === 'get_scraper_stats') {
        // Get recent scraping statistics
        $stmt = $db->query("
            SELECT 
                COUNT(*) as total_properties,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as last_1_hour,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 6 HOUR) THEN 1 END) as last_6_hours,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as last_24_hours,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 72 HOUR) THEN 1 END) as last_72_hours,
                MAX(created_at) as last_scrape_time
            FROM properties
        ");
        $stats = $stmt->fetch(PDO::FETCH_ASSOC);
        
        // Format last scrape time
        if ($stats['last_scrape_time']) {
            $last_scrape = new DateTime($stats['last_scrape_time']);
            $stats['last_scrape_formatted'] = $last_scrape->format('M j, Y H:i');
            $stats['last_scrape_relative'] = $last_scrape->diff(new DateTime())->format('%h hours ago');
        } else {
            $stats['last_scrape_formatted'] = 'Never';
            $stats['last_scrape_relative'] = 'Never';
        }
        
        echo json_encode([
            'status' => 'success',
            'stats' => $stats
        ]);
        
    } elseif ($action === 'reset_recent_scraping') {
        $timeframe = $_POST['timeframe'] ?? '24'; // hours
        
        if (!in_array($timeframe, ['1', '6', '24', '72'])) {
            throw new Exception('Invalid timeframe');
        }
        
        // Count properties that will be removed
        $count_stmt = $db->prepare("
            SELECT COUNT(*) as count 
            FROM properties 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL ? HOUR)
        ");
        $count_stmt->execute([$timeframe]);
        $count = $count_stmt->fetchColumn();
        
        if ($count == 0) {
            echo json_encode([
                'status' => 'success',
                'message' => 'No recent properties found to remove',
                'removed_count' => 0,
                'timeframe' => $timeframe
            ]);
            return;
        }
        
        // Remove recent properties
        $delete_stmt = $db->prepare("
            DELETE FROM properties 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL ? HOUR)
        ");
        $result = $delete_stmt->execute([$timeframe]);
        
        if ($result) {
            // Log the action
            error_log("Admin reset recent scraping: Removed {$count} properties from last {$timeframe} hours");
            
            echo json_encode([
                'status' => 'success',
                'message' => "Successfully removed {$count} properties from last {$timeframe} hours",
                'removed_count' => $count,
                'timeframe' => $timeframe
            ]);
        } else {
            throw new Exception('Failed to remove recent properties');
        }
        
    } elseif ($action === 'reset_specific_property') {
        $assessment_number = $_POST['assessment_number'] ?? '';
        
        if (!$assessment_number) {
            throw new Exception('Assessment number required');
        }
        
        // Remove specific property
        $stmt = $db->prepare("DELETE FROM properties WHERE assessment_number = ?");
        $result = $stmt->execute([$assessment_number]);
        
        if ($result) {
            error_log("Admin removed specific property for testing: {$assessment_number}");
            
            echo json_encode([
                'status' => 'success',
                'message' => "Property {$assessment_number} removed successfully",
                'assessment_number' => $assessment_number
            ]);
        } else {
            throw new Exception('Failed to remove property');
        }
        
    } else {
        throw new Exception('Invalid action');
    }
    
} catch (Exception $e) {
    error_log("Scraper testing API error: " . $e->getMessage());
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage()
    ]);
}
?>