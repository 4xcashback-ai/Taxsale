<?php
session_start();
require_once 'config/database.php';
require_once 'includes/thumbnail_generator.php';

// Check if user is logged in
$is_logged_in = isset($_SESSION['user_id']) && isset($_SESSION['access_token']);

if (!$is_logged_in) {
    header('Location: login.php?redirect=' . urlencode($_SERVER['REQUEST_URI']));
    exit;
}

$user_id = $_SESSION['user_id'];

// Check if user is a paying customer
$db = getDB();
$stmt = $db->prepare("SELECT subscription_status, email FROM users WHERE id = ?");
$stmt->execute([$user_id]);
$user = $stmt->fetch();

if (!$user || $user['subscription_status'] !== 'paid') {
    // Redirect to upgrade page or show upgrade message
    header('Location: upgrade.php?feature=favorites');
    exit;
}

// Initialize thumbnail generator
$thumbnail_generator = new ThumbnailGenerator(GOOGLE_MAPS_API_KEY);

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Favorites - Tax Sale Compass</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
            --info-color: #17a2b8;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .main-content {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            margin: 2rem auto;
            max-width: 1400px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
        }
        
        .page-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border-radius: 20px 20px 0 0;
            padding: 2rem;
            text-align: center;
        }
        
        .favorites-stats {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 1rem;
            margin-top: 1rem;
            text-align: center;
        }
        
        .property-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            transition: all 0.3s ease;
            margin-bottom: 2rem;
        }
        
        .property-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        }
        
        .property-thumbnail {
            height: 200px;
            overflow: hidden;
            position: relative;
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
        
        .favorite-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(220, 53, 69, 0.9);
            color: white;
            border-radius: 20px;
            padding: 5px 10px;
            font-size: 0.8rem;
        }
        
        .property-content {
            padding: 1.5rem;
        }
        
        .property-title {
            color: var(--primary-color);
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }
        
        .property-details {
            color: #6c757d;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        
        .property-details i {
            width: 16px;
            margin-right: 8px;
            color: var(--primary-color);
        }
        
        .bid-info {
            background: linear-gradient(135deg, var(--success-color), #20c997);
            color: white;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .bid-amount {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .property-actions {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .btn-remove-favorite {
            background: var(--danger-color);
            border: none;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .btn-remove-favorite:hover {
            background: #c82333;
            color: white;
            transform: translateY(-2px);
        }
        
        .btn-view-property {
            background: var(--primary-color);
            border: none;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .btn-view-property:hover {
            background: var(--secondary-color);
            color: white;
            transform: translateY(-2px);
        }
        
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            color: #6c757d;
        }
        
        .empty-state i {
            font-size: 4rem;
            margin-bottom: 1rem;
            color: #dee2e6;
        }
        
        .loading-spinner {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 4rem 2rem;
        }
        
        .navbar {
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
        }
        
        .navbar-brand {
            font-weight: bold;
            color: var(--primary-color) !important;
        }
        
        .nav-link {
            color: #6c757d !important;
            font-weight: 500;
            transition: color 0.3s ease;
        }
        
        .nav-link:hover {
            color: var(--primary-color) !important;
        }
        
        .nav-link.active {
            color: var(--primary-color) !important;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-light fixed-top">
        <div class="container">
            <a class="navbar-brand" href="search.php">
                <i class="fas fa-gavel me-2"></i>Tax Sale Compass
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="search.php">
                            <i class="fas fa-search me-1"></i>Search
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link active" href="favorites.php">
                            <i class="fas fa-heart me-1"></i>My Favorites
                        </a>
                    </li>
                </ul>
                <ul class="navbar-nav">
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user me-1"></i><?php echo htmlspecialchars($user['email']); ?>
                        </a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="logout.php">
                                <i class="fas fa-sign-out-alt me-1"></i>Logout
                            </a></li>
                        </ul>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container mt-5 pt-4">
        <div class="main-content">
            <!-- Page Header -->
            <div class="page-header">
                <h1><i class="fas fa-heart me-3"></i>My Favorite Properties</h1>
                <p class="mb-0">Track and compare your most interesting tax sale opportunities</p>
                
                <div class="favorites-stats">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="h4 mb-0" id="favorites-count">--</div>
                            <small>Properties Saved</small>
                        </div>
                        <div class="col-md-4">
                            <div class="h4 mb-0">50</div>
                            <small>Max Allowed</small>
                        </div>
                        <div class="col-md-4">
                            <div class="h4 mb-0" id="remaining-slots">--</div>
                            <small>Slots Remaining</small>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Favorites Content -->
            <div class="p-4">
                <!-- Loading State -->
                <div id="loading-state" class="loading-spinner">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading favorites...</span>
                    </div>
                </div>

                <!-- Empty State -->
                <div id="empty-state" class="empty-state" style="display: none;">
                    <i class="fas fa-heart-broken"></i>
                    <h3>No Favorites Yet</h3>
                    <p>You haven't saved any properties to your favorites list yet.</p>
                    <a href="search.php" class="btn btn-primary btn-lg">
                        <i class="fas fa-search me-2"></i>Start Browsing Properties
                    </a>
                </div>

                <!-- Favorites Grid -->
                <div id="favorites-grid" class="row" style="display: none;">
                    <!-- Favorites will be loaded here dynamically -->
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Load favorites on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadFavorites();
        });

        function loadFavorites() {
            const loadingState = document.getElementById('loading-state');
            const emptyState = document.getElementById('empty-state');
            const favoritesGrid = document.getElementById('favorites-grid');
            
            loadingState.style.display = 'flex';
            emptyState.style.display = 'none';
            favoritesGrid.style.display = 'none';

            fetch('/api/favorites.php')
                .then(response => response.json())
                .then(data => {
                    loadingState.style.display = 'none';
                    
                    if (data.success) {
                        updateStats(data.count, data.max_allowed);
                        
                        if (data.favorites.length === 0) {
                            emptyState.style.display = 'block';
                        } else {
                            displayFavorites(data.favorites);
                            favoritesGrid.style.display = 'block';
                        }
                    } else {
                        showError(data.message);
                    }
                })
                .catch(error => {
                    loadingState.style.display = 'none';
                    showError('Failed to load favorites. Please try again.');
                    console.error('Error:', error);
                });
        }

        function updateStats(count, maxAllowed) {
            document.getElementById('favorites-count').textContent = count;
            document.getElementById('remaining-slots').textContent = maxAllowed - count;
        }

        function displayFavorites(favorites) {
            const grid = document.getElementById('favorites-grid');
            grid.innerHTML = '';

            favorites.forEach(property => {
                const card = createPropertyCard(property);
                grid.appendChild(card);
            });
        }

        function createPropertyCard(property) {
            const col = document.createElement('div');
            col.className = 'col-lg-6 col-xl-4';
            
            const thumbnailUrl = `/assets/thumbnails/${property.assessment_number}_boundary.png`;
            const favoritedDate = new Date(property.favorited_at).toLocaleDateString();
            
            col.innerHTML = `
                <div class="property-card">
                    <div class="property-thumbnail">
                        <img src="${thumbnailUrl}" alt="Property ${property.assessment_number}" 
                             onerror="this.src='data:image/svg+xml;base64,${generatePlaceholderSVG()}'">
                        <div class="favorite-badge">
                            <i class="fas fa-heart me-1"></i>${property.favorite_count || 0}
                        </div>
                    </div>
                    <div class="property-content">
                        <div class="property-title">
                            Property #${property.assessment_number}
                        </div>
                        <div class="property-details">
                            <div><i class="fas fa-map-marker-alt"></i>${property.civic_address || 'Address Not Available'}</div>
                            <div><i class="fas fa-city"></i>${property.municipality || 'N/A'}</div>
                            <div><i class="fas fa-tag"></i>${property.property_type ? property.property_type.charAt(0).toUpperCase() + property.property_type.slice(1).replace('_', ' ') : 'N/A'}</div>
                            <div><i class="fas fa-calendar"></i>Added ${favoritedDate}</div>
                        </div>
                        <div class="bid-info">
                            <div class="bid-amount">$${Number(property.opening_bid || property.total_taxes || 0).toLocaleString()}</div>
                            <div>Minimum Bid</div>
                        </div>
                        <div class="property-actions">
                            <button class="btn btn-remove-favorite" onclick="removeFavorite('${property.assessment_number}')">
                                <i class="fas fa-heart-broken me-1"></i>Remove
                            </button>
                            <a href="property.php?assessment=${property.assessment_number}" class="btn btn-view-property">
                                <i class="fas fa-eye me-1"></i>View Details
                            </a>
                        </div>
                    </div>
                </div>
            `;
            
            return col;
        }

        function removeFavorite(assessmentNumber) {
            if (!confirm('Are you sure you want to remove this property from your favorites?')) {
                return;
            }

            fetch('/api/favorites.php', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    assessment_number: assessmentNumber
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Reload favorites
                    loadFavorites();
                    showSuccess('Property removed from favorites');
                } else {
                    showError(data.message);
                }
            })
            .catch(error => {
                showError('Failed to remove favorite. Please try again.');
                console.error('Error:', error);
            });
        }

        function generatePlaceholderSVG() {
            const svg = `
                <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
                    <rect width="300" height="200" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
                    <text x="150" y="85" font-family="Arial" font-size="14" fill="#6c757d" text-anchor="middle">Property Image</text>
                    <text x="150" y="105" font-family="Arial" font-size="14" fill="#6c757d" text-anchor="middle">Not Available</text>
                    <text x="150" y="125" font-family="Arial" font-size="14" fill="#6c757d" text-anchor="middle">At This Time</text>
                    <circle cx="150" cy="140" r="8" fill="#6c757d" opacity="0.3"/>
                </svg>
            `;
            return btoa(svg);
        }

        function showSuccess(message) {
            // Create and show success toast
            const toast = createToast(message, 'success');
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }

        function showError(message) {
            // Create and show error toast
            const toast = createToast(message, 'error');
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 5000);
        }

        function createToast(message, type) {
            const toast = document.createElement('div');
            toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} position-fixed`;
            toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
            toast.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
            `;
            return toast;
        }
    </script>
</body>
</html>