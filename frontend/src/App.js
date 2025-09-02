import React, { useState, useEffect, useCallback, useRef, createContext, useContext } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import "./App.css";
import axios from "axios";
import { Search, MapPin, Calendar, DollarSign, Building2, BarChart3, RefreshCw, Download, Gavel, Users, Clock, Plus, Edit, Save, X, Home, Trash2, Check, Lock, LogIn } from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Wrapper, Status } from "@googlemaps/react-wrapper";
import PropertyDetails from './components/PropertyDetails';

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

// Environment variables with fallbacks
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const GOOGLE_MAPS_API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;

// Authentication Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for stored token on app load
    const storedToken = localStorage.getItem('admin_token');
    if (storedToken) {
      setToken(storedToken);
      verifyToken(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const verifyToken = async (tokenToVerify) => {
    try {
      const response = await axios.get(`${API}/auth/verify`, {
        headers: { Authorization: `Bearer ${tokenToVerify}` }
      });
      setIsAuthenticated(true);
      setLoading(false);
    } catch (error) {
      localStorage.removeItem('admin_token');
      setToken(null);
      setIsAuthenticated(false);
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        username,
        password
      });
      
      const { access_token } = response.data;
      setToken(access_token);
      setIsAuthenticated(true);
      localStorage.setItem('admin_token', access_token);
      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setIsAuthenticated(false);
    localStorage.removeItem('admin_token');
  };

  return (
    <AuthContext.Provider value={{ 
      isAuthenticated, 
      token, 
      login, 
      logout, 
      loading 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

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
    const processProperty = (property) => {
      if (property.latitude && property.longitude) {
        // Determine marker color based on property type
        let iconColor = '#dc2626'; // Red for tax sale properties
        const propertyType = property.property_description?.toLowerCase() || '';
        
        if (propertyType.includes('commercial') || propertyType.includes('business')) {
          iconColor = '#f59e0b'; // Orange
        } else if (propertyType.includes('land') || propertyType.includes('lot')) {
          iconColor = '#10b981'; // Green
        }

        // Start with geocoded coordinates as fallback
        let markerPosition = { lat: property.latitude, lng: property.longitude };

        const createMarkerAndInfoWindow = (position) => {
          // Create marker - use AdvancedMarkerElement if available, fallback to Marker
          let marker;
          
          if (window.google.maps.marker && window.google.maps.marker.AdvancedMarkerElement) {
            // Use new AdvancedMarkerElement
            const markerElement = document.createElement('div');
            markerElement.style.cssText = `
              width: 16px; 
              height: 16px; 
              background-color: ${iconColor}; 
              border: 2px solid white; 
              border-radius: 50%; 
              cursor: pointer;
              box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            `;
            
            marker = new window.google.maps.marker.AdvancedMarkerElement({
              position: position,
              map: map,
              title: property.property_address || property.address || 'Tax Sale Property',
              content: markerElement
            });
          } else {
            // Fallback to legacy Marker (with warning suppression)
            marker = new window.google.maps.Marker({
              position: position,
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
          }

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
        };

        // Try to get boundary data for better marker positioning
        if (property.pid_number) {
          // Fetch boundary data to get precise center coordinates
          fetch(`${BACKEND_URL}/api/query-ns-government-parcel/${property.pid_number}`)
            .then(response => response.json())
            .then(data => {
              if (data.found && data.center) {
                // Use boundary center coordinates for more accurate positioning
                markerPosition = { lat: data.center.lat, lng: data.center.lon };
              }
              
              // Create marker with the best available position
              createMarkerAndInfoWindow(markerPosition);
              
              if (data.found && data.geometry && data.geometry.rings) {
                // Convert NSPRD polygon to Google Maps format
                const paths = data.geometry.rings.map(ring => 
                  ring.map(coord => ({ lat: coord[1], lng: coord[0] }))
                );
                
                // Create property boundary polygon with tax sale styling
                const propertyPolygon = new window.google.maps.Polygon({
                  paths: paths,
                  strokeColor: iconColor,
                  strokeOpacity: 0.9,
                  strokeWeight: 2,
                  fillColor: iconColor,
                  fillOpacity: 0.25,
                  map: map,
                  clickable: true
                });
                
                // Make polygon clickable to show same info as marker
                propertyPolygon.addListener('click', () => {
                  const infoWindow = new window.google.maps.InfoWindow({
                    content: `
                      <div style="max-width: 280px;">
                        <h3 style="margin: 0 0 8px 0; color: #1f2937; font-size: 14px;">${property.property_address || 'Tax Sale Property'}</h3>
                        <p style="margin: 4px 0; color: #6b7280; font-size: 12px;"><strong>PID:</strong> ${property.pid_number || 'N/A'}</p>
                        <p style="margin: 4px 0; color: #6b7280; font-size: 12px;"><strong>Assessment:</strong> ${property.assessment_number || 'N/A'}</p>
                        <p style="margin: 4px 0; color: #6b7280; font-size: 12px;"><strong>Opening Bid:</strong> $${parseFloat(property.opening_bid || 0).toLocaleString()}</p>
                        <p style="margin: 4px 0; color: #6b7280; font-size: 12px;"><strong>Municipality:</strong> ${property.municipality_name || 'N/A'}</p>
                        <p style="margin: 4px 0; color: #16a34a; font-size: 12px;"><strong>Area:</strong> ${Math.round(data.property_info?.area_sqm || 0).toLocaleString()} sqm</p>
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
                  infoWindow.setPosition(markerPosition);
                  infoWindow.open(map);
                });

                // Add hover effect
                propertyPolygon.addListener('mouseover', () => {
                  propertyPolygon.setOptions({
                    strokeOpacity: 1.0,
                    fillOpacity: 0.4,
                    strokeWeight: 3
                  });
                });

                propertyPolygon.addListener('mouseout', () => {
                  propertyPolygon.setOptions({
                    strokeOpacity: 0.9,
                    fillOpacity: 0.25,
                    strokeWeight: 2
                  });
                });

                // Add polygon to state immediately when loaded
                setBoundaryPolygons(current => [...current, propertyPolygon]);
              }
            })
            .catch(error => {
              console.warn(`Could not load boundary for PID ${property.pid_number}:`, error);
              // Create marker with geocoded coordinates as fallback
              createMarkerAndInfoWindow(markerPosition);
            });
        } else {
          // No PID available, use geocoded coordinates
          createMarkerAndInfoWindow(markerPosition);
        }
      }
    };

    properties.forEach(processProperty);

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
    <Wrapper 
      apiKey={GOOGLE_MAPS_API_KEY} 
      render={render}
      libraries={['marker', 'geometry']}
      version="weekly"
      loading="async"
    >
      <GoogleMapComponent properties={properties} onMarkerClick={onMarkerClick} />
    </Wrapper>
  );
};

function MainApp() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/" element={<PropertySearch />} />
            <Route path="/property/:assessmentNumber" element={<PropertyDetails />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

function PropertySearch() {
  const [taxSales, setTaxSales] = useState([]);
  const [municipalities, setMunicipalities] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMunicipality, setSelectedMunicipality] = useState("");
  const [selectedStatus, setSelectedStatus] = useState('active'); // New status filter state
  const [scrapeStatus, setScrapeStatus] = useState("");
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [selectedPropertyForResult, setSelectedPropertyForResult] = useState(null);
  
  // Authentication state
  const { isAuthenticated, token, logout } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);
  
  // Helper function to handle both old and new boundary_screenshot formats
  const getBoundaryImageUrl = (boundaryScreenshot, assessmentNumber) => {
    // If it's already a full URL (old format), use the property image endpoint directly
    if (boundaryScreenshot && boundaryScreenshot.startsWith('http')) {
      return `${BACKEND_URL}/api/property-image/${assessmentNumber}`;
    }
    // If it's a filename (new format), use the boundary-image endpoint
    if (boundaryScreenshot && !boundaryScreenshot.startsWith('http')) {
      return `${BACKEND_URL}/api/boundary-image/${boundaryScreenshot}`;
    }
    // Fallback to property image endpoint
    return `${BACKEND_URL}/api/property-image/${assessmentNumber}`;
  };
  
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

  // Deployment management state
  const [deploymentStatus, setDeploymentStatus] = useState(null);
  const [deploymentLoading, setDeploymentLoading] = useState(false);
  const [deploymentMessage, setDeploymentMessage] = useState("");
  const [systemHealth, setSystemHealth] = useState(null);
  const [githubRepo, setGithubRepo] = useState("");
  const [buttonStates, setButtonStates] = useState({
    checkUpdates: false,
    deploy: false,
    verify: false,
    health: false,
    refresh: false
  });

  // Fetch initial data and refresh when filters change
  useEffect(() => {
    fetchStats();
    fetchMunicipalities();
    fetchTaxSales();
    // Removed fetchMapData() to prevent duplicate API calls
    // Map will use the same data from taxSales state
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



  const handleAddMunicipality = async () => {
    if (!newMunicipality.name.trim() || !newMunicipality.website_url.trim()) return;
    
    if (!token) {
      alert('Please log in as admin to add municipalities.');
      return;
    }
    
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/municipalities`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
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
    
    if (!token) {
      alert('Please log in as admin to edit municipalities.');
      return;
    }
    
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/municipalities/${municipality.id}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
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
    
    if (!token) {
      alert('Please log in as admin to delete municipalities.');
      return;
    }
    
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/municipalities/${municipalityId}`, {
        method: 'DELETE',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
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
    if (!isAuthenticated) {
      setShowLoginModal(true);
      return;
    }
    
    setLoading(true);
    setScrapeStatus("Scraping Halifax tax sales...");
    try {
      const response = await axios.post(`${API}/scrape/halifax`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      console.log("Halifax scraping results:", response.data);
      await fetchTaxSales();
      await fetchMunicipalities(); // Refresh municipalities to show updated status
      await fetchStats();
      setScrapeStatus(`Halifax scraping completed! ${response.data.properties_scraped} properties processed.`);
    } catch (error) {
      console.error("Error scraping Halifax:", error);
      setScrapeStatus("Halifax scraping failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const scrapeIndividualMunicipality = async (municipalityId, municipalityName, scraperType) => {
    if (!isAuthenticated) {
      setShowLoginModal(true);
      return;
    }
    
    setLoading(true);
    setScrapeStatus(`Scraping ${municipalityName}...`);
    try {
      let response;
      
      // Always use the individual municipality endpoint - it will route to correct scraper based on type
      response = await axios.post(`${API}/scrape-municipality/${municipalityId}`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      console.log(`${municipalityName} scraping results:`, response.data);
      await fetchTaxSales();
      await fetchMunicipalities(); // Refresh municipalities to show updated status
      await fetchStats();
      setScrapeStatus(`${municipalityName} scraping completed! ${response.data.properties_scraped || 0} properties processed.`);
    } catch (error) {
      console.error(`Error scraping ${municipalityName}:`, error);
      setScrapeStatus(`${municipalityName} scraping failed. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  const scrapeAllMunicipalities = async () => {
    if (!isAuthenticated) {
      setShowLoginModal(true);
      return;
    }
    
    setLoading(true);
    setScrapeStatus("Scraping all municipalities...");
    try {
      const response = await axios.post(`${API}/scrape-all`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      console.log("All scraping results:", response.data);
      await fetchTaxSales();
      await fetchMunicipalities(); // Refresh municipalities to show updated status
      await fetchStats();
      setScrapeStatus("Scraping completed for all municipalities!");
    } catch (error) {
      console.error("Error scraping municipalities:", error);
      setScrapeStatus("Some scraping operations failed. Check logs for details.");
    } finally {
      setLoading(false);
    }
  };

  // Deployment management functions
  const fetchDeploymentStatus = async () => {
    if (!isAuthenticated) {
      return;
    }
    
    try {
      const response = await axios.get(`${API}/deployment/status`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      setDeploymentStatus(response.data);
      // Clear any previous error messages on successful fetch
      if (deploymentMessage && deploymentMessage.includes("Failed to fetch")) {
        setDeploymentMessage("");
      }
    } catch (error) {
      console.error("Error fetching deployment status:", error);
      setDeploymentMessage("Failed to fetch deployment status");
      // Set a default error state for deploymentStatus
      setDeploymentStatus({
        status: 'error',
        message: 'Unable to connect to deployment service',
        updates_available: false,
        last_deployment: null
      });
    }
  };

  const checkForUpdates = async () => {
    if (!isAuthenticated) {
      setShowLoginModal(true);
      return;
    }
    
    setButtonStates(prev => ({ ...prev, checkUpdates: true }));
    setDeploymentMessage("Checking for updates...");
    try {
      const response = await axios.post(`${API}/deployment/check-updates`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      const updateResult = response.data;
      
      if (updateResult.updates_available) {
        setDeploymentMessage(`Updates available! ${updateResult.message}`);
      } else {
        setDeploymentMessage("No updates available. Application is up to date.");
      }
      
      // Update deployment status with the updates_available info
      setDeploymentStatus(prev => ({
        ...prev,
        updates_available: updateResult.updates_available,
        last_update_check: updateResult.checked_at
      }));
      
    } catch (error) {
      console.error("Error checking for updates:", error);
      setDeploymentMessage("Failed to check for updates: " + (error.response?.data?.detail || error.message));
    } finally {
      setButtonStates(prev => ({ ...prev, checkUpdates: false }));
    }
  };

  const deployApplication = async () => {
    if (!isAuthenticated) {
      setShowLoginModal(true);
      return;
    }
    
    if (!window.confirm("Are you sure you want to deploy the latest version? This will restart all services.")) {
      return;
    }

    setButtonStates(prev => ({ ...prev, deploy: true }));
    setDeploymentMessage("Starting deployment...");
    try {
      const response = await axios.post(`${API}/deployment/deploy`, null, {
        params: githubRepo ? { github_repo: githubRepo } : {},
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      setDeploymentMessage("Deployment started successfully! This may take a few minutes.");
      
      // Check status periodically
      const statusInterval = setInterval(async () => {
        try {
          await fetchDeploymentStatus();
          await fetchSystemHealth();
        } catch (error) {
          console.error("Error checking deployment progress:", error);
        }
      }, 10000); // Check every 10 seconds

      // Clear interval after 5 minutes
      setTimeout(() => clearInterval(statusInterval), 300000);
      
    } catch (error) {
      console.error("Error deploying application:", error);
      setDeploymentMessage("Failed to start deployment: " + (error.response?.data?.detail || error.message));
    } finally {
      setButtonStates(prev => ({ ...prev, deploy: false }));
    }
  };

  const fetchSystemHealth = async () => {
    if (!isAuthenticated) {
      return;
    }
    
    try {
      const response = await axios.get(`${API}/deployment/health`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      setSystemHealth(response.data);
    } catch (error) {
      console.error("Error fetching system health:", error);
      // Set a default error state for system health
      setSystemHealth({
        health_status: 'unknown',
        output: 'Unable to fetch health status',
        errors: [error.message],
        checked_at: new Date().toISOString()
      });
    }
  };

  const handleHealthCheck = async () => {
    setButtonStates(prev => ({ ...prev, health: true }));
    setDeploymentMessage("Checking system health...");
    try {
      await fetchSystemHealth();
      setDeploymentMessage("System health check completed.");
    } catch (error) {
      setDeploymentMessage("Failed to check system health.");
    } finally {
      setButtonStates(prev => ({ ...prev, health: false }));
    }
  };

  const verifyDeployment = async () => {
    if (!isAuthenticated) {
      setShowLoginModal(true);
      return;
    }
    
    setButtonStates(prev => ({ ...prev, verify: true }));
    setDeploymentMessage("Verifying deployment...");
    try {
      const response = await axios.post(`${API}/deployment/verify`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      const verificationResult = response.data;
      
      if (verificationResult.deployment_valid) {
        setDeploymentMessage("Deployment verification successful! All services are running correctly.");
      } else {
        setDeploymentMessage(`Deployment verification failed: ${verificationResult.message}`);
      }
      
      await fetchSystemHealth();
      await fetchDeploymentStatus(); // Refresh status after verification
    } catch (error) {
      console.error("Error verifying deployment:", error);
      setDeploymentMessage("Failed to verify deployment: " + (error.response?.data?.detail || error.message));
    } finally {
      setButtonStates(prev => ({ ...prev, verify: false }));
    }
  };

  const refreshDeploymentStatus = async () => {
    setButtonStates(prev => ({ ...prev, refresh: true }));
    setDeploymentMessage("Refreshing deployment status...");
    try {
      await fetchDeploymentStatus();
      await fetchSystemHealth();
      setDeploymentMessage("Deployment status refreshed successfully.");
    } catch (error) {
      setDeploymentMessage("Failed to refresh deployment status.");
    } finally {
      setButtonStates(prev => ({ ...prev, refresh: false }));
    }
  };

  // Load deployment status on component mount
  useEffect(() => {
    fetchDeploymentStatus();
    fetchSystemHealth();
  }, []);

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
                <h1 className="text-2xl font-bold text-slate-900">Tax Sale Compass</h1>
                <p className="text-sm text-slate-600">Tax Sale Aggregator - Live Data</p>
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
            <div>
              <h2 className="text-2xl font-bold mb-4">Tax Sale Properties</h2>
              
              {/* Search and Filters */}
              <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {/* Search Input */}
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Search Properties
                    </label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input
                        type="text"
                        placeholder="Search by address, assessment number, PID..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            handleSearch();
                          }
                        }}
                      />
                    </div>
                  </div>
                  
                  {/* Municipality Filter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
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
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Status
                    </label>
                    <select
                      value={selectedStatus}
                      onChange={(e) => setSelectedStatus(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="active">Active</option>
                      <option value="sold">Sold</option>
                      <option value="all">All Status</option>
                    </select>
                  </div>
                </div>
                
                {/* Search Button */}
                <div className="mt-4 flex justify-end">
                  <Button 
                    onClick={handleSearch}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                    disabled={loading}
                  >
                    <Search className="h-4 w-4 mr-2" />
                    {loading ? 'Searching...' : 'Search Properties'}
                  </Button>
                </div>
              </div>
              
              {/* Results Count */}
              {taxSales.length > 0 && (
                <div className="mb-4 text-sm text-gray-600">
                  Showing {taxSales.length} properties
                  {searchQuery && ` matching "${searchQuery}"`}
                  {selectedMunicipality && ` in ${selectedMunicipality}`}
                </div>
              )}
              
              {/* Property Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {taxSales.map((property, index) => (
                  <React.Fragment key={property.id || index}>
                    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-slate-200">
                      {/* Property Image */}
                      <div className="relative h-48 bg-gray-200">
                        {property.boundary_screenshot ? (
                          <img
                            src={getBoundaryImageUrl(property.boundary_screenshot, property.assessment_number)}
                            alt={`Property boundary map of ${property.property_address}`}
                            className="w-full h-full object-cover rounded-t-lg"
                            onError={(e) => {
                              // First fallback: try dynamic property image endpoint
                              if (e.target.src.includes('/api/boundary-image/') && property.assessment_number) {
                                e.target.src = `${BACKEND_URL}/api/property-image/${property.assessment_number}`;
                              }
                              // Second fallback: satellite image  
                              else if (property.latitude && property.longitude) {
                                e.target.src = `https://maps.googleapis.com/maps/api/staticmap?center=${property.latitude},${property.longitude}&zoom=17&size=400x300&maptype=satellite&key=${GOOGLE_MAPS_API_KEY}`;
                              } else {
                                e.target.style.display = 'none';
                                e.target.parentNode.innerHTML = '<div class="w-full h-full bg-gradient-to-br from-blue-100 to-green-100 flex items-center justify-center rounded-t-lg"><div class="text-center text-gray-600"><div class="text-2xl mb-1">🏠</div><div class="text-sm">No Image Available</div></div></div>';
                              }
                            }}
                          />
                        ) : property.latitude && property.longitude ? (
                          <img
                            src={`https://maps.googleapis.com/maps/api/staticmap?center=${property.latitude},${property.longitude}&zoom=17&size=400x300&maptype=satellite&key=${GOOGLE_MAPS_API_KEY}`}
                            alt={`Satellite view of ${property.property_address}`}
                            className="w-full h-full object-cover rounded-t-lg"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.parentNode.innerHTML = '<div class="w-full h-full bg-gradient-to-br from-blue-100 to-green-100 flex items-center justify-center rounded-t-lg"><div class="text-center text-gray-600"><div class="text-2xl mb-1">🏠</div><div class="text-sm">No Image Available</div></div></div>';
                            }}
                          />
                        ) : (
                          <div className="w-full h-full bg-gradient-to-br from-blue-100 to-green-100 flex items-center justify-center rounded-t-lg">
                            <div className="text-center text-gray-600">
                              <div className="text-2xl mb-1">🏠</div>
                              <div className="text-sm">No Image Available</div>
                            </div>
                          </div>
                        )}
                        
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
                      </div>

                      {/* Property Content */}
                      <div className="p-4">
                        <div className="mb-3">
                          <h3 className="text-lg font-semibold text-slate-900 mb-1">
                            {property.property_address || 'Address not available'}
                          </h3>
                          <p className="text-sm text-slate-600">
                            Assessment #: {property.assessment_number}
                          </p>
                          {property.pid_number && (
                            <p className="text-sm text-slate-600">
                              PID: {property.pid_number}
                            </p>
                          )}
                        </div>

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

                        {/* Details */}
                        <div className="text-sm text-slate-600 space-y-1 mb-4">
                          <div>Owner: {property.owner_name || 'Not available'}</div>
                          <div>Municipality: {property.municipality_name || property.municipality || 'Halifax Regional Municipality'}</div>
                          {property.sale_date && (
                            <div>Sale Date: {formatDate(property.sale_date)}</div>
                          )}
                        </div>

                        {/* Action Button */}
                        <Link
                          to={`/property/${property.assessment_number}`}
                          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md text-sm font-medium transition-colors duration-200 text-center block"
                        >
                          See More Details →
                        </Link>
                      </div>
                    </div>

                    {/* Insert AdSense Ad after every 6th property */}
                    {(index + 1) % 6 === 0 && index < taxSales.length - 1 && (
                      <div className="md:col-span-2 lg:col-span-3">
                        <SearchPageAd index={Math.floor((index + 1) / 6)} />
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
              
              {/* No Results */}
              {taxSales.length === 0 && (
                <div className="text-center py-12">
                  <div className="text-gray-500 text-lg">No tax sale properties found</div>
                  <p className="text-gray-400 mt-2">Try scraping Halifax data to populate properties</p>
                </div>
              )}
            </div>
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
                  Interactive map showing {taxSales.filter(p => p.latitude && p.longitude).length} tax sale properties across Nova Scotia
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-96 rounded-lg overflow-hidden border border-slate-200">
                  {taxSales.length > 0 ? (
                    <MapWrapper 
                      properties={taxSales}
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
              {/* Authentication Check */}
              {!isAuthenticated ? (
                <Card className="bg-yellow-50/80 backdrop-blur-sm border-yellow-200/50">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Lock className="h-5 w-5 text-yellow-600" />
                      <span>Admin Access Required</span>
                    </CardTitle>
                    <CardDescription>
                      You need to be authenticated to access admin features.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button 
                      onClick={() => setShowLoginModal(true)}
                      className="flex items-center space-x-2"
                    >
                      <LogIn className="h-4 w-4" />
                      <span>Login as Admin</span>
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <>
                  {/* Admin Header with Logout */}
                  <Card className="bg-green-50/80 backdrop-blur-sm border-green-200/50">
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Check className="h-4 w-4 text-green-600" />
                          <span className="text-green-800">Authenticated as Admin</span>
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={logout}
                        >
                          Logout
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

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
                          <label className="block text-sm font-medium text-gray-700 mb-1">Municipality Description (Optional)</label>
                          <textarea
                            value={newMunicipality.description || ''}
                            onChange={(e) => setNewMunicipality({...newMunicipality, description: e.target.value})}
                            placeholder="Enter municipality-specific information for property details pages (tax sale process, contact info, etc.)"
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                          />
                          <p className="text-xs text-gray-500 mt-1">This description will be displayed on property detail pages for this municipality</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Scraper Type</label>
                          <select
                            value={newMunicipality.scraper_type}
                            onChange={(e) => setNewMunicipality({...newMunicipality, scraper_type: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                          >
                            <option value="generic">Generic</option>
                            <option value="halifax">Halifax (PDF)</option>
                            <option value="cape_breton">Cape Breton</option>
                            <option value="kentville">Kentville</option>
                            <option value="victoria_county">Victoria County (PDF)</option>
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
                              <div className="flex-1 space-y-3">
                                {/* Municipality Name */}
                                <Input
                                  value={editingMunicipality.name}
                                  onChange={(e) => setEditingMunicipality({...editingMunicipality, name: e.target.value})}
                                  placeholder="Municipality Name"
                                  className="mb-2"
                                />
                                
                                {/* Tax Sale URL */}
                                <Input
                                  value={editingMunicipality.tax_sale_url || ''}
                                  onChange={(e) => setEditingMunicipality({...editingMunicipality, tax_sale_url: e.target.value})}
                                  placeholder="Tax Sale URL"
                                />
                                
                                {/* Municipality Description */}
                                <div>
                                  <label className="block text-sm font-medium text-gray-700 mb-1">Municipality Description</label>
                                  <textarea
                                    value={editingMunicipality.description || ''}
                                    onChange={(e) => setEditingMunicipality({...editingMunicipality, description: e.target.value})}
                                    placeholder="Enter municipality-specific information for property details pages (tax sale process, contact info, etc.)"
                                    rows={3}
                                    className="w-full p-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                                  />
                                  <p className="text-xs text-gray-500 mt-1">This description will be displayed on property detail pages for this municipality</p>
                                </div>
                                
                                {/* Scraper Type */}
                                <div>
                                  <label className="block text-sm font-medium text-gray-700 mb-1">Scraper Type</label>
                                  <select
                                    value={editingMunicipality.scraper_type || 'manual'}
                                    onChange={(e) => setEditingMunicipality({...editingMunicipality, scraper_type: e.target.value})}
                                    className="w-full p-2 border border-gray-300 rounded-md text-sm"
                                  >
                                    <option value="manual">Manual</option> 
                                    <option value="generic">Generic</option>
                                    <option value="halifax">Halifax (PDF)</option>
                                    <option value="cape_breton">Cape Breton</option>
                                    <option value="kentville">Kentville</option>
                                    <option value="victoria_county">Victoria County (PDF)</option>
                                    <option value="placeholder">Placeholder</option>
                                  </select>
                                </div>
                                
                                {/* Scraping Enabled */}
                                <div className="flex items-center space-x-2">
                                  <input
                                    type="checkbox"
                                    id={`scrape-enabled-${editingMunicipality.id}`}
                                    checked={editingMunicipality.scrape_enabled || false}
                                    onChange={(e) => setEditingMunicipality({...editingMunicipality, scrape_enabled: e.target.checked})}
                                    className="rounded"
                                  />
                                  <label htmlFor={`scrape-enabled-${editingMunicipality.id}`} className="text-sm font-medium text-gray-700">
                                    Enable Automatic Scraping
                                  </label>
                                </div>
                                
                                {editingMunicipality.scrape_enabled && (
                                  <>
                                    {/* Scrape Frequency */}
                                    <div>
                                      <label className="block text-sm font-medium text-gray-700 mb-1">Scrape Frequency</label>
                                      <select
                                        value={editingMunicipality.scrape_frequency || 'weekly'}
                                        onChange={(e) => setEditingMunicipality({...editingMunicipality, scrape_frequency: e.target.value})}
                                        className="w-full p-2 border border-gray-300 rounded-md text-sm"
                                      >
                                        <option value="daily">Daily</option>
                                        <option value="weekly">Weekly</option>
                                        <option value="monthly">Monthly</option>
                                      </select>
                                    </div>
                                    
                                    {/* Time Settings */}
                                    <div className="grid grid-cols-2 gap-2">
                                      <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Hour (24h)</label>
                                        <input
                                          type="number"
                                          min="0"
                                          max="23"
                                          value={editingMunicipality.scrape_time_hour || 2}
                                          onChange={(e) => setEditingMunicipality({...editingMunicipality, scrape_time_hour: parseInt(e.target.value)})}
                                          className="w-full p-2 border border-gray-300 rounded-md text-sm"
                                        />
                                      </div>
                                      <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Minute</label>
                                        <input
                                          type="number"
                                          min="0"
                                          max="59"
                                          value={editingMunicipality.scrape_time_minute || 0}
                                          onChange={(e) => setEditingMunicipality({...editingMunicipality, scrape_time_minute: parseInt(e.target.value)})}
                                          className="w-full p-2 border border-gray-300 rounded-md text-sm"
                                        />
                                      </div>
                                    </div>
                                    
                                    {/* Day Settings */}
                                    {editingMunicipality.scrape_frequency === 'weekly' && (
                                      <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Day of Week</label>
                                        <select
                                          value={editingMunicipality.scrape_day_of_week || 0}
                                          onChange={(e) => setEditingMunicipality({...editingMunicipality, scrape_day_of_week: parseInt(e.target.value)})}
                                          className="w-full p-2 border border-gray-300 rounded-md text-sm"
                                        >
                                          <option value="0">Sunday</option>
                                          <option value="1">Monday</option>
                                          <option value="2">Tuesday</option>
                                          <option value="3">Wednesday</option>
                                          <option value="4">Thursday</option>
                                          <option value="5">Friday</option>
                                          <option value="6">Saturday</option>
                                        </select>
                                      </div>
                                    )}
                                    
                                    {editingMunicipality.scrape_frequency === 'monthly' && (
                                      <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Day of Month</label>
                                        <input
                                          type="number"
                                          min="1"
                                          max="31"
                                          value={editingMunicipality.scrape_day_of_month || 1}
                                          onChange={(e) => setEditingMunicipality({...editingMunicipality, scrape_day_of_month: parseInt(e.target.value)})}
                                          className="w-full p-2 border border-gray-300 rounded-md text-sm"
                                        />
                                      </div>
                                    )}
                                  </>
                                )}
                                
                                {/* Save/Cancel Buttons */}
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
                                    Status: <span className={`font-semibold ${municipality.scrape_status === 'success' ? 'text-green-600' : municipality.scrape_status === 'pending' ? 'text-yellow-600' : 'text-red-600'}`}>
                                      {municipality.scrape_status}
                                    </span> |
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
                          
                          {(muni.scraper_type === 'halifax' || muni.scraper_type === 'victoria_county') && (
                            <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700">
                              Live Scraper
                            </Badge>
                          )}
                        </div>
                        
                        <div className="mb-3">
                          <Button
                            onClick={() => scrapeIndividualMunicipality(muni.id, muni.name, muni.scraper_type)}
                            disabled={loading}
                            size="sm"
                            className={`w-full ${
                              (muni.scraper_type === 'halifax' || muni.scraper_type === 'victoria_county')
                                ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                                : 'bg-gray-600 hover:bg-gray-700 text-white'
                            }`}
                          >
                            {loading ? (
                              <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                            ) : (
                              <Download className="h-3 w-3 mr-1" />
                            )}
                            {muni.scraper_type === 'halifax' ? 'Run Halifax Scraper' : 
                             muni.scraper_type === 'victoria_county' ? 'Run Victoria County Scraper' : 'Run Generic Scraper'}
                          </Button>
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

              {/* Deployment Management */}
              <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <RefreshCw className="h-5 w-5 text-green-600" />
                    <span>Deployment Management</span>
                  </CardTitle>
                  <CardDescription>
                    Manage application updates and deployments
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Deployment Status Messages */}
                  {deploymentMessage && (
                    <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <RefreshCw className={`h-4 w-4 text-blue-600 ${
                          buttonStates.checkUpdates || buttonStates.deploy || 
                          buttonStates.verify || buttonStates.health || 
                          buttonStates.refresh ? 'animate-spin' : ''
                        }`} />
                        <span className="text-blue-800">{deploymentMessage}</span>
                      </div>
                    </div>
                  )}

                  {/* Deployment Status Overview */}
                  {deploymentStatus && (
                    <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
                      <h4 className="font-semibold text-gray-800 mb-3">Current Status</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Status:</span>
                          <div className={`font-medium ${
                            !deploymentStatus.status || deploymentStatus.status === 'idle' ? 'text-green-600' : 
                            deploymentStatus.status === 'error' ? 'text-red-600' : 'text-yellow-600'
                          }`}>
                            {deploymentStatus.status ? 
                              deploymentStatus.status.charAt(0).toUpperCase() + deploymentStatus.status.slice(1) : 
                              'Unknown'
                            }
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Updates Available:</span>
                          <div className={`font-medium ${deploymentStatus.updates_available ? 'text-orange-600' : 'text-green-600'}`}>
                            {deploymentStatus.updates_available ? 'Yes' : 'No'}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Last Deployment:</span>
                          <div className="font-medium text-gray-800">
                            {deploymentStatus.last_deployment ? formatDate(deploymentStatus.last_deployment) : 'Never'}
                          </div>
                        </div>
                      </div>
                      {deploymentStatus.current_commit && (
                        <div className="mt-3 pt-3 border-t text-xs">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            <div>
                              <span className="text-gray-600">Current:</span>
                              <code className="ml-2 px-2 py-1 bg-gray-200 rounded">{deploymentStatus.current_commit}</code>
                            </div>
                            <div>
                              <span className="text-gray-600">Latest:</span>
                              <code className="ml-2 px-2 py-1 bg-gray-200 rounded">{deploymentStatus.remote_commit}</code>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* System Health */}
                  {systemHealth && (
                    <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
                      <h4 className="font-semibold text-gray-800 mb-3">System Health</h4>
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${
                          systemHealth.health_status === 'excellent' ? 'bg-green-500' :
                          systemHealth.health_status === 'good' ? 'bg-yellow-500' :
                          systemHealth.health_status === 'poor' ? 'bg-red-500' : 'bg-gray-500'
                        }`}></div>
                        <span className="font-medium capitalize">{systemHealth.health_status}</span>
                        <span className="text-gray-600 text-sm">
                          (checked {systemHealth.checked_at ? formatDate(systemHealth.checked_at) : 'unknown'})
                        </span>
                      </div>
                    </div>
                  )}

                  {/* GitHub Repository Input */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      GitHub Repository URL (Optional)
                    </label>
                    <Input
                      value={githubRepo}
                      onChange={(e) => setGithubRepo(e.target.value)}
                      placeholder="https://github.com/username/tax-sale-compass.git"
                      className="w-full"
                      type="url"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Leave empty to use the current repository configuration
                    </p>
                  </div>

                  {/* Deployment Actions */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
                    <Button
                      onClick={refreshDeploymentStatus}
                      disabled={buttonStates.refresh}
                      className="bg-gray-600 hover:bg-gray-700"
                    >
                      <RefreshCw className={`h-4 w-4 mr-2 ${buttonStates.refresh ? 'animate-spin' : ''}`} />
                      Refresh Status
                    </Button>
                    
                    <Button
                      onClick={checkForUpdates}
                      disabled={buttonStates.checkUpdates}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <RefreshCw className={`h-4 w-4 mr-2 ${buttonStates.checkUpdates ? 'animate-spin' : ''}`} />
                      Check Updates
                    </Button>
                    
                    <Button
                      onClick={deployApplication}
                      disabled={buttonStates.deploy}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <Download className={`h-4 w-4 mr-2 ${buttonStates.deploy ? 'animate-pulse' : ''}`} />
                      Deploy Latest
                    </Button>
                    
                    <Button
                      onClick={verifyDeployment}
                      disabled={buttonStates.verify}
                      className="bg-purple-600 hover:bg-purple-700"
                    >
                      <Check className={`h-4 w-4 mr-2 ${buttonStates.verify ? 'animate-pulse' : ''}`} />
                      Verify Status
                    </Button>
                    
                    <Button
                      onClick={handleHealthCheck}
                      disabled={buttonStates.health}
                      className="bg-orange-600 hover:bg-orange-700"
                    >
                      <BarChart3 className={`h-4 w-4 mr-2 ${buttonStates.health ? 'animate-pulse' : ''}`} />
                      Health Check
                    </Button>
                  </div>

                  <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <div className="w-4 h-4 rounded-full bg-yellow-500 mt-0.5 flex-shrink-0"></div>
                      <div className="text-sm text-yellow-800">
                        <strong>Important:</strong> Deployment will restart all services and may cause brief downtime.
                        Always verify the deployment after completion.
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Auction Result Management */}
              <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                <CardHeader>
                  <CardTitle>Auction Result Management</CardTitle>
                  <CardDescription>
                    Update auction results for properties after sales
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Properties Pending Results */}
                    {taxSales.filter(prop => prop.auction_result === 'pending').length > 0 && (
                      <div className="bg-yellow-50 rounded-lg p-4">
                        <h4 className="font-semibold text-yellow-800 mb-3">Properties with Pending Results</h4>
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                          {taxSales
                            .filter(prop => prop.auction_result === 'pending')
                            .map(property => (
                              <div key={property.id} className="bg-white rounded border p-3">
                                <div className="flex justify-between items-start">
                                  <div className="flex-1">
                                    <div className="font-medium">{property.property_address}</div>
                                    <div className="text-sm text-gray-600">
                                      Assessment: {property.assessment_number} | 
                                      Opening Bid: ${parseFloat(property.opening_bid || 0).toLocaleString()}
                                    </div>
                                    {property.sale_date && (
                                      <div className="text-sm text-gray-500">
                                        Auction Date: {formatDate(property.sale_date)}
                                      </div>
                                    )}
                                  </div>
                                  <Button
                                    size="sm"
                                    onClick={() => setSelectedPropertyForResult(property)}
                                    className="ml-2"
                                  >
                                    Update Result
                                  </Button>
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* Quick Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
                      <div className="bg-yellow-50 rounded-lg p-3">
                        <div className="text-2xl font-bold text-yellow-800">
                          {taxSales.filter(prop => prop.auction_result === 'pending').length}
                        </div>
                        <div className="text-sm text-yellow-600">Pending</div>
                      </div>
                      <div className="bg-blue-50 rounded-lg p-3">
                        <div className="text-2xl font-bold text-blue-800">
                          {taxSales.filter(prop => prop.auction_result === 'sold').length}
                        </div>
                        <div className="text-sm text-blue-600">Sold</div>
                      </div>
                      <div className="bg-red-50 rounded-lg p-3">
                        <div className="text-2xl font-bold text-red-800">
                          {taxSales.filter(prop => prop.auction_result === 'canceled').length}
                        </div>
                        <div className="text-sm text-red-600">Canceled</div>
                      </div>
                      <div className="bg-orange-50 rounded-lg p-3">
                        <div className="text-2xl font-bold text-orange-800">
                          {taxSales.filter(prop => prop.auction_result === 'deferred').length}
                        </div>
                        <div className="text-sm text-orange-600">Deferred</div>
                      </div>
                      <div className="bg-green-50 rounded-lg p-3">
                        <div className="text-2xl font-bold text-green-800">
                          {taxSales.filter(prop => prop.auction_result === 'taxes_paid').length}
                        </div>
                        <div className="text-sm text-green-600">Redeemed</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              </>
              )}
            </div>
          </TabsContent>
        </Tabs>
        
        {/* Login Modal */}
        <LoginModal 
          isOpen={showLoginModal} 
          onClose={() => setShowLoginModal(false)} 
        />
        
        {/* Auction Result Modal */}
        <AuctionResultModal
          isOpen={selectedPropertyForResult !== null}
          property={selectedPropertyForResult}
          onClose={() => setSelectedPropertyForResult(null)}
          onUpdate={() => {
            fetchTaxSales();
            fetchStats();
          }}
        />
      </div>
    </div>
  );
}

// Login Modal Component
const LoginModal = ({ isOpen, onClose }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const success = await login(username, password);
    if (success) {
      onClose();
      setUsername('');
      setPassword('');
    } else {
      setError('Invalid username or password');
    }
    setIsLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Admin Login</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X size={24} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <Input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full"
            />
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full"
            />
          </div>
          
          {error && (
            <div className="mb-4 text-red-600 text-sm">
              {error}
            </div>
          )}
          
          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={isLoading}
              className="flex-1"
            >
              {isLoading ? 'Logging in...' : 'Login'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Auction Result Update Modal Component
const AuctionResultModal = ({ isOpen, property, onClose, onUpdate }) => {
  const [auctionResult, setAuctionResult] = useState('');
  const [winningBidAmount, setWinningBidAmount] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { token } = useAuth();
  
  useEffect(() => {
    if (property) {
      setAuctionResult(property.auction_result || '');
      setWinningBidAmount(property.winning_bid_amount || '');
    }
  }, [property]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const requestData = { auction_result: auctionResult };
      if (auctionResult === 'sold' && winningBidAmount) {
        requestData.winning_bid_amount = parseFloat(winningBidAmount.replace(/,/g, ''));
      }
      
      const response = await axios.put(
        `${API}/admin/properties/${property.id}/auction-result`,
        requestData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data.status === 'success') {
        onUpdate(); // Refresh the data
        onClose();
        setAuctionResult('');
        setWinningBidAmount('');
      }
    } catch (error) {
      console.error('Error updating auction result:', error);
      setError(error.response?.data?.detail || 'Failed to update auction result');
    }
    setIsLoading(false);
  };

  if (!isOpen || !property) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Update Auction Result</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X size={24} />
          </button>
        </div>
        
        {/* Property Info */}
        <div className="bg-gray-50 rounded-lg p-3 mb-4">
          <div className="font-semibold">{property.property_address}</div>
          <div className="text-sm text-gray-600">
            Assessment: {property.assessment_number} | 
            Opening Bid: ${parseFloat(property.opening_bid || 0).toLocaleString()}
          </div>
          {property.sale_date && (
            <div className="text-sm text-gray-500">
              Auction Date: {new Date(property.sale_date).toLocaleDateString()}
            </div>
          )}
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Auction Result *
            </label>
            <select
              value={auctionResult}
              onChange={(e) => setAuctionResult(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select result...</option>
              <option value="pending">Pending (Results not available yet)</option>
              <option value="sold">Sold</option>
              <option value="canceled">Canceled</option>
              <option value="deferred">Deferred</option>
              <option value="taxes_paid">Taxes Paid (Redeemed)</option>
            </select>
          </div>
          
          {auctionResult === 'sold' && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Final Sale Price *
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                <Input
                  type="text"
                  value={winningBidAmount}
                  onChange={(e) => {
                    // Format number with commas
                    const value = e.target.value.replace(/[^\d.]/g, '');
                    const formatted = value.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
                    setWinningBidAmount(formatted);
                  }}
                  placeholder="0.00"
                  required={auctionResult === 'sold'}
                  className="w-full pl-8"
                />
              </div>
            </div>
          )}
          
          {error && (
            <div className="mb-4 text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
              {error}
            </div>
          )}
          
          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={isLoading}
              className="flex-1"
            >
              {isLoading ? 'Updating...' : 'Update Result'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MainApp;