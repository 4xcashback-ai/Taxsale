-- Rollback script for scraper configuration migration
-- WARNING: This will remove all scraper configurations!

USE tax_sale_compass;

-- Show current data before rollback
SELECT 'Current scraper configurations (will be deleted):' as warning;
SELECT municipality, base_url, enabled FROM scraper_config;

-- Create backup table first (optional safety measure)
-- CREATE TABLE scraper_config_backup_$(date +%Y%m%d) AS SELECT * FROM scraper_config;

-- Drop the scraper_config table
DROP TABLE IF EXISTS scraper_config;

-- Verify rollback
SELECT 'Rollback complete. scraper_config table removed.' as status;

-- Check that table no longer exists (this should produce an error)
-- DESCRIBE scraper_config;