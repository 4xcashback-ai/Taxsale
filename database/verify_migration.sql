-- Verification script for scraper configuration migration
-- Run this to verify the migration was applied correctly

USE tax_sale_compass;

-- Check if table exists and show structure
SELECT 'Checking scraper_config table structure...' as status;
DESCRIBE scraper_config;

-- Show current configurations
SELECT 'Current scraper configurations:' as status;
SELECT 
    municipality,
    base_url,
    tax_sale_page_url,
    enabled,
    timeout_seconds,
    created_at
FROM scraper_config 
ORDER BY municipality;

-- Check JSON patterns (sample)
SELECT 'Sample PDF search patterns:' as status;
SELECT 
    municipality,
    JSON_EXTRACT(pdf_search_patterns, '$[0]') as first_pdf_pattern,
    JSON_EXTRACT(excel_search_patterns, '$[0]') as first_excel_pattern
FROM scraper_config 
ORDER BY municipality;

-- Count total configurations
SELECT 'Total configurations:' as status;
SELECT COUNT(*) as total_configs FROM scraper_config;

-- Check for enabled configurations
SELECT 'Enabled configurations:' as status;
SELECT COUNT(*) as enabled_configs FROM scraper_config WHERE enabled = 1;

-- Show last updated information
SELECT 'Last update information:' as status;
SELECT 
    municipality,
    last_successful_scrape,
    updated_at
FROM scraper_config 
ORDER BY updated_at DESC;

-- Verification summary
SELECT 'Migration verification complete!' as status;