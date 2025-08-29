# Google Maps Integration Setup

This application now includes enhanced Google Maps integration with property boundary visualization for Nova Scotia tax sale properties.

## Features

- **Interactive Google Maps**: Full Google Maps integration with zoom, street view, and map type controls
- **Property Boundaries**: Displays actual property boundaries from Nova Scotia government data
- **Property Markers**: Custom red markers to highlight the exact property location
- **Info Windows**: Click on markers to see property details including PID, assessment number, opening bid, and area
- **Fallback Support**: Automatically falls back to iframe-based maps if Google Maps API is unavailable

## Setup Instructions

### 1. Get a Google Maps API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Maps JavaScript API
   - Geocoding API (optional, for address validation)
4. Create credentials (API Key)
5. Restrict the API key to your domain for security

### 2. Configure the API Key

1. Copy the example environment file:
   ```bash
   cp /app/frontend/.env.example /app/frontend/.env
   ```

2. Edit the `.env` file and add your Google Maps API key:
   ```
   REACT_APP_GOOGLE_MAPS_API_KEY=your_actual_api_key_here
   REACT_APP_BACKEND_URL=http://localhost:8000
   ```

### 3. Restart the Application

After adding the API key, restart the frontend service:
```bash
# If using Docker/supervisord
supervisorctl restart frontend

# If running locally
npm start
```

## How It Works

### Property Boundary Data

The application fetches property boundary data from the Nova Scotia government's parcel database using the property's PID number. When available, it:

1. Queries the backend API endpoint: `/api/query-ns-government-parcel/{pid_number}`
2. Converts the government polygon data to Google Maps format
3. Displays the property boundaries as a red polygon overlay
4. Automatically adjusts the map view to show the entire property

### Fallback Behavior

If the Google Maps API is not available or fails to load:
- The map automatically falls back to an iframe-based Google Maps embed
- Basic location functionality is preserved
- No JavaScript errors occur

### Data Sources

- **Property Location**: Latitude/longitude coordinates from property data
- **Property Boundaries**: Nova Scotia Property Records Database (NSPRD)
- **Map Tiles**: Google Maps satellite and street view imagery

## Troubleshooting

### Map Not Loading
1. Check that your Google Maps API key is correctly set in the `.env` file
2. Verify the API key has the Maps JavaScript API enabled
3. Check browser console for any API key errors
4. Ensure your domain is whitelisted for the API key

### Property Boundaries Not Showing
1. Verify the property has `government_boundary_data` in the backend
2. Check that the PID number is valid and exists in the NSPRD
3. Look for network errors in the browser console when fetching boundary data

### Performance Considerations
- The Google Maps API is loaded asynchronously to avoid blocking page load
- Boundary data is fetched only when needed (lazy loading)
- Maps are only initialized when the component is visible

## API Usage Limits

Google Maps API has usage limits and pricing. Monitor your usage in the Google Cloud Console to avoid unexpected charges. For development, the free tier should be sufficient.

## Security Notes

- Never commit your actual API key to version control
- Use domain restrictions on your API key in production
- Consider using server-side proxy for API calls in production environments