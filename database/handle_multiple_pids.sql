-- Handle Multiple PIDs and Special Property Types
-- Run this to add support for multiple PIDs and property type classification
-- Safe migration that handles existing data

-- First, let's see what property_type values already exist
SELECT DISTINCT property_type, COUNT(*) as count 
FROM properties 
WHERE property_type IS NOT NULL 
GROUP BY property_type;

-- Migrate existing property_type values to new standard (handle all cases)
UPDATE properties SET property_type = 'mixed' WHERE property_type = 'Dwelling';
UPDATE properties SET property_type = 'land' WHERE property_type = 'Land';
UPDATE properties SET property_type = 'land' WHERE property_type = 'Unknown';
UPDATE properties SET property_type = 'land' WHERE property_type = 'vacant_land';
UPDATE properties SET property_type = 'building' WHERE property_type = 'commercial';
UPDATE properties SET property_type = 'building' WHERE property_type = 'residential';
UPDATE properties SET property_type = 'land' WHERE property_type = '' OR property_type IS NULL;

-- Show data after cleanup
SELECT 'After cleanup:' as status;
SELECT DISTINCT property_type, COUNT(*) as count 
FROM properties 
WHERE property_type IS NOT NULL 
GROUP BY property_type;

-- Add columns for multiple PID support (with existence checks)
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'properties' 
     AND column_name = 'primary_pid' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE properties ADD COLUMN primary_pid VARCHAR(20) AFTER pid_number",
    "SELECT 'Column primary_pid already exists' as notice"
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'properties' 
     AND column_name = 'secondary_pids' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE properties ADD COLUMN secondary_pids TEXT AFTER primary_pid",
    "SELECT 'Column secondary_pids already exists' as notice"
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'properties' 
     AND column_name = 'pid_count' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE properties ADD COLUMN pid_count INT DEFAULT 1 AFTER secondary_pids",
    "SELECT 'Column pid_count already exists' as notice"
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Now apply the enum constraint after data is cleaned
ALTER TABLE properties MODIFY COLUMN property_type ENUM('land', 'mobile_home_only', 'building', 'mixed') DEFAULT 'land';

-- Update existing data to set primary_pid from current pid_number (only if primary_pid is empty)
UPDATE properties 
SET primary_pid = pid_number 
WHERE (primary_pid IS NULL OR primary_pid = '') 
  AND pid_number IS NOT NULL 
  AND pid_number != '' 
  AND pid_number != 'N/A';

-- Add indexes for better performance (with existence checks)
CREATE INDEX IF NOT EXISTS idx_properties_primary_pid ON properties (primary_pid);
CREATE INDEX IF NOT EXISTS idx_properties_type ON properties (property_type);
CREATE INDEX IF NOT EXISTS idx_properties_pid_count ON properties (pid_count);

-- Show current data structure after migration
SELECT 'Migration Results:' as status;
SELECT 
    COUNT(*) as total_properties,
    COUNT(CASE WHEN primary_pid IS NOT NULL AND primary_pid != '' THEN 1 END) as with_primary_pid,
    COUNT(CASE WHEN property_type = 'mobile_home_only' THEN 1 END) as mobile_home_only,
    COUNT(CASE WHEN property_type = 'mixed' THEN 1 END) as mixed_properties,
    COUNT(CASE WHEN property_type = 'land' THEN 1 END) as land_only,
    COUNT(CASE WHEN property_type = 'building' THEN 1 END) as building_only,
    COUNT(CASE WHEN pid_count > 1 THEN 1 END) as multiple_pid_properties
FROM properties;

-- Show property type distribution
SELECT property_type, COUNT(*) as count 
FROM properties 
GROUP BY property_type;