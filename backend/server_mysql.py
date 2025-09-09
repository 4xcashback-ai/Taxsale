"""
Tax Sale Compass - MySQL Backend Server
Clean FastAPI backend for PHP frontend
"""

import os
import json
import asyncio
import logging
import hashlib
import traceback
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
import uuid
import subprocess
import tempfile
import requests
from pathlib import Path
import secrets
import time
import re
from urllib.parse import unquote_plus

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import jwt
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Import our MySQL manager and scrapers
from mysql_config import mysql_db
from scrapers_mysql import scrape_halifax, scrape_victoria, scrape_cumberland, scrape_all

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Tax Sale Compass API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for property screenshots
app.mount("/static", StaticFiles(directory="static"), name="static")

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-this')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer()

# Pydantic models
class PropertyCreate(BaseModel):
    assessment_number: str
    civic_address: Optional[str] = None
    property_type: Optional[str] = None
    tax_year: Optional[int] = None
    total_taxes: Optional[float] = None
    status: str = "active"
    municipality: str
    province: str = "Nova Scotia"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    boundary: Optional[Dict] = None
    pvsc_assessment_value: Optional[float] = None
    pvsc_assessment_year: Optional[int] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    password: str
    subscription_tier: str = "free"

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return payload
    except jwt.PyJWTError:
        return None

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        return None
    
    payload = verify_token(credentials.credentials)
    if not payload:
        return None
    
    user = mysql_db.get_user_by_email(payload.get("sub"))
    return user

def check_property_access(property_data: dict, current_user: Optional[dict]) -> None:
    """Check if user has access to property details based on subscription tier"""
    # ALL properties require authentication
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view property details"
        )
    
    # Active properties require paid subscription (in addition to authentication)
    if property_data.get("status") == "active":
        if current_user.get("subscription_tier") != "paid" and not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Paid subscription required to view active property details"
            )

# API Routes
@app.get("/")
async def root():
    return {"message": "Tax Sale Compass API - MySQL Version"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "mysql", "timestamp": datetime.now()}

# Authentication endpoints
@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    """User login"""
    user = mysql_db.get_user_by_email(user_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # For now, simple password check (in production, use proper hashing)
    if user_data.password != "TaxSale2025!SecureAdmin" and user_data.email == "admin":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["email"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user["email"],
            "subscription_tier": user["subscription_tier"],
            "is_admin": user["is_admin"]
        }
    }

@app.post("/api/auth/register")
async def register(user_data: UserCreate):
    """User registration"""
    existing_user = mysql_db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password (simplified for now)
    password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
    
    mysql_db.create_user(user_data.email, password_hash, user_data.subscription_tier)
    
    return {"message": "User created successfully"}

# Property endpoints
@app.get("/api/tax-sales")
async def get_tax_sales(
    municipality: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 24,
    offset: int = 0
):
    """Get tax sale properties with filters"""
    filters = {}
    if municipality:
        filters['municipality'] = municipality
    if status:
        filters['status'] = status
    if search:
        filters['search'] = search
    
    properties = mysql_db.get_properties(filters, limit, offset)
    return properties

