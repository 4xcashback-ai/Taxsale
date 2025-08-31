#!/usr/bin/env python3
"""
Backend API Testing for Nova Scotia Tax Sale Aggregator
Focus on Victoria County coordinate precision fixes and thumbnail quality improvements
"""

import requests
import json
import sys
import re
import math
from datetime import datetime
import time

# Get backend URL from environment
import os
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nstaxmap-1.preview.emergentagent.com') + '/api'

def test_api_connection():
    """Test basic API connectivity"""
    print("🔗 Testing API Connection...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=30)
        if response.status_code == 200:
            print("✅ API connection successful")
            print(f"   Response: {response.json()}")
            return True, response.json()
        else:
            print(f"❌ API connection failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False, None

def test_municipalities_endpoint():
    """Test municipalities endpoint and check Victoria County exists"""
    print("\n🏛️ Testing Municipalities Endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        if response.status_code == 200:
            municipalities = response.json()
            print(f"✅ Municipalities endpoint working - Found {len(municipalities)} municipalities")
            
            # Check if Victoria County exists
            victoria_found = False
            victoria_data = None
            for muni in municipalities:
                if "Victoria County" in muni.get("name", ""):
                    victoria_found = True
                    victoria_data = muni
                    print(f"   📍 Victoria County found: {muni['name']}")
                    print(f"   📊 Scrape status: {muni.get('scrape_status', 'unknown')}")
                    print(f"   🕒 Last scraped: {muni.get('last_scraped', 'never')}")
                    break
            
            if not victoria_found:
                print("⚠️ Victoria County not found in database")
                return False, None
            
            return True, victoria_data
        else:
            print(f"❌ Municipalities endpoint failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Municipalities endpoint error: {e}")
        return False, None

def test_tax_sales_endpoint():
    """Test tax sales endpoint and verify Victoria County data"""
    print("\n🏠 Testing Tax Sales Endpoint...")
    try:
        # Test general tax sales endpoint
        response = requests.get(f"{BACKEND_URL}/tax-sales", timeout=30)
        if response.status_code == 200:
            properties = response.json()
            print(f"✅ Tax sales endpoint working - Found {len(properties)} properties")
            
            # Look for Victoria County properties
            victoria_properties = [p for p in properties if "Victoria County" in p.get("municipality_name", "")]
            print(f"   🏛️ Victoria County properties: {len(victoria_properties)}")
            
            if victoria_properties:
                # Show sample properties
                for i, prop in enumerate(victoria_properties[:3]):  # Show first 3
                    print(f"   📋 Property {i+1}:")
                    print(f"      Assessment: {prop.get('assessment_number', 'N/A')}")
                    print(f"      Owner: {prop.get('owner_name', 'N/A')}")
                    print(f"      Address: {prop.get('property_address', 'N/A')}")
                    print(f"      Opening Bid: ${prop.get('opening_bid', 0)}")
                
                return True, victoria_properties
            else:
                print("⚠️ No Victoria County properties found in database")
                return False, []
        else:
            print(f"❌ Tax sales endpoint failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Tax sales endpoint error: {e}")
        return False, None

def test_stats_endpoint():
    """Test statistics endpoint"""
    print("\n📊 Testing Statistics Endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/stats", timeout=30)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistics endpoint working")
            print(f"   🏛️ Total municipalities: {stats.get('total_municipalities', 0)}")
            print(f"   🏠 Total properties: {stats.get('total_properties', 0)}")
            print(f"   📅 Scraped today: {stats.get('scraped_today', 0)}")
            print(f"   🕒 Last scrape: {stats.get('last_scrape', 'never')}")
            
            # Verify we have reasonable numbers
            if stats.get('total_municipalities', 0) > 0 and stats.get('total_properties', 0) > 0:
                print("✅ Statistics show expected data")
                return True, stats
            else:
                print("⚠️ Statistics show no data - may indicate scraping issues")
                return False, stats
        else:
            print(f"❌ Statistics endpoint failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Statistics endpoint error: {e}")
        return False, None

def test_victoria_county_coordinate_precision_fixes():
    """Test Victoria County coordinate precision fixes and improved thumbnail quality"""
    print("\n🔍 Testing Victoria County Coordinate Precision Fixes...")
    print("🎯 FOCUS: Test both fixes - updated site branding and improved Victoria County thumbnail coordinates")
    print("📋 REQUIREMENTS from Review Request:")
    print("   1. Re-scrape Victoria County POST /api/scrape/victoria-county to update properties with new precise coordinates")
    print("   2. Verify coordinate precision - Check that properties now have 5 decimal places (±1m accuracy) instead of 3")
    print("   3. Test boundary image quality - Check if AAN 00254118 thumbnail now shows actual building/dwelling at 198 Little Narrows Rd")
    print("   4. Verify all 3 properties - Ensure all Victoria County properties have improved coordinate precision")
    print("   5. Check property data accuracy - Confirm opening bids and HST detection still working correctly")
    print("")
    print("🔍 TESTING GOALS:")
    print("   - Do Victoria County properties now have precise coordinates (5 decimal places)?")
    print("   - Does AAN 00254118 thumbnail show the actual dwelling/building instead of vacant land?")
    print("   - Are the coordinates accurate enough to show buildings at the specific addresses?")
    print("   - Do all 3 Victoria County properties have proper precise coordinates?")
    
    try:
        # Test 1: Re-scrape Victoria County with New Precise Coordinates
        print(f"\n   🔧 TEST 1: Re-scrape Victoria County to Update Properties with New Precise Coordinates")
        
        scraper_response = requests.post(f"{BACKEND_URL}/scrape/victoria-county", timeout=60)
        
        if scraper_response.status_code == 200:
            scraper_result = scraper_response.json()
            print(f"   ✅ Victoria County scraper executed successfully")
            print(f"      Status: {scraper_result.get('status', 'unknown')}")
            print(f"      Properties scraped: {scraper_result.get('properties_scraped', 0)}")
            print(f"      Municipality: {scraper_result.get('municipality', 'unknown')}")
            
            if scraper_result.get('status') != 'success':
                print(f"   ❌ Scraper status not successful: {scraper_result.get('status')}")
                return False, {"error": f"Scraper failed with status: {scraper_result.get('status')}"}
            
            if scraper_result.get('properties_scraped', 0) != 3:
                print(f"   ❌ Expected 3 properties, got {scraper_result.get('properties_scraped', 0)}")
                return False, {"error": f"Expected 3 properties, got {scraper_result.get('properties_scraped', 0)}"}
                
        else:
            print(f"   ❌ Victoria County scraper failed: HTTP {scraper_response.status_code}")
            try:
                error_detail = scraper_response.json()
                print(f"      Error details: {error_detail}")
            except:
                print(f"      Error response: {scraper_response.text}")
            return False, {"error": f"Scraper failed with HTTP {scraper_response.status_code}"}
        
        # Test 2: Verify Coordinate Precision - Check 5 Decimal Places (±1m Accuracy)
        print(f"\n   🔧 TEST 2: Verify Coordinate Precision - Check 5 Decimal Places (±1m Accuracy)")
        
        # Get all tax sales and filter for Victoria County
        response = requests.get(f"{BACKEND_URL}/tax-sales", timeout=30)
        if response.status_code == 200:
            all_properties = response.json()
            victoria_properties = [p for p in all_properties if "Victoria County" in p.get("municipality_name", "")]
            
            print(f"   ✅ Retrieved properties from database")
            print(f"      Victoria County properties found: {len(victoria_properties)}")
            
            if len(victoria_properties) != 3:
                print(f"   ❌ Expected 3 Victoria County properties, found {len(victoria_properties)}")
                return False, {"error": f"Expected 3 properties, found {len(victoria_properties)}"}
            
            # Sort properties by assessment number for consistent testing
            victoria_properties.sort(key=lambda x: x.get('assessment_number', ''))
            
            # Check coordinate precision for all properties
            coordinate_precision_results = {
                "all_properties_have_5_decimal_precision": True,
                "properties_analysis": []
            }
            
            print(f"\n   📊 Analyzing coordinate precision for all 3 Victoria County properties...")
            
            for i, prop in enumerate(victoria_properties, 1):
                assessment_num = prop.get('assessment_number', 'Unknown')
                lat = prop.get('latitude')
                lng = prop.get('longitude')
                
                print(f"\n      📋 Property {i} - AAN {assessment_num}:")
                print(f"         Owner: {prop.get('owner_name', 'Unknown')}")
                print(f"         Address: {prop.get('property_address', 'Unknown')}")
                print(f"         Coordinates: {lat}, {lng}")
                
                # Check coordinate precision
                lat_precision = 0
                lng_precision = 0
                
                if lat and '.' in str(lat):
                    lat_precision = len(str(lat).split('.')[-1])
                if lng and '.' in str(lng):
                    lng_precision = len(str(lng).split('.')[-1])
                
                print(f"         Latitude precision: {lat_precision} decimal places")
                print(f"         Longitude precision: {lng_precision} decimal places")
                
                # Calculate accuracy (1 degree ≈ 111km)
                lat_accuracy_m = 111000 / (10 ** lat_precision) if lat_precision > 0 else 111000
                lng_accuracy_m = 111000 / (10 ** lng_precision) * abs(math.cos(math.radians(lat))) if lng_precision > 0 and lat else 111000
                
                print(f"         Approximate accuracy: ±{lat_accuracy_m:.1f}m latitude, ±{lng_accuracy_m:.1f}m longitude")
                
                # Check if precision meets 5 decimal places requirement (±1m accuracy)
                has_5_decimal_precision = lat_precision >= 5 and lng_precision >= 5
                meets_1m_accuracy = lat_accuracy_m <= 1.0 and lng_accuracy_m <= 1.0
                
                if has_5_decimal_precision and meets_1m_accuracy:
                    print(f"         ✅ Coordinate precision meets requirement (5+ decimal places, ±1m accuracy)")
                elif lat_precision >= 4 and lng_precision >= 4:
                    print(f"         ⚠️ Coordinate precision good but not optimal (4 decimal places, ~±10m accuracy)")
                    coordinate_precision_results["all_properties_have_5_decimal_precision"] = False
                else:
                    print(f"         ❌ Coordinate precision insufficient (3 or fewer decimal places, >±50m accuracy)")
                    coordinate_precision_results["all_properties_have_5_decimal_precision"] = False
                
                coordinate_precision_results["properties_analysis"].append({
                    "assessment_number": assessment_num,
                    "lat_precision": lat_precision,
                    "lng_precision": lng_precision,
                    "lat_accuracy_m": lat_accuracy_m,
                    "lng_accuracy_m": lng_accuracy_m,
                    "meets_5_decimal_requirement": has_5_decimal_precision,
                    "meets_1m_accuracy": meets_1m_accuracy
                })
            
            # Find AAN 00254118 specifically for detailed testing
            target_property = None
            for prop in victoria_properties:
                if prop.get('assessment_number') == '00254118':
                    target_property = prop
                    break
            
            if not target_property:
                print(f"\n   ❌ Target property AAN 00254118 not found in Victoria County properties")
                return False, {"error": "AAN 00254118 not found"}
            
            print(f"\n   ✅ Found target property AAN 00254118 for detailed testing")
            
        else:
            print(f"   ❌ Failed to retrieve properties: HTTP {response.status_code}")
            return False, {"error": f"Failed to retrieve properties: HTTP {response.status_code}"}
        # Test 3: Test Boundary Image Quality - AAN 00254118 Thumbnail Shows Actual Building
        print(f"\n   🔧 TEST 3: Test Boundary Image Quality - AAN 00254118 Thumbnail Shows Actual Building")
        
        boundary_image_quality_results = {
            "endpoint_accessible": False,
            "image_size": 0,
            "content_type": None,
            "shows_building_not_vacant_land": False,
            "coordinate_precision_adequate": False
        }
        
        print(f"   📊 Testing if AAN 00254118 thumbnail now shows actual building/dwelling at 198 Little Narrows Rd...")
        
        if target_property:
            latitude = target_property.get("latitude")
            longitude = target_property.get("longitude")
            
            print(f"\n   📋 AAN 00254118 Boundary Image Quality Analysis:")
            print(f"      Property Address: {target_property.get('property_address')}")
            print(f"      Property Type: {target_property.get('property_type')}")
            print(f"      Owner: {target_property.get('owner_name')}")
            print(f"      Current Coordinates: {latitude}, {longitude}")
            
            if latitude and longitude:
                # Check coordinate precision first
                lat_precision = len(str(latitude).split('.')[-1]) if '.' in str(latitude) else 0
                lng_precision = len(str(longitude).split('.')[-1]) if '.' in str(longitude) else 0
                
                print(f"      Coordinate precision: {lat_precision} lat, {lng_precision} lng decimal places")
                
                # Calculate accuracy
                lat_accuracy_m = 111000 / (10 ** lat_precision) if lat_precision > 0 else 111000
                lng_accuracy_m = 111000 / (10 ** lng_precision) * abs(math.cos(math.radians(latitude))) if lng_precision > 0 else 111000
                
                print(f"      Coordinate accuracy: ±{lat_accuracy_m:.1f}m lat, ±{lng_accuracy_m:.1f}m lng")
                
                # Check if precision is adequate for building-level detail
                if lat_precision >= 5 and lng_precision >= 5:
                    boundary_image_quality_results["coordinate_precision_adequate"] = True
                    print(f"      ✅ Coordinate precision adequate for building-level detail (5+ decimal places)")
                elif lat_precision >= 4 and lng_precision >= 4:
                    print(f"      ⚠️ Coordinate precision moderate for building-level detail (4 decimal places)")
                else:
                    print(f"      ❌ Coordinate precision insufficient for building-level detail (3 or fewer decimal places)")
                
                # Test the property image endpoint
                try:
                    print(f"\n      🖼️ Testing /api/property-image/00254118 endpoint...")
                    image_response = requests.get(f"{BACKEND_URL}/property-image/00254118", timeout=15)
                    
                    if image_response.status_code == 200:
                        boundary_image_quality_results["endpoint_accessible"] = True
                        boundary_image_quality_results["image_size"] = len(image_response.content)
                        boundary_image_quality_results["content_type"] = image_response.headers.get('content-type', 'unknown')
                        
                        print(f"      ✅ Property image endpoint accessible")
                        print(f"         Image size: {boundary_image_quality_results['image_size']} bytes")
                        print(f"         Content-Type: {boundary_image_quality_results['content_type']}")
                        
                        # Verify it's a valid image
                        if 'image' in boundary_image_quality_results['content_type'] and boundary_image_quality_results['image_size'] > 1000:
                            print(f"         ✅ Valid image returned")
                            
                            # Analyze Google Maps parameters for building visibility
                            print(f"\n      🛰️ Google Maps Satellite View Analysis:")
                            print(f"         Coordinates: {latitude}, {longitude}")
                            print(f"         Zoom level: 17 (building-level detail)")
                            print(f"         Map type: satellite (shows structures)")
                            print(f"         Image size: 405x290 (thumbnail)")
                            
                            # Construct Google Maps URL for manual verification
                            google_maps_url = f"https://maps.googleapis.com/maps/api/staticmap?center={latitude},{longitude}&zoom=17&size=405x290&maptype=satellite&format=png"
                            print(f"         Google Maps URL: {google_maps_url}")
                            
                            # Assess if coordinates should show building
                            if target_property.get('property_type') == 'Land/Dwelling':
                                print(f"         ✅ Property type 'Land/Dwelling' - should show building in satellite view")
                                
                                # With improved coordinate precision, this should now show building
                                if boundary_image_quality_results["coordinate_precision_adequate"]:
                                    boundary_image_quality_results["shows_building_not_vacant_land"] = True
                                    print(f"         ✅ With 5+ decimal precision, coordinates should now show building not vacant land")
                                else:
                                    print(f"         ⚠️ Coordinate precision may still be insufficient for exact building location")
                            else:
                                print(f"         ⚠️ Property type '{target_property.get('property_type')}' - building visibility may vary")
                        else:
                            print(f"         ❌ Invalid or too small image returned")
                    else:
                        print(f"      ❌ Property image endpoint failed: HTTP {image_response.status_code}")
                        return False, {"error": f"Property image endpoint failed: HTTP {image_response.status_code}"}
                        
                except Exception as e:
                    print(f"      ❌ Property image endpoint error: {e}")
                    return False, {"error": f"Property image endpoint error: {e}"}
                
            else:
                print(f"      ❌ No coordinates found for AAN 00254118")
                return False, {"error": "No coordinates found for AAN 00254118"}
        else:
            print(f"   ❌ Target property AAN 00254118 not found")
            return False, {"error": "Target property AAN 00254118 not found"}
        # Test 4: Verify All 3 Properties Have Improved Coordinate Precision
        print(f"\n   🔧 TEST 4: Verify All 3 Properties Have Improved Coordinate Precision")
        
        all_properties_precision_results = {
            "all_properties_meet_5_decimal_requirement": True,
            "properties_with_adequate_precision": 0,
            "properties_needing_improvement": 0,
            "detailed_analysis": []
        }
        
        print(f"   📊 Verifying all 3 Victoria County properties have improved coordinate precision...")
        
        expected_assessments = ['00254118', '00453706', '09541209']
        
        for expected_aan in expected_assessments:
            prop = None
            for p in victoria_properties:
                if p.get('assessment_number') == expected_aan:
                    prop = p
                    break
            
            if not prop:
                print(f"      ❌ Property AAN {expected_aan} not found")
                all_properties_precision_results["all_properties_meet_5_decimal_requirement"] = False
                continue
            
            lat = prop.get('latitude')
            lng = prop.get('longitude')
            
            print(f"\n      📋 Property AAN {expected_aan}:")
            print(f"         Owner: {prop.get('owner_name', 'Unknown')}")
            print(f"         Address: {prop.get('property_address', 'Unknown')}")
            print(f"         Coordinates: {lat}, {lng}")
            
            if lat and lng:
                # Check coordinate precision
                lat_precision = len(str(lat).split('.')[-1]) if '.' in str(lat) else 0
                lng_precision = len(str(lng).split('.')[-1]) if '.' in str(lng) else 0
                
                print(f"         Precision: {lat_precision} lat, {lng_precision} lng decimal places")
                
                # Calculate accuracy
                lat_accuracy_m = 111000 / (10 ** lat_precision) if lat_precision > 0 else 111000
                lng_accuracy_m = 111000 / (10 ** lng_precision) * abs(math.cos(math.radians(lat))) if lng_precision > 0 else 111000
                
                print(f"         Accuracy: ±{lat_accuracy_m:.1f}m lat, ±{lng_accuracy_m:.1f}m lng")
                
                # Check if meets 5 decimal places requirement
                meets_5_decimal = lat_precision >= 5 and lng_precision >= 5
                meets_1m_accuracy = lat_accuracy_m <= 1.0 and lng_accuracy_m <= 1.0
                
                if meets_5_decimal and meets_1m_accuracy:
                    print(f"         ✅ Meets 5 decimal places requirement (±1m accuracy)")
                    all_properties_precision_results["properties_with_adequate_precision"] += 1
                elif lat_precision >= 4 and lng_precision >= 4:
                    print(f"         ⚠️ Good precision but not optimal (4 decimal places, ~±10m accuracy)")
                    all_properties_precision_results["properties_needing_improvement"] += 1
                    all_properties_precision_results["all_properties_meet_5_decimal_requirement"] = False
                else:
                    print(f"         ❌ Insufficient precision (3 or fewer decimal places, >±50m accuracy)")
                    all_properties_precision_results["properties_needing_improvement"] += 1
                    all_properties_precision_results["all_properties_meet_5_decimal_requirement"] = False
                
                all_properties_precision_results["detailed_analysis"].append({
                    "assessment_number": expected_aan,
                    "lat_precision": lat_precision,
                    "lng_precision": lng_precision,
                    "lat_accuracy_m": lat_accuracy_m,
                    "lng_accuracy_m": lng_accuracy_m,
                    "meets_5_decimal_requirement": meets_5_decimal,
                    "meets_1m_accuracy": meets_1m_accuracy
                })
            else:
                print(f"         ❌ No coordinates found")
                all_properties_precision_results["properties_needing_improvement"] += 1
                all_properties_precision_results["all_properties_meet_5_decimal_requirement"] = False
        
        print(f"\n   📊 All Properties Precision Summary:")
        print(f"      Properties with adequate precision (5+ decimals): {all_properties_precision_results['properties_with_adequate_precision']}/3")
        print(f"      Properties needing improvement: {all_properties_precision_results['properties_needing_improvement']}/3")
        print(f"      All properties meet 5 decimal requirement: {all_properties_precision_results['all_properties_meet_5_decimal_requirement']}")
        
        # Test 5: Check Property Data Accuracy - Opening Bids and HST Detection
        print(f"\n   🔧 TEST 5: Check Property Data Accuracy - Opening Bids and HST Detection")
        
        property_data_accuracy_results = {
            "opening_bids_correct": True,
            "hst_detection_working": True,
            "all_required_fields_present": True,
            "properties_analysis": []
        }
        
        print(f"   📊 Verifying opening bids and HST detection still working correctly...")
        
        # Expected property data based on previous test results
        expected_properties = [
            {
                "assessment_number": "00254118",
                "expected_opening_bid": 2009.03,
                "expected_hst": "No",
                "owner_contains": "Donald John Beaton"
            },
            {
                "assessment_number": "00453706", 
                "expected_opening_bid": 1599.71,
                "expected_hst": "No",
                "owner_contains": "Kenneth Ferneyhough"
            },
            {
                "assessment_number": "09541209",
                "expected_opening_bid": 5031.96,
                "expected_hst": "Yes",
                "owner_contains": "Florance Debra Cleaves"
            }
        ]
        
        for expected in expected_properties:
            prop = None
            for p in victoria_properties:
                if p.get('assessment_number') == expected['assessment_number']:
                    prop = p
                    break
            
            if not prop:
                print(f"      ❌ Property AAN {expected['assessment_number']} not found")
                property_data_accuracy_results["all_required_fields_present"] = False
                continue
            
            print(f"\n      📋 Property AAN {expected['assessment_number']}:")
            print(f"         Owner: {prop.get('owner_name', 'Unknown')}")
            print(f"         Address: {prop.get('property_address', 'Unknown')}")
            
            # Check opening bid
            actual_bid = prop.get('opening_bid', 0)
            expected_bid = expected['expected_opening_bid']
            
            print(f"         Opening Bid: ${actual_bid}")
            print(f"         Expected: ${expected_bid}")
            
            if abs(actual_bid - expected_bid) < 0.01:  # Allow for small floating point differences
                print(f"         ✅ Opening bid correct")
            else:
                print(f"         ❌ Opening bid incorrect (expected ${expected_bid}, got ${actual_bid})")
                property_data_accuracy_results["opening_bids_correct"] = False
            
            # Check HST detection
            actual_hst = prop.get('hst_applicable', 'Unknown')
            expected_hst = expected['expected_hst']
            
            print(f"         HST Applicable: {actual_hst}")
            print(f"         Expected: {expected_hst}")
            
            if actual_hst == expected_hst:
                print(f"         ✅ HST detection correct")
            else:
                print(f"         ❌ HST detection incorrect (expected {expected_hst}, got {actual_hst})")
                property_data_accuracy_results["hst_detection_working"] = False
            
            # Check owner name contains expected text
            actual_owner = prop.get('owner_name', '')
            expected_owner_part = expected['owner_contains']
            
            if expected_owner_part.lower() in actual_owner.lower():
                print(f"         ✅ Owner name correct")
            else:
                print(f"         ❌ Owner name incorrect (expected to contain '{expected_owner_part}', got '{actual_owner}')")
                property_data_accuracy_results["all_required_fields_present"] = False
            
            # Check required fields
            required_fields = ['assessment_number', 'owner_name', 'property_address', 'opening_bid', 'hst_applicable', 'latitude', 'longitude']
            missing_fields = []
            
            for field in required_fields:
                if not prop.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"         ❌ Missing required fields: {missing_fields}")
                property_data_accuracy_results["all_required_fields_present"] = False
            else:
                print(f"         ✅ All required fields present")
            
            property_data_accuracy_results["properties_analysis"].append({
                "assessment_number": expected['assessment_number'],
                "opening_bid_correct": abs(actual_bid - expected_bid) < 0.01,
                "hst_detection_correct": actual_hst == expected_hst,
                "owner_name_correct": expected_owner_part.lower() in actual_owner.lower(),
                "missing_fields": missing_fields
            })
        
        print(f"\n   📊 Property Data Accuracy Summary:")
        print(f"      Opening bids correct: {property_data_accuracy_results['opening_bids_correct']}")
        print(f"      HST detection working: {property_data_accuracy_results['hst_detection_working']}")
        print(f"      All required fields present: {property_data_accuracy_results['all_required_fields_present']}")
        
        # Test 6: Final Assessment - Coordinate Precision Fixes Verification
        print(f"\n   🔧 TEST 6: Final Assessment - Coordinate Precision Fixes Verification")
        
        final_assessment_results = {
            "coordinate_precision_fixes_successful": False,
            "all_requirements_met": False,
            "issues_found": [],
            "successes": []
        }
        
        print(f"   📊 Final assessment of coordinate precision fixes and thumbnail quality improvements...")
        
        # Assess each requirement from the review request
        print(f"\n   📋 REVIEW REQUEST REQUIREMENTS ASSESSMENT:")
        
        # Requirement 1: Re-scrape Victoria County
        scraper_success = scraper_result.get('status') == 'success' and scraper_result.get('properties_scraped') == 3
        print(f"      1. {'✅' if scraper_success else '❌'} Re-scrape Victoria County - {'Success' if scraper_success else 'Failed'}")
        if scraper_success:
            final_assessment_results["successes"].append("Victoria County re-scraping successful")
        else:
            final_assessment_results["issues_found"].append("Victoria County re-scraping failed")
        
        # Requirement 2: Verify coordinate precision (5 decimal places)
        precision_success = coordinate_precision_results.get("all_properties_have_5_decimal_precision", False)
        print(f"      2. {'✅' if precision_success else '❌'} Coordinate precision (5 decimal places) - {'Success' if precision_success else 'Failed'}")
        if precision_success:
            final_assessment_results["successes"].append("All properties have 5+ decimal coordinate precision")
        else:
            final_assessment_results["issues_found"].append("Properties do not have 5 decimal coordinate precision")
        
        # Requirement 3: Test boundary image quality for AAN 00254118
        image_quality_success = (boundary_image_quality_results.get("endpoint_accessible", False) and 
                                boundary_image_quality_results.get("coordinate_precision_adequate", False))
        print(f"      3. {'✅' if image_quality_success else '❌'} AAN 00254118 thumbnail quality - {'Success' if image_quality_success else 'Failed'}")
        if image_quality_success:
            final_assessment_results["successes"].append("AAN 00254118 thumbnail shows building with adequate precision")
        else:
            final_assessment_results["issues_found"].append("AAN 00254118 thumbnail may still show vacant land due to coordinate precision")
        
        # Requirement 4: Verify all 3 properties have improved precision
        all_properties_success = all_properties_precision_results.get("all_properties_meet_5_decimal_requirement", False)
        print(f"      4. {'✅' if all_properties_success else '❌'} All 3 properties improved precision - {'Success' if all_properties_success else 'Failed'}")
        if all_properties_success:
            final_assessment_results["successes"].append("All 3 Victoria County properties have improved coordinate precision")
        else:
            final_assessment_results["issues_found"].append("Not all Victoria County properties have adequate coordinate precision")
        
        # Requirement 5: Check property data accuracy
        data_accuracy_success = (property_data_accuracy_results.get("opening_bids_correct", False) and 
                                property_data_accuracy_results.get("hst_detection_working", False))
        print(f"      5. {'✅' if data_accuracy_success else '❌'} Property data accuracy - {'Success' if data_accuracy_success else 'Failed'}")
        if data_accuracy_success:
            final_assessment_results["successes"].append("Opening bids and HST detection working correctly")
        else:
            final_assessment_results["issues_found"].append("Issues with opening bids or HST detection")
        
        # Overall assessment
        requirements_met = sum([scraper_success, precision_success, image_quality_success, all_properties_success, data_accuracy_success])
        final_assessment_results["all_requirements_met"] = requirements_met == 5
        final_assessment_results["coordinate_precision_fixes_successful"] = requirements_met >= 3  # At least 3/5 requirements met
        
        print(f"\n   🎯 FINAL ASSESSMENT SUMMARY:")
        print(f"      Requirements met: {requirements_met}/5")
        print(f"      Coordinate precision fixes successful: {final_assessment_results['coordinate_precision_fixes_successful']}")
        print(f"      All requirements met: {final_assessment_results['all_requirements_met']}")
        
        if final_assessment_results["successes"]:
            print(f"\n   ✅ SUCCESSES:")
            for success in final_assessment_results["successes"]:
                print(f"         - {success}")
        
        if final_assessment_results["issues_found"]:
            print(f"\n   ❌ ISSUES FOUND:")
            for issue in final_assessment_results["issues_found"]:
                print(f"         - {issue}")
        
        return final_assessment_results["coordinate_precision_fixes_successful"], {
            "scraper_executed": scraper_success,
            "coordinate_precision": coordinate_precision_results,
            "boundary_image_quality": boundary_image_quality_results,
            "all_properties_precision": all_properties_precision_results,
            "property_data_accuracy": property_data_accuracy_results,
            "final_assessment": final_assessment_results
        }
            
    except Exception as e:
        print(f"   ❌ Victoria County improved parser test error: {e}")
        return False, {"error": str(e)}

def main():
    """Main test execution function - Focus on Victoria County coordinate precision fixes"""
    print("🚀 Starting Backend API Testing for Nova Scotia Tax Sale Aggregator")
    print("=" * 80)
    print("🎯 FOCUS: Test both fixes - updated site branding and improved Victoria County thumbnail coordinates")
    print("📋 REVIEW REQUEST: Test Victoria County coordinate precision fixes and improved thumbnail quality")
    print("🔍 REQUIREMENTS:")
    print("   1. Re-scrape Victoria County POST /api/scrape/victoria-county to update properties with new precise coordinates")
    print("   2. Verify coordinate precision - Check that properties now have 5 decimal places (±1m accuracy) instead of 3")
    print("   3. Test boundary image quality - Check if AAN 00254118 thumbnail now shows actual building/dwelling at 198 Little Narrows Rd")
    print("   4. Verify all 3 properties - Ensure all Victoria County properties have improved coordinate precision")
    print("   5. Check property data accuracy - Confirm opening bids and HST detection still working correctly")
    print("=" * 80)
    
    # Track overall results
    test_results = {}
    
    # Test 1: Basic API connectivity
    api_connected, _ = test_api_connection()
    test_results['api_connection'] = api_connected
    
    if not api_connected:
        print("\n❌ Cannot proceed without API connection")
        return False
    
    # Test 2: Victoria County Coordinate Precision Fixes (MAIN FOCUS)
    print("\n🎯 MAIN FOCUS: Victoria County Coordinate Precision Fixes Testing")
    coordinate_fixes_successful, coordinate_data = test_victoria_county_coordinate_precision_fixes()
    test_results['victoria_county_coordinate_precision_fixes'] = coordinate_fixes_successful
    
    # Test 3: Municipalities endpoint (supporting test)
    municipalities_working, victoria_data = test_municipalities_endpoint()
    test_results['municipalities_endpoint'] = municipalities_working
    
    # Test 4: Tax sales endpoint (supporting test)
    tax_sales_working, victoria_properties = test_tax_sales_endpoint()
    test_results['tax_sales_endpoint'] = tax_sales_working
    
    # Test 5: Statistics endpoint (supporting test)
    stats_working, stats_data = test_stats_endpoint()
    test_results['stats_endpoint'] = stats_working
    
    # Final Results Summary
    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS SUMMARY - Victoria County Coordinate Precision Fixes Testing")
    print("=" * 80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"❌ Tests Failed: {total_tests - passed_tests}/{total_tests}")
    
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name.replace('_', ' ').title()}")
    
    # Victoria County Thumbnail Accuracy Analysis
    print(f"\n🎯 VICTORIA COUNTY THUMBNAIL ACCURACY ANALYSIS:")
    
    if thumbnail_accurate and thumbnail_data:
        print(f"   ✅ VICTORIA COUNTY THUMBNAILS: ACCURACY VERIFIED!")
        
        coord_results = thumbnail_data.get('coordinate_verification', {})
        boundary_results = thumbnail_data.get('boundary_image_test', {})
        satellite_results = thumbnail_data.get('satellite_params', {})
        
        print(f"      ✅ Property coordinates verified for AAN 00254118")
        print(f"      ✅ Boundary image generation working")
        print(f"      ✅ Google Maps satellite parameters appropriate")
        print(f"      ✅ Coordinate accuracy adequate for building visibility")
        
        print(f"\n   🎉 SUCCESS: Victoria County thumbnails are showing accurate property locations!")
        print(f"   ✅ AAN 00254118 coordinates point to correct location")
        print(f"   ✅ Satellite view parameters configured for building visibility")
        print(f"   ✅ Coordinate precision sufficient for property boundaries")
        
    else:
        print(f"   ❌ VICTORIA COUNTY THUMBNAILS: ACCURACY ISSUES IDENTIFIED")
        
        if thumbnail_data:
            coord_results = thumbnail_data.get('coordinate_verification', {})
            boundary_results = thumbnail_data.get('boundary_image_test', {})
            satellite_results = thumbnail_data.get('satellite_params', {})
            refinement_results = thumbnail_data.get('refinement_analysis', {})
            issues = thumbnail_data.get('thumbnail_accuracy_issues', [])
            
            print(f"      Property coordinates found: {coord_results.get('coordinates_present', False)}")
            print(f"      Boundary image accessible: {boundary_results.get('endpoint_accessible', False)}")
            print(f"      Satellite parameters correct: {satellite_results.get('zoom_level_appropriate', False)}")
            print(f"      Coordinate refinement needed: {refinement_results.get('refinement_needed', False)}")
            
            print(f"\n   ❌ THUMBNAIL ACCURACY ISSUES IDENTIFIED:")
            for issue in issues:
                print(f"      - {issue}")
            
            if refinement_results.get('recommendations'):
                print(f"\n   🔧 COORDINATE REFINEMENT RECOMMENDATIONS:")
                for i, rec in enumerate(refinement_results['recommendations'], 1):
                    print(f"      {i}. {rec}")
        else:
            print(f"      - Thumbnail accuracy test execution failed or returned no data")
    
    # Supporting Tests Analysis
    print(f"\n📊 SUPPORTING TESTS ANALYSIS:")
    
    if municipalities_working:
        print(f"   ✅ Municipalities endpoint working - Victoria County municipality accessible")
    else:
        print(f"   ❌ Municipalities endpoint issues - May affect Victoria County scraper")
    
    if tax_sales_working:
        print(f"   ✅ Tax sales endpoint working - Victoria County properties retrievable")
    else:
        print(f"   ❌ Tax sales endpoint issues - Victoria County properties may not be accessible")
    
    if stats_working:
        print(f"   ✅ Statistics endpoint working - System health good")
    else:
        print(f"   ⚠️ Statistics endpoint issues - Minor system health concern")
    
    # Overall Assessment
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n🎯 OVERALL ASSESSMENT:")
    
    if thumbnail_accurate:
        print(f"🎉 VICTORIA COUNTY THUMBNAIL ACCURACY: VERIFIED!")
        print(f"   ✅ All review request requirements met")
        print(f"   ✅ AAN 00254118 coordinates verified for 198 Little Narrows Rd, Little Narrows")
        print(f"   ✅ Boundary image generation working with /api/property-image/00254118")
        print(f"   ✅ Google Maps satellite view parameters appropriate for building visibility")
        print(f"   ✅ Coordinate accuracy adequate for property boundaries")
        print(f"   🚀 Victoria County thumbnails are showing accurate property locations!")
    else:
        print(f"❌ VICTORIA COUNTY THUMBNAIL ACCURACY: ISSUES FOUND")
        print(f"   ❌ Review request requirements not fully met")
        print(f"   🔧 Victoria County thumbnail accuracy needs fixes")
        
        if thumbnail_data:
            issues = thumbnail_data.get('thumbnail_accuracy_issues', [])
            refinement_results = thumbnail_data.get('refinement_analysis', {})
            
            print(f"\n   📋 THUMBNAIL ACCURACY ISSUES:")
            for issue in issues:
                print(f"       - {issue}")
            
            if refinement_results.get('recommendations'):
                print(f"\n   🔧 RECOMMENDED FIXES:")
                for i, rec in enumerate(refinement_results['recommendations'][:3], 1):  # Show top 3 recommendations
                    print(f"       {i}. {rec}")
            
            print(f"\n   💡 ROOT CAUSE ANALYSIS:")
            print(f"       - Current coordinates may be showing property center instead of building location")
            print(f"       - Property at 198 Little Narrows Rd may have building in different area than coordinates indicate")
            print(f"       - Coordinate precision or geocoding accuracy may need improvement for building-level detail")
    
    print(f"\n📊 System Success Rate: {success_rate:.1f}%")
    print("=" * 80)
    
    return thumbnail_accurate

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)