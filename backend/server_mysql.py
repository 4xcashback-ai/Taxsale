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
async def check_updates(current_user: dict = Depends(get_current_user_optional)):
    """Check for updates"""
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Just return the deployment status for now
    return await get_deployment_status(current_user)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)