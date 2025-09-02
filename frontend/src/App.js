import React, { useState, useEffect, useCallback, useRef } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import "./App.css";
import axios from "axios";
import { Search, MapPin, Calendar, DollarSign, Building2, BarChart3, RefreshCw, Download, Gavel, Users, Clock, Plus, Edit, Save, X, Home, Trash2, Check, Lock, LogIn, LogOut } from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Wrapper, Status } from "@googlemaps/react-wrapper";
import PropertyDetails from './components/PropertyDetails';
import LandingPage from './components/LandingPage';
import EmailVerification from './components/EmailVerification';
import UpgradeModal from './components/UpgradeModal';
import { UserProvider, useUser } from './contexts/UserContext';

// AdSense Component for Search Page
const SearchPageAd = ({ index }) => {
  useEffect(() => {
    try {
      // Load AdSense script if not already loaded
      if (!document.querySelector('script[src*="googlesyndication.com"]')) {
        const script = document.createElement('script');
        script.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5947395928510215';
        script.async = true;
        script.crossOrigin = 'anonymous';
        document.head.appendChild(script);
      }
      
      // Push ad to AdSense
      if (window.adsbygoogle) {
        window.adsbygoogle.push({});
      }
    } catch (err) {
      console.log('AdSense error:', err);
    }
  }, [index]);

  return (
    <div className="my-6 p-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
      <div className="text-center text-sm text-gray-500 mb-2">Advertisement</div>
      <ins className="adsbygoogle"
           style={{display:'block'}}
           data-ad-client="ca-pub-5947395928510215"
           data-ad-slot="2293195574"
           data-ad-format="auto"
           data-full-width-responsive="true">
      </ins>
    </div>
  );
};

