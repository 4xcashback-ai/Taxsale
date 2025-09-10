-- Add PVSC (Property Valuation Services Corporation) data table
-- This table will store detailed property data scraped from PVSC API

CREATE TABLE IF NOT EXISTS pvsc_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_number VARCHAR(20) NOT NULL,
    ain VARCHAR(20) NULL, -- Assessment Identification Number
    
    -- Property Identification
    civic_address TEXT NULL,
    legal_description TEXT NULL,
    pid_number VARCHAR(20) NULL,
    
    -- Location Data
    latitude DECIMAL(10, 8) NULL,
    longitude DECIMAL(11, 8) NULL,
    municipal_unit VARCHAR(100) NULL,
    planning_district VARCHAR(100) NULL,
    
    -- Assessment Information
    assessed_value DECIMAL(12, 2) NULL,
    taxable_assessed_value DECIMAL(12, 2) NULL,
    capped_assessment_value DECIMAL(12, 2) NULL,
    assessment_year INT NULL,
    
    -- Property Characteristics
    property_type VARCHAR(50) NULL,
    property_use VARCHAR(100) NULL,
    land_size DECIMAL(12, 2) NULL,
    land_size_unit VARCHAR(20) NULL,
    building_size DECIMAL(12, 2) NULL,
    building_size_unit VARCHAR(20) NULL,
    
    -- Residential Dwelling Characteristics
    dwelling_type VARCHAR(50) NULL,
    year_built INT NULL,
    number_of_bedrooms INT NULL,
    number_of_bathrooms DECIMAL(3, 1) NULL,
    basement_type VARCHAR(50) NULL,
    heating_type VARCHAR(50) NULL,
    exterior_finish VARCHAR(100) NULL,
    roof_type VARCHAR(50) NULL,
    
    -- Commercial Building Characteristics
    building_class VARCHAR(50) NULL,
    building_type VARCHAR(100) NULL,
    construction_type VARCHAR(50) NULL,
    occupancy_type VARCHAR(100) NULL,
    
    -- Sales History
    last_sale_date DATE NULL,
    last_sale_price DECIMAL(12, 2) NULL,
    previous_sale_date DATE NULL,
    previous_sale_price DECIMAL(12, 2) NULL,
    
    -- Additional Data
    neighborhood_code VARCHAR(20) NULL,
    zoning VARCHAR(50) NULL,
    school_district VARCHAR(100) NULL,
    
    -- System Fields
    data_source VARCHAR(50) DEFAULT 'PVSC_API',
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    raw_json JSON NULL, -- Store raw API response for debugging
    
    -- Indexes
    UNIQUE KEY unique_assessment (assessment_number),
    INDEX idx_ain (ain),
    INDEX idx_pid (pid_number),
    INDEX idx_location (latitude, longitude),
    INDEX idx_scraped_at (scraped_at)
);

-- Add foreign key constraint to link with properties table
ALTER TABLE pvsc_data 
ADD CONSTRAINT fk_pvsc_properties 
FOREIGN KEY (assessment_number) 
REFERENCES properties(assessment_number) 
ON DELETE CASCADE ON UPDATE CASCADE;