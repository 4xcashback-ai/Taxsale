#!/usr/bin/env python3
"""
Migration script: MongoDB -> MySQL
Migrates all tax sale property data from MongoDB to MySQL
"""

import os
import json
import mysql.connector
from pymongo import MongoClient
from datetime import datetime

# Database connections
def get_mongo_connection():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/tax_sales')
    client = MongoClient(mongo_url)
    return client.tax_sales

def get_mysql_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='tax_sale_compass'
    )

def migrate_properties():
    """Migrate properties from MongoDB to MySQL"""
    print("Starting property migration...")
    
    # Get connections
    mongo_db = get_mongo_connection()
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    # Get all properties from MongoDB
    properties = list(mongo_db.tax_sales.find())
    print(f"Found {len(properties)} properties in MongoDB")
    
    # Prepare MySQL insert statement
    insert_query = """
        INSERT INTO properties (
            assessment_number, civic_address, property_type, tax_year, 
            total_taxes, status, municipality, province, 
            latitude, longitude, boundary_data, 
            pvsc_assessment_value, pvsc_assessment_year,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            civic_address = VALUES(civic_address),
            property_type = VALUES(property_type),
            tax_year = VALUES(tax_year),
            total_taxes = VALUES(total_taxes),
            status = VALUES(status),
            municipality = VALUES(municipality),
            latitude = VALUES(latitude),
            longitude = VALUES(longitude),
            boundary_data = VALUES(boundary_data),
            pvsc_assessment_value = VALUES(pvsc_assessment_value),
            pvsc_assessment_year = VALUES(pvsc_assessment_year),
            updated_at = VALUES(updated_at)
    """
    
    migrated_count = 0
    error_count = 0
    
    for prop in properties:
        try:
            # Extract and clean data
            assessment_number = prop.get('assessment_number', '')
            civic_address = prop.get('civic_address')
            property_type = prop.get('property_type')
            tax_year = prop.get('tax_year')
            total_taxes = float(prop.get('total_taxes', 0)) if prop.get('total_taxes') else None
            status = prop.get('status', 'active')
            municipality = prop.get('municipality', '')
            province = prop.get('province', 'Nova Scotia')
            
            # Location data
            latitude = float(prop.get('latitude')) if prop.get('latitude') else None
            longitude = float(prop.get('longitude')) if prop.get('longitude') else None
            
            # Boundary data (convert to JSON string)
            boundary_data = None
            if prop.get('boundary'):
                boundary_data = json.dumps(prop['boundary'])
            
            # PVSC data
            pvsc_assessment_value = float(prop.get('pvsc_assessment_value')) if prop.get('pvsc_assessment_value') else None
            pvsc_assessment_year = prop.get('pvsc_assessment_year')
            
            # Timestamps
            created_at = prop.get('created_at', datetime.now())
            updated_at = prop.get('updated_at', datetime.now())
            
            # Insert into MySQL
            mysql_cursor.execute(insert_query, (
                assessment_number, civic_address, property_type, tax_year,
                total_taxes, status, municipality, province,
                latitude, longitude, boundary_data,
                pvsc_assessment_value, pvsc_assessment_year,
                created_at, updated_at
            ))
            
            migrated_count += 1
            
            if migrated_count % 100 == 0:
                print(f"Migrated {migrated_count} properties...")
                mysql_conn.commit()
            
        except Exception as e:
            error_count += 1
            print(f"Error migrating property {prop.get('assessment_number', 'unknown')}: {e}")
    
    # Final commit
    mysql_conn.commit()
    
    print(f"Migration complete!")
    print(f"Successfully migrated: {migrated_count}")
    print(f"Errors: {error_count}")
    
    mysql_cursor.close()
    mysql_conn.close()

def migrate_users():
    """Migrate users from MongoDB to MySQL (if any exist)"""
    print("Starting user migration...")
    
    mongo_db = get_mongo_connection()
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    # Check if users collection exists
    if 'users' not in mongo_db.list_collection_names():
        print("No users collection found in MongoDB, skipping user migration")
        return
    
    users = list(mongo_db.users.find())
    print(f"Found {users} users in MongoDB")
    
    insert_query = """
        INSERT INTO users (email, password, subscription_tier, is_admin, created_at)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            subscription_tier = VALUES(subscription_tier),
            is_admin = VALUES(is_admin)
    """
    
    for user in users:
        try:
            email = user.get('email', user.get('username', ''))
            password = user.get('password', '')
            subscription_tier = user.get('subscription_tier', 'free')
            is_admin = user.get('is_admin', False)
            created_at = user.get('created_at', datetime.now())
            
            mysql_cursor.execute(insert_query, (
                email, password, subscription_tier, is_admin, created_at
            ))
            
        except Exception as e:
            print(f"Error migrating user {user.get('email', 'unknown')}: {e}")
    
    mysql_conn.commit()
    mysql_cursor.close()
    mysql_conn.close()
    
    print("User migration complete!")

if __name__ == "__main__":
    print("=== MongoDB to MySQL Migration ===")
    
    # Create MySQL database if it doesn't exist
    print("Setting up MySQL database...")
    os.system("mysql -u root < /app/database/mysql_schema.sql")
    
    # Run migrations
    migrate_properties()
    migrate_users()
    
    print("=== Migration Complete! ===")
    print("PHP frontend can now use MySQL database")