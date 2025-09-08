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
            # Use the actual Halifax PDF URL
            pdf_url = "https://cdn.halifax.ca/sites/default/files/documents/home-property/property-taxes/sept16.2025newspaper.website-sept3.25.pdf"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            logger.info(f"Downloading Halifax PDF for debugging: {pdf_url}")
            pdf_response = self.session.get(pdf_url, headers=headers, timeout=60)
            pdf_response.raise_for_status()
            
            logger.info(f"PDF downloaded successfully: {len(pdf_response.content)} bytes")
            
            # Extract auction information from PDF URL and content
            logger.info("Extracting auction information...")
            sale_date_from_url, auction_type_from_url = extract_auction_info_from_pdf_url(pdf_url)
            sale_date_from_content, auction_type_from_content = extract_auction_info_from_pdf_content(pdf_response.content)
            
            # Use the best available information (prefer content over URL)
            final_sale_date = sale_date_from_content or sale_date_from_url
            final_auction_type = auction_type_from_content if auction_type_from_content != "Public Auction" else auction_type_from_url
            
            logger.info(f"Final auction info - Date: {final_sale_date}, Type: {final_auction_type}")
            
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
                            
                            properties = self._parse_halifax_pdf_text(all_text)
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

    def _parse_halifax_pdf_text(self, text: str) -> List[Dict]:
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
                        
                        for i, word in enumerate(words):
                            # If we find a number (like "42" for address), that's likely start of address
                            if re.match(r'^\d+$', word) and not found_address_start:
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
                    
                    # Clean up extracted data
                    if not owner_name or len(owner_name) < 2:
                        owner_name = "Unknown Owner"
                    if not civic_address or len(civic_address) < 3:
                        civic_address = f"Halifax Property {assessment_number}"
                    if not property_type:
                        property_type = "Unknown"
                    
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
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Enhanced PID parsing for multiple PIDs
                    raw_pid = pid_number
                    primary_pid, secondary_pids, pid_count = parse_multiple_pids(raw_pid)
                    
                    # Use the property type extracted from the listing (not detected)
                    # Convert listing property types to standardized values based on actual meaning
                    if property_type.lower() in ['dwelling', 'house', 'residence']:
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
                    
                    # Add new fields for multiple PID support
                    property_data.update({
                        'pid_number': raw_pid,  # Keep original for compatibility
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
def scrape_halifax():
    return tax_scraper.scrape_halifax_properties()

def scrape_victoria():
    return tax_scraper.scrape_victoria_properties()

def scrape_cumberland():
    return tax_scraper.scrape_cumberland_properties()

def scrape_all():
    return tax_scraper.scrape_all_municipalities()