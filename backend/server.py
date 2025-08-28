from fastapi import FastAPI, APIRouter, HTTPException, Query
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

class MunicipalityCreate(BaseModel):
    name: str
    website_url: str
    tax_sale_url: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class TaxSaleProperty(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    municipality_id: str
    municipality_name: str
    property_address: str
    property_description: Optional[str] = None
    assessment_value: Optional[float] = None
    tax_owing: Optional[float] = None
    sale_date: Optional[datetime] = None
    sale_time: Optional[str] = None
    sale_location: Optional[str] = None
    property_id: Optional[str] = None  # Municipal property ID
    property_type: Optional[str] = None
    lot_size: Optional[str] = None
    zoning: Optional[str] = None
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
    sale_date: Optional[datetime] = None
    sale_time: Optional[str] = None
    sale_location: Optional[str] = None
    property_id: Optional[str] = None
    property_type: Optional[str] = None
    lot_size: Optional[str] = None
    zoning: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: str
    raw_data: Optional[dict] = None

class ScrapeStats(BaseModel):
    total_municipalities: int
    scraped_today: int
    total_properties: int
    last_scrape: Optional[datetime] = None


# Municipality Management Endpoints
@api_router.get("/")
async def root():
    return {"message": "Nova Scotia Tax Sale Aggregator API"}

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
            {"property_description": {"$regex": q, "$options": "i"}}
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
        "tax_owing": prop.get("tax_owing"),
        "sale_date": prop.get("sale_date"),
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


# Web Scraping Functions (Basic Framework)
async def scrape_municipality_tax_sales(municipality_id: str):
    """Scrape tax sales for a specific municipality"""
    municipality = await db.municipalities.find_one({"id": municipality_id})
    if not municipality:
        raise HTTPException(status_code=404, detail="Municipality not found")
    
    try:
        # Basic web scraping framework
        # This will be expanded based on each municipality's website structure
        url = municipality.get("tax_sale_url") or municipality["website_url"]
        
        # Update scrape status to in progress
        await db.municipalities.update_one(
            {"id": municipality_id},
            {"$set": {"scrape_status": "in_progress"}}
        )
        
        # Placeholder for actual scraping logic
        # TODO: Implement specific scraping logic for each municipality
        
        # Update scrape status and timestamp
        await db.municipalities.update_one(
            {"id": municipality_id},
            {
                "$set": {
                    "scrape_status": "success",
                    "last_scraped": datetime.now(timezone.utc)
                }
            }
        )
        
        return {"status": "success", "municipality": municipality["name"]}
        
    except Exception as e:
        # Update scrape status to failed
        await db.municipalities.update_one(
            {"id": municipality_id},
            {"$set": {"scrape_status": "failed"}}
        )
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@api_router.post("/scrape/{municipality_id}")
async def scrape_municipality(municipality_id: str):
    """Trigger scraping for a specific municipality"""
    result = await scrape_municipality_tax_sales(municipality_id)
    return result

@api_router.post("/scrape-all")
async def scrape_all_municipalities():
    """Trigger scraping for all municipalities"""
    municipalities = await db.municipalities.find().to_list(1000)
    results = []
    
    for municipality in municipalities:
        try:
            result = await scrape_municipality_tax_sales(municipality["id"])
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
            "tax_sale_url": "https://www.halifax.ca/city-hall/property-taxes/tax-sales",
            "region": "Halifax",
            "latitude": 44.6488,
            "longitude": -63.5752
        },
        {
            "name": "Cape Breton Regional Municipality", 
            "website_url": "https://www.cbrm.ns.ca",
            "region": "Cape Breton",
            "latitude": 46.1368,
            "longitude": -60.1942
        },
        {
            "name": "Truro",
            "website_url": "https://www.truro.ca", 
            "region": "Central Nova Scotia",
            "latitude": 45.3676,
            "longitude": -63.2653
        },
        {
            "name": "New Glasgow",
            "website_url": "https://www.newglasgow.ca",
            "region": "Pictou County",
            "latitude": 45.5931,
            "longitude": -62.6488
        },
        {
            "name": "Bridgewater",
            "website_url": "https://www.bridgewater.ca",
            "region": "South Shore",
            "latitude": 44.3776,
            "longitude": -64.5223
        },
        {
            "name": "Yarmouth",
            "website_url": "https://www.townofyarmouth.ca",
            "region": "Southwest Nova Scotia", 
            "latitude": 43.8374,
            "longitude": -66.1175
        },
        {
            "name": "Kentville",
            "website_url": "https://www.kentville.ca",
            "region": "Annapolis Valley",
            "latitude": 45.0777,
            "longitude": -64.4963
        },
        {
            "name": "Antigonish",
            "website_url": "https://www.townofantigonish.ca",
            "region": "Eastern Nova Scotia",
            "latitude": 45.6186,
            "longitude": -61.9986
        }
    ]
    
    created_count = 0
    for muni_data in municipalities:
        municipality = Municipality(**muni_data)
        await db.municipalities.insert_one(municipality.dict())
        created_count += 1
    
    return {"message": f"Initialized {created_count} municipalities"}


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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()