# VPS Authentication Troubleshooting Guide

## Issue: 401 Unauthorized on Admin Deployment Endpoints

You're getting 401 errors when clicking the "Check Updates" button in the admin panel:
```
INFO: 24.142.25.79:0 - "POST /api/deployment/check-updates HTTP/1.1" 401 Unauthorized
```

## Root Cause Analysis

The backend authentication system is working correctly (confirmed by dev testing). The issue is environment-specific and likely caused by:

1. **JWT Secret Key Mismatch**: VPS has different `JWT_SECRET_KEY` than when your browser token was generated
2. **Expired Token**: Your browser token may have expired
3. **Environment Variables**: VPS `.env` file missing or incorrect

## Solution Steps

### Step 1: Check VPS Environment Variables
SSH into your VPS and verify:
```bash
cd /var/www/tax-sale-compass
cat backend/.env | grep JWT_SECRET_KEY
```

Make sure it matches this development value:
```
JWT_SECRET_KEY="your-super-secret-jwt-key-that-should-be-very-long-and-random-for-production"
```

### Step 2: Force Fresh Login
1. **Clear browser storage**: In browser developer tools (F12), go to Application > Storage > Clear all
2. **Refresh the page**: Go to https://taxsalecompass.ca
3. **Login again**: Use `admin@taxsalecompass.ca` / `TaxSale2025!SecureAdmin`
4. **Test the buttons**: Try "Check Updates" again

### Step 3: Restart Backend Services (if needed)
If Step 2 doesn't work:
```bash
# On your VPS
pm2 restart taxsale-backend
# Wait 10 seconds, then test again
```

### Step 4: Check VPS Backend Logs
Monitor the enhanced logging we added:
```bash
pm2 logs taxsale-backend --lines 20
```

Look for:
- ✅ `JWT decoded successfully - username: admin`
- ❌ `JWT validation failed:` or `JWT token has expired`

## Enhanced Logging Added

The backend now logs detailed JWT validation info:
- Token validation attempts
- Specific error reasons (expired, invalid, missing)
- IP addresses for admin requests

## Expected Behavior After Fix

You should see in VPS logs:
```
INFO: Deployment status requested by user: admin
INFO: JWT decoded successfully - username: admin, exp: [timestamp]
INFO: 24.142.25.79:0 - "POST /api/deployment/check-updates HTTP/1.1" 200 OK
```

## If Problem Persists

1. **Check browser console** (F12 > Console) for JavaScript errors
2. **Verify network tab** shows requests are being sent with Authorization header
3. **Compare JWT tokens**: Login in dev vs production - should have similar length (~124 chars)

## Security Note

The 401 responses are actually **good security** - they show your admin endpoints are properly protected. Once you get a fresh token with the correct secret key, everything will work perfectly.