// Main authenticated application component
const AuthenticatedApp = () => {
  const { user, logout, isAdmin, canViewActiveProperties } = useUser();
  
  // All the existing app state and functions
  const [taxSales, setTaxSales] = useState([]);
  const [municipalities, setMunicipalities] = useState([]);
  const [stats, setStats] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMunicipality, setSelectedMunicipality] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('active');
  const [loading, setLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [showPropertyDetails, setShowPropertyDetails] = useState(false);
  const [selectedPropertyForResult, setSelectedPropertyForResult] = useState(null);
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false);
  const [upgradeModalProperty, setUpgradeModalProperty] = useState(null);
  
  // Admin state
  const [newMunicipality, setNewMunicipality] = useState({
    name: '',
    website_url: '',
    scrape_enabled: false,
    scraper_type: 'halifax'
  });
  const [editingMunicipality, setEditingMunicipality] = useState(null);

  // Environment variables with fallbacks
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchStats();
    fetchMunicipalities();
    fetchTaxSales();
  }, [selectedStatus, selectedMunicipality]);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/api/stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const fetchMunicipalities = async () => {
    try {
      const response = await axios.get(`${API}/api/municipalities`);
      setMunicipalities(response.data);
    } catch (error) {
      console.error("Error fetching municipalities:", error);
    }
  };

  const fetchTaxSales = async (municipality = selectedMunicipality, query = searchQuery) => {
    setLoading(true);
    try {
      let url = `${API}/api/tax-sales`;
      const params = new URLSearchParams();
      
      if (municipality) {
        params.append("municipality", municipality);
      }
      if (selectedStatus && selectedStatus !== 'all') {
        params.append("status", selectedStatus);
      }
      if (query) {
        url = `${API}/api/tax-sales/search`;
        params.append("q", query);
      }
      
      if (params.toString()) {
        url += "?" + params.toString();
      }

      const response = await axios.get(url);
      setTaxSales(response.data);
    } catch (error) {
      console.error("Error fetching tax sales:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    await fetchTaxSales(selectedMunicipality, searchQuery);
  };

  const handlePropertyClick = (property) => {
    // Check if user can view this property
    if (property.status === 'active' && !canViewActiveProperties()) {
      setUpgradeModalProperty(property);
      setUpgradeModalOpen(true);
      return;
    }
    
    setSelectedProperty(property);
    setShowPropertyDetails(true);
  };

  const formatCurrency = (amount) => {
    if (!amount) return "$0";
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'TBA';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-CA', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Admin functions (existing functions with token headers)
  const handleAddMunicipality = async () => {
    if (!newMunicipality.name.trim() || !newMunicipality.website_url.trim()) return;

    try {
      const response = await axios.post(`${API}/api/municipalities`, newMunicipality);
      setMunicipalities([...municipalities, response.data]);
      setNewMunicipality({
        name: '',
        website_url: '',
        scrape_enabled: false,
        scraper_type: 'halifax'
      });
    } catch (error) {
      console.error('Error adding municipality:', error);
      alert('Error adding municipality. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Tax Sale Compass</h1>
              <Badge variant="secondary" className="ml-2">Alpha</Badge>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* User Info */}
              <div className="text-sm text-gray-600">
                <span className="font-medium">{user?.email}</span>
                <Badge 
                  variant={user?.subscription_tier === 'paid' ? 'default' : 'secondary'}
                  className="ml-2"
                >
                  {user?.subscription_tier === 'paid' ? 'Premium' : 'Free'}
                </Badge>
              </div>
              
              {/* Logout Button */}
              <Button 
                variant="outline" 
                size="sm"
                onClick={logout}
                className="flex items-center"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="search" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="search">Property Search</TabsTrigger>
            <TabsTrigger value="map">Interactive Map</TabsTrigger>
            <TabsTrigger value="stats">Statistics</TabsTrigger>
            {isAdmin() && <TabsTrigger value="admin">Admin</TabsTrigger>}
          </TabsList>

          {/* Property Search Tab */}
          <TabsContent value="search" className="space-y-6">
            {/* Search Controls */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Search className="mr-2 h-5 w-5" />
                  Search Properties
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  {/* Search Input */}
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <input
                      type="text"
                      placeholder="Search by address, assessment number, PID..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleSearch();
                        }
                      }}
                    />
                  </div>

                  {/* Municipality Filter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Municipality
                    </label>
                    <select
                      value={selectedMunicipality}
                      onChange={(e) => setSelectedMunicipality(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">All Municipalities</option>
                      {municipalities.map((municipality) => (
                        <option key={municipality.id} value={municipality.name}>
                          {municipality.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Status Filter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Status
                    </label>
                    <select
                      value={selectedStatus}
                      onChange={(e) => setSelectedStatus(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                      <option value="sold">Sold</option>
                      <option value="all">All</option>
                    </select>
                  </div>
                </div>

                <Button onClick={handleSearch} className="w-full md:w-auto">
                  <Search className="mr-2 h-4 w-4" />
                  Search Properties
                </Button>
              </CardContent>
            </Card>

            {/* Results */}
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-semibold text-gray-900">
                  {loading ? 'Loading...' : `Showing ${taxSales.length} properties`}
                  {searchQuery && ` matching "${searchQuery}"`}
                </h2>
              </div>

              {loading ? (
                <div className="text-center py-12">
                  <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400" />
                  <p className="mt-2 text-gray-600">Loading properties...</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {taxSales.map((property, index) => (
                    <div key={property.id}>
                      <Card 
                        className="cursor-pointer hover:shadow-lg transition-shadow duration-200 relative"
                        onClick={() => handlePropertyClick(property)}
                      >
                        {/* Status and Auction Result Badges */}
                        <div className="absolute top-2 right-2 flex flex-col gap-1">
                          {/* Main Status Badge */}
                          <div className={`px-2 py-1 rounded text-xs font-medium ${
                            property.status === 'active' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {(property.status || 'Unknown').charAt(0).toUpperCase() + (property.status || 'Unknown').slice(1)}
                          </div>
                          
                          {/* Auction Result Badge */}
                          {property.auction_result && (
                            <div className={`px-2 py-1 rounded text-xs font-medium ${
                              property.auction_result === 'sold' ? 'bg-blue-100 text-blue-800' :
                              property.auction_result === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              property.auction_result === 'canceled' ? 'bg-red-100 text-red-800' :
                              property.auction_result === 'deferred' ? 'bg-orange-100 text-orange-800' :
                              property.auction_result === 'taxes_paid' ? 'bg-green-100 text-green-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {property.auction_result === 'sold' ? 'Sold' :
                               property.auction_result === 'pending' ? 'Results Pending' :
                               property.auction_result === 'canceled' ? 'Canceled' :
                               property.auction_result === 'deferred' ? 'Deferred' :
                               property.auction_result === 'taxes_paid' ? 'Redeemed' :
                               property.auction_result}
                            </div>
                          )}
                        </div>

                        <CardContent className="p-4">
                          {/* Property Address */}
                          <h3 className="text-lg font-semibold text-gray-900 mb-2 pr-16">
                            {property.property_address}
                          </h3>

                          {/* Municipality */}
                          <p className="text-sm text-gray-600 mb-3 flex items-center">
                            <MapPin className="h-4 w-4 mr-1" />
                            {property.municipality_name}
                          </p>

                          {/* Price */}
                          <div className="mb-3">
                            <span className="text-xl font-bold text-green-600">
                              ${parseFloat(property.opening_bid || 0).toLocaleString()}
                            </span>
                            {property.auction_result === 'sold' && property.winning_bid_amount && (
                              <div className="mt-1">
                                <span className="text-sm text-gray-500">Final Sale: </span>
                                <span className="text-lg font-semibold text-blue-600">
                                  ${parseFloat(property.winning_bid_amount).toLocaleString()}
                                </span>
                              </div>
                            )}
                          </div>

                          {/* Additional Info */}
                          <div className="space-y-1 text-sm text-gray-600 mb-4">
                            {property.assessment_number && (
                              <p>Assessment: {property.assessment_number}</p>
                            )}
                            {property.pid_number && (
                              <div className="flex items-center">
                                <span>PID: {property.pid_number}</span>
                                {property.pid_number.includes('/') && (
                                  <Badge variant="secondary" className="ml-2 text-xs">
                                    Multiple PIDs
                                  </Badge>
                                )}
                              </div>
                            )}
                            {property.sale_date && (
                              <p className="flex items-center">
                                <Calendar className="h-3 w-3 mr-1" />
                                {formatDate(property.sale_date)}
                              </p>
                            )}
                          </div>

                          {/* Access Control Notice */}
                          {property.status === 'active' && !canViewActiveProperties() && (
                            <div className="bg-blue-50 border border-blue-200 rounded p-2 mb-3">
                              <div className="flex items-center">
                                <Lock className="h-4 w-4 text-blue-600 mr-2" />
                                <span className="text-sm text-blue-800 font-medium">
                                  Premium Required
                                </span>
                              </div>
                              <p className="text-xs text-blue-700 mt-1">
                                Upgrade to view active property details
                              </p>
                            </div>
                          )}

                          <Button 
                            className="w-full" 
                            variant={property.status === 'active' && !canViewActiveProperties() ? "outline" : "default"}
                          >
                            {property.status === 'active' && !canViewActiveProperties() 
                              ? 'Upgrade to View Details' 
                              : 'See More Details'
                            }
                          </Button>
                        </CardContent>
                      </Card>

                      {/* Ad placement every 3 properties */}
                      {(index + 1) % 3 === 0 && <SearchPageAd index={index} />}
                    </div>
                  ))}
                </div>
              )}

              {!loading && taxSales.length === 0 && (
                <div className="text-center py-12 bg-white rounded-lg">
                  <Building2 className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Properties Found</h3>
                  <p className="text-gray-600">
                    {searchQuery ? 
                      'Try adjusting your search terms or filters.' : 
                      'No tax sale properties available at this time.'
                    }
                  </p>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Statistics Tab */}
          <TabsContent value="stats">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Properties</CardTitle>
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.total_properties || 0}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Properties</CardTitle>
                  <Gavel className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">{stats.active_properties || 0}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Municipalities</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.total_municipalities || 0}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Last Update</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-sm">{stats.last_scrape ? formatDate(stats.last_scrape) : 'Never'}</div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Admin Tab */}
          {isAdmin() && (
            <TabsContent value="admin">
              <div className="space-y-6">
                {/* Admin header with user info */}
                <Card>
                  <CardHeader>
                    <CardTitle>Admin Dashboard</CardTitle>
                    <CardDescription>
                      Manage municipalities, monitor system status, and configure settings
                    </CardDescription>
                  </CardHeader>
                </Card>

                {/* Existing admin functionality would go here */}
                <Card>
                  <CardHeader>
                    <CardTitle>System Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-green-600">All systems operational</p>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          )}
        </Tabs>
      </div>

      {/* Property Details Modal */}
      {showPropertyDetails && selectedProperty && (
        <PropertyDetails
          property={selectedProperty}
          onClose={() => {
            setShowPropertyDetails(false);
            setSelectedProperty(null);
          }}
        />
      )}

      {/* Upgrade Modal */}
      <UpgradeModal
        isOpen={upgradeModalOpen}
        onClose={() => {
          setUpgradeModalOpen(false);
          setUpgradeModalProperty(null);
        }}
        onUpgrade={() => {
          // Handle upgrade logic
          setUpgradeModalOpen(false);
        }}
        propertyAddress={upgradeModalProperty?.property_address}
      />
    </div>
  );
};

// Main App Component with Router and User Context
const App = () => {
  return (
    <UserProvider>
      <div className="App">
        <Router>
          <Routes>
            <Route path="/verify-email" element={<EmailVerification />} />
            <Route path="/*" element={<AppContent />} />
          </Routes>
        </Router>
      </div>
    </UserProvider>
  );
};

// App Content Component that handles landing vs authenticated views
const AppContent = () => {
  const { user, loading, login, register, isAuthenticated } = useUser();
  const [sampleProperties, setSampleProperties] = useState([]);

  // Fetch sample properties for landing page
  useEffect(() => {
    if (!isAuthenticated) {
      fetchSampleProperties();
    }
  }, [isAuthenticated]);

  const fetchSampleProperties = async () => {
    try {
      const API = process.env.REACT_APP_BACKEND_URL || 'https://taxsale-mapper.preview.emergentagent.com';
      const response = await axios.get(`${API}/api/tax-sales?limit=8`);
      setSampleProperties(response.data);
    } catch (error) {
      console.error("Error fetching sample properties:", error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-600 mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Show landing page if not authenticated
  if (!isAuthenticated) {
    return (
      <LandingPage
        onLogin={login}
        onRegister={register}
        sampleProperties={sampleProperties}
      />
    );
  }

  // Show authenticated app
  return <AuthenticatedApp />;
};

export default App;