#!/usr/bin/env python3
"""
Fix Boundary Image References Script
Fixes boundary file references in database to match actual files on disk
"""

import os
import sys
import pymongo
import glob
from dotenv import load_dotenv

load_dotenv()

def fix_boundary_references():
    """Fix boundary file references to match actual files on disk"""
    
    print("🔧 Fixing Boundary Image References")
    print("=" * 50)
    
    try:
        # Connect to database
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        
        client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=10000)
        db = client[db_name]
        
        print(f"✅ Connected to database: {db_name}")
        
        # Get all properties with boundary references
        properties_with_boundaries = list(db.tax_sales.find(
            {"boundary_screenshot": {"$exists": True, "$ne": None}}
        ))
        
        print(f"📋 Found {len(properties_with_boundaries)} properties with boundary references")
        
        # Get actual boundary files on disk
        boundary_dir = "static/property_screenshots"
        if not os.path.exists(boundary_dir):
            boundary_dir = "/app/backend/static/property_screenshots"
        if not os.path.exists(boundary_dir):
            print(f"❌ Boundary directory not found: {boundary_dir}")
            return False
        
        boundary_files = glob.glob(os.path.join(boundary_dir, "boundary_*.png"))
        boundary_filenames = [os.path.basename(f) for f in boundary_files]
        
        print(f"📁 Found {len(boundary_filenames)} boundary files on disk")
        
        # Create mapping of assessment numbers to actual filenames
        assessment_to_file = {}
        for filename in boundary_filenames:
            # Extract assessment numbers from filename
            # Files can be: boundary_XXXXX_YYYYY.png or boundary_XXXXX.png
            parts = filename.replace('boundary_', '').replace('.png', '').split('_')
            
            # Add all parts as potential assessment numbers
            for part in parts:
                if part.isdigit() and len(part) >= 5:  # Assessment numbers are typically 5+ digits
                    if part not in assessment_to_file:
                        assessment_to_file[part] = filename
        
        print(f"🔍 Created mapping for {len(assessment_to_file)} assessment numbers")
        
        # Fix database references
        fixed_count = 0
        missing_count = 0
        
        for prop in properties_with_boundaries:
            assessment_number = prop.get('assessment_number')
            current_boundary = prop.get('boundary_screenshot')
            
            if not assessment_number:
                continue
            
            # Check if current reference file exists
            current_path = os.path.join(boundary_dir, current_boundary)
            
            if os.path.exists(current_path):
                print(f"✅ {assessment_number}: File exists - {current_boundary}")
                continue
            
            # Try to find correct filename
            if assessment_number in assessment_to_file:
                correct_filename = assessment_to_file[assessment_number]
                
                if correct_filename != current_boundary:
                    # Update database
                    result = db.tax_sales.update_one(
                        {"assessment_number": assessment_number},
                        {"$set": {"boundary_screenshot": correct_filename}}
                    )
                    
                    if result.modified_count > 0:
                        print(f"🔧 {assessment_number}: {current_boundary} → {correct_filename}")
                        fixed_count += 1
                    else:
                        print(f"⚠️ {assessment_number}: Update failed")
                else:
                    print(f"✅ {assessment_number}: Already correct - {current_boundary}")
            else:
                # File not found - remove boundary reference to use Google Maps fallback
                result = db.tax_sales.update_one(
                    {"assessment_number": assessment_number},
                    {"$unset": {"boundary_screenshot": ""}}
                )
                
                if result.modified_count > 0:
                    print(f"🗑️ {assessment_number}: Removed missing reference - {current_boundary}")
                    missing_count += 1
        
        print("\n" + "=" * 50)
        print("📊 BOUNDARY FIX SUMMARY")
        print("=" * 50)
        print(f"   🔧 Fixed references: {fixed_count}")
        print(f"   🗑️ Removed missing: {missing_count}")
        print(f"   ✅ Total processed: {len(properties_with_boundaries)}")
        
        if fixed_count > 0 or missing_count > 0:
            print(f"\n✅ Database updated successfully!")
            print("   Restart your backend service to see changes.")
        else:
            print(f"\n✅ All boundary references are already correct!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing boundary references: {e}")
        return False

if __name__ == "__main__":
    success = fix_boundary_references()
    sys.exit(0 if success else 1)