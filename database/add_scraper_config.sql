-- Scraper Configuration Table
-- Stores configurable parameters for each municipality scraper

CREATE TABLE IF NOT EXISTS scraper_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipality VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    tax_sale_page_url VARCHAR(500) NOT NULL,
    pdf_search_patterns JSON,
    excel_search_patterns JSON,
    enabled BOOLEAN DEFAULT TRUE,
    last_successful_scrape TIMESTAMP NULL,
    scrape_interval_hours INT DEFAULT 24,
    max_retries INT DEFAULT 3,
    timeout_seconds INT DEFAULT 30,
    user_agent VARCHAR(500) DEFAULT 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    additional_headers JSON,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_municipality (municipality),
    INDEX idx_enabled (enabled)
);

-- Insert default configurations for existing scrapers
INSERT INTO scraper_config (
    municipality, 
    base_url, 
    tax_sale_page_url, 
    pdf_search_patterns,
    excel_search_patterns,
    notes
) VALUES 
(
    'Halifax Regional Municipality',
    'https://www.halifax.ca',
    'https://www.halifax.ca/home-property/property-taxes/tax-sales',
    JSON_ARRAY('TaxSale.*\\.pdf', 'tax-sale.*\\.pdf', 'Tax Sale.*\\.pdf'),
    JSON_ARRAY('TaxSale.*\\.xlsx', 'tax-sale.*\\.xlsx', 'Tax Sale.*\\.xlsx'),
    'Halifax tax sale page - look for PDF and Excel files'
),
(
    'Victoria County',
    'https://www.countyofvictoria.ca',
    'https://www.countyofvictoria.ca/departments/finance/tax-sale/',
    JSON_ARRAY('.*tax.*sale.*\\.pdf', '.*sale.*\\.pdf'),
    JSON_ARRAY('.*tax.*sale.*\\.xlsx', '.*sale.*\\.xlsx'),
    'Victoria County tax sale page'
),
(
    'Cumberland County', 
    'https://www.cumberlandcounty.ns.ca',
    'https://www.cumberlandcounty.ns.ca/departments/finance-administration/tax-sale/',
    JSON_ARRAY('.*tax.*sale.*\\.pdf', '.*sale.*\\.pdf'),
    JSON_ARRAY('.*tax.*sale.*\\.xlsx', '.*sale.*\\.xlsx'),
    'Cumberland County tax sale page'
);