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
        $status = [];
        
        // Check backend service status directly
        $backend_status = shell_exec('systemctl is-active tax-sale-backend 2>/dev/null');
        $status['backend_service'] = trim($backend_status) ?: 'unknown';
        
        // Check if port 8001 is listening
        $port_check = shell_exec('ss -tlnp | grep :8001 2>/dev/null');
        $status['port_8001'] = !empty(trim($port_check)) ? 'listening' : 'not_listening';
        
        // Check database connection directly
        try {
            $db = getDB();
            $db->query("SELECT 1");
            $status['database_connection'] = 'connected';
        } catch (Exception $e) {
            $status['database_connection'] = 'error: ' . substr($e->getMessage(), 0, 100);
        }
        
        // Get backend process info
        $backend_processes = shell_exec("ps aux | grep 'server_mysql.py' | grep -v grep 2>/dev/null");
        $process_lines = array_filter(explode("\n", trim($backend_processes)));
        $status['backend_processes'] = count($process_lines);
        $status['backend_process_details'] = $process_lines;
        
        // Check memory usage
        $memory_info = shell_exec('free -m 2>/dev/null');
        if ($memory_info) {
            $lines = explode("\n", $memory_info);
            if (isset($lines[1])) {
                $mem_parts = preg_split('/\s+/', $lines[1]);
                if (count($mem_parts) >= 3) {
                    $total = intval($mem_parts[1]);
                    $used = intval($mem_parts[2]);
                    $status['memory_usage'] = [
                        'total_mb' => $total,
                        'used_mb' => $used,
                        'free_mb' => $total - $used,
                        'percent' => $total > 0 ? round(($used / $total) * 100, 1) : 0
                    ];
                }
            }
        }
        
        // Check disk usage
        $disk_info = shell_exec('df -h / 2>/dev/null');
        if ($disk_info) {
            $lines = explode("\n", $disk_info);
            if (isset($lines[1])) {
                $disk_parts = preg_split('/\s+/', $lines[1]);
                if (count($disk_parts) >= 5) {
                    $status['disk_usage'] = [
                        'total' => $disk_parts[1],
                        'used' => $disk_parts[2],
                        'available' => $disk_parts[3],
                        'percent' => rtrim($disk_parts[4], '%')
                    ];
                }
            }
        }
        
        // Test backend API connectivity
        $api_test = @file_get_contents('http://localhost:8001/api/municipalities', false, stream_context_create([
            'http' => ['timeout' => 3]
        ]));
        $status['api_connectivity'] = $api_test !== false ? 'responding' : 'not_responding';
        
        // Get uptime
        $uptime = shell_exec('uptime 2>/dev/null');
        $status['system_uptime'] = trim($uptime) ?: 'unknown';
        
        echo json_encode([
            'status' => 'success',
            'system_status' => $status,
            'timestamp' => date('Y-m-d H:i:s')
        ]);
        
    } elseif ($action === 'get_logs') {
        $level = $_GET['level'] ?? 'all';
        $lines = intval($_GET['lines'] ?? 50);
        
        // Validate parameters
        $lines = max(10, min(500, $lines));
        
        $logs = [];
        
        // Get systemd logs for backend service
        $log_command = "journalctl -u tax-sale-backend --lines {$lines} --no-pager -o json 2>/dev/null";
        $log_output = shell_exec($log_command);
        
        if ($log_output) {
            $log_lines = array_filter(explode("\n", trim($log_output)));
            
            foreach ($log_lines as $line) {
                $log_entry = json_decode($line, true);
                if ($log_entry && isset($log_entry['MESSAGE'])) {
                    $message = $log_entry['MESSAGE'];
                    $timestamp = isset($log_entry['__REALTIME_TIMESTAMP']) ? 
                        date('Y-m-d H:i:s', $log_entry['__REALTIME_TIMESTAMP'] / 1000000) : 
                        date('Y-m-d H:i:s');
                    
                    // Filter by log level
                    $include = true;
                    if ($level === 'error') {
                        $include = stripos($message, 'error') !== false || 
                                  stripos($message, 'exception') !== false || 
                                  stripos($message, 'failed') !== false ||
                                  stripos($message, 'traceback') !== false;
                    } elseif ($level === 'warning') {
                        $include = stripos($message, 'warning') !== false || 
                                  stripos($message, 'warn') !== false;
                    } elseif ($level === 'info') {
                        $include = !preg_match('/error|exception|failed|warning|warn/i', $message);
                    }
                    
                    if ($include) {
                        $priority = $log_entry['PRIORITY'] ?? '6';
                        $logs[] = [
                            'timestamp' => $timestamp,
                            'message' => $message,
                            'priority' => $priority,
                            'service' => 'tax-sale-backend'
                        ];
                    }
                }
            }
        }
        
        // Also get nginx error logs if available
        $nginx_errors = shell_exec('tail -n 10 /var/log/nginx/error.log 2>/dev/null');
        if ($nginx_errors) {
            $error_lines = array_filter(explode("\n", trim($nginx_errors)));
            foreach ($error_lines as $line) {
                if (!empty(trim($line))) {
                    $logs[] = [
                        'timestamp' => date('Y-m-d H:i:s'),
                        'message' => $line,
                        'priority' => '3',
                        'service' => 'nginx'
                    ];
                }
            }
        }
        
        // Sort by timestamp (most recent first)
        usort($logs, function($a, $b) {
            return strtotime($b['timestamp']) - strtotime($a['timestamp']);
        });
        
        echo json_encode([
            'status' => 'success',
            'logs' => array_slice($logs, 0, $lines),
            'total_logs' => count($logs),
            'filter' => $level
        ]);
        
    } elseif ($action === 'restart_backend') {
        if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
            throw new Exception('POST method required');
        }
        
        // Log the restart request
        error_log("Admin requested backend restart from web interface");
        
        // Execute restart command
        $output = shell_exec('sudo systemctl restart tax-sale-backend 2>&1');
        
        // Wait a moment for service to start
        sleep(2);
        
        // Check if service started successfully
        $status_check = shell_exec('systemctl is-active tax-sale-backend 2>/dev/null');
        $is_active = trim($status_check) === 'active';
        
        echo json_encode([
            'status' => 'success',
            'message' => $is_active ? 'Backend restarted successfully' : 'Backend restart may have failed',
            'service_status' => trim($status_check) ?: 'unknown',
            'output' => trim($output) ?: 'No output'
        ]);
        
    } elseif ($action === 'test_api') {
        // Test various API endpoints
        $tests = [];
        
        $endpoints = [
            'health' => 'http://localhost:8001/api/health',
            'municipalities' => 'http://localhost:8001/api/municipalities',
            'scraper-configs' => 'http://localhost:8001/api/admin/scraper-configs'
        ];
        
        foreach ($endpoints as $name => $url) {
            $start_time = microtime(true);
            
            $context = stream_context_create([
                'http' => [
                    'timeout' => 5,
                    'header' => $name === 'scraper-configs' ? 
                        "Authorization: Bearer " . ($_SESSION['access_token'] ?? 'none') : ''
                ]
            ]);
            
            $response = @file_get_contents($url, false, $context);
            $response_time = round((microtime(true) - $start_time) * 1000, 2);
            
            $tests[$name] = [
                'url' => $url,
                'status' => $response !== false ? 'success' : 'failed',
                'response_time_ms' => $response_time,
                'response_length' => $response ? strlen($response) : 0,
                'response_preview' => $response ? substr($response, 0, 100) . '...' : 'No response'
            ];
        }
        
        echo json_encode([
            'status' => 'success',
            'api_tests' => $tests,
            'timestamp' => date('Y-m-d H:i:s')
        ]);
        
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