#!/bin/bash

# Setup Favorites System for Tax Sale Compass VPS

echo "Setting up favorites system..."

# Create database tables
mysql -u taxsale -p'SecureTaxSale2025!' tax_sale_compass << 'EOF'

-- Create user_favorites table
CREATE TABLE IF NOT EXISTS user_favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    assessment_number VARCHAR(20) NOT NULL,
    favorited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_property (user_id, assessment_number),
    INDEX idx_user_id (user_id),
    INDEX idx_assessment_number (assessment_number),
    INDEX idx_favorited_at (favorited_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add subscription_status column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status ENUM('free', 'paid') DEFAULT 'free';

-- Add favorite_count column to properties table
ALTER TABLE properties ADD COLUMN IF NOT EXISTS favorite_count INT DEFAULT 0;
ALTER TABLE properties ADD INDEX IF NOT EXISTS idx_favorite_count (favorite_count);

-- Update admin user to have paid subscription
UPDATE users SET subscription_status = 'paid' WHERE email = 'admin';

-- Show results
SELECT 'User Favorites Table:' as status;
DESCRIBE user_favorites;

SELECT 'Users with Subscription Status:' as status;
SELECT id, email, subscription_status FROM users LIMIT 5;

SELECT 'Properties with Favorite Count:' as status;
SELECT assessment_number, civic_address, favorite_count FROM properties LIMIT 5;

EOF

echo "✅ Favorites system setup complete!"
echo ""
echo "Features available:"
echo "- ❤️ Add/Remove favorites (max 50 per paying user)"
echo "- 📊 Favorite count display on property pages" 
echo "- 📋 My Favorites page at /favorites.php"
echo "- 🔒 Restricted to paying users only"
echo ""
echo "Admin user updated to 'paid' subscription status."
echo "Ready for VPS deployment!"