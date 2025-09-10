-- Add thumbnail support to properties table
-- Run this to add thumbnail_path column if it doesn't exist

-- Add thumbnail_path column
ALTER TABLE properties 
ADD COLUMN thumbnail_path VARCHAR(255) DEFAULT NULL;

-- Add index for faster queries on properties needing thumbnails
CREATE INDEX idx_properties_thumbnail 
ON properties (pid_number, thumbnail_path);

-- Add index for faster queries on properties with PID (without WHERE clause for MariaDB compatibility)
CREATE INDEX idx_properties_pid 
ON properties (pid_number);

-- Update existing properties to have proper null values
UPDATE properties 
SET thumbnail_path = NULL 
WHERE thumbnail_path = '';

-- Show current thumbnail status
SELECT 
    COUNT(*) as total_properties,
    COUNT(CASE WHEN pid_number IS NOT NULL AND pid_number != '' AND pid_number != 'N/A' THEN 1 END) as properties_with_pid,
    COUNT(CASE WHEN thumbnail_path IS NOT NULL AND thumbnail_path != '' THEN 1 END) as properties_with_thumbnails,
    COUNT(CASE WHEN pid_number IS NOT NULL AND pid_number != '' AND pid_number != 'N/A' 
               AND (thumbnail_path IS NULL OR thumbnail_path = '') THEN 1 END) as properties_needing_thumbnails
FROM properties;