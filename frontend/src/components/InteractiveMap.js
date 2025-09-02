import React, { useState, useEffect, useRef } from 'react';

const InteractiveMap = ({ properties, onPropertySelect }) => {
  const mapRef = useRef();
  const [map, setMap] = useState(null);
  const [markers, setMarkers] = useState([]);

  useEffect(() => {
    if (mapRef.current && !map) {
      // Initialize map centered on Nova Scotia
      const googleMap = new window.google.maps.Map(mapRef.current, {
        center: { lat: 45.0, lng: -63.0 },
        zoom: 7,
        mapTypeId: 'satellite',
        styles: [
          {
            featureType: 'all',
            elementType: 'labels',
            stylers: [{ visibility: 'on' }]
          }
        ]
      });
      setMap(googleMap);
    }
  }, [map]);

  useEffect(() => {
    if (map && properties) {
      // Clear existing markers
      markers.forEach(marker => marker.setMap(null));
      
      const newMarkers = properties
        .filter(property => property.latitude && property.longitude)
        .map(property => {
          // Determine marker color based on status and auction result
          let markerColor = '#10B981'; // green for active
          if (property.status === 'inactive') {
            markerColor = '#6B7280'; // gray for inactive
          }
          if (property.auction_result === 'sold') {
            markerColor = '#3B82F6'; // blue for sold
          }
          if (property.auction_result === 'pending') {
            markerColor = '#F59E0B'; // yellow for pending
          }

          const marker = new window.google.maps.Marker({
            position: { 
              lat: parseFloat(property.latitude), 
              lng: parseFloat(property.longitude) 
            },
            map: map,
            title: property.property_address,
            icon: {
              path: window.google.maps.SymbolPath.CIRCLE,
              scale: 8,
              fillColor: markerColor,
              fillOpacity: 0.8,
              strokeColor: '#FFFFFF',
              strokeWeight: 2
            }
          });

          // Add click listener
          marker.addListener('click', () => {
            onPropertySelect(property);
          });

          // Add info window
          const infoWindow = new window.google.maps.InfoWindow({
            content: `
              <div style="max-width: 250px;">
                <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold;">
                  ${property.property_address}
                </h3>
                <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">
                  ${property.municipality_name}
                </p>
                <p style="margin: 0 0 4px 0; font-size: 12px;">
                  <strong>Opening Bid:</strong> $${parseFloat(property.opening_bid || 0).toLocaleString()}
                </p>
                ${property.assessment_number ? `
                  <p style="margin: 0 0 4px 0; font-size: 12px;">
                    <strong>Assessment:</strong> ${property.assessment_number}
                  </p>
                ` : ''}
                ${property.sale_date ? `
                  <p style="margin: 0 0 8px 0; font-size: 12px;">
                    <strong>Sale Date:</strong> ${new Date(property.sale_date).toLocaleDateString()}
                  </p>
                ` : ''}
                <div style="text-align: center;">
                  <button 
                    onclick="window.selectProperty('${property.id}')" 
                    style="background: #3B82F6; color: white; border: none; padding: 4px 12px; border-radius: 4px; font-size: 12px; cursor: pointer;"
                  >
                    View Details
                  </button>
                </div>
              </div>
            `
          });

          marker.addListener('mouseover', () => {
            infoWindow.open(map, marker);
          });

          marker.addListener('mouseout', () => {
            infoWindow.close();
          });

          return marker;
        });

      setMarkers(newMarkers);

      // Fit map bounds to show all properties
      if (newMarkers.length > 0) {
        const bounds = new window.google.maps.LatLngBounds();
        newMarkers.forEach(marker => {
          bounds.extend(marker.getPosition());
        });
        map.fitBounds(bounds);
        
        // Don't zoom in too much for single properties
        if (newMarkers.length === 1) {
          map.setZoom(Math.min(map.getZoom(), 15));
        }
      }
    }
  }, [map, properties, onPropertySelect]);

  // Global function for info window buttons
  useEffect(() => {
    window.selectProperty = (propertyId) => {
      const property = properties.find(p => p.id === propertyId);
      if (property) {
        onPropertySelect(property);
      }
    };

    return () => {
      delete window.selectProperty;
    };
  }, [properties, onPropertySelect]);

  return (
    <div className="relative">
      <div 
        ref={mapRef} 
        className="w-full h-96 rounded-lg shadow-md"
        style={{ minHeight: '400px' }}
      />
      
      {/* Property count indicator */}
      <div className="absolute top-4 left-4 bg-white bg-opacity-90 backdrop-blur-sm rounded-lg px-3 py-2 shadow-md">
        <div className="text-sm font-medium text-gray-700">
          {properties?.filter(p => p.latitude && p.longitude).length || 0} properties on map
        </div>
      </div>
    </div>
  );
};

export default InteractiveMap;