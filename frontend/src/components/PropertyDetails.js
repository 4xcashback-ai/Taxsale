import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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

const PropertyDetails = () => {
  const { assessmentNumber } = useParams();
  const navigate = useNavigate();
  const [property, setProperty] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPropertyDetails();
  }, [assessmentNumber]);

  const fetchPropertyDetails = async () => {
    try {
      setLoading(true);
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      // Try to get enhanced details first
      try {
        const enhancedResponse = await fetch(`${backendUrl}/api/property/${assessmentNumber}/enhanced`);
        if (enhancedResponse.ok) {
          const enhancedProperty = await enhancedResponse.json();
          setProperty(enhancedProperty);
          return;
        }
      } catch (enhancedError) {
        console.warn('Enhanced data not available, falling back to basic data:', enhancedError);
      }
      
      // Fallback to basic property list
      const response = await fetch(`${backendUrl}/api/tax-sales`);
      if (!response.ok) throw new Error('Failed to fetch properties');
      
      const properties = await response.json();
      const foundProperty = properties.find(p => p.assessment_number === assessmentNumber);
      
      if (foundProperty) {
        setProperty(foundProperty);
      } else {
        setError('Property not found');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading property details...</p>
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
                onClick={() => navigate('/')}
                className="hover:text-blue-600 transition-colors"
              >
                Nova Scotia Tax Sales
              </button>
              <span>›</span>
              <span className="text-gray-900 font-medium">Halifax</span>
              <span>›</span>
              <span className="text-gray-900 font-medium">{assessmentNumber}</span>
            </nav>
            <button
              onClick={() => navigate('/')}
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
              <dd className="mt-1 text-sm text-gray-900">{property.municipality}</dd>
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

            {/* Location Map */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Location on Map</h2>
              
              {/* Google Maps Link Button */}
              {property.google_maps_link && (
                <div className="mb-4">
                  <a
                    href={property.google_maps_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                  >
                    🗺️ View on Google Maps
                  </a>
                  <p className="text-xs text-gray-500 mt-1">
                    Click to see the exact location with street view and directions
                  </p>
                </div>
              )}
              
              <div className="h-64 w-full rounded-lg overflow-hidden">
                {property.latitude && property.longitude ? (
                  <MapContainer
                    center={[property.latitude, property.longitude]}
                    zoom={15}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />
                    <Marker position={[property.latitude, property.longitude]}>
                      <Popup>
                        <div>
                          <strong>{property.civic_address || property.property_address}</strong><br/>
                          AAN: {property.assessment_number}<br/>
                          Opening Bid: {formatCurrency(property.opening_bid)}
                        </div>
                      </Popup>
                    </Marker>
                  </MapContainer>
                ) : (
                  <div className="bg-gray-100 h-full flex items-center justify-center flex-col">
                    <p className="text-gray-500 mb-2">Interactive map coordinates not available</p>
                    {property.google_maps_link && (
                      <p className="text-sm text-gray-400">Use the Google Maps button above for location details</p>
                    )}
                  </div>
                )}
              </div>
              
              {property.civic_address && property.civic_address !== property.property_address && (
                <div className="mt-4 p-3 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-800">
                    <strong>Official Civic Address:</strong> {property.civic_address}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    This is the official municipal address from PVSC records
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
                  <dt className="text-sm font-medium text-gray-500">Property ID</dt>
                  <dd className="mt-1 text-sm text-gray-900">{property.id}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {property.updated_at ? formatDate(property.updated_at) : 'Recently'}
                  </dd>
                </div>
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