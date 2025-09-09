<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tax Sale Compass - Canadian Property Search</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <!-- Google AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5947395928510215"
         crossorigin="anonymous"></script>
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
        .ad-container-landing {
            background: white;
            border-radius: 10px;
            padding: 2rem;
            margin: 3rem 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border: 1px solid #e9ecef;
        }
        .ad-container-landing::before {
            content: "Advertisement";
            display: block;
            text-align: center;
            font-size: 0.8rem;
            color: #6c757d;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .property-preview-card {
            transition: all 0.3s ease;
            overflow: hidden;
        }
        .property-preview-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15) !important;
        }
        .property-preview-thumbnail {
            position: relative;
            height: 200px;
            overflow: hidden;
        }
        .property-preview-thumbnail img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }
        .property-preview-card:hover .property-preview-thumbnail img {
            transform: scale(1.05);
        }
        .property-status-overlay {
            position: absolute;
            top: 10px;
            right: 10px;
        }
        .status-active {
            background-color: #28a745 !important;
            color: white;
        }
        .status-inactive {
            background-color: #6c757d !important;
            color: white;
        }
        .status-sold {
            background-color: #dc3545 !important;
            color: white;
        }
        .status-withdrawn {
            background-color: #ffc107 !important;
            color: black;
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
                    <h1 class="display-4 fw-bold mb-4">Find Canadian Tax Sale Properties</h1>
                    <p class="lead mb-5">Your comprehensive resource for discovering tax sale opportunities across Canada. Access detailed property information, interactive maps, and real-time updates from municipalities nationwide.</p>
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
                    <div class="stat-number">500+</div>
                    <h5>Active Properties</h5>
                    <p class="text-muted">Across Canadian municipalities</p>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="stat-number">10+</div>
                    <h5>Provinces Covered</h5>
                    <p class="text-muted">Coast to coast coverage</p>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="stat-number">$5K+</div>
                    <h5>Average Starting Bids</h5>
                    <p class="text-muted">Nationwide opportunities</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Google AdSense Ad -->
    <section class="py-0">
        <div class="container">
            <div class="ad-container-landing">
                <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5947395928510215"
                     crossorigin="anonymous"></script>
                <!-- Landing Page -->
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-5947395928510215"
                     data-ad-slot="6272201514"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
                <script>
                     (adsbygoogle = window.adsbygoogle || []).push({});
                </script>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="py-5" id="features">
        <div class="container">
            <div class="row mb-5">
                <div class="col-lg-8 mx-auto text-center">
                    <h2 class="fw-bold mb-3">Why Choose Tax Sale Compass?</h2>
                    <p class="lead text-muted">We provide the most comprehensive and up-to-date tax sale information across Canada</p>
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
                            <p class="card-text">Search by address, assessment number, municipality, province, or property type. Filter by price range and more across Canada.</p>
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
                            <p class="card-text">Get the latest tax sale information with automatic updates from municipal sources across Canada.</p>
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

    <!-- Properties Showcase Section -->
    <section class="py-5 bg-light">
        <div class="container">
            <div class="row mb-5">
                <div class="col-lg-8 mx-auto text-center">
                    <h2 class="fw-bold mb-3">Featured Properties</h2>
                    <p class="lead text-muted">Explore some of the latest tax sale opportunities available across Canada</p>
                </div>
            </div>
            
            <?php if (!empty($landing_properties)): ?>
            <div class="row">
                <?php foreach ($landing_properties as $property): ?>
                    <?php $thumbnail_url = $thumbnail_generator->getThumbnail($property); ?>
                    <div class="col-lg-4 col-md-6 mb-4">
                        <div class="card property-preview-card h-100 border-0 shadow-sm">
                            <!-- Property Thumbnail -->
                            <div class="property-preview-thumbnail">
                                <img src="<?php echo htmlspecialchars($thumbnail_url); ?>?v=<?php echo time(); ?>" 
                                     alt="Property <?php echo htmlspecialchars($property['assessment_number']); ?>"
                                     class="card-img-top"
                                     loading="lazy">
                                <div class="property-status-overlay">
                                    <span class="badge status-<?php echo $property['status']; ?>">
                                        <?php echo ucfirst($property['status']); ?>
                                    </span>
                                </div>
                            </div>
                            
                            <div class="card-body">
                                <h6 class="card-title text-primary fw-bold">
                                    Property #<?php echo htmlspecialchars($property['assessment_number']); ?>
                                </h6>
                                <p class="card-text text-muted small mb-2">
                                    <i class="fas fa-map-marker-alt me-1"></i>
                                    <?php echo htmlspecialchars($property['civic_address'] ?? 'Address Not Available'); ?>
                                </p>
                                <p class="card-text text-muted small mb-2">
                                    <i class="fas fa-city me-1"></i>
                                    <?php echo htmlspecialchars($property['municipality'] ?? 'N/A'); ?>
                                </p>
                                
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <div>
                                        <span class="fw-bold text-success">
                                            $<?php echo number_format($property['opening_bid'] ?? $property['total_taxes'] ?? 0, 2); ?>
                                        </span>
                                        <small class="text-muted d-block">Min Bid</small>
                                    </div>
                                    <?php if ($property['property_type']): ?>
                                    <span class="badge bg-info">
                                        <?php echo ucfirst(str_replace('_', ' ', $property['property_type'])); ?>
                                    </span>
                                    <?php endif; ?>
                                </div>
                                
                                <?php if ($property['status'] === 'active'): ?>
                                    <!-- Active property - requires login -->
                                    <a href="login.php?redirect=<?php echo urlencode('property.php?assessment=' . $property['assessment_number']); ?>" 
                                       class="btn btn-primary btn-sm w-100">
                                        <i class="fas fa-sign-in-alt me-1"></i>Login to View Details
                                    </a>
                                <?php else: ?>
                                    <!-- Inactive property - can view directly -->
                                    <a href="property.php?assessment=<?php echo $property['assessment_number']; ?>" 
                                       class="btn btn-outline-primary btn-sm w-100">
                                        <i class="fas fa-eye me-1"></i>View Details
                                    </a>
                                <?php endif; ?>
                            </div>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
            
            <div class="text-center mt-4">
                <a href="register.php" class="btn btn-primary btn-lg px-4">
                    <i class="fas fa-search me-2"></i>Search All Properties
                </a>
                <p class="text-muted mt-2 small">Join now to access all active properties and advanced search features</p>
            </div>
            
            <?php else: ?>
            <div class="text-center py-5">
                <i class="fas fa-home fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">No properties available at the moment</h5>
                <p class="text-muted">Check back soon for new listings</p>
            </div>
            <?php endif; ?>
        </div>
    </section>

    <!-- About Section -->
    <section class="py-5 bg-light" id="about">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6 mb-4">
                    <h2 class="fw-bold mb-4">About Tax Sale Compass</h2>
                    <p class="mb-4">Tax Sale Compass is Canada's premier platform for discovering tax sale opportunities. We aggregate and organize tax sale information from municipalities across all provinces and territories, making it easy for investors and homebuyers to find properties of interest nationwide.</p>
                    
                    <div class="row">
                        <div class="col-sm-6">
                            <h6 class="fw-bold text-primary">
                                <i class="fas fa-check-circle me-2"></i>Comprehensive Coverage
                            </h6>
                            <p class="small text-muted mb-3">All Canadian provinces & territories</p>
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
            <p class="lead mb-4">Join thousands of investors and homebuyers using Tax Sale Compass to discover opportunities across Canada.</p>
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