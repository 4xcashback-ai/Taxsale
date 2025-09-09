#!/bin/bash

# Fix property_type ENUM database schema issue
# This script fixes the "Data truncated for column 'property_type'" error

echo "🔧 Fixing property_type ENUM schema..."

# Run the SQL fix
mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass < database/fix_property_type_enum.sql

if [ $? -eq 0 ]; then
    echo "✅ Property type ENUM updated successfully"
    
    # Test the fix by checking current property types
    echo "📊 Current property types in database:"
    mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass -e "
        SELECT property_type, COUNT(*) as count 
        FROM properties 
        GROUP BY property_type 
        ORDER BY count DESC;
    "
else
    echo "❌ Failed to update property type ENUM"
    exit 1
fi

echo "🎉 Property type ENUM fix completed!"