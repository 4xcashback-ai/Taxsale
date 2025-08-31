# Tax Sale Compass - VPS Deployment Guide

## Overview
This guide covers deploying Tax Sale Compass to your VPS and updating the existing deployment on taxsalecompass.ca.

## Prerequisites

### System Requirements
- Ubuntu 20.04 LTS or higher
- 2GB+ RAM
- 20GB+ storage
- Root or sudo access

### Required Software
- Node.js 18+ 
- Python 3.9+
- MongoDB 5.0+
- Nginx
- PM2 (Process Manager)
- Git

## Step 1: Export Code from Emergent

1. **Save to GitHub**
   - Use Emergent's "Save to GitHub" feature
   - Note your repository URL (e.g., `https://github.com/yourusername/nstaxsales`)

2. **Clone to VPS**
   ```bash
   cd /var/www
   sudo git clone https://github.com/yourusername/nstaxsales.git
   sudo chown -R $USER:$USER nstaxsales
   cd nstaxsales
   ```

## Step 2: Install Dependencies

### System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Install Nginx
sudo apt install nginx -y

# Install PM2 globally
sudo npm install -g pm2 yarn
```

### MongoDB Setup
```bash
# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Create database user (optional but recommended)
mongo
> use taxsalecompass
> db.createUser({
    user: "taxsale_user",
    pwd: "your_secure_password",
    roles: [{ role: "readWrite", db: "taxsalecompass" }]
  })
> exit
```

## Step 3: Setup Application Environment

### Backend Setup
```bash
cd /var/www/nstaxsales/backend

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install additional dependencies for production
pip install gunicorn
```

### Frontend Setup
```bash
cd /var/www/nstaxsales/frontend

# Install Node dependencies
yarn install

# Build for production
yarn build
```

## Step 4: Environment Configuration

### Backend Environment
```bash
cd /var/www/nstaxsales/backend
nano .env
```

**Backend .env file:**
```env
# Database
MONGO_URL=mongodb://localhost:27017/taxsalecompass
# OR if using authentication:
# MONGO_URL=mongodb://taxsale_user:your_secure_password@localhost:27017/taxsalecompass

DB_NAME=taxsalecompass
DATABASE_NAME=taxsalecompass

# API Keys (get these from your current deployment)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# CORS
CORS_ORIGINS=["https://taxsalecompass.ca", "https://www.taxsalecompass.ca"]

# Production settings
ENVIRONMENT=production
```

### Frontend Environment
```bash
cd /var/www/nstaxsales/frontend
nano .env
```

**Frontend .env file:**
```env
REACT_APP_BACKEND_URL=https://taxsalecompass.ca
REACT_APP_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

## Step 5: PM2 Process Configuration

Create PM2 ecosystem file:
```bash
cd /var/www/nstaxsales
nano ecosystem.config.js
```

**ecosystem.config.js:**
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

## Step 6: Nginx Configuration

### Backup existing config (if updating)
```bash
sudo cp /etc/nginx/sites-available/taxsalecompass.ca /etc/nginx/sites-available/taxsalecompass.ca.backup
```

### Create/Update Nginx config
```bash
sudo nano /etc/nginx/sites-available/taxsalecompass.ca
```

**Nginx configuration:**
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

### Enable site and restart Nginx
```bash
sudo ln -sf /etc/nginx/sites-available/taxsalecompass.ca /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 7: SSL Certificate (if not already configured)

If you don't have SSL certificates, install Certbot:
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d taxsalecompass.ca -d www.taxsalecompass.ca
```

## Step 8: Deploy Application

### Start services
```bash
cd /var/www/nstaxsales

# Start applications with PM2
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 startup
pm2 startup systemd
# Follow the instructions provided by the command above
```

### Verify deployment
```bash
# Check PM2 status
pm2 status

# Check logs
pm2 logs

# Check if services are responding
curl http://localhost:8001/api/health
curl http://localhost:3000
```

## Step 9: Database Migration (if updating existing deployment)

If you have existing data, you may need to migrate:
```bash
# Backup existing database
mongodump --db taxsalecompass --out /backup/mongodb-backup-$(date +%Y%m%d)

# If needed, restore or migrate data
# mongorestore --db taxsalecompass /path/to/backup
```

## Step 10: Post-Deployment Tasks

### Setup log rotation
```bash
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

### Setup monitoring
```bash
# Monitor PM2 processes
pm2 monit

# Setup automatic restarts
pm2 set pm2:autodump true
```

### Firewall configuration
```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

## Updating Existing Deployment

For future updates:

```bash
cd /var/www/nstaxsales

# Pull latest changes
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Update frontend
cd ../frontend
yarn install
yarn build

# Restart services
pm2 restart all

# Check status
pm2 status
pm2 logs --lines 50
```

## Troubleshooting

### Common issues:

1. **Port conflicts**: Ensure ports 3000 and 8001 are available
2. **Permission issues**: 
   ```bash
   sudo chown -R $USER:$USER /var/www/tax-sale-compass
   ```
3. **MongoDB connection**: Check MongoDB status
   ```bash
   sudo systemctl status mongod
   ```
4. **Environment variables**: Verify .env files are properly configured

### Useful commands:
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
```

## Security Recommendations

1. **Keep system updated**: `sudo apt update && sudo apt upgrade`
2. **Regular backups**: Setup automated MongoDB backups
3. **Monitor logs**: Check for suspicious activity
4. **SSL certificate renewal**: Certbot should auto-renew, but verify periodically
5. **Firewall**: Keep UFW enabled with minimal required ports
6. **Application updates**: Regular deployment of security updates

## Performance Optimization

1. **Enable Gzip**: Already configured in Nginx
2. **Static file caching**: Configured for 1 year
3. **Database indexing**: Ensure proper MongoDB indexes
4. **PM2 clustering**: Consider increasing worker count for high traffic
5. **CDN**: Consider using CloudFlare for static assets

---

Your Tax Sale Compass application should now be successfully deployed and accessible at https://taxsalecompass.ca!