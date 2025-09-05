/**
 * Ultra-Robust Google Maps API Loader for VPS Environment
 * Handles loading Google Maps API with aggressive retry and error handling
 */

const GOOGLE_MAPS_API_KEY = 'AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY';

class GoogleMapsLoader {
  constructor() {
    this.isLoaded = false;
    this.isLoading = false;
    this.callbacks = [];
    this.loadPromise = null;
    this.retryCount = 0;
    this.maxRetries = 5;
    this.scriptId = 'google-maps-api-script';
  }

  /**
   * Load Google Maps API with ultra-aggressive retry mechanism
   */
  load() {
    // Return existing promise if already loading
    if (this.loadPromise) {
      return this.loadPromise;
    }

    // Return resolved promise if already loaded
    if (this.isLoaded && window.google?.maps) {
      console.log('GoogleMapsLoader: Already loaded, returning resolved promise');
      return Promise.resolve();
    }

    console.log('GoogleMapsLoader: Starting ultra-robust loading process...');
    
    this.loadPromise = new Promise((resolve, reject) => {
      this.callbacks.push({ resolve, reject });

      if (!this.isLoading) {
        this._loadScript();
      }
    });

    return this.loadPromise;
  }

  /**
   * Internal method to load the script with non-blocking approach
   */
  _loadScript() {
    this.isLoading = true;
    this.retryCount++;

    console.log(`GoogleMapsLoader: Loading attempt ${this.retryCount}/${this.maxRetries}`);

    // Use requestIdleCallback for non-blocking execution
    const performLoad = () => {
      // Remove any existing Google Maps scripts
      this._cleanupExistingScripts();

      // Generate unique callback name for this attempt
      const callbackName = `initGoogleMaps_${Date.now()}_${this.retryCount}`;
      
      // Create global callback
      window[callbackName] = () => {
        console.log('GoogleMapsLoader: Callback executed successfully');
        delete window[callbackName]; // Cleanup
        // Use setTimeout to avoid blocking the callback
        setTimeout(() => this._handleSuccess(), 0);
      };

      const script = document.createElement('script');
      script.id = this.scriptId;
      script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=geometry&callback=${callbackName}&v=3.55`;
      script.async = true;
      script.defer = true;

      // Set up timeout with performance-friendly timing
      const timeoutId = setTimeout(() => {
        console.error(`GoogleMapsLoader: Loading timeout on attempt ${this.retryCount}`);
        delete window[callbackName]; // Cleanup callback
        script.remove(); // Remove failed script
        // Use setTimeout to avoid blocking
        setTimeout(() => this._handleError(new Error(`Google Maps loading timeout (attempt ${this.retryCount})`)), 0);
      }, 15000); // Reduced to 15 seconds for faster feedback

      script.onload = () => {
        console.log('GoogleMapsLoader: Script onload event fired');
        // Don't handle success here, wait for callback
      };

      script.onerror = (error) => {
        clearTimeout(timeoutId);
        delete window[callbackName]; // Cleanup callback
        console.error(`GoogleMapsLoader: Script onerror on attempt ${this.retryCount}`, error);
        // Use setTimeout to avoid blocking
        setTimeout(() => this._handleError(new Error(`Failed to load Google Maps script (attempt ${this.retryCount})`)), 0);
      };

      console.log(`GoogleMapsLoader: Appending script with callback ${callbackName}`);
      document.head.appendChild(script);

      // Cleanup timeout reference
      setTimeout(() => {
        clearTimeout(timeoutId);
      }, 16000);
    };

    // Use requestIdleCallback for non-blocking execution
    if (window.requestIdleCallback) {
      window.requestIdleCallback(performLoad, { timeout: 1000 });
    } else {
      // Fallback for browsers without requestIdleCallback
      setTimeout(performLoad, 0);
    }
  }

  /**
   * Remove all existing Google Maps scripts
   */
  _cleanupExistingScripts() {
    // Remove all Google Maps related scripts
    const scripts = document.querySelectorAll('script[src*="maps.googleapis.com"], script[id*="google"], script[src*="google"]');
    scripts.forEach(script => {
      if (script.src.includes('maps.googleapis.com')) {
        console.log('GoogleMapsLoader: Removing existing Google Maps script');
        script.remove();
      }
    });

    // Clean up window.google if it exists but is broken
    if (window.google && !window.google.maps) {
      console.log('GoogleMapsLoader: Cleaning up broken window.google');
      delete window.google;
    }
  }

  /**
   * Handle successful loading
   */
  _handleSuccess() {
    // Double-check that Google Maps is actually available
    if (!window.google?.maps) {
      console.error('GoogleMapsLoader: Success callback fired but Google Maps not available');
      this._handleError(new Error('Google Maps callback fired but API not available'));
      return;
    }

    this.isLoaded = true;
    this.isLoading = false;
    this.retryCount = 0;

    console.log(`GoogleMapsLoader: Successfully loaded! Notifying ${this.callbacks.length} callbacks`);
    
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
   * Handle loading errors with non-blocking retry logic
   */
  _handleError(error) {
    this.isLoading = false;
    
    console.error(`GoogleMapsLoader: Error on attempt ${this.retryCount}:`, error.message);
    
    if (this.retryCount < this.maxRetries) {
      console.log(`GoogleMapsLoader: Retrying in ${2 * this.retryCount} seconds...`);
      
      // Use non-blocking timeout for retry
      setTimeout(() => {
        // Use requestIdleCallback for non-blocking retry
        if (window.requestIdleCallback) {
          window.requestIdleCallback(() => this._loadScript(), { timeout: 1000 });
        } else {
          setTimeout(() => this._loadScript(), 0);
        }
      }, 2000 * this.retryCount); // Exponential backoff
      
      return;
    }

    console.error(`GoogleMapsLoader: Failed after ${this.maxRetries} attempts. Giving up.`);
    
    // Use setTimeout to avoid blocking main thread
    setTimeout(() => {
      this.callbacks.forEach(callback => {
        try {
          callback.reject(new Error(`Google Maps failed to load after ${this.maxRetries} attempts: ${error.message}`));
        } catch (callbackError) {
          console.error('GoogleMapsLoader: Error in error callback', callbackError);
        }
      });

      this.callbacks = [];
      this.loadPromise = null;
      this.retryCount = 0; // Reset for potential future attempts
    }, 0);
  }

  /**
   * Check if Google Maps is already loaded
   */
  isGoogleMapsLoaded() {
    return this.isLoaded && window.google?.maps;
  }

  /**
   * Force reload (for manual retry)
   */
  forceReload() {
    console.log('GoogleMapsLoader: Force reload requested');
    this.isLoaded = false;
    this.isLoading = false;
    this.loadPromise = null;
    this.retryCount = 0;
    this._cleanupExistingScripts();
    return this.load();
  }
}

// Create singleton instance
const googleMapsLoader = new GoogleMapsLoader();

export default googleMapsLoader;