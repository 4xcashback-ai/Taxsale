#!/usr/bin/env python3
"""
Fix Cumberland County property coordinates by extracting them from government boundary data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import logging
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_cumberland_coordinates():
    """Update coordinates for Cumberland County properties using government boundary data"""
    
    # Load environment variables
    load_dotenv(Path('/app/backend/.env'))
    
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # The problematic properties with their PIDs
    properties = [
        {'assessment_number': '07486596', 'pid_number': '25330655'},
        {'assessment_number': '01578626', 'pid_number': '25240243'},
        {'assessment_number': '10802059', 'pid_number': '25254327'}
    ]
    
    # Get admin token for API calls
    admin_login_url = "http://localhost:8001/api/auth/login"
    login_response = requests.post(admin_login_url, json={
        "username": "admin",
        "password": "TaxSale2025!SecureAdmin"
    })
    
    if login_response.status_code != 200:
        logger.error(f"Failed to login: {login_response.status_code}")
        return False
        
    token = login_response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    updated_count = 0
    
    for prop in properties:
        assessment_num = prop['assessment_number']
        pid_number = prop['pid_number']
        
        logger.info(f"Processing property {assessment_num} (PID: {pid_number})")
        
        # Get government boundary data
        gov_api_url = f"http://localhost:8001/api/query-ns-government-parcel/{pid_number}"
        gov_response = requests.get(gov_api_url, headers=headers)
        
        if gov_response.status_code != 200:
            logger.error(f"Failed to get boundary data for {assessment_num}: {gov_response.status_code}")
            continue
            
        boundary_data = gov_response.json()
        
        if not boundary_data.get('found') or not boundary_data.get('center'):
            logger.error(f"No center coordinates found for {assessment_num}")
            continue
            
        center = boundary_data['center']
        latitude = center['lat']
        longitude = center['lon']
        
        logger.info(f"Found coordinates for {assessment_num}: {latitude}, {longitude}")
        
        # Update the property in the database
        result = await db.tax_sales.update_one(
            {'assessment_number': assessment_num},
            {'$set': {
                'latitude': latitude,
                'longitude': longitude
            }}
        )
        
        if result.modified_count > 0:
            updated_count += 1
            logger.info(f"✅ Successfully updated coordinates for {assessment_num}")
        else:
            logger.warning(f"❌ Failed to update {assessment_num}")
    
    await client.close()
    
    logger.info(f"\n=== SUMMARY ===")
    logger.info(f"Updated coordinates for {updated_count}/{len(properties)} properties")
    
    return updated_count == len(properties)

if __name__ == "__main__":
    success = asyncio.run(fix_cumberland_coordinates())
    if success:
        print("\n🎉 All Cumberland County property coordinates fixed successfully!")
    else:
        print("\n❌ Some issues occurred during the coordinate fix")