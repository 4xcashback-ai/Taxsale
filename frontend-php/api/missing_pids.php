<?php
session_start();
require_once '../config/database.php';

// Check if user is admin
if (!isset($_SESSION['is_admin']) || !$_SESSION['is_admin']) {
    http_response_code(403);
    echo json_encode(['error' => 'Admin access required']);
    exit;
}

$action = $_GET['action'] ?? '';

try {
    $db = getDB();
    
    if ($action === 'get_missing_pids') {
        // Get properties without PID numbers
        $stmt = $db->query("
            SELECT assessment_number, owner_name, civic_address, property_type, created_at, updated_at
            FROM properties 
            WHERE (pid_number IS NULL OR pid_number = '' OR pid_number = 'N/A')
            ORDER BY created_at DESC
            LIMIT 50
        ");
        $properties = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        echo json_encode([
            'status' => 'success',
            'properties' => $properties,
            'count' => count($properties)
        ]);
        
    } elseif ($action === 'rescan_property') {
        $assessment_number = $_POST['assessment_number'] ?? '';
        
        if (!$assessment_number) {
            throw new Exception('Assessment number required');
        }
        
        // Call the backend API to actually rescan the property
        $api_url = API_BASE_URL . '/admin/rescan-property';
        
        $data = json_encode(['assessment_number' => $assessment_number]);
        
        $context = stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => [
                    'Content-Type: application/json',
                    'Authorization: Bearer ' . $_SESSION['access_token']
                ],
                'content' => $data
            ]
        ]);
        
        $response = file_get_contents($api_url, false, $context);
        
        if ($response === false) {
            throw new Exception('Failed to connect to backend API');
        }
        
        $result = json_decode($response, true);
        
        if ($result && isset($result['success'])) {
            if ($result['success']) {
                error_log("Admin successfully rescanned property: {$assessment_number}");
                echo json_encode([
                    'status' => 'success',
                    'message' => $result['message'],
                    'assessment_number' => $assessment_number,
                    'updated_fields' => $result['updated_fields'] ?? []
                ]);
            } else {
                echo json_encode([
                    'status' => 'warning',
                    'message' => $result['message'],
                    'assessment_number' => $assessment_number
                ]);
            }
        } else {
            throw new Exception('Invalid response from backend API');
        }
        
    } elseif ($action === 'manual_edit') {
        $assessment_number = $_POST['assessment_number'] ?? '';
        $pid_number = $_POST['pid_number'] ?? '';
        $civic_address = $_POST['civic_address'] ?? '';
        $owner_name = $_POST['owner_name'] ?? '';
        
        if (!$assessment_number) {
            throw new Exception('Assessment number required');
        }
        
        // Build update query dynamically
        $updates = [];
        $params = [];
        
        if ($pid_number) {
            $updates[] = "pid_number = ?";
            $updates[] = "primary_pid = ?";
            $params[] = $pid_number;
            $params[] = $pid_number;
        }
        
        if ($civic_address) {
            $updates[] = "civic_address = ?";
            $params[] = $civic_address;
        }
        
        if ($owner_name) {
            $updates[] = "owner_name = ?";
            $params[] = $owner_name;
        }
        
        if (empty($updates)) {
            throw new Exception('No data to update');
        }
        
        $updates[] = "updated_at = NOW()";
        $params[] = $assessment_number;
        
        $query = "UPDATE properties SET " . implode(', ', $updates) . " WHERE assessment_number = ?";
        
        $stmt = $db->prepare($query);
        $result = $stmt->execute($params);
        
        if ($result) {
            echo json_encode([
                'status' => 'success',
                'message' => 'Property updated successfully',
                'assessment_number' => $assessment_number
            ]);
        } else {
            throw new Exception('Failed to update property');
        }
        
    } else {
        throw new Exception('Invalid action');
    }
    
} catch (Exception $e) {
    error_log("Missing PIDs API error: " . $e->getMessage());
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage()
    ]);
}
?>