import React, { useState, useEffect } from 'react';
import { Eye, Search, MapPin, Users, CheckCircle, ArrowRight, Star, TrendingUp } from 'lucide-react';

const LandingPage = ({ onLogin, onRegister, sampleProperties = [] }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [municipalities, setMunicipalities] = useState([]);
  const [stats, setStats] = useState({
    municipalities: 0,
    active: 0,
    inactive: 0,
    total: 0,
    scrapedToday: 0,
    lastScrape: '2025-09-03'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    console.log('LandingPage login attempt:', { email, isLogin, isAdmin: email === 'admin' });

    try {
      if (isLogin) {
        // Convert 'admin' username to full admin email for backend
        const loginEmail = email === 'admin' ? 'admin@taxsalecompass.ca' : email;
        console.log('LandingPage calling onLogin with:', loginEmail, password.length + ' char password');
        
        const result = await onLogin(loginEmail, password);
        console.log('LandingPage login result:', result);
        
        if (result && result.success) {
          console.log('Login successful, user should be authenticated now');
          // The authentication state change should trigger a re-render in App.js
        } else {
          throw new Error('Login failed - no success result');
        }
      } else {
        console.log('LandingPage calling onRegister with:', email, password.length + ' char password');
        const result = await onRegister(email, password);
        console.log('LandingPage registration result:', result);
      }
    } catch (err) {
      console.error('LandingPage Login/Registration error:', err);
      // Ensure we're displaying the error message, not the error object
      setError(typeof err === 'string' ? err : err.message || err.toString() || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Load statistics data
  useEffect(() => {
    const loadStats = async () => {
      try {
        const backendUrl = process.env.REACT_APP_BACKEND_URL;
        
        // Load municipalities
        const munResponse = await fetch(`${backendUrl}/api/municipalities`);
        if (munResponse.ok) {
          const munData = await munResponse.json();
          setMunicipalities(munData);
        }
        
        // Calculate stats from sample properties
        const active = sampleProperties.filter(p => p.status === 'active').length;
        const inactive = sampleProperties.filter(p => p.status === 'inactive').length;
        
        // Get unique provinces from municipalities
        const uniqueProvinces = [...new Set(municipalities.map(m => m.province))].filter(Boolean);
        const provinceCount = uniqueProvinces.length || 1; // Fallback to 1 for Nova Scotia
        
        setStats({
          municipalities: municipalities.length || 3, // Fallback to 3
          provinces: provinceCount,
          active: active,
          inactive: inactive,
          total: sampleProperties.length,
          scrapedToday: 0,
          lastScrape: '2025-09-03'
        });
      } catch (error) {
        console.error('Error loading statistics:', error);
      }
    };

    loadStats();
  }, [sampleProperties, municipalities.length]);

  const features = [
    {
      icon: <Search className="h-8 w-8 text-blue-600" />,
      title: "Search Properties",
      description: "Find tax sale properties across all Canadian provinces with detailed filters and real-time updates."
    },
    {
      icon: <MapPin className="h-8 w-8 text-green-600" />,
      title: "Interactive Maps",
      description: "View property boundaries, locations, and nearby amenities with our integrated mapping system."
    },
    {
      icon: <TrendingUp className="h-8 w-8 text-purple-600" />,
      title: "Market Analysis",
      description: "Get insights on opening bids, property values, and market trends to make informed decisions."
    },
    {
      icon: <Users className="h-8 w-8 text-orange-600" />,
      title: "Expert Research",
      description: "Access detailed property information, ownership history, and legal documentation."
    }
  ];

  const howItWorks = [
    {
      step: "1",
      title: "Search Properties",
      description: "Browse our comprehensive database of tax sale properties across Canada."
    },
    {
      step: "2",
      title: "Research Details",
      description: "Get detailed property information, legal descriptions, and market analysis."
    },
    {
      step: "3",
      title: "Make Your Move",
      description: "Use our insights to make informed bidding decisions at tax sale auctions."
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Tax Sale Compass</h1>
                <p className="text-sm text-gray-600 font-medium">All tax sales. One platform.</p>
              </div>
              <span className="ml-3 px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                Alpha
              </span>
            </div>
            <nav className="hidden md:flex space-x-8">
              <a href="#features" className="text-gray-600 hover:text-gray-900">Features</a>
              <a href="#how-it-works" className="text-gray-600 hover:text-gray-900">How It Works</a>
              <a href="#properties" className="text-gray-600 hover:text-gray-900">Properties</a>
            </nav>
          </div>
        </div>
      </header>

      {/* Statistics Header */}
      <div className="bg-gray-900 text-white py-3">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center items-center space-x-8 text-sm">
            <div className="flex items-center">
              <span className="text-gray-300">{stats.municipalities} Municipalities</span>
            </div>
            <div className="flex items-center">
              <span className="font-semibold text-green-400">{stats.active}</span>
              <span className="ml-1 text-gray-300">Active</span>
            </div>
            <div className="flex items-center">
              <span className="font-semibold text-yellow-400">{stats.inactive}</span>
              <span className="ml-1 text-gray-300">Inactive</span>
            </div>
            <div className="flex items-center">
              <span className="font-semibold text-blue-400">{stats.total}</span>
              <span className="ml-1 text-gray-300">Total Properties</span>
            </div>
            <div className="flex items-center">
              <span className="font-semibold text-white">{stats.scrapedToday}</span>
              <span className="ml-1 text-gray-300">Scraped Today</span>
            </div>
            <div className="flex items-center">
              <span className="text-gray-300">Last:</span>
              <span className="ml-1 font-semibold text-white">{stats.lastScrape}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-5xl font-bold text-gray-900 mb-6">
                Your Compass to Canadian Tax Sale Investing
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Stop searching and start finding. Tax Sales Compass is your all-in-one platform for navigating the world of Canadian tax sale properties. We provide you with the data, maps, and tools you need to confidently discover and acquire your next investment opportunity.
              </p>
              <div className="grid grid-cols-2 gap-6 mb-8">
                <div className="text-center">
                  <div className="flex items-center justify-center space-x-2">
                    <div className="text-3xl font-bold text-green-600">1</div>
                    <div className="text-2xl">🍁</div>
                  </div>
                  <div className="text-sm text-gray-600">Provinces Covered</div>
                  <div className="text-xs text-gray-500 mt-1">Nova Scotia</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">{stats.municipalities}</div>
                  <div className="text-sm text-gray-600">Municipalities</div>
                </div>
              </div>
              <div className="flex space-x-4">
                <button
                  onClick={() => setIsLogin(false)}
                  className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center"
                >
                  Get Started Free
                  <ArrowRight className="ml-2 h-5 w-5" />
                </button>
                <button
                  onClick={() => setIsLogin(true)}
                  className="border border-gray-300 text-gray-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                >
                  Sign In
                </button>
              </div>
            </div>

            {/* Auth Form */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <div className="mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  {isLogin ? 'Welcome Back' : 'Start Your Search'}
                </h3>
                <p className="text-gray-600">
                  {isLogin ? 'Sign in to access your account' : 'Create your free account to get started'}
                </p>
              </div>

              <form onSubmit={handleSubmit}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {email === 'admin' ? 'Username' : 'Email Address'}
                  </label>
                  <input
                    type={email === 'admin' ? 'text' : 'email'}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder={email === 'admin' ? 'Enter username' : 'Enter your email'}
                    required
                  />
                  {email === 'admin' && (
                    <p className="text-sm text-blue-600 mt-1">
                      Admin login detected
                    </p>
                  )}
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your password"
                    required
                    minLength={6}
                  />
                </div>

                {error && (
                  <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-700 text-sm">{error}</p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading 
                    ? (isLogin ? 'Signing In...' : 'Creating Account...') 
                    : (isLogin ? 'Sign In' : 'Create Free Account')
                  }
                </button>

                <div className="mt-4 text-center">
                  <button
                    type="button"
                    onClick={() => {
                      setIsLogin(!isLogin);
                      setError('');
                    }}
                    className="text-blue-600 hover:text-blue-700 text-sm"
                  >
                    {isLogin 
                      ? "Don't have an account? Sign up" 
                      : "Already have an account? Sign in"
                    }
                  </button>
                </div>
              </form>

              {!isLogin && (
                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <div className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
                    <div className="text-sm text-blue-800">
                      <p className="font-medium mb-1">Free Account Includes:</p>
                      <ul className="space-y-1">
                        <li>• View all property listings</li>
                        <li>• Access inactive property details</li>
                        <li>• Basic search and filtering</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Sample Properties Section */}
      {sampleProperties.length > 0 && (
        <section id="properties" className="py-16 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h3 className="text-3xl font-bold text-gray-900 mb-4">Featured Properties</h3>
              <p className="text-xl text-gray-600">
                Discover investment opportunities across Canada
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {sampleProperties.slice(0, 6).map((property) => (
                <div key={property.id} className="bg-white rounded-lg shadow-lg overflow-hidden border">
                  {/* Property Image */}
                  <div className="h-48 bg-gradient-to-br from-gray-200 to-gray-300 relative">
                    {property.boundary_screenshot ? (
                      <img
                        src={`${process.env.REACT_APP_BACKEND_URL}/api/property-image/${property.assessment_number}?v=${Date.now()}`}
                        alt={property.property_address}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <MapPin className="h-12 w-12 text-gray-400" />
                      </div>
                    )}
                    <div className="absolute top-4 right-4 flex flex-col gap-2">
                      {/* Main Status Badge */}
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        property.status === 'active' 
                          ? 'bg-green-100 text-green-800 border border-green-200' 
                          : property.status === 'inactive'
                          ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                          : property.status === 'sold'
                          ? 'bg-blue-100 text-blue-800 border border-blue-200'
                          : 'bg-gray-100 text-gray-800 border border-gray-200'
                      }`}>
                        {(property.status || 'active').toUpperCase()}
                      </span>
                      
                      {/* Auction Result Badge - Only show for inactive/sold properties */}
                      {(property.status === 'inactive' || property.status === 'sold') && property.auction_result && (
                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                          property.auction_result === 'sold' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                          property.auction_result === 'pending' ? 'bg-orange-100 text-orange-800 border border-orange-200' :
                          property.auction_result === 'canceled' ? 'bg-red-100 text-red-800 border border-red-200' :
                          property.auction_result === 'deferred' ? 'bg-purple-100 text-purple-800 border border-purple-200' :
                          property.auction_result === 'taxes_paid' ? 'bg-green-100 text-green-800 border border-green-200' :
                          'bg-gray-100 text-gray-800 border border-gray-200'
                        }`}>
                          {property.auction_result === 'sold' ? 'SOLD' :
                           property.auction_result === 'pending' ? 'PENDING' :
                           property.auction_result === 'canceled' ? 'CANCELED' :
                           property.auction_result === 'deferred' ? 'DEFERRED' :
                           property.auction_result === 'taxes_paid' ? 'REDEEMED' :
                           property.auction_result.toUpperCase()}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Property Details */}
                  <div className="p-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-2 truncate">
                      {property.property_address}
                    </h4>
                    <p className="text-gray-600 text-sm mb-4">
                      {property.municipality_name}
                    </p>

                    <div className="flex justify-between items-center mb-4">
                      <div>
                        <p className="text-2xl font-bold text-green-600">
                          ${parseFloat(property.opening_bid || 0).toLocaleString()}
                        </p>
                        <p className="text-sm text-gray-600">Opening Bid</p>
                      </div>
                      {property.assessment_number && (
                        <div className="text-right">
                          <p className="text-sm font-medium text-gray-900">
                            #{property.assessment_number}
                          </p>
                          <p className="text-xs text-gray-600">Assessment</p>
                        </div>
                      )}
                    </div>

                    <button className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center">
                      <Eye className="mr-2 h-4 w-4" />
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="text-center mt-12">
              <button
                onClick={() => setIsLogin(false)}
                className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Create Free Account to View All Properties
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Features Section */}
      <section id="features" className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Everything You Need to Find Your Next Investment
            </h3>
            <p className="text-xl text-gray-600">
              Comprehensive tools and data to help you discover profitable tax sale opportunities
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-lg shadow-md mb-4">
                  {feature.icon}
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h4>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">How It Works</h3>
            <p className="text-xl text-gray-600">
              Three simple steps to start finding profitable tax sale properties
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {howItWorks.map((step, index) => (
              <div key={index} className="text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-600 text-white rounded-full text-xl font-bold mb-4">
                  {step.step}
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-2">{step.title}</h4>
                <p className="text-gray-600">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-blue-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h3 className="text-3xl font-bold text-white mb-4">
            Ready to Start Finding Great Deals?
          </h3>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of investors using Tax Sale Compass to find their next opportunity
          </p>
          <button
            onClick={() => setIsLogin(false)}
            className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
          >
            Get Started Free Today
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h4 className="text-2xl font-bold mb-4">Tax Sale Compass</h4>
            <p className="text-gray-400 mb-6">
              Your Complete Tax Sale Research Platform - Find properties cheap across Canada
            </p>
            <p className="text-sm text-gray-500">
              © 2025 Tax Sale Compass. All rights reserved. Alpha Version.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;