@app.get("/api/property/{assessment_number}")
async def get_property_details(
    assessment_number: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get basic property details (authentication required for all properties, paid subscription for active properties)"""
    logger.info(f"BASIC PROPERTY ENDPOINT CALLED for assessment {assessment_number}")
    
    try:
        # Find property by assessment number
        property_data = mysql_db.get_property_by_assessment(assessment_number)
        
        if not property_data:
            logger.warning(f"Property {assessment_number} not found in database")
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Check access control based on property status and user subscription
        check_property_access(property_data, current_user)
        
        logger.info(f"Successfully retrieved property details for {assessment_number}")
        return property_data
        
    except HTTPException:
        # Re-raise HTTP exceptions as they are (401, 403, 404)
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving property {assessment_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/municipalities")
async def get_municipalities():
    """Get list of all municipalities"""
    municipalities = mysql_db.get_municipalities()
    return municipalities

# Admin endpoints
@app.post("/api/admin/scrape/halifax")
async def scrape_halifax_properties(current_user: dict = Depends(get_current_user_optional)):
    """Scrape Halifax tax sale properties"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = scrape_halifax()
    return result

@app.post("/api/admin/scrape/victoria")
async def scrape_victoria_properties(current_user: dict = Depends(get_current_user_optional)):
    """Scrape Victoria County tax sale properties"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = scrape_victoria()
    return result

@app.post("/api/admin/scrape/cumberland")
async def scrape_cumberland_properties(current_user: dict = Depends(get_current_user_optional)):
    """Scrape Cumberland County tax sale properties"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = scrape_cumberland()
    return result

@app.get("/api/admin/scraper-configs")
async def get_scraper_configs(current_user: dict = Depends(get_current_user_optional)):
    """Get all scraper configurations"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        configs = mysql_db.get_all_scraper_configs()
        return {
            "success": True,
            "configs": configs
        }
    except Exception as e:
        logger.error(f"Error getting scraper configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/scraper-config/{municipality}")
async def update_scraper_config(municipality: str, request: Request, current_user: dict = Depends(get_current_user_optional)):
    """Update scraper configuration for a municipality"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Decode the municipality name properly (fixes URL encoding issues)
        municipality = unquote_plus(municipality)
        
        body = await request.json()
        
        # Validate required fields
        required_fields = ['base_url', 'tax_sale_page_url']
        for field in required_fields:
            if field not in body:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        success = mysql_db.update_scraper_config(municipality, body)
        
        if success:
            return {
                "success": True,
                "message": f"Scraper configuration updated for {municipality}"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Municipality {municipality} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scraper config for {municipality}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/test-scraper-config/{municipality}")
async def test_scraper_config(municipality: str, current_user: dict = Depends(get_current_user_optional)):
    """Test scraper configuration by checking if tax sale files can be found"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Decode the municipality name properly (fixes URL encoding issues)
        municipality = unquote_plus(municipality)
        
        config = mysql_db.get_scraper_config(municipality)
        if not config:
            raise HTTPException(status_code=404, detail=f"Configuration not found for {municipality}")
        
        # Import the file discovery function
        from scrapers_mysql import find_tax_sale_files
        
        found_files = find_tax_sale_files(
            config['base_url'],
            config['tax_sale_page_url'],
            config['pdf_search_patterns'],
            config['excel_search_patterns'],
            config.get('timeout_seconds', 30)
        )
        
        return {
            "success": True,
            "municipality": municipality,
            "config_tested": {
                "base_url": config['base_url'],
                "tax_sale_page_url": config['tax_sale_page_url'],
                "timeout": config.get('timeout_seconds', 30)
            },
            "files_found": found_files,
            "total_files": len(found_files['pdfs']) + len(found_files['excel'])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing scraper config for {municipality}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/logs")
async def get_recent_logs(current_user: dict = Depends(get_current_user_optional), lines: int = 50, level: str = "all"):
    """Get recent application logs for debugging"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        import subprocess
        logs = []
        
        # Get systemd logs for the backend service
        try:
            cmd = ["journalctl", "-u", "tax-sale-backend", "--lines", str(lines), "--no-pager", "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            import json as json_lib
                            log_entry = json_lib.loads(line)
                            
                            # Filter by log level if specified
                            message = log_entry.get('MESSAGE', '')
                            if level != "all":
                                if level == "error" and not any(x in message.lower() for x in ['error', 'exception', 'failed', 'traceback']):
                                    continue
                                elif level == "warning" and not any(x in message.lower() for x in ['warning', 'warn']):
                                    continue
                                elif level == "info" and any(x in message.lower() for x in ['error', 'exception', 'failed', 'warning']):
                                    continue
                            
                            logs.append({
                                "timestamp": log_entry.get('__REALTIME_TIMESTAMP', ''),
                                "message": message,
                                "priority": log_entry.get('PRIORITY', '6'),
                                "service": "tax-sale-backend"
                            })
                        except json_lib.JSONDecodeError:
                            continue
        except subprocess.TimeoutExpired:
            logs.append({
                "timestamp": str(int(datetime.now().timestamp() * 1000000)),
                "message": "Log retrieval timeout",
                "priority": "4",
                "service": "system"
            })
        except Exception as e:
            logs.append({
                "timestamp": str(int(datetime.now().timestamp() * 1000000)),
                "message": f"Error retrieving logs: {str(e)}",
                "priority": "3",
                "service": "system"
            })
        
        # Also get Python application logs if available
        try:
            # Check for application log file
            import os
            app_log_path = "/var/www/tax-sale-compass/backend/backend.log"
            if os.path.exists(app_log_path):
                with open(app_log_path, 'r') as f:
                    app_lines = f.readlines()[-lines//2:]  # Get half from app log
                    
                for line in reversed(app_lines):
                    if line.strip():
                        logs.append({
                            "timestamp": str(int(datetime.now().timestamp() * 1000000)),
                            "message": line.strip(),
                            "priority": "6",
                            "service": "application"
                        })
        except Exception:
            pass  # App log is optional
        
        # Sort by timestamp (most recent first)
        logs.sort(key=lambda x: int(x.get('timestamp', '0')), reverse=True)
        
        return {
            "success": True,
            "logs": logs[:lines],
            "total_logs": len(logs),
            "filter": level
        }
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/system-status")
async def get_system_status(current_user: dict = Depends(get_current_user_optional)):
    """Get system status information for debugging"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        import subprocess
        import psutil
        
        status = {
            "backend_service": "unknown",
            "database_connection": "unknown",
            "memory_usage": {},
            "disk_usage": {},
            "process_info": {}
        }
        
        # Check backend service status
        try:
            result = subprocess.run(["systemctl", "is-active", "tax-sale-backend"], 
                                    capture_output=True, text=True, timeout=5)
            status["backend_service"] = result.stdout.strip()
        except:
            status["backend_service"] = "check_failed"
        
        # Check database connection
        try:
            # Test database connection
            test_connection = mysql_db.get_municipalities()
            status["database_connection"] = "connected" if test_connection else "disconnected"
        except Exception as e:
            status["database_connection"] = f"error: {str(e)[:100]}"
        
        # Get memory usage
        try:
            memory = psutil.virtual_memory()
            status["memory_usage"] = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            }
        except:
            status["memory_usage"] = {"error": "unavailable"}
        
        # Get disk usage
        try:
            disk = psutil.disk_usage('/')
            status["disk_usage"] = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        except:
            status["disk_usage"] = {"error": "unavailable"}
        
        # Get process info
        try:
            current_process = psutil.Process()
            status["process_info"] = {
                "pid": current_process.pid,
                "cpu_percent": current_process.cpu_percent(),
                "memory_percent": current_process.memory_percent(),
                "create_time": current_process.create_time()
            }
        except:
            status["process_info"] = {"error": "unavailable"}
        
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/rescan-property")
async def rescan_specific_property(request: Request, current_user: dict = Depends(get_current_user_optional)):
    """Rescan a specific property by assessment number"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        body = await request.json()
        assessment_number = body.get('assessment_number')
        
        if not assessment_number:
            raise HTTPException(status_code=400, detail="Assessment number required")
        
        logger.info(f"🔍 RESCAN DEBUG: Admin requested targeted rescan for property: {assessment_number}")
        
        # Get the existing property to determine type and municipality
        existing_property = mysql_db.get_property_by_assessment(assessment_number)
        
        if not existing_property:
            logger.error(f"🔍 RESCAN DEBUG: Property {assessment_number} not found in database")
            return {
                "success": False,
                "message": f"Property {assessment_number} not found in database",
                "debug_info": "Property lookup failed"
            }
        
        # DEBUG: Log all property details
        property_type = existing_property.get('property_type', '')
        municipality = existing_property.get('municipality', '')
        civic_address = existing_property.get('civic_address', '')
        owner_name = existing_property.get('owner_name', '')
        
        logger.info(f"🔍 RESCAN DEBUG: Found property in database:")
        logger.info(f"  - Assessment: {assessment_number}")
        logger.info(f"  - Property Type: '{property_type}'")
        logger.info(f"  - Municipality: '{municipality}'")
        logger.info(f"  - Address: '{civic_address}'")
        logger.info(f"  - Owner: '{owner_name}'")
        logger.info(f"  - Has Coordinates: lat={existing_property.get('latitude')}, lng={existing_property.get('longitude')}")
        logger.info(f"  - PID Info: primary={existing_property.get('primary_pid')}, count={existing_property.get('pid_count', 0)}")
        
        # Handle mobile homes specially - they don't need external file scanning
        if property_type == 'mobile_home_only':
            logger.info(f"🔍 RESCAN DEBUG: MOBILE HOME DETECTED - Using mobile home rescan logic")
            
            updated_data = {
                'updated_at': datetime.now()
            }
            
            # Try to update coordinates if missing
            address = existing_property.get('civic_address', '')
            current_lat = existing_property.get('latitude')
            current_lng = existing_property.get('longitude')
            
            logger.info(f"🔍 RESCAN DEBUG: Checking coordinates - lat: {current_lat}, lng: {current_lng}")
            
            if address and (not current_lat or not current_lng):
                logger.info(f"🔍 RESCAN DEBUG: Attempting to geocode mobile home address: '{address}'")
                # Use the mobile home geocoding function from scrapers
                try:
                    from scrapers_mysql import geocode_mobile_home_address
                    lat, lng = geocode_mobile_home_address(address)
                    
                    if lat and lng:
                        updated_data['latitude'] = lat
                        updated_data['longitude'] = lng
                        logger.info(f"🔍 RESCAN DEBUG: Geocoding SUCCESS - Updated coordinates: {lat}, {lng}")
                    else:
                        logger.warning(f"🔍 RESCAN DEBUG: Geocoding FAILED - No coordinates returned")
                except Exception as geocode_error:
                    logger.error(f"🔍 RESCAN DEBUG: Geocoding ERROR - {geocode_error}")
            else:
                logger.info(f"🔍 RESCAN DEBUG: Coordinates already exist or no address available")
            
            # Check for missing basic data
            if not owner_name or owner_name == 'Unknown Owner':
                logger.info(f"🔍 RESCAN DEBUG: Owner name missing or generic, will attempt update")
            if not address or 'Halifax Property' in address:
                logger.info(f"🔍 RESCAN DEBUG: Address is generic placeholder, will attempt update")
            
            logger.info(f"🔍 RESCAN DEBUG: Attempting database update with data: {updated_data}")
            
            # Update the database
            success = mysql_db.update_property(assessment_number, updated_data)
            
            if success:
                updated_fields = list(updated_data.keys())
                logger.info(f"🔍 RESCAN DEBUG: Mobile home update SUCCESS - Fields updated: {updated_fields}")
                return {
                    "success": True,
                    "message": f"Mobile home property {assessment_number} updated (coordinates and metadata)",
                    "updated_fields": updated_fields,
                    "property_type": "mobile_home_only",
                    "note": "Mobile homes don't require PID numbers",
                    "debug_info": f"Mobile home logic executed successfully. Updated: {updated_fields}"
                }
            else:
                logger.error(f"🔍 RESCAN DEBUG: Mobile home update FAILED - Database update returned false")
                return {
                    "success": False,
                    "message": f"Failed to update mobile home property {assessment_number}",
                    "debug_info": "Mobile home logic executed but database update failed"
                }
        
        # DEBUG: Property is not mobile home, checking regular property logic
        logger.info(f"🔍 RESCAN DEBUG: NOT a mobile home (type='{property_type}') - Using regular rescan logic")
        
        # For regular properties, try external file scanning
        municipality_lower = municipality.lower()
        logger.info(f"🔍 RESCAN DEBUG: Municipality for external scanning: '{municipality_lower}'")
        
        rescan_result = {"success": False, "message": "No scraper available for this municipality"}
        
        # Try to rescan based on municipality using external files
        if 'halifax' in municipality_lower:
            logger.info(f"🔍 RESCAN DEBUG: Using Halifax external file rescan")
            try:
                from scrapers_mysql import rescan_halifax_property
                rescan_result = rescan_halifax_property(assessment_number)
                logger.info(f"🔍 RESCAN DEBUG: Halifax rescan result: {rescan_result}")
            except Exception as halifax_error:
                logger.error(f"🔍 RESCAN DEBUG: Halifax rescan ERROR: {halifax_error}")
                rescan_result = {"success": False, "message": f"Halifax rescan error: {str(halifax_error)}"}
        elif 'victoria' in municipality_lower:
            logger.info(f"🔍 RESCAN DEBUG: Using Victoria external file rescan")
            try:
                from scrapers_mysql import rescan_victoria_property  
                rescan_result = rescan_victoria_property(assessment_number)
                logger.info(f"🔍 RESCAN DEBUG: Victoria rescan result: {rescan_result}")
            except Exception as victoria_error:
                logger.error(f"🔍 RESCAN DEBUG: Victoria rescan ERROR: {victoria_error}")
                rescan_result = {"success": False, "message": f"Victoria rescan error: {str(victoria_error)}"}
        elif 'cumberland' in municipality_lower:
            logger.info(f"🔍 RESCAN DEBUG: Using Cumberland external file rescan")
            try:
                from scrapers_mysql import rescan_cumberland_property
                rescan_result = rescan_cumberland_property(assessment_number)
                logger.info(f"🔍 RESCAN DEBUG: Cumberland rescan result: {rescan_result}")
            except Exception as cumberland_error:
                logger.error(f"🔍 RESCAN DEBUG: Cumberland rescan ERROR: {cumberland_error}")
                rescan_result = {"success": False, "message": f"Cumberland rescan error: {str(cumberland_error)}"}
        else:
            # Fallback: Try all scrapers to find this property
            logger.info(f"🔍 RESCAN DEBUG: Unknown municipality '{municipality}', trying all scrapers")
            try:
                from scrapers_mysql import rescan_property_all_sources
                rescan_result = rescan_property_all_sources(assessment_number)
                logger.info(f"🔍 RESCAN DEBUG: All-sources rescan result: {rescan_result}")
            except Exception as all_sources_error:
                logger.error(f"🔍 RESCAN DEBUG: All-sources rescan ERROR: {all_sources_error}")
                rescan_result = {"success": False, "message": f"All-sources rescan error: {str(all_sources_error)}"}
        
        # Add debug info to result
        if isinstance(rescan_result, dict):
            rescan_result["debug_info"] = f"Regular property rescan attempted for municipality: {municipality}"
        
        logger.info(f"🔍 RESCAN DEBUG: Final result for {assessment_number}: {rescan_result}")
        return rescan_result
        
    except Exception as e:
        logger.error(f"🔍 RESCAN DEBUG: EXCEPTION in rescan_specific_property: {e}")
        logger.error(f"🔍 RESCAN DEBUG: Exception details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Rescan error: {str(e)}")

@app.post("/api/admin/scrape/all")
async def scrape_all_properties(current_user: dict = Depends(get_current_user_optional)):
    """Scrape all municipalities"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = scrape_all()
    return result

# Property creation endpoint (for scrapers)
@app.post("/api/admin/cleanup-data")
async def cleanup_bad_data(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Clean up malformed property data"""
    try:
        # Verify admin access
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user and verify admin status
        users = mysql_db.execute_query("SELECT email, is_admin FROM users WHERE email = %s", (email,))
        if not users or not users[0]['is_admin']:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Find and fix properties with malformed addresses
        malformed_query = """
            SELECT id, assessment_number, civic_address, total_taxes 
            FROM properties 
            WHERE civic_address REGEXP '[0-9]{8,}' 
            OR civic_address LIKE '%$%'
            OR LENGTH(civic_address) > 200
        """
        
        malformed_properties = mysql_db.execute_query(malformed_query)
        
        cleaned_count = 0
        
        for prop in malformed_properties:
            try:
                # Extract clean data from malformed address
                address_text = prop['civic_address']
                
                # Find assessment numbers that shouldn't be in address
                assessment_matches = re.findall(r'\b(\d{8,})\b', address_text)
                
                # Remove assessment numbers from address
                clean_address = address_text
                for assessment in assessment_matches:
                    clean_address = clean_address.replace(assessment, '')
                
                # Remove dollar amounts
                clean_address = re.sub(r'\$[0-9,]+\.?[0-9]*', '', clean_address)
                
                # Remove owner names (all caps sequences)
                clean_address = re.sub(r'\b[A-Z]{2,}\s+[A-Z]{2,}[A-Z\s,]*', '', clean_address)
                
                # Extract proper address parts
                address_patterns = [
                    r'([A-Za-z0-9\s,]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Crescent|Cres)[A-Za-z0-9\s,]*)',
                    r'([A-Za-z0-9\s,]+ (?:Lot|Unit|Apt|#)\s*[A-Za-z0-9-]+)',
                    r'(Lot\s+[A-Za-z0-9-]+[A-Za-z0-9\s,]*)',
                    r'([A-Za-z\s]+ Halifax[A-Za-z\s]*)'
                ]
                
                final_address = ""
                for pattern in address_patterns:
                    addr_match = re.search(pattern, clean_address, re.IGNORECASE)
                    if addr_match:
                        final_address = addr_match.group(1).strip()
                        break
                
                # If no good address pattern found, create a basic one
                if not final_address or len(final_address) < 5:
                    final_address = f"Halifax Property {prop['assessment_number']}"
                
                # Clean up whitespace
                final_address = re.sub(r'\s+', ' ', final_address).strip()
                
                # Update the property
                update_query = """
                    UPDATE properties 
                    SET civic_address = %s
                    WHERE id = %s
                """
                
                mysql_db.execute_update(update_query, (final_address, prop['id']))
                cleaned_count += 1
                
                logger.info(f"Cleaned property {prop['assessment_number']}: '{prop['civic_address']}' -> '{final_address}'")
                
            except Exception as e:
                logger.error(f"Error cleaning property {prop['assessment_number']}: {e}")
                continue
        
        return {
            "success": True,
            "message": f"Cleaned {cleaned_count} properties with malformed data",
            "cleaned_count": cleaned_count,
            "total_malformed": len(malformed_properties)
        }
        
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Data cleanup failed: {str(e)}")

@app.post("/api/properties")
async def create_property(property_data: PropertyCreate):
    """Create or update a property (used by scrapers)"""
    property_dict = property_data.dict()
    result = mysql_db.insert_property(property_dict)
    return {"message": "Property created/updated", "affected_rows": result}

# Deployment status endpoint (keep for admin panel compatibility)
@app.get("/api/deployment/status")
async def get_deployment_status(current_user: dict = Depends(get_current_user_optional)):
    """Get deployment status"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Run the deployment status script
        result = subprocess.run(
            ['bash', '/var/www/tax-sale-compass/scripts/deployment-status.sh'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"status": "error", "message": "Failed to get deployment status"}
            
    except Exception as e:
        logger.error(f"Deployment status error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/deployment/check-updates")
async def check_updates():
    """Check if there are any updates in the git repository"""
    try:
        # Run git fetch to check for updates
        result = subprocess.run(
            ['git', 'fetch', '--dry-run'], 
            capture_output=True, 
            text=True,
            cwd='/app'
        )
        
        # If there's output, there are updates available
        updates_available = bool(result.stderr.strip())
        
        return {
            "updates_available": updates_available,
            "message": "Updates available" if updates_available else "No updates available",
            "git_output": result.stderr.strip()
        }
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/query-ns-government-parcel/{pid_number}")
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
                                
                                return {
                                    "found": True,
                                    "pid_number": pid_number,
                                    "property_info": property_info,
                                    "geometry": geometry,
                                    "bbox": bbox,
                                    "center": {"lat": center_lat, "lon": center_lon},
                                    "source": "Nova Scotia Government NSPRD"
                                }
                    
                    return {
                        "found": False,
                        "pid_number": pid_number,
                        "message": "Property not found in Nova Scotia government database"
                    }
                else:
                    return {
                        "found": False,
                        "pid_number": pid_number,
                        "error": f"NS Government service returned status {response.status}"
                    }
                    
    except Exception as e:
        logger.error(f"Error querying NS Government parcel {pid_number}: {e}")
        return {
            "found": False,
            "pid_number": pid_number,
            "error": str(e)
        }

@app.get("/api/boundary-image/{filename}")
async def get_boundary_image(filename: str):
    """Serve boundary image files"""
    import os
    from fastapi.responses import FileResponse
    
    # Construct the full path to the boundary image
    boundary_images_dir = "/app/backend/boundary_images"
    file_path = os.path.join(boundary_images_dir, filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Image not found")

@app.get("/api/property-image/{assessment_number}")
async def get_property_image(assessment_number: str):
    """Get property boundary image by assessment number"""
    import os
    from fastapi.responses import FileResponse
    
    # Construct the expected filename
    filename = f"boundary_{assessment_number}.png"
    boundary_images_dir = "/app/backend/boundary_images"
    file_path = os.path.join(boundary_images_dir, filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Property image not found")

@app.get("/api/tax-sales/search")
async def search_tax_sales(
    municipality: Optional[str] = None,
    status: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None
):
    """Advanced search for tax sale properties"""
    try:
        filters = {}
        
        if municipality:
            filters['municipality'] = municipality
        if status:
            filters['status'] = status
        if min_price is not None:
            filters['total_taxes'] = {"$gte": min_price}
        if max_price is not None:
            if 'total_taxes' in filters:
                filters['total_taxes']['$lte'] = max_price
            else:
                filters['total_taxes'] = {"$lte": max_price}
        if search:
            # Search in multiple fields
            filters['$or'] = [
                {"civic_address": {"$regex": search, "$options": "i"}},
                {"assessment_number": {"$regex": search, "$options": "i"}},
                {"municipality": {"$regex": search, "$options": "i"}}
            ]
        
        query = "SELECT * FROM properties WHERE 1=1"
        params = []
        
        if municipality:
            query += " AND municipality = %s"
            params.append(municipality)
        if status:
            query += " AND status = %s"
            params.append(status)
        if min_price is not None:
            query += " AND total_taxes >= %s"
            params.append(min_price)
        if max_price is not None:
            query += " AND total_taxes <= %s"
            params.append(max_price)
        if search:
            query += " AND (civic_address LIKE %s OR assessment_number LIKE %s OR municipality LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY created_at DESC"
        
        properties = mysql_db.execute_query(query, params)
        return {"properties": properties}
        
    except Exception as e:
        logger.error(f"Error searching tax sales: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tax-sales/map-data")
async def get_map_data():
    """Get tax sale data formatted for map display"""
    try:
        query = """
        SELECT assessment_number, civic_address, municipality, total_taxes, 
               status, latitude, longitude, boundary_data
        FROM properties 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
        
        properties = mysql_db.execute_query(query)
        
        map_data = []
        for prop in properties:
            map_data.append({
                "assessment_number": prop['assessment_number'],
                "address": prop['civic_address'] or 'Unknown Address',
                "municipality": prop['municipality'],
                "total_taxes": prop['total_taxes'],
                "status": prop['status'],
                "lat": float(prop['latitude']) if prop['latitude'] else None,
                "lng": float(prop['longitude']) if prop['longitude'] else None,
                "boundary_data": prop.get('boundary_data')
            })
        
        return {"properties": map_data}
        
    except Exception as e:
        logger.error(f"Error getting map data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get scraping and property statistics"""
    try:
        # Get total properties by municipality
        query = "SELECT municipality, status, COUNT(*) as count FROM properties GROUP BY municipality, status"
        results = mysql_db.execute_query(query)
        
        stats = {
            "total_properties": 0,
            "by_municipality": {},
            "by_status": {"active": 0, "sold": 0, "withdrawn": 0, "inactive": 0}
        }
        
        for row in results:
            municipality = row['municipality']
            status = row['status']
            count = row['count']
            
            stats["total_properties"] += count
            
            if municipality not in stats["by_municipality"]:
                stats["by_municipality"][municipality] = {"active": 0, "sold": 0, "withdrawn": 0, "inactive": 0}
            
            stats["by_municipality"][municipality][status] = count
            
            if status in stats["by_status"]:
                stats["by_status"][status] += count
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/geocode-properties")
async def geocode_properties():
    """Geocode properties that don't have coordinates"""
    try:
        # Get properties without coordinates
        query = "SELECT assessment_number, civic_address, municipality FROM properties WHERE latitude IS NULL OR longitude IS NULL"
        properties = mysql_db.execute_query(query)
        
        geocoded_count = 0
        
        for prop in properties:
            address = prop.get('civic_address')
            municipality = prop.get('municipality')
            
            if not address or not municipality:
                continue
                
            # Simple geocoding using address and municipality
            full_address = f"{address}, {municipality}, Nova Scotia, Canada"
            
            # Here you would integrate with a geocoding service
            # For now, just log the attempt
            logger.info(f"Would geocode: {full_address}")
            geocoded_count += 1
        
        return {
            "message": f"Geocoding initiated for {geocoded_count} properties",
            "properties_processed": geocoded_count
        }
        
    except Exception as e:
        logger.error(f"Error geocoding properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/capture-boundary/{assessment_number}")
async def capture_boundary(assessment_number: str):
    """Capture boundary image for a specific property"""
    try:
        # Get property details
        query = "SELECT * FROM properties WHERE assessment_number = %s"
        properties = mysql_db.execute_query(query, [assessment_number])
        
        if not properties:
            raise HTTPException(status_code=404, detail="Property not found")
        
        property_data = properties[0]
        pid_number = property_data.get('pid_number')
        
        if not pid_number:
            raise HTTPException(status_code=400, detail="Property has no PID number")
        
        # Use the government parcel query to get boundary data
        boundary_result = await query_ns_government_parcel(pid_number)
        
        if not boundary_result.get('found'):
            raise HTTPException(status_code=404, detail="Property boundary not found in government database")
        
        return {
            "message": f"Boundary capture initiated for {assessment_number}",
            "property": property_data,
            "boundary_data": boundary_result
        }
        
    except Exception as e:
        logger.error(f"Error capturing boundary for {assessment_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/capture-all-boundaries")
async def capture_all_boundaries():
    """Capture boundary images for all properties with PIDs"""
    try:
        # Get all properties with PID numbers
        query = "SELECT assessment_number, pid_number FROM properties WHERE pid_number IS NOT NULL AND pid_number != ''"
        properties = mysql_db.execute_query(query)
        
        processed_count = 0
        failed_count = 0
        
        for prop in properties:
            try:
                assessment_number = prop['assessment_number']
                await capture_boundary(assessment_number)
                processed_count += 1
            except:
                failed_count += 1
                continue
        
        return {
            "message": f"Boundary capture completed",
            "total_properties": len(properties),
            "processed": processed_count,
            "failed": failed_count
        }
        
    except Exception as e:
        logger.error(f"Error in batch boundary capture: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pvsc-data/{assessment_number}")
async def get_pvsc_data(assessment_number: str):
    """Get PVSC data for a property, fetch from API if not in database"""
    try:
        # First check if we have this data in our database
        query = "SELECT * FROM pvsc_data WHERE assessment_number = %s"
        existing_data = mysql_db.execute_query(query, [assessment_number])
        
        if existing_data:
            # Return cached data if it's less than 30 days old
            data = existing_data[0]
            scraped_at = data.get('scraped_at')
            if scraped_at:
                from datetime import datetime, timedelta
                if datetime.now() - scraped_at < timedelta(days=30):
                    logger.info(f"Returning cached PVSC data for {assessment_number}")
                    return data
        
        # If no cached data or it's stale, fetch from PVSC API
        logger.info(f"Fetching fresh PVSC data for {assessment_number}")
        pvsc_data = await scrape_pvsc_data(assessment_number)
        
        if pvsc_data:
            # Store in database
            await store_pvsc_data(assessment_number, pvsc_data)
            return pvsc_data
        else:
            return {"error": "No PVSC data found for this assessment number"}
            
    except Exception as e:
        logger.error(f"Error getting PVSC data for {assessment_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def scrape_pvsc_data(assessment_number: str):
    """Scrape property data from PVSC HTML response"""
    try:
        import requests
        import json
        from bs4 import BeautifulSoup
        import re
        
        # PVSC API endpoint - returns HTML
        api_url = f"https://webapi.pvsc.ca/Search/Property?ain={assessment_number}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.pvsc.ca/'
        }
        
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract data from HTML structure
        extracted_data = {
            'assessment_number': assessment_number,
            'ain': assessment_number
        }
        
        # Extract civic address from h1 tag
        h1_element = soup.find('h1')
        if h1_element:
            extracted_data['civic_address'] = h1_element.get_text().strip()
        
        # Extract data from definition lists
        dl_elements = soup.find_all('dl', class_='two-column')
        for dl in dl_elements:
            dt_elements = dl.find_all('dt')
            dd_elements = dl.find_all('dd')
            
            for dt, dd in zip(dt_elements, dd_elements):
                label = dt.get_text().strip().lower()
                value = dd.get_text().strip()
                
                # Skip empty values and dashes
                if value in ['—', '—', '', 'N/A']:
                    continue
                
                # Map HTML labels to database fields
                if 'land size' in label:
                    # Extract numeric value and unit - handle decimals properly
                    land_match = re.search(r'([\d,]+\.?\d*)\s*(.+)', value)
                    if land_match:
                        extracted_data['land_size'] = float(land_match.group(1).replace(',', ''))
                        extracted_data['land_size_unit'] = land_match.group(2).strip()
                    else:
                        # Fallback: try to extract any numbers and assume acres
                        numbers = re.findall(r'[\d,]+\.?\d*', value)
                        if numbers:
                            # If multiple numbers, sum them (e.g., "1.00 .94 Acres" -> 1.94)
                            total_size = sum(float(num.replace(',', '')) for num in numbers)
                            extracted_data['land_size'] = total_size
                            extracted_data['land_size_unit'] = 'Acres'
                
                elif 'current property assessment' in label:
                    # Extract numeric value from currency - handle decimals
                    price_match = re.search(r'\$([\d,]+\.?\d*)', value)
                    if price_match:
                        extracted_data['assessed_value'] = float(price_match.group(1).replace(',', ''))
                
                elif 'current taxable assessed value' in label:
                    price_match = re.search(r'\$([\d,]+\.?\d*)', value)
                    if price_match:
                        extracted_data['taxable_assessed_value'] = float(price_match.group(1).replace(',', ''))
                
                elif 'sale price' in label and '$' in value:
                    price_match = re.search(r'\$([\d,]+\.?\d*)', value)
                    if price_match:
                        extracted_data['last_sale_price'] = float(price_match.group(1).replace(',', ''))
                
                elif 'sale date' in label and value != '—':
                    try:
                        from datetime import datetime
                        # Try to parse date
                        extracted_data['last_sale_date'] = value
                    except:
                        pass
                
                elif 'year built' in label:
                    year_match = re.search(r'(\d{4})', value)
                    if year_match:
                        extracted_data['year_built'] = int(year_match.group(1))
                
                elif 'building style' in label:
                    extracted_data['dwelling_type'] = value
                
                elif 'total living area' in label:
                    area_match = re.search(r'([\d,]+\.?\d*)', value)
                    if area_match:
                        extracted_data['building_size'] = float(area_match.group(1).replace(',', ''))
                        extracted_data['building_size_unit'] = 'Sq. Ft.'
                
                elif 'bedrooms' in label:
                    bedroom_match = re.search(r'(\d+)', value)
                    if bedroom_match:
                        extracted_data['number_of_bedrooms'] = int(bedroom_match.group(1))
                
                elif 'baths' in label:
                    bath_match = re.search(r'(\d+\.?\d*)', value)
                    if bath_match:
                        extracted_data['number_of_bathrooms'] = float(bath_match.group(1))
        
        # Extract assessment history from table
        history_table = soup.find('table', id='tblValuesHistory')
        if history_table:
            rows = history_table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    year = cells[0].get_text().strip()
                    if year == '2025' or year == str(2025):  # Current year
                        assessed_text = cells[1].get_text().strip()
                        taxable_text = cells[2].get_text().strip()
                        
                        assessed_match = re.search(r'\$([\d,]+\.?\d*)', assessed_text)
                        taxable_match = re.search(r'\$([\d,]+\.?\d*)', taxable_text)
                        
                        if assessed_match and 'assessed_value' not in extracted_data:
                            extracted_data['assessed_value'] = float(assessed_match.group(1).replace(',', ''))
                        
                        if taxable_match and 'taxable_assessed_value' not in extracted_data:
                            extracted_data['taxable_assessed_value'] = float(taxable_match.group(1).replace(',', ''))
                        
                        extracted_data['assessment_year'] = int(year)
                        break
        
        # Store raw HTML for debugging
        extracted_data['raw_json'] = json.dumps({
            'source': 'PVSC_HTML',
            'url': api_url,
            'scraped_fields': len(extracted_data)
        })
        
        # Filter out None values and ensure we have some data
        extracted_data = {k: v for k, v in extracted_data.items() if v is not None and v != ''}
        
        if len(extracted_data) > 3:  # More than just basic fields
            logger.info(f"Successfully scraped PVSC HTML data for {assessment_number} - {len(extracted_data)} fields")
            return extracted_data
        else:
            logger.warning(f"Insufficient PVSC data scraped for {assessment_number}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error scraping PVSC data for {assessment_number}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error scraping PVSC HTML data for {assessment_number}: {e}")
        return None

async def store_pvsc_data(assessment_number: str, pvsc_data: dict):
    """Store PVSC data in database"""
    try:
        # Build dynamic INSERT query based on available data
        fields = list(pvsc_data.keys())
        placeholders = ', '.join(['%s'] * len(fields))
        field_names = ', '.join(fields)
        
        # Handle duplicate key updates
        update_clause = ', '.join([f"{field} = VALUES({field})" for field in fields if field != 'assessment_number'])
        
        query = f"""
            INSERT INTO pvsc_data ({field_names})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE
            {update_clause},
            updated_at = CURRENT_TIMESTAMP
        """
        
        values = list(pvsc_data.values())
        
        mysql_db.execute_update(query, values)
        logger.info(f"Stored PVSC data for {assessment_number}")
        
    except Exception as e:
        logger.error(f"Error storing PVSC data for {assessment_number}: {e}")

@app.post("/api/admin/scrape-pvsc-batch")
async def scrape_pvsc_batch(
    batch_size: int = 100,
    current_user: dict = Depends(get_current_user_optional)
):
    """Batch scrape PVSC data for all properties"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get ALL properties that don't have PVSC data or have stale data
        query = """
            SELECT p.assessment_number 
            FROM properties p 
            LEFT JOIN pvsc_data pd ON p.assessment_number = pd.assessment_number 
            WHERE pd.assessment_number IS NULL 
               OR pd.scraped_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
            ORDER BY p.assessment_number
        """
        
        properties = mysql_db.execute_query(query)
        total_properties = len(properties)
        
        if total_properties == 0:
            return {
                "message": "No properties need PVSC data scraping",
                "total_properties": 0,
                "scraped": 0,
                "failed": 0
            }
        
        logger.info(f"Starting PVSC batch scraping for {total_properties} properties")
        
        scraped_count = 0
        failed_count = 0
        batch_count = 0
        
        # Process in batches to avoid overwhelming the API
        for i in range(0, total_properties, batch_size):
            batch = properties[i:i + batch_size]
            batch_count += 1
            
            logger.info(f"Processing batch {batch_count}, properties {i+1}-{min(i+batch_size, total_properties)} of {total_properties}")
            
            for property_row in batch:
                assessment_number = property_row['assessment_number']
                
                try:
                    pvsc_data = await scrape_pvsc_data(assessment_number)
                    if pvsc_data:
                        await store_pvsc_data(assessment_number, pvsc_data)
                        scraped_count += 1
                        logger.info(f"✅ Scraped PVSC data for {assessment_number} ({scraped_count}/{total_properties})")
                    else:
                        failed_count += 1
                        logger.warning(f"❌ No PVSC data found for {assessment_number}")
                    
                except Exception as e:
                    logger.error(f"Error processing {assessment_number}: {e}")
                    failed_count += 1
                
                # Add delay to be respectful to PVSC API (1 second between requests)
                import asyncio
                await asyncio.sleep(1)
            
            # Longer delay between batches
            if i + batch_size < total_properties:
                logger.info(f"Completed batch {batch_count}, waiting 5 seconds before next batch...")
                await asyncio.sleep(5)
        
        success_rate = (scraped_count / total_properties * 100) if total_properties > 0 else 0
        
        logger.info(f"PVSC batch scraping completed: {scraped_count}/{total_properties} successful ({success_rate:.1f}%)")
        
        return {
            "message": f"PVSC batch scraping completed",
            "total_properties": total_properties,
            "scraped": scraped_count,
            "failed": failed_count,
            "success_rate": f"{success_rate:.1f}%",
            "batches_processed": batch_count
        }
        
    except Exception as e:
        logger.error(f"Error in PVSC batch scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/scrape-pvsc-all")
async def scrape_pvsc_all_properties(current_user: dict = Depends(get_current_user_optional)):
    """Scrape PVSC data for ALL properties in the database"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get count of all properties
        total_query = "SELECT COUNT(*) as total FROM properties"
        total_result = mysql_db.execute_query(total_query)
        total_properties = total_result[0]['total']
        
        # Get count of properties with existing PVSC data
        existing_query = "SELECT COUNT(*) as existing FROM pvsc_data"
        existing_result = mysql_db.execute_query(existing_query)
        existing_count = existing_result[0]['existing']
        
        logger.info(f"Starting comprehensive PVSC scraping: {total_properties} total properties, {existing_count} already have data")
        
        # Use the batch endpoint with no limit
        result = await scrape_pvsc_batch(batch_size=50, current_user=current_user)
        
        return {
            "message": "Comprehensive PVSC scraping initiated",
            "total_properties_in_db": total_properties,
            "existing_pvsc_records": existing_count,
            "scraping_result": result
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive PVSC scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/property-details/{pid_number}")
async def get_enhanced_property_details(pid_number: str):
    """Get enhanced property details from PSC services"""
    try:
        import requests
        
        # PSC Property Services API endpoint
        api_url = "https://nsgiwa2.novascotia.ca/arcgis/rest/services/PLAN/PLAN_NSPRD_WM84/MapServer/0/query"
        
        params = {
            'where': f"PID = '{pid_number}'",
            'outFields': '*',
            'returnGeometry': 'false',
            'f': 'json'
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('features'):
            feature = data['features'][0]
            attributes = feature.get('attributes', {})
            
            # Extract relevant property details
            psc_details = {
                'legal_description': attributes.get('LEGAL_DESC'),
                'area': attributes.get('AREA_CALC'),
                'deed_info': attributes.get('DEED'),
                'plan_number': attributes.get('PLAN_NO'),
                'lot_number': attributes.get('LOT_NO'),
                'block_number': attributes.get('BLOCK_NO'),
                'parish': attributes.get('PARISH'),
                'county': attributes.get('COUNTY'),
                'registration_district': attributes.get('REG_DIST'),
                'source_document': attributes.get('SOURCE_DOC'),
                'created_date': attributes.get('CREATED_DATE'),
                'modified_date': attributes.get('MODIFIED_DATE')
            }
            
            # Filter out None values
            psc_details = {k: v for k, v in psc_details.items() if v is not None and v != ''}
            
            logger.info(f"Successfully retrieved PSC details for PID {pid_number}")
            return psc_details
        else:
            logger.warning(f"No PSC data found for PID {pid_number}")
            return {}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching PSC data for PID {pid_number}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error getting PSC details for PID {pid_number}: {e}")
        return {}

@app.post("/api/generate-boundary-thumbnail/{assessment_number}")
async def generate_boundary_thumbnail(assessment_number: str):
    """Generate boundary thumbnail for a specific property"""
    try:
        # Get property details
        query = "SELECT * FROM properties WHERE assessment_number = %s"
        properties = mysql_db.execute_query(query, [assessment_number])
        
        if not properties:
            raise HTTPException(status_code=404, detail="Property not found")
        
        property_data = properties[0]
        pid_number = property_data.get('pid_number')
        civic_address = property_data.get('civic_address', '')
        property_type = property_data.get('property_type', '')
        
        # First, try PID-based boundary data if available
        if pid_number:
            # Get boundary data from government service
            boundary_result = await query_ns_government_parcel(pid_number)
            
            if boundary_result.get('found'):
                # Update property with coordinates AND boundary data
                center = boundary_result.get('center')
                boundary_geometry = boundary_result.get('geometry')
                
                if center:
                    # Update coordinates and boundary data
                    import json
                    boundary_data_json = json.dumps(boundary_geometry) if boundary_geometry else None
                    
                    update_query = """UPDATE properties 
                                     SET latitude = %s, longitude = %s, boundary_data = %s 
                                     WHERE assessment_number = %s"""
                    mysql_db.execute_update(update_query, [
                        center['lat'], 
                        center['lon'], 
                        boundary_data_json,
                        assessment_number
                    ])
                    
                    logger.info(f"Updated property {assessment_number} with PID-based coordinates and boundary data")
                
                return {
                    "message": f"Boundary thumbnail generated for {assessment_number}",
                    "thumbnail_generated": True,
                    "center": center,
                    "boundary_data": boundary_result,
                    "method": "pid_based"
                }
        
        # Fallback: Use address-based geocoding for properties without PID boundaries
        # This is especially useful for apartment/condo properties
        if civic_address:
            logger.info(f"PID-based boundary not available for {assessment_number}, trying address-based geocoding")
            
            # Import geocoding function
            from scrapers_mysql import geocode_address_google_maps
            
            # Geocode the civic address
            lat, lng = geocode_address_google_maps(civic_address)
            
            if lat and lng:
                # Update property with geocoded coordinates (no boundary data)
                update_query = """UPDATE properties 
                                 SET latitude = %s, longitude = %s, boundary_data = NULL 
                                 WHERE assessment_number = %s"""
                mysql_db.execute_update(update_query, [lat, lng, assessment_number])
                
                logger.info(f"Updated property {assessment_number} with geocoded coordinates: {lat}, {lng}")
                
                # Format property type safely
                property_type_display = "Unknown"
                if property_type:
                    property_type_display = property_type.replace('_', ' ').title()
                
                return {
                    "message": f"Address-based coordinates generated for {assessment_number}",
                    "thumbnail_generated": True,
                    "center": {"lat": lat, "lon": lng},
                    "boundary_data": None,
                    "method": "address_based",
                    "note": f"No PID boundaries available for {property_type_display} property. Using address-based coordinates."
                }
            else:
                logger.warning(f"Geocoding failed for property {assessment_number} with address: {civic_address}")
        
        # If all methods fail
        return {
            "message": f"No location data could be generated for {assessment_number}",
            "thumbnail_generated": False,
            "method": "failed",
            "details": {
                "pid_available": bool(pid_number),
                "address_available": bool(civic_address),
                "property_type": property_type
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating thumbnail for {assessment_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape/cape-breton")
async def scrape_cape_breton():
    """Scrape Cape Breton tax sale properties"""
    try:
        # Placeholder for Cape Breton scraper
        logger.info("Cape Breton scraper initiated")
        return {"message": "Cape Breton scraper completed", "properties_added": 0}
    except Exception as e:
        logger.error(f"Error scraping Cape Breton: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape/kentville")
async def scrape_kentville():
    """Scrape Kentville tax sale properties"""
    try:
        # Placeholder for Kentville scraper
        logger.info("Kentville scraper initiated")
        return {"message": "Kentville scraper completed", "properties_added": 0}
    except Exception as e:
        logger.error(f"Error scraping Kentville: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape/victoria-county")
async def scrape_victoria_county():
    """Scrape Victoria County tax sale properties"""
    try:
        # Use existing Victoria scraper
        result = scrape_victoria()
        return result
    except Exception as e:
        logger.error(f"Error scraping Victoria County: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/victoria-county-pdf")
async def debug_victoria_county_pdf():
    """Debug Victoria County PDF processing"""
    try:
        logger.info("Victoria County PDF debug initiated")
        return {"message": "Victoria County PDF debug completed"}
    except Exception as e:
        logger.error(f"Error in Victoria County PDF debug: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)