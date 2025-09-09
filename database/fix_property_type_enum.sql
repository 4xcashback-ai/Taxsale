-- Fix property_type ENUM to include all values used by the application
-- This fixes the "Data truncated for column 'property_type'" error

-- First, check current ENUM values
SELECT COLUMN_TYPE 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'tax_sale_compass' 
  AND TABLE_NAME = 'properties' 
  AND COLUMN_NAME = 'property_type';

-- Update the ENUM to include all property types used by the application
-- Current ENUM: enum('land','building','mixed','mobile_home_only','regular')
-- Need to add: 'apartment'

ALTER TABLE properties 
MODIFY COLUMN property_type 
ENUM(
    'land',                -- Vacant land properties
    'building',            -- Building only properties  
    'mixed',               -- Land + Building properties (houses, etc.)
    'mobile_home_only',    -- Mobile home properties
    'regular',             -- Regular properties (from enhanced scraper)
    'apartment'            -- Apartment/Condo properties (NEW)
) DEFAULT 'land';

-- Verify the update
SELECT COLUMN_TYPE 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'tax_sale_compass' 
  AND TABLE_NAME = 'properties' 
  AND COLUMN_NAME = 'property_type';

-- Show count of each property type currently in database
SELECT property_type, COUNT(*) as count 
FROM properties 
GROUP BY property_type 
ORDER BY count DESC;