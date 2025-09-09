# VPS Geocoding Deployment Instructions

## Overview
This guide will help you deploy the enhanced geocoding functionality to your VPS and update all properties with coordinates so they display on Google Maps.

## What This Update Does
- ✅ Enables address-based geocoding for apartment/condo properties
- ✅ Updates all properties without coordinates using Google Maps API  
- ✅ Fixes properties that were not displaying on interactive maps
- ✅ Maintains existing PID-based boundary functionality

## Step-by-Step Deployment

### Step 1: Deploy Code Changes to VPS

**Option A: Using Admin Panel (Recommended)**
1. Go to your admin panel: `https://taxsalecompass.ca/admin.php`
2. Login with admin credentials
3. Scroll to "System Operations" section
4. Click **"Full Deploy & Restart"** button
5. Watch the real-time console output
6. Wait for "Deployment successful" message

**Option B: Command Line**
```bash
# SSH into your VPS
ssh your-user@your-vps-ip

# Navigate to application directory
cd /var/www/tax-sale-compass

# Run full deployment
sudo bash scripts/vps_deploy.sh
```

### Step 2: Update Properties with Geocoding

After successful deployment, run the geocoding update:

```bash
# Make the geocoding script executable
sudo chmod +x /var/www/tax-sale-compass/scripts/vps_geocode_update.sh

# Run the geocoding update
sudo bash /var/www/tax-sale-compass/scripts/vps_geocode_update.sh
```

### Step 3: Verify the Update

**Check the logs:**
```bash
# View the geocoding update log
tail -f /var/log/taxsale_geocode_update.log
```

**Expected output:**
```
=== FINAL STATISTICS ===
Total properties: XX
Properties with coordinates: XX
Properties still needing geocoding: 0
🎉 SUCCESS: All properties now have coordinates for map display!
```

**Test on your website:**
1. Visit a property page: `https://taxsalecompass.ca/property.php?assessment=07737947`
2. Verify the interactive map displays with coordinates
3. Check that apartment properties show as markers (not boundary polygons)

## What Files Were Updated

### Backend Changes:
- `backend/server_mysql.py` - Enhanced boundary generation endpoint with geocoding fallback
- `backend/scrapers_mysql.py` - Added Google Maps geocoding function
- `backend/requirements.txt` - Added python-dotenv dependency

### New Scripts:
- `scripts/vps_geocode_update.sh` - Batch geocoding update script

### Environment:
- Uses existing `GOOGLE_MAPS_API_KEY` from your backend `.env` file

## Expected Results

**Before Update:**
- Properties with PID boundaries: ✅ Display correctly
- Apartment/condo properties: ❌ No coordinates, don't display on maps

**After Update:**
- Properties with PID boundaries: ✅ Display with boundary polygons
- Apartment/condo properties: ✅ Display with coordinate markers
- All properties: ✅ Have map locations

## Troubleshooting

### If Deployment Fails:
```bash
# Check service status
sudo systemctl status nginx php8.1-fpm mysql

# Emergency restore if needed
sudo bash /var/www/tax-sale-compass/scripts/emergency_restore.sh
```

### If Geocoding Update Fails:
```bash
# Check backend is running
curl http://localhost:8001/api/health

# Restart backend if needed
sudo systemctl restart tax-sale-backend

# Check deployment logs
tail -f /var/log/taxsale_deploy.log
```

### If Google Maps API Issues:
```bash
# Verify API key is loaded
cd /var/www/tax-sale-compass/backend
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key loaded:', bool(os.environ.get('GOOGLE_MAPS_API_KEY')))"
```

## Verification Steps

1. **Check Property Statistics:**
   - Visit admin panel
   - All properties should have coordinates
   - No "missing coordinates" errors

2. **Test Property Maps:**
   - Visit individual property pages
   - Interactive maps should display for all properties
   - Apartment properties show as markers
   - Regular properties show boundary polygons

3. **Test Search Results:**
   - Search for properties
   - All properties should have thumbnail images
   - No "No coordinates" errors in thumbnails

## Contact Support

If you encounter issues:
1. Check the log files: `/var/log/taxsale_geocode_update.log`
2. Verify all services are running: `sudo systemctl status nginx php8.1-fpm mysql`
3. Test backend API: `curl http://localhost:8001/api/health`

The enhanced geocoding system ensures all properties display on Google Maps, solving the apartment property display issue!