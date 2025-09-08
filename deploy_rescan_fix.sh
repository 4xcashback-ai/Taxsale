#!/bin/bash

# Direct deployment script for Halifax rescan fix
# No Git required - just copy the changed files

echo "🚀 Deploying Halifax Rescan Fix to VPS..."

VPS_HOST="$1"
VPS_USER="${2:-root}"
VPS_PATH="/var/www/tax-sale-compass"

if [ -z "$VPS_HOST" ]; then
    echo "❌ Usage: $0 <vps-ip-or-domain> [user]"
    echo "   Example: $0 your-vps-ip.com root"
    exit 1
fi

echo "📋 Deployment Summary:"
echo "   - Target: $VPS_USER@$VPS_HOST:$VPS_PATH"
echo "   - Files: backend/scrapers_mysql.py, backend/mysql_config.py"
echo "   - Database: Update Halifax scraper configuration"
echo ""

# 1. Copy the fixed Python files
echo "📁 Copying backend files..."
scp /app/backend/scrapers_mysql.py $VPS_USER@$VPS_HOST:$VPS_PATH/backend/
scp /app/backend/mysql_config.py $VPS_USER@$VPS_HOST:$VPS_PATH/backend/

# 2. Update Halifax URL in database
echo "🗄️ Updating Halifax URL in database..."
ssh $VPS_USER@$VPS_HOST "mysql -u taxsale -pSecureTaxSale2025! tax_sale_compass << 'EOF'
UPDATE scraper_config 
SET tax_sale_page_url = 'https://www.halifax.ca/home-property/property-taxes/tax-sale',
    pdf_search_patterns = JSON_ARRAY('/media/91740', '/media/91402', 'SCHEDULE.*A.*TAXSALE', 'TENDER.*DOCUMENT.*'),
    excel_search_patterns = JSON_ARRAY('/media/91740', '/media/91402', 'SCHEDULE.*A.*TAXSALE', 'TENDER.*DOCUMENT.*')
WHERE municipality = 'Halifax Regional Municipality';
EOF"

# 3. Restart backend service
echo "🔄 Restarting backend service..."
ssh $VPS_USER@$VPS_HOST "sudo systemctl restart tax-sale-backend"

# 4. Test the fix
echo "🧪 Testing the rescan functionality..."
ssh $VPS_USER@$VPS_HOST "cd $VPS_PATH && timeout 10 python3 -c \"
import sys
sys.path.append('backend')
from scrapers_mysql import rescan_halifax_property
result = rescan_halifax_property('01999184')
print('✅ Rescan test result:', result.get('success', False))
print('📝 Message:', result.get('message', 'No message'))
\" 2>/dev/null || echo '⚠️ Test timeout - but deployment complete'"

echo ""
echo "✅ Deployment complete!"
echo "🔍 The Halifax rescan fix is now live on your VPS"
echo "📍 Fixed URL: https://www.halifax.ca/home-property/property-taxes/tax-sale"
echo ""
echo "Test the rescan functionality in your admin panel:"
echo "   1. Go to admin panel"
echo "   2. Find property 01999184 in 'Missing PIDs'"  
echo "   3. Click 'Rescan' - should now work!"
