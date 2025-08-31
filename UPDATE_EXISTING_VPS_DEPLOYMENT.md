# Step-by-Step Instructions: Update Current VPS Deployment

This guide will help you safely update your existing Tax Sale Compass deployment at taxsalecompass.ca with the new deployment automation features.

## 🚨 **IMPORTANT: Backup First!**

Before making any changes, we'll create a complete backup of your current working deployment.

---

## **Step 1: Export Updated Code from Emergent**

**In Emergent Interface:**

1. Click the **"Save to GitHub"** button in Emergent
2. If asked, connect your GitHub account
3. Create a new repository or use existing one:
   - Repository name: `tax-sale-compass` (or your preferred name)
   - Make sure it's public or you have SSH access configured
4. Push all the code to GitHub
5. **Copy the repository URL** - you'll need this later:
   ```
   https://github.com/[your-username]/tax-sale-compass.git
   ```

---

## **Step 2: Connect to Your VPS**

```bash
ssh root@taxsalecompass.ca
# OR if you use a different user:
ssh your-username@taxsalecompass.ca
```

---

## **Step 3: Create Complete Backup**

```bash
# Create backup directory with timestamp
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
sudo mkdir -p /var/backups/tax-sale-compass-manual

# Backup current application
sudo cp -r /var/www/tax-sale-compass /var/backups/tax-sale-compass-manual/app_backup_$BACKUP_DATE

# Backup database
sudo mkdir -p /var/backups/mongodb
mongodump --db taxsalecompass --out /var/backups/mongodb/backup_$BACKUP_DATE

# Backup nginx config
sudo cp /etc/nginx/sites-available/taxsalecompass.ca /var/backups/tax-sale-compass-manual/nginx_backup_$BACKUP_DATE

# Backup PM2 config
pm2 save
sudo cp ~/.pm2/dump.pm2 /var/backups/tax-sale-compass-manual/pm2_backup_$BACKUP_DATE

echo "✅ Backup completed: /var/backups/tax-sale-compass-manual/"
echo "📝 Backup timestamp: $BACKUP_DATE"
```

---

## **Step 4: Stop Services Safely**

```bash
# Stop PM2 processes
pm2 stop all

# Verify services are stopped
pm2 status

echo "✅ Services stopped safely"
```

---

## **Step 5: Update Application Code**

```bash
cd /var/www/tax-sale-compass

# Add your GitHub repository as remote (replace with your actual repo URL)
git remote set-url origin https://github.com/[your-username]/tax-sale-compass.git

# Stash any local changes
git stash push -m "Local changes before update $(date)"

# Pull latest code
git pull origin main

echo "✅ Code updated from GitHub"
```

---

## **Step 6: Update Backend Dependencies**

```bash
cd /var/www/tax-sale-compass/backend

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Verify server.py has new deployment endpoints
grep -n "deployment/status" server.py
# Should show line numbers with deployment endpoints

echo "✅ Backend dependencies updated"
```

---

## **Step 7: Update Frontend**

```bash
cd /var/www/tax-sale-compass/frontend

# Update dependencies
yarn install

# Rebuild production bundle
yarn build

# Verify build completed
ls -la build/

echo "✅ Frontend updated and built"
```

---

## **Step 8: Set Up Automation System**

```bash
cd /var/www/tax-sale-compass

# Make scripts executable
chmod +x scripts/*.sh

# Run automation setup
sudo ./scripts/setup-automation.sh

# Verify automation scripts are installed
ls -la /opt/tax-sale-compass/scripts/

# Test deployment status script
sudo /opt/tax-sale-compass/scripts/deployment-status.sh

echo "✅ Automation system installed"
```

---

## **Step 9: Restart Services**

```bash
cd /var/www/tax-sale-compass

# Start PM2 processes
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Check PM2 status
pm2 status

# Reload Nginx (don't restart to avoid downtime)
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Services restarted"
```

---

## **Step 10: Verify Everything Works**

**Test Backend:**
```bash
# Test basic API
curl -s http://localhost:8001/api/health
echo ""

# Test new deployment endpoints
curl -s http://localhost:8001/api/deployment/status | head -3
echo ""

# Test frontend
curl -s http://localhost:3000 | head -1
echo ""
```

**Test from Browser:**
1. Go to **https://taxsalecompass.ca**
2. Verify the site loads normally
3. Test search functionality
4. Click on **"Admin"** tab
5. Scroll down to see **"Deployment Management"** section
6. Click **"Health Check"** button
7. Click **"Check Updates"** button

---

## **Step 11: Test Deployment Features**

**In the Admin Panel:**

1. **GitHub Repository URL:** Enter your repository URL
2. **Click "Health Check"** - Should show system status
3. **Click "Check Updates"** - Should check for updates
4. **Click "Verify Status"** - Should verify deployment
5. **DON'T click "Deploy Latest" yet** - we'll test this separately

**Test Deployment Safely:**
```bash
# Test deployment verification
sudo /opt/tax-sale-compass/scripts/deployment.sh verify

# Test update checking
sudo /opt/tax-sale-compass/scripts/deployment.sh check-updates
```

---

## **Step 12: Verify Admin Panel Features**

The admin panel should now show:

✅ **Deployment Management section** with green refresh icon  
✅ **Current Status** showing deployment info  
✅ **System Health** with color-coded status  
✅ **GitHub Repository URL** input field  
✅ **Four action buttons:**
   - Check Updates (blue)
   - Deploy Latest (green) 
   - Verify Status (purple)
   - Health Check (orange)
✅ **Warning message** about deployment downtime

---

## **🚨 Troubleshooting**

**If something goes wrong:**

**1. Service Won't Start:**
```bash
# Check PM2 logs
pm2 logs

# Check specific service logs
pm2 logs tax-sale-backend --lines 50
pm2 logs tax-sale-frontend --lines 50

# Restart individual services
pm2 restart tax-sale-backend
pm2 restart tax-sale-frontend
```

**2. Frontend Build Issues:**
```bash
cd /var/www/tax-sale-compass/frontend
rm -rf node_modules build
yarn install
yarn build
```

**3. Backend Issues:**
```bash
cd /var/www/tax-sale-compass/backend
source venv/bin/activate
python server.py  # Test manually
```

**4. Deployment Endpoints Not Working:**
```bash
# Check if scripts exist
ls -la /opt/tax-sale-compass/scripts/

# Test script permissions
sudo /opt/tax-sale-compass/scripts/deployment-status.sh

# Check sudoers configuration
sudo visudo -c -f /etc/sudoers.d/tax-sale-compass
```

---

## **🔄 Emergency Rollback (If Needed)**

If anything breaks and you need to restore:

```bash
# Stop current services
pm2 delete all

# Restore application
sudo rm -rf /var/www/tax-sale-compass
sudo cp -r /var/backups/tax-sale-compass-manual/app_backup_$BACKUP_DATE /var/www/tax-sale-compass

# Restore nginx config
sudo cp /var/backups/tax-sale-compass-manual/nginx_backup_$BACKUP_DATE /etc/nginx/sites-available/taxsalecompass.ca
sudo nginx -t && sudo systemctl reload nginx

# Restore database (if needed)
mongorestore --db taxsalecompass --drop /var/backups/mongodb/backup_$BACKUP_DATE/taxsalecompass

# Restart services
cd /var/www/tax-sale-compass
pm2 start ecosystem.config.js
```

---

## **✅ Success Verification**

Your update is successful if:

✅ **Website loads:** https://taxsalecompass.ca works normally  
✅ **Search works:** Property search returns results  
✅ **Admin panel:** Shows new "Deployment Management" section  
✅ **Health check:** Button returns system status  
✅ **Check updates:** Button checks GitHub for updates  
✅ **No errors:** PM2 status shows all services online  

---

## **🎉 Next Steps**

Once everything is working:

1. **Test deployment** in low-traffic period:
   - Make a small change to your GitHub repo
   - Use "Deploy Latest" button in admin panel
   - Verify it updates automatically

2. **Set up monitoring:**
   - Check logs periodically: `tail -f /var/log/tax-sale-*.log`
   - Monitor system health via admin panel

3. **Regular maintenance:**
   - Updates are now one-click via admin panel
   - Backups are automatic before each deployment
   - Health monitoring shows system status

**Your Tax Sale Compass now has powerful automated deployment capabilities! 🚀**

---

## **📞 Support**

If you encounter any issues:
1. Check the troubleshooting section above
2. Review logs: `pm2 logs`, `/var/log/tax-sale-*.log`
3. Test individual components step by step
4. Use the emergency rollback if needed

The automation system is designed to be safe with automatic backups and rollback capabilities.