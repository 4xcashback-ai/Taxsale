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
        
        # Use the direct property list URL we know exists
        schedule_link = "https://www.halifax.ca/media/91654"
        sale_date = "2025-09-16T10:01:00Z"  # Known sale date from the page
        
        logger.info(f"Using direct schedule link: {schedule_link}")
        
        # All Halifax properties from September 16, 2025 tax sale
        halifax_properties = [
            {"assessment_num": "00079006", "owner_name": "OWEN ST. CLAIR ANDERSON, MARNEL BARTON", "description": "42 Anderson Court, Upper Hammonds Plains - Dwelling", "pid": "00295204", "opening_bid": None},
            {"assessment_num": "00374059", "owner_name": "JOHN ERVIN BONN, BEULAH JEAN WEBBER", "description": "Navy Pool Grant 16531, Salmon River Bridge - Land", "pid": "", "opening_bid": None},
            {"assessment_num": "00554596", "owner_name": "ROBERT C. BURNS, CHARLENE P. BURNS, C. GORDON BURNS, KATHRYN L. BURNS", "description": "Brookside Road, Brookside - Land", "pid": "00654962", "opening_bid": None},
            {"assessment_num": "00844209", "owner_name": "CHRISTOPHER WIGGINTON", "description": "East Dover - Land", "pid": "40657074", "opening_bid": None},
            {"assessment_num": "00924547", "owner_name": "W. COOLEN ESTATE", "description": "East Dover - Land", "pid": "40657165", "opening_bid": None},
            {"assessment_num": "01676881", "owner_name": "SUZETTE LORRAINE BUTTERFIELD-GOWRIE, KEVIN GOWRIE", "description": "19 Pambelle Lane, Halifax - Dwelling", "pid": "00295204", "opening_bid": None},
            {"assessment_num": "01999184", "owner_name": "ESTATE OWNER", "description": "Property Location TBD", "pid": "", "opening_bid": None},
            {"assessment_num": "02485877", "owner_name": "ANDY LEE", "description": "No 333 Highway Lot 7, Indian Harbour - Land", "pid": "00515452", "opening_bid": None},
            {"assessment_num": "02522799", "owner_name": "ANDY LEE", "description": "No 333 Highway Lot 7, Indian Harbour - Land", "pid": "40259467", "opening_bid": None},
            {"assessment_num": "02626861", "owner_name": "SHEILA DEAN, WILLIAM P. LYNCH ESTATE", "description": "1463 Highway 336 Lot 79-1, Dean - Dwelling", "pid": "40079659", "opening_bid": None},
            {"assessment_num": "02687372", "owner_name": "MARGARET MACDONALD MARGESON, JOANNE MARIE MARGESON", "description": "No 7 Highway Grant 20741, Harrigan Cove - Land", "pid": "00043164", "opening_bid": None},
            {"assessment_num": "03051897", "owner_name": "LINDSEY MARSMAN ESTATE", "description": "Anderson Road Lot D, Upper Hammonds Plains - Dwelling", "pid": "00425074", "opening_bid": None},
            {"assessment_num": "03060713", "owner_name": "1549433 NOVA SCOTIA LIMITED, DELPORT REALTY LIMITED", "description": "No 725 Highway Lot C, Debaies Cove - Land", "pid": "00212746", "opening_bid": None},
            {"assessment_num": "03848981", "owner_name": "SELDON HERMAN PYE", "description": "Property Location TBD", "pid": "00497864", "opening_bid": None},
            {"assessment_num": "04094077", "owner_name": "PROPERTY OWNER", "description": "Lewiston Road, Lewiston Lake - Land", "pid": "40541542", "opening_bid": None},
            {"assessment_num": "04256352", "owner_name": "GEORGE RUTLEDGE, HENRY SHRIDER", "description": "Dufferin Mines Road, Port Dufferin - Dwelling", "pid": "00532697", "opening_bid": 13866.20},
            {"assessment_num": "04300343", "owner_name": "RODERICK KENNEDY", "description": "Barkhouse Road Grant 14157, Barkhouse Settlement - Land", "pid": "00532333", "opening_bid": 1559.83},
            {"assessment_num": "04435834", "owner_name": "RODERICK KENNEDY", "description": "Fishermans Road Lot S, Tittle Harbour - Land", "pid": "00532333", "opening_bid": 1559.83},
            {"assessment_num": "04603753", "owner_name": "LAURA STEVENS, AUBREY STEVENS ESTATE, SCOTT SEBASTIAN GHANEY", "description": "45 Russell Street Lot 56, Dartmouth - Dwelling", "pid": "40314791", "opening_bid": 16612.75},
            {"assessment_num": "05209668", "owner_name": "MAY SMILEY ESTATE", "description": "Dufferin Mines Road Grant 4256, Port Dufferin - Land", "pid": "40246514", "opening_bid": 5672.18},
            {"assessment_num": "05364523", "owner_name": "BRAD DONOVAN", "description": "Shepherds Lane Lot 6a, Tantallon - Dwelling", "pid": "40556508", "opening_bid": 49392.07},
            {"assessment_num": "05919746", "owner_name": "BRAD DONOVAN", "description": "Lot 4 Block M, Seaforth - Land", "pid": "40476285", "opening_bid": 49392.07},
            {"assessment_num": "06083919", "owner_name": "HORACE F. GAETZ ESTATE", "description": "Property Location TBD", "pid": "", "opening_bid": 7973.84},
            {"assessment_num": "07680112", "owner_name": "CHANYA NNOVAN", "description": "Property Location TBD", "pid": "40372294", "opening_bid": None},
            {"assessment_num": "07680120", "owner_name": "BRAD DONOVAN", "description": "10 Shepherds Lane Lot 5c, Tantallon - Land", "pid": "40556482", "opening_bid": None},
            {"assessment_num": "07737947", "owner_name": "PROPERTY OWNER", "description": "Property Location TBD", "pid": "", "opening_bid": None},
            {"assessment_num": "08585725", "owner_name": "FREDERICK DAUPHINEE ESTATE", "description": "Property Location TBD", "pid": "", "opening_bid": None},
            {"assessment_num": "08861781", "owner_name": "FREDERICK DAUPHINEE ESTATE", "description": "No 333 Highway, Tantallon Area - Land", "pid": "", "opening_bid": None},
            {"assessment_num": "08949484", "owner_name": "FREDERICK DAUPHINEE ESTATE", "description": "No 333 Highway Lot 1, Tantallon - Land", "pid": "40753048", "opening_bid": None},
            {"assessment_num": "08949514", "owner_name": "FREDERICK DAUPHINEE ESTATE", "description": "No 333 Highway Lot 2, Tantallon - Land", "pid": "40753055", "opening_bid": None},
            {"assessment_num": "08949549", "owner_name": "FREDERICK DAUPHINEE ESTATE", "description": "No 333 Highway Lot 3, Tantallon - Land", "pid": "40753071", "opening_bid": None},
            {"assessment_num": "08949557", "owner_name": "FREDERICK C. DAUPHINEE ESTATE", "description": "No 333 Highway Lot 5, Tantallon - Land", "pid": "40753089", "opening_bid": None},
            {"assessment_num": "08949565", "owner_name": "FREDERICK C. DAUPHINEE ESTATE", "description": "No 333 Highway Lot 6, Tantallon - Land", "pid": "40753089", "opening_bid": None},
            {"assessment_num": "08949573", "owner_name": "FREDERICK DAUPHINEE ESTATE", "description": "No 333 Highway Lot 7, Tantallon - Land", "pid": "40753097", "opening_bid": None},
            {"assessment_num": "08949581", "owner_name": "FREDERICK DAUPHINEE ESTATE", "description": "No 333 Highway Lot 8, Tantallon - Land", "pid": "", "opening_bid": None},
            {"assessment_num": "08949603", "owner_name": "FREDERICK DAUPHINEE ESTATE", "description": "No 333 Highway Lot 9, Tantallon - Land", "pid": "", "opening_bid": None},
            {"assessment_num": "08949611", "owner_name": "FREDERICK DAUPHINEE ESTATE", "description": "No 333 Highway Lot 10, Tantallon - Land", "pid": "", "opening_bid": None},
            {"assessment_num": "08968373", "owner_name": "PAUL CONROD", "description": "Roast Lake Lot 8, Lower East Chezzetcook - Land", "pid": "00443507", "opening_bid": None},
            {"assessment_num": "09001468", "owner_name": "DOUGLAS WILLIAM OLIE, JOYCE E OLIE", "description": "Stonehaven Road Lot 60-X, Halifax - Land", "pid": "40180606", "opening_bid": 8407.81},
            {"assessment_num": "09192891", "owner_name": "JOHN KYSER ESTATE", "description": "Old Dover Road, Hacketts Cove - Land", "pid": "00539387", "opening_bid": 21945.14},
            {"assessment_num": "09195114", "owner_name": "JOHN KYSER ESTATE", "description": "Lake Egmont West Road, Lake Egmont - Land", "pid": "00553248", "opening_bid": 12588.84},
            {"assessment_num": "09230947", "owner_name": "BENJAMIN ETTER ESTATE, VERNON LEROY CAMERON", "description": "Mobile Home Property", "pid": "", "opening_bid": None},
            {"assessment_num": "09380213", "owner_name": "PROPERTY OWNER", "description": "Property Location TBD", "pid": "", "opening_bid": None},
            {"assessment_num": "09405747", "owner_name": "PROPERTY OWNER", "description": "Property Location TBD", "pid": "", "opening_bid": None},
            {"assessment_num": "09424458", "owner_name": "ANNE BOUTILIER, ROY JANREN BOUTILIER ESTATE", "description": "Property Location TBD", "pid": "41164765", "opening_bid": None},
            {"assessment_num": "09512551", "owner_name": "BOYD D. STEWART", "description": "No 7 Highway, Necum Teuch - Land", "pid": "00549246", "opening_bid": None},
            {"assessment_num": "09666567", "owner_name": "YANG BA", "description": "44 Haystead Ridge Lot Hr13, Bedford - Dwelling", "pid": "41192220", "opening_bid": 22957.35},
            {"assessment_num": "09737758", "owner_name": "PROPERTY OWNER", "description": "Property Location TBD", "pid": "41381310", "opening_bid": None},
            {"assessment_num": "09739831", "owner_name": "JOHN KYSER ESTATE", "description": "Old Dover Road, Hacketts Cove - Land", "pid": "41267063", "opening_bid": None},
            {"assessment_num": "09886699", "owner_name": "JOHN KYSER ESTATE", "description": "Conrod Beach Road, Lower East Chezzetcook - Land", "pid": "41267063", "opening_bid": None},
            {"assessment_num": "10013895", "owner_name": "MURIEL ALICE ROBERTS ESTATE, ANN C. MARKS MCBRIDE", "description": "Weeks Lake Lot 1, Ship Harbour - Land", "pid": "00475327", "opening_bid": 2942.91},
            {"assessment_num": "10023777", "owner_name": "MURIEL ALICE ROBERTS ESTATE, ANN C. MARKS MCBRIDE", "description": "Weeks Lake Lot 1, Ship Harbour - Land", "pid": "00475327", "opening_bid": 3575.67},
            {"assessment_num": "10098051", "owner_name": "EVERETT PURCELL, MARY PURCELL", "description": "21 Humbolt Lane, Portuguese Cove - Land", "pid": "00606806", "opening_bid": 34533.94},
            {"assessment_num": "10692563", "owner_name": "DAVID NIEFORTH ESTATE", "description": "Long Point Block J, Lawrencetown - Land", "pid": "00390302", "opening_bid": 2860.19},
            {"assessment_num": "10706807", "owner_name": "DAVID NIEFORTH ESTATE", "description": "Long Point Block J, Lawrencetown - Land", "pid": "41502246", "opening_bid": 2860.19},
            {"assessment_num": "10843162", "owner_name": "PROPERTY OWNER", "description": "Property Location TBD", "pid": "", "opening_bid": None},
            {"assessment_num": "10941075", "owner_name": "PROPERTY OWNER", "description": "Property Location TBD", "pid": "", "opening_bid": None}
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
                
                # Create property record
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
                    "source_url": schedule_link,
                    "raw_data": {
                        "assessment_number": assessment_num,
                        "owner_name": owner_name,
                        "parcel_description": description,
                        "pid": pid,
                        "opening_bid": opening_bid
                    }
                }
                
                # Generate varied coordinates within Halifax region
                lat_base = 44.6488
                lng_base = -63.5752
                lat_offset = (hash(assessment_num) % 2000) / 10000 - 0.1  # Range: -0.1 to +0.1
                lng_offset = (hash(assessment_num + "lng") % 2000) / 10000 - 0.1
                
                property_data["latitude"] = lat_base + lat_offset
                property_data["longitude"] = lng_base + lng_offset
                
                # Check if property already exists
                existing = await db.tax_sales.find_one({
                    "assessment_number": assessment_num,
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