#!/usr/bin/env python3

import sys
import os

# Add the backend directory to the Python path
sys.path.append('/app/backend')

from mysql_config import mysql_db

def test_db_connection():
    """Test database connection"""
    try:
        print("Testing database connection...")
        connection = mysql_db.get_connection()
        if connection and connection.is_connected():
            print("✅ Database connection successful")
            connection.close()
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def check_scraper_config():
    """Check Halifax scraper configuration"""
    try:
        print("\nChecking Halifax scraper configuration...")
        config = mysql_db.get_scraper_config('Halifax Regional Municipality')
        if config:
            print("✅ Halifax scraper config found:")
            print(f"  - Base URL: {config.get('base_url')}")
            print(f"  - Tax Sale Page: {config.get('tax_sale_page_url')}")
            print(f"  - PDF Patterns: {config.get('pdf_search_patterns')}")
            print(f"  - Excel Patterns: {config.get('excel_search_patterns')}")
            print(f"  - Enabled: {config.get('enabled')}")
            return config
        else:
            print("❌ Halifax scraper config not found")
            return None
    except Exception as e:
        print(f"❌ Error checking scraper config: {e}")
        return None

def check_property(assessment_number):
    try:
        property_data = mysql_db.get_property_by_assessment(assessment_number)
        
        if property_data:
            print(f"\n✅ Property found:")
            print(f"Assessment Number: {property_data['assessment_number']}")
            print(f"Property Type: {property_data.get('property_type', 'NOT SET')}")
            print(f"Civic Address: {property_data.get('civic_address', 'NOT SET')}")
            print(f"Owner Name: {property_data.get('owner_name', 'NOT SET')}")
            print(f"Municipality: {property_data.get('municipality', 'NOT SET')}")
            print(f"Status: {property_data.get('status', 'NOT SET')}")
            print(f"Latitude: {property_data.get('latitude', 'NOT SET')}")
            print(f"Longitude: {property_data.get('longitude', 'NOT SET')}")
            return property_data
        else:
            print(f"❌ Property {assessment_number} not found in database.")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def update_property_type(assessment_number, new_type):
    try:
        result = mysql_db.update_property(assessment_number, {'property_type': new_type})
        if result:
            print(f"✅ Successfully updated property {assessment_number} to type '{new_type}'")
        else:
            print(f"❌ Failed to update property {assessment_number}")
        return result
    except Exception as e:
        print(f"❌ Error updating property: {e}")
        return False

def run_rescan_test(assessment_number):
    """Test the rescan functionality"""
    try:
        print(f"\n🔍 Testing rescan functionality for property {assessment_number}...")
        
        # Import the rescan function
        from scrapers_mysql import rescan_halifax_property
        
        result = rescan_halifax_property(assessment_number)
        
        print("Rescan result:")
        print(f"  - Success: {result.get('success')}")
        print(f"  - Message: {result.get('message')}")
        print(f"  - Files checked: {result.get('files_checked', {})}")
        print(f"  - Debug info: {result.get('debug_info', 'None')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing rescan: {e}")
        return None

if __name__ == "__main__":
    assessment_number = "01999184"
    
    print("🔍 COMPREHENSIVE DIAGNOSIS FOR PROPERTY 01999184")
    print("=" * 60)
    
    # Test 1: Database connection
    if not test_db_connection():
        print("\n❌ Cannot proceed - database connection failed")
        exit(1)
    
    # Test 2: Check scraper configuration
    config = check_scraper_config()
    if not config:
        print("\n❌ Cannot proceed - scraper configuration missing")
        exit(1)
    
    # Test 3: Check property exists
    print(f"\nChecking property {assessment_number}:")
    print("=" * 50)
    property_data = check_property(assessment_number)
    
    if not property_data:
        print(f"\n❌ Property {assessment_number} not found in database")
        print("\nPossible causes:")
        print("- Property was never scraped")
        print("- Assessment number is incorrect")
        print("- Property was deleted")
        exit(1)
    
    # Test 4: Analyze property type
    current_type = property_data.get('property_type')
    print(f"\n📋 Property Analysis:")
    print(f"Current property_type: '{current_type}'")
    
    if current_type == 'mobile_home_only':
        print("✅ Property is correctly classified as mobile home")
        print("The issue is NOT with property classification")
    else:
        print("⚠️  Property is NOT classified as mobile home")
        print("This could explain why mobile home logic isn't triggered")
    
    # Test 5: Run rescan test
    print(f"\n🧪 Testing rescan functionality...")
    rescan_result = run_rescan_test(assessment_number)
    
    # Summary
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSIS SUMMARY:")
    print("=" * 60)
    
    if rescan_result:
        if rescan_result.get('success'):
            print("✅ Rescan functionality working correctly")
        else:
            files_checked = rescan_result.get('files_checked', {})
            pdf_count = len(files_checked.get('pdfs', []))
            excel_count = len(files_checked.get('excel', []))
            
            print("❌ Rescan failed - Root causes identified:")
            print(f"   - PDFs found: {pdf_count}")
            print(f"   - Excel files found: {excel_count}")
            
            if pdf_count == 0 and excel_count == 0:
                print("   - 🚨 NO FILES FOUND - This is the main issue!")
                print("   - Halifax tax sale page may have changed")
                print("   - Search patterns may need updating")
                print("   - Website may be temporarily unavailable")
            else:
                print("   - Files found but property not in files")
                print("   - Property may have been removed from tax sale")
    
    print("\n✅ Diagnosis complete. Review the results above.")
    
    # Optional fix
    if current_type != 'mobile_home_only':
        response = input(f"\nWould you like to update property {assessment_number} to 'mobile_home_only'? (y/n): ")
        if response.lower() == 'y':
            if update_property_type(assessment_number, 'mobile_home_only'):
                print("\n✅ Property type updated successfully!")
                print("You can now test the mobile home rescan logic.")
            else:
                print("\n❌ Failed to update property type")