"""
MySQL Database Configuration and Connection Management
"""
import os
import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, List
import json
from datetime import datetime

class MySQLManager:
    def __init__(self):
        self.connection_config = {
            'host': 'localhost',
            'database': 'tax_sale_compass',
            'user': 'taxsale',
            'password': 'SecureTaxSale2025!',
            'auth_plugin': 'mysql_native_password'
        }
        
    def get_connection(self):
        """Create and return a MySQL connection"""
        try:
            connection = mysql.connector.connect(**self.connection_config)
            return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SELECT query and return results as list of dictionaries"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            result = cursor.fetchall()
            return result
            
        except Error as e:
            print(f"Error executing query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            connection.commit()
            return cursor.rowcount
            
        except Error as e:
            print(f"Error executing update: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
    
    def insert_property(self, property_data: Dict) -> int:
        """Insert or update a property record"""
        query = """
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
        
        # Convert boundary data to JSON string if it exists
        boundary_json = None
        if property_data.get('boundary'):
            boundary_json = json.dumps(property_data['boundary'])
        
        params = (
            property_data.get('assessment_number'),
            property_data.get('civic_address'),
            property_data.get('property_type'),
            property_data.get('tax_year'),
            property_data.get('total_taxes'),
            property_data.get('status', 'active'),
            property_data.get('municipality'),
            property_data.get('province', 'Nova Scotia'),
            property_data.get('latitude'),
            property_data.get('longitude'),
            boundary_json,
            property_data.get('pvsc_assessment_value'),
            property_data.get('pvsc_assessment_year'),
            datetime.now(),
            datetime.now()
        )
        
        return self.execute_update(query, params)
        
    def get_properties(self, filters: Dict = None, limit: int = 24, offset: int = 0) -> List[Dict]:
        """Get properties with optional filters"""
        query = "SELECT * FROM properties WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('municipality'):
                query += " AND municipality = %s"
                params.append(filters['municipality'])
                
            if filters.get('status'):
                query += " AND status = %s"
                params.append(filters['status'])
                
            if filters.get('search'):
                query += " AND (assessment_number LIKE %s OR civic_address LIKE %s)"
                search_term = f"%{filters['search']}%"
                params.append(search_term)
                params.append(search_term)
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.execute_query(query, tuple(params))
    
    def get_property_by_assessment(self, assessment_number: str) -> Optional[Dict]:
        """Get a single property by assessment number"""
        query = "SELECT * FROM properties WHERE assessment_number = %s"
        result = self.execute_query(query, (assessment_number,))
        return result[0] if result else None
    
    def get_municipalities(self) -> List[str]:
        """Get list of all municipalities"""
        query = "SELECT DISTINCT municipality FROM properties ORDER BY municipality"
        result = self.execute_query(query)
        return [row['municipality'] for row in result]
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = %s"
        result = self.execute_query(query, (email,))
        return result[0] if result else None
    
    def create_user(self, email: str, password_hash: str, subscription_tier: str = 'free') -> int:
        """Create a new user"""
        query = """
            INSERT INTO users (email, password, subscription_tier, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (email, password_hash, subscription_tier, datetime.now(), datetime.now())
        return self.execute_update(query, params)

# Global instance
mysql_db = MySQLManager()