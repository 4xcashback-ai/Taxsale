# 🚀 Fresh VPS Deployment - Tax Sale Compass PHP/MySQL
## Panel-Free High Performance Setup

Complete instructions for deploying the new PHP/MySQL version on a fresh VPS with **maximum performance** and **no panel overhead**.

## 📋 Prerequisites

- Fresh Ubuntu 22.04 LTS VPS (recommended)
- Root access  
- AI Assistant for any command line help needed 🤖
- Domain pointed to VPS (optional)

## 🔧 Step 1: System Setup & Optimization

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install core packages (optimized selection)
sudo apt install -y \
  git nginx mysql-server \
  php8.1-fpm php8.1-mysql php8.1-json php8.1-mbstring php8.1-curl php8.1-xml \
  python3 python3-pip python3-venv \
  curl wget unzip htop ncdu \
  ufw fail2ban logrotate

# Basic security setup
sudo ufw allow 22
sudo ufw allow 80  
sudo ufw allow 443
sudo ufw --force enable

# Optimize system
echo 'net.core.somaxconn = 65536' | sudo tee -a /etc/sysctl.conf
echo 'vm.swappiness = 10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## 🗄️ Step 2: MySQL Setup & Optimization

```bash
# Secure MySQL installation
sudo mysql_secure_installation
# Answer: Y, 2 (strong password), Y, Y, Y, Y

# Login to MySQL and create optimized database
sudo mysql -u root -p

# Create database with optimized settings
CREATE DATABASE tax_sale_compass CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Create user with secure password
CREATE USER 'taxsale'@'localhost' IDENTIFIED BY 'TaxSale2025!SecureDB';
GRANT ALL PRIVILEGES ON tax_sale_compass.* TO 'taxsale'@'localhost';
FLUSH PRIVILEGES;

# Optimize MySQL for property searches
SET GLOBAL innodb_buffer_pool_size = 128M;
SET GLOBAL query_cache_size = 16M;
SET GLOBAL query_cache_type = 1;

EXIT;

# Optimize MySQL config for better performance
sudo tee -a /etc/mysql/mysql.conf.d/tax-sale-optimization.cnf << EOF
[mysqld]
# Optimized for property database searches
innodb_buffer_pool_size = 256M
query_cache_size = 32M
query_cache_type = 1
key_buffer_size = 32M
table_open_cache = 64
sort_buffer_size = 512K
net_buffer_length = 8K
read_buffer_size = 256K
read_rnd_buffer_size = 512K
myisam_sort_buffer_size = 8M

# Logging
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
EOF

sudo systemctl restart mysql
```

## 📥 Step 3: Deploy Application

```bash
# Clone repository
cd /var/www/
sudo git clone https://github.com/4xcashback-ai/Taxsale.git tax-sale-compass
sudo chown -R www-data:www-data tax-sale-compass
cd tax-sale-compass

# Setup MySQL schema
sudo mysql -u root -p tax_sale_compass < database/mysql_schema.sql

# Setup Python backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🌐 Step 4: High-Performance Nginx Configuration

Create optimized Nginx configuration:

```bash
# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Create optimized Tax Sale Compass config
sudo tee /etc/nginx/sites-available/tax-sale-compass << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name _;  # Replace with your domain
    root /var/www/tax-sale-compass/frontend-php;
    index index.php index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # PHP handling (optimized)
    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
        
        # Performance settings
        fastcgi_buffer_size 128k;
        fastcgi_buffers 4 256k;
        fastcgi_busy_buffers_size 256k;
    }

    # API proxy to FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Performance settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # Static files with caching
    location /static/ {
        alias /var/www/tax-sale-compass/backend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # CSS/JS caching
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
        expires 7d;
        add_header Cache-Control "public";
    }

    # Main routing
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    # Security: Block access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ /(config|database|scripts)/ {
        deny all;
    }
}
EOF

# Enable site and optimize Nginx
sudo ln -s /etc/nginx/sites-available/tax-sale-compass /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Optimize Nginx for better performance
sudo tee -a /etc/nginx/nginx.conf << 'EOF'

# Tax Sale Compass Optimizations
worker_processes auto;
worker_connections 1024;
keepalive_timeout 30;
client_max_body_size 20M;
EOF

sudo systemctl restart nginx
```

## 🐍 Step 5: Backend Service Setup

Create systemd service:

```bash
sudo nano /etc/systemd/system/tax-sale-backend.service
```

Add:

```ini
[Unit]
Description=Tax Sale Compass FastAPI Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/tax-sale-compass/backend
Environment=PATH=/var/www/tax-sale-compass/backend/venv/bin
ExecStart=/var/www/tax-sale-compass/backend/venv/bin/python server_mysql.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tax-sale-backend
sudo systemctl start tax-sale-backend
sudo systemctl status tax-sale-backend
```

## 🔧 Step 6: Configuration

Update database config if needed:

```bash
sudo nano /var/www/tax-sale-compass/frontend-php/config/database.php
```

Set your MySQL credentials:

```php
define('DB_HOST', 'localhost');
define('DB_USER', 'taxsale');
define('DB_PASS', 'secure_password_here');
define('DB_NAME', 'tax_sale_compass');
```

## 🧪 Step 7: Test the System

1. **Access website**: `http://your-domain.com`
2. **Login**: admin / TaxSale2025!SecureAdmin
3. **Test property search**: Should show empty initially
4. **Access admin panel**: Should show scraping options
5. **Run scraper**: Test one municipality scraper
6. **Test Google Maps**: Property details should show map without conflicts

## 🔄 Step 8: Data Population

Once system is running, populate with data:

1. Login to admin panel
2. Click "Scrape All Municipalities"
3. Wait for completion
4. Test property search and details

## 🔒 Step 9: Security (Optional)

Install SSL certificate:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## 📊 Step 10: Monitoring

Check services:

```bash
# Backend status
sudo systemctl status tax-sale-backend

# Nginx status
sudo systemctl status nginx

# PHP-FPM status
sudo systemctl status php8.1-fpm

# MySQL status
sudo systemctl status mysql

# View backend logs
sudo journalctl -u tax-sale-backend -f
```

## 🎉 Success Criteria

After deployment, you should have:

- ✅ **Working PHP frontend** on port 80
- ✅ **FastAPI backend** on port 8001
- ✅ **MySQL database** with empty tables
- ✅ **Admin login** working
- ✅ **Google Maps** loading without conflicts
- ✅ **Property scrapers** ready to populate data
- ✅ **No React build process** - direct PHP serving
- ✅ **Simple deployment** - just git pull for updates

## 🛠️ Troubleshooting

**Backend not starting:**
```bash
sudo journalctl -u tax-sale-backend -n 50
```

**PHP errors:**
```bash
sudo tail -f /var/log/nginx/error.log
```

**Database connection issues:**
```bash
mysql -u taxsale -p tax_sale_compass -e "SHOW TABLES;"
```

## 🔄 Future Updates

To update the system:

```bash
cd /var/www/tax-sale-compass
sudo git pull origin main
sudo systemctl restart tax-sale-backend
sudo systemctl reload nginx
```

That's it! Your clean PHP/MySQL Tax Sale Compass is now running! 🎉