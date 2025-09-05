import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Wrapper, Status } from "@googlemaps/react-wrapper";
import ReliableMap from './ReliableMap';

// AdSense Component for Property Details Page
const PropertyDetailsAd = () => {
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
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div className="text-center text-sm text-gray-500 mb-2">Advertisement</div>
      <ins className="adsbygoogle"
           style={{display:'block'}}
           data-ad-client="ca-pub-5947395928510215"
           data-ad-slot="3653544552"
           data-ad-format="auto"
           data-full-width-responsive="true">
      </ins>
    </div>
  );
};

const PropertyDetails = () => {
  const { assessmentNumber } = useParams();
  const navigate = useNavigate();
  const [property, setProperty] = useState(null);
  const [propertyDetails, setPropertyDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [boundaryData, setBoundaryData] = useState(null);
  const mapRef = useRef();
  const [map, setMap] = useState(null);
  const [boundaryPolygon, setBoundaryPolygon] = useState(null);
  const [municipalityData, setMunicipalityData] = useState(null);

  useEffect(() => {
    fetchPropertyDetails();
  }, [assessmentNumber]);

  // Fetch municipality data when property is loaded
  useEffect(() => {
    if (property && property.municipality_name && !municipalityData) {
      fetchMunicipalityData(property.municipality_name);
    }
  }, [property, municipalityData]);

  // Fetch municipality data for tax sale URL
  const fetchMunicipalityData = async (municipalityName) => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/municipalities`);
      const municipalities = await response.json();
      
      // Find the municipality that matches the property's municipality name
      const municipality = municipalities.find(m => m.name === municipalityName);
      if (municipality) {
        setMunicipalityData(municipality);
      }
    } catch (error) {
      console.error('Error fetching municipality data:', error);
    }
  };

  // Fetch NSPRD boundary data (supports multiple PIDs)
  const fetchBoundaryData = async (pidNumber) => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/query-ns-government-parcel/${pidNumber}`);
      const data = await response.json();
      
      // Handle both single PID and multiple PID responses
      if (data.found) {
        // For multiple PIDs, use combined geometry
        if (data.multiple_pids && data.combined_geometry && data.combined_geometry.rings) {
          setBoundaryData({
            ...data,
            geometry: data.combined_geometry,
            bbox: data.combined_bbox,
            center: data.center,
            pid_count: data.pids ? data.pids.length : 1
          });
          return data;
        }
        // For single PID, use regular geometry
        else if (data.geometry && data.geometry.rings) {
          setBoundaryData({
            ...data,
            pid_count: 1
          });
          return data;
        }
      }
    } catch (error) {
      console.error('Error fetching boundary data:', error);
    }
    return null;
  };

  // Load boundary data when property is available
  useEffect(() => {
    if (property && property.pid_number && !boundaryData) {
      fetchBoundaryData(property.pid_number);
    }
  }, [property, boundaryData]);

  // Initialize Google Map with boundary polygons
  useEffect(() => {
    if (!property?.latitude || !property?.longitude || !mapRef.current) return;

    // Initialize map directly without LoadScript to avoid conflicts
    const initMap = () => {
      if (!window.google?.maps) {
        console.log('Google Maps not yet loaded, waiting...');
        return;
      }

      try {
        const map = new window.google.maps.Map(mapRef.current, {
          center: {
            lat: parseFloat(property.latitude),
            lng: parseFloat(property.longitude)
          },
          zoom: 17,
          mapTypeId: 'satellite',
          disableDefaultUI: false,
          zoomControl: true,
          streetViewControl: true,
          mapTypeControl: true,
          fullscreenControl: true
        });

        // Don't add marker here - will be added in drawBoundaryPolygon at centroid
        setMap(map);
        console.log('Google Map initialized successfully');

        // Draw boundary polygon if data is available
        if (boundaryData?.geometry?.rings) {
          drawBoundaryPolygon(map, boundaryData.geometry.rings);
        } else {
          // If no boundary data, add marker at original coordinates
          new window.google.maps.Marker({
            position: {
              lat: parseFloat(property.latitude),
              lng: parseFloat(property.longitude)
            },
            map: map,
            title: `${property.property_address} - ${formatCurrency(property.opening_bid)}`
          });
        }

      } catch (error) {
        console.error('Error initializing Google Map:', error);
      }
    };

    // Use the robust Google Maps loader
    const initializeMapAsync = async () => {
      try {
        console.log('PropertyDetails: Loading Google Maps API...');
        await googleMapsLoader.load();
        initMap();
      } catch (error) {
        console.error('PropertyDetails: Error loading Google Maps:', error);
      }
    };

    initializeMapAsync();
  }, [property, boundaryData]);

  // Calculate polygon centroid
  const calculatePolygonCentroid = (rings) => {
    if (!rings || rings.length === 0) return null;
    
    // Use the first (main) ring
    const ring = rings[0];
    if (!ring || ring.length === 0) return null;
    
    let totalLat = 0;
    let totalLng = 0;
    let pointCount = 0;
    
    for (const point of ring) {
      totalLat += point[1]; // Latitude is second element
      totalLng += point[0]; // Longitude is first element
      pointCount++;
    }
    
    return {
      lat: totalLat / pointCount,
      lng: totalLng / pointCount
    };
  };

  // Draw NSPRD boundary polygon on the map
  const drawBoundaryPolygon = (map, rings) => {
    try {
      // Clear existing polygon
      if (boundaryPolygon) {
        boundaryPolygon.setMap(null);
      }

      // Convert rings to Google Maps format
      const paths = rings.map(ring => 
        ring.map(point => ({
          lat: point[1], // Latitude is second element
          lng: point[0]  // Longitude is first element
        }))
      );

      // Create and display polygon
      const polygon = new window.google.maps.Polygon({
        paths: paths,
        strokeColor: '#FF0000',
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: '#FF0000',
        fillOpacity: 0.15
      });

      polygon.setMap(map);
      setBoundaryPolygon(polygon);

      // Calculate centroid and reposition marker
      const centroid = calculatePolygonCentroid(rings);
      if (centroid) {
        // Create new marker at boundary centroid
        const marker = new window.google.maps.Marker({
          position: centroid,
          map: map,
          title: `${property.property_address} - ${formatCurrency(property.opening_bid)}`,
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            scale: 8,
            fillColor: '#FF0000',
            fillOpacity: 1,
            strokeColor: '#FFFFFF',
            strokeWeight: 2
          }
        });

        // Center map on the boundary centroid
        map.setCenter(centroid);
        
        console.log('Marker repositioned to boundary centroid:', centroid);
      }

      console.log('NSPRD boundary polygon drawn successfully on map');
    } catch (error) {
      console.error('Error drawing boundary polygon:', error);
    }
  };

  // Update polygon when boundary data changes
  useEffect(() => {
    if (map && boundaryData?.geometry?.rings) {
      drawBoundaryPolygon(map, boundaryData.geometry.rings);
    }
  }, [map, boundaryData]);

  const fetchPropertyDetails = async () => {
    try {
      setLoading(true);
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('authToken');
      
      // Check if user is authenticated
      if (!token) {
        setError('Please log in to view property details');
        return;
      }
      
      // Use the dedicated property endpoint
      const headers = { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      };
      
      const response = await fetch(`${backendUrl}/api/property/${assessmentNumber}`, {
        headers: headers
      });
      
      if (response.status === 401) {
        setError('Please log in to view property details');
        return;
      }
      
      if (response.status === 403) {
        setError('Paid subscription required to view active property details');
        return;
      }
      
      if (response.status === 404) {
        setError('Property not found');
        return;
      }
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const foundProperty = await response.json();
      setProperty(foundProperty);
      
      // Try to fetch enhanced property details (PVSC data)
      try {
        const enhancedResponse = await fetch(`${backendUrl}/api/property/${assessmentNumber}/enhanced`, {
          headers: headers
        });
        if (enhancedResponse.ok) {
          const enhanced = await enhancedResponse.json();
          setPropertyDetails(enhanced);
        }
      } catch (error) {
        console.log('Enhanced details not available:', error);
      }
      
    } catch (error) {
      console.error('Error fetching property details:', error);
      setError('Failed to load property details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      minimumFractionDigits: 2
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not specified';
    return new Date(dateString).toLocaleDateString('en-CA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const calculateTimeLeft = (saleDate) => {
    if (!saleDate) return 'Not specified';
    
    const now = new Date();
    const sale = new Date(saleDate);
    const diffTime = sale - now;
    
    if (diffTime <= 0) {
      return 'Sale ended';
    }
    
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
      return '1 day left';
    } else if (diffDays < 30) {
      return `${diffDays} days left`;
    } else {
      const diffMonths = Math.floor(diffDays / 30);
      const remainingDays = diffDays % 30;
      if (remainingDays === 0) {
        return `${diffMonths} month${diffMonths > 1 ? 's' : ''} left`;
      } else {
        return `${diffMonths} month${diffMonths > 1 ? 's' : ''}, ${remainingDays} day${remainingDays > 1 ? 's' : ''} left`;
      }
    }
  };

  const getTaxSaleUrl = () => {
    // Use database municipality data for URLs
    if (municipalityData) {
      // Prefer tax_sale_url if available, otherwise use website_url
      if (municipalityData.tax_sale_url) {
        return municipalityData.tax_sale_url;
      } else if (municipalityData.website_url) {
        // If no specific tax sale URL, try common tax sale page patterns
        const baseUrl = municipalityData.website_url.replace(/\/$/, ''); // Remove trailing slash
        return `${baseUrl}/tax-sales`;
      }
    }
    
    // Fallback to # if no municipality data available
    return '#';
  };

  // Google Maps configuration
  const mapContainerStyle = {
    width: '100%',
    height: '400px'
  };

  const mapOptions = {
    disableDefaultUI: false,
    zoomControl: true,
    streetViewControl: true,
    mapTypeControl: true,
    fullscreenControl: true
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900">Loading Property Details...</h2>
        </div>
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Property Not Found</h2>
          <p className="text-gray-600 mb-6">{error || 'The requested property could not be found.'}</p>
          <button
            onClick={() => navigate('/')}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            ← Back to Property Search
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <div className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 py-3">
          <button
            onClick={() => navigate('/')}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to Search
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content - Left Column */}
          <div className="lg:col-span-2 space-y-8">
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                Tax Sale Property in {property.municipality_name || 'Nova Scotia'}
              </h1>
              <h2 className="text-2xl text-gray-700 mb-4">
                {property.property_address || 'Address not available'}
              </h2>
              
              <div className="flex items-center space-x-4 text-sm mb-6">
                <span><strong>AAN:</strong> {property.assessment_number}</span>
                {property.pid_number && <span>•</span>}
                {property.pid_number && <span><strong>PID:</strong> {property.pid_number}</span>}
              </div>

              {/* Comprehensive Property Information Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div>
                  <span className="block text-sm text-gray-500">Status</span>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                    property.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {property.status || 'Active'}
                  </span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Sale Type</span>
                  <span className="text-gray-900">
                    {property.sale_type === 'public_auction' ? 'Public Auction' : 
                     property.sale_type === 'public_tender' ? 'Public Tender' : 
                     'Public Sale'}
                  </span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Tax Sale Date</span>
                  <span className="text-gray-900">{formatDate(property.sale_date)}</span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Time Left</span>
                  <span className="text-gray-900 font-medium text-green-600">
                    {calculateTimeLeft(property.sale_date)}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div>
                  <span className="block text-sm text-gray-500">Province</span>
                  <span className="text-gray-900">Nova Scotia</span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Municipality</span>
                  <span className="text-gray-900">{property.municipality_name || 'Not specified'}</span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Property Type</span>
                  <span className="text-gray-900">{property.property_type || 'Not specified'}</span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Redeemable</span>
                  <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                    property.redeemable === 'Yes' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {property.redeemable || 'Not specified'}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div>
                  <span className="block text-sm text-gray-500">HST Status</span>
                  <span className="text-gray-900">{property.hst_applicable || 'No HST'}</span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Opening Bid</span>
                  <span className="text-2xl font-bold text-green-600">
                    {formatCurrency(property.tax_owing || property.opening_bid)}
                  </span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Lot Size</span>
                  <span className="text-gray-900">
                    {(() => {
                      const landSize = propertyDetails?.property_details?.land_size || property.lot_size;
                      if (landSize && !landSize.startsWith('.00') && !landSize.startsWith('0.00')) {
                        return landSize;
                      } else if (landSize && (landSize.startsWith('.00') || landSize.startsWith('0.00'))) {
                        return 'Not available in PVSC database';
                      } else if (property.property_type === 'Land') {
                        return 'Not available for land-only properties';
                      } else {
                        return 'Not specified';
                      }
                    })()}
                  </span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Zoning</span>
                  <span className="text-gray-900">{property.zoning || 'Not specified'}</span>
                </div>
              </div>
            </div>

            {/* Property Details Section */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Comprehensive Property Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Full Address</span>
                    <span className="text-gray-900 font-medium">{property.property_address || 'Not available'}</span>
                  </div>
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Assessment Number (AAN)</span>
                    <span className="text-gray-900 font-mono">{property.assessment_number}</span>
                  </div>
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Property Identification (PID)</span>
                    <span className="text-gray-900 font-mono">{property.pid_number || 'Not available'}</span>
                  </div>
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Property Description</span>
                    <span className="text-gray-900">{property.property_description || property.property_address || 'Not available'}</span>
                  </div>
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Assessment Value</span>
                    <span className="text-gray-900 font-semibold">
                      {propertyDetails?.property_details?.current_assessment ? formatCurrency(propertyDetails.property_details.current_assessment) : 
                       propertyDetails?.current_assessment ? formatCurrency(propertyDetails.current_assessment) :
                       property.assessment_value ? formatCurrency(property.assessment_value) : 'Not available'}
                    </span>
                    {propertyDetails?.property_details?.current_assessment && (
                      <span className="block text-xs text-gray-500 mt-1">From PVSC Data: ${propertyDetails.property_details.current_assessment.toLocaleString()}</span>
                    )}
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Current Owner</span>
                    <span className="text-gray-900 font-medium">{property.owner_name || 'Not available'}</span>
                  </div>
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Minimum Bid (Tax Owing)</span>
                    <span className="text-green-600 font-bold text-lg">
                      {formatCurrency(property.tax_owing || property.opening_bid)}
                    </span>
                    <span className="block text-xs text-gray-500 mt-1">
                      Required minimum {property.sale_type === 'public_auction' ? 'bid' : 'tender'} amount
                    </span>
                  </div>
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Sale Date & Time</span>
                    <span className="text-gray-900">
                      {formatDate(property.sale_date)}
                      {property.sale_time && <><br /><span className="text-sm text-gray-600">at {property.sale_time}</span></>}
                    </span>
                  </div>
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Sale Location</span>
                    <span className="text-gray-900">{property.sale_location || 'To be announced'}</span>
                  </div>
                  {propertyDetails?.property_details?.current_assessment && (
                    <div>
                      <span className="block text-sm text-gray-500 mb-1">PVSC Assessment</span>
                      <span className="text-gray-900">{formatCurrency(propertyDetails.property_details.current_assessment)}</span>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Additional Property Characteristics */}
              {(propertyDetails?.property_details?.land_size || property.lot_size || property.zoning || propertyDetails?.property_details?.bedrooms || propertyDetails?.property_details?.bathrooms) && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h4 className="text-lg font-medium text-gray-900 mb-4">Property Characteristics</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {(propertyDetails?.property_details?.land_size || property.lot_size || property.property_type === 'Land') && (
                      <div>
                        <span className="block text-sm text-gray-500">Lot Size</span>
                        <span className="text-gray-900 font-medium">
                          {(() => {
                            const landSize = propertyDetails?.property_details?.land_size || property.lot_size;
                            if (landSize && !landSize.startsWith('.00') && !landSize.startsWith('0.00')) {
                              return landSize;
                            } else if (landSize && (landSize.startsWith('.00') || landSize.startsWith('0.00'))) {
                              return 'Not available in PVSC database';
                            } else if (property.property_type === 'Land') {
                              return 'Not available for land-only properties';
                            } else {
                              return 'Not specified';
                            }
                          })()}
                        </span>
                      </div>
                    )}
                    {property.zoning && (
                      <div>
                        <span className="block text-sm text-gray-500">Zoning</span>
                        <span className="text-gray-900">{property.zoning}</span>
                      </div>
                    )}
                    {propertyDetails?.property_details?.bedrooms && (
                      <div>
                        <span className="block text-sm text-gray-500">Bedrooms</span>
                        <span className="text-gray-900">{propertyDetails.property_details.bedrooms}</span>
                      </div>
                    )}
                    {propertyDetails?.property_details?.bathrooms && (
                      <div>
                        <span className="block text-sm text-gray-500">Bathrooms</span>
                        <span className="text-gray-900">{propertyDetails.property_details.bathrooms}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Enhanced Assessment Information */}
            {propertyDetails?.property_details && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">📊 Detailed Assessment Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 mb-4">
                  {propertyDetails.property_details.current_assessment && (
                    <div>
                      <span className="block text-sm text-gray-500">Current Assessment</span>
                      <span className="text-lg font-semibold text-green-600">{formatCurrency(propertyDetails.property_details.current_assessment)}</span>
                    </div>
                  )}
                  {propertyDetails.property_details.taxable_assessment && (
                    <div>
                      <span className="block text-sm text-gray-500">Taxable Assessment</span>
                      <span className="text-lg font-semibold text-blue-600">{formatCurrency(propertyDetails.property_details.taxable_assessment)}</span>
                    </div>
                  )}
                  {propertyDetails.property_details.building_style && (
                    <div>
                      <span className="block text-sm text-gray-500">Building Style</span>
                      <span className="text-lg font-semibold text-gray-900">{propertyDetails.property_details.building_style}</span>
                    </div>
                  )}
                  {propertyDetails.property_details.quality_of_construction && (
                    <div>
                      <span className="block text-sm text-gray-500">Quality of Construction</span>
                      <span className="text-lg font-semibold text-gray-900">{propertyDetails.property_details.quality_of_construction}</span>
                    </div>
                  )}
                  {propertyDetails.property_details.under_construction !== undefined && (
                    <div>
                      <span className="block text-sm text-gray-500">Under Construction</span>
                      <span className="text-lg font-semibold text-gray-900">{propertyDetails.property_details.under_construction}</span>
                    </div>
                  )}
                  {propertyDetails.property_details.year_built && (
                    <div>
                      <span className="block text-sm text-gray-500">Year Built</span>
                      <span className="text-lg font-semibold text-gray-900">{propertyDetails.property_details.year_built}</span>
                    </div>
                  )}
                  {propertyDetails.property_details.living_units && (
                    <div>
                      <span className="block text-sm text-gray-500">Living Units</span>
                      <span className="text-lg font-semibold text-gray-900">{propertyDetails.property_details.living_units}</span>
                    </div>
                  )}
                  {propertyDetails.property_details.living_area && (
                    <div>
                      <span className="block text-sm text-gray-500">Total Living Area</span>
                      <span className="text-lg font-semibold text-gray-900">{propertyDetails.property_details.living_area} sq ft</span>
                    </div>
                  )}
                  {propertyDetails.property_details.bedrooms !== undefined && (
                    <div>
                      <span className="block text-sm text-gray-500">Bedrooms</span>
                      <span className="text-lg font-semibold text-gray-900">{propertyDetails.property_details.bedrooms}</span>
                    </div>
                  )}
                  {propertyDetails.property_details.bathrooms !== undefined && (
                    <div>
                      <span className="block text-sm text-gray-500"># of Baths</span>
                      <span className="text-lg font-semibold text-gray-900">{propertyDetails.property_details.bathrooms}</span>
                    </div>
                  )}
                  {propertyDetails.property_details.finished_basement !== undefined && (
                    <div>
                      <span className="block text-sm text-gray-500">Finished Basement</span>
                      <span className="text-lg font-semibold text-gray-900">{propertyDetails.property_details.finished_basement}</span>
                    </div>
                  )}
                  {propertyDetails.property_details.garage && (
                    <div>
                      <span className="block text-sm text-gray-500">Garage</span>
                      <span className="text-lg font-semibold text-gray-900">{propertyDetails.property_details.garage}</span>
                    </div>
                  )}
                  {propertyDetails.property_details.land_size && (
                    <div>
                      <span className="block text-sm text-gray-500">Land Size</span>
                      <span className="text-lg font-semibold text-gray-900">{propertyDetails.property_details.land_size}</span>
                    </div>
                  )}
                </div>
                <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                  <p className="text-sm text-blue-800">
                    ℹ️ This enhanced information is sourced from the Property Valuation Services Corporation (PVSC) and provides official assessment details for this property.
                  </p>
                </div>
              </div>
            )}

            {/* Legal Description */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Legal Description</h3>
              <p className="text-gray-700 leading-relaxed">
                {property.assessment_number}; {property.owner_name || 'Owner Not Listed'}; {property.property_address || 'Address Not Available'}; 
                <span className="font-medium">
                  PID: {property.pid_number}
                  {property.pid_number && property.pid_number.includes('/') && (
                    <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">
                      Multiple PIDs
                    </span>
                  )}
                </span>
                ; {formatCurrency(property.opening_bid)}; {property.hst_applicable || 'No HST'}
              </p>
            </div>

            {/* Location & Boundaries */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Location & Property Boundaries</h3>
              
              {/* Interactive Map */}
              {property.latitude && property.longitude && (
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">Interactive Map with Property Boundaries</h4>
                  <div className="border rounded-lg overflow-hidden">
                    <div 
                      ref={mapRef}
                      style={{ width: '100%', height: '400px' }}
                      className="bg-gray-100"
                    />
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    📍 Property Location: {property.latitude}, {property.longitude}
                    {boundaryData && (
                      <span className="ml-4 text-green-600">
                        🔴 NSPRD Boundaries: {Math.round(boundaryData.property_info?.area_sqm || 0).toLocaleString()} sqm
                        {boundaryData.pid_count > 1 && (
                          <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                            {boundaryData.pid_count} PIDs Combined
                          </span>
                        )}
                      </span>
                    )}
                  </p>
                </div>
              )}
              
              {/* Address Information */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">📍 Official Civic Address:</h4>
                <p className="text-blue-800">{property.property_address || 'Address not available'}</p>
                <p className="text-sm text-blue-600 mt-1">This is the official municipal address from PVSC records</p>
              </div>
            </div>

            {/* Municipality-Specific Information */}
            {municipalityData?.description && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">{property.municipality_name} Tax Sale Information</h3>
                <div className="prose max-w-none text-gray-700">
                  <div className="whitespace-pre-line">{municipalityData.description}</div>
                </div>
              </div>
            )}
            
            {/* Default Description if no municipality-specific description */}
            {!municipalityData?.description && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Tax Sale Information</h3>
                <div className="prose max-w-none text-gray-700">
                  <p className="mb-4">
                    This property is available for tax sale by {
                      property.sale_type === 'public_auction' ? 'auction' : 
                      property.sale_type === 'public_tender' ? 'tender' : 
                      'public sale'
                    }.
                  </p>
                  <p className="mb-4">Please contact {property.municipality_name || 'the municipality'} directly for specific bidding instructions, submission methods, and deadlines.</p>
                  <p>
                    The municipality reserves the right to reject any or all {
                      property.sale_type === 'public_auction' ? 'bids' : 'tenders'
                    } or to accept any {
                      property.sale_type === 'public_auction' ? 'bid' : 'tender'
                    } considered to be in its best interest.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Right Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Minimum Bid Box */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-green-900 mb-2">Minimum Bid</h3>
              <div className="flex items-baseline">
                <span className="text-4xl font-bold text-green-800">
                  {formatCurrency(property.tax_owing || property.opening_bid)}
                </span>
                <span className="text-lg text-green-600 ml-2">CAD</span>
              </div>
              <p className="text-sm text-green-700 mt-2">Tax Owing Amount</p>
              
              {/* Auction Result Section */}
              {property.auction_result && (
                <div className="mt-4 pt-4 border-t border-green-200">
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Auction Result</h4>
                  <div className="flex items-center mb-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      property.auction_result === 'sold' ? 'bg-blue-100 text-blue-800' :
                      property.auction_result === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      property.auction_result === 'canceled' ? 'bg-red-100 text-red-800' :
                      property.auction_result === 'deferred' ? 'bg-orange-100 text-orange-800' :
                      property.auction_result === 'taxes_paid' ? 'bg-green-100 text-green-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {property.auction_result === 'sold' ? 'Sold' :
                       property.auction_result === 'pending' ? 'Auction Results Pending' :
                       property.auction_result === 'canceled' ? 'Auction Canceled' :
                       property.auction_result === 'deferred' ? 'Auction Deferred' :
                       property.auction_result === 'taxes_paid' ? 'Taxes Paid (Redeemed)' :
                       property.auction_result}
                    </span>
                  </div>
                  
                  {/* Winning Bid Amount for Sold Properties */}
                  {property.auction_result === 'sold' && property.winning_bid_amount && (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mt-2">
                      <div className="flex items-baseline">
                        <span className="text-2xl font-bold text-blue-800">
                          {formatCurrency(property.winning_bid_amount)}
                        </span>
                        <span className="text-sm text-blue-600 ml-2">CAD</span>
                      </div>
                      <p className="text-sm text-blue-700 mt-1">Final Sale Price</p>
                    </div>
                  )}
                  
                  {/* Pending Results Message */}
                  {property.auction_result === 'pending' && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mt-2">
                      <p className="text-sm text-yellow-800">
                        The auction has ended. Official results will be posted once available.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* AdSense Ad Block */}
            <div className="bg-white rounded-lg shadow-sm p-4">
              <div className="text-center text-sm text-gray-500 mb-2">Advertisement</div>
              <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5947395928510215"
                   crossOrigin="anonymous"></script>
              <ins className="adsbygoogle"
                   style={{display:'block'}}
                   data-ad-client="ca-pub-5947395928510215"
                   data-ad-slot="3653544552"
                   data-ad-format="auto"
                   data-full-width-responsive="true">
              </ins>
              <script>
                   {`(adsbygoogle = window.adsbygoogle || []).push({});`}
              </script>
            </div>

            {/* External Resources */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">External Resources</h3>
              <div className="space-y-3">
                {property.pid_number && (
                  <a
                    href={`https://www.viewpoint.ca/show/property/${property.pid_number}/1/${property.property_address?.replace(/\s+/g, '-')}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-blue-600 text-white text-center py-3 px-4 rounded-md hover:bg-blue-700 transition-colors font-medium"
                  >
                    View Property on Viewpoint.ca
                  </a>
                )}
                <a
                  href={`https://webapi.pvsc.ca/Search/Property?ain=${property.assessment_number}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full bg-green-600 text-white text-center py-3 px-4 rounded-md hover:bg-green-700 transition-colors font-medium"
                >
                  View PVSC Assessment Details
                </a>
                <a
                  href={getTaxSaleUrl()}
                  target={getTaxSaleUrl() !== '#' ? "_blank" : "_self"}
                  rel={getTaxSaleUrl() !== '#' ? "noopener noreferrer" : undefined}
                  className={`block w-full text-white text-center py-3 px-4 rounded-md transition-colors font-medium ${
                    getTaxSaleUrl() !== '#' 
                      ? 'bg-gray-600 hover:bg-gray-700 cursor-pointer' 
                      : 'bg-gray-400 cursor-not-allowed'
                  }`}
                  onClick={getTaxSaleUrl() === '#' ? (e) => e.preventDefault() : undefined}
                >
                  {property.municipality_name || 'Municipality'} Tax Sale Info
                  {!municipalityData && ' (Loading...)'}
                  {municipalityData && getTaxSaleUrl() === '#' && ' (Not Available)'}
                </a>
              </div>
            </div>

            {/* Owner Information */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Owner Information</h3>
              <div className="space-y-4">
                <div>
                  <span className="block text-sm text-gray-500 mb-1">Current Owner</span>
                  <span className="text-gray-900 font-medium">{property.owner_name || 'Not available'}</span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500 mb-1">Property Classification</span>
                  <span className="text-gray-900">
                    {propertyDetails?.property_type || 'Dwelling'} 
                    {propertyDetails?.year_built && ` (Built ${propertyDetails.year_built})`}
                  </span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500 mb-1">Tax Sale Municipality</span>
                  <span className="text-gray-900">{property.municipality_name || 'Not specified'}</span>
                </div>
              </div>
            </div>

            {/* Important Notice */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <h4 className="font-semibold text-yellow-800 mb-3">Important Notice</h4>
              <p className="text-yellow-700 text-sm leading-relaxed">
                This is a tax sale property. Please conduct thorough due diligence before bidding. The municipality does not guarantee the accuracy of the information provided.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertyDetails;