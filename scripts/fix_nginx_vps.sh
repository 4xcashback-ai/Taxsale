#!/bin/bash

# Fix nginx configuration for VPS deployment
echo "🔧 Fixing nginx configuration for Tax Sale Compass..."

# Backup existing nginx config
cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S)

# Create new nginx configuration for Tax Sale Compass
cat > /etc/nginx/sites-available/taxsale << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name taxsalecompass.ca www.taxsalecompass.ca localhost;
    
    root /var/www/tax-sale-compass/frontend-php;
    index index.php index.html index.htm;
    
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Handle PHP files
    location ~ \.php$ {
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\.php)(/.+)$;
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
        fastcgi_param PATH_INFO $fastcgi_path_info;
        
        # Increase timeout for long-running operations
        fastcgi_read_timeout 300;
        fastcgi_connect_timeout 300;
        fastcgi_send_timeout 300;
    }
    
    # Handle static files with caching
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
        try_files $uri =404;
    }
    
    # API endpoints (if needed for future backend integration)
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    # Default location with proper PHP routing
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Hide nginx version
    server_tokens off;
    
    # Prevent access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ /(config|includes|scripts)/.*\.(php|inc)$ {
        deny all;
    }
    
    # Log files
    access_log /var/log/nginx/taxsale_access.log;
    error_log /var/log/nginx/taxsale_error.log;
}

# HTTPS redirect (if SSL is configured)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name taxsalecompass.ca www.taxsalecompass.ca;
    
    # SSL configuration (update paths as needed)
    ssl_certificate /etc/letsencrypt/live/taxsalecompass.ca/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/taxsalecompass.ca/privkey.pem;
    
    root /var/www/tax-sale-compass/frontend-php;
    index index.php index.html index.htm;
    
    # Same configuration as HTTP version
    include /etc/nginx/sites-available/taxsale;
}
EOF

# Enable the new site
ln -sf /etc/nginx/sites-available/taxsale /etc/nginx/sites-enabled/taxsale

# Disable default site if it exists
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    
    # Reload nginx
    systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
    
    # Test the website
    echo "🔍 Testing website response..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
    echo "Website HTTP response: $HTTP_CODE"
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "🎉 Website is responding correctly!"
    else
        echo "⚠️ Website response code: $HTTP_CODE"
    fi
else
    echo "❌ Nginx configuration test failed"
    exit 1
fi

echo "✅ Nginx configuration fix completed"