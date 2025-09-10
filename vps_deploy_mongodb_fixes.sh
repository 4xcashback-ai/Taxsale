#!/bin/bash

echo "=== VPS MongoDB Deployment Script ==="
echo "This script will deploy all fixed files for MongoDB compatibility"

# Set proper permissions and ownership
echo "Setting file permissions..."
sudo chown -R www-data:www-data /var/www/tax-sale-compass/frontend-php/
sudo chmod -R 755 /var/www/tax-sale-compass/frontend-php/
sudo chmod 644 /var/www/tax-sale-compass/frontend-php/config/database.php

# Test MongoDB connection
echo "Testing MongoDB connection..."
php -r "
require_once '/var/www/tax-sale-compass/frontend-php/config/database.php';
echo 'Testing MongoDB...' . PHP_EOL;
\$db = getDB();
if (\$db) {
    echo 'SUCCESS: MongoDB connected' . PHP_EOL;
    echo 'Properties: ' . \$db->properties->countDocuments() . PHP_EOL;
    echo 'Users: ' . \$db->users->countDocuments() . PHP_EOL;
} else {
    echo 'FAILED: MongoDB connection failed' . PHP_EOL;
}
"

# Test PHP syntax
echo "Checking PHP syntax..."
php -l /var/www/tax-sale-compass/frontend-php/index.php
php -l /var/www/tax-sale-compass/frontend-php/config/database.php
php -l /var/www/tax-sale-compass/frontend-php/api/favorites.php

# Restart services
echo "Restarting services..."
sudo systemctl restart php8.1-fpm
sudo systemctl restart nginx

# Test website
echo "Testing website..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://taxsalecompass.ca/)
echo "Website HTTP response: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS: Website is working!"
else
    echo "❌ ERROR: Website returned HTTP $HTTP_CODE"
    echo "Checking error logs..."
    sudo tail -5 /var/log/nginx/error.log
fi

echo "=== Deployment Complete ==="
echo ""
echo "Files updated for MongoDB compatibility:"
echo "- config/database.php (MongoDB connection)"
echo "- index.php (Landing page with MongoDB)"  
echo "- search.php (Property search with MongoDB)"
echo "- property.php (Property details with MongoDB)"
echo "- api/favorites.php (Favorites API with MongoDB)"
echo "- favorites.php (Favorites page with MongoDB)"
echo "- admin.php (Database reference updated)"
echo ""
echo "Next steps:"
echo "1. Upload all files from /app/frontend-php/ to /var/www/tax-sale-compass/frontend-php/"
echo "2. Run: sudo chown -R www-data:www-data /var/www/tax-sale-compass/frontend-php/"
echo "3. Run: sudo systemctl restart php8.1-fpm nginx"
echo "4. Test: curl -I https://taxsalecompass.ca/"