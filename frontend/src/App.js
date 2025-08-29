import React, { useState, useEffect, useCallback, useRef } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import "./App.css";
import axios from "axios";
import { Search, MapPin, Calendar, DollarSign, Building2, BarChart3, RefreshCw, Download, Gavel, Users, Clock, Plus, Edit, Save, X, Home, Trash2 } from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Wrapper, Status } from "@googlemaps/react-wrapper";
import PropertyDetails from './components/PropertyDetails';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const GOOGLE_MAPS_API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;

// Google Maps component with NSPRD boundary overlays
const GoogleMapComponent = ({ properties, onMarkerClick }) => {
  const mapRef = useRef();
  const [map, setMap] = useState(null);
  const [markers, setMarkers] = useState([]);
  const [boundaryPolygons, setBoundaryPolygons] = useState([]);

  const onLoad = useCallback((map) => {
    mapRef.current = map;
    setMap(map);
  }, []);

  const onUnmount = useCallback(() => {
    mapRef.current = null;
    setMap(null);
  }, []);

  // Update markers and boundaries when properties change
  useEffect(() => {
    if (!map || !properties.length) return;

    // Clear existing markers and polygons
    markers.forEach(marker => marker.setMap(null));
    boundaryPolygons.forEach(polygon => polygon.setMap(null));
    const newMarkers = [];
    const newPolygons = [];

    // Add markers and boundaries for each property
    properties.forEach((property) => {
      if (property.latitude && property.longitude) {
        // Determine marker color based on property type
        let iconColor = '#dc2626'; // Red for tax sale properties
        const propertyType = property.property_description?.toLowerCase() || '';
        
        if (propertyType.includes('commercial') || propertyType.includes('business')) {
          iconColor = '#f59e0b'; // Orange
        } else if (propertyType.includes('land') || propertyType.includes('lot')) {
          iconColor = '#10b981'; // Green
        }

        const marker = new window.google.maps.Marker({
          position: { lat: property.latitude, lng: property.longitude },
          map: map,
          title: property.property_address || property.address || 'Tax Sale Property',
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            fillColor: iconColor,
            fillOpacity: 0.9,
            strokeColor: 'white',
            strokeWeight: 2,
            scale: 8
          }
        });

        // Add click event for marker
        marker.addListener('click', () => {
          if (onMarkerClick) {
            onMarkerClick(property);
          }
        });

        // Create info window with enhanced property details
        const infoWindow = new window.google.maps.InfoWindow({
          content: `
            <div style="max-width: 280px;">
              <h3 style="margin: 0 0 8px 0; color: #1f2937; font-size: 14px;">${property.property_address || 'Tax Sale Property'}</h3>
              <p style="margin: 4px 0; color: #6b7280; font-size: 12px;"><strong>PID:</strong> ${property.pid_number || 'N/A'}</p>
              <p style="margin: 4px 0; color: #6b7280; font-size: 12px;"><strong>Assessment:</strong> ${property.assessment_number || 'N/A'}</p>
              <p style="margin: 4px 0; color: #6b7280; font-size: 12px;"><strong>Opening Bid:</strong> $${parseFloat(property.opening_bid || 0).toLocaleString()}</p>
              <p style="margin: 4px 0; color: #6b7280; font-size: 12px;"><strong>Municipality:</strong> ${property.municipality_name || 'N/A'}</p>
              ${property.government_boundary_data ? `<p style="margin: 4px 0; color: #16a34a; font-size: 12px;"><strong>Area:</strong> ${Math.round(property.government_boundary_data.area_sqm || 0).toLocaleString()} sqm</p>` : ''}
              <div style="margin-top: 8px;">
                <button 
                  onclick="window.open('/property/${property.assessment_number}', '_blank')"
                  style="padding: 4px 8px; background: #dc2626; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;"
                >
                  View Details
                </button>
              </div>
            </div>
          `
        });

        marker.addListener('click', () => {
          infoWindow.open(map, marker);
        });

        newMarkers.push(marker);

        // Add property boundary polygon if PID exists
        if (property.pid_number) {
          // Fetch and display NSPRD boundary polygon
          fetch(`${BACKEND_URL}/api/query-ns-government-parcel/${property.pid_number}`)
            .then(response => response.json())
            .then(data => {
              if (data.found && data.geometry && data.geometry.rings) {
                // Convert NSPRD polygon to Google Maps format
                const paths = data.geometry.rings.map(ring => 
                  ring.map(coord => ({ lat: coord[1], lng: coord[0] }))
                );
                
                // Create property boundary polygon with tax sale styling
                const propertyPolygon = new window.google.maps.Polygon({
                  paths: paths,
                  strokeColor: iconColor,
                  strokeOpacity: 0.8,
                  strokeWeight: 2,
                  fillColor: iconColor,
                  fillOpacity: 0.15,
                  map: map,
                  clickable: true
                });
                
                // Make polygon clickable to show same info as marker
                propertyPolygon.addListener('click', () => {
                  infoWindow.setPosition({ lat: property.latitude, lng: property.longitude });
                  infoWindow.open(map);
                });

                // Add hover effect
                propertyPolygon.addListener('mouseover', () => {
                  propertyPolygon.setOptions({
                    strokeOpacity: 1.0,
                    fillOpacity: 0.25,
                    strokeWeight: 3
                  });
                });

                propertyPolygon.addListener('mouseout', () => {
                  propertyPolygon.setOptions({
                    strokeOpacity: 0.8,
                    fillOpacity: 0.15,
                    strokeWeight: 2
                  });
                });

                // Add polygon to state immediately when loaded
                console.log(`Adding polygon for PID ${property.pid_number} to map`);
                setBoundaryPolygons(current => [...current, propertyPolygon]);
              } else {
                console.log(`No boundary geometry found for PID ${property.pid_number}:`, data);
              }
            })
            .catch(error => {
              console.warn(`Could not load boundary for PID ${property.pid_number}:`, error);
            });
        }
      }
    });

    setMarkers(newMarkers);
    // Clear existing boundary polygons at start, new ones will be added as they load
    setBoundaryPolygons([]);

    // Adjust map bounds to show all properties
    if (newMarkers.length > 0) {
      const bounds = new window.google.maps.LatLngBounds();
      newMarkers.forEach(marker => {
        bounds.extend(marker.getPosition());
      });
      map.fitBounds(bounds);
      
      // Don't zoom in too much for single properties
      const listener = window.google.maps.event.addListener(map, 'bounds_changed', () => {
        if (map.getZoom() > 15) map.setZoom(15);
        window.google.maps.event.removeListener(listener);
      });
    }
  }, [map, properties, onMarkerClick]);

  return (
    <div 
      style={{ height: '400px', width: '100%' }}
      ref={(node) => {
        if (node && !map) {
          const mapInstance = new window.google.maps.Map(node, {
            center: { lat: 44.6488, lng: -63.5752 }, // Halifax center
            zoom: 8,
            mapTypeControl: true,
            streetViewControl: true,
            fullscreenControl: true,
            zoomControl: true,
            styles: [
              {
                featureType: "poi",
                elementType: "labels",
                stylers: [{ visibility: "off" }]
              }
            ]
          });
          setMap(mapInstance);
        }
      }}
    />
  );
};

