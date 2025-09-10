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

if ($action === 'start_generation') {
    // Start thumbnail generation in background using correct path
    $script_path = dirname(__DIR__, 2) . '/scripts/batch_thumbnail_generator.php';
    $generate_command = "php {$script_path} > /tmp/thumbnail_generation.log 2>&1 &";
    shell_exec($generate_command);
    
    echo json_encode([
        'status' => 'started',
        'message' => 'Thumbnail generation started in background',
        'log_file' => '/tmp/thumbnail_generation.log',
        'script_path' => $script_path
    ]);
    
} elseif ($action === 'get_progress') {
    // Check thumbnail generation progress
    $generation_running = shell_exec("pgrep -f 'batch_thumbnail_generator.php'");
    
    // Get stats from database
    $pdo = getDB();
    
    $totalProperties = $pdo->query("SELECT COUNT(*) FROM properties")->fetchColumn();
    $propertiesWithPID = $pdo->query("SELECT COUNT(*) FROM properties WHERE pid_number IS NOT NULL AND pid_number != '' AND pid_number != 'N/A'")->fetchColumn();
    $propertiesWithThumbnails = $pdo->query("SELECT COUNT(*) FROM properties WHERE thumbnail_path IS NOT NULL AND thumbnail_path != '' AND thumbnail_path != '/assets/images/placeholder-property.jpg'")->fetchColumn();
    $needingThumbnails = $pdo->query("SELECT COUNT(*) FROM properties WHERE pid_number IS NOT NULL AND pid_number != '' AND pid_number != 'N/A' AND (thumbnail_path IS NULL OR thumbnail_path = '')")->fetchColumn();
    
    $completionRate = $propertiesWithPID > 0 ? round(($propertiesWithThumbnails / $propertiesWithPID) * 100, 2) : 0;
    
    echo json_encode([
        'status' => 'success',
        'generation_running' => !empty(trim($generation_running)),
        'stats' => [
            'total_properties' => $totalProperties,
            'properties_with_pid' => $propertiesWithPID,
            'properties_with_thumbnails' => $propertiesWithThumbnails,
            'properties_needing_thumbnails' => $needingThumbnails,
            'completion_rate' => $completionRate
        ]
    ]);
    
} elseif ($action === 'get_logs') {
    $log_file = $_GET['log_file'] ?? '/var/log/thumbnail_generation.log';
    $lines = $_GET['lines'] ?? 50;
    
    if (file_exists($log_file)) {
        $logs = shell_exec("tail -n $lines $log_file 2>&1");
        $log_lines = explode("\n", trim($logs));
        
        $parsed_logs = [];
        foreach ($log_lines as $line) {
            if (empty($line)) continue;
            
            $type = 'info';
            if (strpos($line, 'ERROR') !== false) $type = 'error';
            elseif (strpos($line, 'Failed') !== false) $type = 'warning';
            elseif (strpos($line, '✅') !== false || strpos($line, 'successful') !== false) $type = 'success';
            
            $parsed_logs[] = [
                'timestamp' => date('H:i:s'),
                'message' => $line,
                'type' => $type
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
    
} else {
    echo json_encode(['error' => 'Invalid action']);
}
?>