-- Add user favorites table for Tax Sale Compass
-- This table tracks which properties users have favorited

CREATE TABLE IF NOT EXISTS user_favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    assessment_number VARCHAR(20) NOT NULL,
    favorited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assessment_number) REFERENCES properties(assessment_number) ON DELETE CASCADE,
    
    -- Ensure unique favorite per user per property
    UNIQUE KEY unique_user_property (user_id, assessment_number),
    
    -- Indexes for performance
    INDEX idx_user_id (user_id),
    INDEX idx_assessment_number (assessment_number),
    INDEX idx_favorited_at (favorited_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add favorite count trigger
DELIMITER //
CREATE TRIGGER update_favorite_count_insert 
AFTER INSERT ON user_favorites
FOR EACH ROW
BEGIN
    UPDATE properties 
    SET favorite_count = (
        SELECT COUNT(*) 
        FROM user_favorites 
        WHERE assessment_number = NEW.assessment_number
    )
    WHERE assessment_number = NEW.assessment_number;
END//

CREATE TRIGGER update_favorite_count_delete 
AFTER DELETE ON user_favorites
FOR EACH ROW
BEGIN
    UPDATE properties 
    SET favorite_count = (
        SELECT COUNT(*) 
        FROM user_favorites 
        WHERE assessment_number = OLD.assessment_number
    )
    WHERE assessment_number = OLD.assessment_number;
END//
DELIMITER ;

-- Add favorite_count column to properties table if it doesn't exist
ALTER TABLE properties 
ADD COLUMN IF NOT EXISTS favorite_count INT DEFAULT 0,
ADD INDEX idx_favorite_count (favorite_count);

-- Initialize favorite counts for existing properties
UPDATE properties SET favorite_count = (
    SELECT COUNT(*) 
    FROM user_favorites 
    WHERE user_favorites.assessment_number = properties.assessment_number
);