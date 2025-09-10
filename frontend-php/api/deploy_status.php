<?php
session_start();
require_once '../config/database.php';

// Check if user is admin
if (!isset($_SESSION['user_id']) || !$_SESSION['is_admin']) {
    http_response_code(403);
    echo json_encode(['error' => 'Access denied']);
    exit;
}

header('Content-Type: application/json');

$action = $_GET['action'] ?? '';

if ($action === 'start_deploy') {
    // Start deployment in background with web deploy flag
    $deploy_command = 'WEB_DEPLOY=true sudo -E /var/www/tax-sale-compass/scripts/vps_deploy.sh > /tmp/deploy_output.log 2>&1 &';
    shell_exec($deploy_command);
    
    echo json_encode([
        'status' => 'started',
        'message' => 'Deployment started in background',
        'log_file' => '/tmp/deploy_output.log'
    ]);
    
} elseif ($action === 'get_logs') {
    $log_file = $_GET['log_file'] ?? '/var/log/taxsale_deploy.log';
    $lines = $_GET['lines'] ?? 50;
    
    if (file_exists($log_file)) {
        $logs = shell_exec("tail -n $lines $log_file 2>&1");
        $log_lines = explode("\n", trim($logs));
        
        $parsed_logs = [];
        foreach ($log_lines as $line) {
            if (empty($line)) continue;
            
            $parsed_logs[] = [
                'timestamp' => date('H:i:s'),
                'message' => $line,
                'type' => (strpos($line, 'ERROR') !== false) ? 'error' : ((strpos($line, 'Warning') !== false) ? 'warning' : 'info')
            ];
        }
        
        echo json_encode([
            'status' => 'success',
            'logs' => $parsed_logs
        ]);
    } else {
        echo json_encode([
            'status' => 'error',
            'message' => 'Log file not found'
        ]);
    }
    
} elseif ($action === 'check_status') {
    // Check if deployment is still running
    $deploy_running = shell_exec("pgrep -f 'vps_deploy.sh'");
    $services_status = [
        'nginx' => shell_exec("systemctl is-active nginx 2>/dev/null") ?: 'unknown',
        'php8.1-fpm' => shell_exec("systemctl is-active php8.1-fpm 2>/dev/null") ?: 'unknown',
        'mysql' => shell_exec("systemctl is-active mysql 2>/dev/null") ?: 'unknown'
    ];
    
    // Clean up status strings
    foreach ($services_status as $key => $status) {
        $services_status[$key] = trim($status);
    }
    
    echo json_encode([
        'status' => 'success',
        'deploy_running' => !empty(trim($deploy_running)),
        'services' => $services_status,
        'last_deploy' => file_exists('/var/log/taxsale_deploy.log') ? 
                        date('Y-m-d H:i:s', filemtime('/var/log/taxsale_deploy.log')) : 'Never'
    ]);
    
} else {
    echo json_encode(['error' => 'Invalid action']);
}
?>