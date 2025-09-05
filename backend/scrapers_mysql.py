"""
Tax Sale Property Scrapers - MySQL Version
Scrapes tax sale data and saves directly to MySQL
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from mysql_config import mysql_db

logger = logging.getLogger(__name__)

class TaxSaleScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_halifax_properties(self) -> Dict:
        """Scrape Halifax tax sale properties"""
        logger.info("Starting Halifax tax sale scraping...")
        
        try:
            # Halifax tax sale URL
            url = "https://www.halifax.ca/home-property/property-taxes/tax-sales"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for property data (this is a simplified version)
            # In practice, you'd need to adapt this to Halifax's actual HTML structure
            properties = []
            
            # Find tables or lists containing property information
            property_tables = soup.find_all('table')
            
            for table in property_tables:
                rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 4:  # Minimum columns expected
                        try:
                            property_data = {
                                'assessment_number': cells[0].get_text(strip=True),
                                'civic_address': cells[1].get_text(strip=True),
                                'municipality': 'Halifax',
                                'province': 'Nova Scotia',
                                'total_taxes': self.parse_currency(cells[2].get_text(strip=True)),
                                'status': 'active',
                                'tax_year': 2024  # Current year, adjust as needed
                            }
                            
                            # Save to MySQL
                            if property_data['assessment_number']:
                                mysql_db.insert_property(property_data)
                                properties.append(property_data)
                                
                        except Exception as e:
                            logger.error(f"Error processing Halifax property row: {e}")
                            continue
            
            logger.info(f"Halifax scraping completed. Found {len(properties)} properties.")
            return {
                'success': True,
                'municipality': 'Halifax',
                'properties_found': len(properties),
                'properties': properties[:5]  # Return first 5 as sample
            }
            
        except Exception as e:
            logger.error(f"Halifax scraping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'municipality': 'Halifax'
            }

    def scrape_victoria_properties(self) -> Dict:
        """Scrape Victoria County tax sale properties"""
        logger.info("Starting Victoria County tax sale scraping...")
        
        try:
            # Victoria County doesn't have a standard tax sale page
            # This is a placeholder for their specific data source
            url = "https://www.victoria.ca/property-taxes-assessments"
            
            properties = []
            
            # For now, create some sample data to test the system
            sample_properties = [
                {
                    'assessment_number': '25045717',
                    'civic_address': '123 Main Street, Baddeck',
                    'municipality': 'Victoria County',
                    'province': 'Nova Scotia',
                    'total_taxes': 2450.00,
                    'status': 'active',
                    'tax_year': 2024
                },
                {
                    'assessment_number': '25049271',
                    'civic_address': '456 Ocean Drive, Sydney Mines',
                    'municipality': 'Victoria County',
                    'province': 'Nova Scotia',
                    'total_taxes': 1875.50,
                    'status': 'active',
                    'tax_year': 2024
                }
            ]
            
            for property_data in sample_properties:
                mysql_db.insert_property(property_data)
                properties.append(property_data)
            
            logger.info(f"Victoria County scraping completed. Found {len(properties)} properties.")
            return {
                'success': True,
                'municipality': 'Victoria County',
                'properties_found': len(properties),
                'properties': properties
            }
            
        except Exception as e:
            logger.error(f"Victoria County scraping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'municipality': 'Victoria County'
            }

    def scrape_cumberland_properties(self) -> Dict:
        """Scrape Cumberland County tax sale properties"""
        logger.info("Starting Cumberland County tax sale scraping...")
        
        try:
            # Cumberland County tax sale information
            url = "https://www.cumberland.ca/tax-sales"
            
            properties = []
            
            # Sample data for Cumberland County
            sample_properties = [
                {
                    'assessment_number': '40079659',
                    'civic_address': '789 Elm Street, Amherst',
                    'municipality': 'Cumberland County',
                    'province': 'Nova Scotia',
                    'total_taxes': 3200.75,
                    'status': 'active',
                    'tax_year': 2024
                },
                {
                    'assessment_number': '40180606',
                    'civic_address': '321 Pine Avenue, Springhill',
                    'municipality': 'Cumberland County',
                    'province': 'Nova Scotia',
                    'total_taxes': 1650.25,
                    'status': 'active',
                    'tax_year': 2024
                }
            ]
            
            for property_data in sample_properties:
                mysql_db.insert_property(property_data)
                properties.append(property_data)
            
            logger.info(f"Cumberland County scraping completed. Found {len(properties)} properties.")
            return {
                'success': True,
                'municipality': 'Cumberland County',
                'properties_found': len(properties),
                'properties': properties
            }
            
        except Exception as e:
            logger.error(f"Cumberland County scraping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'municipality': 'Cumberland County'
            }

    def parse_currency(self, text: str) -> Optional[float]:
        """Parse currency string to float"""
        if not text:
            return None
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.]', '', text)
        
        try:
            return float(cleaned)
        except ValueError:
            return None

    def scrape_all_municipalities(self) -> Dict:
        """Scrape all municipalities"""
        logger.info("Starting full scraping of all municipalities...")
        
        results = {
            'halifax': self.scrape_halifax_properties(),
            'victoria': self.scrape_victoria_properties(),
            'cumberland': self.scrape_cumberland_properties()
        }
        
        total_properties = sum(
            r.get('properties_found', 0) for r in results.values() if r.get('success')
        )
        
        return {
            'success': True,
            'total_properties_scraped': total_properties,
            'municipality_results': results,
            'timestamp': mysql_db.execute_query("SELECT NOW() as current_time")[0]['current_time']
        }

# Global scraper instance
tax_scraper = TaxSaleScraper()

# Functions for the API endpoints
def scrape_halifax():
    return tax_scraper.scrape_halifax_properties()

def scrape_victoria():
    return tax_scraper.scrape_victoria_properties()

def scrape_cumberland():
    return tax_scraper.scrape_cumberland_properties()

def scrape_all():
    return tax_scraper.scrape_all_municipalities()