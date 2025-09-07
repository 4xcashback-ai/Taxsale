<?php
session_start();
require_once 'config/database.php';
require_once 'includes/thumbnail_generator.php';

// Check if user is logged in
$is_logged_in = isset($_SESSION['user_id']) && isset($_SESSION['access_token']);

// If user is not logged in, show landing page content
if (!$is_logged_in) {
    require_once 'landing.php';
    exit;
}

// Initialize database and ensure thumbnail_path column exists
$db = getDB();

// Check if thumbnail_path column exists, add it if not
try {
    $stmt = $db->query("SHOW COLUMNS FROM properties LIKE 'thumbnail_path'");
    if ($stmt->rowCount() === 0) {
        error_log("Adding thumbnail_path column to properties table");
        $db->exec("ALTER TABLE properties ADD COLUMN thumbnail_path VARCHAR(255) DEFAULT NULL");
        $db->exec("CREATE INDEX idx_properties_thumbnail ON properties (pid_number, thumbnail_path)");
    }
} catch (Exception $e) {
    error_log("Database migration error: " . $e->getMessage());
}

// Initialize thumbnail generator
$thumbnail_generator = new ThumbnailGenerator(GOOGLE_MAPS_API_KEY);

// User is logged in, continue with search functionality
// Get search parameters
$municipality = $_GET['municipality'] ?? '';
$status = $_GET['status'] ?? '';
$search = $_GET['search'] ?? '';

// Build query - ensure we get the thumbnail_path column
$query = "SELECT *, COALESCE(thumbnail_path, '') as thumbnail_path FROM properties WHERE 1=1";
$params = [];

if ($municipality) {
    $query .= " AND municipality = ?";
    $params[] = $municipality;
}

if ($status) {
    $query .= " AND status = ?";
    $params[] = $status;
}

if ($search) {
    // Prioritize civic_address search and make it more flexible
    $query .= " AND (civic_address LIKE ? OR municipality LIKE ? OR assessment_number LIKE ?)";
    $params[] = "%$search%";
    $params[] = "%$search%";
    $params[] = "%$search%";
}

// Get pagination parameters
$page = isset($_GET['page']) ? max(1, intval($_GET['page'])) : 1;
$per_page = 24;
$offset = ($page - 1) * $per_page;

// Get total count for pagination
$count_query = "SELECT COUNT(*) FROM properties WHERE 1=1";
$count_params = [];

// Apply same filters to count query
if ($municipality) {
    $count_query .= " AND municipality = ?";
    $count_params[] = $municipality;
}

if ($status) {
    $count_query .= " AND status = ?";
    $count_params[] = $status;
}

if ($search) {
    $count_query .= " AND (civic_address LIKE ? OR municipality LIKE ? OR assessment_number LIKE ?)";
    $count_params[] = "%$search%";
    $count_params[] = "%$search%";
    $count_params[] = "%$search%";
}

$query .= " ORDER BY created_at DESC LIMIT $per_page OFFSET $offset";

$db = getDB();

// Get total count
$count_stmt = $db->prepare($count_query);
$count_stmt->execute($count_params);
$total_properties = $count_stmt->fetchColumn();
$total_pages = ceil($total_properties / $per_page);

// Get properties for current page
$stmt = $db->prepare($query);
$stmt->execute($params);
$properties = $stmt->fetchAll();

// DEBUG: Log thumbnail data for first few properties (admin only)
if (isset($_SESSION['is_admin']) && $_SESSION['is_admin']) {
    error_log("=== THUMBNAIL DEBUG INFO ===");
    foreach (array_slice($properties, 0, 3) as $property) {
        error_log("Property {$property['assessment_number']}: PID={$property['pid_number']}, thumbnail_path=" . ($property['thumbnail_path'] ?? 'NULL') . ", coords=" . ($property['latitude'] ?? 'NULL') . "," . ($property['longitude'] ?? 'NULL'));
        
        // Test getThumbnail method
        $thumbnail_url = $thumbnail_generator->getThumbnail($property);
        error_log("getThumbnail() returned: {$thumbnail_url}");
        
        // Check if file exists
        if (strpos($thumbnail_url, '/assets/thumbnails/') === 0) {
            $file_path = dirname(__DIR__) . $thumbnail_url;
            $file_exists = file_exists($file_path);
            error_log("File path: {$file_path}, exists: " . ($file_exists ? 'YES' : 'NO'));
        }
    }
    error_log("=== END THUMBNAIL DEBUG ===");
}

