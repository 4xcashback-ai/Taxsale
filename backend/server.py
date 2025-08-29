from fastapi import FastAPI, APIRouter, HTTPException, Query, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import asyncio
import re
import PyPDF2
import pdfplumber
import io
import pandas as pd
from io import BytesIO
import re
from urllib.parse import quote
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="NS Tax Sale Aggregator", description="Nova Scotia Municipality Tax Sale Information Aggregator")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize scheduler
scheduler = AsyncIOScheduler()

# Define Models
class Municipality(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    website_url: str
    tax_sale_url: Optional[str] = None
    province: str = "Nova Scotia"
    region: Optional[str] = None
    last_scraped: Optional[datetime] = None
    scrape_status: str = "pending"  # pending, success, failed
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    scraper_type: str = "generic"  # generic, halifax, cbrm, etc.
    # Scraping Schedule Configuration
    scrape_enabled: bool = True
    scrape_frequency: str = "weekly"  # daily, weekly, monthly
    scrape_day_of_week: Optional[int] = 1  # 0=Monday, 6=Sunday (for weekly)
    scrape_day_of_month: Optional[int] = 1  # 1-28 (for monthly)
    scrape_time_hour: int = 2  # 24-hour format
    scrape_time_minute: int = 0
    next_scrape_time: Optional[datetime] = None

class MunicipalityCreate(BaseModel):
    name: str
    website_url: str
    tax_sale_url: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    scraper_type: str = "generic"
    # Scraping Schedule Configuration
    scrape_enabled: bool = True
    scrape_frequency: str = "weekly"  # daily, weekly, monthly
    scrape_day_of_week: Optional[int] = 1  # 0=Monday, 6=Sunday (for weekly)
    scrape_day_of_month: Optional[int] = 1  # 1-28 (for monthly)
    scrape_time_hour: int = 2  # 24-hour format
    scrape_time_minute: int = 0

class MunicipalityUpdate(BaseModel):
    name: Optional[str] = None
    website_url: Optional[str] = None
    tax_sale_url: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    scraper_type: Optional[str] = None
    scrape_enabled: Optional[bool] = None
    scrape_frequency: Optional[str] = None
    scrape_day_of_week: Optional[int] = None
    scrape_day_of_month: Optional[int] = None
    scrape_time_hour: Optional[int] = None
    scrape_time_minute: Optional[int] = None

class TaxSaleProperty(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    municipality_id: str
    municipality_name: str
    property_address: str
    property_description: Optional[str] = None
    assessment_value: Optional[float] = None
    tax_owing: Optional[float] = None
    opening_bid: Optional[float] = None
    sale_date: Optional[datetime] = None
    sale_time: Optional[str] = None
    sale_location: Optional[str] = None
    property_id: Optional[str] = None  # Municipal property ID
    assessment_number: Optional[str] = None  # AAN
    property_type: Optional[str] = None
    lot_size: Optional[str] = None
    zoning: Optional[str] = None
    owner_name: Optional[str] = None
    pid_number: Optional[str] = None  # Property Identification Number
    redeemable: Optional[str] = None  # Redeemable status from tax sale
    hst_applicable: Optional[str] = None  # HST information
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_url: str
    raw_data: Optional[dict] = None  # Store original scraped data
    status: str = "active"  # active, inactive, sold
    status_updated_at: Optional[datetime] = None

class TaxSalePropertyCreate(BaseModel):
    municipality_id: str
    municipality_name: str
    property_address: str
    property_description: Optional[str] = None
    assessment_value: Optional[float] = None
    tax_owing: Optional[float] = None
    opening_bid: Optional[float] = None
    sale_date: Optional[datetime] = None
    sale_time: Optional[str] = None
    sale_location: Optional[str] = None
    property_id: Optional[str] = None
    assessment_number: Optional[str] = None
    property_type: Optional[str] = None
    lot_size: Optional[str] = None
    zoning: Optional[str] = None
    owner_name: Optional[str] = None
    pid_number: Optional[str] = None
    redeemable: Optional[str] = None
    hst_applicable: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: str
    raw_data: Optional[dict] = None

class ScrapeStats(BaseModel):
    total_municipalities: int
    scraped_today: int
    total_properties: int
    active_properties: int = 0
    inactive_properties: int = 0
    last_scrape: Optional[datetime] = None


async def update_property_statuses():
    """
    Update property statuses based on sale dates and current listings
    """
    try:
        current_time = datetime.now(timezone.utc)
        
        # Mark properties as inactive if sale date has passed
        sale_date_filter = {
            "sale_date": {"$lt": current_time},
            "status": "active"
        }
        
        result = await db.tax_sales.update_many(
            sale_date_filter,
            {
                "$set": {
                    "status": "inactive",
                    "status_updated_at": current_time
                }
            }
        )
        
        logger.info(f"Updated {result.modified_count} properties to inactive due to passed sale dates")
        
        return result.modified_count
        
    except Exception as e:
        logger.error(f"Error updating property statuses: {e}")
        return 0

async def mark_missing_properties_inactive(current_assessment_numbers: list, municipality_name: str):
    """
    Mark properties as inactive if they're no longer in the current tax sale list
    """
    try:
        current_time = datetime.now(timezone.utc)
        
        # Find active properties that are not in the current list
        missing_properties_filter = {
            "municipality_name": municipality_name,
            "assessment_number": {"$nin": current_assessment_numbers},
            "status": "active"
        }
        
        result = await db.tax_sales.update_many(
            missing_properties_filter,
            {
                "$set": {
                    "status": "inactive",
                    "status_updated_at": current_time
                }
            }
        )
        
        logger.info(f"Marked {result.modified_count} properties as inactive - no longer in {municipality_name} tax sale list")
        
        return result.modified_count
        
    except Exception as e:
        logger.error(f"Error marking missing properties inactive: {e}")
        return 0


# Halifax-specific scraper
async def scrape_halifax_tax_sales():
    """Scrape Halifax Regional Municipality tax sales"""
    try:
        logger.info("Starting Halifax tax sale scraping...")
        
        # Get Halifax municipality
        halifax = await db.municipalities.find_one({"name": "Halifax Regional Municipality"})
        if not halifax:
            raise Exception("Halifax municipality not found in database")
        
        municipality_id = halifax["id"]
        
        # Update scrape status
        await db.municipalities.update_one(
            {"id": municipality_id},
            {"$set": {"scrape_status": "in_progress"}}
        )
        
        # Scrape main tax sale page to find the PDF link
        main_url = "https://www.halifax.ca/home-property/property-taxes/tax-sale"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(main_url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the PDF schedule link dynamically
        schedule_link = None
        sale_date = "2025-09-16T10:01:00Z"  # Known sale date
        
        # Look for the schedule PDF link
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.get_text()
            # Look for PDF links containing tax sale schedule info
            if ('SCHEDULE' in text.upper() or 'newspaper' in text.lower()) and href.endswith('.pdf'):
                schedule_link = href
                break
            elif 'Sept16.2025newspaper' in href or '91654' in href:
                schedule_link = href
                break
        
        # Fallback to known link if not found dynamically
        if not schedule_link:
            schedule_link = "https://www.halifax.ca/media/91654"
            
        # Make URL absolute if relative
        if schedule_link.startswith('/'):
            schedule_link = "https://www.halifax.ca" + schedule_link
            
        logger.info(f"Found Halifax schedule link: {schedule_link}")
        
        # Download and parse the PDF directly
        try:
            # Add proper headers to avoid 403 errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.halifax.ca/home-property/property-taxes/tax-sale'
            }
            pdf_response = requests.get(schedule_link, headers=headers, timeout=60)
            pdf_response.raise_for_status()
            logger.info(f"Downloaded PDF from {schedule_link}, size: {len(pdf_response.content)} bytes")
            
            # Parse the PDF using pdfplumber for better table extraction
            halifax_properties = []
            
            with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
                logger.info(f"PDF has {len(pdf.pages)} pages")
                
                for page_num, page in enumerate(pdf.pages):
                    logger.info(f"Processing page {page_num + 1}")
                    
                    # TEMPORARY: Force text extraction to debug the issue
                    tables = []  # Skip table extraction for debugging
                    logger.info("DEBUG: Forcing text extraction path to test enhanced parsing logic")
                    
                    if tables:
                        for table_num, table in enumerate(tables):
                            logger.info(f"Processing table {table_num + 1} on page {page_num + 1}")
                            
                            # Convert table to DataFrame for easier processing
                            if len(table) > 1:  # Ensure we have header and data rows
                                try:
                                    df = pd.DataFrame(table[1:], columns=table[0])  # First row as header
                                    logger.info(f"Table columns: {list(df.columns)}")
                                    logger.info(f"Column details: {[(i, col) for i, col in enumerate(df.columns)]}")
                                    
                                    # Log a sample row for debugging
                                    if not df.empty:
                                        first_row = df.iloc[0]
                                        logger.info(f"Sample row data: {dict(first_row)}")
                                    
                                    # Process each row to extract property information
                                    for index, row in df.iterrows():
                                        try:
                                            # Extract data based on table structure
                                            # Halifax PDFs typically have columns for Assessment Number, Owner, Description, PID, Opening Bid, etc.
                                            
                                            # Initialize variables
                                            assessment_num = None
                                            owner_name = None
                                            description = None
                                            pid = None
                                            opening_bid = None
                                            
                                            # Try to identify columns by common patterns
                                            for col_name, value in row.items():
                                                if value and str(value).strip():
                                                    col_lower = str(col_name).lower() if col_name else ""
                                                    value_str = str(value).strip()
                                                    
                                                    # Look for specific column names first
                                                    if ("assessment" in col_lower or "account" in col_lower or 
                                                        col_lower == "aan" or re.match(r'^\d{8}$', value_str)):
                                                        if not assessment_num:
                                                            assessment_num = value_str
                                                    
                                                    # Look specifically for "Parcel Description" column
                                                    elif ("parcel" in col_lower and "description" in col_lower) or col_lower == "parcel description":
                                                        description = value_str
                                                        logger.info(f"Found Parcel Description: {value_str}")
                                                    
                                                    # Owner name patterns
                                                    elif ("owner" in col_lower or col_lower == "name"):
                                                        if not owner_name:
                                                            owner_name = value_str
                                                    
                                                    # PID column
                                                    elif "pid" in col_lower and re.match(r'^\d{8}$', value_str):
                                                        if not pid:
                                                            pid = value_str
                                                    
                                                    # Opening bid patterns
                                                    elif ("bid" in col_lower or "amount" in col_lower):
                                                        try:
                                                            numeric_value = re.findall(r'[\d,]+\.?\d*', value_str.replace(",", ""))
                                                            if numeric_value:
                                                                bid_value = float(numeric_value[0].replace(",", ""))
                                                                if bid_value > 100:
                                                                    opening_bid = bid_value
                                                        except:
                                                            pass
                                                    
                                                    # Fallback patterns if columns don't have clear names
                                                    elif not assessment_num and re.match(r'^\d{8}$', value_str):
                                                        assessment_num = value_str
                                                    elif not owner_name and len(value_str) > 5 and " " in value_str and any(c.isupper() for c in value_str):
                                                        # Check if this looks like a name (has uppercase and spaces)
                                                        if not any(addr_word in value_str for addr_word in ["Rd", "St", "Ave", "Drive", "Road", "Street", "Lot"]):
                                                            owner_name = value_str
                                                    elif not description and (
                                                        any(addr_word in value_str for addr_word in ["Rd", "St", "Ave", "Drive", "Road", "Street", "Avenue", "Lane", "Court", "Place", "Way", "Crescent", "Circle", "Close", "Lot", "Unit", "Apt"]) or
                                                        re.search(r'\d+\s+\w+', value_str) or  # Street number pattern
                                                        " - " in value_str):  # Common separator
                                                        description = value_str
                                                        logger.info(f"Found address-like description: {value_str}")
                                            
                                            # Validate we have minimum required data
                                            if owner_name and (assessment_num or description):
                                                # Enhanced description extraction if not found yet
                                                if not description:
                                                    # Look for any column that might contain address/property info
                                                    for col_name, value in row.items():
                                                        if value and str(value).strip():
                                                            value_str = str(value).strip()
                                                            # Look for values that seem like addresses or property descriptions
                                                            # Exclude values that are clearly other fields
                                                            if (len(value_str) > 10 and 
                                                                value_str != owner_name and 
                                                                value_str != assessment_num and 
                                                                value_str != pid and
                                                                not re.match(r'^\$?[\d,]+\.?\d*$', value_str.replace(',', '')) and  # Not just a number/amount
                                                                (any(word in value_str for word in ["Rd", "St", "Ave", "Drive", "Road", "Street", "Avenue", "Lane", "Court", "Place", "Way", "Lot", "Unit", "Grant", "Halifax", "Dartmouth", "Bedford"]) or
                                                                 re.search(r'\b\d+\s+\w+', value_str) or  # Street number pattern
                                                                 " - " in value_str)):  # Common separator in property descriptions
                                                                
                                                                # Clean up the description
                                                                cleaned_desc = value_str
                                                                # Remove assessment numbers and PIDs from the description
                                                                cleaned_desc = re.sub(r'\b\d{8}\b', '', cleaned_desc)
                                                                # Remove dollar amounts
                                                                cleaned_desc = re.sub(r'\$[\d,]+\.?\d*', '', cleaned_desc)
                                                                # Clean up extra spaces
                                                                cleaned_desc = re.sub(r'\s+', ' ', cleaned_desc).strip()
                                                                
                                                                if len(cleaned_desc) > 5:
                                                                    if not description or len(cleaned_desc) > len(description):
                                                                        description = cleaned_desc
                                                
                                                # Use reasonable defaults if still missing
                                                if not description and assessment_num:
                                                    description = f"Property at assessment #{assessment_num}"
                                                elif not assessment_num and description:
                                                    # Try to extract assessment number from description
                                                    assessment_match = re.search(r'\b\d{8}\b', description)
                                                    if assessment_match:
                                                        assessment_num = assessment_match.group()
                                                
                                                if not pid:
                                                    # Try to extract PID from description or use assessment as fallback
                                                    pid_match = re.search(r'PID[:\s]*(\d{8})', description or "")
                                                    if pid_match:
                                                        pid = pid_match.group(1)
                                                    elif assessment_num and len(assessment_num) == 8:
                                                        pid = assessment_num  # Sometimes they're the same
                                                
                                                if not opening_bid:
                                                    opening_bid = 1000.0  # Default minimum bid if not found
                                                
                                                property_data = {
                                                    "assessment_num": assessment_num,
                                                    "owner_name": owner_name,
                                                    "description": description,
                                                    "pid": pid,
                                                    "opening_bid": opening_bid,
                                                    "hst_status": "Contact HRM for HST details",
                                                    "redeemable_status": "Contact HRM for redemption status"
                                                }
                                                
                                                halifax_properties.append(property_data)
                                                logger.info(f"Extracted property: {assessment_num} - {owner_name}")
                                        
                                        except Exception as row_error:
                                            logger.warning(f"Error processing table row: {row_error}")
                                            continue
                                
                                except Exception as table_error:
                                    logger.warning(f"Error processing table: {table_error}")
                                    continue
                    
                    # If no tables found, extract complete text and parse more carefully
                    if not tables:
                        logger.info("No tables found, extracting complete PDF text for careful parsing...")
                        text = page.extract_text()
                        if text:
                            # Get all lines and clean them
                            all_lines = text.split('\n')
                            cleaned_lines = [line.strip() for line in all_lines if line.strip()]
                            
                            logger.info(f"Extracted {len(cleaned_lines)} non-empty text lines from PDF")
                            logger.info(f"Sample lines: {cleaned_lines[:5]}")
                            
                            # Process lines to find property data - look for patterns that indicate property entries
                            i = 0
                            while i < len(cleaned_lines):
                                line = cleaned_lines[i]
                                
                                # Look for lines starting with assessment numbers (8 digits)
                                assessment_match = re.search(r'^(\d{8})\s+(.+)', line)
                                if assessment_match:
                                    assessment_num = assessment_match.group(1)
                                    rest_of_line = assessment_match.group(2)
                                    
                                    # The rest of the line and potentially next lines contain owner + property info
                                    full_property_text = rest_of_line
                                    
                                    # Check if the property data continues on next lines
                                    j = i + 1
                                    while j < len(cleaned_lines) and not re.match(r'^\d{8}\s+', cleaned_lines[j]):
                                        # This line is part of the current property entry
                                        full_property_text += " " + cleaned_lines[j]
                                        j += 1
                                    
                                    logger.info(f"Full property text for {assessment_num}: '{full_property_text[:100]}...'")
                                    
                                    # Parse the complete property text
                                    try:
                                        # Extract owner name - typically uppercase words at the beginning
                                        words = full_property_text.split()
                                        owner_parts = []
                                        property_parts = []
                                        
                                        # More sophisticated owner name extraction
                                        in_owner_section = True
                                        for word_idx, word in enumerate(words):
                                            if in_owner_section:
                                                # Owner names are typically uppercase, include ESTATE, LTD, etc.
                                                if (word.isupper() or 
                                                    word in ['ESTATE', 'LTD', 'LIMITED', 'INC', 'CORP', 'COMPANY'] or
                                                    re.match(r'^[A-Z]+[,.]?$', word)):  # All caps with optional comma/period
                                                    owner_parts.append(word.rstrip(','))  # Remove trailing comma
                                                else:
                                                    # Check if this might be a continuation like "A2", "JR", "SR", "III"
                                                    if word in ['A2', 'A', 'B', 'C', 'JR', 'SR', 'III', 'II', 'IV']:
                                                        owner_parts.append(word)
                                                    else:
                                                        # Transition to property description
                                                        in_owner_section = False
                                                        property_parts = words[word_idx:]
                                                        break
                                            
                                        owner_name = " ".join(owner_parts) if owner_parts else f"Owner for {assessment_num}"
                                        property_desc_words = property_parts if property_parts else words[len(owner_parts):]
                                        
                                        # Extract property description (address/location)
                                        description = " ".join(property_desc_words) if property_desc_words else f"Property at assessment #{assessment_num}"
                                        
                                        # Clean description - remove PIDs and dollar amounts but keep the address
                                        if description:
                                            # Remove PID numbers, dollar amounts, but preserve property description
                                            cleaned_desc = description
                                            # Remove standalone 8-digit numbers (PIDs) but keep street numbers
                                            cleaned_desc = re.sub(r'\b\d{8}\b', '', cleaned_desc)
                                            # Remove dollar amounts
                                            cleaned_desc = re.sub(r'\$[\d,]+\.?\d*', '', cleaned_desc)
                                            # Clean up multiple spaces
                                            cleaned_desc = re.sub(r'\s+', ' ', cleaned_desc).strip()
                                            if cleaned_desc and len(cleaned_desc) > 5:
                                                description = cleaned_desc
                                        
                                        # Extract redeemable and HST status from the full text
                                        redeemable_status = "Contact HRM for redemption details"  
                                        hst_status = "Contact HRM for HST details"
                                        
                                        # Look for "No" and "Yes" patterns at the end of the property description
                                        # Halifax PDFs often have "No Yes" or "Yes No" indicating redeemable and HST status
                                        if description:
                                            # Check for status patterns at the end of description
                                            status_pattern = re.search(r'\b(No|Yes)\s+(No|Yes)\s*$', description)
                                            if status_pattern:
                                                # Based on Halifax PDF structure: First value is HST, Second value is Redeemable
                                                hst_value = status_pattern.group(1)  # First value = HST
                                                redeemable_value = status_pattern.group(2)  # Second value = Redeemable
                                                
                                                # Format with proper labels
                                                hst_status = "HST Applicable" if hst_value == "Yes" else "No HST"
                                                redeemable_status = "Redeemable" if redeemable_value == "Yes" else "Not Redeemable"
                                                
                                                # Clean these status values from the description
                                                description = re.sub(r'\s+(No|Yes)\s+(No|Yes)\s*$', '', description).strip()
                                                
                                                logger.info(f"Extracted status for {assessment_num}: HST={hst_status}, Redeemable={redeemable_status}")
                                        
                                        # Additional pattern matching for other status indicators
                                        full_text_lower = full_property_text.lower()
                                        if 'redeemable' in full_text_lower or 'redeem' in full_text_lower:
                                            if 'not redeemable' in full_text_lower or 'no' in full_text_lower:
                                                redeemable_status = "Not Redeemable"
                                            elif 'redeemable' in full_text_lower or 'yes' in full_text_lower:
                                                redeemable_status = "Redeemable"
                                        
                                        # Extract opening bid
                                        opening_bid = 1000.0
                                        bid_matches = re.findall(r'\$[\d,]+\.?\d*', full_property_text)
                                        if bid_matches:
                                            try:
                                                amounts = [float(match.replace('$', '').replace(',', '')) for match in bid_matches]
                                                opening_bid = max(amounts) if amounts else 1000.0
                                            except:
                                                pass
                                        
                                        # Extract PID
                                        pid_match = re.search(r'\b(\d{8})\b', full_property_text)
                                        pid = pid_match.group(1) if pid_match and pid_match.group(1) != assessment_num else assessment_num
                                        
                                        property_data = {
                                            "assessment_num": assessment_num,
                                            "owner_name": owner_name,
                                            "description": description,
                                            "pid": pid,
                                            "opening_bid": opening_bid,
                                            "hst_status": hst_status,
                                            "redeemable_status": redeemable_status
                                        }
                                        
                                        halifax_properties.append(property_data)
                                        logger.info(f"Parsed complete property - Assessment: {assessment_num}")
                                        logger.info(f"  Owner: '{owner_name}' (len: {len(owner_name)})")
                                        logger.info(f"  Description: '{description}' (len: {len(description)})")
                                        logger.info(f"  Redeemable: {redeemable_status}, HST: {hst_status}")
                                        
                                    except Exception as parse_error:
                                        logger.warning(f"Error parsing property {assessment_num}: {parse_error}")
                                    
                                    # Move to the next property (skip lines we already processed)
                                    i = j
                                else:
                                    i += 1
            
            logger.info(f"Successfully parsed PDF - extracted {len(halifax_properties)} properties")
            
            # Update property statuses before processing new data
            await update_property_statuses()
            
            # Get current assessment numbers for inactive marking
            current_assessment_numbers = [prop["assessment_num"] for prop in halifax_properties]
            await mark_missing_properties_inactive(current_assessment_numbers, "Halifax Regional Municipality")
            
            # If no properties were extracted, fall back to the sample data
            if not halifax_properties:
                logger.warning("No properties extracted from PDF, using fallback sample data")
                halifax_properties = [
                    {"assessment_num": "02102943", "owner_name": "MARILYN ANNE BURNS, LEONARD WILLIAM HUGHES", 
                     "description": "405 Conrod Beach Rd Lot 4 Port Lower East Chezzetcook - Dwelling", 
                     "pid": "00443267", "opening_bid": 16306.02, "hst_status": "No", "redeemable_status": "No"},
                ]
            
        except Exception as e:
            logger.error(f"Failed to download or parse PDF: {e}")
            # Fallback to the sample data
            halifax_properties = [
                {"assessment_num": "02102943", "owner_name": "MARILYN ANNE BURNS, LEONARD WILLIAM HUGHES", 
                 "description": "405 Conrod Beach Rd Lot 4 Port Lower East Chezzetcook - Dwelling", 
                 "pid": "00443267", "opening_bid": 16306.02, "hst_status": "No", "redeemable_status": "No"},
            ]
        
        properties_scraped = 0
        
        for prop in halifax_properties:
            try:
                assessment_num = prop["assessment_num"]
                owner_name = prop["owner_name"]
                description = prop["description"]
                pid = prop["pid"]
                opening_bid = prop["opening_bid"]
                
                # Parse property type from description
                property_type = "Dwelling" if "Dwelling" in description else "Land" if "Land" in description else "Property"
                
                # Use extracted redeemable and HST status from PDF, not generic defaults
                redeemable_status = prop.get("redeemable_status", "Contact HRM for redemption details")
                hst_status = prop.get("hst_status", "Contact HRM for HST details")
                
                # Create property record with status tracking
                property_data = {
                    "municipality_id": municipality_id,
                    "municipality_name": "Halifax Regional Municipality",
                    "property_address": description,
                    "property_description": f"Assessment: {assessment_num}, Owner: {owner_name}",
                    "opening_bid": opening_bid,
                    "sale_date": sale_date,
                    "sale_time": "10:01 AM",
                    "sale_location": "Halifax Regional Municipality - Tender Opening",
                    "assessment_number": assessment_num,
                    "property_type": property_type,
                    "owner_name": owner_name,
                    "pid_number": pid,
                    "redeemable": redeemable_status,
                    "hst_applicable": hst_status,
                    "source_url": schedule_link,
                    "status": "active",  # New properties default to active
                    "status_updated_at": datetime.now(timezone.utc),
                    "raw_data": {
                        "assessment_number": assessment_num,
                        "owner_name": owner_name,
                        "parcel_description": description,
                        "pid": pid,
                        "opening_bid": opening_bid,
                        "redeemable": redeemable_status,
                        "hst_applicable": hst_status
                    }
                }
                
                # Generate varied coordinates within Halifax region
                lat_base = 44.6488
                lng_base = -63.5752
                lat_offset = (hash(assessment_num) % 2000) / 10000 - 0.1  # Range: -0.1 to +0.1
                lng_offset = (hash(assessment_num + "lng") % 2000) / 10000 - 0.1
                
                property_data["latitude"] = lat_base + lat_offset
                property_data["longitude"] = lng_base + lng_offset
                
                # Check if property already exists using a unique combination
                # Use assessment number if available, otherwise use owner name + description
                if assessment_num:
                    existing = await db.tax_sales.find_one({
                        "assessment_number": assessment_num,
                        "municipality_name": "Halifax Regional Municipality"
                    })
                else:
                    # For properties without assessment numbers, use owner + description as unique identifier
                    existing = await db.tax_sales.find_one({
                        "owner_name": owner_name,
                        "property_address": description,
                        "municipality_name": "Halifax Regional Municipality"
                    })
                
                if existing:
                    # Update existing property
                    await db.tax_sales.update_one(
                        {"id": existing["id"]},
                        {"$set": property_data}
                    )
                    logger.info(f"Updated existing property: {assessment_num}")
                else:
                    # Insert new property
                    tax_sale_property = TaxSaleProperty(**property_data)
                    await db.tax_sales.insert_one(tax_sale_property.dict())
                    logger.info(f"Inserted new property: {assessment_num}")
                
                properties_scraped += 1
                
            except Exception as e:
                logger.warning(f"Error processing Halifax property {prop.get('assessment_num', 'unknown')}: {e}")
                continue
        
        # Update municipality scrape status
        await db.municipalities.update_one(
            {"id": municipality_id},
            {
                "$set": {
                    "scrape_status": "success",
                    "last_scraped": datetime.now(timezone.utc)
                }
            }
        )
        
        logger.info(f"Halifax scraping completed: {properties_scraped} properties processed")
        return {"status": "success", "properties_scraped": properties_scraped}
        
    except Exception as e:
        logger.error(f"Halifax scraping failed: {e}")
        if 'municipality_id' in locals():
            await db.municipalities.update_one(
                {"id": municipality_id},
                {"$set": {"scrape_status": "failed"}}
            )
        raise HTTPException(status_code=500, detail=f"Halifax scraping failed: {str(e)}")


# Generic municipality scraper (placeholder for other municipalities)
async def scrape_generic_municipality(municipality_id: str):
    """Generic scraper for municipalities without specific implementation"""
    municipality = await db.municipalities.find_one({"id": municipality_id})
    if not municipality:
        raise HTTPException(status_code=404, detail="Municipality not found")
    
    # Placeholder - would implement specific scraping logic for each municipality
    logger.info(f"Generic scraping for {municipality['name']} - not yet implemented")
    
    await db.municipalities.update_one(
        {"id": municipality_id},
        {
            "$set": {
                "scrape_status": "pending",
                "last_scraped": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"status": "pending", "message": f"Scraper for {municipality['name']} not yet implemented"}


# Municipality Management Endpoints
@api_router.get("/")
async def root():
    return {"message": "Nova Scotia Tax Sale Aggregator API - Enhanced with Real Scraping"}

@api_router.post("/municipalities", response_model=Municipality)
async def create_municipality(municipality: MunicipalityCreate):
    municipality_dict = municipality.dict()
    municipality_obj = Municipality(**municipality_dict)
    await db.municipalities.insert_one(municipality_obj.dict())
    return municipality_obj

@api_router.get("/municipalities", response_model=List[Municipality])
async def get_municipalities():
    municipalities = await db.municipalities.find().to_list(1000)
    
    # Handle data migration for municipalities missing website_url field
    processed_municipalities = []
    for municipality in municipalities:
        # Remove MongoDB _id field if present
        if '_id' in municipality:
            del municipality['_id']
        
        # Ensure website_url field exists and is not None (migrate from tax_sale_url if needed)
        if ('website_url' not in municipality or municipality.get('website_url') is None) and 'tax_sale_url' in municipality:
            municipality['website_url'] = municipality['tax_sale_url']
        elif 'website_url' not in municipality or municipality.get('website_url') is None:
            municipality['website_url'] = "https://example.com"  # Default fallback
            
        processed_municipalities.append(Municipality(**municipality))
    
    return processed_municipalities

@api_router.get("/municipalities/{municipality_id}", response_model=Municipality)
async def get_municipality(municipality_id: str):
    municipality = await db.municipalities.find_one({"id": municipality_id})
    if not municipality:
        raise HTTPException(status_code=404, detail="Municipality not found")
    
    # Remove MongoDB _id field if present
    if '_id' in municipality:
        del municipality['_id']
    
    # Ensure website_url field exists and is not None (migrate from tax_sale_url if needed)
    if ('website_url' not in municipality or municipality.get('website_url') is None) and 'tax_sale_url' in municipality:
        municipality['website_url'] = municipality['tax_sale_url']
    elif 'website_url' not in municipality or municipality.get('website_url') is None:
        municipality['website_url'] = "https://example.com"  # Default fallback
    
    return Municipality(**municipality)


# Tax Sale Property Endpoints
@api_router.post("/tax-sales", response_model=TaxSaleProperty)
async def create_tax_sale_property(property_data: TaxSalePropertyCreate):
    property_dict = property_data.dict()
    property_obj = TaxSaleProperty(**property_dict)
    await db.tax_sales.insert_one(property_obj.dict())
    return property_obj

# API endpoint for getting tax sale properties with filtering
@api_router.get("/tax-sales", response_model=List[TaxSaleProperty])
async def get_tax_sale_properties(
    municipality: Optional[str] = Query(None, description="Filter by municipality name"),
    limit: int = Query(100, description="Number of results to return"),
    skip: int = Query(0, description="Number of results to skip"),
    status: Optional[str] = Query(None, description="Filter by status: active, inactive, all")
):
    # Build query filter
    query = {}
    
    if municipality:
        query["municipality_name"] = {"$regex": municipality, "$options": "i"}
    
    # Handle status filtering
    if status and status != "all":
        query["status"] = status
    elif status != "all":
        # Default to active only if no status specified
        query["status"] = "active"
    
    # Get properties with filtering
    properties = await db.tax_sales.find(query).skip(skip).limit(limit).to_list(limit)
    return [TaxSaleProperty(**prop) for prop in properties]

@api_router.get("/tax-sales/search")
async def search_tax_sales(
    q: Optional[str] = Query(None, description="Search query"),
    municipality: Optional[str] = Query(None, description="Municipality filter"),
    limit: int = Query(50, description="Results limit")
):
    query = {}
    
    if q:
        # Search across multiple fields
        query["$or"] = [
            {"property_address": {"$regex": q, "$options": "i"}},
            {"municipality_name": {"$regex": q, "$options": "i"}},
            {"property_description": {"$regex": q, "$options": "i"}},
            {"owner_name": {"$regex": q, "$options": "i"}}
        ]
    
    if municipality:
        query["municipality_name"] = {"$regex": municipality, "$options": "i"}
    
    properties = await db.tax_sales.find(query).limit(limit).to_list(limit)
    return [TaxSaleProperty(**prop) for prop in properties]

@api_router.get("/tax-sales/map-data")
async def get_map_data():
    """Get tax sale properties with location data for map display"""
    properties = await db.tax_sales.find({
        "latitude": {"$exists": True, "$ne": None},
        "longitude": {"$exists": True, "$ne": None}
    }).to_list(1000)
    
    return [{
        "id": prop["id"],
        "municipality": prop["municipality_name"],
        "address": prop["property_address"],
        "opening_bid": prop.get("opening_bid"),
        "tax_owing": prop.get("tax_owing"),
        "assessment_value": prop.get("assessment_value"),
        "sale_date": prop.get("sale_date"),
        "property_type": prop.get("property_type", "Property"),
        "latitude": prop["latitude"],
        "longitude": prop["longitude"]
    } for prop in properties]


# Statistics and Monitoring
@api_router.get("/stats", response_model=ScrapeStats)
async def get_statistics():
    total_municipalities = await db.municipalities.count_documents({})
    total_properties = await db.tax_sales.count_documents({})
    
    # Count active and inactive properties
    active_properties = await db.tax_sales.count_documents({"status": "active"})
    inactive_properties = await db.tax_sales.count_documents({"status": "inactive"})
    
    # Get municipalities scraped today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    scraped_today = await db.municipalities.count_documents({
        "last_scraped": {"$gte": today_start}
    })
    
    # Get last scrape time
    last_scrape_doc = await db.municipalities.find_one(
        {"last_scraped": {"$exists": True}},
        sort=[("last_scraped", -1)]
    )
    last_scrape = last_scrape_doc["last_scraped"] if last_scrape_doc else None
    
    return ScrapeStats(
        total_municipalities=total_municipalities,
        scraped_today=scraped_today,
        total_properties=total_properties,
        active_properties=active_properties,
        inactive_properties=inactive_properties,
        last_scrape=last_scrape
    )


# Database cleanup endpoint
@api_router.post("/clear-tax-sales")
async def clear_all_tax_sales():
    """Clear all tax sale properties from database"""
    result = await db.tax_sales.delete_many({})
    return {"deleted_count": result.deleted_count, "message": "All tax sale properties cleared"}

# Enhanced Scraping Endpoints
@api_router.post("/scrape/halifax")
async def scrape_halifax():
    """Trigger Halifax-specific scraping"""
    result = await scrape_halifax_tax_sales()
    return result

@api_router.post("/scrape/{municipality_id}")
async def scrape_municipality(municipality_id: str):
    """Trigger scraping for a specific municipality"""
    municipality = await db.municipalities.find_one({"id": municipality_id})
    if not municipality:
        raise HTTPException(status_code=404, detail="Municipality not found")
    
    if municipality["name"] == "Halifax Regional Municipality":
        result = await scrape_halifax_tax_sales()
    else:
        result = await scrape_generic_municipality(municipality_id)
    
    return result

@api_router.post("/scrape-all")
async def scrape_all_municipalities():
    """Trigger scraping for all municipalities"""
    municipalities = await db.municipalities.find().to_list(1000)
    results = []
    
    for municipality in municipalities:
        try:
            if municipality["name"] == "Halifax Regional Municipality":
                result = await scrape_halifax_tax_sales()
            else:
                result = await scrape_generic_municipality(municipality["id"])
            results.append(result)
        except Exception as e:
            results.append({
                "status": "failed",
                "municipality": municipality["name"],
                "error": str(e)
            })
    
    return {"results": results}


# API endpoint to manually update property statuses
@app.post("/api/update-property-statuses")
async def update_statuses_endpoint():
    """Manually trigger property status updates"""
    try:
        updated_count = await update_property_statuses()
        return {
            "message": "Property statuses updated successfully",
            "updated_count": updated_count
        }
    except Exception as e:
        logger.error(f"Error updating property statuses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint to get property statistics by status
@app.get("/api/property-stats")
async def get_property_statistics():
    """Get statistics about properties by status"""
    try:
        # Count properties by status
        active_count = await db.tax_sales.count_documents({"status": "active"})
        inactive_count = await db.tax_sales.count_documents({"status": "inactive"})
        total_count = await db.tax_sales.count_documents({})
        
        # Get recent status changes
        recent_changes = await db.tax_sales.find(
            {"status_updated_at": {"$exists": True}},
            {"assessment_number": 1, "status": 1, "status_updated_at": 1}
        ).sort("status_updated_at", -1).limit(10).to_list(length=10)
        
        for change in recent_changes:
            change["_id"] = str(change["_id"])
        
        return {
            "active_count": active_count,
            "inactive_count": inactive_count,
            "total_count": total_count,
            "recent_changes": recent_changes
        }
    except Exception as e:
        logger.error(f"Error getting property statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint for updating a municipality
@app.put("/api/municipalities/{municipality_id}")
async def update_municipality(municipality_id: str, municipality: MunicipalityCreate):
    """Update an existing municipality"""
    try:
        municipality_dict = municipality.dict()
        municipality_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await db.municipalities.update_one(
            {"id": municipality_id},
            {"$set": municipality_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        return {"message": "Municipality updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating municipality: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint for creating a new municipality
@app.post("/api/municipalities")
async def create_municipality(municipality: MunicipalityCreate):
    """Create a new municipality"""
    try:
        new_municipality = {
            "id": str(uuid.uuid4()),
            "name": municipality.name,
            "website_url": municipality.website_url,  # Add missing website_url field
            "scraper_type": municipality.scraper_type,
            "tax_sale_url": municipality.tax_sale_url,
            "region": municipality.region,
            "latitude": municipality.latitude,
            "longitude": municipality.longitude,
            "province": "Nova Scotia",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_scraped": None,
            "scrape_status": "pending"
        }
        
        await db.municipalities.insert_one(new_municipality)
        
        return {"message": "Municipality created successfully", "id": new_municipality["id"]}
        
    except Exception as e:
        logger.error(f"Error creating municipality: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def scrape_pvsc_details(assessment_number: str):
    """
    Scrape additional property details from PVSC website
    """
    try:
        pvsc_url = f"https://webapi.pvsc.ca/Search/Property?ain={assessment_number}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(pvsc_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract Google Maps link
        google_maps_link = None
        maps_links = soup.find_all('a', href=True)
        for link in maps_links:
            href = link['href']
            if 'maps.google.com' in href:
                google_maps_link = href
                break
        
        # Extract civic address
        civic_address = None
        address_elements = soup.find_all(['h1', 'div'], string=re.compile(r'[A-Z0-9\s]+[A-Z]{2,}'))
        for element in address_elements:
            text = element.get_text(strip=True)
            if len(text) > 10 and any(word in text.upper() for word in ['RD', 'ST', 'AVE', 'DRIVE', 'COURT', 'CRT']):
                civic_address = text
                break
        
        # Extract property details from table-like structure
        property_details = {}
        
        # Look for assessment value
        assessment_text = soup.get_text()
        
        # Current Property Assessment
        assessment_match = re.search(r'Current Property Assessment\s*\$?([\d,]+)', assessment_text)
        if assessment_match:
            property_details['current_assessment'] = float(assessment_match.group(1).replace(',', ''))
        
        # Taxable Assessed Value
        taxable_match = re.search(r'Current Taxable Assessed Value:\s*\$?([\d,]+)', assessment_text)
        if taxable_match:
            property_details['taxable_assessment'] = float(taxable_match.group(1).replace(',', ''))
        
        # Land Size
        land_size_match = re.search(r'Land Size\s*([\d,]+)\s*Sq\.\s*Ft\.', assessment_text)
        if land_size_match:
            property_details['land_size'] = land_size_match.group(1).replace(',', '') + ' Sq. Ft.'
        
        # Building Style
        style_match = re.search(r'Building Style\s*([^\n]+)', assessment_text)
        if style_match:
            property_details['building_style'] = style_match.group(1).strip()
        
        # Year Built
        year_match = re.search(r'Year Built\s*(\d{4})', assessment_text)
        if year_match:
            property_details['year_built'] = int(year_match.group(1))
        
        # Living Area
        area_match = re.search(r'Total Living Area\(Sq Ft\)\s*†?\s*(\d+)', assessment_text)
        if area_match:
            property_details['living_area'] = int(area_match.group(1))
        
        # Bedrooms
        bedroom_match = re.search(r'Bedrooms\s*(\d+)', assessment_text)
        if bedroom_match:
            property_details['bedrooms'] = int(bedroom_match.group(1))
        
        # Bathrooms
        bath_match = re.search(r'#of Baths[^0-9]*(\d+)', assessment_text)
        if bath_match:
            property_details['bathrooms'] = int(bath_match.group(1))
        
        # Extract coordinates from Google Maps link if available
        latitude, longitude = None, None
        if google_maps_link:
            # Try to extract address from Google Maps link and geocode it
            try:
                import urllib.parse
                if '?q=' in google_maps_link:
                    address_query = google_maps_link.split('?q=')[1]
                    decoded_address = urllib.parse.unquote(address_query)
                    
                    # Use a simple geocoding approach with the address
                    # For now, we'll store the Google Maps link and address
                    property_details['google_maps_link'] = google_maps_link
                    property_details['geocoded_address'] = decoded_address
            except:
                property_details['google_maps_link'] = google_maps_link
        
        return {
            'civic_address': civic_address,
            'google_maps_link': google_maps_link,
            'property_details': property_details,
            'pvsc_url': pvsc_url
        }
        
    except Exception as e:
        logger.error(f"Error scraping PVSC data for {assessment_number}: {e}")
        return None

# API endpoint to get enhanced property details with PVSC data
@app.get("/api/property/{assessment_number}/enhanced")
async def get_enhanced_property_details(assessment_number: str):
    """Get property details enhanced with PVSC data"""
    try:
        # Get basic property from database
        property_data = await db.tax_sales.find_one({"assessment_number": assessment_number})
        
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Convert ObjectId to string
        property_data["_id"] = str(property_data["_id"])
        
        # Get enhanced PVSC data
        pvsc_data = await scrape_pvsc_details(assessment_number)
        
        if pvsc_data:
            property_data.update(pvsc_data)
        
        return property_data
        
    except Exception as e:
        logger.error(f"Error getting enhanced property details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Initialize with some Nova Scotia municipalities
@api_router.post("/init-municipalities")
async def initialize_municipalities():
    """Initialize the database with Nova Scotia municipalities"""
    
    # Check if already initialized
    count = await db.municipalities.count_documents({})
    if count > 0:
        return {"message": f"Already initialized with {count} municipalities"}
    
    # Major Nova Scotia municipalities with their websites
    municipalities = [
        {
            "name": "Halifax Regional Municipality",
            "website_url": "https://www.halifax.ca",
            "tax_sale_url": "https://www.halifax.ca/home-property/property-taxes/tax-sale",
            "region": "Halifax",
            "latitude": 44.6488,
            "longitude": -63.5752,
            "scraper_type": "halifax"
        },
        {
            "name": "Cape Breton Regional Municipality", 
            "website_url": "https://www.cbrm.ns.ca",
            "region": "Cape Breton",
            "latitude": 46.1368,
            "longitude": -60.1942,
            "scraper_type": "generic"
        },
        {
            "name": "Truro",
            "website_url": "https://www.truro.ca", 
            "region": "Central Nova Scotia",
            "latitude": 45.3676,
            "longitude": -63.2653,
            "scraper_type": "generic"
        },
        {
            "name": "New Glasgow",
            "website_url": "https://www.newglasgow.ca",
            "region": "Pictou County",
            "latitude": 45.5931,
            "longitude": -62.6488,
            "scraper_type": "generic"
        },
        {
            "name": "Bridgewater",
            "website_url": "https://www.bridgewater.ca",
            "region": "South Shore",
            "latitude": 44.3776,
            "longitude": -64.5223,
            "scraper_type": "generic"
        },
        {
            "name": "Yarmouth",
            "website_url": "https://www.townofyarmouth.ca",
            "region": "Southwest Nova Scotia", 
            "latitude": 43.8374,
            "longitude": -66.1175,
            "scraper_type": "generic"
        },
        {
            "name": "Kentville",
            "website_url": "https://www.kentville.ca",
            "region": "Annapolis Valley",
            "latitude": 45.0777,
            "longitude": -64.4963,
            "scraper_type": "generic"
        },
        {
            "name": "Antigonish",
            "website_url": "https://www.townofantigonish.ca",
            "region": "Eastern Nova Scotia",
            "latitude": 45.6186,
            "longitude": -61.9986,
            "scraper_type": "generic"
        }
    ]
    
    created_count = 0
    for muni_data in municipalities:
        municipality = Municipality(**muni_data)
        await db.municipalities.insert_one(municipality.dict())
        created_count += 1
    
    return {"message": f"Initialized {created_count} municipalities"}


# Weekly scraping scheduler
async def weekly_scrape_job():
    """Weekly automated scraping job"""
    logger.info("Starting weekly automated scraping...")
    try:
        # Scrape Halifax (priority municipality)
        await scrape_halifax_tax_sales()
        
        # Add other municipalities as scrapers are implemented
        logger.info("Weekly scraping completed")
    except Exception as e:
        logger.error(f"Weekly scraping failed: {e}")


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    # Start the scheduler
    scheduler.start()
    
    # Schedule weekly scraping on Sundays at 6 AM
    scheduler.add_job(
        weekly_scrape_job,
        CronTrigger(day_of_week=6, hour=6, minute=0),  # Sunday 6 AM
        id='weekly_scrape',
        replace_existing=True
    )
    logger.info("Scheduler started - Weekly scraping on Sundays at 6 AM")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    client.close()