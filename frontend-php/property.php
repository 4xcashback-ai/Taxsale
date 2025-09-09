<?php
session_start();
require_once 'config/database.php';

$assessment_number = $_GET['assessment'] ?? $_GET['id'] ?? '';

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
    // Allow viewing inactive properties without login
    if ($property['status'] !== 'active') {
        // Allow access to inactive properties for preview
        $show_limited_view = true;
    } else {
        // Redirect to login for active property details
        header('Location: login.php?redirect=' . urlencode($_SERVER['REQUEST_URI']));
        exit;
    }
}

if ($property['status'] === 'active' && !$is_paid_user) {
    // Show upgrade modal for active properties
    $show_upgrade_modal = true;
}

// Get PVSC property details
$pvsc_data = null;
$pvsc_error = null;

if ($property['assessment_number']) {
    // Call backend API to get PVSC property details
    $api_url = API_BASE_URL . '/pvsc-data/' . $property['assessment_number'];
    
    // Add debug logging for admin users
    $debug_mode = isset($_SESSION['is_admin']) && $_SESSION['is_admin'];
    
    if ($debug_mode) {
        error_log("PVSC DEBUG: Calling API URL: $api_url");
    }
    
    $context = stream_context_create([
        'http' => [
            'timeout' => 15,
            'ignore_errors' => true,
            'method' => 'GET',
            'header' => [
                'User-Agent: Tax-Sale-Compass-Frontend/1.0',
                'Accept: application/json'
            ]
        ]
    ]);
    
    $response = @file_get_contents($api_url, false, $context);
    
    if ($debug_mode) {
        error_log("PVSC DEBUG: Response received: " . ($response ? 'Yes' : 'No'));
        if ($response) {
            error_log("PVSC DEBUG: Response content: " . substr($response, 0, 200));
        }
    }
    
    if ($response) {
        $pvsc_data = json_decode($response, true);
        
        // Check for API errors
        if (isset($pvsc_data['error'])) {
            $pvsc_error = $pvsc_data['error'];
            $pvsc_data = null;
            if ($debug_mode) {
                error_log("PVSC DEBUG: API returned error: $pvsc_error");
            }
        } else if (is_array($pvsc_data) && !empty($pvsc_data)) {
            if ($debug_mode) {
                error_log("PVSC DEBUG: Successfully loaded PVSC data with " . count($pvsc_data) . " fields");
            }
        }
    } else {
        $pvsc_error = "Failed to connect to backend API";
        if ($debug_mode) {
            error_log("PVSC DEBUG: Failed to get response from API");
        }
    }
    
    // Fallback: Try to get data directly from database if API fails
    if (!$pvsc_data && !$pvsc_error) {
        try {
            $stmt = $db->prepare("SELECT * FROM pvsc_data WHERE assessment_number = ?");
            $stmt->execute([$property['assessment_number']]);
            $db_pvsc_data = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if ($db_pvsc_data) {
                // Convert database row to expected format
                $pvsc_data = $db_pvsc_data;
                if ($debug_mode) {
                    error_log("PVSC DEBUG: Loaded data directly from database as fallback");
                }
            } else {
                $pvsc_error = "No PVSC data found in database";
                if ($debug_mode) {
                    error_log("PVSC DEBUG: No data found in database for assessment " . $property['assessment_number']);
                }
            }
        } catch (Exception $e) {
            $pvsc_error = "Database error: " . $e->getMessage();
            if ($debug_mode) {
                error_log("PVSC DEBUG: Database fallback failed: " . $e->getMessage());
            }
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Property <?php echo htmlspecialchars($assessment_number); ?> - <?php echo SITE_NAME; ?></title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://maps.googleapis.com/maps/api/js?key=<?php echo GOOGLE_MAPS_API_KEY; ?>&libraries=geometry"></script>
    
    <!-- Google AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5947395928510215"
         crossorigin="anonymous"></script>
    <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --success-color: #00d4aa;
            --warning-color: #ff8f00;
            --danger-color: #ff5252;
        }
        
        body {
            background: #f8f9fa;
            min-height: 100vh;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .container-fluid {
            padding: 2rem 1rem;
        }
        
        .property-header {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .property-title {
            color: var(--primary-color);
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .property-address {
            color: #6c757d;
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }
        
        .status-badge {
            font-size: 0.9rem;
            font-weight: 600;
            padding: 0.5rem 1rem;
            border-radius: 20px;
        }
        
        .card {
            border: none;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            overflow: hidden;
        }
        
        .card-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            padding: 1.5rem 2rem;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .card-body {
            padding: 2rem;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .info-item {
            background: #f8f9ff;
            padding: 1.5rem;
            border-radius: 15px;
            border-left: 4px solid var(--primary-color);
        }
        
        .info-label {
            font-weight: 600;
            color: var(--primary-color);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
        
        .info-value {
            font-size: 1.1rem;
            color: #2d3748;
            font-weight: 500;
        }
        
        .map-container {
            height: 500px;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }
        
        .map-controls {
            position: absolute;
            top: 15px;
            right: 15px;
            z-index: 1000;
            background: white;
            border-radius: 10px;
            padding: 0.5rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .btn-map-control {
            border: none;
            background: none;
            padding: 0.5rem;
            margin: 0 0.2rem;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        
        .btn-map-control:hover, .btn-map-control.active {
            background: var(--primary-color);
            color: white;
        }
        
        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
        }
        
        .back-button {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border: none;
            border-radius: 15px;
            padding: 0.75rem 1.5rem;
            color: white;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .back-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            color: white;
            text-decoration: none;
        }
        
        .psc-data {
            background: linear-gradient(135deg, #e8f5e8, #f0f8f0);
            border-left: 4px solid var(--success-color);
        }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .property-type-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: capitalize;
        }
        
        .property-type-apartment { background: #e1f5fe; color: #0277bd; }
        .property-type-regular { background: #f3e5f5; color: #7b1fa2; }
        .property-type-land { background: #e8f5e8; color: #388e3c; }
        .property-type-mixed { background: #fff3e0; color: #f57c00; }
        .property-type-mobile_home_only { background: #fce4ec; color: #c2185b; }
        
        .ad-container-detail {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 0.5rem;
            min-height: 250px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .ad-container-detail::before {
            content: "Advertisement";
            position: absolute;
            top: 5px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.7rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
        <div class="container">
            <a class="navbar-brand text-primary" href="search.php">
                <i class="fas fa-compass me-2"></i><?php echo SITE_NAME; ?>
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="back-button" href="search.php">
                            <i class="fas fa-arrow-left"></i> Back to Search
                        </a>
                    </li>
                    <?php if (isset($_SESSION['user_id'])): ?>
                        <li class="nav-item ms-3">
                            <a class="nav-link" href="favorites.php">
                                <i class="fas fa-heart me-1"></i>Favorites
                            </a>
                        </li>
                        <?php if ($_SESSION['is_admin'] ?? false): ?>
                            <li class="nav-item">
                                <a class="nav-link" href="admin.php">
                                    <i class="fas fa-cog me-1"></i>Admin
                                </a>
                            </li>
                        <?php endif; ?>
                        <li class="nav-item">
                            <a class="nav-link" href="logout.php">
                                <i class="fas fa-sign-out-alt me-1"></i>Logout
                            </a>
                        </li>
                    <?php endif; ?>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container-fluid">
        <!-- Property Header -->
        <div class="property-header">
            <div class="row align-items-center">
                <div class="col-lg-8">
                    <h1 class="property-title">
                        <i class="fas fa-home me-2"></i>
                        Property #<?php echo htmlspecialchars($assessment_number); ?>
                    </h1>
                    <div class="property-address">
                        <i class="fas fa-map-marker-alt me-2"></i>
                        <?php echo htmlspecialchars($property['civic_address'] ?? 'Address Not Available'); ?>
                    </div>
                    <div class="d-flex gap-2 flex-wrap">
                        <span class="status-badge bg-<?php echo $property['status'] === 'active' ? 'success' : 'secondary'; ?>">
                            <i class="fas fa-<?php echo $property['status'] === 'active' ? 'check-circle' : 'clock'; ?> me-1"></i>
                            <?php echo ucfirst($property['status'] ?? 'Unknown'); ?>
                        </span>
                        <?php if ($property['property_type']): ?>
                        <span class="property-type-badge property-type-<?php echo $property['property_type']; ?>">
                            <i class="fas fa-tag me-1"></i>
                            <?php echo ucfirst(str_replace('_', ' ', $property['property_type'])); ?>
                        </span>
                        <?php endif; ?>
                        <?php if ($property['municipality']): ?>
                        <span class="badge bg-info">
                            <i class="fas fa-city me-1"></i>
                            <?php echo htmlspecialchars($property['municipality']); ?>
                        </span>
                        <?php endif; ?>
                    </div>
                </div>
                <div class="col-lg-4 text-lg-end mt-3 mt-lg-0">
                    <?php if ($property['opening_bid'] || $property['total_taxes']): ?>
                    <div class="text-end">
                        <?php if ($property['opening_bid']): ?>
                        <div class="mb-2">
                            <small class="text-muted">Opening Bid</small>
                            <div class="h4 text-success mb-0">
                                <i class="fas fa-gavel me-1"></i>
                                $<?php echo number_format($property['opening_bid'], 2); ?>
                            </div>
                        </div>
                        <?php endif; ?>
                        <?php if ($property['total_taxes']): ?>
                        <div>
                            <small class="text-muted">Total Taxes Due</small>
                            <div class="h5 text-danger mb-0">
                                <i class="fas fa-receipt me-1"></i>
                                $<?php echo number_format($property['total_taxes'], 2); ?>
                            </div>
                        </div>
                        <?php endif; ?>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Left Column: Map + Property Info + PVSC Data -->
            <div class="col-lg-8">
                <!-- Interactive Property Map -->
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-map-marked-alt me-2"></i>Interactive Property Map
                    </div>
                    <div class="card-body p-0">
                        <div class="map-container">
                            <div id="property-map" class="w-100 h-100"></div>
                            <div class="map-controls">
                                <button type="button" class="btn-map-control active" onclick="toggleMapType('satellite')" title="Satellite View" data-type="satellite">
                                    <i class="fas fa-satellite"></i>
                                </button>
                                <button type="button" class="btn-map-control" onclick="toggleMapType('roadmap')" title="Map View" data-type="roadmap">
                                    <i class="fas fa-map"></i>
                                </button>
                                <button type="button" class="btn-map-control" onclick="toggleMapType('hybrid')" title="Hybrid View" data-type="hybrid">
                                    <i class="fas fa-layer-group"></i>
                                </button>
                                <button type="button" class="btn-map-control" onclick="centerOnProperty()" title="Center on Property">
                                    <i class="fas fa-crosshairs"></i>
                                </button>
                            </div>
                        </div>
                        <div class="p-3 bg-light border-top">
                            <div class="row text-center">
                                <div class="col-md-3">
                                    <small class="text-muted d-block">Coordinates</small>
                                    <small class="fw-bold"><?php echo number_format($property['latitude'] ?? 44.6488, 6); ?>, <?php echo number_format($property['longitude'] ?? -63.5752, 6); ?></small>
                                </div>
                                <div class="col-md-3">
                                    <small class="text-muted d-block">Boundary Data</small>
                                    <small class="fw-bold"><?php echo $property['boundary_data'] ? '✅ Available' : '📍 Coordinates Only'; ?></small>
                                </div>
                                <div class="col-md-3">
                                    <small class="text-muted d-block">Property Type</small>
                                    <small class="fw-bold"><?php echo htmlspecialchars(ucfirst(str_replace('_', ' ', $property['property_type'] ?? 'Unknown'))); ?></small>
                                </div>
                                <div class="col-md-3">
                                    <small class="text-muted d-block">Municipality</small>
                                    <small class="fw-bold"><?php echo htmlspecialchars($property['municipality'] ?? 'N/A'); ?></small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Basic Property Information -->
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-info-circle me-2"></i>Property Information
                    </div>
                    <div class="card-body">
                        <div class="info-grid">
                            <?php if ($property['pid_number']): ?>
                            <div class="info-item">
                                <div class="info-label">
                                    <i class="fas fa-fingerprint me-1"></i>PID Number
                                </div>
                                <div class="info-value">
                                    <?php echo htmlspecialchars($property['pid_number']); ?>
                                </div>
                            </div>
                            <?php endif; ?>
                            
                            <?php if ($property['tax_year']): ?>
                            <div class="info-item">
                                <div class="info-label">
                                    <i class="fas fa-calendar me-1"></i>Tax Year
                                </div>
                                <div class="info-value">
                                    <?php echo htmlspecialchars($property['tax_year']); ?>
                                </div>
                            </div>
                            <?php endif; ?>
                            
                            <?php if ($property['pvsc_assessment_value']): ?>
                            <div class="info-item">
                                <div class="info-label">
                                    <i class="fas fa-calculator me-1"></i>PVSC Assessment
                                </div>
                                <div class="info-value">
                                    $<?php echo number_format($property['pvsc_assessment_value'], 2); ?>
                                    <?php if ($property['pvsc_assessment_year']): ?>
                                    <small class="text-muted">(<?php echo $property['pvsc_assessment_year']; ?>)</small>
                                    <?php endif; ?>
                                </div>
                            </div>
                            <?php endif; ?>
                            

                            
                            <?php if ($property['sale_date']): ?>
                            <div class="info-item">
                                <div class="info-label">
                                    <i class="fas fa-calendar-alt me-1"></i>Tax Sale Date
                                </div>
                                <div class="info-value text-warning">
                                    <?php echo date('F j, Y', strtotime($property['sale_date'])); ?>
                                </div>
                                <div class="mt-2">
                                    <div id="countdown-<?php echo $assessment_number; ?>" class="badge bg-warning text-dark fs-6 p-2">
                                        <i class="fas fa-clock me-1"></i>
                                        <span id="countdown-text-<?php echo $assessment_number; ?>">Loading...</span>
                                    </div>
                                </div>
                            </div>
                            <?php endif; ?>
                            
                            <?php if ($property['auction_type']): ?>
                            <div class="info-item">
                                <div class="info-label">
                                    <i class="fas fa-hammer me-1"></i>Auction Type
                                </div>
                                <div class="info-value">
                                    <?php echo htmlspecialchars($property['auction_type']); ?>
                                </div>
                            </div>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>

                <!-- PVSC Property Data Table -->
                <?php if ($pvsc_data && !empty($pvsc_data) && !isset($pvsc_data['error'])): ?>
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-database me-2"></i>PVSC Property Data
                        <small class="badge bg-success ms-2"><?php echo isset($pvsc_data['scraped_at']) ? 'Cached' : 'Live'; ?></small>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <!-- Left Column -->
                            <div class="col-md-6">
                                <?php if (isset($pvsc_data['assessed_value']) && $pvsc_data['assessed_value']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-calculator me-1"></i>Assessed Value
                                    </div>
                                    <div class="info-value text-success fw-bold">$<?php echo number_format($pvsc_data['assessed_value'], 2); ?></div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['land_size']) && $pvsc_data['land_size']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-ruler-combined me-1"></i>Land Size
                                    </div>
                                    <div class="info-value">
                                        <?php echo number_format($pvsc_data['land_size'], 2); ?>
                                        <?php if (isset($pvsc_data['land_size_unit'])): ?>
                                            <?php echo htmlspecialchars($pvsc_data['land_size_unit']); ?>
                                        <?php endif; ?>
                                    </div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['year_built']) && $pvsc_data['year_built']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-calendar-alt me-1"></i>Year Built
                                    </div>
                                    <div class="info-value"><?php echo htmlspecialchars($pvsc_data['year_built']); ?></div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['number_of_bedrooms']) && $pvsc_data['number_of_bedrooms']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-bed me-1"></i>Bedrooms
                                    </div>
                                    <div class="info-value"><?php echo htmlspecialchars($pvsc_data['number_of_bedrooms']); ?></div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['basement_type']) && $pvsc_data['basement_type']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-layer-group me-1"></i>Basement
                                    </div>
                                    <div class="info-value">
                                        <span class="badge bg-<?php echo $pvsc_data['basement_type'] === 'Finished' ? 'success' : 'secondary'; ?>">
                                            <?php echo htmlspecialchars($pvsc_data['basement_type']); ?>
                                        </span>
                                    </div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['construction_quality']) && $pvsc_data['construction_quality']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-hammer me-1"></i>Construction Quality
                                    </div>
                                    <div class="info-value"><?php echo htmlspecialchars($pvsc_data['construction_quality']); ?></div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['last_sale_date']) && $pvsc_data['last_sale_date']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-handshake me-1"></i>Last Sale Date
                                    </div>
                                    <div class="info-value text-warning"><?php echo date('M j, Y', strtotime($pvsc_data['last_sale_date'])); ?></div>
                                </div>
                                <?php endif; ?>
                            </div>
                            
                            <!-- Right Column -->
                            <div class="col-md-6">
                                <?php if (isset($pvsc_data['taxable_assessed_value']) && $pvsc_data['taxable_assessed_value']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-receipt me-1"></i>Taxable Assessed Value
                                    </div>
                                    <div class="info-value text-info fw-bold">$<?php echo number_format($pvsc_data['taxable_assessed_value'], 2); ?></div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['building_size']) && $pvsc_data['building_size']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-building me-1"></i>Building Size
                                    </div>
                                    <div class="info-value">
                                        <?php echo number_format($pvsc_data['building_size'], 0); ?>
                                        <?php if (isset($pvsc_data['building_size_unit'])): ?>
                                            <?php echo htmlspecialchars($pvsc_data['building_size_unit']); ?>
                                        <?php endif; ?>
                                    </div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['building_style']) && $pvsc_data['building_style']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-home me-1"></i>Building Style
                                    </div>
                                    <div class="info-value"><?php echo htmlspecialchars($pvsc_data['building_style']); ?></div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['number_of_bathrooms']) && $pvsc_data['number_of_bathrooms']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-bath me-1"></i>Bathrooms
                                    </div>
                                    <div class="info-value"><?php echo htmlspecialchars($pvsc_data['number_of_bathrooms']); ?></div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['garage']) && $pvsc_data['garage']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-car me-1"></i>Garage
                                    </div>
                                    <div class="info-value">
                                        <span class="badge bg-<?php echo $pvsc_data['garage'] === 'Yes' ? 'success' : 'secondary'; ?>">
                                            <?php echo htmlspecialchars($pvsc_data['garage']); ?>
                                        </span>
                                    </div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['living_units']) && $pvsc_data['living_units']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-door-open me-1"></i>Living Units
                                    </div>
                                    <div class="info-value"><?php echo htmlspecialchars($pvsc_data['living_units']); ?></div>
                                </div>
                                <?php endif; ?>
                                
                                <?php if (isset($pvsc_data['last_sale_price']) && $pvsc_data['last_sale_price']): ?>
                                <div class="info-item mb-3">
                                    <div class="info-label">
                                        <i class="fas fa-dollar-sign me-1"></i>Last Sale Price
                                    </div>
                                    <div class="info-value text-warning fw-bold">$<?php echo number_format($pvsc_data['last_sale_price'], 2); ?></div>
                                </div>
                                <?php endif; ?>
                            </div>
                        </div>
                        <div class="card-footer bg-light">
                            <small class="text-muted">
                                <i class="fas fa-database me-1"></i>
                                Data from Property Valuation Services Corporation (PVSC)
                                <?php if (isset($pvsc_data['scraped_at'])): ?>
                                - Updated: <?php echo date('M j, Y', strtotime($pvsc_data['scraped_at'])); ?>
                                <?php endif; ?>
                            </small>
                        </div>
                    </div>
                </div>
                <?php else: ?>
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-database me-2"></i>PVSC Property Data
                        <?php if ($pvsc_error): ?>
                        <small class="badge bg-warning ms-2">Error</small>
                        <?php else: ?>
                        <small class="badge bg-info ms-2">No Data</small>
                        <?php endif; ?>
                    </div>
                    <div class="card-body text-center py-4">
                        <?php if ($pvsc_error): ?>
                        <div class="mb-3">
                            <i class="fas fa-exclamation-triangle fa-2x text-warning"></i>
                        </div>
                        <p class="text-muted mb-2">Unable to load PVSC data</p>
                        <small class="text-warning">
                            <?php echo htmlspecialchars($pvsc_error); ?>
                        </small>
                        <?php else: ?>
                        <div class="mb-3">
                            <i class="fas fa-info-circle fa-2x text-muted"></i>
                        </div>
                        <p class="text-muted mb-2">PVSC data not available for this property</p>
                        <small class="text-info">
                            This property may not have detailed assessment information available
                        </small>
                        <?php endif; ?>
                        
                        <div class="mt-3">
                            <button class="btn btn-sm btn-outline-primary" onclick="location.reload()">
                                <i class="fas fa-sync-alt me-1"></i>Retry Loading
                            </button>
                        </div>
                    </div>
                </div>
                <?php endif; ?>
            </div>
            
            <!-- Right Column: Minimum Bid + Actions + Stats -->
            <div class="col-lg-4">
                <!-- Minimum Bid - Prominently at Top -->
                <?php if ($property['opening_bid'] || $property['total_taxes']): ?>
                <div class="card mb-3" style="border: 2px solid var(--success-color);">
                    <div class="card-header text-center" style="background: linear-gradient(135deg, var(--success-color), #00b894); color: white;">
                        <h4 class="mb-0">
                            <i class="fas fa-gavel me-2"></i>Minimum Bid
                        </h4>
                    </div>
                    <div class="card-body text-center">
                        <?php if ($property['opening_bid']): ?>
                        <div class="display-4 text-success fw-bold mb-2">
                            $<?php echo number_format($property['opening_bid'], 2); ?>
                        </div>
                        <div class="text-muted mb-3">Opening Bid Amount</div>
                        <?php endif; ?>
                        
                        <!-- Assessed Value from PVSC -->
                        <?php if (isset($pvsc_data['assessed_value']) && $pvsc_data['assessed_value']): ?>
                        <div class="border-top pt-3">
                            <div class="h5 text-info mb-1">
                                $<?php echo number_format($pvsc_data['assessed_value'], 2); ?>
                            </div>
                            <small class="text-muted">Assessed Value</small>
                        </div>
                        <?php endif; ?>
                        
                        <!-- Potential Profit Calculation -->
                        <?php if ($property['opening_bid'] && isset($pvsc_data['assessed_value']) && $pvsc_data['assessed_value']): ?>
                        <?php 
                            $potential_profit = $pvsc_data['assessed_value'] - $property['opening_bid']; 
                            $is_profit = $potential_profit > 0;
                        ?>
                        <div class="border-top pt-3 mt-3">
                            <div class="h5 text-<?php echo $is_profit ? 'success' : 'danger'; ?> mb-1">
                                <?php echo $is_profit ? '+' : ''; ?>$<?php echo number_format($potential_profit, 2); ?>
                            </div>
                            <small class="text-muted">
                                Potential <?php echo $is_profit ? 'Profit' : 'Loss'; ?>
                                <small class="d-block">(Assessed Value - Min Bid)</small>
                            </small>
                        </div>
                        <?php endif; ?>
                        
                        <?php if ($property['opening_bid'] && $property['total_taxes']): ?>
                        <div class="mt-3 pt-3 border-top">
                            <?php $percentage = ($property['opening_bid'] / $property['total_taxes']) * 100; ?>
                            <div class="progress mb-2" style="height: 8px;">
                                <div class="progress-bar bg-success" style="width: <?php echo min($percentage, 100); ?>%"></div>
                            </div>
                            <small class="text-muted">
                                Bid is <?php echo number_format($percentage, 1); ?>% of taxes due
                            </small>
                        </div>
                        <?php endif; ?>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Google AdSense Ad -->
                <div class="card mb-3">
                    <div class="card-body text-center p-2">
                        <div class="ad-container-detail">
                            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5947395928510215"
                                 crossorigin="anonymous"></script>
                            <!-- detail page -->
                            <ins class="adsbygoogle"
                                 style="display:block"
                                 data-ad-client="ca-pub-5947395928510215"
                                 data-ad-slot="3653544552"
                                 data-ad-format="auto"
                                 data-full-width-responsive="true"></ins>
                            <script>
                                 (adsbygoogle = window.adsbygoogle || []).push({});
                            </script>
                        </div>
                    </div>
                </div>

                <!-- Property Actions -->
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-tools me-2"></i>Property Actions
                    </div>
                    <div class="card-body">
                        <?php if ($is_logged_in): ?>
                        <div class="d-grid gap-2">
                            <button class="btn btn-outline-danger" onclick="addToFavorites()">
                                <i class="fas fa-heart me-2"></i>Add to Favorites
                            </button>
                            <button class="btn btn-outline-info" onclick="shareProperty()">
                                <i class="fas fa-share-alt me-2"></i>Share Property
                            </button>
                            <button class="btn btn-outline-success" onclick="downloadDetails()">
                                <i class="fas fa-download me-2"></i>Download Details
                            </button>
                        </div>
                        <?php endif; ?>
                        
                        <div class="mt-4 pt-3 border-top">
                            <small class="text-muted d-block mb-2">
                                <i class="fas fa-clock me-1"></i>Last updated: 
                                <?php echo date('M j, Y \a\t g:i A', strtotime($property['updated_at'] ?? $property['created_at'])); ?>
                            </small>
                            <?php if ($property['boundary_data']): ?>
                            <small class="text-success d-block">
                                <i class="fas fa-check-circle me-1"></i>Boundary data available
                            </small>
                            <?php else: ?>
                            <small class="text-warning d-block">
                                <i class="fas fa-info-circle me-1"></i>Location based on address geocoding
                            </small>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>

                <!-- Quick Stats -->
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-chart-bar me-2"></i>Quick Stats
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <?php if ($property['tax_year']): ?>
                            <div class="col-6 mb-3">
                                <div class="text-primary h4 mb-0"><?php echo $property['tax_year']; ?></div>
                                <small class="text-muted">Tax Year</small>
                            </div>
                            <?php endif; ?>
                            
                            <?php if ($property['pvsc_assessment_year']): ?>
                            <div class="col-6 mb-3">
                                <div class="text-info h4 mb-0"><?php echo $property['pvsc_assessment_year']; ?></div>
                                <small class="text-muted">Assessment Year</small>
                            </div>
                            <?php endif; ?>
                        </div>
                        
                        <?php if (isset($pvsc_data['assessed_value']) && isset($pvsc_data['taxable_assessed_value']) && $pvsc_data['assessed_value'] && $pvsc_data['taxable_assessed_value']): ?>
                        <div class="border-top pt-3">
                            <?php $cap_percentage = ($pvsc_data['taxable_assessed_value'] / $pvsc_data['assessed_value']) * 100; ?>
                            <div class="progress mb-2" style="height: 8px;">
                                <div class="progress-bar bg-info" style="width: <?php echo $cap_percentage; ?>%"></div>
                            </div>
                            <small class="text-muted">
                                Taxable value is <?php echo number_format($cap_percentage, 1); ?>% of assessed value
                            </small>
                        </div>
                        <?php endif; ?>
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
        // Enhanced Google Maps Integration
        let map;
        
        function initMap() {
            const lat = <?php echo $property['latitude'] ?? 44.6488; ?>;
            const lng = <?php echo $property['longitude'] ?? -63.5752; ?>;
            
            // Enhanced map configuration with satellite view
            map = new google.maps.Map(document.getElementById("property-map"), {
                zoom: 17,
                center: { lat: lat, lng: lng },
                mapTypeId: google.maps.MapTypeId.SATELLITE,
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
            
            // Add custom marker for property location
            const marker = new google.maps.Marker({
                position: { lat: lat, lng: lng },
                map: map,
                title: "Property <?php echo htmlspecialchars($assessment_number); ?>",
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 10,
                    fillColor: "#FF4444",
                    fillOpacity: 0.9,
                    strokeColor: "#FFFFFF",
                    strokeWeight: 3
                },
                animation: google.maps.Animation.DROP
            });
            
            // Add info window with property details
            const infoWindow = new google.maps.InfoWindow({
                content: `
                    <div style="max-width: 300px;">
                        <h6 class="fw-bold text-primary mb-2">
                            <i class="fas fa-home me-1"></i>Property <?php echo htmlspecialchars($assessment_number); ?>
                        </h6>
                        <div class="small">
                            <div class="mb-1">
                                <i class="fas fa-map-marker-alt text-danger me-1"></i>
                                <?php echo htmlspecialchars($property['civic_address'] ?? 'Address not available'); ?>
                            </div>
                            <?php if ($property['municipality']): ?>
                            <div class="mb-1">
                                <i class="fas fa-city text-info me-1"></i>
                                <?php echo htmlspecialchars($property['municipality']); ?>
                            </div>
                            <?php endif; ?>
                            <?php if ($property['property_type']): ?>
                            <div class="mb-1">
                                <i class="fas fa-tag text-success me-1"></i>
                                <?php echo htmlspecialchars(ucfirst(str_replace('_', ' ', $property['property_type']))); ?>
                            </div>
                            <?php endif; ?>
                            <?php if ($property['opening_bid']): ?>
                            <div class="mb-1">
                                <i class="fas fa-gavel text-warning me-1"></i>
                                Opening Bid: $<?php echo number_format($property['opening_bid'], 2); ?>
                            </div>
                            <?php endif; ?>
                            <div class="text-muted mt-2">
                                <small>Coordinates: ${lat.toFixed(6)}, ${lng.toFixed(6)}</small>
                            </div>
                        </div>
                    </div>
                `
            });
            
            marker.addListener("click", () => {
                infoWindow.open(map, marker);
            });
            
            // Show info window by default after a short delay
            setTimeout(() => {
                infoWindow.open(map, marker);
            }, 1000);
            
            <?php if ($property['boundary_data']): ?>
            // Add property boundary if available
            try {
                const boundaryData = <?php echo $property['boundary_data']; ?>;
                console.log("Boundary data structure:", boundaryData);
                
                let boundaries = null;
                
                // Handle different boundary data formats
                if (boundaryData && boundaryData.coordinates) {
                    // GeoJSON format
                    boundaries = boundaryData.coordinates[0].map(coord => ({
                        lat: coord[1],
                        lng: coord[0]
                    }));
                } else if (boundaryData && boundaryData.rings) {
                    // ArcGIS format
                    boundaries = boundaryData.rings[0].map(coord => ({
                        lat: coord[1],
                        lng: coord[0]
                    }));
                } else if (Array.isArray(boundaryData)) {
                    // Direct coordinate array
                    boundaries = boundaryData.map(coord => ({
                        lat: Array.isArray(coord) ? coord[1] : coord.lat,
                        lng: Array.isArray(coord) ? coord[0] : coord.lng
                    }));
                }
                
                if (boundaries && boundaries.length > 0) {
                    console.log("Rendering boundaries with", boundaries.length, "points");
                    
                    const propertyPolygon = new google.maps.Polygon({
                        paths: boundaries,
                        strokeColor: "#FF6B35",
                        strokeOpacity: 0.9,
                        strokeWeight: 3,
                        fillColor: "#FF6B35",
                        fillOpacity: 0.2,
                        map: map,
                        clickable: true
                    });
                    
                    const boundaryInfoWindow = new google.maps.InfoWindow({
                        content: `
                            <div>
                                <h6><strong>Property Boundary</strong></h6>
                                <p>Assessment: <?php echo htmlspecialchars($assessment_number); ?></p>
                                <p>Boundary as recorded in government records</p>
                                <p><small>${boundaries.length} boundary points</small></p>
                            </div>
                        `
                    });
                    
                    propertyPolygon.addListener("click", (event) => {
                        boundaryInfoWindow.setPosition(event.latLng);
                        boundaryInfoWindow.open(map);
                    });
                    
                    // Fit map to show entire property boundary
                    const bounds = new google.maps.LatLngBounds();
                    boundaries.forEach(point => bounds.extend(point));
                    
                    // Add some padding around the boundary
                    const extendedBounds = new google.maps.LatLngBounds(
                        new google.maps.LatLng(bounds.getSouthWest().lat() - 0.0005, bounds.getSouthWest().lng() - 0.0005),
                        new google.maps.LatLng(bounds.getNorthEast().lat() + 0.0005, bounds.getNorthEast().lng() + 0.0005)
                    );
                    
                    map.fitBounds(extendedBounds);
                    
                    google.maps.event.addListenerOnce(map, 'bounds_changed', function() {
                        if (map.getZoom() > 19) {
                            map.setZoom(19);
                        }
                    });
                    
                    console.log("✅ Property boundary rendered successfully");
                } else {
                    console.log("⚠️ No valid boundary coordinates found");
                }
                
            } catch (e) {
                console.error("❌ Error rendering boundary data:", e);
                console.log("Raw boundary data:", <?php echo json_encode($property['boundary_data']); ?>);
            }
            <?php else: ?>
            // No boundary data - just center on coordinates with appropriate zoom
            console.log("No boundary data available for this property");
            map.setZoom(17);
            <?php endif; ?>
            
            // Add map legend
            const legend = document.createElement('div');
            legend.style.backgroundColor = 'white';
            legend.style.border = '2px solid #ccc';
            legend.style.borderRadius = '8px';
            legend.style.margin = '10px';
            legend.style.padding = '12px';
            legend.style.fontSize = '12px';
            legend.style.fontFamily = 'Arial, sans-serif';
            legend.style.boxShadow = '0 2px 6px rgba(0,0,0,0.3)';
            legend.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 8px; color: #333;">Property Map Legend</div>
                <div style="margin-bottom: 4px;">
                    <span style="display: inline-block; width: 12px; height: 12px; background-color: #FF4444; border-radius: 50%; margin-right: 8px;"></span>
                    Property Location
                </div>
                <?php if ($property['boundary_data']): ?>
                <div>
                    <span style="display: inline-block; width: 12px; height: 12px; background-color: #FF6B35; opacity: 0.5; margin-right: 8px;"></span>
                    Property Boundary
                </div>
                <?php endif; ?>
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
                
                // Update button states
                document.querySelectorAll('.btn-map-control[data-type]').forEach(btn => {
                    btn.classList.remove('active');
                });
                const targetBtn = document.querySelector(`[data-type="${type}"]`);
                if (targetBtn) {
                    targetBtn.classList.add('active');
                }
            }
        }
        
        function centerOnProperty() {
            if (map) {
                const lat = <?php echo $property['latitude'] ?? 44.6488; ?>;
                const lng = <?php echo $property['longitude'] ?? -63.5752; ?>;
                
                map.setCenter({ lat: lat, lng: lng });
                map.setZoom(18);
                
                // Add a subtle animation
                setTimeout(() => {
                    map.setZoom(17);
                }, 1000);
            }
        }
        
        // Property action functions
        function addToFavorites() {
            fetch('/api/favorites.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    assessment_number: '<?php echo htmlspecialchars($assessment_number); ?>'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Added to favorites!');
                } else {
                    alert('Error: ' + (data.message || 'Unable to add to favorites'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error adding to favorites. Please try again.');
            });
        }
        
        function shareProperty() {
            if (navigator.share) {
                navigator.share({
                    title: 'Property <?php echo htmlspecialchars($assessment_number); ?>',
                    text: 'Check out this tax sale property: <?php echo htmlspecialchars($property['civic_address'] ?? ''); ?>',
                    url: window.location.href
                });
            } else {
                // Fallback: copy to clipboard
                navigator.clipboard.writeText(window.location.href).then(() => {
                    alert('Property link copied to clipboard!');
                }).catch(() => {
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = window.location.href;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    alert('Property link copied to clipboard!');
                });
            }
        }
        
        function downloadDetails() {
            // Create a simple property details text file
            const propertyDetails = `
Tax Sale Property Details

Assessment Number: <?php echo htmlspecialchars($assessment_number); ?>
Address: <?php echo htmlspecialchars($property['civic_address'] ?? 'N/A'); ?>
Municipality: <?php echo htmlspecialchars($property['municipality'] ?? 'N/A'); ?>
Property Type: <?php echo htmlspecialchars($property['property_type'] ?? 'N/A'); ?>
<?php if ($property['opening_bid']): ?>
Opening Bid: $<?php echo number_format($property['opening_bid'], 2); ?>
<?php endif; ?>
<?php if ($property['total_taxes']): ?>
Total Taxes Due: $<?php echo number_format($property['total_taxes'], 2); ?>
<?php endif; ?>
Tax Year: <?php echo htmlspecialchars($property['tax_year'] ?? 'N/A'); ?>
Status: <?php echo htmlspecialchars($property['status'] ?? 'N/A'); ?>

Coordinates: <?php echo number_format($property['latitude'] ?? 44.6488, 6); ?>, <?php echo number_format($property['longitude'] ?? -63.5752, 6); ?>

Downloaded from: ${window.location.href}
Downloaded on: ${new Date().toLocaleString()}
            `.trim();
            
            const blob = new Blob([propertyDetails], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `property_${<?php echo json_encode($assessment_number); ?>}_details.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
        
        // Countdown Timer Function
        function updateCountdown() {
            <?php if ($property['sale_date']): ?>
            const saleDate = new Date('<?php echo date('c', strtotime($property['sale_date'])); ?>');
            const now = new Date();
            const timeDiff = saleDate.getTime() - now.getTime();
            
            const countdownElement = document.getElementById('countdown-text-<?php echo $assessment_number; ?>');
            
            if (timeDiff > 0) {
                const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
                const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                
                if (days > 0) {
                    countdownElement.textContent = `${days} days ${hours} hours`;
                } else if (hours > 0) {
                    countdownElement.textContent = `${hours} hours remaining`;
                } else {
                    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
                    countdownElement.textContent = `${minutes} minutes remaining`;
                }
                
                // Update countdown color based on time remaining
                const countdownContainer = document.getElementById('countdown-<?php echo $assessment_number; ?>');
                if (days < 7) {
                    countdownContainer.classList.remove('bg-warning');
                    countdownContainer.classList.add('bg-danger', 'text-white');
                } else if (days < 30) {
                    countdownContainer.classList.remove('bg-warning');
                    countdownContainer.classList.add('bg-warning', 'text-dark');
                } else {
                    countdownContainer.classList.add('bg-success', 'text-white');
                }
            } else {
                countdownElement.textContent = 'Auction has ended';
                const countdownContainer = document.getElementById('countdown-<?php echo $assessment_number; ?>');
                countdownContainer.classList.remove('bg-warning');
                countdownContainer.classList.add('bg-secondary', 'text-white');
            }
            <?php endif; ?>
        }
        
        // Initialize map when page loads
        window.onload = function() {
            if (typeof google !== 'undefined' && google.maps) {
                initMap();
            } else {
                console.error('Google Maps API not loaded');
            }
            
            // Initialize countdown
            <?php if ($property['sale_date']): ?>
            updateCountdown();
            // Update countdown every minute
            setInterval(updateCountdown, 60000);
            <?php endif; ?>
        };
        
        // Show upgrade modal if needed
        <?php if (isset($show_upgrade_modal)): ?>
        document.addEventListener('DOMContentLoaded', function() {
            const upgradeModal = new bootstrap.Modal(document.getElementById('upgradeModal'));
            upgradeModal.show();
        });
        <?php endif; ?>
    </script>
</body>
</html>