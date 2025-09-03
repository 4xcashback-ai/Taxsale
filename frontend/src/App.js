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
import InteractiveMap from './components/InteractiveMap';
import LandingPage from './components/LandingPage';
import EmailVerification from './components/EmailVerification';
import UpgradeModal from './components/UpgradeModal';
import AuctionResultModal from './components/AuctionResultModal';
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
  const [allProperties, setAllProperties] = useState([]); // For statistics header - always shows all properties
  const [municipalities, setMunicipalities] = useState([]);
  const [stats, setStats] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMunicipality, setSelectedMunicipality] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [loading, setLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [showPropertyDetails, setShowPropertyDetails] = useState(false);
  const [selectedPropertyForResult, setSelectedPropertyForResult] = useState(null);
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false);
  const [upgradeModalProperty, setUpgradeModalProperty] = useState(null);
  const [activeView, setActiveView] = useState('search');
  
  // Admin state
  const [newMunicipality, setNewMunicipality] = useState({
    name: '',
    website_url: '',
    scrape_enabled: false,
    scraper_type: 'halifax'
  });
  const [editingMunicipality, setEditingMunicipality] = useState(null);

  // Deployment state
  const [deploymentStatus, setDeploymentStatus] = useState({});
  const [deploymentLoading, setDeploymentLoading] = useState(false);
  const [githubRepo, setGithubRepo] = useState('');
  const [systemHealth, setSystemHealth] = useState({});
  const [updateCheckResult, setUpdateCheckResult] = useState({});

  // Environment variables with fallbacks
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchStats();
    fetchMunicipalities();
    fetchTaxSales();
    fetchAllProperties(); // Fetch all properties for statistics header
  }, [selectedStatus, selectedMunicipality]);

  // Fetch deployment status when admin view is active
  useEffect(() => {
    if (activeView === 'admin' && isAdmin()) {
      fetchDeploymentStatus();
    }
  }, [activeView]);

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

  // Fetch ALL properties for statistics header (unfiltered)
  const fetchAllProperties = async () => {
    try {
      const response = await axios.get(`${API}/api/tax-sales`); // No filters - get all properties
      setAllProperties(response.data);
    } catch (error) {
      console.error("Error fetching all properties:", error);
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
    
    // Navigate to property details page with assessment number
    window.open(`/property/${property.assessment_number}`, '_blank');
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

  // Deployment functions
  const fetchDeploymentStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/deployment/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDeploymentStatus(response.data);
    } catch (error) {
      console.error('Error fetching deployment status:', error);
      setDeploymentStatus({ status: 'error', message: 'Failed to fetch deployment status' });
    }
  };

  const checkForUpdates = async () => {
    try {
      setDeploymentLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/api/deployment/check-updates`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUpdateCheckResult(response.data);
    } catch (error) {
      console.error('Error checking for updates:', error);
      setUpdateCheckResult({ updates_available: false, message: 'Error checking for updates' });
    } finally {
      setDeploymentLoading(false);
    }
  };

  const deployLatest = async () => {
    if (!window.confirm('This will deploy the latest version and may cause brief downtime. Continue?')) {
      return;
    }

    try {
      setDeploymentLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/api/deployment/deploy`, 
        { github_repo: githubRepo },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      alert('Deployment started successfully! Please monitor the system status.');
      fetchDeploymentStatus();
    } catch (error) {
      console.error('Error starting deployment:', error);
      alert('Error starting deployment: ' + (error.response?.data?.detail || error.message));
    } finally {
      setDeploymentLoading(false);
    }
  };

  const verifyDeployment = async () => {
    try {
      setDeploymentLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/api/deployment/verify`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert(response.data.message);
    } catch (error) {
      console.error('Error verifying deployment:', error);
      alert('Error verifying deployment: ' + (error.response?.data?.detail || error.message));
    } finally {
      setDeploymentLoading(false);
    }
  };

  const checkSystemHealth = async () => {
    try {
      setDeploymentLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/deployment/health`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSystemHealth(response.data);
    } catch (error) {
      console.error('Error checking system health:', error);
      setSystemHealth({ health_status: 'unknown', message: 'Failed to check system health' });
    } finally {
      setDeploymentLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="flex items-center space-x-4">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Tax Sale Compass</h1>
                  <p className="text-sm text-gray-600 font-medium">All tax sales. One platform.</p>
                </div>
                <Badge variant="secondary">Alpha</Badge>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Navigation matching live site */}
              <nav className="flex items-center space-x-6">
                <button 
                  onClick={logout}
                  className="text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center"
                >
                  <Home className="h-4 w-4 mr-1" />
                  Home
                </button>
                <button 
                  onClick={() => setActiveView('search')}
                  className={`text-sm font-medium ${activeView === 'search' ? 'text-blue-600' : 'text-gray-700 hover:text-gray-900'}`}
                >
                  Search
                </button>
                <button 
                  onClick={() => setActiveView('map')}
                  className={`text-sm font-medium ${activeView === 'map' ? 'text-blue-600' : 'text-gray-700 hover:text-gray-900'}`}
                >
                  Live Map
                </button>
                {isAdmin() && (
                  <button 
                    onClick={() => setActiveView('admin')}
                    className={`text-sm font-medium ${activeView === 'admin' ? 'text-blue-600' : 'text-gray-700 hover:text-gray-900'}`}
                  >
                    Admin
                  </button>
                )}
              </nav>
              
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

      {/* Statistics Header - Always shows total counts regardless of filters */}
      <div className="bg-gray-900 text-white py-3">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center items-center space-x-8 text-sm">
            <div className="flex items-center">
              <span className="text-gray-300">{municipalities.length} Municipalities</span>
            </div>
            <div className="flex items-center">
              <span className="font-semibold text-green-400">
                {allProperties.filter(p => p.status === 'active').length}
              </span>
              <span className="ml-1 text-gray-300">Active</span>
            </div>
            <div className="flex items-center">
              <span className="font-semibold text-yellow-400">
                {allProperties.filter(p => p.status === 'inactive').length}
              </span>
              <span className="ml-1 text-gray-300">Inactive</span>
            </div>
            <div className="flex items-center">
              <span className="font-semibold text-blue-400">{allProperties.length}</span>
              <span className="ml-1 text-gray-300">Total Properties</span>
            </div>
            <div className="flex items-center">
              <span className="font-semibold text-white">0</span>
              <span className="ml-1 text-gray-300">Scraped Today</span>
            </div>
            <div className="flex items-center">
              <span className="text-gray-300">Last:</span>
              <span className="ml-1 font-semibold text-white">2025-09-03</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Property Search View */}
        {activeView === 'search' && (
          <div className="space-y-6">
            {/* Title */}
            <h2 className="text-3xl font-bold text-gray-900">Tax Sale Properties</h2>
            
            {/* Search Controls - More compact like live site */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                {/* Search Input */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <input
                    type="text"
                    placeholder="Search Properties"
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

                {/* Status Filter */}
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="sold">Sold</option>
                  <option value="all">All Status</option>
                </select>

                <Button onClick={handleSearch} className="w-full">
                  Search Properties
                </Button>
              </div>
            </div>

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
                        className="cursor-pointer hover:shadow-lg transition-shadow duration-200 relative bg-white rounded-lg overflow-hidden"
                        onClick={() => handlePropertyClick(property)}
                      >
                        {/* Property Map Image */}
                        <div className="relative h-48 bg-gray-200">
                          {property.boundary_screenshot || property.latitude ? (
                            <img
                              src={property.boundary_screenshot?.startsWith('http') 
                                ? property.boundary_screenshot 
                                : `${API}/api/property-image/${property.assessment_number}?v=${Date.now()}`
                              }
                              alt={`Property map for ${property.property_address}`}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                // Fallback to Google Maps static image if boundary image fails
                                const lat = property.latitude || 44.6488;
                                const lng = property.longitude || -63.5752;
                                e.target.src = `https://maps.googleapis.com/maps/api/staticmap?center=${lat},${lng}&zoom=17&size=400x300&maptype=satellite&markers=color:blue%7C${lat},${lng}&key=AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY`;
                              }}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center bg-gray-100">
                              <MapPin className="h-12 w-12 text-gray-400" />
                            </div>
                          )}
                          
                          {/* Status Badges */}
                          <div className="absolute top-3 right-3 flex flex-col gap-2">
                            {/* Main Status Badge */}
                            <div className={`px-3 py-1 rounded-full text-sm font-bold ${
                              property.status === 'active' 
                                ? 'bg-green-100 text-green-800 border border-green-200' 
                                : property.status === 'inactive'
                                ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                                : property.status === 'sold'
                                ? 'bg-blue-100 text-blue-800 border border-blue-200'
                                : 'bg-gray-100 text-gray-800 border border-gray-200'
                            }`}>
                              {(property.status || 'active').toUpperCase()}
                            </div>
                            
                            {/* Auction Result Badge - Only show for inactive/sold properties */}
                            {(property.status === 'inactive' || property.status === 'sold') && property.auction_result && (
                              <div className={`px-3 py-1 rounded-full text-xs font-bold ${
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
                              </div>
                            )}
                          </div>
                        </div>

                        <CardContent className="p-6">
                          {/* Property Address */}
                          <h3 className="text-xl font-bold text-gray-900 mb-4">
                            {property.property_address}
                          </h3>

                          {/* Property Details */}
                          <div className="space-y-2 text-gray-600 mb-4">
                            <div className="flex justify-between">
                              <span>Assessment #:</span>
                              <span className="font-medium">{property.assessment_number}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>PID:</span>
                              <span className="font-medium">{property.pid_number}</span>
                            </div>
                          </div>

                          {/* Price */}
                          <div className="mb-4">
                            <div className="text-3xl font-bold text-green-600">
                              ${parseFloat(property.opening_bid || 0).toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                              })}
                            </div>
                            {property.auction_result === 'sold' && property.winning_bid_amount && (
                              <div className="mt-1">
                                <span className="text-sm text-gray-500">Final Sale: </span>
                                <span className="text-lg font-semibold text-blue-600">
                                  ${parseFloat(property.winning_bid_amount).toLocaleString('en-US', {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                  })}
                                </span>
                              </div>
                            )}
                          </div>

                          {/* Additional Info */}
                          <div className="space-y-2 text-gray-600 mb-6">
                            <div className="flex justify-between">
                              <span>Owner:</span>
                              <span className="font-medium text-right">{property.owner_name || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Municipality:</span>
                              <span className="font-medium">{property.municipality_name}</span>
                            </div>
                            {property.sale_date && (
                              <div className="flex justify-between">
                                <span>Sale Date:</span>
                                <span className="font-medium">{formatDate(property.sale_date)}</span>
                              </div>
                            )}
                          </div>

                          {/* Access Control Notice */}
                          {property.status === 'active' && !canViewActiveProperties() && (
                            <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
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
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg"
                            variant={property.status === 'active' && !canViewActiveProperties() ? "outline" : "default"}
                          >
                            {property.status === 'active' && !canViewActiveProperties() 
                              ? 'Upgrade to View Details' 
                              : 'See More Details →'
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
          </div>
        )}

        {/* Enhanced Interactive Map View */}
        {activeView === 'map' && (
          <div>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MapPin className="mr-2 h-5 w-5" />
                  Interactive Map with Property Boundaries
                </CardTitle>
                <CardDescription>
                  Explore tax sale properties on an interactive map with precise boundary visualization
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Map Controls */}
                  <div className="flex flex-wrap gap-4 items-center bg-slate-50 p-4 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <label className="text-sm font-medium">Municipality:</label>
                      <select
                        value={selectedMunicipality}
                        onChange={(e) => setSelectedMunicipality(e.target.value)}
                        className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">All Municipalities</option>
                        {municipalities.map((municipality) => (
                          <option key={municipality.id} value={municipality.name}>
                            {municipality.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <label className="text-sm font-medium">Status:</label>
                      <select
                        value={selectedStatus}
                        onChange={(e) => setSelectedStatus(e.target.value)}
                        className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                        <option value="sold">Sold</option>
                        <option value="all">All</option>
                      </select>
                    </div>
                    
                    <Button 
                      onClick={() => fetchTaxSales()} 
                      size="sm"
                      className="ml-auto"
                    >
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Refresh Map
                    </Button>
                  </div>

                  {/* Interactive Map */}
                  <div className="relative">
                    <Wrapper 
                      apiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY || "AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY"}
                      render={(status) => {
                        switch (status) {
                          case Status.LOADING:
                            return (
                              <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg">
                                <div className="text-center">
                                  <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400 mb-2" />
                                  <p className="text-gray-600">Loading Google Maps...</p>
                                </div>
                              </div>
                            );
                          case Status.FAILURE:
                            return (
                              <div className="flex items-center justify-center h-96 bg-red-50 border border-red-200 rounded-lg">
                                <div className="text-center">
                                  <MapPin className="h-8 w-8 mx-auto text-red-400 mb-2" />
                                  <p className="text-red-600">Failed to load Google Maps</p>
                                  <p className="text-sm text-red-500 mt-1">Please check your API key</p>
                                </div>
                              </div>
                            );
                          default:
                            return <InteractiveMap properties={taxSales} onPropertySelect={handlePropertyClick} />;
                        }
                      }}
                    />
                  </div>

                  {/* Map Legend */}
                  <div className="bg-white border rounded-lg p-4">
                    <h4 className="font-semibold mb-3">Map Legend</h4>
                    <div className="flex flex-wrap gap-4 text-sm">
                      <div className="flex items-center">
                        <div className="w-4 h-4 bg-green-500 rounded-full mr-2"></div>
                        <span>Active Properties</span>
                      </div>
                      <div className="flex items-center">
                        <div className="w-4 h-4 bg-gray-500 rounded-full mr-2"></div>
                        <span>Inactive Properties</span>
                      </div>
                      <div className="flex items-center">
                        <div className="w-4 h-4 bg-blue-500 rounded-full mr-2"></div>
                        <span>Sold Properties</span>
                      </div>
                      <div className="flex items-center">
                        <div className="w-4 h-4 bg-yellow-500 rounded-full mr-2"></div>
                        <span>Results Pending</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Statistics View */}
        {activeView === 'stats' && (
          <div>
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
          </div>
        )}

        {/* Admin View */}
        {activeView === 'admin' && isAdmin() && (
          <div>
              <div className="space-y-6">
                {/* Admin header */}
                <Card>
                  <CardHeader>
                    <CardTitle>Admin Dashboard</CardTitle>
                    <CardDescription>
                      Manage municipalities, monitor system status, and configure settings
                    </CardDescription>
                  </CardHeader>
                </Card>

                {/* Main layout: Quick Actions on left, content on right */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  {/* Quick Actions - Left sidebar column */}
                  <div className="lg:col-span-1">
                    <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50 h-fit sticky top-0">
                      <CardHeader>
                        <CardTitle>Quick Actions</CardTitle>
                        <CardDescription>
                          Common administrative tasks
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <Button className="w-full" size="sm">
                            <RefreshCw className="mr-2 h-4 w-4" />
                            Refresh Data
                          </Button>
                          <Button className="w-full" size="sm" variant="outline">
                            <Download className="mr-2 h-4 w-4" />
                            Export Data
                          </Button>
                          <Button className="w-full" size="sm" variant="outline">
                            <BarChart3 className="mr-2 h-4 w-4" />
                            View Analytics
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Right side content in rows */}
                  <div className="lg:col-span-3 space-y-6">
                  {/* Data Management - Full width row */}
                  <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                    <CardHeader>
                      <CardTitle>Data Management</CardTitle>
                      <CardDescription>
                        Manage tax sale data and municipalities
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Add Municipality */}
                        <div className="space-y-4">
                          <h4 className="font-semibold text-blue-800">Add Municipality</h4>
                          <div className="space-y-3">
                            <Input
                              placeholder="Municipality name"
                              value={newMunicipality.name}
                              onChange={(e) => setNewMunicipality({...newMunicipality, name: e.target.value})}
                            />
                            <Input
                              placeholder="Website URL"
                              value={newMunicipality.website_url}
                              onChange={(e) => setNewMunicipality({...newMunicipality, website_url: e.target.value})}
                            />
                            <select
                              value={newMunicipality.scraper_type}
                              onChange={(e) => setNewMunicipality({...newMunicipality, scraper_type: e.target.value})}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="halifax">Halifax</option>
                              <option value="victoria_county">Victoria County</option>
                            </select>
                            <Button onClick={handleAddMunicipality} className="w-full">
                              <Plus className="mr-2 h-4 w-4" />
                              Add Municipality
                            </Button>
                          </div>
                        </div>

                        {/* Municipalities List */}
                        <div className="space-y-4">
                          <h4 className="font-semibold text-blue-800">Current Municipalities</h4>
                          <div className="space-y-2 max-h-80 overflow-y-auto">
                            {municipalities.map((municipality) => (
                              <div key={municipality.id} className="bg-gray-50 rounded p-3 border">
                                <div className="font-medium">{municipality.name}</div>
                                <div className="text-sm text-gray-600">{municipality.scraper_type}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Auction Result Management - Full width row */}
                  <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                    <CardHeader>
                      <CardTitle>Auction Result Management</CardTitle>
                      <CardDescription>
                        Update auction results for properties after sales
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        {/* Quick Stats - Horizontal row */}
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
                          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                            <div className="text-3xl font-bold text-yellow-800">
                              {taxSales.filter(prop => prop.auction_result === 'pending').length}
                            </div>
                            <div className="text-sm text-yellow-600 font-medium">Pending</div>
                          </div>
                          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                            <div className="text-3xl font-bold text-blue-800">
                              {taxSales.filter(prop => prop.auction_result === 'sold').length}
                            </div>
                            <div className="text-sm text-blue-600 font-medium">Sold</div>
                          </div>
                          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                            <div className="text-3xl font-bold text-red-800">
                              {taxSales.filter(prop => prop.auction_result === 'canceled').length}
                            </div>
                            <div className="text-sm text-red-600 font-medium">Canceled</div>
                          </div>
                          <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                            <div className="text-3xl font-bold text-orange-800">
                              {taxSales.filter(prop => prop.auction_result === 'deferred').length}
                            </div>
                            <div className="text-sm text-orange-600 font-medium">Deferred</div>
                          </div>
                          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                            <div className="text-3xl font-bold text-green-800">
                              {taxSales.filter(prop => prop.auction_result === 'taxes_paid').length}
                            </div>
                            <div className="text-sm text-green-600 font-medium">Redeemed</div>
                          </div>
                        </div>

                        {/* Properties Pending Results */}
                        {taxSales.filter(prop => prop.auction_result === 'pending').length > 0 && (
                          <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200">
                            <h4 className="font-semibold text-yellow-800 mb-4 text-lg">Properties with Pending Results</h4>
                            <div className="space-y-3 max-h-80 overflow-y-auto">
                              {taxSales
                                .filter(prop => prop.auction_result === 'pending')
                                .map(property => (
                                  <div key={property.id} className="bg-white rounded border p-4 shadow-sm">
                                    <div className="flex justify-between items-start">
                                      <div className="flex-1">
                                        <div className="font-medium text-lg">{property.property_address}</div>
                                        <div className="text-sm text-gray-600 mt-1">
                                          Assessment: {property.assessment_number} | 
                                          Opening Bid: ${parseFloat(property.opening_bid || 0).toLocaleString()}
                                        </div>
                                        {property.sale_date && (
                                          <div className="text-sm text-gray-500 mt-1">
                                            Auction Date: {formatDate(property.sale_date)}
                                          </div>
                                        )}
                                      </div>
                                      <Button
                                        size="sm"
                                        onClick={() => setSelectedPropertyForResult(property)}
                                        className="ml-4"
                                      >
                                        Update Result
                                      </Button>
                                    </div>
                                  </div>
                                ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* System Status - Full width row */}
                  <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                    <CardHeader>
                      <CardTitle>System Status</CardTitle>
                      <CardDescription>
                        Monitor system health and performance
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        <div className="bg-green-50 rounded-lg p-4 text-center border border-green-200">
                          <div className="text-2xl font-bold text-green-600">✅</div>
                          <div className="text-sm font-medium text-gray-700 mt-2">Frontend</div>
                          <div className="text-xs text-green-600">Running</div>
                        </div>
                        <div className="bg-green-50 rounded-lg p-4 text-center border border-green-200">
                          <div className="text-2xl font-bold text-green-600">✅</div>
                          <div className="text-sm font-medium text-gray-700 mt-2">Backend</div>
                          <div className="text-xs text-green-600">Running</div>
                        </div>
                        <div className="bg-green-50 rounded-lg p-4 text-center border border-green-200">
                          <div className="text-2xl font-bold text-green-600">✅</div>
                          <div className="text-sm font-medium text-gray-700 mt-2">Database</div>
                          <div className="text-xs text-green-600">Connected</div>
                        </div>
                        <div className="bg-blue-50 rounded-lg p-4 text-center border border-blue-200">
                          <div className="text-2xl font-bold text-blue-600">{stats.total_properties || 0}</div>
                          <div className="text-sm font-medium text-gray-700 mt-2">Properties</div>
                          <div className="text-xs text-blue-600">Total Count</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Deployment Management - Full width row */}
                  <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <RefreshCw className="mr-2 h-5 w-5 text-green-600" />
                        Deployment Management
                      </CardTitle>
                      <CardDescription>
                        Safely deploy updates to your VPS with automatic backup and rollback
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        {/* Current Status */}
                        <div className="bg-slate-50 rounded-lg p-4 border">
                          <h4 className="font-semibold text-slate-800 mb-3">Current Status</h4>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="text-center">
                              <div className="text-sm text-gray-600">Deployment Status</div>
                              <div className={`font-semibold ${
                                deploymentStatus.status === 'success' ? 'text-green-600' : 
                                deploymentStatus.status === 'error' ? 'text-red-600' : 'text-yellow-600'
                              }`}>
                                {deploymentStatus.status?.toUpperCase() || 'UNKNOWN'}
                              </div>
                            </div>
                            <div className="text-center">
                              <div className="text-sm text-gray-600">System Health</div>
                              <div className={`font-semibold ${
                                systemHealth.health_status === 'excellent' ? 'text-green-600' :
                                systemHealth.health_status === 'good' ? 'text-blue-600' :
                                systemHealth.health_status === 'fair' ? 'text-yellow-600' :
                                systemHealth.health_status === 'poor' ? 'text-red-600' : 'text-gray-600'
                              }`}>
                                {systemHealth.health_status?.toUpperCase() || 'UNKNOWN'}
                              </div>
                            </div>
                            <div className="text-center">
                              <div className="text-sm text-gray-600">Updates Available</div>
                              <div className={`font-semibold ${
                                updateCheckResult.updates_available ? 'text-orange-600' : 'text-green-600'
                              }`}>
                                {updateCheckResult.updates_available ? 'YES' : 'NO'}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* GitHub Repository */}
                        <div className="space-y-3">
                          <h4 className="font-semibold text-slate-800">GitHub Repository URL</h4>
                          <Input
                            placeholder="https://github.com/username/repository.git"
                            value={githubRepo}
                            onChange={(e) => setGithubRepo(e.target.value)}
                            className="max-w-md"
                          />
                          <p className="text-sm text-gray-600">
                            Enter your GitHub repository URL for automatic updates
                          </p>
                        </div>

                        {/* Action Buttons */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <Button
                            onClick={checkForUpdates}
                            disabled={deploymentLoading}
                            className="bg-blue-600 hover:bg-blue-700"
                          >
                            {deploymentLoading ? (
                              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                              <RefreshCw className="mr-2 h-4 w-4" />
                            )}
                            Check Updates
                          </Button>

                          <Button
                            onClick={deployLatest}
                            disabled={deploymentLoading || !githubRepo}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            {deploymentLoading ? (
                              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                              <Download className="mr-2 h-4 w-4" />
                            )}
                            Deploy Latest
                          </Button>

                          <Button
                            onClick={verifyDeployment}
                            disabled={deploymentLoading}
                            className="bg-purple-600 hover:bg-purple-700"
                          >
                            {deploymentLoading ? (
                              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                              <Check className="mr-2 h-4 w-4" />
                            )}
                            Verify Status
                          </Button>

                          <Button
                            onClick={checkSystemHealth}
                            disabled={deploymentLoading}
                            className="bg-orange-600 hover:bg-orange-700"
                          >
                            {deploymentLoading ? (
                              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                              <BarChart3 className="mr-2 h-4 w-4" />
                            )}
                            Health Check
                          </Button>
                        </div>

                        {/* Warning Message */}
                        <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                          <div className="flex items-start">
                            <div className="text-yellow-600 mr-3 mt-0.5">⚠️</div>
                            <div>
                              <div className="font-semibold text-yellow-800">Important Notice</div>
                              <div className="text-sm text-yellow-700 mt-1">
                                Deployment will cause brief downtime (30-60 seconds). Automatic backup and rollback are enabled for safety.
                                Always test in a staging environment first when possible.
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Status Messages */}
                        {deploymentStatus.message && (
                          <div className={`rounded-lg p-4 border ${
                            deploymentStatus.status === 'success' ? 'bg-green-50 border-green-200' :
                            deploymentStatus.status === 'error' ? 'bg-red-50 border-red-200' :
                            'bg-blue-50 border-blue-200'
                          }`}>
                            <div className="text-sm">
                              <strong>Last Status:</strong> {deploymentStatus.message}
                            </div>
                            {deploymentStatus.last_check && (
                              <div className="text-xs text-gray-600 mt-1">
                                Checked: {new Date(deploymentStatus.last_check).toLocaleString()}
                              </div>
                            )}
                          </div>
                        )}

                        {systemHealth.output && (
                          <div className="bg-gray-50 rounded-lg p-4 border">
                            <div className="text-sm font-semibold text-gray-800 mb-2">System Health Details:</div>
                            <pre className="text-xs text-gray-700 whitespace-pre-wrap max-h-40 overflow-y-auto">
                              {systemHealth.output}
                            </pre>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                  </div>
                </div>
              </div>
          </div>
        )}
      </div>

      {/* Property Details Modal - Removed in favor of routing */}

      {/* Auction Result Modal */}
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

      {/* Auction Result Update Modal */}
      {selectedPropertyForResult && (
        <AuctionResultModal
          isOpen={selectedPropertyForResult !== null}
          property={selectedPropertyForResult}
          onClose={() => setSelectedPropertyForResult(null)}
          onUpdate={() => {
            fetchTaxSales();
            fetchStats();
            setSelectedPropertyForResult(null);
          }}
        />
      )}
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
            <Route path="/property/:assessmentNumber" element={<PropertyDetails />} />
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
      const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
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