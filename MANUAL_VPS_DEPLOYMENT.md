# Manual VPS Deployment Guide

## Situation
The deployment button isn't working due to authentication issues, but we need to deploy the authentication fixes. Here's how to manually deploy to your VPS.

## Manual Deployment Steps

### 1. SSH into your VPS
```bash
ssh root@your-vps-ip
# or
ssh your-username@your-vps-ip
```

### 2. Navigate to Application Directory
```bash
cd /var/www/tax-sale-compass
```

### 3. Backup Current Version (Safety First)
```bash
# Create backup of current working version
cp -r . ../tax-sale-compass-backup-$(date +%Y%m%d_%H%M%S)
echo "Backup created in ../tax-sale-compass-backup-$(date +%Y%m%d_%H%M%S)"
```

### 4. Pull Latest Code from Repository
```bash
# Fetch latest changes
git fetch origin

# Check what changes will be applied
git log HEAD..origin/main --oneline

# Pull the latest code
git pull origin main
```

### 5. Install Dependencies (if needed)
```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies  
cd ../frontend
yarn install
```

### 6. Build Frontend
```bash
# Still in frontend directory
yarn build
```

### 7. Restart Services
```bash
# Go back to root directory
cd /var/www/tax-sale-compass

# Restart PM2 services
pm2 restart taxsale-backend
pm2 restart taxsale-frontend

# Check status
pm2 status
pm2 logs taxsale-backend --lines 10
```

### 8. Verify Deployment
```bash
# Check if services are running
curl -I https://taxsalecompass.ca

# Check backend health
curl -I https://taxsalecompass.ca/api/health || curl -I https://taxsalecompass.ca/api/tax-sales
```

## What This Deployment Includes

✅ **Enhanced JWT Authentication Logging**
- Better error messages for 401 issues
- IP tracking for admin requests
- Detailed token validation logging

✅ **Improved Security Monitoring**  
- Custom exception handler for unauthorized access
- Suppressed harmless "Invalid HTTP request" warnings
- Enhanced deployment endpoint logging

✅ **Admin Boundary Generation Fix**
- Municipality boundary regeneration now focuses on active properties only
- Updated API responses with clear messaging

## After Deployment Success

1. **Clear your browser storage** (F12 > Application > Storage > Clear all)
2. **Login fresh** at https://taxsalecompass.ca  
3. **Test admin buttons** - should now work with 200 OK responses

## Expected Log Output After Fix

You should see in `pm2 logs taxsale-backend`:
```
INFO: JWT decoded successfully - username: admin
INFO: Deployment update check requested by admin user from IP: [your_ip]
INFO: [your_ip]:0 - "POST /api/deployment/check-updates HTTP/1.1" 200 OK
```

## If Manual Deployment Fails

### Git Issues:
```bash
# If git pull fails due to conflicts
git stash
git pull origin main
git stash pop
```

### Permission Issues:
```bash
# Fix ownership if needed
chown -R www-data:www-data /var/www/tax-sale-compass
# or
chown -R $USER:$USER /var/www/tax-sale-compass
```

### Service Issues:
```bash
# If PM2 services won't start
pm2 delete all
pm2 start ecosystem.config.js
```

## Emergency Rollback (if needed)
```bash
# If something goes wrong, restore backup
cd /var/www
mv tax-sale-compass tax-sale-compass-broken
mv tax-sale-compass-backup-[timestamp] tax-sale-compass
pm2 restart all
```

## Once Working
After manual deployment succeeds and admin buttons work, the automatic deployment buttons will work again for future updates!