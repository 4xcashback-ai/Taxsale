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

                <!-- Interactive Property Map -->
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h4><i class="fas fa-map-marked-alt"></i> Interactive Property Map</h4>
                        <div class="btn-group btn-group-sm" role="group">
                            <button type="button" class="btn btn-outline-primary" onclick="toggleMapType('satellite')" title="Satellite View">
                                <i class="fas fa-satellite"></i>
                            </button>
                            <button type="button" class="btn btn-outline-primary" onclick="toggleMapType('roadmap')" title="Map View">
                                <i class="fas fa-map"></i>
                            </button>
                            <button type="button" class="btn btn-outline-primary" onclick="toggleMapType('hybrid')" title="Hybrid View">
                                <i class="fas fa-layer-group"></i>
                            </button>
                            <button type="button" class="btn btn-outline-success" onclick="centerOnProperty()" title="Center on Property">
                                <i class="fas fa-crosshairs"></i>
                            </button>
                        </div>
                    </div>
                    <div class="card-body p-0">
                        <div id="map" style="height: 500px; width: 100%; border-radius: 0 0 0.375rem 0.375rem;"></div>
                        <div class="p-3 bg-light border-top">
                            <div class="row text-center">
                                <div class="col-md-3">
                                    <small class="text-muted"><strong>Coordinates</strong></small><br>
                                    <small><?php echo number_format($property['latitude'] ?? 44.6488, 6); ?>, <?php echo number_format($property['longitude'] ?? -63.5752, 6); ?></small>
                                </div>
                                <div class="col-md-3">
                                    <small class="text-muted"><strong>View Type</strong></small><br>
                                    <small id="current-map-type">Satellite</small>
                                </div>
                                <div class="col-md-3">
                                    <small class="text-muted"><strong>Zoom Level</strong></small><br>
                                    <small id="current-zoom">17</small>
                                </div>
                                <div class="col-md-3">
                                    <small class="text-muted"><strong>Boundary Data</strong></small><br>
                                    <small><?php echo $property['boundary_data'] ? '✅ Available' : '❌ Not Available'; ?></small>
                                </div>
                            </div>
                        </div>
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
            
            // Enhanced map configuration with satellite view
            map = new google.maps.Map(document.getElementById("map"), {
                zoom: 17,  // Closer zoom for property details
                center: { lat: lat, lng: lng },
                mapTypeId: google.maps.MapTypeId.SATELLITE,  // Default to satellite view
                mapTypeControl: true,
                mapTypeControlOptions: {
                    style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
                    position: google.maps.ControlPosition.TOP_RIGHT,
                    mapTypeIds: [
                        google.maps.MapTypeId.ROADMAP,
                        google.maps.MapTypeId.SATELLITE,
                        google.maps.MapTypeId.HYBRID,
                        google.maps.MapTypeId.TERRAIN
                    ]
                },
                streetViewControl: true,
                fullscreenControl: true,
                zoomControl: true,
                scaleControl: true
            });
            
            // Enhanced marker with custom icon
            const marker = new google.maps.Marker({
                position: { lat: lat, lng: lng },
                map: map,
                title: "<?php echo htmlspecialchars($property['assessment_number']); ?>",
                icon: {
                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                        <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="16" cy="16" r="12" fill="#FF4444" stroke="#FFFFFF" stroke-width="2"/>
                            <text x="16" y="20" text-anchor="middle" fill="white" font-family="Arial" font-size="12" font-weight="bold">P</text>
                        </svg>
                    `),
                    scaledSize: new google.maps.Size(32, 32),
                    anchor: new google.maps.Point(16, 16)
                }
            });
            
            // Enhanced info window
            const infoWindow = new google.maps.InfoWindow({
                content: `
                    <div style="max-width: 300px;">
                        <h6><strong>Property <?php echo htmlspecialchars($property['assessment_number']); ?></strong></h6>
                        <p><strong>Address:</strong> <?php echo htmlspecialchars($property['civic_address'] ?? 'N/A'); ?></p>
                        <p><strong>Type:</strong> <?php echo htmlspecialchars(ucfirst(str_replace('_', ' ', $property['property_type'] ?? 'N/A'))); ?></p>
                        <p><strong>Municipality:</strong> <?php echo htmlspecialchars($property['municipality']); ?></p>
                        <?php if ($property['opening_bid']): ?>
                            <p><strong>Opening Bid:</strong> $<?php echo number_format($property['opening_bid'], 2); ?></p>
                        <?php endif; ?>
                    </div>
                `
            });
            
            marker.addListener("click", () => {
                infoWindow.open(map, marker);
            });
            
            // Enhanced property boundaries with better styling
            <?php if ($property['boundary_data']): ?>
            const boundaryData = <?php echo $property['boundary_data']; ?>;
            let propertyPolygon = null;
            
            if (boundaryData && boundaryData.rings) {
                const boundaries = boundaryData.rings.map(ring => 
                    ring.map(coord => ({ lat: coord[1], lng: coord[0] }))
                );
                
                boundaries.forEach((boundary, index) => {
                    propertyPolygon = new google.maps.Polygon({
                        paths: boundary,
                        strokeColor: "#FF6B35",      // Orange stroke
                        strokeOpacity: 0.9,
                        strokeWeight: 3,
                        fillColor: "#FF6B35",        // Orange fill
                        fillOpacity: 0.2,
                        map: map,
                        clickable: true
                    });
                    
                    // Add boundary info window
                    const boundaryInfoWindow = new google.maps.InfoWindow({
                        content: `
                            <div>
                                <h6><strong>Property Boundary</strong></h6>
                                <p>Assessment: <?php echo htmlspecialchars($property['assessment_number']); ?></p>
                                <p>Area boundary as recorded in government records</p>
                            </div>
                        `
                    });
                    
                    propertyPolygon.addListener("click", (event) => {
                        boundaryInfoWindow.setPosition(event.latLng);
                        boundaryInfoWindow.open(map);
                    });
                });
                
                // Fit map to show entire property boundary
                if (boundaries.length > 0 && boundaries[0].length > 0) {
                    const bounds = new google.maps.LatLngBounds();
                    boundaries[0].forEach(point => bounds.extend(point));
                    
                    // Add some padding around the boundary
                    const extendedBounds = new google.maps.LatLngBounds(
                        new google.maps.LatLng(bounds.getSouthWest().lat() - 0.0005, bounds.getSouthWest().lng() - 0.0005),
                        new google.maps.LatLng(bounds.getNorthEast().lat() + 0.0005, bounds.getNorthEast().lng() + 0.0005)
                    );
                    
                    map.fitBounds(extendedBounds);
                    
                    // Ensure minimum zoom level
                    google.maps.event.addListenerOnce(map, 'bounds_changed', function() {
                        if (map.getZoom() > 19) {
                            map.setZoom(19);
                        }
                    });
                }
            }
            <?php else: ?>
            // No boundary data - just center on coordinates with appropriate zoom
            map.setZoom(17);
            <?php endif; ?>
            
            // Add map legend
            const legend = document.createElement('div');
            legend.style.backgroundColor = 'white';
            legend.style.border = '2px solid #ccc';
            legend.style.borderRadius = '3px';
            legend.style.margin = '10px';
            legend.style.padding = '8px';
            legend.style.fontSize = '12px';
            legend.style.fontFamily = 'Arial, sans-serif';
            
            legend.innerHTML = `
                <div><strong>Property Map Legend</strong></div>
                <div style="margin-top: 5px;">
                    <span style="color: #FF4444;">●</span> Property Location<br>
                    <span style="color: #FF6B35;">■</span> Property Boundary
                </div>
            `;
            
            map.controls[google.maps.ControlPosition.LEFT_BOTTOM].push(legend);
        }
        
        // Map control functions
        function toggleMapType(type) {
            if (map) {
                const mapTypes = {
                    'satellite': google.maps.MapTypeId.SATELLITE,
                    'roadmap': google.maps.MapTypeId.ROADMAP,
                    'hybrid': google.maps.MapTypeId.HYBRID,
                    'terrain': google.maps.MapTypeId.TERRAIN
                };
                
                map.setMapTypeId(mapTypes[type]);
                document.getElementById('current-map-type').textContent = type.charAt(0).toUpperCase() + type.slice(1);
                
                // Update button states
                document.querySelectorAll('.btn-group .btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.closest('button').classList.add('active');
            }
        }
        
        function centerOnProperty() {
            if (map) {
                const lat = <?php echo $property['latitude'] ?? 44.6488; ?>;
                const lng = <?php echo $property['longitude'] ?? -63.5752; ?>;
                
                map.setCenter({ lat: lat, lng: lng });
                map.setZoom(18);
                
                // Animate to center
                map.panTo({ lat: lat, lng: lng });
            }
        }
        
        // Update zoom level display
        function updateZoomDisplay() {
            if (map) {
                google.maps.event.addListener(map, 'zoom_changed', function() {
                    document.getElementById('current-zoom').textContent = map.getZoom();
                });
            }
        }
        
        // Initialize map when page loads
        google.maps.event.addDomListener(window, 'load', function() {
            initMap();
            setTimeout(updateZoomDisplay, 1000); // Allow map to initialize
        });
        
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