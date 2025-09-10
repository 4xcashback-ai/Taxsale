-- Add auction information fields to properties table
-- Run this to add sale_date and auction_type columns

-- Add sale_date column
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'properties' 
     AND column_name = 'sale_date' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE properties ADD COLUMN sale_date DATE AFTER status",
    "SELECT 'Column sale_date already exists' as notice"
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add auction_type column
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'properties' 
     AND column_name = 'auction_type' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE properties ADD COLUMN auction_type ENUM('Public Auction', 'Public Tender Auction') DEFAULT 'Public Auction' AFTER sale_date",
    "SELECT 'Column auction_type already exists' as notice"
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add indexes for better performance
SET @sql = 'CREATE INDEX idx_properties_sale_date ON properties (sale_date)';
SET @sql = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS WHERE table_name = 'properties' AND index_name = 'idx_properties_sale_date' AND table_schema = DATABASE()) > 0, 'SELECT "Index idx_properties_sale_date already exists" AS notice', @sql);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql = 'CREATE INDEX idx_properties_auction_type ON properties (auction_type)';
SET @sql = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS WHERE table_name = 'properties' AND index_name = 'idx_properties_auction_type' AND table_schema = DATABASE()) > 0, 'SELECT "Index idx_properties_auction_type already exists" AS notice', @sql);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Show current properties with auction info
SELECT 'Properties with auction information:' as status;
SELECT 
    assessment_number,
    civic_address,
    sale_date,
    auction_type,
    property_type
FROM properties 
WHERE sale_date IS NOT NULL 
LIMIT 5;

-- Show auction statistics
SELECT 'Auction Statistics:' as status;
SELECT 
    COUNT(*) as total_properties,
    COUNT(sale_date) as with_sale_date,
    COUNT(CASE WHEN auction_type = 'Public Auction' THEN 1 END) as public_auctions,
    COUNT(CASE WHEN auction_type = 'Public Tender Auction' THEN 1 END) as tender_auctions
FROM properties;