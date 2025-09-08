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

        <!-- Thumbnail Generation Controls -->
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h4>Thumbnail Generation</h4>
                    </div>
                    <div class="card-body">
                        <p>Generate property boundary thumbnails for better search page performance:</p>
                        
                        <div class="d-flex align-items-center mb-3">
                            <button id="generate-thumbnails-btn" class="btn btn-info me-2">
                                <i class="fas fa-image"></i> Generate Missing Thumbnails
                            </button>
                            <button id="regenerate-all-thumbnails-btn" class="btn btn-warning me-2">
                                <i class="fas fa-sync"></i> Regenerate All Thumbnails
                            </button>
                            <div id="thumbnail-status" class="ms-3">
                                <span class="badge bg-secondary">Ready</span>
                            </div>
                        </div>
                        
                        <div id="thumbnail-progress" class="mb-3" style="display: none;">
                            <div class="progress">
                                <div id="thumbnail-progress-bar" class="progress-bar" style="width: 0%"></div>
                            </div>
                            <small id="thumbnail-progress-text" class="text-muted"></small>
                        </div>
                        
                        <div id="thumbnail-stats" class="row text-center mb-3">
                            <div class="col-md-3">
                                <div class="fw-bold text-primary fs-5" id="total-properties">-</div>
                                <div class="text-muted">Total Properties</div>
                            </div>
                            <div class="col-md-3">
                                <div class="fw-bold text-info fs-5" id="properties-with-pid">-</div>
                                <div class="text-muted">With PID Numbers</div>
                            </div>
                            <div class="col-md-3">
                                <div class="fw-bold text-success fs-5" id="properties-with-thumbnails">-</div>
                                <div class="text-muted">With Thumbnails</div>
                            </div>
                            <div class="col-md-3">
                                <div class="fw-bold text-warning fs-5" id="completion-rate">-</div>
                                <div class="text-muted">Completion Rate</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Missing PID Management -->
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h4>Missing PID Management</h4>
                    </div>
                    <div class="card-body">
                        <p>Properties without PID numbers cannot generate boundary thumbnails:</p>
                        
                        <div class="d-flex align-items-center mb-3">
                            <button id="load-missing-pids-btn" class="btn btn-warning me-2">
                                <i class="fas fa-search"></i> Show Missing PIDs
                            </button>
                            <div id="missing-pids-status" class="ms-3">
                                <span class="badge bg-secondary">Ready</span>
                            </div>
                        </div>
                        
                        <div id="missing-pids-container" style="display: none;">
                            <div class="table-responsive">
                                <table class="table table-striped" id="missing-pids-table">
                                    <thead>
                                        <tr>
                                            <th>Assessment #</th>
                                            <th>Owner</th>
                                            <th>Address</th>
                                            <th>Property Type</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="missing-pids-tbody">
                                        <!-- Data loaded dynamically -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Auction Information Management -->
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h4>Auction Information Management</h4>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i> <strong>Important:</strong> This will only update <strong>ACTIVE properties</strong> in the selected municipality. Inactive/sold properties will not be affected.
                        </div>
                        
                        <p>Update auction date and type for existing active properties by municipality:</p>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <h5>Municipality Selection</h5>
                                <div class="mb-3">
                                    <label class="form-label">Municipality:</label>
                                    <select id="auction-municipality" class="form-select">
                                        <option value="">Select Municipality...</option>
                                        <option value="Halifax Regional Municipality">Halifax Regional Municipality</option>
                                        <option value="Victoria County">Victoria County</option>
                                        <option value="Cumberland County">Cumberland County</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Auction Type:</label>
                                    <select id="auction-type" class="form-select">
                                        <option value="Public Auction">Public Auction</option>
                                        <option value="Public Tender Auction">Public Tender Auction</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Sale Date:</label>
                                    <input type="date" id="auction-sale-date" class="form-control">
                                </div>
                                
                                <button id="preview-auction-update-btn" class="btn btn-info me-2">
                                    <i class="fas fa-eye"></i> Preview Update
                                </button>
                                
                                <button id="apply-auction-update-btn" class="btn btn-warning" disabled>
                                    <i class="fas fa-save"></i> Apply Changes
                                </button>
                            </div>
                            
                            <div class="col-md-6">
                                <h5>Update Preview</h5>
                                <div id="auction-preview-container" class="border rounded p-3 bg-light">
                                    <p class="text-muted">Select municipality and click "Preview Update" to see affected properties.</p>
                                </div>
                                
                                <div id="auction-stats" class="mt-3">
                                    <div class="row text-center">
                                        <div class="col-4">
                                            <div class="fw-bold text-primary fs-5" id="total-active-properties">-</div>
                                            <div class="text-muted">Active Properties</div>
                                        </div>
                                        <div class="col-4">
                                            <div class="fw-bold text-warning fs-5" id="missing-auction-info">-</div>
                                            <div class="text-muted">Missing Auction Info</div>
                                        </div>
                                        <div class="col-4">
                                            <div class="fw-bold text-success fs-5" id="will-be-updated">-</div>
                                            <div class="text-muted">Will Be Updated</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div id="auction-update-status" class="mt-3">
                                    <span class="badge bg-secondary">Ready</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Scraper Testing Tools -->
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card border-warning">
                    <div class="card-header bg-warning">
                        <h4 class="text-dark">🧪 Scraper Testing Tools</h4>
                        <small class="text-dark">For development and testing only</small>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle"></i> <strong>Warning:</strong> These tools modify live data. Use with caution!
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <h5>Recent Scraping Data</h5>
                                <p>Remove recently scraped properties to test scraper improvements:</p>
                                
                                <div class="mb-3">
                                    <label class="form-label">Municipality:</label>
                                    <select id="scraper-reset-municipality" class="form-select">
                                        <option value="all">All Municipalities</option>
                                        <option value="Halifax">Halifax</option>
                                        <option value="Victoria">Victoria</option>
                                        <option value="Cumberland">Cumberland</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Remove properties scraped in last:</label>
                                    <select id="scraper-reset-timeframe" class="form-select">
                                        <option value="1">1 hour</option>
                                        <option value="6">6 hours</option>
                                        <option value="24" selected>24 hours</option>
                                        <option value="72">3 days</option>
                                    </select>
                                </div>
                                
                                <button id="reset-recent-scraping-btn" class="btn btn-danger">
                                    <i class="fas fa-trash"></i> Reset Recent Scraping
                                </button>
                            </div>
                            
                            <div class="col-md-6">
                                <h5>Scraper Status</h5>
                                <div id="scraper-test-stats" class="row text-center">
                                    <div class="col-6">
                                        <div class="fw-bold text-info fs-5" id="recent-properties">-</div>
                                        <div class="text-muted">Recent Properties</div>
                                    </div>
                                    <div class="col-6">
                                        <div class="fw-bold text-warning fs-5" id="last-scrape-time">-</div>
                                        <div class="text-muted">Last Scrape</div>
                                    </div>
                                </div>
                                
                                <div class="mt-3">
                                    <h6>Municipality Breakdown (24h)</h6>
                                    <div id="municipality-breakdown" class="small text-muted">
                                        Loading...
                                    </div>
                                </div>
                                
                                <div class="mt-3">
                                    <button id="refresh-scraper-stats-btn" class="btn btn-outline-info btn-sm">
                                        <i class="fas fa-refresh"></i> Refresh Stats
                                    </button>
                                </div>
                            </div>
                        </div>
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
    <script src="https://kit.fontawesome.com/your-font-awesome-kit.js" crossorigin="anonymous"></script>
    
    <script>
    class DeploymentManager {
        constructor() {
            this.consoleOutput = document.getElementById('console-output');
            this.deployStatus = document.getElementById('deploy-status');
            this.serviceStatus = document.getElementById('status-display');
            this.deployConsole = document.getElementById('deploy-console');
            this.isDeploying = false;
            
            this.initEventListeners();
            this.refreshServiceStatus();
            
            // Auto-refresh service status every 30 seconds
            setInterval(() => this.refreshServiceStatus(), 30000);
        }
        
        initEventListeners() {
            document.getElementById('full-deploy-btn').addEventListener('click', () => {
                if (!this.isDeploying) {
                    this.startFullDeploy();
                }
            });
            
            document.getElementById('quick-update-btn').addEventListener('click', () => {
                if (!this.isDeploying) {
                    this.startQuickUpdate();
                }
            });
            
            document.getElementById('refresh-status').addEventListener('click', () => {
                this.refreshServiceStatus();
            });
            
            document.getElementById('clear-console').addEventListener('click', () => {
                this.clearConsole();
            });
        }
        
        async refreshServiceStatus() {
            try {
                const response = await fetch('/api/deploy_status.php?action=check_status');
                const data = await response.json();
                
                if (data.status === 'success') {
                    let statusHtml = '';
                    Object.entries(data.services).forEach(([service, status]) => {
                        const badge = status === 'active' ? 'bg-success' : 'bg-danger';
                        statusHtml += `<span class="badge ${badge} me-1">${service}: ${status}</span>`;
                    });
                    
                    statusHtml += `<small class="text-muted ms-2">Last Deploy: ${data.last_deploy}</small>`;
                    this.serviceStatus.innerHTML = statusHtml;
                }
            } catch (error) {
                this.serviceStatus.innerHTML = '<span class="text-danger">Status check failed</span>';
            }
        }
        
        async startFullDeploy() {
            if (!confirm('This will perform a full deployment with automatic conflict resolution. Continue?')) {
                return;
            }
            
            this.isDeploying = true;
            this.showConsole();
            this.setDeployStatus('Deploying', 'bg-warning');
            this.addConsoleMessage('🚀 Starting full deployment...', 'info');
            
            try {
                // Start deployment
                const response = await fetch('/api/deploy_status.php?action=start_deploy');
                const data = await response.json();
                
                if (data.status === 'started') {
                    this.addConsoleMessage('✅ Deployment process started', 'success');
                    this.pollDeploymentStatus();
                } else {
                    throw new Error('Failed to start deployment');
                }
            } catch (error) {
                this.addConsoleMessage(`❌ Failed to start deployment: ${error.message}`, 'error');
                this.setDeployStatus('Failed', 'bg-danger');
                this.isDeploying = false;
            }
        }
        
        async startQuickUpdate() {
            if (!confirm('This will pull latest code and restart services. Continue?')) {
                return;
            }
            
            // Use the existing form submission for quick update
            const form = document.createElement('form');
            form.method = 'POST';
            form.style.display = 'none';
            
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'system_action';
            input.value = 'git_pull_restart';
            
            form.appendChild(input);
            document.body.appendChild(form);
            form.submit();
        }
        
        async pollDeploymentStatus() {
            const maxAttempts = 60; // 5 minutes max
            let attempts = 0;
            
            const poll = async () => {
                try {
                    const response = await fetch('/api/deploy_status.php?action=get_logs&lines=20');
                    const data = await response.json();
                    
                    if (data.status === 'success' && data.logs) {
                        // Add new log entries
                        data.logs.forEach(log => {
                            this.addConsoleMessage(log.message, log.type);
                        });
                    }
                    
                    // Check if deployment is still running
                    const statusResponse = await fetch('/api/deploy_status.php?action=check_status');
                    const statusData = await statusResponse.json();
                    
                    if (!statusData.deploy_running) {
                        // Deployment finished
                        this.addConsoleMessage('🎉 Deployment completed!', 'success');
                        this.setDeployStatus('Completed', 'bg-success');
                        this.isDeploying = false;
                        this.refreshServiceStatus();
                        return;
                    }
                    
                    attempts++;
                    if (attempts < maxAttempts) {
                        setTimeout(poll, 5000); // Poll every 5 seconds
                    } else {
                        this.addConsoleMessage('⚠️ Deployment monitoring timeout', 'warning');
                        this.setDeployStatus('Timeout', 'bg-warning');
                        this.isDeploying = false;
                    }
                    
                } catch (error) {
                    this.addConsoleMessage(`❌ Monitoring error: ${error.message}`, 'error');
                    this.setDeployStatus('Error', 'bg-danger');
                    this.isDeploying = false;
                }
            };
            
            poll();
        }
        
        showConsole() {
            this.deployConsole.style.display = 'block';
            this.deployConsole.scrollIntoView({ behavior: 'smooth' });
        }
        
        addConsoleMessage(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString();
            const typeColors = {
                'info': 'text-light',
                'success': 'text-success',
                'warning': 'text-warning',
                'error': 'text-danger'
            };
            
            const color = typeColors[type] || 'text-light';
            const msgDiv = document.createElement('div');
            msgDiv.className = color;
            msgDiv.innerHTML = `<span class="text-muted">[${timestamp}]</span> ${message}`;
            
            this.consoleOutput.appendChild(msgDiv);
            this.consoleOutput.scrollTop = this.consoleOutput.scrollHeight;
        }
        
        setDeployStatus(status, badgeClass) {
            this.deployStatus.textContent = status;
            this.deployStatus.className = `badge ${badgeClass}`;
        }
        
        clearConsole() {
            this.consoleOutput.innerHTML = '<div class="text-muted">Console cleared.</div>';
        }
    }
    
    // Auction Information Management
    class AuctionInfoManager {
        constructor() {
            this.initEventListeners();
            this.setDefaultValues();
        }
        
        initEventListeners() {
            document.getElementById('preview-auction-update-btn').addEventListener('click', () => {
                this.previewUpdate();
            });
            
            document.getElementById('apply-auction-update-btn').addEventListener('click', () => {
                this.applyUpdate();
            });
            
            // Auto-set default values when municipality changes
            document.getElementById('auction-municipality').addEventListener('change', (e) => {
                this.setMunicipalityDefaults(e.target.value);
            });
        }
        
        setDefaultValues() {
            // Set default sale date to a reasonable future date
            const today = new Date();
            const futureDate = new Date(today.setDate(today.getDate() + 30));
            document.getElementById('auction-sale-date').value = futureDate.toISOString().split('T')[0];
        }
        
        setMunicipalityDefaults(municipality) {
            const auctionTypeSelect = document.getElementById('auction-type');
            
            // Set default auction types based on municipality
            if (municipality === 'Halifax Regional Municipality') {
                auctionTypeSelect.value = 'Public Tender Auction';
            } else {
                auctionTypeSelect.value = 'Public Auction';
            }
        }
        
        async previewUpdate() {
            const municipality = document.getElementById('auction-municipality').value;
            
            if (!municipality) {
                alert('Please select a municipality');
                return;
            }
            
            try {
                this.setStatus('Loading preview...', 'bg-info');
                
                const response = await fetch('/api/auction_management.php?action=preview_auction_update', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `municipality=${encodeURIComponent(municipality)}`
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.displayPreview(data);
                    this.updateStats(data.stats);
                    document.getElementById('apply-auction-update-btn').disabled = false;
                    this.setStatus('Preview loaded', 'bg-success');
                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                this.setStatus('Preview failed', 'bg-danger');
                alert('Failed to load preview: ' + error.message);
            }
        }
        
        displayPreview(data) {
            const container = document.getElementById('auction-preview-container');
            const auctionType = document.getElementById('auction-type').value;
            const saleDate = document.getElementById('auction-sale-date').value;
            
            let html = `
                <div class="alert alert-warning">
                    <strong>Updating ACTIVE properties only in:</strong> ${data.municipality}
                </div>
                <p><strong>New Auction Type:</strong> <span class="badge bg-info">${auctionType}</span></p>
                ${saleDate ? `<p><strong>New Sale Date:</strong> ${saleDate}</p>` : ''}
                
                <h6 class="mt-3">Sample ACTIVE Properties (showing first 20):</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Assessment #</th>
                                <th>Address</th>
                                <th>Current Sale Date</th>
                                <th>Current Auction Type</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            data.properties.forEach(property => {
                html += `
                    <tr>
                        <td>${property.assessment_number}</td>
                        <td>${property.civic_address || 'No address'}</td>
                        <td>${property.sale_date || '<span class="text-muted">None</span>'}</td>
                        <td>${property.auction_type || '<span class="text-muted">None</span>'}</td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
            
            container.innerHTML = html;
        }
        
        updateStats(stats) {
            document.getElementById('total-active-properties').textContent = stats.total_active;
            document.getElementById('missing-auction-info').textContent = stats.missing_auction_info;
            document.getElementById('will-be-updated').textContent = stats.will_be_updated;
        }
        
        async applyUpdate() {
            const municipality = document.getElementById('auction-municipality').value;
            const auctionType = document.getElementById('auction-type').value;
            const saleDate = document.getElementById('auction-sale-date').value;
            
            if (!confirm(`Are you sure you want to update auction information for all ACTIVE properties in ${municipality}?\n\nThis will affect ONLY active properties (not sold/inactive ones).\n\nThis will set:\n- Auction Type: ${auctionType}\n- Sale Date: ${saleDate || 'No change'}\n\nThis action cannot be undone!`)) {
                return;
            }
            
            try {
                this.setStatus('Applying update...', 'bg-warning');
                
                const response = await fetch('/api/auction_management.php?action=apply_auction_update', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `municipality=${encodeURIComponent(municipality)}&auction_type=${encodeURIComponent(auctionType)}&sale_date=${saleDate}`
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.setStatus('Update completed', 'bg-success');
                    alert(data.message);
                    
                    // Refresh the preview
                    this.previewUpdate();
                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                this.setStatus('Update failed', 'bg-danger');
                alert('Failed to apply update: ' + error.message);
            }
        }
        
        setStatus(message, badgeClass) {
            const statusElement = document.getElementById('auction-update-status');
            statusElement.innerHTML = `<span class="badge ${badgeClass}">${message}</span>`;
        }
    }
    
    // Missing PID Management
    class MissingPIDManager {
        constructor() {
            this.initEventListeners();
        }
        
        initEventListeners() {
            document.getElementById('load-missing-pids-btn').addEventListener('click', () => {
                this.loadMissingPIDs();
            });
        }
        
        async loadMissingPIDs() {
            try {
                this.setStatus('Loading...', 'bg-info');
                
                const response = await fetch('/api/missing_pids.php?action=get_missing_pids');
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.displayMissingPIDs(data.properties);
                    this.setStatus(`Found ${data.count} properties`, 'bg-warning');
                    document.getElementById('missing-pids-container').style.display = 'block';
                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                this.setStatus('Error', 'bg-danger');
                alert('Failed to load missing PIDs: ' + error.message);
            }
        }
        
        displayMissingPIDs(properties) {
            const tbody = document.getElementById('missing-pids-tbody');
            tbody.innerHTML = '';
            
            properties.forEach(property => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong>${property.assessment_number}</strong></td>
                    <td>${property.owner_name || 'Unknown'}</td>
                    <td>${property.civic_address || 'No address'}</td>
                    <td><span class="badge bg-secondary">${property.property_type || 'Unknown'}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-info me-1" onclick="missingPIDManager.showEditModal('${property.assessment_number}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="btn btn-sm btn-outline-warning" onclick="missingPIDManager.rescanProperty('${property.assessment_number}')">
                            <i class="fas fa-sync"></i> Rescan
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
        
        async rescanProperty(assessmentNumber) {
            if (!confirm(`Request rescan for property ${assessmentNumber}?`)) return;
            
            try {
                const response = await fetch('/api/missing_pids.php?action=rescan_property', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `assessment_number=${assessmentNumber}`
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    alert(data.message);
                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                alert('Rescan request failed: ' + error.message);
            }
        }
        
        showEditModal(assessmentNumber) {
            const pid = prompt(`Enter PID number for property ${assessmentNumber}:`);
            if (pid) {
                this.manualEdit(assessmentNumber, pid);
            }
        }
        
        async manualEdit(assessmentNumber, pidNumber) {
            try {
                const response = await fetch('/api/missing_pids.php?action=manual_edit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `assessment_number=${assessmentNumber}&pid_number=${pidNumber}`
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    alert('Property updated successfully!');
                    this.loadMissingPIDs(); // Refresh the list
                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                alert('Manual edit failed: ' + error.message);
            }
        }
        
        setStatus(message, badgeClass) {
            const statusElement = document.getElementById('missing-pids-status');
            statusElement.innerHTML = `<span class="badge ${badgeClass}">${message}</span>`;
        }
    }
    
    // Scraper Testing Tools
    class ScraperTestingManager {
        constructor() {
            this.initEventListeners();
            this.loadMunicipalities();
            this.updateStats();
        }
        
        initEventListeners() {
            document.getElementById('reset-recent-scraping-btn').addEventListener('click', () => {
                this.resetRecentScraping();
            });
            
            document.getElementById('refresh-scraper-stats-btn').addEventListener('click', () => {
                this.updateStats();
            });
        }
        
        async loadMunicipalities() {
            try {
                const response = await fetch('/api/scraper_testing.php?action=get_municipalities');
                const data = await response.json();
                
                if (data.status === 'success') {
                    const select = document.getElementById('scraper-reset-municipality');
                    // Keep the "All Municipalities" option
                    select.innerHTML = '<option value="all">All Municipalities</option>';
                    
                    // Add actual municipalities from database
                    data.municipalities.forEach(municipality => {
                        const option = document.createElement('option');
                        option.value = municipality;
                        option.textContent = municipality;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('Failed to load municipalities:', error);
            }
        }
        
        async updateStats() {
            try {
                const response = await fetch('/api/scraper_testing.php?action=get_scraper_stats');
                const data = await response.json();
                
                if (data.status === 'success') {
                    const stats = data.stats;
                    document.getElementById('recent-properties').textContent = stats.last_24_hours;
                    document.getElementById('last-scrape-time').textContent = stats.last_scrape_relative;
                }
            } catch (error) {
                console.error('Failed to update scraper stats:', error);
            }
        }
        
        async resetRecentScraping() {
            const timeframe = document.getElementById('scraper-reset-timeframe').value;
            const municipality = document.getElementById('scraper-reset-municipality').value;
            
            const municipalityText = municipality === 'all' ? 'all municipalities' : municipality;
            
            if (!confirm(`Are you sure you want to remove properties from ${municipalityText} scraped in the last ${timeframe} hours?\n\nThis action cannot be undone!`)) {
                return;
            }
            
            try {
                const response = await fetch('/api/scraper_testing.php?action=reset_recent_scraping', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `timeframe=${timeframe}&municipality=${municipality}`
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    alert(data.message);
                    this.updateStats(); // Refresh stats
                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                alert('Reset failed: ' + error.message);
            }
        }
    }
    
    // Thumbnail Generation Manager
    class ThumbnailManager {
        constructor() {
            this.isGenerating = false;
            this.initEventListeners();
            this.updateStats();
            
            // Auto-refresh stats every 10 seconds when generating
            this.statsInterval = setInterval(() => {
                if (this.isGenerating) {
                    this.updateStats();
                }
            }, 10000);
        }
        
        initEventListeners() {
            document.getElementById('generate-thumbnails-btn').addEventListener('click', () => {
                this.startThumbnailGeneration(false);
            });
            
            document.getElementById('regenerate-all-thumbnails-btn').addEventListener('click', () => {
                if (confirm('This will regenerate all thumbnails, which may take a while. Continue?')) {
                    this.startThumbnailGeneration(true);
                }
            });
        }
        
        async updateStats() {
            try {
                const response = await fetch('/api/generate_thumbnails.php?action=get_progress');
                const data = await response.json();
                
                if (data.status === 'success') {
                    const stats = data.stats;
                    document.getElementById('total-properties').textContent = stats.total_properties;
                    document.getElementById('properties-with-pid').textContent = stats.properties_with_pid;
                    document.getElementById('properties-with-thumbnails').textContent = stats.properties_with_thumbnails;
                    document.getElementById('completion-rate').textContent = stats.completion_rate + '%';
                    
                    if (data.generation_running) {
                        this.setStatus('Generating...', 'bg-warning');
                        this.showProgress();
                        const progress = (stats.properties_with_thumbnails / stats.properties_with_pid) * 100;
                        this.updateProgress(progress, `${stats.properties_with_thumbnails}/${stats.properties_with_pid} thumbnails generated`);
                    } else if (this.isGenerating) {
                        this.setStatus('Completed', 'bg-success');
                        this.hideProgress();
                        this.isGenerating = false;
                    }
                }
            } catch (error) {
                console.error('Failed to update thumbnail stats:', error);
            }
        }
        
        async startThumbnailGeneration(regenerateAll = false) {
            if (this.isGenerating) return;
            
            this.isGenerating = true;
            this.setStatus('Starting...', 'bg-info');
            
            try {
                const response = await fetch('/api/generate_thumbnails.php?action=start_generation' + (regenerateAll ? '&regenerate=1' : ''));
                const data = await response.json();
                
                if (data.status === 'started') {
                    this.setStatus('Generating...', 'bg-warning');
                    this.showProgress();
                    this.updateProgress(0, 'Starting thumbnail generation...');
                } else {
                    throw new Error('Failed to start thumbnail generation');
                }
            } catch (error) {
                this.setStatus('Error', 'bg-danger');
                this.isGenerating = false;
                alert('Failed to start thumbnail generation: ' + error.message);
            }
        }
        
        setStatus(status, badgeClass) {
            const statusElement = document.getElementById('thumbnail-status');
            statusElement.innerHTML = `<span class="badge ${badgeClass}">${status}</span>`;
        }
        
        showProgress() {
            document.getElementById('thumbnail-progress').style.display = 'block';
        }
        
        hideProgress() {
            document.getElementById('thumbnail-progress').style.display = 'none';
        }
        
        updateProgress(percentage, text) {
            document.getElementById('thumbnail-progress-bar').style.width = percentage + '%';
            document.getElementById('thumbnail-progress-text').textContent = text;
        }
    }
    
    // Initialize managers when page loads
    document.addEventListener('DOMContentLoaded', () => {
        new DeploymentManager();
        new AuctionInfoManager();
        window.missingPIDManager = new MissingPIDManager();
        new ScraperTestingManager();
        new ThumbnailManager();
    });
    </script>
</body>
</html>