import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default markers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// AdSense Component
const AdSenseAd = () => {
  useEffect(() => {
    try {
      if (window.adsbygoogle) {
        window.adsbygoogle.push({});
      }
    } catch (err) {
      console.log('AdSense error:', err);
    }
  }, []);

  return (
    <ins className="adsbygoogle"
         style={{display:'block'}}
         data-ad-client="ca-pub-5947395928510215"
         data-ad-slot="3653544552"
         data-ad-format="auto"
         data-full-width-responsive="true">
    </ins>
  );
};

const PropertyDetails = ({ property, onClose }) => {
  const [boundaryImage, setBoundaryImage] = useState(null);
  const [boundaryLoading, setBoundaryLoading] = useState(false);

  useEffect(() => {
    if (property?.assessment_number) {
      fetchBoundaryImage();
    }
  }, [property]);

  const fetchBoundaryImage = async () => {
    try {
      setBoundaryLoading(true);
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/property/${property.assessment_number}/boundary-image`);
      
      if (response.ok) {
        const boundaryData = await response.json();
        setBoundaryImage(boundaryData);
      }
    } catch (error) {
      console.warn('Could not fetch boundary image:', error);
    } finally {
      setBoundaryLoading(false);
    }
  };


  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-CA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (!property) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Property Not Found</h2>
          <p className="text-gray-600 mb-6">The requested property could not be found.</p>
          <button
            onClick={onClose}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Return to Property Search
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Navigation */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <nav className="flex items-center space-x-2 text-sm text-gray-500">
              <button 
                onClick={onClose}
                className="hover:text-blue-600 transition-colors"
              >
                Nova Scotia Tax Sales
              </button>
              <span>›</span>
              <span className="text-gray-900 font-medium">Halifax</span>
              <span>›</span>
              <span className="text-gray-900 font-medium">{property.assessment_number}</span>
            </nav>
            <button
              onClick={onClose}
              className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 transition-colors"
            >
              ← Back to Search
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Property Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="border-b border-gray-200 pb-6 mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Tax Sale Property in Halifax, Nova Scotia
            </h1>
            <p className="text-xl text-gray-600 mb-4">{property.property_address}</p>
            <div className="flex flex-wrap gap-4 text-sm">
              <span className="font-semibold">AAN: {property.assessment_number}</span>
              <span className="text-gray-400">•</span>
              <span className="font-semibold">PID: {property.pid_number}</span>
            </div>
          </div>

          {/* Key Information Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1 text-sm text-gray-900">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Active
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Sale Type</dt>
              <dd className="mt-1 text-sm text-gray-900">Public Tender</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Tax Sale Date</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {property.sale_date ? formatDate(property.sale_date) : 'TBD'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Municipality</dt>
              <dd className="mt-1 text-sm text-gray-900">{property.municipality_name || property.municipality || 'Halifax Regional Municipality'}</dd>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Details */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Property Details */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Property Details</h2>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Address</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {property.civic_address || property.property_address}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Property Type</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {property.property_details?.building_style || 
                     (property.property_description?.includes('Dwelling') ? 'Dwelling' : 
                      property.property_description?.includes('Land') ? 'Land' : 'Property')}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Assessment Number</dt>
                  <dd className="mt-1 text-sm text-gray-900">{property.assessment_number}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">PID</dt>
                  <dd className="mt-1 text-sm text-gray-900">{property.pid_number}</dd>
                </div>
                {property.property_details?.current_assessment && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Current Assessment</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {formatCurrency(property.property_details.current_assessment)}
                    </dd>
                  </div>
                )}
                {property.property_details?.land_size && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Land Size</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {property.property_details.land_size}
                    </dd>
                  </div>
                )}
                {property.property_details?.year_built && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Year Built</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {property.property_details.year_built}
                    </dd>
                  </div>
                )}
                {property.property_details?.living_area && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Living Area</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {property.property_details.living_area.toLocaleString()} sq ft
                    </dd>
                  </div>
                )}
                <div>
                  <dt className="text-sm font-medium text-gray-500">Redeemable</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      property.redeemable === 'Redeemable' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {property.redeemable}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">HST Status</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      property.hst_applicable === 'HST Applicable' 
                        ? 'bg-yellow-100 text-yellow-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {property.hst_applicable}
                    </span>
                  </dd>
                </div>
              </dl>
            </div>

            {/* Enhanced Property Information (if available from PVSC) */}
            {property.property_details && (
              <div className="bg-blue-50 rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-blue-900 mb-4">📊 Detailed Assessment Information</h2>
                <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {property.property_details.bedrooms !== undefined && (
                    <div>
                      <dt className="text-sm font-medium text-blue-700">Bedrooms</dt>
                      <dd className="mt-1 text-sm text-blue-900">
                        {property.property_details.bedrooms}
                      </dd>
                    </div>
                  )}
                  {property.property_details.bathrooms !== undefined && (
                    <div>
                      <dt className="text-sm font-medium text-blue-700">Bathrooms</dt>
                      <dd className="mt-1 text-sm text-blue-900">
                        {property.property_details.bathrooms}
                      </dd>
                    </div>
                  )}
                  {property.property_details.taxable_assessment && (
                    <div>
                      <dt className="text-sm font-medium text-blue-700">Taxable Assessment</dt>
                      <dd className="mt-1 text-sm text-blue-900">
                        {formatCurrency(property.property_details.taxable_assessment)}
                        <span className="text-xs text-blue-600 block">Used for tax calculation</span>
                      </dd>
                    </div>
                  )}
                  {property.property_details.building_style && (
                    <div>
                      <dt className="text-sm font-medium text-blue-700">Building Style</dt>
                      <dd className="mt-1 text-sm text-blue-900">
                        {property.property_details.building_style}
                      </dd>
                    </div>
                  )}
                </dl>
                <div className="mt-4 p-3 bg-blue-100 rounded-lg">
                  <p className="text-xs text-blue-800">
                    ℹ️ This enhanced information is sourced from the Property Valuation Services Corporation (PVSC) 
                    and provides official assessment details for this property.
                  </p>
                </div>
              </div>
            )}

            {/* Legal Description */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Legal Description</h2>
              <p className="text-sm text-gray-700">
                {property.assessment_number}; {property.owner_name}; {property.property_address}; {property.pid_number}; {formatCurrency(property.opening_bid)}; {property.hst_applicable}
              </p>
            </div>

            {/* Location & Satellite View */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Location & Property Boundaries</h2>
              
              {/* Property Boundary Satellite View */}
              {boundaryImage && boundaryImage.has_boundary_image ? (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Satellite Property View</h3>
                  <div className="relative">
                    <img 
                      src={`${process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL}${boundaryImage.image_url}`}
                      alt={`Property boundary map of ${property.property_address}`}
                      className="w-full h-80 object-cover rounded-lg border"
                      onLoad={() => console.log('Boundary image loaded successfully')}
                      onError={(e) => {
                        console.error('Boundary image failed to load:', e.target.src);
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'block';
                      }}
                    />
                    <div 
                      className="hidden w-full h-80 bg-gray-100 rounded-lg border flex items-center justify-center"
                    >
                      <div className="text-center">
                        <p className="text-gray-500">Satellite image not available</p>
                        <p className="text-xs text-gray-400 mt-1">URL: {boundaryImage.image_url}</p>
                      </div>
                    </div>
                    <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs">
                      High-resolution satellite view
                    </div>
                  </div>
                </div>
              ) : boundaryImage && boundaryImage.ready_for_capture ? (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Satellite Property View</h3>
                  <div className="w-full h-80 bg-gradient-to-br from-blue-50 to-green-50 rounded-lg border border-dashed border-gray-300 flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-4xl mb-4">🛰️</div>
                      <h4 className="text-lg font-medium text-gray-900 mb-2">Satellite View Available</h4>
                      <p className="text-gray-600 mb-4">High-resolution satellite imagery shows property boundaries and surrounding area</p>
                      <div className="space-y-2">
                        <a
                          href={boundaryImage.google_maps_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                        >
                          🗺️ View Satellite Image
                        </a>
                        <p className="text-xs text-gray-500">Opens in Google Maps satellite view</p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : boundaryLoading ? (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Satellite Property View</h3>
                  <div className="w-full h-80 bg-gray-100 rounded-lg border flex items-center justify-center">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                      <p className="text-gray-600">Loading satellite view...</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Satellite Property View</h3>
                  <div className="w-full h-80 bg-gray-100 rounded-lg border flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <p>Satellite view not available</p>
                      <p className="text-sm">No boundary image data for this property</p>
                      <p className="text-xs mt-2">API Response: {JSON.stringify(boundaryImage)}</p>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Interactive Map with Property Boundaries */}
              <h3 className="text-lg font-medium text-gray-900 mb-3">Interactive Map with Property Boundaries</h3>
              {property.latitude && property.longitude ? (
                <div className="w-full h-96 rounded-lg overflow-hidden border border-slate-200">
                  <div 
                    id="google-map-with-boundaries"
                    className="w-full h-full"
                    ref={(node) => {
                      if (node && !node.hasChildNodes()) {
                        if (window.google && window.google.maps) {
                          // Create Google Map
                          const map = new window.google.maps.Map(node, {
                            center: { lat: property.latitude, lng: property.longitude },
                            zoom: 17,
                            mapTypeControl: true,
                            streetViewControl: true,
                            fullscreenControl: true,
                            zoomControl: true
                          });
                          
                          // Add property marker
                          const marker = new window.google.maps.Marker({
                            position: { lat: property.latitude, lng: property.longitude },
                            map: map,
                            title: property.property_address,
                            icon: {
                              path: window.google.maps.SymbolPath.CIRCLE,
                              fillColor: '#dc2626',
                              fillOpacity: 1,
                              strokeColor: 'white',
                              strokeWeight: 2,
                              scale: 8
                            }
                          });
                          
                          // Add property boundary polygon if we have government data
                          if (property.government_boundary_data) {
                            fetch(`${process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL}/api/query-ns-government-parcel/${property.pid_number}`)
                              .then(response => response.json())
                              .then(data => {
                                if (data.found && data.geometry && data.geometry.rings) {
                                  // Convert NSPRD polygon to Google Maps format
                                  const paths = data.geometry.rings.map(ring => 
                                    ring.map(coord => ({ lat: coord[1], lng: coord[0] }))
                                  );
                                  
                                  // Create property boundary polygon
                                  const propertyPolygon = new window.google.maps.Polygon({
                                    paths: paths,
                                    strokeColor: '#dc2626',
                                    strokeOpacity: 0.8,
                                    strokeWeight: 3,
                                    fillColor: '#dc2626',
                                    fillOpacity: 0.2,
                                    map: map
                                  });
                                  
                                  // Fit map to show entire property
                                  const bounds = new window.google.maps.LatLngBounds();
                                  paths.forEach(path => {
                                    path.forEach(point => bounds.extend(point));
                                  });
                                  map.fitBounds(bounds);
                                }
                              })
                              .catch(error => console.warn('Could not load property boundaries:', error));
                          }
                          
                          // Add info window
                          const infoWindow = new window.google.maps.InfoWindow({
                            content: `
                              <div style="max-width: 250px;">
                                <h3 style="margin: 0 0 8px 0; color: #1f2937;">${property.property_address}</h3>
                                <p style="margin: 4px 0; color: #6b7280;"><strong>PID:</strong> ${property.pid_number}</p>
                                <p style="margin: 4px 0; color: #6b7280;"><strong>Assessment:</strong> ${property.assessment_number}</p>
                                <p style="margin: 4px 0; color: #6b7280;"><strong>Opening Bid:</strong> $${parseFloat(property.opening_bid || 0).toLocaleString()}</p>
                                ${property.government_boundary_data ? `<p style="margin: 4px 0; color: #6b7280;"><strong>Area:</strong> ${Math.round(property.government_boundary_data.area_sqm)} sqm</p>` : ''}
                              </div>
                            `
                          });
                          
                          marker.addListener('click', () => {
                            infoWindow.open(map, marker);
                          });
                        } else {
                          // Fallback to iframe if Google Maps API is not available
                          node.innerHTML = `
                            <iframe
                              src="https://www.google.com/maps?q=${property.latitude},${property.longitude}&output=embed&z=16"
                              width="100%"
                              height="100%"
                              style="border: 0"
                              allowfullscreen=""
                              loading="lazy"
                              referrerpolicy="no-referrer-when-downgrade"
                              title="Property Location Map"
                            ></iframe>
                          `;
                        }
                      }
                    }}
                  />
                </div>
              ) : (
                <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <div className="text-4xl mb-4">🗺️</div>
                    <p>No location data available for this property</p>
                  </div>
                </div>
              )}
              
              {property.civic_address && property.civic_address !== property.property_address && (
                <div className="mt-4 p-3 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-800">
                    <strong>📍 Official Civic Address:</strong> {property.civic_address}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    This is the official municipal address from PVSC records
                  </p>
                </div>
              )}
              
              {property.property_details?.geocoded_address && (
                <div className="mt-2 p-2 bg-blue-50 rounded">
                  <p className="text-xs text-blue-600">
                    📍 Geocoded Address: {property.property_details.geocoded_address}
                  </p>
                </div>
              )}
            </div>

            {/* Description */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Description</h2>
              <div className="prose prose-sm text-gray-700">
                <p className="font-semibold mb-2">SEALED TENDERS are to be submitted:</p>
                <ul className="list-disc pl-5 space-y-1 mb-4">
                  <li>In digital format via submission to Halifax Regional Municipality's website</li>
                  <li>On the Halifax Regional Municipality's bid form in a plain envelope marked "Halifax Regional Municipality Tax Sale Property Tender"</li>
                </ul>
                <p className="mb-4">
                  These bids will only be accepted until the specified deadline.
                  HRM will not accept bids submitted by any other method, including by facsimile or email.
                </p>
                <p className="font-semibold">
                  The Halifax Regional Municipality reserves the right to reject any or all tenders or to accept any tender or part thereof considered to be in its best interest.
                </p>
              </div>
            </div>
          </div>

          {/* Right Column - Financial Info and Actions */}
          <div className="space-y-6">
            
            {/* Minimum Bid */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Minimum Bid</h2>
              <p className="text-3xl font-bold text-green-600 mb-2">
                {formatCurrency(property.opening_bid)}
              </p>
              <p className="text-sm text-gray-500">CAD</p>
            </div>

            {/* Google AdSense - Detail Page */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <AdSenseAd />
            </div>

            {/* External Links */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">External Resources</h2>
              <div className="space-y-3">
                <a
                  href={`https://www.viewpoint.ca/show/property/${property.pid_number}/1/${property.property_address.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '').substring(0, 50)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full text-center bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
                >
                  View Property on Viewpoint.ca
                </a>
                <a
                  href={`https://webapi.pvsc.ca/Search/Property?ain=${property.assessment_number}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full text-center bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors"
                >
                  View PVSC Assessment Details
                </a>
                <a
                  href="https://www.halifax.ca/home-property/property-taxes/tax-sales"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full text-center bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors"
                >
                  Halifax Tax Sale Info
                </a>
              </div>
            </div>

            {/* Property Information */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Owner Information</h2>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Current Owner</dt>
                  <dd className="mt-1 text-sm text-gray-900">{property.owner_name}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Property Classification</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {property.property_details?.building_style ? 
                      `${property.property_details.building_style} ${property.property_details.year_built ? `(Built ${property.property_details.year_built})` : ''}`.trim() :
                      (property.property_description?.includes('Dwelling') ? 'Residential Property' : 
                       property.property_description?.includes('Land') ? 'Vacant Land' : 'Property')
                    }
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Tax Sale Municipality</dt>
                  <dd className="mt-1 text-sm text-gray-900">{property.municipality_name || property.municipality || 'Halifax Regional Municipality'}</dd>
                </div>
                {property.updated_at && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Data Last Updated</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {formatDate(property.updated_at)}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Share Section */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Share Property</h3>
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    const url = window.location.href;
                    const text = `Tax Sale Property in Halifax: ${property.property_address} - Opening bid: ${formatCurrency(property.opening_bid)}`;
                    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}&quote=${encodeURIComponent(text)}`;
                    window.open(facebookUrl, '_blank');
                  }}
                  className="flex-1 bg-blue-600 text-white py-2 px-3 rounded text-sm hover:bg-blue-700 transition-colors"
                >
                  Facebook
                </button>
                <button
                  onClick={() => {
                    const url = window.location.href;
                    const text = `Tax Sale Property in Halifax: ${property.property_address} - Opening bid: ${formatCurrency(property.opening_bid)}`;
                    const twitterUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
                    window.open(twitterUrl, '_blank');
                  }}
                  className="flex-1 bg-gray-800 text-white py-2 px-3 rounded text-sm hover:bg-gray-900 transition-colors"
                >
                  Twitter
                </button>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(window.location.href);
                    alert('Link copied to clipboard!');
                  }}
                  className="flex-1 bg-gray-600 text-white py-2 px-3 rounded text-sm hover:bg-gray-700 transition-colors"
                >
                  Copy Link
                </button>
              </div>
            </div>

            {/* Disclaimer */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-yellow-800 mb-2">Important Notice</h4>
              <p className="text-xs text-yellow-700">
                This is a tax sale property. Please conduct thorough due diligence before bidding. 
                The municipality does not guarantee the accuracy of the information provided.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertyDetails;