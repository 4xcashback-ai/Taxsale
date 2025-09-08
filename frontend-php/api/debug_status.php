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
    if ($action === 'system_status') {
        // Call backend API to get system status
        $api_url = API_BASE_URL . '/admin/system-status';
        
        $context = stream_context_create([
            'http' => [
                'method' => 'GET',
                'header' => [
                    'Content-Type: application/json',
                    'Authorization: Bearer ' . $_SESSION['access_token']
                ],
                'timeout' => 10
            ]
        ]);
        
        $response = file_get_contents($api_url, false, $context);
        
        if ($response === false) {
            throw new Exception('Failed to connect to backend API');
        }
        
        $result = json_decode($response, true);
        
        if ($result && $result['success']) {
            echo json_encode([
                'status' => 'success',
                'system_status' => $result['status'],
                'timestamp' => $result['timestamp']
            ]);
        } else {
            throw new Exception('Backend system status check failed');
        }
        
    } elseif ($action === 'get_logs') {
        $level = $_GET['level'] ?? 'all';
        $lines = intval($_GET['lines'] ?? 50);
        
        // Validate parameters
        $valid_levels = ['all', 'error', 'warning', 'info'];
        if (!in_array($level, $valid_levels)) {
            $level = 'all';
        }
        
        if ($lines < 1 || $lines > 500) {
            $lines = 50;
        }
        
        // Call backend API to get logs
        $api_url = API_BASE_URL . '/admin/logs?' . http_build_query([
            'level' => $level,
            'lines' => $lines
        ]);
        
        $context = stream_context_create([
            'http' => [
                'method' => 'GET',
                'header' => [
                    'Content-Type: application/json',
                    'Authorization: Bearer ' . $_SESSION['access_token']
                ],
                'timeout' => 15
            ]
        ]);
        
        $response = file_get_contents($api_url, false, $context);
        
        if ($response === false) {
            throw new Exception('Failed to connect to backend API');
        }
        
        $result = json_decode($response, true);
        
        if ($result && $result['success']) {
            echo json_encode([
                'status' => 'success',
                'logs' => $result['logs'],
                'total_logs' => $result['total_logs'],
                'filter' => $result['filter']
            ]);
        } else {
            throw new Exception('Backend log retrieval failed');
        }
        
    } elseif ($action === 'restart_backend') {
        // Restart backend service (be very careful with this)
        if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
            throw new Exception('POST method required');
        }
        
        // Log the restart request
        error_log("Admin requested backend restart from web interface");
        
        // Execute restart command
        $output = [];
        $return_code = 0;
        
        // Use systemctl to restart the service
        exec('sudo systemctl restart tax-sale-backend 2>&1', $output, $return_code);
        
        if ($return_code === 0) {
            echo json_encode([
                'status' => 'success',
                'message' => 'Backend restart initiated',
                'output' => implode('\n', $output)
            ]);
        } else {
            echo json_encode([
                'status' => 'error',
                'message' => 'Failed to restart backend',
                'output' => implode('\n', $output),
                'return_code' => $return_code
            ]);
        }
        
    } else {
        throw new Exception('Invalid action');
    }
    
} catch (Exception $e) {
    error_log("Debug status API error: " . $e->getMessage());
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage()
    ]);
}
?>