<?php
session_start();
require_once 'config/database.php';

// Check if user is admin
if (!isset($_SESSION['user_id']) || !$_SESSION['is_admin']) {
    header('Location: login.php?redirect=' . urlencode($_SERVER['REQUEST_URI']));
    exit;
}

// Handle scraping requests
$scrape_result = null;
$system_result = null;

if ($_POST && isset($_POST['scrape_action'])) {
    $action = $_POST['scrape_action'];
    $api_url = API_BASE_URL . '/admin/scrape/' . $action;
    
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
    
    if ($response) {
        $scrape_result = json_decode($response, true);
    }
}

// Handle system update requests
if ($_POST && isset($_POST['system_action'])) {
    $action = $_POST['system_action'];
    
    if ($action === 'git_pull_restart') {
        $system_result = ['action' => 'git_pull_restart', 'steps' => []];
        
        // Execute git pull with detailed output
        $git_command = 'cd /var/www/tax-sale-compass && git pull origin main 2>&1';
        $git_output = shell_exec($git_command);
        $system_result['steps'][] = ['command' => 'git pull origin main', 'output' => $git_output, 'time' => date('Y-m-d H:i:s')];
        
        // Check git status after pull
        $git_status = shell_exec('cd /var/www/tax-sale-compass && git status --porcelain 2>&1');
        $system_result['steps'][] = ['command' => 'git status check', 'output' => $git_status ?: 'Working directory clean', 'time' => date('Y-m-d H:i:s')];
    } elseif ($action === 'full_deploy') {
        // Use the new deployment script
        $system_result = ['action' => 'full_deploy', 'steps' => [], 'success' => false];
        
        // Make sure script is executable
        shell_exec('chmod +x /var/www/tax-sale-compass/scripts/vps_deploy.sh 2>&1');
        
        // Execute deployment script
        $deploy_command = 'sudo /var/www/tax-sale-compass/scripts/vps_deploy.sh 2>&1';
        $deploy_output = shell_exec($deploy_command);
        
        // Parse deployment output
        $lines = explode("\n", $deploy_output);
        $current_step = '';
        
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line)) continue;
            
            if (strpos($line, 'DEPLOY_ERROR:') === 0) {
                $system_result['error'] = substr($line, 13);
                $system_result['success'] = false;
                break;
            } elseif (strpos($line, 'DEPLOY_SUCCESS') === 0) {
                $system_result['success'] = true;
            } elseif (strpos($line, '[') === 0) {
                // Timestamped log entry
                $system_result['steps'][] = [
                    'timestamp' => substr($line, 1, 19),
                    'message' => substr($line, 22),
                    'type' => 'log'
                ];
            }
        }
        
        $system_result['raw_output'] = $deploy_output;
        $system_result['deploy_log'] = '/var/log/taxsale_deploy.log';
    }
        
        // Restart backend service with status check
        $backend_output = shell_exec('sudo systemctl restart tax-sale-backend 2>&1');
        $backend_status = shell_exec('sudo systemctl is-active tax-sale-backend 2>&1');
        $system_result['steps'][] = ['command' => 'restart backend', 'output' => $backend_output . "\nStatus: " . $backend_status, 'time' => date('Y-m-d H:i:s')];
        
        // Restart PHP-FPM with status check
        $php_output = shell_exec('sudo systemctl restart php8.1-fpm 2>&1');
        $php_status = shell_exec('sudo systemctl is-active php8.1-fpm 2>&1');
        $system_result['steps'][] = ['command' => 'restart php-fpm', 'output' => $php_output . "\nStatus: " . $php_status, 'time' => date('Y-m-d H:i:s')];
        
        // Final health check
        $health_check = shell_exec('curl -s http://localhost:8001/api/health 2>&1');
        $system_result['steps'][] = ['command' => 'health check', 'output' => $health_check ?: 'Backend not responding', 'time' => date('Y-m-d H:i:s')];
        
        $system_result['success'] = true;
        $system_result['message'] = 'System updated and services restarted successfully!';
    } elseif ($action === 'cleanup_data') {
        $api_url = API_BASE_URL . '/admin/cleanup-data';
        
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
        
        if ($response) {
            $cleanup_result = json_decode($response, true);
            $system_result = [
                'action' => 'cleanup_data',
                'success' => $cleanup_result['success'] ?? false,
                'message' => $cleanup_result['message'] ?? 'Data cleanup completed',
                'details' => $cleanup_result
            ];
        } else {
            $system_result = [
                'action' => 'cleanup_data',
                'success' => false,
                'message' => 'Failed to connect to cleanup service'
            ];
        }
    }
}