// Google Maps Wrapper with loading states
const MapWrapper = ({ properties, onMarkerClick }) => {
  const render = (status) => {
    switch (status) {
      case Status.LOADING:
        return <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-gray-600">Loading Google Maps...</p>
          </div>
        </div>;
      case Status.FAILURE:
        return <div className="flex items-center justify-center h-96 bg-red-50 rounded-lg border border-red-200">
          <div className="text-center text-red-600">
            <p>Failed to load Google Maps</p>
            <p className="text-sm mt-1">Please check your internet connection</p>
          </div>
        </div>;
      default:
        return <GoogleMapComponent properties={properties} onMarkerClick={onMarkerClick} />;
    }
  };

  return (
    <Wrapper apiKey={GOOGLE_MAPS_API_KEY} render={render}>
      <GoogleMapComponent properties={properties} onMarkerClick={onMarkerClick} />
    </Wrapper>
  );
};

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<MainApp />} />
          <Route path="/property/:assessmentNumber" element={<PropertyDetails />} />
        </Routes>
      </div>
    </Router>
  );
}

function MainApp() {
  const [taxSales, setTaxSales] = useState([]);
  const [municipalities, setMunicipalities] = useState([]);
  const [mapData, setMapData] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMunicipality, setSelectedMunicipality] = useState("");
  const [selectedStatus, setSelectedStatus] = useState('active'); // New status filter state
  const [scrapeStatus, setScrapeStatus] = useState("");
  
  // Municipality management state
  const [editingMunicipality, setEditingMunicipality] = useState(null);
  const [showAddMunicipality, setShowAddMunicipality] = useState(false);
  const [newMunicipality, setNewMunicipality] = useState({ 
    name: '', 
    scraper_type: 'generic', 
    website_url: '', 
    tax_sale_url: '', 
    region: '',
    scrape_enabled: true,
    scrape_frequency: 'weekly',
    scrape_day_of_week: 1,
    scrape_day_of_month: 1,
    scrape_time_hour: 2,
    scrape_time_minute: 0
  });

  // Fetch initial data and refresh when filters change
  useEffect(() => {
    fetchStats();
    fetchMunicipalities();
    fetchTaxSales();
    fetchMapData();
  }, [selectedStatus, selectedMunicipality]); // Refetch when status or municipality changes

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const fetchMunicipalities = async () => {
    try {
      const response = await axios.get(`${API}/municipalities`);
      setMunicipalities(response.data);
    } catch (error) {
      console.error("Error fetching municipalities:", error);
    }
  };

  const fetchTaxSales = async (municipality = "", query = "") => {
    setLoading(true);
    try {
      let url = `${API}/tax-sales`;
      const params = new URLSearchParams();
      
      if (municipality) {
        params.append("municipality", municipality);
      }
      if (selectedStatus) {
        params.append("status", selectedStatus);
      }
      if (query) {
        url = `${API}/tax-sales/search`;
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

  const fetchMapData = async () => {
    try {
      // Use full tax sales data for map instead of simplified map-data endpoint
      let url = `${API}/tax-sales`;
      const params = new URLSearchParams();
      
      if (selectedStatus && selectedStatus !== 'all') {
        params.append('status', selectedStatus);
      }
      
      if (selectedMunicipality) {
        params.append('municipality', selectedMunicipality);
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await axios.get(url);
      setMapData(response.data);
    } catch (error) {
      console.error("Error fetching map data:", error);
    }
  };

  const handleAddMunicipality = async () => {
    if (!newMunicipality.name.trim() || !newMunicipality.website_url.trim()) return;
    
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/municipalities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newMunicipality)
      });
      
      if (response.ok) {
        setNewMunicipality({ 
          name: '', 
          scraper_type: 'generic', 
          website_url: '', 
          tax_sale_url: '', 
          region: '' 
        });
        setShowAddMunicipality(false);
        fetchMunicipalities(); // Refresh the list
        alert('Municipality added successfully!');
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail || 'Failed to add municipality'}`);
      }
    } catch (error) {
      console.error('Error adding municipality:', error);
      alert('Error adding municipality. Please try again.');
    }
  };

  const handleEditMunicipality = async (municipality) => {
    if (!municipality.name.trim() || !municipality.website_url.trim()) return;
    
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/municipalities/${municipality.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(municipality)
      });
      
      if (response.ok) {
        setEditingMunicipality(null);
        fetchMunicipalities(); // Refresh the list
        alert('Municipality updated successfully!');
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail || 'Failed to update municipality'}`);
      }
    } catch (error) {
      console.error('Error editing municipality:', error);
      alert('Error updating municipality. Please try again.');
    }
  };

  const handleDeleteMunicipality = async (municipalityId, municipalityName) => {
    if (!window.confirm(`Are you sure you want to delete "${municipalityName}"? This will also delete all associated tax sale properties.`)) {
      return;
    }
    
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/municipalities/${municipalityId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const result = await response.json();
        fetchMunicipalities(); // Refresh the list
        fetchStats(); // Refresh stats
        alert(result.message);
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail || 'Failed to delete municipality'}`);
      }
    } catch (error) {
      console.error('Error deleting municipality:', error);
      alert('Error deleting municipality. Please try again.');
    }
  };

  const handleSearch = async () => {
    await fetchTaxSales(selectedMunicipality, searchQuery);
    await fetchMapData();
  };

  const initializeMunicipalities = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/init-municipalities`);
      await fetchMunicipalities();
      await fetchStats();
      setScrapeStatus("Municipalities initialized successfully!");
    } catch (error) {
      console.error("Error initializing municipalities:", error);
      setScrapeStatus("Failed to initialize municipalities.");
    } finally {
      setLoading(false);
    }
  };

  const scrapeHalifax = async () => {
    setLoading(true);
    setScrapeStatus("Scraping Halifax tax sales...");
    try {
      const response = await axios.post(`${API}/scrape/halifax`);
      console.log("Halifax scraping results:", response.data);
      await fetchTaxSales();
      await fetchStats();
      await fetchMapData();
      setScrapeStatus(`Halifax scraping completed! ${response.data.properties_scraped} properties processed.`);
    } catch (error) {
      console.error("Error scraping Halifax:", error);
      setScrapeStatus("Halifax scraping failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const scrapeAllMunicipalities = async () => {
    setLoading(true);
    setScrapeStatus("Scraping all municipalities...");
    try {
      const response = await axios.post(`${API}/scrape-all`);
      console.log("All scraping results:", response.data);
      await fetchTaxSales();
      await fetchStats();
      await fetchMapData();
      setScrapeStatus("Scraping completed for all municipalities!");
    } catch (error) {
      console.error("Error scraping municipalities:", error);
      setScrapeStatus("Some scraping operations failed. Check logs for details.");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    if (!amount) return "N/A";
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString('en-CA');
  };

  const getMunicipalityTaxSaleUrl = (municipalityName) => {
    const municipalityLinks = {
      'Halifax Regional Municipality': 'https://www.halifax.ca/home-property/property-taxes/tax-sale',
      'Cape Breton Regional Municipality': 'https://www.cbrm.ns.ca',
      'Truro': 'https://www.truro.ca',
      'New Glasgow': 'https://www.newglasgow.ca',
      'Bridgewater': 'https://www.bridgewater.ca',
      'Yarmouth': 'https://www.townofyarmouth.ca',
      'Kentville': 'https://www.kentville.ca',
      'Antigonish': 'https://www.townofantigonish.ca'
    };
    return municipalityLinks[municipalityName] || '#';
  };

  const renderMunicipalityLink = (municipalityName) => {
    const url = getMunicipalityTaxSaleUrl(municipalityName);
    
    if (url === '#') {
      return <span>{municipalityName}</span>;
    }
    
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 hover:text-blue-800 hover:underline transition-colors cursor-pointer"
        title={`View tax sales on ${municipalityName} website`}
      >
        🏛️ {municipalityName}
      </a>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Building2 className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">NS Tax Sales</h1>
                <p className="text-sm text-slate-600">Nova Scotia Municipality Tax Sale Aggregator - Live Data</p>
              </div>
            </div>
            
            {/* Enhanced Stats Display */}
            {stats && (
              <div className="hidden md:flex items-center space-x-6 text-sm text-slate-600">
                <div className="flex items-center space-x-2">
                  <Building2 className="h-4 w-4 text-blue-500" />
                  <span>{stats.total_municipalities} Municipalities</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Gavel className="h-4 w-4 text-green-500" />
                  <span>{stats.active_properties || 0} Active</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-red-500" />
                  <span>{stats.inactive_properties || 0} Inactive</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Home className="h-4 w-4 text-orange-500" />
                  <span>{stats.total_properties} Total Properties</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-green-500" />
                  <span>{stats.scraped_today} Scraped Today</span>
                </div>
                {stats.last_scrape && (
                  <div className="flex items-center space-x-2">
                    <RefreshCw className="h-4 w-4 text-purple-500" />
                    <span>Last: {formatDate(stats.last_scrape)}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="search" className="w-full">
          <TabsList className="grid w-full grid-cols-3 lg:w-96 mx-auto mb-8">
            <TabsTrigger value="search" className="flex items-center space-x-2">
              <Search className="h-4 w-4" />
              <span>Search</span>
            </TabsTrigger>
            <TabsTrigger value="map" className="flex items-center space-x-2">
              <MapPin className="h-4 w-4" />
              <span>Live Map</span>
            </TabsTrigger>
            <TabsTrigger value="admin" className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Admin</span>
            </TabsTrigger>
          </TabsList>

          {/* Search Tab */}
          <TabsContent value="search">
            {/* Search Controls */}
            <Card className="mb-8 bg-white/80 backdrop-blur-sm border-slate-200/50">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Search className="h-5 w-5 text-blue-600" />
                  <span>Search Tax Sale Properties</span>
                </CardTitle>
                <CardDescription>
                  Find tax sale properties across Nova Scotia municipalities with real-time data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
                  <div className="flex-1">
                    <Input
                      placeholder="Search by address, owner name, or property details..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-white/80"
                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    />
                  </div>
                  <div className="sm:w-48">
                    <select
                      value={selectedMunicipality}
                      onChange={(e) => setSelectedMunicipality(e.target.value)}
                      className="w-full px-3 py-2 bg-white/80 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">All Municipalities</option>
                      {municipalities.map((muni) => (
                        <option key={muni.id} value={muni.name}>
                          {muni.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="sm:w-40">
                    <select
                      value={selectedStatus}
                      onChange={(e) => setSelectedStatus(e.target.value)}
                      className="w-full px-3 py-2 bg-white/80 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      title="Filter properties by status"
                    >
                      <option value="active">🟢 Active</option>
                      <option value="inactive">🔴 Inactive</option>
                      <option value="all">📋 All Properties</option>
                    </select>
                  </div>
                  <Button 
                    onClick={handleSearch}
                    disabled={loading}
                    className="sm:w-auto bg-blue-600 hover:bg-blue-700"
                  >
                    <Search className="h-4 w-4 mr-2" />
                    Search
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Tax Sale Results */}
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-slate-600">Loading tax sales...</span>
              </div>
            ) : (
              <div className="grid gap-6">
                {taxSales.length === 0 ? (
                  <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                    <CardContent className="py-12 text-center">
                      <Gavel className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-slate-900 mb-2">No Tax Sales Found</h3>
                      <p className="text-slate-600 mb-4">
                        Try scraping Halifax data or adjusting your search criteria.
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  taxSales.map((property) => (
                    <Card key={property.id} className="bg-white/80 backdrop-blur-sm border-slate-200/50 hover:shadow-lg transition-shadow">
                      <div className="flex">
                        {/* Property Boundary Thumbnail from viewpoint.ca */}
                        <div className="w-32 h-32 flex-shrink-0">
                          {property.boundary_screenshot ? (
                            <div className="relative w-full h-full rounded-l-lg overflow-hidden">
                              <img
                                src={`${process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL}/api/boundary-image/${property.boundary_screenshot}`}
                                alt={`Property boundary map of ${property.property_address}`}
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                  // Fallback to coordinates-based placeholder
                                  e.target.style.display = 'none';
                                  e.target.parentNode.innerHTML = '<div class="w-full h-full bg-gradient-to-br from-blue-100 to-green-100 flex items-center justify-center"><div class="text-center text-gray-600"><div class="text-xl mb-1">🗺️</div><div class="text-xs">Boundary Map</div></div></div>';
                                }}
                              />
                              <div className="absolute bottom-1 right-1 bg-black bg-opacity-70 text-white text-xs px-1 rounded">
                                Boundaries
                              </div>
                            </div>
                          ) : property.latitude && property.longitude ? (
                            <div className="w-full h-full bg-gradient-to-br from-blue-100 to-green-100 rounded-l-lg flex items-center justify-center">
                              <div className="text-center text-gray-600">
                                <div className="text-xl mb-1">🗺️</div>
                                <div className="text-xs">Capture Available</div>
                              </div>
                            </div>
                          ) : (
                            <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 rounded-l-lg flex items-center justify-center">
                              <div className="text-center text-gray-500">
                                <div className="text-2xl mb-1">🏠</div>
                                <div className="text-xs">No Map</div>
                              </div>
                            </div>
                          )}
                        </div>
                        
                        {/* Property Content */}
                        <div className="flex-1">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <CardTitle className="text-lg text-slate-900">
                                {property.property_address}
                              </CardTitle>
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                property.status === 'active' 
                                  ? 'bg-green-100 text-green-800' 
                                  : property.status === 'inactive'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}>
                                {property.status === 'active' ? '🟢 Active' : 
                                 property.status === 'inactive' ? '🔴 Inactive' : 
                                 '⚪ Unknown'}
                              </span>
                            </div>
                            <CardDescription className="flex items-center space-x-4 mt-1">
                              <div className="flex items-center space-x-2">
                                <MapPin className="h-4 w-4 text-slate-500" />
                                {renderMunicipalityLink(property.municipality_name)}
                              </div>
                              {property.assessment_number && (
                                <a
                                  href={`https://webapi.pvsc.ca/Search/Property?ain=${property.assessment_number}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 transition-colors cursor-pointer"
                                  title="View full property assessment on PVSC"
                                >
                                  <span className="text-xs font-medium">📋 AAN: {property.assessment_number}</span>
                                </a>
                              )}
                            </CardDescription>
                          </div>
                          <div className="flex flex-col items-end space-y-2">
                            <Badge 
                              variant="outline" 
                              className={
                                property.property_type === 'Dwelling' || property.property_type === 'Residential' 
                                  ? "bg-blue-50 text-blue-700 border-blue-200"
                                  : property.property_type === 'Commercial' 
                                  ? "bg-orange-50 text-orange-700 border-orange-200"
                                  : "bg-green-50 text-green-700 border-green-200"
                              }
                            >
                              {property.property_type || 'Property'}
                            </Badge>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {property.opening_bid && (
                            <div className="flex items-center space-x-2">
                              <Gavel className="h-4 w-4 text-blue-500" />
                              <div>
                                <p className="text-sm text-slate-600">Opening Bid</p>
                                <p className="font-semibold text-blue-600">
                                  {formatCurrency(property.opening_bid)}
                                </p>
                              </div>
                            </div>
                          )}

                          {property.tax_owing && (
                            <div className="flex items-center space-x-2">
                              <DollarSign className="h-4 w-4 text-red-500" />
                              <div>
                                <p className="text-sm text-slate-600">Tax Owing</p>
                                <p className="font-semibold text-red-600">
                                  {formatCurrency(property.tax_owing)}
                                </p>
                              </div>
                            </div>
                          )}
                          
                          {property.assessment_value && (
                            <div className="flex items-center space-x-2">
                              <Building2 className="h-4 w-4 text-purple-500" />
                              <div>
                                <p className="text-sm text-slate-600">Assessment</p>
                                <p className="font-semibold text-purple-600">
                                  {formatCurrency(property.assessment_value)}
                                </p>
                              </div>
                            </div>
                          )}
                          
                          {property.sale_date && (
                            <div className="flex items-center space-x-2">
                              <Calendar className="h-4 w-4 text-orange-500" />
                              <div>
                                <p className="text-sm text-slate-600">Sale Date</p>
                                <p className="font-semibold text-orange-600">
                                  {formatDate(property.sale_date)}
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                        
                        {/* Owner Information */}
                        {property.owner_name && (
                          <div className="mt-4 p-3 bg-slate-50/80 rounded-lg">
                            <div className="flex items-center space-x-2 mb-1">
                              <Users className="h-4 w-4 text-slate-600" />
                              <span className="text-sm font-medium text-slate-700">Owner</span>
                            </div>
                            <p className="text-sm text-slate-600">{property.owner_name}</p>
                          </div>
                        )}

                        {/* Property Description */}
                        {property.property_description && (
                          <div className="mt-4 p-3 bg-blue-50/80 rounded-lg">
                            <p className="text-sm text-slate-700">{property.property_description}</p>
                          </div>
                        )}

                        {/* Additional Details with Links */}
                        <div className="mt-4 flex flex-wrap gap-2 text-xs">
                          {property.pid_number && (
                            <a
                              href={`https://www.viewpoint.ca/show/property/${property.pid_number}/1/${property.property_address.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '').substring(0, 50)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="bg-blue-100 text-blue-700 px-2 py-1 rounded hover:bg-blue-200 transition-colors cursor-pointer"
                              title="View property details on Viewpoint.ca"
                            >
                              📍 PID: {property.pid_number}
                            </a>
                          )}
                          {property.assessment_number && (
                            <a
                              href={`https://webapi.pvsc.ca/Search/Property?ain=${property.assessment_number}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200 transition-colors cursor-pointer"
                              title="View property assessment on PVSC"
                            >
                              📋 AAN: {property.assessment_number}
                            </a>
                          )}
                          {property.sale_time && (
                            <span className="bg-slate-100 text-slate-600 px-2 py-1 rounded">⏰ Time: {property.sale_time}</span>
                          )}
                          {property.sale_location && (
                            <span className="bg-slate-100 text-slate-600 px-2 py-1 rounded">🏛️ Location: {property.sale_location}</span>
                          )}
                        </div>

                        {/* Redeemable and HST Information */}
                        {(property.redeemable || property.hst_applicable) && (
                          <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                            <h4 className="font-semibold text-amber-800 text-sm mb-2">⚠️ Important Legal Information</h4>
                            {property.redeemable && (
                              <div className="mb-2">
                                <span className="text-xs font-medium text-amber-700">🔄 Redemption:</span>
                                <p className="text-xs text-amber-700">{property.redeemable}</p>
                              </div>
                            )}
                            {property.hst_applicable && (
                              <div>
                                <span className="text-xs font-medium text-amber-700">💰 HST:</span>
                                <p className="text-xs text-amber-700">{property.hst_applicable}</p>
                              </div>
                            )}
                          </div>
                        )}

                        {/* See More Details Button */}
                        <div className="mt-6 pt-4 border-t border-slate-200">
                          <Link
                            to={`/property/${property.assessment_number}`}
                            className="block w-full text-center bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                          >
                            See More Details →
                          </Link>
                        </div>
                      </CardContent>
                        </div>  {/* Close flex-1 div */}
                      </div>  {/* Close flex container */}
                    </Card>
                  ))
                )}
              </div>
            )}
          </TabsContent>

          {/* Enhanced Interactive Map Tab */}
          <TabsContent value="map">
            <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <MapPin className="h-5 w-5 text-blue-600" />
                    <span>Live Tax Sale Properties Map</span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                      <span className="text-slate-600">Residential</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                      <span className="text-slate-600">Commercial</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      <span className="text-slate-600">Land</span>
                    </div>
                  </div>
                </CardTitle>
                <CardDescription>
                  Interactive map showing {mapData.length} tax sale properties across Nova Scotia
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-96 rounded-lg overflow-hidden border border-slate-200">
                  {mapData.length > 0 ? (
                    <MapWrapper 
                      properties={mapData}
                      onMarkerClick={(property) => {
                        // Handle marker click - could show property details
                        console.log('Property clicked:', property);
                      }}
                    />
                  ) : (
                    <div className="h-full flex items-center justify-center bg-slate-100">
                      <div className="text-center">
                        <MapPin className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-slate-900 mb-2">No Map Data</h3>
                        <p className="text-slate-600">Scrape municipality data to see properties on the map</p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Enhanced Admin Tab */}
          <TabsContent value="admin">
            <div className="space-y-6">
              {/* Status Messages */}
              {scrapeStatus && (
                <Card className="bg-blue-50/80 backdrop-blur-sm border-blue-200/50">
                  <CardContent className="py-4">
                    <div className="flex items-center space-x-2">
                      <RefreshCw className="h-4 w-4 text-blue-600" />
                      <span className="text-blue-800">{scrapeStatus}</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Enhanced Statistics Card */}
              {stats && (
                <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <BarChart3 className="h-5 w-5 text-blue-600" />
                      <span>System Statistics</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-blue-600">{stats.total_municipalities}</div>
                        <div className="text-sm text-slate-600 mt-1">Total Municipalities</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-green-600">{stats.total_properties}</div>
                        <div className="text-sm text-slate-600 mt-1">Tax Sale Properties</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-orange-600">{stats.scraped_today}</div>
                        <div className="text-sm text-slate-600 mt-1">Scraped Today</div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm font-bold text-slate-700">
                          {stats.last_scrape ? formatDate(stats.last_scrape) : "Never"}
                        </div>
                        <div className="text-sm text-slate-600 mt-1">Last Scrape</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Municipality Management */}
              <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Municipality Management</CardTitle>
                      <CardDescription>
                        Add new municipalities and edit existing ones
                      </CardDescription>
                    </div>
                    <Button
                      onClick={() => setShowAddMunicipality(true)}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Municipality
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Add Municipality Form */}
                  {showAddMunicipality && (
                    <div className="mb-6 p-4 bg-green-50 rounded-lg border border-green-200">
                      <h3 className="text-lg font-semibold text-green-800 mb-3">Add New Municipality</h3>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Municipality Name *</label>
                          <Input
                            value={newMunicipality.name}
                            onChange={(e) => setNewMunicipality({...newMunicipality, name: e.target.value})}
                            placeholder="e.g., Dartmouth, Sydney, Truro"
                            className="w-full"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Municipality Website *</label>
                          <Input
                            value={newMunicipality.website_url}
                            onChange={(e) => setNewMunicipality({...newMunicipality, website_url: e.target.value})}
                            placeholder="https://www.municipality.ca"
                            className="w-full"
                            type="url"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Tax Sale URL (Optional)</label>
                          <Input
                            value={newMunicipality.tax_sale_url}
                            onChange={(e) => setNewMunicipality({...newMunicipality, tax_sale_url: e.target.value})}
                            placeholder="https://example.com/tax-sales"
                            className="w-full"
                            type="url"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Region (Optional)</label>
                          <Input
                            value={newMunicipality.region}
                            onChange={(e) => setNewMunicipality({...newMunicipality, region: e.target.value})}
                            placeholder="e.g., Halifax Regional Municipality"
                            className="w-full"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Scraper Type</label>
                          <select
                            value={newMunicipality.scraper_type}
                            onChange={(e) => setNewMunicipality({...newMunicipality, scraper_type: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                          >
                            <option value="generic">Generic</option>
                            <option value="halifax">Halifax-style</option>
                            <option value="pdf">PDF Parser</option>
                          </select>
                        </div>
                        
                        {/* Scheduling Configuration */}
                        <div className="border-t pt-3">
                          <h4 className="text-md font-semibold text-gray-800 mb-2">Scraping Schedule</h4>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">Scrape Enabled</label>
                              <select
                                value={newMunicipality.scrape_enabled}
                                onChange={(e) => setNewMunicipality({...newMunicipality, scrape_enabled: e.target.value === 'true'})}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                              >
                                <option value="true">Enabled</option>
                                <option value="false">Disabled</option>
                              </select>
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">Frequency</label>
                              <select
                                value={newMunicipality.scrape_frequency}
                                onChange={(e) => setNewMunicipality({...newMunicipality, scrape_frequency: e.target.value})}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                              >
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="monthly">Monthly</option>
                              </select>
                            </div>
                            {newMunicipality.scrape_frequency === 'weekly' && (
                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Day of Week</label>
                                <select
                                  value={newMunicipality.scrape_day_of_week}
                                  onChange={(e) => setNewMunicipality({...newMunicipality, scrape_day_of_week: parseInt(e.target.value)})}
                                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                                >
                                  <option value={0}>Monday</option>
                                  <option value={1}>Tuesday</option>
                                  <option value={2}>Wednesday</option>
                                  <option value={3}>Thursday</option>
                                  <option value={4}>Friday</option>
                                  <option value={5}>Saturday</option>
                                  <option value={6}>Sunday</option>
                                </select>
                              </div>
                            )}
                            {newMunicipality.scrape_frequency === 'monthly' && (
                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Day of Month</label>
                                <Input
                                  type="number"
                                  min="1"
                                  max="28"
                                  value={newMunicipality.scrape_day_of_month}
                                  onChange={(e) => setNewMunicipality({...newMunicipality, scrape_day_of_month: parseInt(e.target.value)})}
                                  className="w-full"
                                />
                              </div>
                            )}
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">Scrape Time</label>
                              <div className="flex space-x-1">
                                <Input
                                  type="number"
                                  min="0"
                                  max="23"
                                  value={newMunicipality.scrape_time_hour}
                                  onChange={(e) => setNewMunicipality({...newMunicipality, scrape_time_hour: parseInt(e.target.value)})}
                                  className="w-16"
                                  placeholder="HH"
                                />
                                <span className="text-gray-500">:</span>
                                <Input
                                  type="number"
                                  min="0"
                                  max="59"
                                  value={newMunicipality.scrape_time_minute}
                                  onChange={(e) => setNewMunicipality({...newMunicipality, scrape_time_minute: parseInt(e.target.value)})}
                                  className="w-16"
                                  placeholder="MM"
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <Button onClick={handleAddMunicipality} className="bg-green-600 hover:bg-green-700">
                            <Save className="h-4 w-4 mr-2" />
                            Add Municipality
                          </Button>
                          <Button 
                            onClick={() => setShowAddMunicipality(false)} 
                            variant="outline"
                          >
                            <X className="h-4 w-4 mr-2" />
                            Cancel
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Municipality List */}
                  <div className="space-y-3">
                    <h3 className="text-lg font-semibold text-gray-800">Existing Municipalities</h3>
                    {municipalities.length === 0 ? (
                      <p className="text-gray-500 italic">No municipalities found. Add one to get started.</p>
                    ) : (
                      <div className="space-y-2">
                        {municipalities.map((municipality) => (
                          <div key={municipality.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                            {editingMunicipality?.id === municipality.id ? (
                              <div className="flex-1 space-y-2">
                                <Input
                                  value={editingMunicipality.name}
                                  onChange={(e) => setEditingMunicipality({...editingMunicipality, name: e.target.value})}
                                  className="mb-2"
                                />
                                <Input
                                  value={editingMunicipality.tax_sale_url || ''}
                                  onChange={(e) => setEditingMunicipality({...editingMunicipality, tax_sale_url: e.target.value})}
                                  placeholder="Tax Sale URL"
                                />
                                <div className="flex space-x-2">
                                  <Button 
                                    onClick={() => handleEditMunicipality(editingMunicipality)}
                                    size="sm"
                                    className="bg-blue-600 hover:bg-blue-700"
                                  >
                                    <Save className="h-3 w-3 mr-1" />
                                    Save
                                  </Button>
                                  <Button 
                                    onClick={() => setEditingMunicipality(null)}
                                    size="sm"
                                    variant="outline"
                                  >
                                    <X className="h-3 w-3 mr-1" />
                                    Cancel
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <>
                                <div className="flex-1">
                                  <div className="font-semibold text-gray-800">{municipality.name}</div>
                                  <div className="text-sm text-gray-500">
                                    Type: {municipality.scraper_type} | 
                                    Last Scraped: {municipality.last_scraped ? formatDate(municipality.last_scraped) : 'Never'}
                                  </div>
                                  <div className="text-sm text-gray-500">
                                    Schedule: {municipality.scrape_enabled ? 
                                      `${municipality.scrape_frequency} at ${String(municipality.scrape_time_hour || 2).padStart(2, '0')}:${String(municipality.scrape_time_minute || 0).padStart(2, '0')}` : 
                                      'Disabled'
                                    }
                                    {municipality.scrape_frequency === 'weekly' && municipality.scrape_enabled && (
                                      ` (${['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][municipality.scrape_day_of_week || 1]})`
                                    )}
                                    {municipality.scrape_frequency === 'monthly' && municipality.scrape_enabled && (
                                      ` (${municipality.scrape_day_of_month || 1}th)`
                                    )}
                                  </div>
                                  {municipality.tax_sale_url && (
                                    <div className="text-xs text-blue-600 truncate mt-1">
                                      URL: {municipality.tax_sale_url}
                                    </div>
                                  )}
                                </div>
                                <div className="flex space-x-2">
                                  <Button
                                    onClick={() => setEditingMunicipality({...municipality})}
                                    size="sm"
                                    variant="outline"
                                  >
                                    <Edit className="h-3 w-3 mr-1" />
                                    Edit
                                  </Button>
                                  <Button
                                    onClick={() => handleDeleteMunicipality(municipality.id, municipality.name)}
                                    size="sm"
                                    variant="outline"
                                    className="text-red-600 hover:text-red-800 hover:bg-red-50"
                                  >
                                    <Trash2 className="h-3 w-3 mr-1" />
                                    Delete
                                  </Button>
                                </div>
                              </>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Enhanced Admin Actions */}
              <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                <CardHeader>
                  <CardTitle>Data Management</CardTitle>
                  <CardDescription>
                    Initialize municipalities and manage real-time data scraping
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Button
                        onClick={initializeMunicipalities}
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <Building2 className="h-4 w-4 mr-2" />
                        Initialize Municipalities
                      </Button>
                      
                      <Button
                        onClick={scrapeHalifax}
                        disabled={loading}
                        className="bg-orange-600 hover:bg-orange-700"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Scrape Halifax (Live)
                      </Button>
                      
                      <Button
                        onClick={scrapeAllMunicipalities}
                        disabled={loading}
                        variant="outline"
                        className="border-slate-300 hover:bg-slate-50"
                      >
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Scrape All
                      </Button>
                    </div>
                    
                    <div className="p-4 bg-yellow-50 rounded-lg">
                      <h4 className="font-semibold text-yellow-800 mb-2">🚀 Real Scraping Available</h4>
                      <p className="text-sm text-yellow-700">
                        Halifax scraper is fully implemented and will fetch live data from halifax.ca. 
                        Other municipalities use placeholder scrapers - ready for implementation.
                      </p>
                    </div>

                    <div className="p-4 bg-green-50 rounded-lg">
                      <h4 className="font-semibold text-green-800 mb-2">⏰ Weekly Automation</h4>
                      <p className="text-sm text-green-700">
                        System automatically scrapes Halifax data every Sunday at 6 AM. 
                        Manual scraping available anytime via the buttons above.
                      </p>
                    </div>

                    <div className="p-4 bg-purple-50 rounded-lg">
                      <h4 className="font-semibold text-purple-800 mb-2">🔗 External Links Integration</h4>
                      <p className="text-sm text-purple-700 mb-2">
                        Property data includes clickable links for enhanced research:
                      </p>
                      <ul className="text-sm text-purple-700 space-y-1">
                        <li><strong>📋 Assessment Numbers (AAN):</strong> Link to PVSC for full property assessment details</li>
                        <li><strong>📍 PID Numbers:</strong> Direct search on Viewpoint.ca for property location and mapping</li>
                        <li><strong>🏛️ Municipality Names:</strong> Link back to original tax sale pages on municipal websites</li>
                        <li><strong>🔄 Source Integration:</strong> Seamless navigation between aggregated data and official sources</li>
                        <li><strong>🗺️ Enhanced Research:</strong> Complete property workflow from discovery to location analysis</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Enhanced Municipalities List */}
              <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                <CardHeader>
                  <CardTitle>Municipalities ({municipalities.length})</CardTitle>
                  <CardDescription>
                    Currently configured Nova Scotia municipalities with scraper status
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {municipalities.map((muni) => (
                      <div key={muni.id} className="p-4 border border-slate-200 rounded-lg bg-white/50">
                        <h4 className="font-semibold text-slate-900 mb-1">{muni.name}</h4>
                        <p className="text-sm text-slate-600 mb-2">{muni.region}</p>
                        
                        <div className="flex items-center justify-between mb-2">
                          <Badge
                            variant={
                              muni.scrape_status === 'success' ? 'default' : 
                              muni.scrape_status === 'failed' ? 'destructive' : 
                              'secondary'
                            }
                            className="text-xs"
                          >
                            {muni.scrape_status}
                          </Badge>
                          
                          {muni.scraper_type === 'halifax' && (
                            <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700">
                              Live Scraper
                            </Badge>
                          )}
                        </div>
                        
                        <div className="flex items-center justify-between text-xs text-slate-500">
                          <span>
                            {muni.last_scraped ? formatDate(muni.last_scraped) : "Never scraped"}
                          </span>
                          <a 
                            href={muni.website_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-500 hover:underline"
                          >
                            Website
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;