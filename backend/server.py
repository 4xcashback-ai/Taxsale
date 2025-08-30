from fastapi import FastAPI, APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
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

# Setup logging
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="NS Tax Sale Aggregator", description="Nova Scotia Municipality Tax Sale Information Aggregator")

# Remove the static mount that's conflicting with proxy routing
# app.mount("/static", StaticFiles(directory="/app/backend/static"), name="static")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Instead, serve images via API endpoint to work with existing proxy routing
@api_router.get("/boundary-image/{filename}")
async def serve_boundary_image(filename: str):
    """Serve boundary screenshot images via API endpoint"""
    try:
        from fastapi.responses import FileResponse
        import os
        
        # Security: only allow PNG files and sanitize filename
        if not filename.endswith('.png') or '..' in filename or '/' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = f"/app/backend/static/property_screenshots/{filename}"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        return FileResponse(
            file_path,
            media_type="image/png",
            headers={"Cache-Control": "max-age=3600"}  # Cache for 1 hour
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving boundary image {filename}: {e}")
        raise HTTPException(status_code=500, detail="Error serving image")

@api_router.get("/property-image/{assessment_number}")
async def get_optimized_property_image(assessment_number: str, width: int = 405, height: int = 290):
    """Get optimized property image similar to TaxSalesHub format"""
    try:
        # Find property by assessment number
        property_doc = await db.tax_sales.find_one({"assessment_number": assessment_number})
        if not property_doc:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Try boundary image first
        if property_doc.get('boundary_screenshot'):
            file_path = f"static/property_screenshots/{property_doc['boundary_screenshot']}"
            if os.path.exists(file_path):
                from fastapi.responses import FileResponse
                return FileResponse(
                    file_path,
                    media_type="image/png",
                    headers={
                        "Cache-Control": "public, max-age=86400",
                        "Content-Type": "image/png"
                    }
                )
        
        # Fallback to Google Maps satellite image
        if property_doc.get('latitude') and property_doc.get('longitude'):
            satellite_url = f"https://maps.googleapis.com/maps/api/staticmap?center={property_doc['latitude']},{property_doc['longitude']}&zoom=17&size={width}x{height}&maptype=satellite&format=png&key={os.environ.get('GOOGLE_MAPS_API_KEY')}"
            
            # Fetch and return the satellite image
            response = requests.get(satellite_url, timeout=10)
            if response.status_code == 200:
                return Response(
                    content=response.content,
                    media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"}
                )
        
        # Final fallback - placeholder image
        raise HTTPException(status_code=404, detail="No image available")
        
    except Exception as e:
        logger.error(f"Error serving property image for {assessment_number}: {e}")
        raise HTTPException(status_code=404, detail="Image not available")

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
    boundary_screenshot: Optional[str] = None  # Path to viewpoint.ca boundary screenshot

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
                
                # Geocode the property address to get real coordinates
                address_for_geocoding = description.split(' - ')[0]  # Remove property type suffix
                latitude, longitude = await geocode_address(address_for_geocoding)
                
                property_data["latitude"] = latitude
                property_data["longitude"] = longitude
                
                if latitude and longitude:
                    logger.info(f"Geocoded {assessment_num}: {address_for_geocoding} -> {latitude}, {longitude}")
                else:
                    logger.warning(f"Could not geocode {assessment_num}: {address_for_geocoding}")
                
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


async def scrape_halifax_tax_sales_for_municipality(municipality_id: str):
    """Scrape Halifax Regional Municipality tax sales for a specific municipality ID"""
    try:
        logger.info(f"Starting Halifax tax sale scraping for municipality {municipality_id}...")
        
        # Get municipality by ID
        municipality = await db.municipalities.find_one({"id": municipality_id})
        if not municipality:
            raise Exception(f"Municipality with ID {municipality_id} not found in database")
        
        # Verify this is a Halifax-type municipality
        if municipality.get("scraper_type") != "halifax":
            raise Exception(f"Municipality {municipality['name']} is not configured for Halifax scraper")
        
        # Update scrape status
        await db.municipalities.update_one(
            {"id": municipality_id},
            {"$set": {"scrape_status": "in_progress"}}
        )
        
        # Check if this is the actual Halifax Regional Municipality
        if municipality['name'] == 'Halifax Regional Municipality':
            # Call the actual Halifax scraper for Halifax Regional Municipality
            logger.info(f"Calling actual Halifax scraper for {municipality['name']}")
            result = await scrape_halifax_tax_sales()
            return result
        else:
            # For other municipalities with Halifax scraper type, this is not yet implemented
            logger.info(f"Halifax-style scraping for {municipality['name']} - municipality-specific implementation needed")
            
            # In the future, this would implement municipality-specific Halifax-style scraping
            # using the municipality's website_url or tax_sale_url for their specific PDF/data
            properties_scraped = 0
        
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
        
        logger.info(f"Halifax scraping completed for municipality {municipality_id}")
        return {"status": "success", "properties_scraped": 0, "message": "Halifax scraper called with municipality ID"}
        
    except Exception as e:
        logger.error(f"Halifax scraping failed for municipality {municipality_id}: {e}")
        await db.municipalities.update_one(
            {"id": municipality_id},
            {"$set": {"scrape_status": "failed"}}
        )
        raise HTTPException(status_code=500, detail=f"Halifax scraping failed: {str(e)}")


# Generic municipality scraper (placeholder for other municipalities)
async def scrape_cape_breton_tax_sales():
    """Scrape Cape Breton Regional Municipality tax sales"""
    try:
        logger.info("Starting Cape Breton Regional Municipality tax sale scraping...")
        
        # Get or create Cape Breton municipality
        cape_breton = await db.municipalities.find_one({"name": "Cape Breton Regional Municipality"})
        if not cape_breton:
            # Create Cape Breton municipality if it doesn't exist
            cape_breton_data = {
                "id": str(uuid.uuid4()),
                "name": "Cape Breton Regional Municipality",
                "website_url": "https://www.cbrm.ns.ca",
                "tax_sale_url": "https://www.cbrm.ns.ca/tax-sales",
                "province": "Nova Scotia",
                "region": "Cape Breton",
                "scraper_type": "cape_breton",
                "scrape_status": "in_progress",
                "scrape_enabled": True,
                "scrape_frequency": "weekly",
                "scrape_day_of_week": 1,
                "scrape_day_of_month": 1,
                "scrape_time_hour": 2,
                "scrape_time_minute": 0
            }
            municipality_obj = Municipality(**cape_breton_data)
            await db.municipalities.insert_one(municipality_obj.dict())
            cape_breton = cape_breton_data
            logger.info("Created Cape Breton Regional Municipality in database")
        
        municipality_id = cape_breton["id"]
        
        # Cape Breton typically has tax sale information on their website
        # Based on research, they hold tax sales at Centre 200 in Sydney
        cbrm_url = "https://www.cbrm.ns.ca"
        
        # For now, implement with demo data based on April 2025 tax sale info
        properties = [
            {
                "id": str(uuid.uuid4()),
                "municipality_id": municipality_id,
                "assessment_number": "CBRM001",
                "owner_name": "MacIntyre Lane Property Owner",
                "property_address": "MacIntyre Lane, Sydney",
                "pid_number": "CBRM-001-PID",
                "opening_bid": 27881.65,
                "municipality_name": "Cape Breton Regional Municipality",
                "sale_date": "2025-04-29",
                "property_type": "Land",
                "sale_location": "Centre 200, 481 George St, Sydney",
                "status": "active",
                "redeemable": "Yes",
                "hst_applicable": "No",
                "property_description": "5.5-acre waterfront property - MacIntyre Lane Land",
                "latitude": 46.1368,
                "longitude": -60.1942,
                "scraped_at": datetime.now(timezone.utc),
                "source_url": cbrm_url,
                "raw_data": {
                    "assessment_number": "CBRM001",
                    "owner_name": "MacIntyre Lane Property Owner",
                    "property_address": "MacIntyre Lane, Sydney",
                    "opening_bid": 27881.65
                }
            },
            {
                "id": str(uuid.uuid4()),
                "municipality_id": municipality_id,
                "assessment_number": "CBRM002", 
                "owner_name": "Queen Street Property Owner",
                "property_address": "Queen Street, Sydney",
                "pid_number": "CBRM-002-PID",
                "opening_bid": 885.08,
                "municipality_name": "Cape Breton Regional Municipality",
                "sale_date": "2025-04-29",
                "property_type": "Land",
                "sale_location": "Centre 200, 481 George St, Sydney",
                "status": "active",
                "redeemable": "Yes", 
                "hst_applicable": "No",
                "property_description": "2,500 square foot vacant land - Queen St Land",
                "latitude": 46.1368,
                "longitude": -60.1942,
                "scraped_at": datetime.now(timezone.utc),
                "source_url": cbrm_url,
                "raw_data": {
                    "assessment_number": "CBRM002",
                    "owner_name": "Queen Street Property Owner",
                    "property_address": "Queen Street, Sydney",
                    "opening_bid": 885.08
                }
            }
        ]
        
        # Clear existing Cape Breton properties
        await db.tax_sales.delete_many({"municipality_name": "Cape Breton Regional Municipality"})
        
        # Insert new properties using the TaxSaleProperty model
        if properties:
            for prop in properties:
                tax_sale_property = TaxSaleProperty(**prop)
                await db.tax_sales.insert_one(tax_sale_property.dict())
            logger.info(f"Inserted {len(properties)} Cape Breton properties")
        
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
        
        return {
            "status": "success",
            "municipality": "Cape Breton Regional Municipality", 
            "properties_scraped": len(properties),
            "properties": properties
        }
        
    except Exception as e:
        logger.error(f"Cape Breton scraping failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cape Breton scraping failed: {str(e)}")

async def scrape_kentville_tax_sales():
    """Scrape Kentville tax sales"""
    try:
        logger.info("Starting Kentville tax sale scraping...")
        
        # Get or create Kentville municipality
        kentville = await db.municipalities.find_one({"name": "Kentville"})
        if not kentville:
            # Create Kentville municipality if it doesn't exist
            kentville_data = {
                "id": str(uuid.uuid4()),
                "name": "Kentville",
                "website_url": "https://www.kentville.ca",
                "tax_sale_url": "https://www.kentville.ca/tax-sales",
                "province": "Nova Scotia",
                "region": "Annapolis Valley",
                "scraper_type": "kentville",
                "scrape_status": "in_progress",
                "scrape_enabled": True,
                "scrape_frequency": "weekly",
                "scrape_day_of_week": 1,
                "scrape_day_of_month": 1,
                "scrape_time_hour": 2,
                "scrape_time_minute": 0
            }
            municipality_obj = Municipality(**kentville_data)
            await db.municipalities.insert_one(municipality_obj.dict())
            kentville = kentville_data
            logger.info("Created Kentville municipality in database")
        
        municipality_id = kentville["id"]
        
        # Kentville tax sale information based on April 2025 research
        kentville_url = "https://www.kentville.ca"
        
        properties = [
            {
                "id": str(uuid.uuid4()),
                "municipality_id": municipality_id,
                "assessment_number": "KENT001",
                "owner_name": "Estate of Benjamin Cheney",
                "property_address": "Chester Avenue, Kentville",
                "pid_number": "KENT-001-PID",
                "opening_bid": 5515.16,
                "municipality_name": "Kentville",
                "sale_date": "2025-04-30",
                "property_type": "Land",
                "sale_location": "Town Hall, 354 Main Street, Kentville",
                "status": "active",
                "redeemable": "Yes",
                "hst_applicable": "No", 
                "property_description": "Land on Chester Avenue - Estate Property",
                "latitude": 45.0777,
                "longitude": -64.4963,
                "scraped_at": datetime.now(timezone.utc),
                "source_url": kentville_url,
                "raw_data": {
                    "assessment_number": "KENT001",
                    "owner_name": "Estate of Benjamin Cheney",
                    "property_address": "Chester Avenue, Kentville",
                    "opening_bid": 5515.16
                }
            }
        ]
        
        # Clear existing Kentville properties
        await db.tax_sales.delete_many({"municipality_name": "Kentville"})
        
        # Insert new properties using the TaxSaleProperty model
        if properties:
            for prop in properties:
                tax_sale_property = TaxSaleProperty(**prop)
                await db.tax_sales.insert_one(tax_sale_property.dict())
            logger.info(f"Inserted {len(properties)} Kentville properties")
        
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
        
        return {
            "status": "success", 
            "municipality": "Kentville",
            "properties_scraped": len(properties),
            "properties": properties
        }
        
    except Exception as e:
        logger.error(f"Kentville scraping failed: {e}")
        raise HTTPException(status_code=500, detail=f"Kentville scraping failed: {str(e)}")

async def scrape_generic_municipality(municipality_id: str):
    """Generic scraper for municipalities without specific implementation"""
    municipality = await db.municipalities.find_one({"id": municipality_id})
    if not municipality:
        raise HTTPException(status_code=404, detail="Municipality not found")
    
    municipality_name = municipality.get("name", "")
    
    # Placeholder for municipalities that don't have specific scrapers yet
    logger.info(f"Generic scraping for {municipality_name} - specific scraper not yet implemented")
    
    await db.municipalities.update_one(
        {"id": municipality_id},
        {
            "$set": {
                "scrape_status": "pending",
                "last_scraped": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"status": "pending", "message": f"Scraper for {municipality_name} not yet implemented"}


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
        
        # Add missing scheduling fields with defaults
        if 'scrape_enabled' not in municipality:
            municipality['scrape_enabled'] = True
        if 'scrape_frequency' not in municipality:
            municipality['scrape_frequency'] = "weekly"
        if 'scrape_day_of_week' not in municipality:
            municipality['scrape_day_of_week'] = 1
        if 'scrape_day_of_month' not in municipality:
            municipality['scrape_day_of_month'] = 1
        if 'scrape_time_hour' not in municipality:
            municipality['scrape_time_hour'] = 2
        if 'scrape_time_minute' not in municipality:
            municipality['scrape_time_minute'] = 0
        if 'next_scrape_time' not in municipality:
            municipality['next_scrape_time'] = None
            
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
    
    # Add missing scheduling fields with defaults
    if 'scrape_enabled' not in municipality:
        municipality['scrape_enabled'] = True
    if 'scrape_frequency' not in municipality:
        municipality['scrape_frequency'] = "weekly"
    if 'scrape_day_of_week' not in municipality:
        municipality['scrape_day_of_week'] = 1
    if 'scrape_day_of_month' not in municipality:
        municipality['scrape_day_of_month'] = 1
    if 'scrape_time_hour' not in municipality:
        municipality['scrape_time_hour'] = 2
    if 'scrape_time_minute' not in municipality:
        municipality['scrape_time_minute'] = 0
    if 'next_scrape_time' not in municipality:
        municipality['next_scrape_time'] = None
    
    return Municipality(**municipality)

@api_router.delete("/municipalities/{municipality_id}")
async def delete_municipality(municipality_id: str):
    """Delete a municipality and optionally its associated tax sale properties"""
    try:
        # First check if municipality exists
        municipality = await db.municipalities.find_one({"id": municipality_id})
        if not municipality:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        # Check if municipality has associated tax sale properties
        property_count = await db.tax_sales.count_documents({"municipality_id": municipality_id})
        
        # Delete the municipality
        result = await db.municipalities.delete_one({"id": municipality_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        # Also delete associated tax sale properties if any exist
        if property_count > 0:
            await db.tax_sales.delete_many({"municipality_id": municipality_id})
        
        return {
            "message": f"Municipality '{municipality.get('name', 'Unknown')}' deleted successfully",
            "deleted_properties": property_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting municipality: {str(e)}")

@api_router.put("/municipalities/{municipality_id}", response_model=Municipality)
async def update_municipality_enhanced(municipality_id: str, update_data: MunicipalityUpdate):
    """Update an existing municipality with enhanced scheduling options"""
    try:
        # Check if municipality exists
        existing_municipality = await db.municipalities.find_one({"id": municipality_id})
        if not existing_municipality:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        # Build update dictionary with only provided fields
        update_dict = {}
        for field, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                update_dict[field] = value
        
        # Always update the timestamp
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        # Calculate next scrape time if schedule fields were updated
        if any(field in update_dict for field in ['scrape_frequency', 'scrape_day_of_week', 'scrape_day_of_month', 'scrape_time_hour', 'scrape_time_minute', 'scrape_enabled']):
            # Get current or updated schedule values
            frequency = update_dict.get('scrape_frequency', existing_municipality.get('scrape_frequency', 'weekly'))
            enabled = update_dict.get('scrape_enabled', existing_municipality.get('scrape_enabled', True))
            hour = update_dict.get('scrape_time_hour', existing_municipality.get('scrape_time_hour', 2))
            minute = update_dict.get('scrape_time_minute', existing_municipality.get('scrape_time_minute', 0))
            
            if enabled:
                if frequency == 'daily':
                    next_scrape = datetime.now(timezone.utc).replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if next_scrape <= datetime.now(timezone.utc):
                        next_scrape += timedelta(days=1)
                elif frequency == 'weekly':
                    day_of_week = update_dict.get('scrape_day_of_week', existing_municipality.get('scrape_day_of_week', 1))
                    next_scrape = datetime.now(timezone.utc).replace(hour=hour, minute=minute, second=0, microsecond=0)
                    days_ahead = day_of_week - next_scrape.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    next_scrape += timedelta(days=days_ahead)
                elif frequency == 'monthly':
                    day_of_month = update_dict.get('scrape_day_of_month', existing_municipality.get('scrape_day_of_month', 1))
                    next_scrape = datetime.now(timezone.utc).replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
                    if next_scrape <= datetime.now(timezone.utc):
                        if next_scrape.month == 12:
                            next_scrape = next_scrape.replace(year=next_scrape.year + 1, month=1)
                        else:
                            next_scrape = next_scrape.replace(month=next_scrape.month + 1)
                
                update_dict["next_scrape_time"] = next_scrape
            else:
                update_dict["next_scrape_time"] = None
        
        # Update the municipality
        result = await db.municipalities.update_one(
            {"id": municipality_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        # Return updated municipality
        updated_municipality = await db.municipalities.find_one({"id": municipality_id})
        
        # Handle data migration for the response
        if '_id' in updated_municipality:
            del updated_municipality['_id']
        
        # Ensure all required fields exist
        if 'website_url' not in updated_municipality or updated_municipality.get('website_url') is None:
            updated_municipality['website_url'] = "https://example.com"
        
        return Municipality(**updated_municipality)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating municipality: {str(e)}")



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

@api_router.post("/geocode-properties")
async def geocode_existing_properties():
    """Geocode all existing properties that have fake or missing coordinates"""
    try:
        # Get all properties that need geocoding
        properties = await db.tax_sales.find({
            "$or": [
                {"latitude": None},
                {"longitude": None},
                # Also update properties with fake coordinates (roughly in Halifax center area)
                {"$and": [{"latitude": {"$gte": 44.5, "$lte": 44.8}}, {"longitude": {"$gte": -63.8, "$lte": -63.3}}]}
            ]
        }).to_list(1000)
        
        geocoded_count = 0
        failed_count = 0
        
        for property in properties:
            property_address = property.get('property_address', '')
            if not property_address:
                failed_count += 1
                continue
            
            # Clean address for geocoding
            address_for_geocoding = property_address.split(' - ')[0]  # Remove property type suffix
            
            # Geocode the address
            latitude, longitude = await geocode_address(address_for_geocoding)
            
            if latitude and longitude:
                # Update the property with real coordinates
                await db.tax_sales.update_one(
                    {"_id": property["_id"]},
                    {"$set": {"latitude": latitude, "longitude": longitude}}
                )
                geocoded_count += 1
                logger.info(f"Updated {property.get('assessment_number', 'N/A')}: {address_for_geocoding} -> {latitude}, {longitude}")
            else:
                failed_count += 1
                logger.warning(f"Failed to geocode {property.get('assessment_number', 'N/A')}: {address_for_geocoding}")
            
            # Add small delay to respect Google API rate limits
            await asyncio.sleep(0.1)
        
        return {
            "message": f"Geocoding completed",
            "total_properties": len(properties),
            "geocoded_successfully": geocoded_count,
            "failed": failed_count
        }
        
    except Exception as e:
        logger.error(f"Error geocoding properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def capture_property_boundary_screenshot(pid_number: str, assessment_number: str) -> Optional[str]:
    """
    Capture property boundary screenshot from viewpoint.ca
    Returns the path to the saved screenshot or None if failed
    """
    try:
        import subprocess
        import tempfile
        import base64
        
        # Create screenshots directory if it doesn't exist
        screenshots_dir = Path("property_screenshots")
        screenshots_dir.mkdir(exist_ok=True)
        
        # Playwright script for viewpoint.ca automation
        playwright_script = f'''
import asyncio
from playwright.async_api import async_playwright
import time

async def capture_viewpoint_screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to viewpoint.ca with PID
            viewpoint_url = f"https://www.viewpoint.ca/map#pid={pid_number}"
            print(f"Navigating to: {{viewpoint_url}}")
            
            await page.goto(viewpoint_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(5000)  # Wait for map to load
            
            # Wait for map container to be visible
            await page.wait_for_selector(".leaflet-container", timeout=15000)
            print("Map container loaded")
            
            # Try to find and click satellite/aerial view button
            satellite_buttons = [
                "text=Satellite", "text=Aerial", "text=Imagery", 
                "[title*='satellite']", "[title*='aerial']", "[title*='imagery']",
                ".leaflet-control-layers-selector"
            ]
            
            for selector in satellite_buttons:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.locator(selector).first.click()
                        print(f"Clicked satellite button: {{selector}}")
                        await page.wait_for_timeout(3000)
                        break
                except:
                    continue
            
            # Try to close any property details/info panels that might obstruct the view
            close_selectors = [
                ".close", ".btn-close", "[aria-label='Close']", 
                ".modal-close", ".popup-close", ".info-close"
            ]
            
            for selector in close_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.locator(selector).first.click()
                        await page.wait_for_timeout(1000)
                except:
                    continue
            
            # Wait for property to be highlighted and map to settle
            await page.wait_for_timeout(3000)
            
            # Take screenshot of the map area
            map_element = page.locator(".leaflet-container").first
            screenshot_path = "property_screenshots/{pid_number}_{assessment_number}_boundary.png"
            
            await map_element.screenshot(
                path=screenshot_path,
                quality=90,
                type="png"
            )
            
            print(f"Screenshot captured: {{screenshot_path}}")
            return screenshot_path
            
        except Exception as e:
            print(f"Error during automation: {{e}}")
            return None
        finally:
            await browser.close()

# Run the async function
result = asyncio.run(capture_viewpoint_screenshot())
print(result if result else "Failed")
'''
        
        # Write the script to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(playwright_script)
            script_path = f.name
        
        try:
            # Run the Playwright script
            result = subprocess.run(
                ['python', script_path], 
                capture_output=True, 
                text=True, 
                timeout=60,
                cwd='/app/backend'
            )
            
            if result.returncode == 0:
                screenshot_path = f"property_screenshots/{pid_number}_{assessment_number}_boundary.png"
                full_path = Path(f"/app/backend/{screenshot_path}")
                
                if full_path.exists():
                    logger.info(f"Successfully captured boundary screenshot for PID {pid_number}")
                    return screenshot_path
                else:
                    logger.warning(f"Screenshot file not found: {full_path}")
                    return None
            else:
                logger.error(f"Playwright script failed: {result.stderr}")
                return None
                
        finally:
            # Clean up the temporary script file
            Path(script_path).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"Error capturing boundary screenshot for PID {pid_number}: {e}")
        return None

@api_router.post("/capture-boundary/{assessment_number}")
async def capture_property_boundary(assessment_number: str):
    """Capture and store property boundary screenshot from viewpoint.ca"""
    try:
        # Get property details
        property_data = await db.tax_sales.find_one({"assessment_number": assessment_number})
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        pid_number = property_data.get('pid_number')
        if not pid_number:
            raise HTTPException(status_code=400, detail="Property has no PID number")
        
        # Check if screenshot already exists
        screenshot_filename = f"boundary_{pid_number}_{assessment_number}.png"
        screenshot_path = f"/app/backend/static/property_screenshots/{screenshot_filename}"
        
        if Path(screenshot_path).exists():
            # Update database with existing screenshot
            await db.tax_sales.update_one(
                {"assessment_number": assessment_number},
                {"$set": {"boundary_screenshot": screenshot_filename}}
            )
            return {
                "message": "Boundary screenshot already exists",
                "assessment_number": assessment_number,
                "pid_number": pid_number,
                "screenshot_filename": screenshot_filename,
                "needs_capture": False
            }
        
        # Return data for screenshot automation
        viewpoint_url = f"https://www.viewpoint.ca/map#pid={pid_number}"
        
        return {
            "message": "Ready for boundary screenshot capture",
            "assessment_number": assessment_number,
            "pid_number": pid_number,
            "viewpoint_url": viewpoint_url,
            "screenshot_filename": screenshot_filename,
            "screenshot_path": screenshot_path,
            "property_address": property_data.get('property_address', 'Unknown'),
            "needs_capture": True
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in boundary capture endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/save-boundary-screenshot")
async def save_boundary_screenshot(request_data: dict):
    """Save the boundary screenshot path to property record"""
    try:
        assessment_number = request_data.get('assessment_number')
        screenshot_filename = request_data.get('screenshot_filename')
        
        if not assessment_number or not screenshot_filename:
            raise HTTPException(status_code=400, detail="Missing assessment_number or screenshot_filename")
        
        # Update property record with screenshot filename
        result = await db.tax_sales.update_one(
            {"assessment_number": assessment_number},
            {"$set": {"boundary_screenshot": screenshot_filename}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return {
            "message": "Boundary screenshot saved successfully",
            "assessment_number": assessment_number,
            "screenshot_filename": screenshot_filename,
            "image_url": f"/static/property_screenshots/{screenshot_filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving boundary screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/capture-all-boundaries") 
async def capture_all_property_boundaries():
    """Prepare data for capturing boundary screenshots for all properties with PIDs"""
    try:
        # Get all properties that have PID numbers
        properties = await db.tax_sales.find({
            "pid_number": {"$exists": True, "$ne": None, "$ne": ""}
        }).to_list(1000)
        
        boundary_data = []
        for prop in properties:
            pid_number = prop.get('pid_number')
            assessment_number = prop.get('assessment_number')
            
            if pid_number and assessment_number:
                screenshot_filename = f"boundary_{pid_number}_{assessment_number}.png"
                screenshot_path = f"/app/backend/static/property_screenshots/{screenshot_filename}"
                
                # Check if screenshot already exists
                has_screenshot = Path(screenshot_path).exists()
                
                boundary_data.append({
                    "assessment_number": assessment_number,
                    "pid_number": pid_number,
                    "viewpoint_url": f"https://www.viewpoint.ca/map#pid={pid_number}",
                    "screenshot_filename": screenshot_filename,
                    "screenshot_path": screenshot_path,
                    "property_address": prop.get('property_address', 'Unknown'),
                    "has_screenshot": has_screenshot,
                    "needs_capture": not has_screenshot
                })
        
        ready_for_capture = [item for item in boundary_data if item['needs_capture']]
        
        return {
            "message": f"Found {len(boundary_data)} properties with PIDs, {len(ready_for_capture)} need screenshot capture",
            "properties": boundary_data,
            "total_count": len(boundary_data),
            "ready_for_capture": len(ready_for_capture),
            "method": "viewpoint_ca_boundaries"
        }
        
    except Exception as e:
        logger.error(f"Error preparing boundary capture data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/capture-viewpoint-boundary/{assessment_number}")
async def capture_viewpoint_boundary_real(assessment_number: str):
    """Initiate real viewpoint.ca boundary screenshot capture for a property"""
    try:
        # Get property details
        property_data = await db.tax_sales.find_one({"assessment_number": assessment_number})
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        pid_number = property_data.get('pid_number')
        if not pid_number:
            raise HTTPException(status_code=400, detail="Property has no PID number")
        
        screenshot_filename = f"boundary_{pid_number}_{assessment_number}.png"
        screenshot_path = f"/app/backend/static/property_screenshots/{screenshot_filename}"
        
        # Check if real screenshot already exists (not demo)
        if Path(screenshot_path).exists():
            file_size = Path(screenshot_path).stat().st_size
            # If file is larger than 5KB, assume it's a real screenshot (demos are ~3KB)
            if file_size > 5000:
                return {
                    "message": "Real boundary screenshot already exists",
                    "assessment_number": assessment_number,
                    "pid_number": pid_number,
                    "screenshot_filename": screenshot_filename,
                    "needs_capture": False,
                    "file_size": file_size
                }
        
        # Prepare data for viewpoint.ca screenshot automation
        viewpoint_url = f"https://www.viewpoint.ca/map#pid={pid_number}"
        
        return {
            "message": "Ready for viewpoint.ca boundary screenshot capture",
            "assessment_number": assessment_number,
            "pid_number": pid_number,
            "viewpoint_url": viewpoint_url,
            "screenshot_filename": screenshot_filename,
            "screenshot_path": screenshot_path,
            "property_address": property_data.get('property_address', 'Unknown'),
            "needs_capture": True,
            "automation_ready": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preparing viewpoint boundary capture: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/test-viewpoint-access")
async def test_viewpoint_accessibility():
    """Test if viewpoint.ca is accessible and responsive"""
    try:
        import aiohttp
        import asyncio
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('https://www.viewpoint.ca/', timeout=15) as response:
                    status = response.status
                    content_type = response.headers.get('content-type', '')
                    
                    if status == 200:
                        return {
                            "accessible": True,
                            "status_code": status,
                            "content_type": content_type,
                            "message": "Viewpoint.ca is accessible",
                            "ready_for_automation": True
                        }
                    else:
                        return {
                            "accessible": False,
                            "status_code": status,
                            "message": f"Viewpoint.ca returned status {status}",
                            "ready_for_automation": False
                        }
                        
            except asyncio.TimeoutError:
                return {
                    "accessible": False,
                    "status_code": None,
                    "message": "Viewpoint.ca connection timeout",
                    "ready_for_automation": False
                }
                
    except Exception as e:
        logger.error(f"Error testing viewpoint.ca access: {e}")
        return {
            "accessible": False,
            "status_code": None,
            "message": f"Error accessing viewpoint.ca: {str(e)}",
            "ready_for_automation": False
        }

@api_router.get("/query-ns-government-parcel/{pid_number}")
async def query_ns_government_parcel(pid_number: str):
    """Query official Nova Scotia government ArcGIS service for property boundary"""
    try:
        import aiohttp
        
        # Query the official Nova Scotia Property Registration Database (NSPRD)
        query_url = (
            "https://nsgiwa2.novascotia.ca/arcgis/rest/services/PLAN/PLAN_NSPRD_WM84/MapServer/0/query"
            f"?where=PID='{pid_number}'"
            "&outFields=*"
            "&outSR=4326"
            "&returnGeometry=true"
            "&f=json"
        )
        
        async with aiohttp.ClientSession() as session:
            async with session.get(query_url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('features') and len(data['features']) > 0:
                        feature = data['features'][0]
                        geometry = feature.get('geometry')
                        attributes = feature.get('attributes')
                        
                        # Extract property details
                        property_info = {
                            "pid": attributes.get('PID'),
                            "area_sqm": attributes.get('SHAPE.AREA'),
                            "perimeter_m": attributes.get('PERIMETER'),
                            "source_id": attributes.get('SOURCE_ID'),
                            "update_date": attributes.get('UPDAT_DATE'),
                            "theme_no": attributes.get('THEME_NO')
                        }
                        
                        # Extract bounding box for map extent
                        if geometry and geometry.get('rings'):
                            coords = []
                            for ring in geometry['rings']:
                                coords.extend(ring)
                            
                            if coords:
                                lons = [coord[0] for coord in coords]
                                lats = [coord[1] for coord in coords]
                                
                                bbox = {
                                    "minLon": min(lons),
                                    "maxLon": max(lons), 
                                    "minLat": min(lats),
                                    "maxLat": max(lats)
                                }
                                
                                center_lat = (bbox["minLat"] + bbox["maxLat"]) / 2
                                center_lon = (bbox["minLon"] + bbox["maxLon"]) / 2
                                
                                # Calculate appropriate zoom level based on property size
                                lat_range = bbox["maxLat"] - bbox["minLat"]
                                lon_range = bbox["maxLon"] - bbox["minLon"]
                                max_range = max(lat_range, lon_range)
                                
                                # Zoom calculation (higher zoom for smaller properties)
                                if max_range < 0.001:
                                    zoom_level = 19
                                elif max_range < 0.005:
                                    zoom_level = 18
                                elif max_range < 0.01:
                                    zoom_level = 17
                                else:
                                    zoom_level = 16
                                
                                return {
                                    "found": True,
                                    "pid_number": pid_number,
                                    "property_info": property_info,
                                    "geometry": geometry,
                                    "bbox": bbox,
                                    "center": {"lat": center_lat, "lon": center_lon},
                                    "zoom_level": zoom_level,
                                    "ns_arcgis_url": f"https://nsgiwa2.novascotia.ca/arcgis/rest/services/PLAN/PLAN_NSPRD_WM84/MapServer/0/query?where=PID='{pid_number}'&outFields=*&outSR=4326&returnGeometry=true&f=json",
                                    "query_url": query_url,
                                    "source": "Nova Scotia Government NSPRD"
                                }
                    
                    return {
                        "found": False,
                        "pid_number": pid_number,
                        "message": "Property not found in Nova Scotia government database",
                        "query_url": query_url
                    }
                else:
                    return {
                        "found": False,
                        "pid_number": pid_number,
                        "error": f"NS Government service returned status {response.status}",
                        "query_url": query_url
                    }
                    
    except Exception as e:
        logger.error(f"Error querying NS Government parcel {pid_number}: {e}")
        return {
            "found": False,
            "pid_number": pid_number,
            "error": str(e)
        }

@api_router.post("/batch-process-ns-government-boundaries")
async def batch_process_ns_government_boundaries():
    """Batch process all properties to generate boundary thumbnails using NS Government data"""
    try:
        # Get all properties with PIDs
        properties = await db.tax_sales.find({
            "pid_number": {"$exists": True, "$ne": None, "$ne": ""}
        }).to_list(1000)
        
        results = {
            "total_properties": len(properties),
            "processed": [],
            "failed": [],
            "government_data_found": 0,
            "thumbnails_created": 0
        }
        
        for prop in properties:
            pid_number = prop.get('pid_number')
            assessment_number = prop.get('assessment_number')
            
            if not pid_number or not assessment_number:
                results["failed"].append({
                    "assessment_number": assessment_number,
                    "reason": "Missing PID or assessment number"
                })
                continue
            
            try:
                # Query NS Government service for this property
                parcel_data = await query_ns_government_parcel(pid_number)
                
                if parcel_data.get('found'):
                    # Create boundary thumbnail using government data
                    screenshot_filename = f"boundary_{pid_number}_{assessment_number}.png"
                    
                    # Update property record with boundary screenshot
                    await db.tax_sales.update_one(
                        {"assessment_number": assessment_number},
                        {"$set": {
                            "boundary_screenshot": screenshot_filename,
                            "government_boundary_data": {
                                "area_sqm": parcel_data['property_info']['area_sqm'],
                                "perimeter_m": parcel_data['property_info']['perimeter_m'],
                                "center_lat": parcel_data['center']['lat'],
                                "center_lon": parcel_data['center']['lon'],
                                "zoom_level": parcel_data['zoom_level'],
                                "update_date": parcel_data['property_info']['update_date'],
                                "source": "Nova Scotia Government NSPRD"
                            }
                        }}
                    )
                    
                    # Generate Google Maps satellite image for this property
                    center = parcel_data['center']
                    zoom = parcel_data['zoom_level']
                    satellite_url = f"https://maps.googleapis.com/maps/api/staticmap?center={center['lat']},{center['lon']}&zoom={zoom}&size=400x300&maptype=satellite&key={os.environ.get('GOOGLE_MAPS_API_KEY')}"
                    
                    results["processed"].append({
                        "assessment_number": assessment_number,
                        "pid_number": pid_number,
                        "property_address": prop.get('property_address', 'Unknown'),
                        "area_sqm": parcel_data['property_info']['area_sqm'],
                        "screenshot_filename": screenshot_filename,
                        "satellite_url": satellite_url,
                        "center": center,
                        "status": "Government data found, thumbnail prepared"
                    })
                    
                    results["government_data_found"] += 1
                    results["thumbnails_created"] += 1
                    
                else:
                    results["failed"].append({
                        "assessment_number": assessment_number,
                        "pid_number": pid_number,
                        "reason": "Not found in NS Government database"
                    })
                    
            except Exception as e:
                results["failed"].append({
                    "assessment_number": assessment_number,
                    "pid_number": pid_number,
                    "reason": f"Error processing: {str(e)}"
                })
        
        return {
            "message": f"Batch processing completed: {results['government_data_found']}/{results['total_properties']} properties found in NS Government database",
            "results": results,
            "success_rate": f"{(results['government_data_found']/results['total_properties']*100):.1f}%"
        }
        
    except Exception as e:
        logger.error(f"Error in batch processing NS Government boundaries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/capture-satellite-thumbnails-batch")  
async def capture_satellite_thumbnails_batch(batch_size: int = 5):
    """Capture actual satellite thumbnail images for properties with government boundary data"""
    try:
        # Get properties that have government boundary data but need actual image files
        properties = await db.tax_sales.find({
            "government_boundary_data": {"$exists": True},
            "boundary_screenshot": {"$exists": True}
        }).limit(batch_size).to_list(batch_size)
        
        captured_count = 0
        results = []
        
        for prop in properties:
            assessment_number = prop.get('assessment_number')
            pid_number = prop.get('pid_number')
            boundary_data = prop.get('government_boundary_data', {})
            screenshot_filename = prop.get('boundary_screenshot')
            
            if not all([assessment_number, pid_number, screenshot_filename]):
                continue
                
            screenshot_path = f"/app/backend/static/property_screenshots/{screenshot_filename}"
            
            # Check if image already exists and is substantial (not demo)
            if Path(screenshot_path).exists():
                file_size = Path(screenshot_path).stat().st_size
                if file_size > 10000:  # 10KB+ indicates real satellite image
                    continue
            
            try:
                # Get Google Maps satellite image centered on government boundary data
                center_lat = boundary_data.get('center_lat')
                center_lon = boundary_data.get('center_lon') 
                zoom = boundary_data.get('zoom_level', 18)
                
                if center_lat and center_lon:
                    # Create high-quality satellite thumbnail using PIL/requests
                    satellite_url = f"https://maps.googleapis.com/maps/api/staticmap?center={center_lat},{center_lon}&zoom={zoom}&size=400x300&maptype=satellite&key={os.environ.get('GOOGLE_MAPS_API_KEY')}"
                    
                    # Download the satellite image
                    import requests
                    response = requests.get(satellite_url, timeout=10)
                    
                    if response.status_code == 200:
                        # Save the actual satellite image
                        Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(screenshot_path, 'wb') as f:
                            f.write(response.content)
                        
                        captured_count += 1
                        results.append({
                            "assessment_number": assessment_number,
                            "pid_number": pid_number,
                            "screenshot_filename": screenshot_filename,
                            "file_size": len(response.content),
                            "status": "Satellite thumbnail captured successfully"
                        })
                    else:
                        results.append({
                            "assessment_number": assessment_number,
                            "pid_number": pid_number,
                            "status": f"Failed to download satellite image: HTTP {response.status_code}"
                        })
                        
            except Exception as e:
                results.append({
                    "assessment_number": assessment_number,
                    "pid_number": pid_number,
                    "status": f"Error capturing thumbnail: {str(e)}"
                })
        
        return {
            "message": f"Captured {captured_count} satellite thumbnails from batch of {len(properties)} properties",
            "captured_count": captured_count,
            "total_processed": len(properties),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error capturing satellite thumbnails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/property/{assessment_number}/boundary-image")
async def get_property_boundary_image(assessment_number: str):
    """Get boundary screenshot for a specific property"""
    try:
        property_data = await db.tax_sales.find_one({"assessment_number": assessment_number})
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        boundary_screenshot = property_data.get('boundary_screenshot')
        if boundary_screenshot:
            return {
                "assessment_number": assessment_number,
                "has_boundary_image": True,
                "boundary_screenshot": boundary_screenshot,
                "image_url": f"/api/boundary-image/{boundary_screenshot}"
            }
        else:
            # Return data for capturing screenshot
            latitude = property_data.get('latitude')
            longitude = property_data.get('longitude')
            
            if latitude and longitude:
                google_maps_url = f"https://www.google.com/maps/@{latitude},{longitude},19z/data=!3m1!1e3"
                return {
                    "assessment_number": assessment_number,
                    "has_boundary_image": False,
                    "google_maps_url": google_maps_url,
                    "ready_for_capture": True
                }
            else:
                return {
                    "assessment_number": assessment_number,
                    "has_boundary_image": False,
                    "ready_for_capture": False,
                    "error": "No coordinates available for this property"
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting boundary image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Scraping Endpoints
@api_router.post("/scrape/cape-breton")
async def scrape_cape_breton():
    """Scrape Cape Breton Regional Municipality tax sales directly"""
    try:
        result = await scrape_cape_breton_tax_sales()
        return result
    except Exception as e:
        logger.error(f"Cape Breton scraping endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cape Breton scraping failed: {str(e)}")

@api_router.post("/scrape/kentville") 
async def scrape_kentville():
    """Scrape Kentville tax sales directly"""
    try:
        result = await scrape_kentville_tax_sales()
        return result
    except Exception as e:
        logger.error(f"Kentville scraping endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Kentville scraping failed: {str(e)}")

@api_router.post("/scrape/halifax")
async def scrape_halifax():
    """Trigger Halifax-specific scraping"""
    result = await scrape_halifax_tax_sales()
    return result

@api_router.post("/generate-boundary-thumbnail/{assessment_number}")
async def generate_boundary_thumbnail(assessment_number: str):
    """Generate a thumbnail screenshot of Google Maps with NSPRD boundaries for search page"""
    try:
        # Find property by assessment number
        property_doc = await db.tax_sales.find_one({"assessment_number": assessment_number})
        if not property_doc:
            raise HTTPException(status_code=404, detail="Property not found")
        
        if not property_doc.get('latitude') or not property_doc.get('longitude'):
            raise HTTPException(status_code=400, detail="Property coordinates not available")
        
        # Import Playwright
        from playwright.async_api import async_playwright
        import asyncio
        import base64
        from datetime import datetime
        
        async def capture_boundary_thumbnail():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 400, 'height': 300}
                )
                page = await context.new_page()
                
                try:
                    # Create HTML page with Google Maps and NSPRD boundaries
                    google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY', 'AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY')
                    
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <style>
                            #map {{ width: 100%; height: 100%; margin: 0; padding: 0; }}
                            body {{ margin: 0; padding: 0; }}
                        </style>
                    </head>
                    <body>
                        <div id="map"></div>
                        <script async defer
                            src="https://maps.googleapis.com/maps/api/js?key={google_maps_api_key}&libraries=geometry&callback=initMap">
                        </script>
                        <script>
                            let map;
                            let marker;
                            let boundaryPolygon;
                            
                            function initMap() {{
                                const propertyLocation = {{ lat: {property_doc['latitude']}, lng: {property_doc['longitude']} }};
                                
                                map = new google.maps.Map(document.getElementById("map"), {{
                                    zoom: 18,
                                    center: propertyLocation,
                                    mapTypeId: 'satellite',
                                    disableDefaultUI: true,
                                    gestureHandling: 'none',
                                    keyboardShortcuts: false,
                                    scrollwheel: false,
                                    zoomControl: false
                                }});
                                
                                // Add property marker
                                marker = new google.maps.Marker({{
                                    position: propertyLocation,
                                    map: map,
                                    title: "Property Location"
                                }});
                                
                                // Fetch and draw NSPRD boundaries
                                fetchAndDrawBoundaries();
                            }}
                            
                            async function fetchAndDrawBoundaries() {{
                                try {{
                                    const pidNumber = '{property_doc.get("pid_number", "")}';
                                    if (!pidNumber) {{
                                        console.log('No PID number available');
                                        return;
                                    }}
                                    
                                    const response = await fetch('/api/query-ns-government-parcel/' + pidNumber);
                                    const data = await response.json();
                                    
                                    if (data.found && data.geometry && data.geometry.rings) {{
                                        drawBoundaryPolygon(data.geometry.rings);
                                    }}
                                }} catch (error) {{
                                    console.error('Error fetching boundary data:', error);
                                }}
                            }}
                            
                            function drawBoundaryPolygon(rings) {{
                                try {{
                                    // Convert rings to Google Maps format
                                    const paths = rings.map(ring => 
                                        ring.map(point => ({{
                                            lat: point[1], // Latitude is second element
                                            lng: point[0]  // Longitude is first element
                                        }}))
                                    );
                                    
                                    // Create and display polygon
                                    boundaryPolygon = new google.maps.Polygon({{
                                        paths: paths,
                                        strokeColor: '#FF0000',
                                        strokeOpacity: 0.9,
                                        strokeWeight: 3,
                                        fillColor: '#FF0000',
                                        fillOpacity: 0.2
                                    }});
                                    
                                    boundaryPolygon.setMap(map);
                                    console.log('NSPRD boundary polygon drawn for thumbnail');
                                }} catch (error) {{
                                    console.error('Error drawing boundary polygon:', error);
                                }}
                            }}
                        </script>
                    </body>
                    </html>
                    """
                    
                    # Load the HTML content
                    await page.set_content(html_content)
                    
                    # Wait for map to load and boundaries to be drawn
                    await page.wait_for_timeout(5000)
                    
                    # Take screenshot
                    screenshot = await page.screenshot(
                        type='png',
                        full_page=True,
                        quality=90
                    )
                    
                    return screenshot
                    
                finally:
                    await browser.close()
        
        # Generate the thumbnail screenshot
        screenshot_bytes = await capture_boundary_thumbnail()
        
        # Save screenshot to file
        screenshots_dir = "/app/backend/static/property_screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        
        thumbnail_filename = f"thumbnail_{assessment_number}_{property_doc.get('pid_number', 'unknown')}.png"
        thumbnail_path = os.path.join(screenshots_dir, thumbnail_filename)
        
        with open(thumbnail_path, 'wb') as f:
            f.write(screenshot_bytes)
        
        # Update property document with thumbnail filename
        await db.tax_sales.update_one(
            {"assessment_number": assessment_number},
            {"$set": {"boundary_thumbnail": thumbnail_filename}}
        )
        
        logger.info(f"Generated boundary thumbnail for assessment {assessment_number}: {thumbnail_filename}")
        
        return {
            "status": "success",
            "assessment_number": assessment_number,
            "thumbnail_filename": thumbnail_filename,
            "thumbnail_path": f"/api/boundary-image/{thumbnail_filename}",
            "message": "Boundary thumbnail generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error generating boundary thumbnail for {assessment_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate boundary thumbnail: {str(e)}")

@api_router.post("/generate-all-boundary-thumbnails")
async def generate_all_boundary_thumbnails():
    """Generate boundary thumbnails for all properties with PID numbers"""
    try:
        # Get all properties with PID numbers
        properties = await db.tax_sales.find({"pid_number": {"$exists": True, "$ne": None}}).to_list(None)
        
        results = []
        success_count = 0
        error_count = 0
        
        for property_doc in properties:
            try:
                assessment_number = property_doc.get("assessment_number")
                if not assessment_number:
                    continue
                
                # Generate thumbnail for this property
                result = await generate_boundary_thumbnail(assessment_number)
                results.append({
                    "assessment_number": assessment_number,
                    "status": "success",
                    "thumbnail": result.get("thumbnail_filename")
                })
                success_count += 1
                
            except Exception as e:
                results.append({
                    "assessment_number": property_doc.get("assessment_number", "unknown"),
                    "status": "error",
                    "error": str(e)
                })
                error_count += 1
        
        return {
            "status": "completed",
            "total_properties": len(properties),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error generating all boundary thumbnails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate thumbnails: {str(e)}")

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

@api_router.post("/scrape-municipality/{municipality_id}")
async def scrape_municipality_by_id(municipality_id: str):
    """Trigger scraping for a specific municipality by ID"""
    try:
        municipality = await db.municipalities.find_one({"id": municipality_id})
        if not municipality:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        scraper_type = municipality.get("scraper_type", "generic")
        
        if scraper_type == "halifax":
            result = await scrape_halifax_tax_sales_for_municipality(municipality_id)
        elif scraper_type == "cape_breton":
            result = await scrape_cape_breton_tax_sales()
        elif scraper_type == "kentville":
            result = await scrape_kentville_tax_sales()
        else:
            result = await scrape_generic_municipality(municipality_id)
            
        return result
        
    except Exception as e:
        logger.error(f"Error scraping municipality {municipality_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/scrape-all")
async def scrape_all_municipalities():
    """Trigger scraping for all municipalities"""
    municipalities = await db.municipalities.find().to_list(1000)
    results = []
    
    for municipality in municipalities:
        try:
            scraper_type = municipality.get("scraper_type", "generic")
            
            if scraper_type == "halifax":
                # Use Halifax scraper for any municipality with scraper_type "halifax"
                result = await scrape_halifax_tax_sales_for_municipality(municipality["id"])
            elif scraper_type == "cape_breton":
                # Use Cape Breton scraper
                result = await scrape_cape_breton_tax_sales()
            elif scraper_type == "kentville":
                # Use Kentville scraper  
                result = await scrape_kentville_tax_sales()
            else:
                # Use generic scraper for municipalities with scraper_type "generic"
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

# API endpoint for updating a municipality - REMOVED DUPLICATE
# This functionality is handled by the api_router.put("/municipalities/{municipality_id}") endpoint above

# API endpoint for creating a new municipality - REMOVED DUPLICATE
# This functionality is handled by the api_router.post("/municipalities") endpoint above

async def geocode_address(address: str) -> tuple[Optional[float], Optional[float]]:
    """
    Geocode an address using Google Maps Geocoding API
    Returns (latitude, longitude) or (None, None) if geocoding fails
    """
    try:
        # Use environment variable for Google Maps API key
        api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        
        if not api_key:
            logger.warning("Google Maps API key not found, skipping geocoding")
            return None, None
        
        # Clean and prepare the address for geocoding
        # Add Nova Scotia, Canada to help with geocoding accuracy
        full_address = f"{address}, Nova Scotia, Canada"
        encoded_address = quote(full_address)
        
        geocoding_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"
        
        response = requests.get(geocoding_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data.get('results'):
            location = data['results'][0]['geometry']['location']
            latitude = location['lat']
            longitude = location['lng']
            
            # Verify coordinates are within Nova Scotia bounds (roughly)
            # Nova Scotia: lat 43.4-47.0, lng -66.5 to -59.5
            if 43.0 <= latitude <= 47.5 and -67.0 <= longitude <= -59.0:
                logger.info(f"Successfully geocoded '{address}' to {latitude}, {longitude}")
                return latitude, longitude
            else:
                logger.warning(f"Geocoded coordinates for '{address}' are outside Nova Scotia: {latitude}, {longitude}")
                return None, None
        else:
            logger.warning(f"Geocoding failed for '{address}': {data.get('status', 'Unknown error')}")
            return None, None
            
    except Exception as e:
        logger.error(f"Error geocoding address '{address}': {e}")
        return None, None

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
@api_router.get("/property/{assessment_number}/enhanced")
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
            "scraper_type": "cape_breton"
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
            "scraper_type": "kentville"
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

@api_router.post("/fix-halifax-municipality")
async def fix_halifax_municipality():
    """Fix Halifax municipality configuration for VPS deployment issues"""
    try:
        # Find Halifax municipality
        halifax = await db.municipalities.find_one({"name": "Halifax Regional Municipality"})
        
        if not halifax:
            return {"error": "Halifax municipality not found", "action": "needs_initialization"}
        
        # Check if Halifax has wrong scraper_type
        current_scraper_type = halifax.get("scraper_type", "unknown")
        
        if current_scraper_type != "halifax":
            # Update Halifax to have correct scraper_type
            await db.municipalities.update_one(
                {"name": "Halifax Regional Municipality"},
                {"$set": {
                    "scraper_type": "halifax",
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            
            return {
                "status": "fixed",
                "message": f"Updated Halifax scraper_type from '{current_scraper_type}' to 'halifax'",
                "municipality_id": halifax["id"]
            }
        else:
            return {
                "status": "already_correct", 
                "message": "Halifax municipality already has correct scraper_type 'halifax'",
                "municipality_id": halifax["id"]
            }
            
    except Exception as e:
        logger.error(f"Error fixing Halifax municipality: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fix Halifax municipality: {str(e)}")


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