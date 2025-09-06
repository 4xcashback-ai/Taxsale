-- Tax Sale Compass MySQL Database Schema
CREATE DATABASE IF NOT EXISTS tax_sale_compass;
USE tax_sale_compass;

-- Properties table (main data)
CREATE TABLE properties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_number VARCHAR(20) NOT NULL UNIQUE,
    owner_name VARCHAR(255),
    civic_address VARCHAR(255),
    parcel_description TEXT,
    pid_number VARCHAR(20),
    opening_bid DECIMAL(10,2),
    total_taxes DECIMAL(10,2),
    hst_applicable BOOLEAN DEFAULT FALSE,
    redeemable BOOLEAN DEFAULT TRUE,
    property_type VARCHAR(100),
    tax_year INT,
    status ENUM('active', 'sold', 'withdrawn') DEFAULT 'active',
    municipality VARCHAR(100),
    province VARCHAR(50) DEFAULT 'Nova Scotia',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    boundary_data JSON,
    pvsc_assessment_value DECIMAL(12,2),
    pvsc_assessment_year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_assessment (assessment_number),
    INDEX idx_owner (owner_name),
    INDEX idx_pid (pid_number),
    INDEX idx_municipality (municipality),
    INDEX idx_status (status),
    INDEX idx_tax_year (tax_year),
    INDEX idx_location (latitude, longitude)
);

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    subscription_tier ENUM('free', 'paid') DEFAULT 'free',
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_subscription (subscription_tier)
);

-- User favorites
CREATE TABLE user_favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    property_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    UNIQUE KEY unique_favorite (user_id, property_id)
);

-- Admin user (password: TaxSale2025!SecureAdmin)
INSERT INTO users (email, password, subscription_tier, is_admin) 
VALUES ('admin', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'paid', TRUE);