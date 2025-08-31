# Step-by-Step VPS Deployment Guide

This guide will walk you through deploying Tax Sale Compass on your existing VPS at taxsalecompass.ca step by step.

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] Root or sudo access to your VPS
- [ ] Domain taxsalecompass.ca pointing to your VPS
- [ ] SSH access to your server
- [ ] Your GitHub repository URL where you'll save the code

## Step 1: Export Code from Emergent

1. **In Emergent Interface:**
   - Click "Save to GitHub" button
   - Connect your GitHub account if not already connected
   - Create or select repository (e.g., `tax-sale-compass`)
   - Push the code to GitHub

2. **Note down your repository URL:**
   ```
   https://github.com/[your-username]/tax-sale-compass.git
   ```

## Step 2: Connect to Your VPS

```bash
ssh root@taxsalecompass.ca
# or
ssh your-username@taxsalecompass.ca
```

## Step 3: Install System Dependencies

Run these commands one by one:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify Node.js installation
node --version
npm --version

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install MongoDB (if not already installed)
wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Install Nginx (if not already installed)
sudo apt install nginx -y

# Install PM2 and Yarn globally
sudo npm install -g pm2 yarn

# Install additional system tools
sudo apt install curl wget git htop -y
```

## Step 4: Clone Your Application

```bash
# Navigate to web directory
cd /var/www

# Clone your repository (replace with your actual repo URL)
sudo git clone https://github.com/[your-username]/tax-sale-compass.git

# Set ownership
sudo chown -R $USER:$USER tax-sale-compass
cd tax-sale-compass
```

## Step 5: Setup Backend Environment

```bash
cd /var/www/tax-sale-compass/backend

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install production server
pip install gunicorn

# Create/update .env file
nano .env
```

**Add this content to .env file:**
```env
# Database
MONGO_URL=mongodb://localhost:27017/taxsalecompass
DB_NAME=taxsalecompass
DATABASE_NAME=taxsalecompass

# API Keys - GET THESE FROM YOUR CURRENT DEPLOYMENT
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# CORS
CORS_ORIGINS=["https://taxsalecompass.ca", "https://www.taxsalecompass.ca"]

# Production settings
ENVIRONMENT=production
```

**Important:** Replace `your_google_maps_api_key_here` with your actual Google Maps API key.

## Step 6: Setup Frontend Environment

```bash
cd /var/www/tax-sale-compass/frontend

# Install dependencies
yarn install

# Create/update .env file
nano .env
```

**Add this content to frontend .env file:**
```env
REACT_APP_BACKEND_URL=https://taxsalecompass.ca
REACT_APP_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

**Build production bundle:**
```bash
yarn build
```

## Step 7: Setup PM2 Configuration

```bash
cd /var/www/tax-sale-compass

# Create PM2 ecosystem file
nano ecosystem.config.js
```

**Add this content:**
```javascript
module.exports = {
  apps: [
    {
      name: 'tax-sale-backend',
      cwd: '/var/www/tax-sale-compass/backend',
      script: 'venv/bin/gunicorn',
      args: '-w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001 server:app',
      env: {
        NODE_ENV: 'production'
      },
      error_file: '/var/log/tax-sale-backend.err.log',
      out_file: '/var/log/tax-sale-backend.out.log',
      log_file: '/var/log/tax-sale-backend.log',
      max_restarts: 3,
      restart_delay: 5000
    },
    {
      name: 'tax-sale-frontend',
      cwd: '/var/www/tax-sale-compass/frontend',
      script: 'npx',
      args: 'serve -s build -l 3000',
      env: {
        NODE_ENV: 'production'
      },
      error_file: '/var/log/tax-sale-frontend.err.log',
      out_file: '/var/log/tax-sale-frontend.out.log',
      log_file: '/var/log/tax-sale-frontend.log',
      max_restarts: 3,
      restart_delay: 5000
    }
  ]
};
```

## Step 8: Configure Nginx

**Backup existing config:**
```bash
sudo cp /etc/nginx/sites-available/taxsalecompass.ca /etc/nginx/sites-available/taxsalecompass.ca.backup
```

**Create/update Nginx configuration:**
```bash
sudo nano /etc/nginx/sites-available/taxsalecompass.ca
```

**Add this configuration:**
```nginx
server {
    listen 80;
    server_name taxsalecompass.ca www.taxsalecompass.ca;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name taxsalecompass.ca www.taxsalecompass.ca;

    # SSL Configuration (update paths as needed)
    ssl_certificate /etc/letsencrypt/live/taxsalecompass.ca/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/taxsalecompass.ca/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Frontend (React build)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Backend API routes
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Static files for property screenshots
    location /static/ {
        alias /var/www/tax-sale-compass/backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;

    client_max_body_size 10M;
}
```

**Enable the site:**
```bash
sudo ln -sf /etc/nginx/sites-available/taxsalecompass.ca /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 9: Setup SSL Certificate (if needed)

If you don't have SSL certificates:
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d taxsalecompass.ca -d www.taxsalecompass.ca
```

## Step 10: Start the Application

```bash
cd /var/www/tax-sale-compass

# Start applications with PM2
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 startup (follow the command output)
pm2 startup systemd
```

## Step 11: Setup Automation Scripts

```bash
# Make automation scripts executable
chmod +x /var/www/tax-sale-compass/scripts/*.sh

# Run the setup automation script
sudo /var/www/tax-sale-compass/scripts/setup-automation.sh
```

## Step 12: Verify Deployment

**Check services:**
```bash
# Check PM2 status
pm2 status

# Check if backend is responding
curl http://localhost:8001/api/health

# Check if frontend is responding
curl http://localhost:3000

# Check Nginx status
sudo systemctl status nginx

# Check MongoDB status
sudo systemctl status mongod
```

**Test from browser:**
1. Visit https://taxsalecompass.ca
2. Check if the site loads properly
3. Test the search functionality
4. Check the admin panel

## Step 13: Setup Monitoring and Backups

```bash
# Setup log rotation
sudo nano /etc/logrotate.d/tax-sale-compass
```

Add:
```
/var/log/tax-sale-*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

**Setup firewall:**
```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

## Step 14: Test Admin Deployment Features

1. Go to your admin panel: https://taxsalecompass.ca (Admin tab)
2. Scroll to "Deployment Management" section
3. Test the following buttons:
   - **Check Updates** - See if updates are available
   - **Health Check** - Verify system health
   - **Verify Status** - Confirm deployment is working

## Troubleshooting

### Common Issues:

1. **Backend not starting:**
   ```bash
   cd /var/www/tax-sale-compass/backend
   source venv/bin/activate
   python server.py  # Test manually
   ```

2. **Frontend build fails:**
   ```bash
   cd /var/www/tax-sale-compass/frontend
   rm -rf node_modules
   yarn install
   yarn build
   ```

3. **MongoDB connection issues:**
   ```bash
   sudo systemctl status mongod
   mongo --eval "db.adminCommand('ismaster')"
   ```

4. **Permission issues:**
   ```bash
   sudo chown -R $USER:$USER /var/www/tax-sale-compass
   ```

5. **PM2 process issues:**
   ```bash
   pm2 logs
   pm2 restart all
   ```

### Useful Commands:

```bash
# Check application logs
pm2 logs tax-sale-backend --lines 100
pm2 logs tax-sale-frontend --lines 100

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Check system resources
htop
df -h
free -h

# Restart everything
pm2 restart all
sudo systemctl reload nginx
```

## Future Updates

Once everything is set up, you can use the **Admin Deployment Panel** to:
1. Check for updates from your GitHub repository
2. Deploy new versions automatically
3. Monitor system health
4. Verify deployments

The automation scripts handle:
- Pulling latest code from GitHub
- Installing dependencies
- Building frontend
- Restarting services
- Creating backups
- Rolling back if needed

## Success! 

Your Tax Sale Compass application should now be successfully deployed on your VPS at https://taxsalecompass.ca with automated deployment capabilities!