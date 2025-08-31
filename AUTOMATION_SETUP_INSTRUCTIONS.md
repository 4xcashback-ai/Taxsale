# Automation Setup Instructions for VPS

After you've deployed Tax Sale Compass to your VPS following the step-by-step guide, follow these instructions to enable the automated deployment features in the admin panel.

## Quick Setup (Recommended)

**1. SSH into your VPS:**
```bash
ssh root@taxsalecompass.ca
```

**2. Navigate to your application directory:**
```bash
cd /var/www/tax-sale-compass
```

**3. Run the automation setup script:**
```bash
sudo ./scripts/setup-automation.sh
```

**4. Test the setup:**
```bash
# Test deployment status
sudo /opt/tax-sale-compass/scripts/deployment-status.sh

# Test health check
sudo /opt/tax-sale-compass/scripts/system-health.sh check

# Test deployment script
sudo /opt/tax-sale-compass/scripts/deployment.sh verify
```

**5. Restart your backend to ensure API endpoints work:**
```bash
pm2 restart tax-sale-backend
```

**6. Test the admin panel:**
- Go to https://taxsalecompass.ca
- Click on the "Admin" tab
- Scroll to "Deployment Management"
- Click "Health Check" button - should show system status
- Click "Check Updates" button - should check for GitHub updates

## What the Automation Setup Does

The `setup-automation.sh` script:

1. **Creates system directories:**
   - `/opt/tax-sale-compass/scripts/` - Contains deployment scripts
   - `/var/backups/tax-sale-compass/` - Backup storage
   - `/var/backups/mongodb/` - Database backups

2. **Installs automation scripts:**
   - `deployment.sh` - Main deployment script
   - `system-health.sh` - Health monitoring script
   - `deployment-status.sh` - Status checking script

3. **Sets up permissions:**
   - Allows `www-data` user to run deployment scripts with sudo
   - Creates secure sudoers configuration

4. **Configures system services:**
   - Log rotation for deployment logs
   - Cron jobs for automatic health checks
   - Monitoring and alerting

5. **Creates command shortcuts:**
   - `tax-sale-deploy` - Quick deployment command
   - `tax-sale-health` - Quick health check command

## Manual Setup (Alternative)

If the automatic setup doesn't work, you can set up manually:

**1. Create directories:**
```bash
sudo mkdir -p /opt/tax-sale-compass/scripts
sudo mkdir -p /var/backups/tax-sale-compass
sudo mkdir -p /var/backups/mongodb
```

**2. Copy scripts:**
```bash
sudo cp /var/www/tax-sale-compass/scripts/*.sh /opt/tax-sale-compass/scripts/
sudo chmod +x /opt/tax-sale-compass/scripts/*.sh
```

**3. Create sudoers file:**
```bash
sudo nano /etc/sudoers.d/tax-sale-compass
```

Add this content:
```
# Allow www-data to run deployment scripts
www-data ALL=(root) NOPASSWD: /opt/tax-sale-compass/scripts/deployment.sh
www-data ALL=(root) NOPASSWD: /opt/tax-sale-compass/scripts/system-health.sh
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl restart nginx
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl reload nginx
www-data ALL=(root) NOPASSWD: /usr/bin/pm2 restart *
www-data ALL=(root) NOPASSWD: /usr/bin/pm2 start *
www-data ALL=(root) NOPASSWD: /usr/bin/pm2 stop *
```

**4. Set permissions:**
```bash
sudo chmod 440 /etc/sudoers.d/tax-sale-compass
```

**5. Create status script:**
```bash
sudo nano /opt/tax-sale-compass/scripts/deployment-status.sh
```

Add the status script content from the setup script, then:
```bash
sudo chmod +x /opt/tax-sale-compass/scripts/deployment-status.sh
```

## Using the Admin Panel

Once setup is complete, you can use the admin panel to:

### Check for Updates
- Click "Check Updates" to see if new code is available on GitHub
- Shows current vs latest commit hashes
- Indicates if updates are available

### Deploy Latest Version
- Click "Deploy Latest" to automatically:
  - Create backup of current version
  - Pull latest code from GitHub
  - Update dependencies
  - Rebuild frontend
  - Restart services
  - Verify deployment
  - Rollback if anything fails

### Monitor System Health
- Click "Health Check" to verify:
  - System resources (disk, memory, load)
  - Service status (MongoDB, Nginx, PM2)
  - Application connectivity
  - SSL certificate status
  - Recent error logs

### Verify Deployment
- Click "Verify Status" to check:
  - Backend API responding
  - Frontend loading
  - Database connectivity
  - Service status

## GitHub Repository Setup

To use automatic deployments, make sure:

1. **Your repository is accessible:**
   - Public repository, or
   - Private repository with SSH key access configured

2. **Repository URL is correct:**
   - Use HTTPS URL: `https://github.com/username/tax-sale-compass.git`
   - Or SSH URL: `git@github.com:username/tax-sale-compass.git`

3. **Git is configured on server:**
   ```bash
   cd /var/www/tax-sale-compass
   git remote -v  # Check current repository
   
   # If needed, update repository URL:
   git remote set-url origin https://github.com/username/tax-sale-compass.git
   ```

## Backup and Recovery

The automation system automatically:
- Creates backups before each deployment
- Keeps last 5 backups
- Backs up MongoDB database
- Can rollback to previous version if deployment fails

**Manual rollback:**
```bash
sudo /opt/tax-sale-compass/scripts/deployment.sh rollback /var/backups/tax-sale-compass/backup_YYYYMMDD_HHMMSS
```

## Monitoring and Logs

**View deployment logs:**
```bash
tail -f /var/log/tax-sale-deployment.log
```

**View health check logs:**
```bash
tail -f /var/log/tax-sale-health.log
```

**View application logs:**
```bash
pm2 logs tax-sale-backend
pm2 logs tax-sale-frontend
```

## Troubleshooting

**Common issues:**

1. **"Failed to fetch deployment status"**
   - Run the setup script: `sudo ./scripts/setup-automation.sh`
   - Check if scripts exist: `ls -la /opt/tax-sale-compass/scripts/`

2. **"Permission denied" errors**
   - Check sudoers file: `sudo visudo -c -f /etc/sudoers.d/tax-sale-compass`
   - Verify file permissions: `ls -la /etc/sudoers.d/tax-sale-compass`

3. **Deployment fails**
   - Check deployment logs: `tail -50 /var/log/tax-sale-deployment.log`
   - Verify GitHub access: `cd /var/www/tax-sale-compass && git pull`
   - Check disk space: `df -h`

4. **Health check shows errors**
   - Check individual services: `pm2 status`, `sudo systemctl status nginx mongod`
   - Review error logs: `pm2 logs --err`

**Test commands:**
```bash
# Test scripts directly
sudo /opt/tax-sale-compass/scripts/deployment.sh verify
sudo /opt/tax-sale-compass/scripts/system-health.sh check

# Test API endpoints
curl http://localhost:8001/api/deployment/status
curl -X POST http://localhost:8001/api/deployment/verify
```

## Security Notes

- Deployment scripts run with root privileges for system management
- Access is restricted to www-data user (web server)
- Sudoers configuration uses NOPASSWD for specific scripts only
- All actions are logged for audit purposes
- Backups are created before any system changes

## Success!

Once everything is set up, you'll have a powerful admin panel that lets you:
- ✅ Deploy updates with one click
- ✅ Monitor system health in real-time  
- ✅ Automatically backup and rollback
- ✅ Check for updates from GitHub
- ✅ Verify deployments work correctly

Your Tax Sale Compass application will be fully automated and production-ready!