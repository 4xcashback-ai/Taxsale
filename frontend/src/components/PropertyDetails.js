import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

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
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://nova-taxmap.preview.emergentagent.com';
      
      // Find the property by assessment number
      const response = await fetch(`${backendUrl}/api/tax-sales`);
      const properties = await response.json();
      
      const foundProperty = properties.find(p => p.assessment_number === assessmentNumber);
      
      if (foundProperty) {
        setProperty(foundProperty);
      } else {
        setError('Property not found');
      }
    } catch (error) {
      console.error('Error fetching property details:', error);
      setError('Failed to load property details');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not specified';
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
      <div className="bg-white shadow-sm">
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
              <span className="text-gray-900 font-medium">{property.assessment_number}</span>
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

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Property Details - Main Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Header */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    {property.property_address || 'Address not available'}
                  </h1>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span className="flex items-center">
                      Halifax Regional Municipality, Nova Scotia
                    </span>
                    <span>Assessment #{property.assessment_number}</span>
                  </div>
                </div>
                <div className="ml-4 text-right">
                  <div className="text-3xl font-bold text-green-600">
                    {formatCurrency(property.opening_bid || 0)}
                  </div>
                  <div className="text-sm text-gray-500">Opening Bid</div>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  property.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {property.status || 'Unknown Status'}
                </span>
                {property.property_type && (
                  <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    {property.property_type}
                  </span>
                )}
              </div>
            </div>

            {/* Property Information */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Property Information</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Owner</h3>
                  <p className="text-gray-900">{property.owner_name || 'Not available'}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-1">PID Number</h3>
                  <p className="text-gray-900">{property.pid_number || 'Not available'}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Assessment Number</h3>
                  <p className="text-gray-900">{property.assessment_number}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Municipality</h3>
                  <p className="text-gray-900">{property.municipality_name || property.municipality || 'Halifax Regional Municipality'}</p>
                </div>
              </div>
            </div>

            {/* Sale Information */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Sale Information</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Sale Date</h3>
                  <p className="text-gray-900">{formatDate(property.sale_date)}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Sale Time</h3>
                  <p className="text-gray-900">{property.sale_time || 'Not specified'}</p>
                </div>
                <div className="sm:col-span-2">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Sale Location</h3>
                  <p className="text-gray-900">{property.sale_location || 'Not specified'}</p>
                </div>
              </div>

              {/* Minimum Bid Box */}
              <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-blue-900">Minimum Bid</h3>
                    <p className="text-sm text-blue-700">Starting amount for this tax sale</p>
                  </div>
                  <div className="text-2xl font-bold text-blue-900">
                    {formatCurrency(property.opening_bid || 0)}
                  </div>
                </div>
              </div>
            </div>

            {/* Legal Information */}
            {(property.redeemable || property.hst_applicable) && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-yellow-800 mb-3">
                  Important Legal Information
                </h2>
                <div className="space-y-2 text-sm text-yellow-700">
                  {property.redeemable && (
                    <div>
                      <strong>Redemption Rights:</strong> {property.redeemable}
                    </div>
                  )}
                  {property.hst_applicable && (
                    <div>
                      <strong>HST:</strong> {property.hst_applicable}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Property Images/Map */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Location</h2>
              
              {/* Property Image */}
              {(property.boundary_screenshot || (property.latitude && property.longitude)) && (
                <div className="mb-4">
                  <div className="border rounded-lg overflow-hidden">
                    {property.boundary_screenshot ? (
                      <img
                        src={`${process.env.REACT_APP_BACKEND_URL || 'https://nova-taxmap.preview.emergentagent.com'}/api/boundary-image/${property.boundary_screenshot}`}
                        alt="Property boundary"
                        className="w-full h-64 object-cover"
                      />
                    ) : (
                      <img
                        src={`https://maps.googleapis.com/maps/api/staticmap?center=${property.latitude},${property.longitude}&zoom=17&size=400x300&maptype=satellite&key=${process.env.REACT_APP_GOOGLE_MAPS_API_KEY || 'AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY'}`}
                        alt="Satellite view"
                        className="w-full h-64 object-cover"
                      />
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
              <div className="space-y-3">
                {property.source_url && (
                  <a
                    href={property.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-blue-600 text-white text-center py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
                  >
                    View Official Document
                  </a>
                )}
                <button
                  onClick={() => navigate('/')}
                  className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 transition-colors"
                >
                  ← Back to Search
                </button>
              </div>
            </div>

            {/* Property Stats */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Stats</h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Opening Bid</span>
                  <span className="font-medium">{formatCurrency(property.opening_bid || 0)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Status</span>
                  <span className={`font-medium ${property.status === 'active' ? 'text-green-600' : 'text-gray-600'}`}>
                    {property.status || 'Unknown'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Municipality</span>
                  <span className="font-medium">Halifax</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertyDetails;