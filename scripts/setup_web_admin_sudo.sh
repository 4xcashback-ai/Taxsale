#!/bin/bash

# Setup sudo permissions for web admin operations
echo "🔧 Setting up web admin sudo permissions..."

# Create sudoers file for web operations
cat > /etc/sudoers.d/taxsale-web-admin << 'EOF'
# Allow www-data to run deployment scripts
www-data ALL=(root) NOPASSWD: /var/www/tax-sale-compass/scripts/vps_deploy.sh
www-data ALL=(root) NOPASSWD: /var/www/tax-sale-compass/scripts/fix_nginx_vps.sh
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl restart nginx
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl restart php8.1-fpm
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl restart mysql
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl reload nginx
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl is-active nginx
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl is-active php8.1-fpm
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl is-active mysql
www-data ALL=(root) NOPASSWD: /usr/bin/pkill -f php-fpm
www-data ALL=(root) NOPASSWD: /usr/bin/nginx -t
EOF

# Set proper permissions
chmod 440 /etc/sudoers.d/taxsale-web-admin

# Test sudoers syntax
visudo -c

if [ $? -eq 0 ]; then
    echo "✅ Sudoers configuration is valid"
else
    echo "❌ Sudoers configuration has errors"
    rm -f /etc/sudoers.d/taxsale-web-admin
    exit 1
fi

echo "✅ Web admin sudo permissions configured successfully"