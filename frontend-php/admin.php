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