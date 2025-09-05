<?php
session_start();
require_once 'config/database.php';

$assessment_number = $_GET['id'] ?? '';

if (!$assessment_number) {
    header('Location: index.php');
    exit;
}

// Check if user is logged in for detailed view
$is_logged_in = isset($_SESSION['user_id']);
$is_paid_user = $is_logged_in && ($_SESSION['subscription_tier'] === 'paid' || $_SESSION['is_admin']);

// Get property
$db = getDB();
$stmt = $db->prepare("SELECT * FROM properties WHERE assessment_number = ?");
$stmt->execute([$assessment_number]);
$property = $stmt->fetch();

if (!$property) {
    header('HTTP/1.0 404 Not Found');
    include 'pages/404.php';
    exit;
}

// Check access permissions
if (!$is_logged_in) {
    // Redirect to login for property details
    header('Location: login.php?redirect=' . urlencode($_SERVER['REQUEST_URI']));
    exit;
}

if ($property['status'] === 'active' && !$is_paid_user) {
    // Show upgrade modal for active properties
    $show_upgrade_modal = true;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Property <?php echo htmlspecialchars($assessment_number); ?> - <?php echo SITE_NAME; ?></title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://maps.googleapis.com/maps/api/js?key=<?php echo GOOGLE_MAPS_API_KEY; ?>&libraries=geometry"></script>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="index.php"><?php echo SITE_NAME; ?></a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="index.php">← Back to Search</a>
                <?php if ($is_logged_in): ?>
                    <a class="nav-link" href="logout.php">Logout</a>
                <?php endif; ?>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-lg-8">
                <h1>Property Details</h1>
                
                <div class="card mb-4">
                    <div class="card-header">
                        <h3>Assessment #<?php echo htmlspecialchars($property['assessment_number']); ?></h3>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Civic Address:</strong> <?php echo htmlspecialchars($property['civic_address'] ?? 'N/A'); ?></p>
                                <p><strong>Municipality:</strong> <?php echo htmlspecialchars($property['municipality']); ?></p>
                                <p><strong>Property Type:</strong> <?php echo htmlspecialchars($property['property_type'] ?? 'N/A'); ?></p>
                                <p><strong>Tax Year:</strong> <?php echo $property['tax_year']; ?></p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Total Taxes:</strong> $<?php echo number_format($property['total_taxes'], 2); ?></p>
                                <p><strong>Status:</strong> 
                                    <span class="badge bg-<?php echo $property['status'] === 'active' ? 'success' : 'secondary'; ?>">
                                        <?php echo ucfirst($property['status']); ?>
                                    </span>
                                </p>
                                <?php if ($property['pvsc_assessment_value']): ?>
                                    <p><strong>PVSC Assessment:</strong> $<?php echo number_format($property['pvsc_assessment_value'], 2); ?> (<?php echo $property['pvsc_assessment_year']; ?>)</p>
                                <?php endif; ?>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Google Map -->
                <div class="card">
                    <div class="card-header">
                        <h4>Property Location</h4>
                    </div>
                    <div class="card-body">
                        <div id="map" style="height: 400px; width: 100%;"></div>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h4>Property Actions</h4>
                    </div>
                    <div class="card-body">
                        <?php if ($is_logged_in): ?>
                            <button class="btn btn-outline-primary btn-sm" onclick="addToFavorites()">
                                ⭐ Add to Favorites
                            </button>
                        <?php endif; ?>
                        
                        <div class="mt-3">
                            <small class="text-muted">
                                Last updated: <?php echo date('M j, Y', strtotime($property['updated_at'])); ?>
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Upgrade Modal (if needed) -->
    <?php if (isset($show_upgrade_modal)): ?>
    <div class="modal fade" id="upgradeModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Upgrade Required</h5>
                </div>
                <div class="modal-body">
                    <p>This is an active property. Upgrade to a paid subscription to view detailed information about active properties.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-primary">Upgrade Now</button>
                </div>
            </div>
        </div>
    </div>
    <?php endif; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // SIMPLE, CLEAN GOOGLE MAPS INTEGRATION - NO REACT WRAPPER CONFLICTS!
        let map;
        
        function initMap() {
            const lat = <?php echo $property['latitude'] ?? 44.6488; ?>;
            const lng = <?php echo $property['longitude'] ?? -63.5752; ?>;
            
            map = new google.maps.Map(document.getElementById("map"), {
                zoom: 15,
                center: { lat: lat, lng: lng }
            });
            
            // Add marker
            new google.maps.Marker({
                position: { lat: lat, lng: lng },
                map: map,
                title: "<?php echo htmlspecialchars($property['assessment_number']); ?>"
            });
            
            // Add boundary if available
            <?php if ($property['boundary_data']): ?>
            const boundaryData = <?php echo $property['boundary_data']; ?>;
            if (boundaryData && boundaryData.rings) {
                const boundaries = boundaryData.rings.map(ring => 
                    ring.map(coord => ({ lat: coord[1], lng: coord[0] }))
                );
                
                boundaries.forEach(boundary => {
                    new google.maps.Polygon({
                        paths: boundary,
                        strokeColor: "#FF0000",
                        strokeOpacity: 0.8,
                        strokeWeight: 2,
                        fillColor: "#FF0000",
                        fillOpacity: 0.35,
                        map: map
                    });
                });
            }
            <?php endif; ?>
        }
        
        // Initialize map when page loads
        google.maps.event.addDomListener(window, 'load', initMap);
        
        function addToFavorites() {
            // AJAX call to add to favorites
            fetch('api/favorites.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    assessment_number: '<?php echo $assessment_number; ?>' 
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Added to favorites!');
                } else {
                    alert('Error: ' + data.message);
                }
            });
        }
        
        <?php if (isset($show_upgrade_modal)): ?>
        // Show upgrade modal for active properties
        new bootstrap.Modal(document.getElementById('upgradeModal')).show();
        <?php endif; ?>
    </script>
</body>
</html>