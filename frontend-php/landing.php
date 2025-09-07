<!DOCTYPE html>
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
</html>