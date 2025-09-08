-- Handle Multiple PIDs and Special Property Types
-- Run this to add support for multiple PIDs and property type classification

-- Add columns for multiple PID support
ALTER TABLE properties 
ADD COLUMN primary_pid VARCHAR(20) AFTER pid_number,
ADD COLUMN secondary_pids TEXT AFTER primary_pid,
ADD COLUMN property_type ENUM('land', 'mobile_home_only', 'building', 'mixed') DEFAULT 'land' AFTER secondary_pids,
ADD COLUMN pid_count INT DEFAULT 1 AFTER property_type;

-- Update existing data to set primary_pid from current pid_number
UPDATE properties 
SET primary_pid = pid_number 
WHERE pid_number IS NOT NULL AND pid_number != '' AND pid_number != 'N/A';

-- Add indexes for better performance
CREATE INDEX idx_properties_primary_pid ON properties (primary_pid);
CREATE INDEX idx_properties_type ON properties (property_type);
CREATE INDEX idx_properties_pid_count ON properties (pid_count);

-- Show current data structure
SELECT 
    COUNT(*) as total_properties,
    COUNT(CASE WHEN primary_pid IS NOT NULL AND primary_pid != '' THEN 1 END) as with_primary_pid,
    COUNT(CASE WHEN property_type = 'mobile_home_only' THEN 1 END) as mobile_home_only,
    COUNT(CASE WHEN pid_count > 1 THEN 1 END) as multiple_pid_properties
FROM properties;