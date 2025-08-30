import React from 'react';

const PropertyDetails = ({ property, onClose }) => {
  if (!property) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Property Not Found</h2>
        <p className="text-gray-600 mb-6">The requested property could not be found.</p>
        <button
          onClick={onClose}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          Return to Property Search
        </button>
      </div>
    );
  }

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

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b pb-4 mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {property.property_address || 'Address not available'}
        </h1>
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <span>Assessment #: {property.assessment_number}</span>
          {property.pid_number && <span>PID: {property.pid_number}</span>}
        </div>
      </div>

      {/* Property Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <h3 className="text-lg font-semibold mb-3">Property Information</h3>
          <div className="space-y-2 text-sm">
            <div><strong>Owner:</strong> {property.owner_name || 'Not available'}</div>
            <div><strong>Municipality:</strong> {property.municipality_name || property.municipality || 'Halifax Regional Municipality'}</div>
            <div><strong>Property Type:</strong> {property.property_type || 'Not specified'}</div>
            <div><strong>Status:</strong> 
              <span className={`ml-2 px-2 py-1 rounded text-xs ${
                property.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {property.status || 'Unknown'}
              </span>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-3">Sale Information</h3>
          <div className="space-y-2 text-sm">
            <div><strong>Opening Bid:</strong> 
              <span className="text-2xl font-bold text-green-600 ml-2">
                {formatCurrency(property.opening_bid || 0)}
              </span>
            </div>
            <div><strong>Sale Date:</strong> {formatDate(property.sale_date)}</div>
            <div><strong>Sale Time:</strong> {property.sale_time || 'Not specified'}</div>
            <div><strong>Sale Location:</strong> {property.sale_location || 'Not specified'}</div>
          </div>
        </div>
      </div>

      {/* Additional Details */}
      {(property.redeemable || property.hst_applicable) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-yellow-800 mb-2">Important Legal Information</h3>
          <div className="space-y-1 text-sm text-yellow-700">
            {property.redeemable && (
              <div><strong>Redemption:</strong> {property.redeemable}</div>
            )}
            {property.hst_applicable && (
              <div><strong>HST:</strong> {property.hst_applicable}</div>
            )}
          </div>
        </div>
      )}

      {/* Property Image */}
      {(property.boundary_screenshot || (property.latitude && property.longitude)) && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Property Location</h3>
          <div className="border rounded-lg overflow-hidden">
            {property.boundary_screenshot ? (
              <img
                src={`${(typeof window !== 'undefined' && window.REACT_APP_BACKEND_URL) || process.env.REACT_APP_BACKEND_URL || (typeof import !== 'undefined' && import.meta?.env?.REACT_APP_BACKEND_URL) || 'https://nova-taxmap.preview.emergentagent.com'}/api/boundary-image/${property.boundary_screenshot}`}
                alt="Property boundary"
                className="w-full h-64 object-cover"
              />
            ) : (
              <img
                src={`https://maps.googleapis.com/maps/api/staticmap?center=${property.latitude},${property.longitude}&zoom=17&size=800x300&maptype=satellite&key=${process.env.REACT_APP_GOOGLE_MAPS_API_KEY}`}
                alt="Satellite view"
                className="w-full h-64 object-cover"
              />
            )}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between items-center pt-6 border-t">
        <button
          onClick={onClose}
          className="bg-gray-100 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-200 transition-colors"
        >
          ← Back to Search
        </button>
        
        <div className="space-x-4">
          {property.source_url && (
            <a
              href={property.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              View Official Document
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default PropertyDetails;