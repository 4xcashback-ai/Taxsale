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

class MunicipalityCreate(BaseModel):
    name: str
    website_url: str
    tax_sale_url: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    scraper_type: str = "generic"

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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_url: str
    raw_data: Optional[dict] = None  # Store original scraped data

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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: str
    raw_data: Optional[dict] = None

class ScrapeStats(BaseModel):
    total_municipalities: int
    scraped_today: int
    total_properties: int
    last_scrape: Optional[datetime] = None


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
        
        # Scrape main tax sale page
        main_url = "https://www.halifax.ca/home-property/property-taxes/tax-sale"
        response = requests.get(main_url, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find property list URL and sale details
        schedule_link = None
        sale_date = None
        
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.get_text()
            if 'SCHEDULE' in text.upper() and 'TAXSALE' in text.upper():
                schedule_link = href
            elif 'Sept' in text and '2025' in text:
                # Extract sale date
                date_match = re.search(r'Sept\s+(\d+),\s+(\d{4})', text)
                if date_match:
                    day, year = date_match.groups()
                    sale_date = f"{year}-09-{day.zfill(2)}T10:01:00Z"
        
        if not schedule_link:
            raise Exception("Could not find Halifax property schedule link")
        
        # Make URL absolute if relative
        if schedule_link.startswith('/'):
            schedule_link = "https://www.halifax.ca" + schedule_link
        
        # Scrape property list
        list_response = requests.get(schedule_link, timeout=30)
        list_soup = BeautifulSoup(list_response.content, 'html.parser')
        
        properties_scraped = 0
        
        # Parse table data
        table = list_soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    try:
                        # Extract data from cells
                        assessment_num = cells[0].get_text().strip() if cells[0] else ""
                        owner_name = cells[1].get_text().strip() if cells[1] else ""
                        description = cells[2].get_text().strip() if cells[2] else ""
                        pid = cells[3].get_text().strip() if cells[3] else ""
                        opening_bid_text = cells[4].get_text().strip() if len(cells) > 4 else ""
                        
                        # Skip empty rows
                        if not assessment_num or not description:
                            continue
                        
                        # Parse opening bid
                        opening_bid = None
                        if opening_bid_text:
                            bid_match = re.search(r'\$([0-9,]+\.?\d*)', opening_bid_text)
                            if bid_match:
                                opening_bid = float(bid_match.group(1).replace(',', ''))
                        
                        # Parse property address and type from description
                        property_type = "Land" if "Land" in description else "Dwelling" if "Dwelling" in description else "Property"
                        
                        # Create property record
                        property_data = {
                            "municipality_id": municipality_id,
                            "municipality_name": "Halifax Regional Municipality",
                            "property_address": description,
                            "property_description": f"Assessment: {assessment_num}, Owner: {owner_name}",
                            "opening_bid": opening_bid,
                            "sale_date": sale_date,
                            "sale_time": "10:01 AM",
                            "sale_location": "Halifax Regional Municipality",
                            "assessment_number": assessment_num,
                            "property_type": property_type,
                            "owner_name": owner_name,
                            "pid_number": pid,
                            "source_url": schedule_link,
                            "raw_data": {
                                "assessment_number": assessment_num,
                                "owner_name": owner_name,
                                "parcel_description": description,
                                "pid": pid,
                                "opening_bid_text": opening_bid_text
                            }
                        }
                        
                        # Try to geocode Halifax region (approximate)
                        property_data["latitude"] = 44.6488 + (hash(description) % 1000) / 10000  # Slight variation
                        property_data["longitude"] = -63.5752 + (hash(description) % 1000) / 10000
                        
                        # Insert or update property
                        existing = await db.tax_sales.find_one({
                            "assessment_number": assessment_num,
                            "municipality_name": "Halifax Regional Municipality"
                        })
                        
                        if existing:
                            await db.tax_sales.update_one(
                                {"id": existing["id"]},
                                {"$set": property_data}
                            )
                        else:
                            tax_sale_property = TaxSaleProperty(**property_data)
                            await db.tax_sales.insert_one(tax_sale_property.dict())
                        
                        properties_scraped += 1
                        
                    except Exception as e:
                        logger.warning(f"Error processing Halifax property row: {e}")
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
    return [Municipality(**municipality) for municipality in municipalities]

@api_router.get("/municipalities/{municipality_id}", response_model=Municipality)
async def get_municipality(municipality_id: str):
    municipality = await db.municipalities.find_one({"id": municipality_id})
    if not municipality:
        raise HTTPException(status_code=404, detail="Municipality not found")
    return Municipality(**municipality)


# Tax Sale Property Endpoints
@api_router.post("/tax-sales", response_model=TaxSaleProperty)
async def create_tax_sale_property(property_data: TaxSalePropertyCreate):
    property_dict = property_data.dict()
    property_obj = TaxSaleProperty(**property_dict)
    await db.tax_sales.insert_one(property_obj.dict())
    return property_obj

@api_router.get("/tax-sales", response_model=List[TaxSaleProperty])
async def get_tax_sale_properties(
    municipality: Optional[str] = Query(None, description="Filter by municipality name"),
    limit: int = Query(100, description="Number of results to return"),
    skip: int = Query(0, description="Number of results to skip")
):
    query = {}
    if municipality:
        query["municipality_name"] = {"$regex": municipality, "$options": "i"}
    
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
        last_scrape=last_scrape
    )


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