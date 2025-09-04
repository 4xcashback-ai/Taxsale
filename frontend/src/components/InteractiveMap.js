import React, { useState, useEffect, useRef } from 'react';
import googleMapsLoader from '../utils/googleMapsLoader';

const InteractiveMap = ({ properties, onPropertySelect }) => {
  const mapRef = useRef();
  const [map, setMap] = useState(null);
  const [markers, setMarkers] = useState([]);
  const [polygons, setPolygons] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initializeMap = async () => {
      if (!mapRef.current) {
        console.log('InteractiveMap: MapRef not available yet');
        return;
      }
      
      if (map) {
        console.log('InteractiveMap: Map already initialized');
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        
        console.log('InteractiveMap: Loading Google Maps API...');
        await googleMapsLoader.load();
        
        console.log('InteractiveMap: Initializing Google Map...');
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
        
        console.log('InteractiveMap: Google Map initialized successfully');
        setMap(googleMap);
        setIsLoading(false);
      } catch (error) {
        console.error('InteractiveMap: Error initializing Google Map:', error);
        setError(error.message);
        setIsLoading(false);
      }
    };

    initializeMap();
  }, [map]);

  // Function to fetch boundary data for a property
  const fetchBoundaryData = async (property) => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/query-ns-government-parcel/${property.pid_number}`);
      
      if (response.ok) {
        const data = await response.json();
        return data;
      }
    } catch (error) {
      console.error('Error fetching boundary data for', property.assessment_number, error);
    }
    return null;
  };

  // Function to calculate polygon centroid
  const calculatePolygonCentroid = (rings) => {
    if (!rings || rings.length === 0) return null;
    
    let totalLat = 0;
    let totalLng = 0;
    let totalPoints = 0;
    
    rings.forEach(ring => {
      ring.forEach(point => {
        totalLat += point[1]; // Latitude
        totalLng += point[0]; // Longitude
        totalPoints++;
      });
    });
    
    if (totalPoints === 0) return null;
    
    return {
      lat: totalLat / totalPoints,
      lng: totalLng / totalPoints
    };
  };

  // Function to draw boundary polygon
  const drawBoundaryPolygon = (map, property, boundaryData) => {
    try {
      let rings = null;
      
      // Handle both single PID and multi-PID boundary data
      if (boundaryData.multiple_pids && boundaryData.combined_geometry?.rings) {
        rings = boundaryData.combined_geometry.rings;
      } else if (boundaryData.geometry?.rings) {
        rings = boundaryData.geometry.rings;
      }
      
      if (!rings || rings.length === 0) {
        console.log('No boundary rings found for property', property.assessment_number);
        return null;
      }

      // Convert rings to Google Maps format
      const paths = rings.map(ring => 
        ring.map(point => ({
          lat: point[1], // Latitude is second element
          lng: point[0]  // Longitude is first element
        }))
      );

      // Determine colors based on property status
      let strokeColor = '#FF0000'; // Default red
      let fillColor = '#FF0000';
      
      if (property.status === 'active') {
        strokeColor = '#10B981'; // Green
        fillColor = '#10B981';
      } else if (property.status === 'inactive') {
        strokeColor = '#F59E0B'; // Yellow/Orange
        fillColor = '#F59E0B';
      } else if (property.auction_result === 'sold') {
        strokeColor = '#3B82F6'; // Blue
        fillColor = '#3B82F6';
      }

      // Create and display polygon
      const polygon = new window.google.maps.Polygon({
        paths: paths,
        strokeColor: strokeColor,
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: fillColor,
        fillOpacity: 0.15
      });

      polygon.setMap(map);

      // Add click listener to polygon
      polygon.addListener('click', () => {
        if (onPropertySelect) {
          onPropertySelect(property);
        }
      });

      // Calculate centroid and create marker
      const centroid = calculatePolygonCentroid(rings);
      if (centroid) {
        const marker = new window.google.maps.Marker({
          position: centroid,
          map: map,
          title: `${property.property_address} - $${parseFloat(property.opening_bid || 0).toLocaleString()}`,
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            scale: 6,
            fillColor: strokeColor,
            fillOpacity: 1,
            strokeColor: '#FFFFFF',
            strokeWeight: 2
          }
        });

        // Add click listener to marker
        marker.addListener('click', () => {
          if (onPropertySelect) {
            onPropertySelect(property);
          }
        });

        return { polygon, marker };
      }
    } catch (error) {
      console.error('Error drawing boundary polygon for property', property.assessment_number, error);
    }
    return null;
  };

  useEffect(() => {
    if (map && properties) {
      // Clear existing markers and polygons
      markers.forEach(marker => marker.setMap(null));
      polygons.forEach(polygon => polygon.setMap(null));
      
      const newMarkers = [];
      const newPolygons = [];

      // Process each property
      const loadPropertiesWithBoundaries = async () => {
        console.log(`Loading ${properties.length} properties on Live Map...`);
        
        for (const property of properties.filter(p => p.latitude && p.longitude)) {
          console.log(`Processing property ${property.assessment_number} (${property.property_address})`);
          
          // Fetch boundary data for this property
          const boundaryData = await fetchBoundaryData(property);
          
          if (boundaryData && (boundaryData.geometry?.rings || boundaryData.combined_geometry?.rings)) {
            console.log(`Drawing boundary polygon for ${property.assessment_number}`);
            // Draw boundary polygon
            const result = drawBoundaryPolygon(map, property, boundaryData);
            if (result) {
              newMarkers.push(result.marker);
              newPolygons.push(result.polygon);
            }
          } else {
            console.log(`No boundary data for ${property.assessment_number}, using fallback marker`);
            // Fallback: create regular marker if no boundary data
            const markerColor = property.status === 'active' ? '#10B981' : 
                              property.status === 'inactive' ? '#F59E0B' : 
                              property.auction_result === 'sold' ? '#3B82F6' : '#6B7280';

            const marker = new window.google.maps.Marker({
              position: { 
                lat: parseFloat(property.latitude), 
                lng: parseFloat(property.longitude) 
              },
              map: map,
              title: `${property.property_address} - $${parseFloat(property.opening_bid || 0).toLocaleString()}`,
              icon: {
                path: window.google.maps.SymbolPath.CIRCLE,
                scale: 8,
                fillColor: markerColor,
                fillOpacity: 0.8,
                strokeColor: '#FFFFFF',
                strokeWeight: 2
              }
            });

            // Add click listener to fallback marker
            marker.addListener('click', () => {
              if (onPropertySelect) {
                onPropertySelect(property);
              }
            });

            newMarkers.push(marker);
          }
        }

        setMarkers(newMarkers);
        setPolygons(newPolygons);
      };

      loadPropertiesWithBoundaries();
    }
  }, [map, properties, onPropertySelect]);

  return (
    <div className="relative">
      <div 
        ref={mapRef} 
        style={{ width: '100%', height: '500px' }}
        className="rounded-lg border border-gray-300"
      />
      
      {/* Property count indicator */}
      {properties && properties.length > 0 && (
        <div className="absolute top-4 left-4 bg-white bg-opacity-90 backdrop-blur-sm rounded-lg px-3 py-2 shadow-md">
          <div className="text-sm font-medium text-gray-700">
            {properties.filter(p => p.latitude && p.longitude).length} properties on map
          </div>
        </div>
      )}
      
      {/* Loading indicator */}
      {!map && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 bg-opacity-75 rounded-lg">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-gray-600">Loading map...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveMap;