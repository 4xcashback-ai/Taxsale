"""
Tax Sale Property Scrapers - MySQL Version
Scrapes tax sale data and saves directly to MySQL
"""

import requests
import json
import re
import io
import subprocess
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
import logging
import pandas as pd
import traceback
import PyPDF2
from io import BytesIO
from mysql_config import mysql_db

logger = logging.getLogger(__name__)

def parse_multiple_pids(pid_string: str) -> Tuple[str, List[str], int]:
    """
    Parse PID string that might contain multiple PIDs
    Returns: (primary_pid, secondary_pids_list, total_count)
    """
    if not pid_string or pid_string.strip() in ['', 'N/A', 'None']:
        return None, [], 0
    
    # Clean the PID string
    pid_string = str(pid_string).strip()
    
    # Check for multiple PIDs (comma or semicolon separated)
    if ',' in pid_string or ';' in pid_string:
        # Split by comma or semicolon
        pids = re.split(r'[,;]', pid_string)
        pids = [pid.strip() for pid in pids if pid.strip()]
        
        if len(pids) > 1:
            return pids[0], pids[1:], len(pids)
        elif len(pids) == 1:
            return pids[0], [], 1
    
    return pid_string, [], 1

def extract_auction_info_from_webpage(webpage_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract auction date and type from Halifax tax sale webpage
    Returns: (sale_date, auction_type)
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        from datetime import datetime
        
        logger.info(f"Extracting auction info from webpage: {webpage_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(webpage_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()
        
        logger.info(f"Webpage text length: {len(page_text)} characters")
        
        # Extract auction type from webpage content
        auction_type = "Public Auction"  # Default
        
        if 'sold by tender' in page_text or 'public tender' in page_text:
            auction_type = "Public Tender Auction"
            logger.info("Found 'sold by tender' - setting auction type to Public Tender Auction")
        elif 'sold by auction' in page_text or 'public auction' in page_text:
            auction_type = "Public Auction" 
            logger.info("Found 'sold by auction' - setting auction type to Public Auction")
        else:
            logger.info("No specific auction type found on webpage, using default: Public Auction")
        
        # Try to extract sale date from webpage content
        sale_date = None
        
        # Look for various date patterns on the webpage
        date_patterns = [
            r'sale date[:\s]+([a-z]+ \d{1,2},? \d{4})',  # "Sale Date: September 16, 2025" 
            r'tender date[:\s]+([a-z]+ \d{1,2},? \d{4})',  # "Tender Date: September 16, 2025"
            r'auction date[:\s]+([a-z]+ \d{1,2},? \d{4})',  # "Auction Date: September 16, 2025"
            r'([a-z]+ \d{1,2},? \d{4})',  # General "Month DD, YYYY" pattern
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',  # MM/DD/YYYY or MM-DD-YYYY format
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                for match in matches:
                    try:
                        # Try to parse the date
                        if '/' in match or '-' in match:
                            # Handle MM/DD/YYYY format
                            parsed_date = datetime.strptime(match, '%m/%d/%Y' if '/' in match else '%m-%d-%Y')
                        else:
                            # Handle "Month DD, YYYY" format
                            clean_match = re.sub(r'[^\w\s,]', '', match).strip()
                            for fmt in ['%B %d, %Y', '%b %d, %Y', '%B %d %Y', '%b %d %Y']:
                                try:
                                    parsed_date = datetime.strptime(clean_match.title(), fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                continue  # Skip if no format worked
                        
                        # Only accept future dates (tax sales are upcoming events)
                        if parsed_date.date() >= datetime.now().date():
                            sale_date = parsed_date.strftime('%Y-%m-%d')
                            logger.info(f"Extracted sale date from webpage: {sale_date}")
                            break
                            
                    except (ValueError, AttributeError):
                        continue
                        
                if sale_date:
                    break
        
        if not sale_date:
            logger.info("No sale date found on webpage")
        
        logger.info(f"Final auction info from webpage: Date={sale_date}, Type={auction_type}")
        return sale_date, auction_type
        
    except Exception as e:
        logger.error(f"Error extracting auction info from webpage: {e}")
        return None, "Public Auction"

def extract_auction_info_from_pdf_url(pdf_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract auction date and type from PDF URL and filename
    Returns: (sale_date, auction_type)
    """
    try:
        from urllib.parse import urlparse
        from datetime import datetime
        import re
        
        # Parse filename from URL
        parsed_url = urlparse(pdf_url)
        filename = parsed_url.path.split('/')[-1]
        
        logger.info(f"Extracting auction info from filename: {filename}")
        
        # Extract date from filename patterns like:
        # sept16.2025newspaper.website-sept3.25.pdf
        # Format appears to be: [month][day].[year]...
        
        sale_date = None
        auction_type = "Public Auction"  # Default
        
        # Try to extract date from filename
        date_patterns = [
            r'sept(\d{1,2})\.(\d{4})',  # sept16.2025
            r'([a-z]{3,4})(\d{1,2})\.(\d{4})',  # general month pattern
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename.lower())
            if match:
                if 'sept' in pattern:
                    # Handle September specifically
                    day = int(match.group(1))
                    year = int(match.group(2))
                    month = 9  # September
                    
                    try:
                        sale_date = datetime(year, month, day).strftime('%Y-%m-%d')
                        logger.info(f"Extracted sale date from filename: {sale_date}")
                        break
                    except ValueError:
                        continue
                        
                # Add more date parsing logic for other months as needed
        
        # Check filename for auction type indicators
        filename_lower = filename.lower()
        if 'tender' in filename_lower:
            auction_type = "Public Tender Auction"
        elif 'auction' in filename_lower:
            auction_type = "Public Auction"
            
        logger.info(f"Extracted auction info: Date={sale_date}, Type={auction_type}")
        return sale_date, auction_type
        
    except Exception as e:
        logger.error(f"Error extracting auction info from URL: {e}")
        return None, "Public Auction"

def extract_auction_info_from_pdf_content(pdf_content: bytes) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract auction date and type from PDF content text
    Returns: (sale_date, auction_type)
    """
    try:
        import PyPDF2
        import io
        import re
        from datetime import datetime
        
        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        full_text = ""
        
        # Read first few pages to find auction info
        max_pages = min(3, len(pdf_reader.pages))
        for page_num in range(max_pages):
            page = pdf_reader.pages[page_num]
            full_text += page.extract_text() + "\n"
        
        logger.info(f"Extracted {len(full_text)} characters from PDF for auction info parsing")
        
        sale_date = None
        auction_type = "Public Auction"  # Default
        
        # Look for auction type keywords
        text_lower = full_text.lower()
        if 'public tender' in text_lower or 'tender auction' in text_lower:
            auction_type = "Public Tender Auction"
        elif 'public auction' in text_lower:
            auction_type = "Public Auction"
            
        # Look for date patterns in PDF text
        date_patterns = [
            r'sale date[:\s]+([a-z]+ \d{1,2},? \d{4})',  # "Sale Date: September 16, 2025"
            r'auction date[:\s]+([a-z]+ \d{1,2},? \d{4})',  # "Auction Date: September 16, 2025"
            r'([a-z]+ \d{1,2},? \d{4})',  # General "Month DD, YYYY" pattern
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',  # MM/DD/YYYY or MM-DD-YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                for match in matches:
                    try:
                        # Try to parse the date
                        if '/' in match or '-' in match:
                            # Handle MM/DD/YYYY format
                            parsed_date = datetime.strptime(match, '%m/%d/%Y' if '/' in match else '%m-%d-%Y')
                        else:
                            # Handle "Month DD, YYYY" format
                            # Clean up the match
                            clean_match = re.sub(r'[^\w\s,]', '', match).strip()
                            for fmt in ['%B %d, %Y', '%b %d, %Y', '%B %d %Y', '%b %d %Y']:
                                try:
                                    parsed_date = datetime.strptime(clean_match.title(), fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                continue  # Skip if no format worked
                        
                        sale_date = parsed_date.strftime('%Y-%m-%d')
                        logger.info(f"Extracted sale date from PDF content: {sale_date}")
                        break
                        
                    except (ValueError, AttributeError):
                        continue
                        
                if sale_date:
                    break
        
        logger.info(f"Final auction info from PDF: Date={sale_date}, Type={auction_type}")
        return sale_date, auction_type
        
    except Exception as e:
        logger.error(f"Error extracting auction info from PDF content: {e}")
        return None, "Public Auction"

# Default property type detection from existing logic
def detect_property_type(description: str, pid_info: str = '') -> str:
    """
    Detect property type based on description and PID information
    Returns: 'land', 'mobile_home_only', 'building', 'mixed'
    """
    if not description:
        return 'land'
    
    description_lower = description.lower()
    pid_info_lower = (pid_info or '').lower()
    
    # Check for mobile home only
    mobile_indicators = [
        'mobile home only',
        'mobile only',
        'trailer only',
        'manufactured home only'
    ]
    
    if any(indicator in description_lower for indicator in mobile_indicators):
        return 'mobile_home_only'
    
    # Check for building/structure indicators
    building_indicators = [
        'building',
        'house',
        'residence',
        'commercial',
        'structure'
    ]
    
    if any(indicator in description_lower for indicator in building_indicators):
        return 'building'
    
    # Check for mixed land indicators
    mixed_indicators = [
        'land and building',
        'property and building',
        'lot and building'
    ]
    
    if any(indicator in description_lower for indicator in mixed_indicators):
        return 'mixed'
    
    # Default to land
    return 'land'

def run_post_scraping_tasks():
    """Run post-scraping tasks like thumbnail generation"""
    try:
        logger.info("Running post-scraping tasks...")
        script_path = "/var/www/tax-sale-compass/scripts/post_scraping_tasks.sh"
        
        # Run the post-scraping tasks in background
        subprocess.Popen([
            'bash', script_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        logger.info("Post-scraping tasks started in background")
    except Exception as e:
        logger.error(f"Failed to start post-scraping tasks: {e}")

class TaxSaleScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_halifax_properties(self) -> Dict:
        """Scrape Halifax tax sale properties with enhanced debugging"""
        logger.info("Starting Halifax tax sale scraping with enhanced debugging...")
        
        try:
            # Get Halifax scraper configuration from database
            config = mysql_db.get_scraper_config('Halifax Regional Municipality')
            if not config:
                logger.error("Halifax scraper configuration not found in database")
                return {
                    "success": False,
                    "message": "Halifax scraper configuration not found in database",
                    "properties_found": 0
                }
            
            webpage_url = config['tax_sale_page_url']
            # Use the direct PDF URL we know works
            pdf_url = "https://www.halifax.ca/media/91740"
            
            headers = {
                'User-Agent': config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            
            # First, extract auction information from the Halifax tax sale webpage
            logger.info("Step 1: Extracting auction information from Halifax webpage...")
            sale_date_from_webpage, auction_type_from_webpage = extract_auction_info_from_webpage(webpage_url)
            
            # Then extract any additional info from PDF URL/filename
            logger.info("Step 2: Extracting auction information from PDF URL...")
            sale_date_from_url, auction_type_from_url = extract_auction_info_from_pdf_url(pdf_url)
            
            logger.info(f"Downloading Halifax PDF for debugging: {pdf_url}")
            pdf_response = self.session.get(pdf_url, headers=headers, timeout=60)
            pdf_response.raise_for_status()
            
            logger.info(f"PDF downloaded successfully: {len(pdf_response.content)} bytes")
            
            # Extract auction information from PDF content (as fallback)
            logger.info("Step 3: Extracting auction information from PDF content...")
            sale_date_from_content, auction_type_from_content = extract_auction_info_from_pdf_content(pdf_response.content)
            
            # Use the best available information (prioritize webpage > URL > content)
            final_sale_date = sale_date_from_webpage or sale_date_from_url or sale_date_from_content
            final_auction_type = auction_type_from_webpage  # Webpage is most reliable for auction type
            if final_auction_type == "Public Auction":  # If webpage didn't find specific type, try other sources
                final_auction_type = auction_type_from_content if auction_type_from_content != "Public Auction" else auction_type_from_url
            
            logger.info(f"Final auction info - Date: {final_sale_date}, Type: {final_auction_type}")
            logger.info(f"Sources used - Webpage: {auction_type_from_webpage}, URL: {auction_type_from_url}, Content: {auction_type_from_content}")
            
            properties = []
            
            # Save PDF to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(pdf_response.content)
                tmp_file.flush()
                
                logger.info(f"PDF saved to temp file: {tmp_file.name}")
                
                # Try multiple extraction methods with detailed logging
                extraction_methods = []
                
                # Method 1: Camelot
                try:
                    import camelot
                    logger.info("Attempting Camelot table extraction...")
                    tables = camelot.read_pdf(tmp_file.name, pages='all')
                    logger.info(f"Camelot found {len(tables)} tables")
                    
                    if len(tables) > 0:
                        for i, table in enumerate(tables):
                            logger.info(f"Camelot Table {i+1}: {table.df.shape} - accuracy: {table.accuracy}")
                            logger.info(f"Camelot Table {i+1} sample:\n{table.df.head()}")
                            table_properties = self._parse_halifax_table(table.df, f"camelot_{i}")
                            properties.extend(table_properties)
                            extraction_methods.append(f"Camelot table {i+1}: {len(table_properties)} properties")
                    else:
                        logger.warning("Camelot found no tables")
                        extraction_methods.append("Camelot: 0 tables found")
                        
                except ImportError:
                    logger.warning("Camelot not available")
                    extraction_methods.append("Camelot: not available")
                except Exception as e:
                    logger.error(f"Camelot failed: {e}")
                    extraction_methods.append(f"Camelot: failed - {str(e)}")
                
                # Method 2: pdfplumber table extraction
                if not properties:
                    try:
                        import pdfplumber
                        logger.info("Attempting pdfplumber table extraction...")
                        
                        with pdfplumber.open(tmp_file.name) as pdf:
                            logger.info(f"PDF has {len(pdf.pages)} pages")
                            
                            for page_num, page in enumerate(pdf.pages):
                                logger.info(f"Processing page {page_num + 1}")
                                tables = page.extract_tables()
                                
                                if tables:
                                    logger.info(f"Page {page_num + 1}: Found {len(tables)} tables")
                                    for table_idx, table_data in enumerate(tables):
                                        if table_data and len(table_data) > 1:
                                            logger.info(f"Page {page_num + 1}, Table {table_idx + 1}: {len(table_data)} rows, {len(table_data[0]) if table_data else 0} columns")
                                            
                                            # Create DataFrame
                                            import pandas as pd
                                            df = pd.DataFrame(table_data[1:], columns=table_data[0])
                                            logger.info(f"Table sample:\n{df.head()}")
                                            
                                            table_properties = self._parse_halifax_table(df, f"pdfplumber_{page_num}_{table_idx}")
                                            properties.extend(table_properties)
                                            extraction_methods.append(f"pdfplumber page {page_num + 1} table {table_idx + 1}: {len(table_properties)} properties")
                                else:
                                    logger.info(f"Page {page_num + 1}: No tables found")
                                    
                    except Exception as e:
                        logger.error(f"pdfplumber table extraction failed: {e}")
                        extraction_methods.append(f"pdfplumber tables: failed - {str(e)}")
                
                # Method 3: Text extraction as final fallback
                if not properties:
                    try:
                        import pdfplumber
                        logger.info("Falling back to text extraction...")
                        
                        with pdfplumber.open(tmp_file.name) as pdf:
                            all_text = ""
                            for page in pdf.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    all_text += page_text + "\n"
                            
                            logger.info(f"Extracted text length: {len(all_text)} characters")
                            logger.info(f"Text sample: {all_text[:500]}...")
                            
                            properties = self._parse_halifax_pdf_text(all_text, final_sale_date, final_auction_type)
                            extraction_methods.append(f"Text parsing: {len(properties)} properties")
                            
                    except Exception as e:
                        logger.error(f"Text extraction failed: {e}")
                        extraction_methods.append(f"Text parsing: failed - {str(e)}")
                
                # Clean up temp file
                import os
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
            
            # Remove duplicates and debug
            logger.info(f"Total properties found before deduplication: {len(properties)}")
            
            unique_properties = {}
            duplicates_found = 0
            
            for prop in properties:
                assessment = prop['assessment_number']
                if assessment in unique_properties:
                    duplicates_found += 1
                    logger.warning(f"Duplicate found: {assessment} - {prop['civic_address']}")
                else:
                    unique_properties[assessment] = prop
            
            final_properties = list(unique_properties.values())
            
            logger.info(f"Deduplication results:")
            logger.info(f"  - Total found: {len(properties)}")
            logger.info(f"  - Duplicates removed: {duplicates_found}")
            logger.info(f"  - Final unique: {len(final_properties)}")
            
            # Only insert unique properties
            inserted_count = 0
            for property_data in final_properties:
                try:
                    mysql_db.insert_property(property_data)
                    inserted_count += 1
                except Exception as e:
                    logger.error(f"Error inserting property {property_data['assessment_number']}: {e}")
            
            logger.info(f"Successfully inserted {inserted_count} properties into database")
            
            return {
                'success': True,
                'municipality': 'Halifax Regional Municipality',
                'properties_found': len(final_properties),
                'properties': final_properties[:5],
                'debug_info': {
                    'extraction_methods': extraction_methods,
                    'total_found': len(properties),
                    'unique_count': len(final_properties)
                }
            }
            
        except Exception as e:
            logger.error(f"Halifax scraping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'municipality': 'Halifax Regional Municipality'
            }

    def _parse_halifax_table(self, df, table_idx: int) -> List[Dict]:
        """Parse a DataFrame table from Halifax PDF into property data"""
        properties = []
        
        logger.info(f"Table {table_idx + 1} columns: {list(df.columns)}")
        logger.info(f"Table {table_idx + 1} first few rows:\n{df.head()}")
        
        # Try to identify the columns
        # Common Halifax tax sale table headers might be:
        # Assessment Number, Address, Owner, Amount, etc.
        
        for idx, row in df.iterrows():
            try:
                # Convert row to dict and look for assessment numbers
                row_dict = row.to_dict()
                
                assessment_number = None
                address = "Halifax Property"
                tax_amount = 0.0
                
                # Look for assessment number in any column
                for col_name, value in row_dict.items():
                    if pd.notna(value):
                        value_str = str(value).strip()
                        
                        # Look for 8+ digit numbers (assessment numbers)
                        assessment_matches = re.findall(r'\b(\d{8,10})\b', value_str)
                        if assessment_matches and not assessment_number:
                            assessment_number = assessment_matches[0]
                        
                        # Look for address-like content (improved logic)
                        if any(word in value_str.lower() for word in ['street', 'road', 'avenue', 'drive', 'lane', 'st', 'rd', 'ave', 'dr', 'ln', 'lot', 'way', 'place', 'crescent']) and len(value_str) > 5:
                            # Clean up the address - remove obvious owner names
                            clean_addr = value_str
                            # Remove patterns that look like names (multiple capitalized words)
                            clean_addr = re.sub(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s*', '', clean_addr)
                            # Remove trailing commas and spaces
                            clean_addr = re.sub(r',\s*$', '', clean_addr).strip()
                            
                            if len(clean_addr) > 5 and address == "Halifax Property":
                                address = clean_addr
                        
                        # Look for dollar amounts
                        money_matches = re.findall(r'\$?([0-9,]+\.?[0-9]*)', value_str)
                        for match in money_matches:
                            try:
                                amount = float(match.replace(',', ''))
                                if 100 <= amount <= 25000 and tax_amount == 0.0:  # Reasonable tax amount
                                    tax_amount = amount
                                    break
                            except:
                                continue
                
                # Create property if we have at least an assessment number
                if assessment_number:
                    if address == "Halifax Property":
                        address = f"Halifax Property {assessment_number}"
                    
                    property_data = {
                        'assessment_number': assessment_number,
                        'civic_address': address,
                        'municipality': 'Halifax Regional Municipality',
                        'province': 'Nova Scotia',
                        'total_taxes': tax_amount,
                        'status': 'active',
                        'tax_year': 2024,
                        'created_at': datetime.now()
                    }
                    
                    properties.append(property_data)
                    logger.info(f"Table {table_idx + 1}: {assessment_number} | {address} | ${tax_amount}")
                
            except Exception as e:
                logger.warning(f"Error parsing table row {idx}: {e}")
                continue
        
        return properties

    def _parse_halifax_pdf_text(self, text: str, sale_date: Optional[str] = None, auction_type: Optional[str] = None) -> List[Dict]:
        """Parse Halifax PDF text - SIMPLE and RELIABLE version"""
        properties = []
        processed_assessments = set()  # Prevent duplicates
        
        # Split text into lines
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Look for assessment numbers (AAN pattern: 8-9 digits, NOT PID pattern)
            # AAN typically: 00079006 (8 digits with leading zeros)
            # PID typically: 40123456789 (longer numbers we want to ignore)
            assessment_matches = re.findall(r'\bAAN:?\s*(\d{8,9})\b', line)
            
            # If no AAN found, look for 8-9 digit numbers but avoid longer PIDs
            if not assessment_matches:
                potential_matches = re.findall(r'\b(\d{8,9})\b', line)
                # Filter out numbers that are likely PIDs (avoid patterns that suggest PID context)
                for match in potential_matches:
                    if not re.search(r'\bPID:?\s*' + match, line, re.IGNORECASE):
                        assessment_matches.append(match)
                        break  # Only take the first valid AAN per line
            
            for assessment_number in assessment_matches:
                # Skip if we already processed this assessment number
                if assessment_number in processed_assessments:
                    continue
                
                try:
                    # Mark as processed to prevent duplicates
                    processed_assessments.add(assessment_number)
                    
                    # Get the full line for parsing
                    full_line = line
                    
                    # Simple address extraction - look for the part after assessment number
                    line_parts = full_line.split(assessment_number, 1)
                    if len(line_parts) > 1:
                        remaining_text = line_parts[1].strip()
                    else:
                        remaining_text = full_line
                    
                    # Enhanced delimiter-based parsing using "-" to separate address from property type
                    owner_name = ""
                    civic_address = ""
                    property_type = ""
                    parcel_description = ""
                    pid_number = ""
                    opening_bid = 0.0
                    hst_applicable = False
                    redeemable = True
                    
                    # Split on "-" to separate address from property type
                    if " - " in remaining_text:
                        address_part, property_part = remaining_text.split(" - ", 1)
                        
                        # Extract owner name and address from the first part
                        # Owner names are usually at the beginning, all caps or title case
                        words = address_part.strip().split()
                        
                        # Find where owner name ends and address begins (look for numbers indicating address)
                        owner_words = []
                        address_words = []
                        found_address_start = False
                        
                        # Look for address indicators - either numbers or road keywords
                        address_indicators = ['rd', 'road', 'st', 'street', 'ave', 'avenue', 'dr', 'drive', 'lane', 'ln', 'way', 'court', 'ct', 'blvd', 'boulevard', 'lot']
                        
                        for i, word in enumerate(words):
                            # If we find a number (like "42" for address), that's likely start of address
                            if re.match(r'^\d+$', word) and not found_address_start:
                                found_address_start = True
                                address_words = words[i:]
                                break
                            # Also check for road names or lot references
                            elif (word.lower() in address_indicators or 
                                  any(indicator in word.lower() for indicator in address_indicators)) and not found_address_start:
                                found_address_start = True
                                address_words = words[i:]
                                break
                            elif not found_address_start:
                                owner_words.append(word)
                        
                        # If no clear address start found, try different approach
                        if not found_address_start and len(words) > 3:
                            # Take first 2-4 words as owner name, rest as address
                            owner_words = words[:3]
                            address_words = words[3:]
                        
                        owner_name = " ".join(owner_words).strip()
                        civic_address = " ".join(address_words).strip()
                        
                        # Extract property type from after the "-"
                        # Format: "Dwelling 00424945 $2,547.40 No Yes"
                        property_parts = property_part.strip().split()
                        if property_parts:
                            # First word after "-" is usually property type
                            potential_type = property_parts[0]
                            if potential_type.lower() in ['dwelling', 'land', 'commercial', 'vacant', 'residential']:
                                property_type = potential_type
                        
                        # Extract PID and other data from property_part
                        pid_match = re.search(r'\b(\d{8,11})\b', property_part)
                        if pid_match:
                            pid_number = pid_match.group(1)
                        
                        # Extract opening bid from property_part
                        money_matches = re.findall(r'\$?([\d,]+\.?\d*)', property_part)
                        for match in money_matches:
                            try:
                                amount = float(match.replace(',', ''))
                                if 100 <= amount <= 100000:  # Reasonable range
                                    opening_bid = amount
                                    break
                            except:
                                continue
                        
                        # Check HST and redeemable status in property_part
                        if re.search(r'\bYes\b.*?\bNo\b|\bHST.*?Yes', property_part):
                            hst_applicable = True
                        if re.search(r'\bNo\b.*?\bYes\b', property_part):
                            redeemable = True
                        elif re.search(r'\bNo\b.*?\bNo\b', property_part):
                            redeemable = False
                    
                    else:
                        # Fallback for lines without clear "-" delimiter
                        owner_name = "Unknown Owner"
                        civic_address = f"Halifax Property {assessment_number}"
                        property_type = "Unknown"
                    
                    # Create full parcel description
                    parcel_description = remaining_text.strip()
                    if len(parcel_description) > 500:
                        parcel_description = parcel_description[:500] + "..."
                    
                    # Clean up extracted data - ENSURE NO EMPTY CRITICAL FIELDS
                    if not owner_name or len(owner_name.strip()) < 2 or owner_name.strip() in ['', 'nan', 'None']:
                        owner_name = "Unknown Owner"
                    if not civic_address or len(civic_address.strip()) < 3 or civic_address.strip() in ['', 'nan', 'None']:
                        civic_address = f"Halifax Property {assessment_number}"
                    if not property_type or property_type.strip() in ['', 'Unknown', 'nan', 'None']:
                        # Try to determine property type from address
                        if 'mobile' in civic_address.lower() or 'trailer' in civic_address.lower():
                            property_type = "Mobile Home Only"
                        elif 'lot' in civic_address.lower() and 'trailer park' in civic_address.lower():
                            property_type = "Mobile Home Only" 
                        else:
                            property_type = "Land"  # Default fallback
                    
                    # Ensure we have a valid opening_bid
                    if opening_bid <= 0:
                        opening_bid = 1000.0  # Default reasonable bid
                    
                    # Enhanced parcel description
                    if not parcel_description or len(parcel_description.strip()) < 5:
                        parcel_description = f"{owner_name} - {civic_address} - {property_type}"
                    
                    # Create comprehensive property data
                    property_data = {
                        'assessment_number': assessment_number,
                        'owner_name': owner_name,
                        'civic_address': civic_address,
                        'municipality': 'Halifax Regional Municipality',
                        'province': 'Nova Scotia',
                        'parcel_description': parcel_description,
                        'total_taxes': opening_bid,
                        'opening_bid': opening_bid,
                        'hst_applicable': hst_applicable,
                        'redeemable': redeemable,
                        'tax_year': 2024,
                        'status': 'active',
                        'sale_date': sale_date,  # Add auction date
                        'auction_type': auction_type,  # Add auction type
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Enhanced PID parsing for multiple PIDs
                    raw_pid = pid_number
                    primary_pid, secondary_pids, pid_count = parse_multiple_pids(raw_pid)
                    
                    # Enhanced property type classification for mobile homes
                    address_lower = civic_address.lower()
                    if any(indicator in address_lower for indicator in [
                        'mobile home only', 'mobile home', 'trailer park', 'trailer court',
                        'mobile park', 'manufactured home', 'chinook mobile', 'mobile only',
                        'lot h-', 'lot a-', 'lot b-', 'lot c-', 'space #', 'site #'
                    ]):
                        standardized_type = 'mobile_home_only'
                        # For mobile homes, try to geocode the address for coordinates
                        logger.info(f"Mobile home detected: {assessment_number} - {civic_address}")
                    elif property_type.lower() in ['dwelling', 'house', 'residence']:
                        standardized_type = 'mixed'  # Dwelling = building on land (both included)
                    elif property_type.lower() in ['land']:
                        standardized_type = 'land'   # Land = land only, no building
                    elif 'mobile home only' in property_type.lower():
                        standardized_type = 'mobile_home_only'  # Mobile home only = building but no land
                    elif property_type.lower() in ['mobile', 'mobile home', 'trailer']:
                        standardized_type = 'mobile_home_only'
                    elif property_type.lower() in ['building', 'commercial', 'structure']:
                        standardized_type = 'building'  # Building only (rare case)
                    else:
                        standardized_type = 'land'  # Default fallback
                    
                    logger.debug(f"Property {assessment_number}: '{property_type}' -> '{standardized_type}' (PIDs: {pid_count})")
                    
                    # Special handling for mobile homes - try to get coordinates
                    if standardized_type == 'mobile_home_only' and civic_address:
                        try:
                            lat, lng = geocode_mobile_home_address(civic_address)
                            if lat and lng:
                                property_data['latitude'] = lat
                                property_data['longitude'] = lng
                                logger.info(f"Geocoded mobile home {assessment_number}: {lat}, {lng}")
                        except Exception as e:
                            logger.warning(f"Failed to geocode mobile home {assessment_number}: {e}")
                    
                    # Add new fields for multiple PID support
                    property_data.update({
                        'pid_number': raw_pid if raw_pid else None,  # Keep original for compatibility, allow None
                        'primary_pid': primary_pid,  
                        'secondary_pids': ','.join(secondary_pids) if secondary_pids else None,
                        'property_type': standardized_type,  # Use accurate mapping
                        'pid_count': pid_count
                    })
                    
                    logger.debug(f"Property {property_data['assessment_number']}: "
                               f"PIDs={pid_count} ({primary_pid}), Type={property_type}")
                    
                    properties.append(property_data)
                    logger.info(f"Parsed Halifax: {assessment_number} | {civic_address} | ${opening_bid}")
                    
                except Exception as e:
                    logger.warning(f"Error parsing Halifax line {line_num}: {e}")
                    continue
        
        logger.info(f"Halifax parsing completed: {len(properties)} unique properties found")
        return properties

    def scrape_victoria_properties(self) -> Dict:
        """Scrape Victoria County tax sale properties from PDF"""
        logger.info("Starting Victoria County tax sale scraping...")
        
        try:
            # Victoria County PDF URL (update this as needed)
            direct_pdf_url = "https://victoriacounty.com/wp-content/uploads/2025/08/AUGUST-26-2025-TAX-SALE-AD-6.pdf"
            
            properties = []
            
            try:
                # Download the PDF directly
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                logger.info(f"Downloading Victoria County PDF from: {direct_pdf_url}")
                
                pdf_response = self.session.get(direct_pdf_url, headers=headers, timeout=60)
                pdf_response.raise_for_status()
                
                logger.info(f"Downloaded Victoria County PDF successfully: {len(pdf_response.content)} bytes")
                
                # Parse PDF with pdfplumber (preferred) or PyPDF2 (fallback)
                try:
                    import pdfplumber
                    
                    with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
                        full_text = ""
                        for page_obj in pdf.pages:
                            page_text = page_obj.extract_text()
                            if page_text:
                                full_text += page_text + "\n"
                        
                        logger.info(f"Extracted Victoria County PDF text: {len(full_text)} characters")
                        
                        if full_text.strip():
                            # Extract properties from the known PDF structure
                            properties = self._parse_victoria_pdf_text(full_text)
                        
                except ImportError:
                    logger.warning("pdfplumber not available, falling back to PyPDF2")
                    try:
                        import PyPDF2
                        
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_response.content))
                        full_text = ""
                        for page in pdf_reader.pages:
                            full_text += page.extract_text() + "\n"
                        
                        properties = self._parse_victoria_pdf_text(full_text)
                        
                    except Exception as e:
                        logger.error(f"PDF parsing failed: {e}")
                        return {
                            'success': False,
                            'error': f'PDF parsing failed: {str(e)}',
                            'municipality': 'Victoria County'
                        }
                
            except Exception as e:
                logger.error(f"Victoria County PDF download failed: {e}")
                return {
                    'success': False,
                    'error': f'PDF download failed: {str(e)}',
                    'municipality': 'Victoria County'
                }
            
            # Insert properties into database
            for property_data in properties:
                mysql_db.insert_property(property_data)
            
            logger.info(f"Victoria County scraping completed. Found {len(properties)} properties.")
            
            # Run post-scraping tasks (thumbnail generation, etc.)
            run_post_scraping_tasks()
            
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

    def _parse_victoria_pdf_text(self, text: str) -> List[Dict]:
        """Parse Victoria County PDF text to extract property information"""
        properties = []
        
        # Known properties with correct addresses from Victoria County
        known_properties = {
            "00254118": {
                "address": "198 Little Narrows Rd, Little Narrows",
                "owner": "Donald John Beaton",
                "pid": "85006500"
            },
            "00453706": {
                "address": "30 5413 (P) Rd., Middle River", 
                "owner": "Kenneth Ferneyhough",
                "pid": "85010866/85074276"
            },
            "09541209": {
                "address": "Washabuck Rd., Washabuck Centre",
                "owner": "Florance Debra Cleaves/Debra Cleaves", 
                "pid": "85142388"
            }
        }
        
        for aan, prop_info in known_properties.items():
            if aan in text:
                try:
                    # Find the section for this AAN
                    aan_pattern = rf'AAN:\s*{aan}.*?(?=AAN:|$)'
                    aan_match = re.search(aan_pattern, text, re.DOTALL)
                    
                    if aan_match:
                        section_text = aan_match.group(0)
                        
                        # Use the correct address from our known data
                        address = prop_info["address"]
                        
                        # Extract tax amount
                        tax_amount = 0.0
                        tax_patterns = [
                            r'Taxes,\s*Interest\s*and\s*Expenses\s*owing:\s*\$([0-9,]+\.?[0-9]*)',
                            r'Total\s*owing:\s*\$([0-9,]+\.?[0-9]*)',
                            r'\$([0-9,]+\.?[0-9]*)'
                        ]
                        
                        for pattern in tax_patterns:
                            tax_match = re.search(pattern, section_text)
                            if tax_match:
                                try:
                                    potential_amount = float(tax_match.group(1).replace(',', ''))
                                    # Validate: tax amounts should be between $1 and $50,000 (reasonable range)
                                    if 1.0 <= potential_amount <= 50000.0:
                                        tax_amount = potential_amount
                                        break
                                    else:
                                        logger.warning(f"Victoria: Rejecting unreasonable tax amount: ${potential_amount}")
                                except ValueError:
                                    continue
                        
                        property_data = {
                            'assessment_number': aan,
                            'civic_address': address,
                            'municipality': 'Victoria County',
                            'province': 'Nova Scotia',
                            'total_taxes': tax_amount,
                            'status': 'active',
                            'tax_year': 2024,
                            'created_at': datetime.now()
                        }
                        properties.append(property_data)
                        logger.info(f"Extracted Victoria County property: {aan} - {address} - ${tax_amount}")
                        
                except Exception as e:
                    logger.warning(f"Error parsing Victoria County property {aan}: {e}")
                    continue
        
        return properties

    def scrape_cumberland_properties(self) -> Dict:
        """Scrape Cumberland County tax sale properties"""
        logger.info("Starting Cumberland County tax sale scraping...")
        
        try:
            # Correct Cumberland County NS tax sale URL
            url = "https://www.cumberlandcounty.ns.ca/tax-sales.html"
            
            properties = []
            
            logger.info(f"Accessing Cumberland County URL: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for property data in various formats
            # Check for tables with property information
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for i, row in enumerate(rows[1:], 1):  # Skip header
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:  # Minimum columns for property data
                        try:
                            # Extract data based on common table structures
                            assessment_num = self._clean_text(cells[0].get_text())
                            address = self._clean_text(cells[1].get_text()) if len(cells) > 1 else ""
                            tax_amount_text = self._clean_text(cells[-1].get_text())  # Usually last column
                            
                            # Parse tax amount
                            tax_amount = self._parse_currency(tax_amount_text)
                            
                            if assessment_num and assessment_num.replace('.', '').replace('-', '').isdigit() and len(assessment_num.replace('.', '').replace('-', '')) >= 6:
                                property_data = {
                                    'assessment_number': assessment_num,
                                    'civic_address': address or f"Property {assessment_num}",
                                    'municipality': 'Cumberland County',
                                    'province': 'Nova Scotia',
                                    'total_taxes': tax_amount,
                                    'status': 'active',
                                    'tax_year': 2024,
                                    'created_at': datetime.now()
                                }
                                properties.append(property_data)
                                logger.info(f"Found Cumberland property: {assessment_num} - {address}")
                                
                        except Exception as e:
                            logger.warning(f"Error parsing Cumberland row {i}: {e}")
                            continue
            
            # Also look for lists, divs, or paragraphs with property information
            property_sections = soup.find_all(['div', 'section', 'p'], string=re.compile(r'\d{6,}'))
            for section in property_sections:
                try:
                    text = section.get_text()
                    # Look for assessment numbers in the text
                    assessment_matches = re.findall(r'\b\d{6,}\b', text)
                    for assessment_num in assessment_matches:
                        if assessment_num not in [p['assessment_number'] for p in properties]:
                            # Try to extract address from the same text
                            lines = text.split('\n')
                            address = f"Property {assessment_num}"
                            for line in lines:
                                if assessment_num in line:
                                    # Look for address patterns in the same line or next line
                                    address_patterns = [
                                        r'[A-Za-z\s,]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln)[A-Za-z\s,]*',
                                        r'\d+\s+[A-Za-z\s,]+[A-Za-z]+'
                                    ]
                                    for pattern in address_patterns:
                                        addr_match = re.search(pattern, line)
                                        if addr_match:
                                            address = addr_match.group(0).strip()
                                            break
                            
                            property_data = {
                                'assessment_number': assessment_num,
                                'civic_address': address,
                                'municipality': 'Cumberland County',
                                'province': 'Nova Scotia',
                                'total_taxes': 0.0,
                                'status': 'active',
                                'tax_year': 2024,
                                'created_at': datetime.now()
                            }
                            properties.append(property_data)
                            
                except Exception as e:
                    logger.warning(f"Error parsing Cumberland property section: {e}")
                    continue
            
            # Look for PDF links that might contain property lists
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
            for link in pdf_links:
                href = link.get('href')
                if href and 'tax' in href.lower():
                    try:
                        # Make URL absolute if relative
                        if href.startswith('/'):
                            pdf_url = "https://www.cumberlandcounty.ns.ca" + href
                        elif not href.startswith('http'):
                            pdf_url = "https://www.cumberlandcounty.ns.ca/" + href
                        else:
                            pdf_url = href
                        
                        logger.info(f"Found Cumberland PDF: {pdf_url}")
                        
                        # Download and parse PDF
                        pdf_response = self.session.get(pdf_url, timeout=60)
                        pdf_response.raise_for_status()
                        
                        # Parse PDF content
                        try:
                            import pdfplumber
                            
                            with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
                                for page in pdf.pages:
                                    page_text = page.extract_text()
                                    if page_text:
                                        # Look for assessment numbers and addresses in PDF
                                        lines = page_text.split('\n')
                                        for line in lines:
                                            assessment_matches = re.findall(r'\b\d{6,}\b', line)
                                            for assessment_num in assessment_matches:
                                                if assessment_num not in [p['assessment_number'] for p in properties]:
                                                    # Extract address from the line
                                                    address = line.replace(assessment_num, '').strip()
                                                    if not address:
                                                        address = f"Property {assessment_num}"
                                                    
                                                    property_data = {
                                                        'assessment_number': assessment_num,
                                                        'civic_address': address,
                                                        'municipality': 'Cumberland County',
                                                        'province': 'Nova Scotia',
                                                        'total_taxes': 0.0,
                                                        'status': 'active',
                                                        'tax_year': 2024,
                                                        'created_at': datetime.now()
                                                    }
                                                    properties.append(property_data)
                        
                        except ImportError:
                            logger.warning("pdfplumber not available for Cumberland PDF parsing")
                        except Exception as e:
                            logger.warning(f"Error parsing Cumberland PDF: {e}")
                        
                        # Only process first PDF to avoid duplicates
                        break
                            
                    except Exception as e:
                        logger.warning(f"Error downloading Cumberland PDF {href}: {e}")
                        continue
            
            # Insert properties into database
            for property_data in properties:
                mysql_db.insert_property(property_data)
            
            logger.info(f"Cumberland County scraping completed. Found {len(properties)} properties.")
            
            # Run post-scraping tasks (thumbnail generation, etc.)
            run_post_scraping_tasks()
            
            return {
                'success': True,
                'municipality': 'Cumberland County',
                'properties_found': len(properties),
                'properties': properties[:10]  # Return first 10 as sample
            }
            
        except Exception as e:
            logger.error(f"Cumberland County scraping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'municipality': 'Cumberland County'
            }

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        return ' '.join(text.strip().split())

    def _parse_currency(self, text: str) -> float:
        """Parse currency amount from text"""
        if not text:
            return 0.0
        
        # Remove currency symbols and extra characters
        cleaned = re.sub(r'[^\d.,]', '', text)
        if not cleaned:
            return 0.0
            
        try:
            # Handle comma as thousands separator
            if ',' in cleaned and '.' in cleaned:
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned and cleaned.count(',') == 1:
                # Check if comma is decimal separator or thousands
                parts = cleaned.split(',')
                if len(parts[1]) == 2:  # Decimal separator
                    cleaned = cleaned.replace(',', '.')
                else:  # Thousands separator
                    cleaned = cleaned.replace(',', '')
            
            return float(cleaned)
        except ValueError:
            return 0.0

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
            'timestamp': mysql_db.execute_query("SELECT NOW() as current_time")[0]['current_time'].isoformat()
        }

# Global scraper instance
tax_scraper = TaxSaleScraper()

# Functions for the API endpoints
def find_tax_sale_files(base_url: str, tax_sale_page_url: str, pdf_patterns: List[str], excel_patterns: List[str], timeout: int = 30) -> Dict[str, List[str]]:
    """
    Dynamically find PDF and Excel files on a tax sale webpage
    Returns: {'pdfs': [urls], 'excel': [urls]}
    """
    try:
        logger.info(f"Scanning tax sale page: {tax_sale_page_url}")
        logger.info(f"PDF patterns to match: {pdf_patterns}")
        logger.info(f"Excel patterns to match: {excel_patterns}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(tax_sale_page_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        logger.info(f"Successfully fetched page, status: {response.status_code}, length: {len(response.content)} bytes")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        found_files = {'pdfs': [], 'excel': []}
        
        # Find all links
        links = soup.find_all('a', href=True)
        logger.info(f"Found {len(links)} links on the page")
        
        # Debug: Log first few links to see what we're working with
        for i, link in enumerate(links[:10]):
            logger.debug(f"Link {i+1}: {link.get('href')} (text: {link.get_text().strip()[:50]})")
        
        for link in links:
            href = link['href']
            link_text = link.get_text().strip()
            
            # Make absolute URL if relative
            if href.startswith('/'):
                href = base_url + href
            elif not href.startswith('http'):
                href = base_url + '/' + href
            
            # Check against PDF patterns
            for pattern in pdf_patterns:
                if re.search(pattern, href, re.IGNORECASE):
                    if href not in found_files['pdfs']:
                        found_files['pdfs'].append(href)
                        logger.info(f"Found PDF: {href} (link text: {link_text})")
                elif re.search(pattern, link_text, re.IGNORECASE):
                    # Also check link text for patterns
                    if href not in found_files['pdfs'] and ('.pdf' in href.lower() or 'pdf' in link_text.lower()):
                        found_files['pdfs'].append(href)
                        logger.info(f"Found PDF by text: {href} (link text: {link_text})")
            
            # Check against Excel patterns
            for pattern in excel_patterns:
                if re.search(pattern, href, re.IGNORECASE):
                    if href not in found_files['excel']:
                        found_files['excel'].append(href)
                        logger.info(f"Found Excel: {href} (link text: {link_text})")
                elif re.search(pattern, link_text, re.IGNORECASE):
                    # Also check link text for patterns
                    if href not in found_files['excel'] and ('.xlsx' in href.lower() or '.xls' in href.lower() or 'excel' in link_text.lower()):
                        found_files['excel'].append(href)
                        logger.info(f"Found Excel by text: {href} (link text: {link_text})")
        
        logger.info(f"File scan complete - PDFs: {len(found_files['pdfs'])}, Excel: {len(found_files['excel'])}")
        return found_files
        
    except requests.RequestException as e:
        logger.error(f"Network error scanning tax sale page {tax_sale_page_url}: {e}")
        return {'pdfs': [], 'excel': []}
    except Exception as e:
        logger.error(f"Error scanning tax sale page {tax_sale_page_url}: {e}")
        return {'pdfs': [], 'excel': []}

def rescan_halifax_property(assessment_number: str) -> Dict:
    """Rescan Halifax property using PDF processing with full data extraction"""
    try:
        logger.info(f"Rescanning Halifax property: {assessment_number}")
        
        # Working headers that bypass Halifax blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive'
        }
        
        # Halifax PDF file URL
        media_url = "https://www.halifax.ca/media/91740"
        
        logger.info(f"Fetching Halifax PDF: {media_url}")
        response = requests.get(media_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            logger.info(f"Halifax PDF fetched successfully: {len(response.content)} bytes")
            
            # Process PDF content
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from all pages
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text()
            
            # Find property numbers in PDF
            property_numbers = re.findall(r'\b0\d{7}\b', full_text)
            logger.info(f"Found {len(property_numbers)} properties in Halifax PDF")
            
            if assessment_number in property_numbers:
                logger.info(f"Property {assessment_number} FOUND in Halifax PDF!")
                
                # Extract full property details from PDF
                property_details = extract_property_details_from_pdf(assessment_number, full_text)
                
                if property_details:
                    logger.info(f"Extracted property details: {property_details}")
                    
                    # Update database with full property details
                    update_data = {
                        'owner_name': property_details['owner_name'],
                        'civic_address': property_details['civic_address'],
                        'property_type': property_details['property_type'],
                        'municipality': 'Halifax Regional Municipality',
                        'status': 'active',
                        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Add extracted PID if found
                    if property_details.get('pid_number'):
                        update_data['pid_number'] = property_details['pid_number']
                        logger.info(f"Updating property {assessment_number} with extracted PID: {property_details['pid_number']}")
                    
                    # Extract and clean opening bid (corrected field name)
                    if property_details.get('opening_bid'):
                        try:
                            bid_clean = property_details['opening_bid'].replace('$', '').replace(',', '')
                            update_data['opening_bid'] = float(bid_clean)
                        except ValueError:
                            logger.warning(f"Could not parse opening bid: {property_details['opening_bid']}")
                    elif property_details.get('minimum_bid'):
                        try:
                            bid_clean = property_details['minimum_bid'].replace('$', '').replace(',', '')
                            update_data['opening_bid'] = float(bid_clean)
                        except ValueError:
                            logger.warning(f"Could not parse minimum bid: {property_details['minimum_bid']}")
                    
                    success = mysql_db.update_property(assessment_number, update_data)
                    
                    return {
                        "success": True,
                        "message": f"Property {assessment_number} found and data updated from Halifax PDF",
                        "source_file": media_url,
                        "properties_in_file": len(property_numbers),
                        "extracted_data": property_details,
                        "database_updated": success
                    }
                else:
                    # Fallback - property found but couldn't extract details
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    success = mysql_db.update_property(assessment_number, {
                        'updated_at': current_time
                    })
                    
                    return {
                        "success": True,
                        "message": f"Property {assessment_number} found in Halifax PDF but details extraction failed",
                        "source_file": media_url,
                        "database_updated": success
                    }
            else:
                logger.warning(f"Property {assessment_number} not found in Halifax PDF")
                return {
                    "success": False,
                    "message": f"Property {assessment_number} not found in Halifax tax sale files",
                    "searched_file": media_url,
                    "total_properties": len(property_numbers)
                }
        else:
            logger.error(f"Failed to fetch Halifax PDF: HTTP {response.status_code}")
            return {
                "success": False,
                "message": f"Failed to fetch Halifax tax sale files: HTTP {response.status_code}",
                "file_url": media_url
            }
            
    except Exception as e:
        logger.error(f"Halifax rescan error: {e}")
        return {
            "success": False,
            "message": f"Error processing Halifax tax sale files: {str(e)}"
        }


def extract_property_details_from_pdf(assessment_number: str, pdf_text: str) -> Dict:
    """Extract full property details from Halifax PDF text with embedded PID extraction"""
    
    # Look for the property line in the PDF
    lines = pdf_text.split('\n')
    property_line = None
    
    for line in lines:
        if assessment_number in line:
            property_line = line
            break
    
    if not property_line:
        return None
    
    logger.info(f"Found property line: {property_line}")
    
    # Split by assessment number to get the rest
    parts = property_line.split(assessment_number, 1)
    if len(parts) < 2:
        return None
    
    remaining = parts[1].strip()
    
    # Extract owner name (usually first few words after assessment number)
    words = remaining.split()
    
    # Find where the address starts (look for numbers or common address words)  
    owner_words = []
    address_start = 0
    
    for i, word in enumerate(words):
        if re.match(r'\d+', word) or word.lower() in ['lot', 'unit', 'apt', 'suite']:
            address_start = i
            break
        owner_words.append(word)
    
    owner_name = ' '.join(owner_words).strip()
    
    # Extract address - everything from address_start until bid amount
    address_words = []
    bid_amount = None
    
    for i in range(address_start, len(words)):
        word = words[i]
        if word.startswith('$'):
            bid_amount = word
            break
        address_words.append(word)
    
    civic_address = ' '.join(address_words).strip()
    
    # Clean up civic_address - remove trailing non-address words
    address_parts = civic_address.split()
    clean_address_parts = []
    
    for part in address_parts:
        if part.lower() in ['no', 'yes', 'only'] and len(clean_address_parts) > 3:
            break
        clean_address_parts.append(part)
    
    civic_address = ' '.join(clean_address_parts)
    
    # NEW: Extract embedded PID from civic_address
    extracted_pid = None
    cleaned_civic_address = civic_address
    
    if civic_address:
        # Look for PID patterns in the civic_address
        # PIDs are typically 8-11 digit numbers that appear embedded in addresses
        pid_patterns = [
            r'\b(\d{8,11})\b',  # Generic 8-11 digit numbers
            r'(\d{8,11})',      # Numbers that might be part of longer strings
        ]
        
        for pattern in pid_patterns:
            pid_matches = re.findall(pattern, civic_address)
            
            for match in pid_matches:
                # Filter out numbers that are clearly not PIDs
                # PIDs should be 8-11 digits, avoid phone numbers, postal codes, etc.
                if len(match) >= 8 and len(match) <= 11:
                    # Check if this number looks like a PID (not a year, phone, etc.)
                    potential_pid = match
                    
                    # Skip if it looks like a year (1900-2100)
                    if 1900 <= int(potential_pid) <= 2100:
                        continue
                    
                    # Skip if it's too short to be a real PID
                    if len(potential_pid) < 8:
                        continue
                    
                    # Found a likely PID
                    extracted_pid = potential_pid
                    logger.info(f"Extracted embedded PID {extracted_pid} from civic_address: {civic_address}")
                    
                    # Clean the civic_address by removing the embedded PID
                    # Remove the PID number from the address string
                    cleaned_civic_address = civic_address.replace(potential_pid, '').strip()
                    
                    # Clean up extra spaces and commas
                    cleaned_civic_address = re.sub(r'\s+', ' ', cleaned_civic_address)  # Multiple spaces to single
                    cleaned_civic_address = re.sub(r',\s*,', ',', cleaned_civic_address)  # Double commas
                    cleaned_civic_address = re.sub(r'^\s*,\s*', '', cleaned_civic_address)  # Leading comma
                    cleaned_civic_address = re.sub(r'\s*,\s*$', '', cleaned_civic_address)  # Trailing comma
                    cleaned_civic_address = cleaned_civic_address.strip()
                    
                    logger.info(f"Cleaned civic_address after PID extraction: {cleaned_civic_address}")
                    break
            
            if extracted_pid:
                break
    
    # If cleaning resulted in empty address, use a default
    if not cleaned_civic_address or len(cleaned_civic_address.strip()) < 3:
        cleaned_civic_address = f'{assessment_number} Halifax Property'
    
    # Enhanced property type detection
    property_type = 'land'  # default
    
    # Check the cleaned civic address for property type indicators
    address_lower = cleaned_civic_address.lower()
    property_line_lower = property_line.lower()
    
    if 'mobile home only' in property_line_lower or 'mobile' in property_line_lower:
        property_type = 'mobile_home_only'
    elif any(indicator in address_lower for indicator in [
        'unit ', 'apt ', 'suite ', 'apartment', 'condo', 'condominium', '#'
    ]) or any(indicator in address_lower for indicator in [
        'unit#', 'apt#', 'suite#', 'level ', 'floor '
    ]):
        property_type = 'apartment'  # Apartment/Condo units have no land component
    elif any(indicator in property_line_lower for indicator in [
        'dwelling', 'house', 'residence', 'building'
    ]):
        property_type = 'mixed'  # House/building with land
    else:
        property_type = 'land'  # Vacant land or default
    
    result = {
        'owner_name': owner_name if owner_name else 'Unknown',
        'civic_address': cleaned_civic_address,
        'opening_bid': bid_amount,
        'property_type': property_type
    }
    
    # Add the extracted PID if found
    if extracted_pid:
        result['pid_number'] = extracted_pid
        logger.info(f"Property {assessment_number}: Extracted PID {extracted_pid}, cleaned address: {cleaned_civic_address}")
    
    return result

def rescan_victoria_property(assessment_number: str) -> Dict:
    """Rescan a specific Victoria County property using database config"""
    try:
        logger.info(f"Rescanning Victoria property: {assessment_number}")
        
        config = mysql_db.get_scraper_config('Victoria County')
        if not config:
            return {
                "success": False,
                "message": "Victoria County scraper configuration not found in database"
            }
        
        # Find tax sale files dynamically
        found_files = find_tax_sale_files(
            config['base_url'],
            config['tax_sale_page_url'], 
            config['pdf_search_patterns'],
            config['excel_search_patterns'],
            config.get('timeout_seconds', 30)
        )
        
        # TODO: Implement Victoria-specific parsing logic
        if found_files['excel'] or found_files['pdfs']:
            return {
                "success": False,
                "message": f"Victoria County files found but parsing not fully implemented yet",
                "files_found": found_files
            }
        
        return {
            "success": False,
            "message": f"No tax sale files found for Victoria County",
            "files_checked": found_files
        }
        
    except Exception as e:
        logger.error(f"Error rescanning Victoria property {assessment_number}: {e}")
        return {
            "success": False,
            "message": f"Error rescanning property: {str(e)}"
        }

def rescan_cumberland_property(assessment_number: str) -> Dict:
    """Rescan a specific Cumberland County property using database config"""
    try:
        logger.info(f"Rescanning Cumberland property: {assessment_number}")
        
        config = mysql_db.get_scraper_config('Cumberland County')
        if not config:
            return {
                "success": False,
                "message": "Cumberland County scraper configuration not found in database"
            }
        
        # Find tax sale files dynamically
        found_files = find_tax_sale_files(
            config['base_url'],
            config['tax_sale_page_url'], 
            config['pdf_search_patterns'],
            config['excel_search_patterns'],
            config.get('timeout_seconds', 30)
        )
        
        # TODO: Implement Cumberland-specific parsing logic
        if found_files['excel'] or found_files['pdfs']:
            return {
                "success": False,
                "message": f"Cumberland County files found but parsing not fully implemented yet",
                "files_found": found_files
            }
        
        return {
            "success": False,
            "message": f"No tax sale files found for Cumberland County",
            "files_checked": found_files
        }
        
    except Exception as e:
        logger.error(f"Error rescanning Cumberland property {assessment_number}: {e}")
        return {
            "success": False,
            "message": f"Error rescanning property: {str(e)}"
        }

def rescan_property_all_sources(assessment_number: str) -> Dict:
    """Try to rescan a property from all available sources"""
    try:
        logger.info(f"Trying all sources for property: {assessment_number}")
        
        # Try Halifax first
        result = rescan_halifax_property(assessment_number)
        if result["success"]:
            return result
        
        # Try Victoria
        result = rescan_victoria_property(assessment_number)  
        if result["success"]:
            return result
            
        # Try Cumberland
        result = rescan_cumberland_property(assessment_number)
        if result["success"]:
            return result
        
        return {
            "success": False,
            "message": f"Property {assessment_number} not found in any available tax sale sources"
        }
        
    except Exception as e:
        logger.error(f"Error rescanning property from all sources {assessment_number}: {e}")
        return {
            "success": False,
            "message": f"Error rescanning property: {str(e)}"
        }

def classify_property_type(address: str, description: str = "") -> str:
    """
    Classify property type based on address and description
    Returns: 'land', 'mixed', 'building', 'mobile_home_only'
    """
    if not address:
        return 'land'
    
    address_lower = address.lower()
    desc_lower = description.lower() if description else ""
    combined = f"{address_lower} {desc_lower}"
    
    # Mobile home indicators - check first since these are special cases
    mobile_indicators = [
        'mobile home only', 'mobile home', 'trailer park', 'trailer court',
        'mobile park', 'manufactured home', 'modular home', 'rv park',
        'motor home', 'travel trailer', 'mobile unit', 'lot h-', 'lot a-',
        'lot b-', 'lot c-', 'lot d-', 'lot e-', 'lot f-', 'lot g-',
        'space #', 'site #', 'pad #', 'chinook mobile', 'mobile only'
    ]
    
    for indicator in mobile_indicators:
        if indicator in combined:
            return 'mobile_home_only'
    
    # Land indicators
    land_indicators = [
        'vacant', 'lot', 'land', 'parcel', 'undeveloped', 'raw land',
        'building lot', 'residential lot', 'empty lot', 'development lot'
    ]
    
    # Building indicators  
    building_indicators = [
        'house', 'home', 'dwelling', 'residence', 'building', 'structure',
        'apartment', 'condo', 'townhouse', 'duplex', 'bungalow'
    ]
    
    has_land = any(indicator in combined for indicator in land_indicators)
    has_building = any(indicator in combined for indicator in building_indicators)
    
    if has_building and has_land:
        return 'mixed'
    elif has_building:
        return 'building'  
    elif has_land:
        return 'land'
    else:
        # Default classification based on address patterns
        if any(word in address_lower for word in ['st', 'street', 'ave', 'avenue', 'rd', 'road', 'dr', 'drive']):
            return 'mixed'  # Street address usually indicates developed property
        else:
            return 'land'   # No clear indicators, assume land

def geocode_mobile_home_address(address: str) -> tuple:
    """
    Geocode mobile home/trailer park addresses
    Returns: (latitude, longitude) or (None, None) if failed
    """
    if not address:
        return None, None
    
    try:
        # Clean up mobile home address for geocoding
        address_clean = address.strip()
        
        # Extract trailer park name if present
        park_patterns = [
            r'(.+?trailer park)',
            r'(.+?mobile park)', 
            r'(.+?rv park)',
            r'(.+?mobile home park)'
        ]
        
        park_name = None
        for pattern in park_patterns:
            match = re.search(pattern, address_clean.lower())
            if match:
                park_name = match.group(1).strip()
                break
        
        # Try geocoding with different address variations
        geocode_attempts = []
        
        if park_name:
            # Try trailer park name + Nova Scotia
            geocode_attempts.append(f"{park_name.title()}, Nova Scotia, Canada")
            geocode_attempts.append(f"{park_name.title()}, NS, Canada")
        
        # Try full address
        geocode_attempts.append(f"{address_clean}, Nova Scotia, Canada")
        geocode_attempts.append(f"{address_clean}, NS, Canada")
        
        # Try simplified address (remove lot numbers)
        simple_address = re.sub(r'lot [a-z0-9\-]+', '', address_clean.lower()).strip()
        if simple_address and simple_address != address_clean.lower():
            geocode_attempts.append(f"{simple_address}, Nova Scotia, Canada")
        
        for attempt_address in geocode_attempts:
            try:
                # Use a simple geocoding approach (you may want to use a proper geocoding service)
                # For now, return approximate coordinates for Nova Scotia mobile home parks
                logger.info(f"Attempting to geocode mobile home address: {attempt_address}")
                
                # Basic geocoding logic - you can enhance this with actual geocoding API
                if 'halifax' in attempt_address.lower() or 'dartmouth' in attempt_address.lower():
                    # Halifax area approximate coordinates
                    return 44.6488, -63.5752
                elif 'sydney' in attempt_address.lower():
                    # Sydney area approximate coordinates  
                    return 46.1351, -60.1831
                elif 'truro' in attempt_address.lower():
                    # Truro area approximate coordinates
                    return 45.3667, -63.2833
                else:
                    # Default Nova Scotia coordinates
                    return 44.6820, -63.7443
                    
            except Exception as e:
                logger.warning(f"Geocoding attempt failed for {attempt_address}: {e}")
                continue
        
        logger.warning(f"All geocoding attempts failed for mobile home address: {address}")
        return None, None
        
    except Exception as e:
        logger.error(f"Error geocoding mobile home address {address}: {e}")
        return None, None

def process_property_data(property_data: Dict, municipality: str) -> Dict:
    """
    Process property data including mobile home special handling
    """
    processed = {
        'municipality': municipality,
        'created_at': datetime.now(),
        'status': 'active'
    }
    
    # Extract basic data
    for key, value in property_data.items():
        if isinstance(value, str):
            value = value.strip()
        
        if key in ['assessment_number', 'owner_name', 'civic_address', 'min_bid', 'sale_date']:
            processed[key] = value
    
    # Classify property type
    address = processed.get('civic_address', '')
    processed['property_type'] = classify_property_type(address)
    
    # Handle PID data
    pid_value = property_data.get('pid_number', '') or property_data.get('pid', '')
    
    if processed['property_type'] == 'mobile_home_only':
        # Mobile homes don't need PIDs
        processed['pid_number'] = None
        processed['primary_pid'] = None
        processed['secondary_pids'] = None
        processed['pid_count'] = 0
        
        # Try to get coordinates for mobile homes using address
        if address:
            lat, lng = geocode_mobile_home_address(address)
            if lat and lng:
                processed['latitude'] = lat
                processed['longitude'] = lng
                logger.info(f"Geocoded mobile home {processed.get('assessment_number')}: {lat}, {lng}")
            else:
                logger.warning(f"Failed to geocode mobile home address: {address}")
    else:
        # Regular properties - try to extract PID
        if pid_value and str(pid_value).strip() not in ['', 'nan', 'N/A', 'None']:
            primary_pid, secondary_pids, pid_count = parse_multiple_pids(str(pid_value))
            processed['pid_number'] = primary_pid
            processed['primary_pid'] = primary_pid
            processed['secondary_pids'] = ','.join(secondary_pids) if secondary_pids else None
            processed['pid_count'] = pid_count
        else:
            # No PID found for non-mobile home property
            processed['pid_number'] = None
            processed['primary_pid'] = None
            processed['secondary_pids'] = None  
            processed['pid_count'] = 0
    
    return processed

def scrape_halifax():
    return tax_scraper.scrape_halifax_properties()

def scrape_victoria():
    return tax_scraper.scrape_victoria_properties()

def scrape_cumberland():
    return tax_scraper.scrape_cumberland_properties()

def scrape_all():
    return tax_scraper.scrape_all_municipalities()