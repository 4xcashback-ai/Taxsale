import React, { useState, useEffect } from 'react';
import { Search, Filter, MapPin, Calendar, DollarSign, Eye } from 'lucide-react';

const ImprovedPropertySearch = ({ properties, onPropertyClick, backendUrl }) => {
  const [filteredProperties, setFilteredProperties] = useState(properties);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    municipality: '',
    status: '',
    priceRange: '',
    propertyType: ''
  });
  const [viewMode, setViewMode] = useState('grid'); // grid, list, map

  // Price ranges similar to TaxSalesHub
  const priceRanges = [
    { label: 'All', value: '' },
    { label: 'Below $10,000', value: '0-10000' },
    { label: '$10,000 - $25,000', value: '10000-25000' },
    { label: '$25,000 - $50,000', value: '25000-50000' },
    { label: '$50,000 - $100,000', value: '50000-100000' },
    { label: 'Above $100,000', value: '100000-999999999' }
  ];

  // Get unique municipalities for filter
  const municipalities = [...new Set(properties.map(p => p.municipality || 'Unknown'))];

  // Filter properties
  useEffect(() => {
    let filtered = properties;

    // Search query filter
    if (searchQuery) {
      filtered = filtered.filter(property => 
        property.property_address?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        property.owner_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        property.assessment_number?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Municipality filter
    if (filters.municipality) {
      filtered = filtered.filter(p => p.municipality === filters.municipality);
    }

    // Status filter
    if (filters.status) {
      filtered = filtered.filter(p => p.status === filters.status);
    }

    // Price range filter
    if (filters.priceRange) {
      const [min, max] = filters.priceRange.split('-').map(Number);
      filtered = filtered.filter(p => {
        const bid = parseFloat(p.opening_bid) || 0;
        return bid >= min && bid <= max;
      });
    }

    setFilteredProperties(filtered);
  }, [properties, searchQuery, filters]);

  const formatPrice = (price) => {
    const num = parseFloat(price) || 0;
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(num);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-CA', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getPropertyImage = (property) => {
    // Try boundary image first, then fallback to placeholder
    if (property.boundary_screenshot) {
      return `${backendUrl}/api/boundary-image/${property.boundary_screenshot}`;
    }
    
    // Generate a satellite image URL as fallback
    if (property.latitude && property.longitude) {
      return `https://maps.googleapis.com/maps/api/staticmap?center=${property.latitude},${property.longitude}&zoom=17&size=405x290&maptype=satellite&key=${process.env.REACT_APP_GOOGLE_MAPS_API_KEY}`;
    }
    
    // Final fallback to a placeholder
    return `https://via.placeholder.com/405x290/e2e8f0/64748b?text=No+Image`;
  };

  const PropertyCard = ({ property }) => (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200">
      {/* Property Image */}
      <div className="relative h-48 bg-gray-200">
        <img
          src={getPropertyImage(property)}
          alt={property.property_address || 'Property'}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.src = `https://via.placeholder.com/405x290/e2e8f0/64748b?text=No+Image`;
          }}
        />
        <div className={`absolute top-2 right-2 px-2 py-1 rounded text-xs font-medium ${
          property.status === 'active' 
            ? 'bg-green-100 text-green-800' 
            : 'bg-gray-100 text-gray-800'
        }`}>
          {property.status || 'Unknown'}
        </div>
      </div>

      {/* Property Info */}
      <div className="p-4">
        <h3 className="font-semibold text-lg text-gray-900 mb-2 line-clamp-1">
          {property.property_address || property.assessment_number || 'Unknown Address'}
        </h3>
        
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center">
            <MapPin className="w-4 h-4 mr-1" />
            <span>{property.municipality || 'Unknown'}, Nova Scotia</span>
          </div>
          
          <div className="flex items-center">
            <Calendar className="w-4 h-4 mr-1" />
            <span>Posted {formatDate(property.created_at)}</span>
          </div>
        </div>

        {/* Price and Action */}
        <div className="mt-4 flex items-center justify-between">
          <div className="text-xl font-bold text-green-600">
            {formatPrice(property.opening_bid)}
          </div>
          
          <button
            onClick={() => onPropertyClick(property)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center"
          >
            <Eye className="w-4 h-4 mr-1" />
            See Details
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      {/* Left Sidebar - Filters */}
      <div className="lg:w-80 bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Search & Filter</h2>
        
        {/* Search Bar */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search Properties
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Address, owner, or assessment #"
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Municipality Filter */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Municipality
          </label>
          <select
            value={filters.municipality}
            onChange={(e) => setFilters({...filters, municipality: e.target.value})}
            className="w-full py-2 px-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Municipalities</option>
            {municipalities.map(municipality => (
              <option key={municipality} value={municipality}>
                {municipality}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <select
            value={filters.status}
            onChange={(e) => setFilters({...filters, status: e.target.value})}
            className="w-full py-2 px-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>

        {/* Price Range Filter */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Opening Bid Range
          </label>
          <select
            value={filters.priceRange}
            onChange={(e) => setFilters({...filters, priceRange: e.target.value})}
            className="w-full py-2 px-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {priceRanges.map(range => (
              <option key={range.value} value={range.value}>
                {range.label}
              </option>
            ))}
          </select>
        </div>

        {/* Clear Filters */}
        <button
          onClick={() => {
            setSearchQuery('');
            setFilters({
              municipality: '',
              status: '',
              priceRange: '',
              propertyType: ''
            });
          }}
          className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 px-4 rounded-md transition-colors duration-200"
        >
          Clear All Filters
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1">
        {/* View Controls and Results Count */}
        <div className="flex items-center justify-between mb-6">
          <div className="text-lg font-medium text-gray-900">
            {filteredProperties.length} results found
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-md ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}
            >
              Grid View
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}
            >
              List View
            </button>
          </div>
        </div>

        {/* Property Grid */}
        <div className={`grid gap-6 ${
          viewMode === 'grid' 
            ? 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3' 
            : 'grid-cols-1'
        }`}>
          {filteredProperties.map((property, index) => (
            <PropertyCard key={property.id || index} property={property} />
          ))}
        </div>

        {/* No Results */}
        {filteredProperties.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg">No properties found matching your criteria</div>
            <button
              onClick={() => {
                setSearchQuery('');
                setFilters({
                  municipality: '',
                  status: '',
                  priceRange: '',
                  propertyType: ''
                });
              }}
              className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
            >
              Clear filters to see all properties
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImprovedPropertySearch;