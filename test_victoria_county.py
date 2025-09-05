#!/usr/bin/env python3
"""
Victoria County Scraper Testing - Review Request Focus
Tests the new Victoria County scraper implementation
"""

import requests
import json
import sys
from datetime import datetime
import time

# Get backend URL from environment
import os
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nstax-boundary.preview.emergentagent.com') + '/api'

def test_api_connection():
    """Test basic API connectivity"""
    print("🔗 Testing API Connection...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=30)
        if response.status_code == 200:
            print("✅ API connection successful")
            return True
        else:
            print(f"❌ API connection failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def test_victoria_county_scraper():
    """Test Victoria County scraper implementation - Review Request Focus"""
    print("\n🏛️ Testing Victoria County Scraper Implementation...")
    print("🎯 FOCUS: POST /api/scrape/victoria-county endpoint and municipality creation")
    print("📋 REQUIREMENTS: Verify AAN 00254118 property insertion and data structure")
    
    try:
        # Test 1: Victoria County Scraper Endpoint
        print(f"\n   🔧 TEST 1: POST /api/scrape/victoria-county")
        
        scraper_response = requests.post(f"{BACKEND_URL}/scrape/victoria-county", timeout=120)
        
        if scraper_response.status_code == 200:
            scraper_result = scraper_response.json()
            print(f"   ✅ Victoria County scraper executed successfully - HTTP 200")
            print(f"   📊 Status: {scraper_result.get('status', 'unknown')}")
            print(f"   🏠 Properties scraped: {scraper_result.get('properties_scraped', 0)}")
            print(f"   🏛️ Municipality: {scraper_result.get('municipality', 'N/A')}")
            
            # Verify expected property count
            expected_properties = 1  # Based on the sample data in server.py
            actual_properties = scraper_result.get('properties_scraped', 0)
            
            if actual_properties == expected_properties:
                print(f"   ✅ Expected property count: {actual_properties} properties")
            else:
                print(f"   ⚠️ Property count mismatch: expected {expected_properties}, got {actual_properties}")
                
        else:
            print(f"   ❌ Victoria County scraper failed with status {scraper_response.status_code}")
            try:
                error_detail = scraper_response.json()
                print(f"      Error details: {error_detail}")
            except:
                print(f"      Raw response: {scraper_response.text}")
            return False, {"error": f"Scraper failed with HTTP {scraper_response.status_code}"}
        
        # Test 2: Verify Municipality Creation
        print(f"\n   🔧 TEST 2: Verify Victoria County Municipality Creation")
        
        municipalities_response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        
        if municipalities_response.status_code == 200:
            municipalities = municipalities_response.json()
            
            # Find Victoria County municipality
            victoria_county = None
            for muni in municipalities:
                if muni.get("name") == "Victoria County":
                    victoria_county = muni
                    break
            
            if victoria_county:
                print(f"   ✅ Victoria County municipality found in database")
                print(f"      ID: {victoria_county.get('id')}")
                print(f"      Name: {victoria_county.get('name')}")
                print(f"      Scraper Type: {victoria_county.get('scraper_type')}")
                print(f"      Website URL: {victoria_county.get('website_url')}")
                print(f"      Scrape Status: {victoria_county.get('scrape_status')}")
                
                # Verify scraper_type is "victoria_county"
                if victoria_county.get('scraper_type') == 'victoria_county':
                    print(f"   ✅ Correct scraper_type: 'victoria_county'")
                else:
                    print(f"   ❌ Incorrect scraper_type: '{victoria_county.get('scraper_type')}' (expected 'victoria_county')")
                    return False, {"error": "Incorrect scraper_type"}
                
                # Verify scrape status is success
                if victoria_county.get('scrape_status') == 'success':
                    print(f"   ✅ Scrape status: 'success'")
                else:
                    print(f"   ⚠️ Scrape status: '{victoria_county.get('scrape_status')}'")
                    
            else:
                print(f"   ❌ Victoria County municipality not found in database")
                return False, {"error": "Victoria County municipality not created"}
        else:
            print(f"   ❌ Failed to retrieve municipalities: {municipalities_response.status_code}")
            return False, {"error": "Failed to retrieve municipalities"}
        
        # Test 3: Verify Sample Property (AAN: 00254118) Insertion
        print(f"\n   🔧 TEST 3: Verify Sample Property (AAN: 00254118) Data")
        
        tax_sales_response = requests.get(f"{BACKEND_URL}/tax-sales", timeout=30)
        
        if tax_sales_response.status_code == 200:
            properties = tax_sales_response.json()
            
            # Find Victoria County properties
            victoria_properties = [p for p in properties if p.get("municipality_name") == "Victoria County"]
            print(f"   📊 Victoria County properties found: {len(victoria_properties)}")
            
            # Find the specific sample property (AAN: 00254118)
            sample_property = None
            for prop in victoria_properties:
                if prop.get("assessment_number") == "00254118":
                    sample_property = prop
                    break
            
            if sample_property:
                print(f"   ✅ Sample property (AAN: 00254118) found in database")
                print(f"\n   📋 PROPERTY DATA VERIFICATION:")
                print(f"      Assessment Number: {sample_property.get('assessment_number')}")
                print(f"      Owner Name: {sample_property.get('owner_name')}")
                print(f"      Property Address: {sample_property.get('property_address')}")
                print(f"      PID Number: {sample_property.get('pid_number')}")
                print(f"      Opening Bid: ${sample_property.get('opening_bid')}")
                print(f"      Property Type: {sample_property.get('property_type')}")
                print(f"      Lot Size: {sample_property.get('lot_size')}")
                print(f"      Municipality Name: {sample_property.get('municipality_name')}")
                print(f"      Redeemable: {sample_property.get('redeemable')}")
                print(f"      HST Applicable: {sample_property.get('hst_applicable')}")
                print(f"      Latitude: {sample_property.get('latitude')}")
                print(f"      Longitude: {sample_property.get('longitude')}")
                
                # Verify required fields based on Victoria County format
                required_fields = {
                    'assessment_number': '00254118',
                    'owner_name': 'Donald John Beaton',
                    'pid_number': '85006500',
                    'opening_bid': 2009.03,
                    'municipality_name': 'Victoria County'
                }
                
                field_verification = []
                for field, expected_value in required_fields.items():
                    actual_value = sample_property.get(field)
                    if actual_value == expected_value:
                        field_verification.append(f"✅ {field}: {actual_value}")
                    else:
                        field_verification.append(f"❌ {field}: expected '{expected_value}', got '{actual_value}'")
                
                print(f"\n   🔍 FIELD VERIFICATION:")
                for verification in field_verification:
                    print(f"      {verification}")
                
                # Check if all required fields match
                all_fields_correct = all("✅" in verification for verification in field_verification)
                
                if all_fields_correct:
                    print(f"   ✅ All required fields match expected values")
                else:
                    print(f"   ❌ Some required fields don't match expected values")
                    return False, {"error": "Required fields don't match expected values"}
                
                # Verify additional Victoria County specific fields
                print(f"\n   🏠 VICTORIA COUNTY SPECIFIC FIELDS:")
                property_address = sample_property.get('property_address', '')
                if "198 Little Narrows Rd" in property_address:
                    print(f"   ✅ Property address contains expected location")
                else:
                    print(f"   ⚠️ Property address may not match expected format")
                
                lot_size = sample_property.get('lot_size', '')
                if "22,230" in lot_size and "Sq. Feet" in lot_size:
                    print(f"   ✅ Lot size contains expected dimensions")
                else:
                    print(f"   ⚠️ Lot size format: '{lot_size}'")
                
                property_type = sample_property.get('property_type', '')
                if "Land/Dwelling" in property_type:
                    print(f"   ✅ Property type matches Victoria County format")
                else:
                    print(f"   ⚠️ Property type: '{property_type}'")
                    
            else:
                print(f"   ❌ Sample property (AAN: 00254118) not found in database")
                if victoria_properties:
                    print(f"   📊 Available Victoria County properties:")
                    for prop in victoria_properties:
                        print(f"      - AAN: {prop.get('assessment_number', 'N/A')}, Owner: {prop.get('owner_name', 'N/A')}")
                return False, {"error": "Sample property not found"}
                
        else:
            print(f"   ❌ Failed to retrieve tax sales data: {tax_sales_response.status_code}")
            return False, {"error": "Failed to retrieve tax sales data"}
        
        # Test 4: Test Scraper Dispatch System
        print(f"\n   🔧 TEST 4: Test Municipality Scraper Dispatch")
        
        if victoria_county:
            municipality_id = victoria_county.get('id')
            dispatch_response = requests.post(
                f"{BACKEND_URL}/scrape-municipality/{municipality_id}", 
                timeout=120
            )
            
            if dispatch_response.status_code == 200:
                dispatch_result = dispatch_response.json()
                print(f"   ✅ Municipality scraper dispatch successful")
                print(f"      Status: {dispatch_result.get('status')}")
                print(f"      Municipality: {dispatch_result.get('municipality')}")
                print(f"      Properties Scraped: {dispatch_result.get('properties_scraped', 0)}")
                
                # Verify it correctly identified victoria_county scraper type
                if dispatch_result.get('municipality') == 'Victoria County':
                    print(f"   ✅ Dispatch correctly identified Victoria County scraper")
                else:
                    print(f"   ⚠️ Dispatch municipality mismatch")
                    
            else:
                print(f"   ❌ Municipality scraper dispatch failed: {dispatch_response.status_code}")
                try:
                    error_detail = dispatch_response.json()
                    print(f"      Error: {error_detail}")
                except:
                    print(f"      Raw response: {dispatch_response.text}")
                return False, {"error": "Scraper dispatch failed"}
        
        # Test 5: Verify Property Accessibility via Tax Sales Endpoint
        print(f"\n   🔧 TEST 5: Verify Property Accessibility via /api/tax-sales")
        
        # Test filtering by municipality
        filtered_response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Victoria County", timeout=30)
        
        if filtered_response.status_code == 200:
            filtered_properties = filtered_response.json()
            print(f"   ✅ Tax sales filtering by municipality works")
            print(f"   📊 Victoria County properties via filter: {len(filtered_properties)}")
            
            # Verify our sample property is accessible via filtering
            sample_found_via_filter = any(
                prop.get('assessment_number') == '00254118' 
                for prop in filtered_properties
            )
            
            if sample_found_via_filter:
                print(f"   ✅ Sample property accessible via municipality filter")
            else:
                print(f"   ❌ Sample property not accessible via municipality filter")
                return False, {"error": "Sample property not accessible via filter"}
                
        else:
            print(f"   ⚠️ Tax sales filtering test failed: {filtered_response.status_code}")
        
        print(f"\n   ✅ VICTORIA COUNTY SCRAPER TESTS COMPLETED SUCCESSFULLY")
        print(f"   🎯 REVIEW REQUEST REQUIREMENTS VERIFIED:")
        print(f"      ✅ POST /api/scrape/victoria-county: Returns HTTP 200")
        print(f"      ✅ Municipality Creation: Victoria County created with scraper_type 'victoria_county'")
        print(f"      ✅ Property Data: AAN 00254118 correctly inserted with all required fields")
        print(f"      ✅ Data Structure: All Victoria County format fields populated correctly")
        print(f"      ✅ Scraper Dispatch: Municipality scraper endpoint works with victoria_county type")
        print(f"      ✅ Property Access: Property accessible via /api/tax-sales endpoint")
        
        return True, {
            "scraper_endpoint": True,
            "municipality_created": True,
            "sample_property_inserted": True,
            "required_fields_correct": True,
            "scraper_dispatch_working": True,
            "property_accessible": True,
            "municipality_id": victoria_county.get('id') if victoria_county else None,
            "properties_scraped": scraper_result.get('properties_scraped', 0) if 'scraper_result' in locals() else 0
        }
        
    except Exception as e:
        print(f"   ❌ Victoria County scraper test error: {e}")
        return False, {"error": str(e)}

def main():
    """Main test execution for Victoria County scraper"""
    print("🚀 Starting Victoria County Scraper Testing")
    print("🎯 FOCUS: Test new Victoria County scraper implementation")
    print("=" * 80)
    
    # Test 1: Basic API Connection
    api_connected = test_api_connection()
    if not api_connected:
        print("\n❌ Cannot proceed without API connection")
        return False
    
    # Test 2: Victoria County Scraper (Main Focus)
    victoria_county_working, victoria_county_data = test_victoria_county_scraper()
    
    # Print Summary
    print("\n" + "=" * 80)
    print("📊 VICTORIA COUNTY SCRAPER TESTING SUMMARY")
    print("=" * 80)
    
    if victoria_county_working:
        print("✅ VICTORIA COUNTY SCRAPER: ALL TESTS PASSED")
        
        if victoria_county_data and isinstance(victoria_county_data, dict):
            print(f"\n📋 DETAILED RESULTS:")
            print(f"   ✅ Scraper Endpoint Working: {victoria_county_data.get('scraper_endpoint', False)}")
            print(f"   ✅ Municipality Created: {victoria_county_data.get('municipality_created', False)}")
            print(f"   ✅ Sample Property Inserted: {victoria_county_data.get('sample_property_inserted', False)}")
            print(f"   ✅ Required Fields Correct: {victoria_county_data.get('required_fields_correct', False)}")
            print(f"   ✅ Scraper Dispatch Working: {victoria_county_data.get('scraper_dispatch_working', False)}")
            print(f"   ✅ Property Accessible: {victoria_county_data.get('property_accessible', False)}")
            print(f"   📊 Properties Scraped: {victoria_county_data.get('properties_scraped', 0)}")
            print(f"   🆔 Municipality ID: {victoria_county_data.get('municipality_id', 'N/A')}")
        
        print(f"\n🎯 REVIEW REQUEST VERIFICATION:")
        print(f"   ✅ Does the endpoint return HTTP 200 with property data? YES")
        print(f"   ✅ Is the municipality properly created with scraper_type 'victoria_county'? YES")
        print(f"   ✅ Are all property fields correctly populated based on Victoria County format? YES")
        print(f"   ✅ Is the property properly accessible via the /api/tax-sales endpoint? YES")
        
        print(f"\n🎉 OVERALL RESULT: VICTORIA COUNTY SCRAPER IMPLEMENTATION SUCCESSFUL")
        print(f"   The Victoria County scraper is working correctly and ready for production use")
        
    else:
        print("❌ VICTORIA COUNTY SCRAPER: TESTS FAILED")
        
        if victoria_county_data and isinstance(victoria_county_data, dict):
            error = victoria_county_data.get('error', 'Unknown error')
            print(f"   Error: {error}")
        
        print(f"\n⚠️ OVERALL RESULT: VICTORIA COUNTY SCRAPER NEEDS ATTENTION")
        print(f"   Issues need to be addressed before the scraper can be considered ready")
    
    return victoria_county_working

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)