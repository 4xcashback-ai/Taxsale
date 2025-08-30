import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';

const PropertyDetails = () => {
  const { assessmentNumber } = useParams();
  const navigate = useNavigate();
  const [property, setProperty] = useState(null);
  const [propertyDetails, setPropertyDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPropertyDetails();
  }, [assessmentNumber]);

  const fetchPropertyDetails = async () => {
    try {
      setLoading(true);
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://taxsale-ns.preview.emergentagent.com';
      
      // Find the property by assessment number
      const response = await fetch(`${backendUrl}/api/tax-sales`);
      const properties = await response.json();
      
      const foundProperty = properties.find(p => p.assessment_number === assessmentNumber);
      
      if (foundProperty) {
        setProperty(foundProperty);
        
        // Try to fetch enhanced property details
        try {
          const enhancedResponse = await fetch(`${backendUrl}/api/property/${assessmentNumber}/enhanced`);
          if (enhancedResponse.ok) {
            const enhanced = await enhancedResponse.json();
            setPropertyDetails(enhanced);
          }
        } catch (error) {
          console.log('Enhanced details not available:', error);
        }
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
                Tax Sale Property in Halifax, Nova Scotia
              </h1>
              <h2 className="text-2xl text-gray-700 mb-4">
                {property.property_address || 'Address not available'}
              </h2>
              
              <div className="flex items-center space-x-4 text-sm mb-6">
                <span><strong>AAN:</strong> {property.assessment_number}</span>
                {property.pid_number && <span>•</span>}
                {property.pid_number && <span><strong>PID:</strong> {property.pid_number}</span>}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div>
                  <span className="block text-sm text-gray-500">Status</span>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                    property.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {property.status || 'Unknown'}
                  </span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Sale Type</span>
                  <span className="text-gray-900">Public Tender</span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Tax Sale Date</span>
                  <span className="text-gray-900">{formatDate(property.sale_date)}</span>
                </div>
                <div>
                  <span className="block text-sm text-gray-500">Municipality</span>
                  <span className="text-gray-900">Halifax Regional Municipality</span>
                </div>
              </div>
            </div>

            {/* Property Details Section */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Property Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Address</span>
                    <span className="text-gray-900">{property.property_address || 'Not available'}</span>
                  </div>
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Assessment Number</span>
                    <span className="text-gray-900">{property.assessment_number}</span>
                  </div>
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">PID</span>
                    <span className="text-gray-900">{property.pid_number || 'Not available'}</span>
                  </div>
                  {propertyDetails?.current_assessment && (
                    <div>
                      <span className="block text-sm text-gray-500 mb-1">Current Assessment</span>
                      <span className="text-gray-900">{formatCurrency(propertyDetails.current_assessment)}</span>
                    </div>
                  )}
                </div>
                
                <div className="space-y-4">
                  {propertyDetails?.property_type && (
                    <div>
                      <span className="block text-sm text-gray-500 mb-1">Property Type</span>
                      <span className="text-gray-900">{propertyDetails.property_type}</span>
                    </div>
                  )}
                  {propertyDetails?.year_built && (
                    <div>
                      <span className="block text-sm text-gray-500 mb-1">Year Built</span>
                      <span className="text-gray-900">{propertyDetails.year_built}</span>
                    </div>
                  )}
                  {propertyDetails?.land_size && (
                    <div>
                      <span className="block text-sm text-gray-500 mb-1">Land Size</span>
                      <span className="text-gray-900">{propertyDetails.land_size}</span>
                    </div>
                  )}
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">Redeemable</span>
                    <span className="text-gray-900">{property.redeemable || 'Yes'}</span>
                  </div>
                  <div>
                    <span className="block text-sm text-gray-500 mb-1">HST Status</span>
                    <span className="text-gray-900">{property.hst_applicable || 'No HST'}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Enhanced Assessment Information */}
            {propertyDetails && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">📊 Detailed Assessment Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
                  {propertyDetails.bedrooms !== undefined && (
                    <div>
                      <span className="block text-sm text-gray-500 mb-1">Bedrooms</span>
                      <span className="text-gray-900">{propertyDetails.bedrooms}</span>
                    </div>
                  )}
                  {propertyDetails.bathrooms !== undefined && (
                    <div>
                      <span className="block text-sm text-gray-500 mb-1">Bathrooms</span>
                      <span className="text-gray-900">{propertyDetails.bathrooms}</span>
                    </div>
                  )}
                  {propertyDetails.taxable_assessment && (
                    <div>
                      <span className="block text-sm text-gray-500 mb-1">Taxable Assessment</span>
                      <span className="text-gray-900">{formatCurrency(propertyDetails.taxable_assessment)}</span>
                      <span className="block text-xs text-gray-400">Used for tax calculation</span>
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
                {property.assessment_number}; {property.owner_name || 'Owner Not Listed'}; {property.property_address || 'Address Not Available'}; {property.pid_number}; {formatCurrency(property.opening_bid)}; {property.hst_applicable || 'No HST'}
              </p>
            </div>

            {/* Location & Boundaries */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Location & Property Boundaries</h3>
              
              {/* Satellite View */}
              <div className="mb-6">
                <h4 className="text-lg font-medium text-gray-900 mb-3">Satellite Property View</h4>
                <div className="border rounded-lg overflow-hidden">
                  {property.boundary_screenshot ? (
                    <img
                      src={`${process.env.REACT_APP_BACKEND_URL || 'https://taxsale-ns.preview.emergentagent.com'}/api/boundary-image/${property.boundary_screenshot}`}
                      alt={`Property boundary map of ${property.property_address}`}
                      className="w-full h-96 object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'block';
                      }}
                    />
                  ) : property.latitude && property.longitude ? (
                    <img
                      src={`https://maps.googleapis.com/maps/api/staticmap?center=${property.latitude},${property.longitude}&zoom=17&size=800x400&maptype=satellite&key=${process.env.REACT_APP_GOOGLE_MAPS_API_KEY || 'AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY'}`}
                      alt={`Satellite view of ${property.property_address}`}
                      className="w-full h-96 object-cover"
                    />
                  ) : null}
                  <div style={{display: 'none'}} className="w-full h-96 bg-gray-100 flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <p>Satellite image not available</p>
                      <p className="text-sm mt-2">URL: /api/boundary-image/{property.boundary_screenshot || 'not-available'}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Address Information */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">📍 Official Civic Address:</h4>
                <p className="text-blue-800">{property.property_address || 'Address not available'}</p>
                <p className="text-sm text-blue-600 mt-1">This is the official municipal address from PVSC records</p>
              </div>
            </div>

            {/* Property Description */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Description</h3>
              <div className="prose max-w-none">
                <p className="mb-4">SEALED TENDERS are to be submitted:</p>
                <ul className="list-disc pl-6 space-y-2 mb-4">
                  <li>In digital format via submission to Halifax Regional Municipality's website</li>
                  <li>On the Halifax Regional Municipality's bid form in a plain envelope marked "Halifax Regional Municipality Tax Sale Property Tender"</li>
                </ul>
                <p>These bids will only be accepted until the specified deadline. HRM will not accept bids submitted by any other method, including by facsimile or email.</p>
                <p className="mt-4">The Halifax Regional Municipality reserves the right to reject any or all tenders or to accept any tender or part thereof considered to be in its best interest.</p>
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Minimum Bid Box */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-green-900 mb-2">Minimum Bid</h3>
              <div className="flex items-baseline">
                <span className="text-4xl font-bold text-green-800">{formatCurrency(property.opening_bid)}</span>
                <span className="text-lg text-green-600 ml-2">CAD</span>
              </div>
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
                  href="https://www.halifax.ca/home-property/property-taxes/tax-sales"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full bg-gray-600 text-white text-center py-3 px-4 rounded-md hover:bg-gray-700 transition-colors font-medium"
                >
                  Halifax Tax Sale Info
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
                  <span className="text-gray-900">Halifax Regional Municipality</span>
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