-- Add 'inactive' status to properties table
USE tax_sale_compass;

-- Update the ENUM to include 'inactive' status
ALTER TABLE properties MODIFY COLUMN status ENUM('active', 'inactive', 'sold', 'withdrawn') DEFAULT 'active';

-- Add index for better performance if not exists
-- (This is safe to run even if index exists)
CREATE INDEX IF NOT EXISTS idx_status_updated ON properties(status);