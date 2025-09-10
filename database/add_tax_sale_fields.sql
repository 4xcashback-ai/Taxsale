-- Migration to add complete tax sale fields to existing properties table
-- Run this on your VPS to add the new fields

USE tax_sale_compass;

-- Add new fields for complete tax sale data
ALTER TABLE properties 
ADD COLUMN owner_name VARCHAR(255) AFTER assessment_number,
ADD COLUMN parcel_description TEXT AFTER civic_address,
ADD COLUMN pid_number VARCHAR(20) AFTER parcel_description,
ADD COLUMN opening_bid DECIMAL(10,2) AFTER pid_number,
ADD COLUMN hst_applicable BOOLEAN DEFAULT FALSE AFTER total_taxes,
ADD COLUMN redeemable BOOLEAN DEFAULT TRUE AFTER hst_applicable,
ADD COLUMN property_type VARCHAR(100) AFTER redeemable;

-- Add indexes for the new fields
CREATE INDEX idx_owner ON properties(owner_name);
CREATE INDEX idx_pid ON properties(pid_number);
CREATE INDEX idx_property_type ON properties(property_type);

-- Show the updated table structure
DESCRIBE properties;