// Get database stats
$db = getDB();
$total_properties = $db->query("SELECT COUNT(*) as count FROM properties")->fetch()['count'];
$active_properties = $db->query("SELECT COUNT(*) as count FROM properties WHERE status = 'active'")->fetch()['count'];
$municipalities = $db->query("SELECT municipality, COUNT(*) as count FROM properties GROUP BY municipality")->fetchAll();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - <?php echo SITE_NAME; ?></title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="index.php"><?php echo SITE_NAME; ?></a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="index.php">← Back to Search</a>
                <a class="nav-link" href="logout.php">Logout</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h1>Admin Panel</h1>
        
        <!-- Database Statistics -->
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h4>Database Statistics</h4>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3">
                                <div class="card bg-primary text-white">
                                    <div class="card-body text-center">
                                        <h3><?php echo number_format($total_properties); ?></h3>
                                        <p>Total Properties</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-success text-white">
                                    <div class="card-body text-center">
                                        <h3><?php echo number_format($active_properties); ?></h3>
                                        <p>Active Properties</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h5>Properties by Municipality</h5>
                                <ul class="list-group">
                                    <?php foreach ($municipalities as $muni): ?>
                                        <li class="list-group-item d-flex justify-content-between">
                                            <?php echo htmlspecialchars($muni['municipality']); ?>
                                            <span class="badge bg-primary"><?php echo $muni['count']; ?></span>
                                        </li>
                                    <?php endforeach; ?>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Scraping Controls -->
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h4>Data Scraping</h4>
                    </div>
                    <div class="card-body">
                        <p>Scrape tax sale data from government websites:</p>
                        
                        <form method="POST" class="d-inline">
                            <input type="hidden" name="scrape_action" value="halifax">
                            <button type="submit" class="btn btn-primary me-2">Scrape Halifax</button>
                        </form>
                        
                        <form method="POST" class="d-inline">
                            <input type="hidden" name="scrape_action" value="victoria">
                            <button type="submit" class="btn btn-primary me-2">Scrape Victoria County</button>
                        </form>
                        
                        <form method="POST" class="d-inline">
                            <input type="hidden" name="scrape_action" value="cumberland">
                            <button type="submit" class="btn btn-primary me-2">Scrape Cumberland County</button>
                        </form>
                        
                        <form method="POST" class="d-inline">
                            <input type="hidden" name="scrape_action" value="all">
                            <button type="submit" class="btn btn-success">Scrape All Municipalities</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <!-- System Update Controls -->
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h4>System Updates</h4>
                    </div>
                    <div class="card-body">
                        <p>Update the application and restart services:</p>
                        
                        <!-- Service Status Display -->
                        <div class="row mb-3">
                            <div class="col-md-12">
                                <div id="service-status" class="p-2 bg-light rounded">
                                    <strong>Service Status:</strong> <span id="status-display">Checking...</span>
                                    <button id="refresh-status" class="btn btn-sm btn-outline-secondary ms-2">
                                        <i class="fas fa-refresh"></i> Refresh
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Deployment Buttons -->
                        <div class="btn-group me-2" role="group">
                            <button id="full-deploy-btn" class="btn btn-danger">
                                <i class="fas fa-rocket"></i> Full Deploy & Restart
                            </button>
                            <button id="quick-update-btn" class="btn btn-warning">
                                <i class="fas fa-sync-alt"></i> Quick Git Pull
                            </button>
                        </div>
                        
                        <form method="POST" class="d-inline" onsubmit="return confirm('This will clean up malformed property data. Continue?')">
                            <input type="hidden" name="system_action" value="cleanup_data">
                            <button type="submit" class="btn btn-info">
                                <i class="fas fa-broom"></i> Clean Up Data
                            </button>
                        </form>
                        
                        <!-- Real-time Deployment Console -->
                        <div id="deploy-console" class="mt-3" style="display: none;">
                            <div class="card">
                                <div class="card-header d-flex justify-content-between align-items-center">
                                    <h6 class="mb-0">Deployment Console</h6>
                                    <div>
                                        <span id="deploy-status" class="badge bg-info">Ready</span>
                                        <button id="clear-console" class="btn btn-sm btn-outline-secondary ms-2">Clear</button>
                                    </div>
                                </div>
                                <div class="card-body p-0">
                                    <div id="console-output" class="bg-dark text-light p-3" style="height: 400px; overflow-y: auto; font-family: monospace; font-size: 0.85em;">
                                        <div class="text-muted">Console ready. Click deploy to start...</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <small class="text-muted d-block mt-2">
                            <strong>Full Deploy:</strong> Automated deployment with conflict resolution, service restart, and health checks<br>
                            <strong>Quick Update:</strong> Simple git pull and service restart (legacy method)<br>
                            <strong>Clean Up Data:</strong> Fix malformed property addresses and remove jumbled data
                        </small>
                    </div>
                </div>
            </div>
        </div>

        <!-- System Update Results -->
        <?php if ($system_result): ?>
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h4>System Update Results</h4>
                    </div>
                    <div class="card-body">
                        <?php if ($system_result['success']): ?>
                            <div class="alert alert-success">
                                <h5>✅ System Update Successful!</h5>
                                <p><?php echo htmlspecialchars($system_result['message']); ?></p>
                                
                                <h6>Execution Log:</h6>
                                <?php foreach ($system_result['steps'] as $step): ?>
                                    <div class="mb-3 border rounded p-2">
                                        <strong><?php echo htmlspecialchars($step['command']); ?></strong>
                                        <?php if (isset($step['time'])): ?>
                                            <small class="text-muted">- <?php echo $step['time']; ?></small>
                                        <?php endif; ?>
                                        <pre class="bg-light p-2 mt-1 mb-0" style="font-size: 0.9em;"><?php echo htmlspecialchars($step['output']); ?></pre>
                                    </div>
                                <?php endforeach; ?>
                            </div>
                        <?php else: ?>
                            <div class="alert alert-danger">
                                <h5>❌ System Update Failed</h5>
                                <p><?php echo htmlspecialchars($system_result['error'] ?? 'Unknown error'); ?></p>
                            </div>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
        </div>
        <?php endif; ?>

        <!-- Scraping Results -->
        <?php if ($scrape_result): ?>
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h4>Scraping Results</h4>
                    </div>
                    <div class="card-body">
                        <?php if ($scrape_result['success']): ?>
                            <div class="alert alert-success">
                                <h5>✅ Scraping Successful!</h5>
                                <p><strong>Municipality:</strong> <?php echo htmlspecialchars($scrape_result['municipality'] ?? 'Multiple'); ?></p>
                                <p><strong>Properties Found:</strong> <?php echo $scrape_result['properties_found'] ?? 0; ?></p>
                                
                                <?php if (isset($scrape_result['properties']) && is_array($scrape_result['properties'])): ?>
                                    <h6>Sample Properties:</h6>
                                    <ul>
                                        <?php foreach (array_slice($scrape_result['properties'], 0, 3) as $prop): ?>
                                            <li><?php echo htmlspecialchars($prop['assessment_number'] ?? 'N/A'); ?> - <?php echo htmlspecialchars($prop['civic_address'] ?? 'N/A'); ?></li>
                                        <?php endforeach; ?>
                                    </ul>
                                <?php endif; ?>
                            </div>
                        <?php else: ?>
                            <div class="alert alert-danger">
                                <h5>❌ Scraping Failed</h5>
                                <p><strong>Error:</strong> <?php echo htmlspecialchars($scrape_result['error'] ?? 'Unknown error'); ?></p>
                            </div>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
        </div>
        <?php endif; ?>

        <!-- System Information -->
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h4>System Information</h4>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item"><strong>Database:</strong> MySQL (tax_sale_compass)</li>
                            <li class="list-group-item"><strong>Backend API:</strong> FastAPI on port 8001</li>
                            <li class="list-group-item"><strong>Frontend:</strong> PHP (Native)</li>
                            <li class="list-group-item"><strong>Maps:</strong> Google Maps JavaScript API</li>
                            <li class="list-group-item"><strong>Last Updated:</strong> <?php echo date('Y-m-d H:i:s'); ?></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>