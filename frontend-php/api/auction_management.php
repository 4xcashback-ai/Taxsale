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
    
    if ($action === 'preview_auction_update') {
        $municipality = $_POST['municipality'] ?? '';
        
        if (!$municipality) {
            throw new Exception('Municipality is required');
        }
        
        // Get properties that would be affected
        $stmt = $db->prepare("
            SELECT 
                assessment_number, 
                owner_name, 
                civic_address, 
                sale_date, 
                auction_type,
                created_at
            FROM properties 
            WHERE municipality = ? 
            AND status = 'active'
            ORDER BY assessment_number
            LIMIT 20
        ");
        $stmt->execute([$municipality]);
        $properties = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Get statistics
        $stats_stmt = $db->prepare("
            SELECT 
                COUNT(*) as total_active,
                COUNT(CASE WHEN sale_date IS NULL OR auction_type IS NULL THEN 1 END) as missing_auction_info,
                COUNT(CASE WHEN sale_date IS NULL OR auction_type IS NULL THEN 1 END) as will_be_updated
            FROM properties 
            WHERE municipality = ? 
            AND status = 'active'
        ");
        $stats_stmt->execute([$municipality]);
        $stats = $stats_stmt->fetch(PDO::FETCH_ASSOC);
        
        echo json_encode([
            'status' => 'success',
            'properties' => $properties,
            'stats' => $stats,
            'municipality' => $municipality
        ]);
        
    } elseif ($action === 'apply_auction_update') {
        $municipality = $_POST['municipality'] ?? '';
        $auction_type = $_POST['auction_type'] ?? '';
        $sale_date = $_POST['sale_date'] ?? '';
        
        if (!$municipality || !$auction_type) {
            throw new Exception('Municipality and auction type are required');
        }
        
        // Validate auction type
        if (!in_array($auction_type, ['Public Auction', 'Public Tender Auction'])) {
            throw new Exception('Invalid auction type');
        }
        
        // Validate date format if provided
        if ($sale_date && !DateTime::createFromFormat('Y-m-d', $sale_date)) {
            throw new Exception('Invalid date format');
        }
        
        // Count properties that will be updated
        $count_stmt = $db->prepare("
            SELECT COUNT(*) as count 
            FROM properties 
            WHERE municipality = ? 
            AND status = 'active'
            AND (sale_date IS NULL OR auction_type IS NULL OR sale_date != ? OR auction_type != ?)
        ");
        $count_stmt->execute([$municipality, $sale_date, $auction_type]);
        $count = $count_stmt->fetchColumn();
        
        if ($count == 0) {
            echo json_encode([
                'status' => 'success',
                'message' => 'No properties need updating - all already have correct auction information',
                'updated_count' => 0,
                'municipality' => $municipality
            ]);
            return;
        }
        
        // Apply the update
        $update_parts = ['auction_type = ?', 'updated_at = NOW()'];
        $params = [$auction_type];
        
        if ($sale_date) {
            $update_parts[] = 'sale_date = ?';
            $params[] = $sale_date;
        }
        
        $params[] = $municipality; // for WHERE clause
        
        $update_query = "
            UPDATE properties 
            SET " . implode(', ', $update_parts) . "
            WHERE municipality = ? 
            AND status = 'active'
        ";
        
        $stmt = $db->prepare($update_query);
        $result = $stmt->execute($params);
        
        if ($result) {
            $actual_updated = $stmt->rowCount();
            
            // Log the action
            error_log("Admin updated auction info for {$municipality}: {$actual_updated} properties updated with type '{$auction_type}'" . ($sale_date ? " and date '{$sale_date}'" : ""));
            
            echo json_encode([
                'status' => 'success',
                'message' => "Successfully updated {$actual_updated} properties in {$municipality}",
                'updated_count' => $actual_updated,
                'municipality' => $municipality,
                'auction_type' => $auction_type,
                'sale_date' => $sale_date
            ]);
        } else {
            throw new Exception('Failed to update properties');
        }
        
    } elseif ($action === 'get_municipality_stats') {
        // Get auction information statistics by municipality
        $stmt = $db->query("
            SELECT 
                municipality,
                COUNT(*) as total_properties,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_properties,
                COUNT(CASE WHEN sale_date IS NOT NULL THEN 1 END) as with_sale_date,
                COUNT(CASE WHEN auction_type IS NOT NULL THEN 1 END) as with_auction_type,
                COUNT(CASE WHEN auction_type = 'Public Tender Auction' THEN 1 END) as tender_auctions,
                COUNT(CASE WHEN auction_type = 'Public Auction' THEN 1 END) as public_auctions
            FROM properties 
            GROUP BY municipality
            ORDER BY active_properties DESC
        ");
        $stats = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        echo json_encode([
            'status' => 'success',
            'municipality_stats' => $stats
        ]);
        
    } else {
        throw new Exception('Invalid action');
    }
    
} catch (Exception $e) {
    error_log("Auction management API error: " . $e->getMessage());
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage()
    ]);
}
?>