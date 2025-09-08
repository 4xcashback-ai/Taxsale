"""
MySQL Database Configuration and Connection Management
"""
import os
import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, List
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
    
    def insert_property(self, property_data: Dict) -> bool:
        """
        Insert or update property (UPSERT operation to preserve manually corrected data)
        """
        try:
            assessment_number = property_data.get('assessment_number')
            if not assessment_number:
                logger.error("Cannot insert property without assessment_number")
                return False
            
            # Check if property already exists
            existing_property = self.get_property_by_assessment(assessment_number)
            
            if existing_property:
                # Property exists - do UPDATE (preserve manually corrected data)
                logger.info(f"Property {assessment_number} exists, updating with new data")
                
                # Only update fields that are not manually corrected or are genuinely new
                update_data = {}
                
                # Always update these administrative fields
                safe_to_update = ['municipality', 'status', 'updated_at', 'created_at']
                
                # Update empty or missing fields with new data
                for key, new_value in property_data.items():
                    if key == 'assessment_number':
                        continue  # Don't update the key field
                    
                    existing_value = existing_property.get(key)
                    
                    # Update if field is in safe list OR if existing value is empty/null
                    if (key in safe_to_update or 
                        existing_value is None or 
                        existing_value == '' or 
                        existing_value == 'Unknown Owner'):
                        
                        if new_value and str(new_value).strip() not in ['', 'nan', 'None', 'N/A']:
                            update_data[key] = new_value
                            logger.debug(f"Updating {key}: '{existing_value}' -> '{new_value}'")
                
                # Special handling for mobile homes - preserve their coordinates
                if existing_property.get('property_type') == 'mobile_home_only':
                    existing_lat = existing_property.get('latitude')
                    existing_lng = existing_property.get('longitude')
                    
                    # Don't overwrite mobile home coordinates if they exist
                    if existing_lat and existing_lng and 'latitude' in update_data:
                        del update_data['latitude']
                        logger.info(f"Preserving mobile home coordinates for {assessment_number}")
                    if existing_lat and existing_lng and 'longitude' in update_data:
                        del update_data['longitude']
                
                if update_data:
                    return self.update_property(assessment_number, update_data)
                else:
                    logger.info(f"No updates needed for property {assessment_number}")
                    return True
            
            else:
                # Property doesn't exist - do INSERT
                logger.info(f"Inserting new property: {assessment_number}")
                
                # Build INSERT query dynamically
                columns = list(property_data.keys())
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join(columns)
                
                query = f"""
                    INSERT INTO properties ({column_names})
                    VALUES ({placeholders})
                """
                
                values = list(property_data.values())
                rows_affected = self.execute_update(query, tuple(values))
                
                if rows_affected > 0:
                    logger.info(f"Successfully inserted property: {assessment_number}")
                    return True
                else:
                    logger.error(f"Failed to insert property: {assessment_number}")
                    return False
                
        except Exception as e:
            logger.error(f"Error in insert_property for {property_data.get('assessment_number', 'unknown')}: {e}")
            return False
        
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
        """Get a specific property by assessment number"""
        try:
            query = "SELECT * FROM properties WHERE assessment_number = %s"
            result = self.execute_query(query, (assessment_number,))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting property by assessment {assessment_number}: {e}")
            return None

    def update_property(self, assessment_number: str, update_data: Dict) -> bool:
        """Update a specific property"""
        try:
            if not update_data:
                return False
                
            # Build the SET clause dynamically
            set_clauses = []
            values = []
            
            for key, value in update_data.items():
                if key != 'assessment_number':  # Don't update the key field
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            # Add the WHERE parameter
            values.append(assessment_number)
            
            query = f"""
                UPDATE properties 
                SET {', '.join(set_clauses)}
                WHERE assessment_number = %s
            """
            
            rows_affected = self.execute_update(query, tuple(values))
            
            logger.info(f"Updated property {assessment_number}, rows affected: {rows_affected}")
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error updating property {assessment_number}: {e}")
            return False

    def get_scraper_config(self, municipality: str) -> Optional[Dict]:
        """Get scraper configuration for a municipality"""
        try:
            query = "SELECT * FROM scraper_config WHERE municipality = %s AND enabled = 1"
            result = self.execute_query(query, (municipality,))
            if result:
                config = result[0]
                # Parse JSON fields
                if config.get('pdf_search_patterns'):
                    config['pdf_search_patterns'] = json.loads(config['pdf_search_patterns'])
                if config.get('excel_search_patterns'):
                    config['excel_search_patterns'] = json.loads(config['excel_search_patterns'])
                if config.get('additional_headers'):
                    config['additional_headers'] = json.loads(config['additional_headers'])
                return config
            return None
        except Exception as e:
            logger.error(f"Error getting scraper config for {municipality}: {e}")
            return None

    def get_all_scraper_configs(self) -> List[Dict]:
        """Get all scraper configurations"""
        try:
            query = "SELECT * FROM scraper_config ORDER BY municipality"
            results = self.execute_query(query)
            configs = []
            for config in results:
                # Parse JSON fields
                if config.get('pdf_search_patterns'):
                    config['pdf_search_patterns'] = json.loads(config['pdf_search_patterns'])
                if config.get('excel_search_patterns'):
                    config['excel_search_patterns'] = json.loads(config['excel_search_patterns'])
                if config.get('additional_headers'):
                    config['additional_headers'] = json.loads(config['additional_headers'])
                configs.append(config)
            return configs
        except Exception as e:
            logger.error(f"Error getting all scraper configs: {e}")
            return []

    def update_scraper_config(self, municipality: str, config_data: Dict) -> bool:
        """Update scraper configuration"""
        try:
            # Handle JSON fields
            if 'pdf_search_patterns' in config_data and isinstance(config_data['pdf_search_patterns'], list):
                config_data['pdf_search_patterns'] = json.dumps(config_data['pdf_search_patterns'])
            if 'excel_search_patterns' in config_data and isinstance(config_data['excel_search_patterns'], list):
                config_data['excel_search_patterns'] = json.dumps(config_data['excel_search_patterns'])
            if 'additional_headers' in config_data and isinstance(config_data['additional_headers'], dict):
                config_data['additional_headers'] = json.dumps(config_data['additional_headers'])
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            for key, value in config_data.items():
                if key != 'municipality':
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = NOW()")
            values.append(municipality)
            
            query = f"""
                UPDATE scraper_config 
                SET {', '.join(set_clauses)}
                WHERE municipality = %s
            """
            
            rows_affected = self.execute_update(query, tuple(values))
            logger.info(f"Updated scraper config for {municipality}, rows affected: {rows_affected}")
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error updating scraper config for {municipality}: {e}")
            return False

    def update_scraper_last_run(self, municipality: str, success: bool = True) -> bool:
        """Update last successful scrape timestamp"""
        try:
            query = """
                UPDATE scraper_config 
                SET last_successful_scrape = NOW()
                WHERE municipality = %s
            """
            rows_affected = self.execute_update(query, (municipality,))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating scraper last run for {municipality}: {e}")
            return False

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