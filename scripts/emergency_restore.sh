#!/bin/bash

# Emergency restore script for Tax Sale Compass
echo "🚨 Emergency restore for Tax Sale Compass..."

# Restore nginx configuration if tax-sale-compass exists
if [ -f "/etc/nginx/sites-available/tax-sale-compass" ]; then
    echo "✅ Restoring tax-sale-compass nginx configuration..."
    
    # Remove any conflicting configurations
    rm -f /etc/nginx/sites-enabled/taxsale
    rm -f /etc/nginx/sites-available/taxsale
    
    # Enable the working configuration
    ln -sf /etc/nginx/sites-available/tax-sale-compass /etc/nginx/sites-enabled/tax-sale-compass
    
    # Test configuration
    if nginx -t; then
        echo "✅ Nginx configuration is valid"
        systemctl restart nginx
        
        if systemctl is-active nginx >/dev/null; then
            echo "✅ Nginx restarted successfully"
        else
            echo "❌ Nginx failed to restart"
        fi
    else
        echo "❌ Nginx configuration test failed"
    fi
else
    echo "❌ No tax-sale-compass configuration found"
fi

# Restart PHP-FPM
echo "🔄 Restarting PHP-FPM..."
systemctl restart php8.1-fpm

# Check service status
echo "📊 Service Status:"
echo "Nginx: $(systemctl is-active nginx)"
echo "PHP-FPM: $(systemctl is-active php8.1-fpm)" 
echo "MySQL: $(systemctl is-active mysql)"

# Test website
echo "🌐 Testing website..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://localhost/ -k 2>/dev/null || echo "000")
echo "HTTPS response: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "🎉 Website is responding correctly!"
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
    echo "HTTP response: $HTTP_CODE"
    
    if [ "$HTTP_CODE" = "301" ]; then
        echo "✅ HTTP redirecting to HTTPS (normal for SSL sites)"
    else
        echo "❌ Website not responding correctly"
    fi
fi

echo "✅ Emergency restore completed"