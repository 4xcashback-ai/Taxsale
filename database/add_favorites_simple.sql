-- Add user favorites table for Tax Sale Compass (Simple version)

CREATE TABLE IF NOT EXISTS user_favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    assessment_number VARCHAR(20) NOT NULL,
    favorited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique favorite per user per property
    UNIQUE KEY unique_user_property (user_id, assessment_number),
    
    -- Indexes for performance
    INDEX idx_user_id (user_id),
    INDEX idx_assessment_number (assessment_number),
    INDEX idx_favorited_at (favorited_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add favorite_count column to properties table if it doesn't exist
ALTER TABLE properties 
ADD COLUMN IF NOT EXISTS favorite_count INT DEFAULT 0;

-- Add index for favorite_count
ALTER TABLE properties
ADD INDEX IF NOT EXISTS idx_favorite_count (favorite_count);

-- Initialize favorite counts for existing properties
UPDATE properties SET favorite_count = (
    SELECT COUNT(*) 
    FROM user_favorites 
    WHERE user_favorites.assessment_number = properties.assessment_number
) WHERE EXISTS (
    SELECT 1 FROM user_favorites WHERE user_favorites.assessment_number = properties.assessment_number
);