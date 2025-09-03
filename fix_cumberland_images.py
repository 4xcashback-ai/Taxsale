#!/usr/bin/env python3
"""
Fix Cumberland County property image 404 errors by updating boundary_screenshot filenames
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_cumberland_property_images():
    """Fix the boundary screenshot filenames for Cumberland County properties"""
    
    # Load environment variables
    load_dotenv(Path('/app/backend/.env'))
    
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # The problematic properties and their correct PID-assessment filename mapping
    property_fixes = [
        {
            'assessment_number': '07486596',
            'pid_number': '25330655',
            'correct_filename': 'boundary_25330655_07486596.png'
        },
        {
            'assessment_number': '01578626', 
            'pid_number': '25240243',
            'correct_filename': 'boundary_25240243_01578626.png'
        },
        {
            'assessment_number': '10802059',
            'pid_number': '25254327', 
            'correct_filename': 'boundary_25254327_10802059.png'
        }
    ]
    
    # Verify the files actually exist on filesystem
    for prop in property_fixes:
        file_path = f"/app/backend/static/property_screenshots/{prop['correct_filename']}"
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return False
        else:
            logger.info(f"✅ Verified file exists: {prop['correct_filename']}")
    
    # Update the database
    updated_count = 0
    for prop in property_fixes:
        assessment_num = prop['assessment_number']
        correct_filename = prop['correct_filename']
        
        # Find the property
        property_doc = await db.tax_sales.find_one({'assessment_number': assessment_num})
        if not property_doc:
            logger.error(f"Property {assessment_num} not found in database")
            continue
            
        logger.info(f"Updating property {assessment_num}")
        logger.info(f"  Current filename: {property_doc.get('boundary_screenshot', 'None')}")
        logger.info(f"  New filename: {correct_filename}")
        
        # Update the boundary screenshot filename
        result = await db.tax_sales.update_one(
            {'assessment_number': assessment_num},
            {'$set': {'boundary_screenshot': correct_filename}}
        )
        
        if result.modified_count > 0:
            updated_count += 1
            logger.info(f"✅ Successfully updated {assessment_num}")
        else:
            logger.warning(f"❌ Failed to update {assessment_num}")
    
    await client.close()
    
    logger.info(f"\n=== SUMMARY ===")
    logger.info(f"Updated {updated_count}/{len(property_fixes)} properties")
    
    return updated_count == len(property_fixes)

if __name__ == "__main__":
    success = asyncio.run(fix_cumberland_property_images())
    if success:
        print("\n🎉 All Cumberland County property images fixed successfully!")
    else:
        print("\n❌ Some issues occurred during the fix")