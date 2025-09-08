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
    if ($action === 'get_config') {
        $municipality = $_POST['municipality'] ?? '';
        
        if (!$municipality) {
            throw new Exception('Municipality required');
        }
        
        // Call backend API to get scraper configuration
        $api_url = API_BASE_URL . '/admin/scraper-configs';
        
        $context = stream_context_create([
            'http' => [
                'method' => 'GET',
                'header' => [
                    'Content-Type: application/json',
                    'Authorization: Bearer ' . $_SESSION['access_token']
                ]
            ]
        ]);
        
        $response = file_get_contents($api_url, false, $context);
        
        if ($response === false) {
            throw new Exception('Failed to connect to backend API');
        }
        
        $result = json_decode($response, true);
        
        if ($result && $result['success']) {
            // Find the specific municipality configuration
            $config = null;
            foreach ($result['configs'] as $cfg) {
                if ($cfg['municipality'] === $municipality) {
                    $config = $cfg;
                    break;
                }
            }
            
            if ($config) {
                echo json_encode([
                    'status' => 'success',
                    'config' => $config
                ]);
            } else {
                echo json_encode([
                    'status' => 'error',
                    'message' => 'Configuration not found for municipality'
                ]);
            }
        } else {
            throw new Exception('Failed to get configurations from backend');
        }
        
    } elseif ($action === 'save_config') {
        // Get JSON input
        $input = file_get_contents('php://input');
        $data = json_decode($input, true);
        
        if (!$data || !isset($data['municipality'])) {
            throw new Exception('Invalid configuration data');
        }
        
        $municipality = $data['municipality'];
        
        // Call backend API to save scraper configuration
        $api_url = API_BASE_URL . '/admin/scraper-config/' . urlencode($municipality);
        
        $context = stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => [
                    'Content-Type: application/json',
                    'Authorization: Bearer ' . $_SESSION['access_token']
                ],
                'content' => json_encode($data)
            ]
        ]);
        
        $response = file_get_contents($api_url, false, $context);
        
        if ($response === false) {
            throw new Exception('Failed to connect to backend API');
        }
        
        $result = json_decode($response, true);
        
        if ($result && $result['success']) {
            error_log("Admin updated scraper config for: {$municipality}");
            echo json_encode([
                'status' => 'success',
                'message' => 'Configuration saved successfully'
            ]);
        } else {
            throw new Exception($result['message'] ?? 'Failed to save configuration');
        }
        
    } elseif ($action === 'test_config') {
        $municipality = $_POST['municipality'] ?? '';
        
        if (!$municipality) {
            throw new Exception('Municipality required');
        }
        
        // Call backend API to test scraper configuration
        $api_url = API_BASE_URL . '/admin/test-scraper-config/' . urlencode($municipality);
        
        $context = stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => [
                    'Content-Type: application/json',
                    'Authorization: Bearer ' . $_SESSION['access_token']
                ]
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
                'test_results' => $result
            ]);
        } else {
            throw new Exception($result['detail'] ?? $result['message'] ?? 'Configuration test failed');
        }
        
    } else {
        throw new Exception('Invalid action');
    }
    
} catch (Exception $e) {
    error_log("Scraper config API error: " . $e->getMessage());
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage()
    ]);
}
?>