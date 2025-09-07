<?php
session_start();
require_once 'config/database.php';

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

# Get total count for pagination
$count_query = "SELECT COUNT(*) FROM properties WHERE 1=1";
$count_params = [];

# Apply same filters to count query
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

# Get total count
$count_stmt = $db->prepare($count_query);
$count_stmt->execute($count_params);
$total_properties = $count_stmt->fetchColumn();
$total_pages = ceil($total_properties / $per_page);

$query .= " ORDER BY created_at DESC LIMIT $per_page OFFSET $offset";

$db = getDB();
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
                        <a href="index.php" class="btn btn-secondary">Clear</a>
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