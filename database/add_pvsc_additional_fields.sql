-- Add additional PVSC fields for basement, garage, and other property details

ALTER TABLE pvsc_data 
ADD COLUMN garage VARCHAR(50) NULL AFTER basement_type,
ADD COLUMN construction_quality VARCHAR(50) NULL AFTER construction_type,
ADD COLUMN under_construction VARCHAR(10) NULL AFTER construction_quality,
ADD COLUMN living_units INT NULL AFTER occupancy_type,
ADD COLUMN building_style VARCHAR(100) NULL AFTER building_type;

-- Add indexes for the new fields
ALTER TABLE pvsc_data 
ADD INDEX idx_garage (garage),
ADD INDEX idx_construction_quality (construction_quality);