// Get municipalities for filter
$municipalities = $db->query("SELECT DISTINCT municipality FROM properties ORDER BY municipality")->fetchAll(PDO::FETCH_COLUMN);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo SITE_NAME; ?> - Canadian Tax Sale Properties</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://maps.googleapis.com/maps/api/js?key=<?php echo GOOGLE_MAPS_API_KEY; ?>&libraries=geometry" defer></script>
    <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --accent-color: #f093fb;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
        }
        
        body {
            background: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .search-hero {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 3rem 0;
            margin-bottom: 2rem;
        }
        
        .search-form {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-top: -3rem;
            position: relative;
            z-index: 10;
        }
        
        .search-stats {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            margin-bottom: 2rem;
        }
        
        .property-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            border: none;
            height: 100%;
        }
        
        .property-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }
        
        .property-thumbnail {
            width: 100%;
            height: 200px;
            background: #f8f9fa;
            position: relative;
            overflow: hidden;
        }
        
        .property-thumbnail img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }
        
        .property-card:hover .property-thumbnail img {
            transform: scale(1.05);
        }
        
        .thumbnail-overlay {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .property-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 1.5rem;
            position: relative;
        }
        
        .property-id {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .property-status {
            position: absolute;
            top: 1rem;
            right: 1rem;
        }
        
        .status-badge {
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .status-active {
            background: var(--success-color);
            color: white;
        }
        
        .status-inactive {
            background: #6c757d;
            color: white;
        }
        
        .status-sold {
            background: var(--danger-color);
            color: white;
        }
        
        .status-withdrawn {
            background: var(--warning-color);
            color: black;
        }
        
        .property-details {
            padding: 1.5rem;
        }
        
        .detail-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.8rem;
            padding-bottom: 0.8rem;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .detail-row:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }
        
        .detail-label {
            font-weight: 600;
            color: #666;
            display: flex;
            align-items: center;
        }
        
        .detail-value {
            font-weight: 500;
            color: #333;
        }
        
        .tax-amount {
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .btn-view-details {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 25px;
            color: white;
            font-weight: 600;
            transition: all 0.3s ease;
            width: 100%;
        }
        
        .btn-view-details:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            color: white;
        }
        
        .pagination-wrapper {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        
        .page-link {
            border-radius: 10px;
            margin: 0 0.2rem;
            border: none;
            color: var(--primary-color);
        }
        
        .page-item.active .page-link {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border: none;
        }
        
        .no-results {
            text-align: center;
            padding: 4rem 2rem;
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        
        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
        }
        
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 0.75rem 1rem;
            transition: all 0.3s ease;
        }
        
        .form-control:focus, .form-select:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        
        .btn-search {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border: none;
            border-radius: 10px;
            padding: 0.75rem 2rem;
            font-weight: 600;
        }
        
        .btn-clear {
            border-radius: 10px;
            padding: 0.75rem 2rem;
            font-weight: 600;
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
                    <?php if (isset($_SESSION['user_id'])): ?>
                        <li class="nav-item">
                            <a class="nav-link" href="favorites.php">
                                <i class="fas fa-heart me-1"></i>My Favorites
                            </a>
                        </li>
                        <?php if ($_SESSION['is_admin']): ?>
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
                    <?php else: ?>
                        <li class="nav-item">
                            <a class="nav-link" href="login.php">Login</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="register.php">Register</a>
                        </li>
                    <?php endif; ?>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Search Hero Section -->
    <section class="search-hero">
        <div class="container">
            <div class="row">
                <div class="col-lg-8 mx-auto text-center">
                    <h1 class="display-5 fw-bold mb-3">
                        <i class="fas fa-search me-3"></i>Canadian Tax Sale Properties
                    </h1>
                    <p class="lead">Find your next investment opportunity across Canada</p>
                </div>
            </div>
        </div>
    </section>

    <div class="container">
        <!-- Search Form -->
        <div class="search-form">
            <form method="GET" class="row g-4">
                <div class="col-md-3">
                    <label class="form-label fw-semibold">
                        <i class="fas fa-map-marker-alt me-2 text-primary"></i>Municipality
                    </label>
                    <select name="municipality" class="form-select">
                        <option value="">All Municipalities</option>
                        <?php foreach ($municipalities as $muni): ?>
                            <option value="<?php echo htmlspecialchars($muni); ?>" 
                                    <?php echo $municipality === $muni ? 'selected' : ''; ?>>
                                <?php echo htmlspecialchars($muni); ?>
                            </option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label fw-semibold">
                        <i class="fas fa-flag me-2 text-primary"></i>Status
                    </label>
                    <select name="status" class="form-select">
                        <option value="">All Status</option>
                        <option value="active" <?php echo $status === 'active' ? 'selected' : ''; ?>>Active</option>
                        <option value="inactive" <?php echo $status === 'inactive' ? 'selected' : ''; ?>>Inactive</option>
                        <option value="sold" <?php echo $status === 'sold' ? 'selected' : ''; ?>>Sold</option>
                        <option value="withdrawn" <?php echo $status === 'withdrawn' ? 'selected' : ''; ?>>Withdrawn</option>
                    </select>
                </div>
                <div class="col-md-5">
                    <label class="form-label fw-semibold">
                        <i class="fas fa-search me-2 text-primary"></i>Search
                    </label>
                    <input type="text" name="search" class="form-control" 
                           placeholder="Address, assessment number, or municipality"
                           value="<?php echo htmlspecialchars($search); ?>">
                </div>
                <div class="col-md-2 d-flex align-items-end gap-2">
                    <button type="submit" class="btn btn-search text-white flex-fill">
                        <i class="fas fa-search me-1"></i>Search
                    </button>
                </div>
            </form>
            <div class="text-center mt-3">
                <a href="search.php" class="btn btn-outline-secondary btn-clear">
                    <i class="fas fa-times me-1"></i>Clear Filters
                </a>
            </div>
        </div>

        <!-- Search Stats -->
        <div class="search-stats">
            <div class="row text-center">
                <div class="col-md-4">
                    <div class="fw-bold text-primary fs-4"><?php echo number_format($total_properties); ?></div>
                    <div class="text-muted">Total Properties</div>
                </div>
                <div class="col-md-2">
                    <div class="fw-bold text-success fs-4">
                        <?php echo count(array_filter($properties, fn($p) => $p['status'] === 'active')); ?>
                    </div>
                    <div class="text-muted">Active</div>
                </div>
                <div class="col-md-2">
                    <div class="fw-bold text-secondary fs-4">
                        <?php echo count(array_filter($properties, fn($p) => $p['status'] === 'inactive')); ?>
                    </div>
                    <div class="text-muted">Inactive</div>
                </div>
                <div class="col-md-2">
                    <div class="fw-bold text-info fs-4"><?php echo count($municipalities); ?></div>
                    <div class="text-muted">Municipalities</div>
                </div>
                <div class="col-md-2">
                    <div class="fw-bold text-warning fs-4">
                        Page <?php echo $page; ?> of <?php echo $total_pages; ?>
                    </div>
                    <div class="text-muted">Current Page</div>
                </div>
            </div>
        </div>

        <!-- DEBUG: Thumbnail Debug Panel (Admin Only) -->
        <?php if (isset($_SESSION['is_admin']) && $_SESSION['is_admin']): ?>
        <div class="alert alert-info mb-4" id="thumbnail-debug">
            <h5><i class="fas fa-bug"></i> Thumbnail Debug Info (Admin Only)</h5>
            <div class="row">
                <?php 
                // Show debug info for first 3 properties
                $debug_count = 0;
                foreach ($properties as $property): 
                    if ($debug_count >= 3) break;
                    $debug_count++;
                    
                    $thumbnail_url = $thumbnail_generator->getThumbnail($property);
                    $file_exists = false;
                    $file_size = 0;
                    
                    if (strpos($thumbnail_url, '/assets/thumbnails/') === 0) {
                        $file_path = dirname(__DIR__) . $thumbnail_url;
                        $file_exists = file_exists($file_path);
                        if ($file_exists) {
                            $file_size = filesize($file_path);
                        }
                    }
                ?>
                <div class="col-md-4 mb-3">
                    <div class="card">
                        <div class="card-header">
                            <strong><?php echo htmlspecialchars($property['assessment_number']); ?></strong>
                        </div>
                        <div class="card-body small">
                            <p><strong>PID:</strong> <?php echo htmlspecialchars($property['pid_number'] ?? 'NULL'); ?></p>
                            <p><strong>DB thumbnail_path:</strong> <code><?php echo htmlspecialchars($property['thumbnail_path'] ?? 'NULL'); ?></code></p>
                            <p><strong>getThumbnail() returns:</strong> <code><?php echo htmlspecialchars($thumbnail_url); ?></code></p>
                            <p><strong>Coordinates:</strong> <?php echo htmlspecialchars(($property['latitude'] ?? 'NULL') . ', ' . ($property['longitude'] ?? 'NULL')); ?></p>
                            <?php if (strpos($thumbnail_url, '/assets/thumbnails/') === 0): ?>
                                <p><strong>File exists:</strong> <?php echo $file_exists ? '<span class="text-success">✅ Yes</span>' : '<span class="text-danger">❌ No</span>'; ?></p>
                                <?php if ($file_exists): ?>
                                    <p><strong>File size:</strong> <?php echo number_format($file_size); ?> bytes</p>
                                <?php endif; ?>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
            
            <div class="mt-3">
                <button class="btn btn-sm btn-outline-danger" onclick="document.getElementById('thumbnail-debug').style.display='none'">
                    Hide Debug Panel
                </button>
                <a href="/admin.php" class="btn btn-sm btn-outline-primary">
                    Go to Admin Panel
                </a>
            </div>
        </div>
        <?php endif; ?>

        <!-- Properties Grid -->
        <div class="row">
            <?php foreach ($properties as $property): ?>
                <?php $thumbnail_url = $thumbnail_generator->getThumbnail($property); ?>
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="property-card">
                        <!-- Property Boundary Thumbnail -->
                        <div class="property-thumbnail">
                            <img src="<?php echo htmlspecialchars($thumbnail_url); ?>" 
                                 alt="Property boundary for <?php echo htmlspecialchars($property['assessment_number']); ?>"
                                 loading="lazy">
                            <div class="thumbnail-overlay">
                                <i class="fas fa-map-marked-alt me-1"></i>Boundary View
                            </div>
                        </div>
                        
                        <div class="property-header">
                            <div class="property-id"><?php echo htmlspecialchars($property['assessment_number']); ?></div>
                            <div class="property-status">
                                <span class="status-badge status-<?php echo $property['status']; ?>">
                                    <?php echo ucfirst($property['status']); ?>
                                </span>
                            </div>
                        </div>
                        <div class="property-details">
                            <div class="detail-row">
                                <div class="detail-label">
                                    <i class="fas fa-home me-2 text-primary"></i>Address
                                </div>
                                <div class="detail-value"><?php echo htmlspecialchars($property['civic_address'] ?? 'N/A'); ?></div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">
                                    <i class="fas fa-map-marker-alt me-2 text-info"></i>Municipality
                                </div>
                                <div class="detail-value"><?php echo htmlspecialchars($property['municipality']); ?></div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">
                                    <i class="fas fa-dollar-sign me-2 text-success"></i>Total Taxes
                                </div>
                                <div class="detail-value tax-amount">$<?php echo number_format($property['total_taxes'], 2); ?></div>
                            </div>
                            <div class="mt-3">
                                <a href="property.php?id=<?php echo $property['assessment_number']; ?>" 
                                   class="btn btn-view-details">
                                    <i class="fas fa-eye me-2"></i>View Details
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>

        <?php if (empty($properties)): ?>
            <div class="no-results">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h4>No properties found</h4>
                <p class="text-muted">Try adjusting your search criteria or <a href="search.php">clear all filters</a>.</p>
            </div>
        <?php endif; ?>

        <!-- Pagination -->
        <?php if ($total_pages > 1): ?>
            <div class="pagination-wrapper mt-4">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div class="text-muted">
                        <i class="fas fa-info-circle me-2"></i>
                        Showing <?php echo (($page - 1) * $per_page) + 1; ?> to <?php echo min($page * $per_page, $total_properties); ?> of <?php echo $total_properties; ?> properties
                    </div>
                </div>
                
                <nav aria-label="Property search pagination">
                    <ul class="pagination justify-content-center">
                        <!-- Previous page -->
                        <?php if ($page > 1): ?>
                            <li class="page-item">
                                <a class="page-link" href="?<?php echo http_build_query(array_merge($_GET, ['page' => $page - 1])); ?>">
                                    <i class="fas fa-chevron-left me-1"></i>Previous
                                </a>
                            </li>
                        <?php endif; ?>

                        <!-- Page numbers -->
                        <?php
                        $start = max(1, $page - 2);
                        $end = min($total_pages, $page + 2);
                        
                        if ($start > 1): ?>
                            <li class="page-item">
                                <a class="page-link" href="?<?php echo http_build_query(array_merge($_GET, ['page' => 1])); ?>">1</a>
                            </li>
                            <?php if ($start > 2): ?>
                                <li class="page-item disabled"><span class="page-link">...</span></li>
                            <?php endif;
                        endif;

                        for ($i = $start; $i <= $end; $i++): ?>
                            <li class="page-item <?php echo $i == $page ? 'active' : ''; ?>">
                                <a class="page-link" href="?<?php echo http_build_query(array_merge($_GET, ['page' => $i])); ?>"><?php echo $i; ?></a>
                            </li>
                        <?php endfor;

                        if ($end < $total_properties): ?>
                            <?php if ($end < $total_pages - 1): ?>
                                <li class="page-item disabled"><span class="page-link">...</span></li>
                            <?php endif; ?>
                            <li class="page-item">
                                <a class="page-link" href="?<?php echo http_build_query(array_merge($_GET, ['page' => $total_pages])); ?>"><?php echo $total_pages; ?></a>
                            </li>
                        <?php endif; ?>

                        <!-- Next page -->
                        <?php if ($page < $total_pages): ?>
                            <li class="page-item">
                                <a class="page-link" href="?<?php echo http_build_query(array_merge($_GET, ['page' => $page + 1])); ?>">
                                    Next<i class="fas fa-chevron-right ms-1"></i>
                                </a>
                            </li>
                        <?php endif; ?>
                    </ul>
                </nav>
            </div>
        <?php endif; ?>
    </div>

    <!-- Footer -->
    <footer class="py-5 bg-dark text-light mt-5">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h6 class="fw-bold">
                        <i class="fas fa-compass me-2"></i>Tax Sale Compass
                    </h6>
                    <p class="small text-muted">Your guide to Canadian tax sale opportunities.</p>
                </div>
                <div class="col-md-6 text-md-end">
                    <small class="text-muted">
                        © 2024 Tax Sale Compass. All rights reserved.
                    </small>
                </div>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>