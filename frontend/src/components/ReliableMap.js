import React, { useState } from 'react';

const ReliableMap = ({ assessmentNumber, width = 600, height = 400, zoom = 17 }) => {
  const [imageError, setImageError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  
  // Static map URL - always works, no JavaScript timing issues
  const staticMapUrl = `${API}/api/static-map/${assessmentNumber}?width=${width}&height=${height}&zoom=${zoom}&v=${Date.now()}`;
  
  const handleImageLoad = () => {
    setIsLoading(false);
    setImageError(false);
  };
  
  const handleImageError = () => {
    setIsLoading(false);
    setImageError(true);
  };
  
  const handleRetry = () => {
    setIsLoading(true);
    setImageError(false);
    // Force reload by updating the image src
    const img = document.querySelector(`img[data-assessment="${assessmentNumber}"]`);
    if (img) {
      img.src = `${staticMapUrl}&retry=${Date.now()}`;
    }
  };

  return (
    <div className="relative w-full">
      {/* Loading indicator */}
      {isLoading && (
        <div 
          className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg"
          style={{ width, height }}
        >
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-gray-600 text-sm">Loading map...</p>
          </div>
        </div>
      )}
      
      {/* Error state */}
      {imageError && (
        <div 
          className="flex items-center justify-center bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg"
          style={{ width, height }}
        >
          <div className="text-center">
            <div className="text-gray-400 mb-2">
              <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
              </svg>
            </div>
            <p className="text-gray-500 text-sm mb-2">Map not available</p>
            <button 
              onClick={handleRetry}
              className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      )}
      
      {/* Map image - Python-generated, always reliable */}
      <img
        data-assessment={assessmentNumber}
        src={staticMapUrl}
        alt={`Property map for ${assessmentNumber}`}
        className={`rounded-lg border border-gray-300 ${isLoading || imageError ? 'hidden' : 'block'}`}
        style={{ width, height }}
        onLoad={handleImageLoad}
        onError={handleImageError}
      />
      
      {/* Map info overlay */}
      {!isLoading && !imageError && (
        <div className="absolute top-2 left-2 bg-white bg-opacity-90 backdrop-blur-sm rounded px-2 py-1 text-xs text-gray-700">
          Property {assessmentNumber}
        </div>
      )}
    </div>
  );
};

export default ReliableMap;