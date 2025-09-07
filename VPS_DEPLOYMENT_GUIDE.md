# VPS Deployment System for Tax Sale Compass

## Overview
This deployment system provides automated, conflict-free updates and service management through the admin panel with real-time logging.

## Files Created/Modified

### 1. Core Deployment Script
- **`/scripts/vps_deploy.sh`** - Main deployment script with automatic conflict resolution
- **`/scripts/fix_nginx_vps.sh`** - Nginx configuration fixer
- **`/scripts/setup_web_admin_sudo.sh`** - Sudoers configuration for web admin

### 2. Admin Panel Integration
- **`/frontend-php/admin.php`** - Enhanced with deployment interface and real-time console
- **`/frontend-php/api/deploy_status.php`** - AJAX endpoint for deployment status and logs

### 3. Features Implemented

#### Admin Panel Deployment Interface
- **Service Status Monitor** - Real-time display of nginx, PHP-FPM, and MySQL status
- **Full Deploy Button** - Automated deployment with conflict resolution and health checks
- **Quick Update Button** - Legacy git pull and restart (for quick fixes)
- **Real-time Console** - Live deployment logging with color-coded messages
- **Clean Up Data** - Existing data cleanup functionality

#### Deployment Script Features
- **Automatic Conflict Resolution** - Stashes local changes, resets to remote, handles cleanly
- **Service Health Checks** - Verifies all services are running after deployment
- **Backup Creation** - Creates timestamped backups before deployment
- **Permission Management** - Sets correct file permissions automatically
- **Nginx Auto-fix** - Detects and fixes nginx configuration issues
- **Web-Safe Mode** - Automatically detects web deployments and skips PHP cleanup
- **Comprehensive Logging** - Detailed logs with timestamps in `/var/log/taxsale_deploy.log`

## Deployment Instructions for VPS

### 1. Initial Setup (Run once on VPS)
```bash
# Navigate to your application directory
cd /var/www/tax-sale-compass

# Pull the latest changes with deployment system
git pull origin main

# Setup sudo permissions for web admin
sudo bash scripts/setup_web_admin_sudo.sh

# Make scripts executable
sudo chmod +x scripts/*.sh

# Fix nginx configuration
sudo bash scripts/fix_nginx_vps.sh

# Test the deployment system
sudo bash scripts/vps_deploy.sh
```

### 2. Using the Admin Panel (Recommended)
1. Login to admin panel: `https://taxsalecompass.ca/admin.php`
2. Scroll to "System Operations" section
3. Click "Full Deploy & Restart" for complete deployment
4. Monitor real-time console output
5. Check service status indicators

### 3. Manual Command Line (Backup method)
```bash
cd /var/www/tax-sale-compass
sudo bash scripts/vps_deploy.sh
```

## Deployment Process Flow

### Full Deploy Process:
1. **Backup Creation** - Creates timestamped backup
2. **Git Conflict Resolution** - Stashes local changes, resets to remote
3. **Permission Setting** - Sets proper file/directory permissions
4. **Nginx Configuration Check** - Fixes configuration if needed
5. **Service Cleanup** - Kills stuck PHP processes
6. **Service Restart** - Restarts nginx, PHP-FPM, MySQL in order
7. **Health Verification** - Checks all services are active
8. **Website Test** - Verifies website responds correctly

### Quick Update Process:
1. Git pull latest changes
2. Basic service restart
3. Status verification

## Troubleshooting

### Common Issues:

1. **Permission Denied on Scripts**
   ```bash
   sudo chmod +x /var/www/tax-sale-compass/scripts/*.sh
   ```

2. **Deployment Broke the Website**
   ```bash
   # Emergency restore script
   sudo bash /var/www/tax-sale-compass/scripts/emergency_restore.sh
   ```

3. **Nginx Configuration Errors**
   ```bash
   # Check if SSL config exists and use it
   sudo ls -la /etc/nginx/sites-available/tax-sale-compass
   sudo bash /var/www/tax-sale-compass/scripts/fix_nginx_vps.sh
   ```

4. **Service Won't Start**
   ```bash
   sudo systemctl status nginx php8.1-fpm mysql
   sudo journalctl -u nginx -f
   ```

5. **Git Conflicts**
   - The deployment script handles these automatically
   - Manual resolution: `git reset --hard origin/main`

### Emergency Recovery:
If deployment breaks your site:
```bash
cd /var/www/tax-sale-compass
sudo bash scripts/emergency_restore.sh
```

### Log Files:
- **Deployment Logs**: `/var/log/taxsale_deploy.log`
- **Nginx Logs**: `/var/log/nginx/taxsale_error.log`
- **PHP-FPM Logs**: `/var/log/php8.1-fpm.log`

## Admin Panel URLs:
- **Main Admin**: `https://taxsalecompass.ca/admin.php`
- **Debug Thumbnails**: `https://taxsalecompass.ca/debug_thumbnails.php`
- **Deploy API**: `https://taxsalecompass.ca/api/deploy_status.php`

## Security Features:
- Sudoers configuration restricts web admin to specific commands only
- Backup creation before each deployment
- Service health verification
- Comprehensive error logging
- Read-only deployment status API

This system eliminates the git conflict issues and provides a professional deployment interface through the admin panel!