/**
 * Robust Google Maps API Loader for VPS Environment
 * Handles loading Google Maps API with proper error handling and retries
 */

const GOOGLE_MAPS_API_KEY = 'AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY';
const GOOGLE_MAPS_URL = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=geometry`;

class GoogleMapsLoader {
  constructor() {
    this.isLoaded = false;
    this.isLoading = false;
    this.callbacks = [];
    this.loadPromise = null;
    this.retryCount = 0;
    this.maxRetries = 3;
  }

  /**
   * Load Google Maps API with retry mechanism
   */
  load() {
    // Return existing promise if already loading
    if (this.loadPromise) {
      return this.loadPromise;
    }

    // Return resolved promise if already loaded
    if (this.isLoaded && window.google?.maps) {
      return Promise.resolve();
    }

    console.log('GoogleMapsLoader: Starting to load Google Maps API...');
    
    this.loadPromise = new Promise((resolve, reject) => {
      this.callbacks.push({ resolve, reject });

      if (!this.isLoading) {
        this._loadScript();
      }
    });

    return this.loadPromise;
  }

  /**
   * Internal method to load the script
   */
  _loadScript() {
    this.isLoading = true;

    // Check if script already exists
    const existingScript = document.querySelector('script[src*="maps.googleapis.com"]');
    if (existingScript) {
      console.log('GoogleMapsLoader: Script already exists, removing...');
      existingScript.remove();
    }

    const script = document.createElement('script');
    script.src = GOOGLE_MAPS_URL;
    script.async = true;
    script.defer = true;

    const timeoutId = setTimeout(() => {
      console.error('GoogleMapsLoader: Loading timeout');
      this._handleError(new Error('Google Maps loading timeout'));
    }, 15000); // 15 second timeout

    script.onload = () => {
      clearTimeout(timeoutId);
      console.log('GoogleMapsLoader: Script loaded successfully');
      
      // Wait a bit for Google Maps to initialize
      setTimeout(() => {
        if (window.google?.maps) {
          console.log('GoogleMapsLoader: Google Maps API is ready');
          this._handleSuccess();
        } else {
          console.error('GoogleMapsLoader: Google Maps API not available after script load');
          this._handleError(new Error('Google Maps API not available'));
        }
      }, 500);
    };

    script.onerror = (error) => {
      clearTimeout(timeoutId);
      console.error('GoogleMapsLoader: Script loading error', error);
      this._handleError(new Error('Failed to load Google Maps script'));
    };

    console.log('GoogleMapsLoader: Appending script to head');
    document.head.appendChild(script);
  }

  /**
   * Handle successful loading
   */
  _handleSuccess() {
    this.isLoaded = true;
    this.isLoading = false;
    this.retryCount = 0;

    console.log(`GoogleMapsLoader: Successfully loaded, notifying ${this.callbacks.length} callbacks`);
    
    this.callbacks.forEach(callback => {
      try {
        callback.resolve();
      } catch (error) {
        console.error('GoogleMapsLoader: Error in success callback', error);
      }
    });

    this.callbacks = [];
    this.loadPromise = null;
  }

  /**
   * Handle loading errors with retry logic
   */
  _handleError(error) {
    this.isLoading = false;
    
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      console.log(`GoogleMapsLoader: Retry attempt ${this.retryCount}/${this.maxRetries}`);
      
      setTimeout(() => {
        this._loadScript();
      }, 2000 * this.retryCount); // Exponential backoff
      
      return;
    }

    console.error(`GoogleMapsLoader: Failed after ${this.maxRetries} retries`);
    
    this.callbacks.forEach(callback => {
      try {
        callback.reject(error);
      } catch (callbackError) {
        console.error('GoogleMapsLoader: Error in error callback', callbackError);
      }
    });

    this.callbacks = [];
    this.loadPromise = null;
  }

  /**
   * Check if Google Maps is already loaded
   */
  isGoogleMapsLoaded() {
    return this.isLoaded && window.google?.maps;
  }
}

// Create singleton instance
const googleMapsLoader = new GoogleMapsLoader();

export default googleMapsLoader;