<?php
session_start();
require_once 'config/database.php';

// Check if user is logged in
$is_logged_in = isset($_SESSION['user_id']) && isset($_SESSION['access_token']);

// If user is not logged in, show landing page content
if (!$is_logged_in) {
    // Include landing page HTML directly
    ?><!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tax Sale Compass - Canadian Property Search</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 100px 0;
            text-align: center;
        }
        .feature-card {
            transition: transform 0.3s;
            height: 100%;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .feature-icon {
            font-size: 3rem;
            color: #667eea;
            margin-bottom: 1rem;
        }
        .stats-section {
            background: #f8f9fa;
            padding: 60px 0;
        }
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark" style="background-color: #667eea;">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="fas fa-compass me-2"></i>Tax Sale Compass
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#features">Features</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#about">About</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link btn btn-outline-light ms-2 px-3" href="login.php">Login</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link btn btn-light text-primary ms-2 px-3" href="register.php">Sign Up</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <h1 class="display-4 fw-bold mb-4">Find Nova Scotia Tax Sale Properties</h1>
                    <p class="lead mb-5">Your comprehensive resource for discovering tax sale opportunities across Nova Scotia. Access detailed property information, interactive maps, and real-time updates.</p>
                    <div class="d-gap-3">
                        <a href="register.php" class="btn btn-light btn-lg me-3 px-4">
                            <i class="fas fa-search me-2"></i>Start Searching
                        </a>
                        <a href="login.php" class="btn btn-outline-light btn-lg px-4">
                            <i class="fas fa-sign-in-alt me-2"></i>Login
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Stats Section -->
    <section class="stats-section">
        <div class="container">
            <div class="row text-center">
                <div class="col-md-4 mb-4">
                    <div class="stat-number">61</div>
                    <h5>Halifax Properties</h5>
                    <p class="text-muted">Active tax sale listings</p>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="stat-number">3</div>
                    <h5>Municipalities</h5>
                    <p class="text-muted">Halifax, Victoria, Cumberland</p>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="stat-number">$2.5K+</div>
                    <h5>Starting Bids</h5>
                    <p class="text-muted">Average opening bid</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="py-5" id="features">
        <div class="container">
            <div class="row mb-5">
                <div class="col-lg-8 mx-auto text-center">
                    <h2 class="fw-bold mb-3">Why Choose Tax Sale Compass?</h2>
                    <p class="lead text-muted">We provide the most comprehensive and up-to-date tax sale information in Nova Scotia</p>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="card feature-card border-0 shadow-sm h-100">
                        <div class="card-body text-center p-4">
                            <div class="feature-icon">
                                <i class="fas fa-map-marked-alt"></i>
                            </div>
                            <h5 class="card-title">Interactive Maps</h5>
                            <p class="card-text">View properties on interactive Google Maps with detailed location information and boundary overlays.</p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card feature-card border-0 shadow-sm h-100">
                        <div class="card-body text-center p-4">
                            <div class="feature-icon">
                                <i class="fas fa-search"></i>
                            </div>
                            <h5 class="card-title">Advanced Search</h5>
                            <p class="card-text">Search by address, assessment number, municipality, or property type. Filter by price range and more.</p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card feature-card border-0 shadow-sm h-100">
                        <div class="card-body text-center p-4">
                            <div class="feature-icon">
                                <i class="fas fa-clock"></i>
                            </div>
                            <h5 class="card-title">Real-time Updates</h5>
                            <p class="card-text">Get the latest tax sale information with automatic updates from municipal sources.</p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card feature-card border-0 shadow-sm h-100">
                        <div class="card-body text-center p-4">
                            <div class="feature-icon">
                                <i class="fas fa-file-alt"></i>
                            </div>
                            <h5 class="card-title">Detailed Information</h5>
                            <p class="card-text">Access complete property details including assessment numbers, opening bids, and property types.</p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card feature-card border-0 shadow-sm h-100">
                        <div class="card-body text-center p-4">
                            <div class="feature-icon">
                                <i class="fas fa-heart"></i>
                            </div>
                            <h5 class="card-title">Favorites List</h5>
                            <p class="card-text">Save interesting properties to your personal favorites list for easy tracking and comparison.</p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card feature-card border-0 shadow-sm h-100">
                        <div class="card-body text-center p-4">
                            <div class="feature-icon">
                                <i class="fas fa-mobile-alt"></i>
                            </div>
                            <h5 class="card-title">Mobile Friendly</h5>
                            <p class="card-text">Access tax sale information on any device with our responsive, mobile-optimized design.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section class="py-5 bg-light" id="about">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6 mb-4">
                    <h2 class="fw-bold mb-4">About Tax Sale Compass</h2>
                    <p class="mb-4">Tax Sale Compass is Nova Scotia's premier platform for discovering tax sale opportunities. We aggregate and organize tax sale information from multiple municipalities, making it easy for investors and homebuyers to find properties of interest.</p>
                    
                    <div class="row">
                        <div class="col-sm-6">
                            <h6 class="fw-bold text-primary">
                                <i class="fas fa-check-circle me-2"></i>Comprehensive Coverage
                            </h6>
                            <p class="small text-muted mb-3">All major NS municipalities</p>
                        </div>
                        <div class="col-sm-6">
                            <h6 class="fw-bold text-primary">
                                <i class="fas fa-check-circle me-2"></i>Real-time Data
                            </h6>
                            <p class="small text-muted mb-3">Updated daily from official sources</p>
                        </div>
                    </div>
                    
                    <a href="register.php" class="btn btn-primary btn-lg">Get Started Today</a>
                </div>
                <div class="col-lg-6">
                    <div class="text-center">
                        <i class="fas fa-compass text-primary" style="font-size: 8rem; opacity: 0.1;"></i>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="py-5" style="background-color: #667eea;">
        <div class="container text-center text-white">
            <h2 class="fw-bold mb-3">Ready to Find Your Next Property?</h2>
            <p class="lead mb-4">Join thousands of investors and homebuyers using Tax Sale Compass to discover opportunities in Nova Scotia.</p>
            <a href="register.php" class="btn btn-light btn-lg px-4">
                <i class="fas fa-rocket me-2"></i>Start Your Search Now
            </a>
        </div>
    </section>

    <!-- Footer -->
    <footer class="py-4 bg-dark text-light">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h6 class="fw-bold">
                        <i class="fas fa-compass me-2"></i>Tax Sale Compass
                    </h6>
                    <p class="small text-muted">Your guide to Nova Scotia tax sale opportunities.</p>
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
</html><?php
    exit; // Stop execution after showing landing page
}

// If we reach here, user is logged in, continue with search functionality

// Get search parameters
$municipality = $_GET['municipality'] ?? '';
$status = $_GET['status'] ?? '';
$search = $_GET['search'] ?? '';

// Build query
$query = "SELECT * FROM properties WHERE 1=1";
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

// Get municipalities for filter
$municipalities = $db->query("SELECT DISTINCT municipality FROM properties ORDER BY municipality")->fetchAll(PDO::FETCH_COLUMN);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo SITE_NAME; ?> - Nova Scotia Tax Sale Properties</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://maps.googleapis.com/maps/api/js?key=<?php echo GOOGLE_MAPS_API_KEY; ?>&libraries=geometry" defer></script>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="index.php"><?php echo SITE_NAME; ?></a>
            <div class="navbar-nav ms-auto">
                <?php if (isset($_SESSION['user_id'])): ?>
                    <a class="nav-link" href="favorites.php">My Favorites</a>
                    <?php if ($_SESSION['is_admin']): ?>
                        <a class="nav-link" href="admin.php">Admin</a>
                    <?php endif; ?>
                    <a class="nav-link" href="logout.php">Logout</a>
                <?php else: ?>
                    <a class="nav-link" href="login.php">Login</a>
                    <a class="nav-link" href="register.php">Register</a>
                <?php endif; ?>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h1>Nova Scotia Tax Sale Properties</h1>
        
        <!-- Search Filters -->
        <div class="row mb-4">
            <div class="col-md-12">
                <form method="GET" class="row g-3">
                    <div class="col-md-3">
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
                        <select name="status" class="form-select">
                            <option value="">All Status</option>
                            <option value="active" <?php echo $status === 'active' ? 'selected' : ''; ?>>Active</option>
                            <option value="sold" <?php echo $status === 'sold' ? 'selected' : ''; ?>>Sold</option>
                            <option value="withdrawn" <?php echo $status === 'withdrawn' ? 'selected' : ''; ?>>Withdrawn</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <input type="text" name="search" class="form-control" 
                               placeholder="Search by assessment number or address"
                               value="<?php echo htmlspecialchars($search); ?>">
                    </div>
                    <div class="col-md-3">
                        <button type="submit" class="btn btn-primary">Search</button>
                        <a href="search.php" class="btn btn-secondary">Clear</a>
                    </div>
                </form>
            </div>
        </div>

        <!-- Properties Grid -->
        <div class="row">
            <?php foreach ($properties as $property): ?>
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">
                                <a href="property.php?id=<?php echo $property['assessment_number']; ?>" 
                                   class="text-decoration-none">
                                    <?php echo htmlspecialchars($property['assessment_number']); ?>
                                </a>
                            </h5>
                            <p class="card-text">
                                <strong>Address:</strong> <?php echo htmlspecialchars($property['civic_address'] ?? 'N/A'); ?><br>
                                <strong>Municipality:</strong> <?php echo htmlspecialchars($property['municipality']); ?><br>
                                <strong>Total Taxes:</strong> $<?php echo number_format($property['total_taxes'], 2); ?><br>
                                <strong>Status:</strong> 
                                <span class="badge bg-<?php echo $property['status'] === 'active' ? 'success' : 'secondary'; ?>">
                                    <?php echo ucfirst($property['status']); ?>
                                </span>
                            </p>
                            <a href="property.php?id=<?php echo $property['assessment_number']; ?>" 
                               class="btn btn-primary btn-sm">View Details</a>
                        </div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>

        <?php if (empty($properties)): ?>
            <div class="alert alert-info">
                <h4>No properties found</h4>
                <p>Try adjusting your search criteria.</p>
            </div>
        <?php endif; ?>

        <!-- Pagination -->
        <?php if ($total_pages > 1): ?>
            <nav aria-label="Property search pagination" class="mt-4">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div class="text-muted">
                        Showing <?php echo (($page - 1) * $per_page) + 1; ?> to <?php echo min($page * $per_page, $total_properties); ?> of <?php echo $total_properties; ?> properties
                    </div>
                </div>
                
                <ul class="pagination justify-content-center">
                    <!-- Previous page -->
                    <?php if ($page > 1): ?>
                        <li class="page-item">
                            <a class="page-link" href="?<?php echo http_build_query(array_merge($_GET, ['page' => $page - 1])); ?>">Previous</a>
                        </li>
                    <?php else: ?>
                        <li class="page-item disabled">
                            <span class="page-link">Previous</span>
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

                    if ($end < $total_pages): ?>
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
                            <a class="page-link" href="?<?php echo http_build_query(array_merge($_GET, ['page' => $page + 1])); ?>">Next</a>
                        </li>
                    <?php else: ?>
                        <li class="page-item disabled">
                            <span class="page-link">Next</span>
                        </li>
                    <?php endif; ?>
                </ul>
            </nav>
        <?php endif; ?>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>