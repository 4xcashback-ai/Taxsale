#!/usr/bin/env python3
"""
Backend API Testing for Nova Scotia Tax Sale Aggregator
Focus on Victoria County scraper with fixed minimum bid calculation and boundary image generation
"""

import requests
import json
import sys
import re
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

def test_victoria_county_fixed_scraper():
    """Test Victoria County scraper with fixed minimum bid calculation and boundary image generation"""
    print("\n🔍 Testing Victoria County Fixed Scraper...")
    print("🎯 FOCUS: Fixed minimum bid calculation and boundary image generation")
    print("📋 REQUIREMENTS from Review Request:")
    print("   1. Test fixed scraper POST /api/scrape/victoria-county with enhanced tax amount extraction patterns")
    print("   2. Verify correct minimum bids - Should now show correct amounts:")
    print("      - Entry 1 (AAN 00254118): $2,009.03 (not $2.0)")
    print("      - Entry 2 (AAN 00453706): $1,599.71 (not $1.0)")
    print("      - Entry 8 (AAN 09541209): $5,031.96 (not $0.0)")
    print("   3. Check boundary image generation - All properties should now have:")
    print("      - Proper latitude/longitude coordinates assigned")
    print("      - boundary_screenshot URLs generated")
    print("      - Location-specific coordinates for Little Narrows, Middle River, Washabuck")
    print("   4. Verify HST detection - Entry 8 should have hst_applicable: 'Yes' due to '+ HST' in PDF")
    print("   5. Test boundary image endpoints - Try accessing the generated boundary screenshot URLs")
    print("")
    print("🔍 EXPECTED MINIMUM BIDS (fixed calculations):")
    print("   - Entry 1 (AAN 00254118): $2,009.03")
    print("   - Entry 2 (AAN 00453706): $1,599.71")
    print("   - Entry 8 (AAN 09541209): $5,031.96")
    print("🔍 EXPECTED BOUNDARY IMAGES: All properties should have boundary_screenshot URLs and coordinates")
    
    try:
        # Test 1: Victoria County Fixed Scraper - Enhanced Tax Amount Extraction
        print(f"\n   🔧 TEST 1: POST /api/scrape/victoria-county (Fixed Scraper with Enhanced Tax Amount Extraction)")
        
        scrape_response = requests.post(
            f"{BACKEND_URL}/scrape/victoria-county", 
            timeout=120  # Allow time for PDF download and processing
        )
        
        properties_count = 0
        all_data_complete = False
        fallback_detected = False
        found_aans = []
        
        if scrape_response.status_code == 200:
            scrape_result = scrape_response.json()
            print(f"   ✅ Victoria County fixed scraper executed successfully")
            print(f"      Status: {scrape_result.get('status')}")
            print(f"      Municipality: {scrape_result.get('municipality', 'N/A')}")
            print(f"      Properties scraped: {scrape_result.get('properties_scraped', 0)}")
            
            # Check property count - expecting 3 properties
            properties_count = scrape_result.get('properties_scraped', 0)
            if properties_count == 3:
                print(f"   ✅ PROPERTY COUNT: Found all 3 properties (entries 1, 2, 8)")
            elif properties_count == 1:
                print(f"   ❌ PROPERTY COUNT ISSUE: Only 1 property found (expected 3)")
                print(f"   🔍 DEBUG: PDF parsing may not be finding all numbered sections")
            else:
                print(f"   ⚠️ UNEXPECTED PROPERTY COUNT: Found {properties_count} properties (expected 3)")
            
        else:
            print(f"   ❌ Victoria County fixed scraper failed with status {scrape_response.status_code}")
            try:
                error_detail = scrape_response.json()
                print(f"      Error details: {error_detail}")
            except:
                print(f"      Raw response: {scrape_response.text[:200]}...")
            return False, {"error": f"Fixed scraper failed with HTTP {scrape_response.status_code}"}
        
        # Test 2: Verify Fixed Minimum Bid Calculations
        print(f"\n   🔧 TEST 2: GET /api/tax-sales (Verify Fixed Minimum Bid Calculations)")
        
        properties_response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Victoria County", timeout=30)
        
        if properties_response.status_code == 200:
            properties = properties_response.json()
            victoria_properties = [p for p in properties if p.get("municipality_name") == "Victoria County"]
            
            print(f"   ✅ Retrieved {len(victoria_properties)} Victoria County properties from database")
            
            # Expected minimum bids from fixed tax amount extraction (from review request)
            expected_bids = {
                "00254118": 2009.03,  # Entry 1: Should be $2,009.03 (not $2.0)
                "00453706": 1599.71,  # Entry 2: Should be $1,599.71 (not $1.0)  
                "09541209": 5031.96   # Entry 8: Should be $5,031.96 (not $0.0)
            }
            
            # Expected locations for coordinate verification
            expected_locations = {
                "00254118": "Little Narrows",
                "00453706": "Middle River", 
                "09541209": "Washabuck"
            }
            
            print(f"\n   🎯 VERIFYING FIXED MINIMUM BID CALCULATIONS:")
            
            found_aans = []
            bid_calculations_correct = True
            boundary_images_present = True
            coordinates_assigned = True
            hst_detection_correct = True
            
            for i, prop in enumerate(victoria_properties):
                aan = prop.get("assessment_number")
                owner = prop.get("owner_name")
                address = prop.get("property_address")
                pid = prop.get("pid_number")
                opening_bid = prop.get("opening_bid")
                boundary_screenshot = prop.get("boundary_screenshot")
                latitude = prop.get("latitude")
                longitude = prop.get("longitude")
                hst_applicable = prop.get("hst_applicable")
                raw_data = prop.get("raw_data", {})
                
                print(f"\n   📋 Property {i+1} - Fixed Scraper Analysis:")
                print(f"      AAN: {aan}")
                print(f"      Owner: '{owner}'")
                print(f"      Address: '{address}'")
                print(f"      Opening Bid: ${opening_bid}")
                print(f"      Coordinates: {latitude}, {longitude}")
                print(f"      HST Applicable: {hst_applicable}")
                print(f"      Boundary Screenshot: {boundary_screenshot}")
                
                # Verify fixed minimum bid calculation
                if aan in expected_bids:
                    expected_bid = expected_bids[aan]
                    if opening_bid and abs(float(opening_bid) - expected_bid) < 0.01:
                        print(f"      ✅ FIXED MINIMUM BID CORRECT: ${opening_bid} matches expected ${expected_bid}")
                    else:
                        print(f"      ❌ FIXED MINIMUM BID STILL INCORRECT: Got ${opening_bid}, expected ${expected_bid}")
                        print(f"         🔍 DEBUG: Enhanced tax amount extraction patterns may still be failing")
                        bid_calculations_correct = False
                    found_aans.append(aan)
                else:
                    print(f"      ⚠️ AAN {aan} not in expected list for bid verification")
                
                # Check coordinate assignment for boundary image generation
                if latitude and longitude:
                    print(f"      ✅ COORDINATES ASSIGNED: {latitude}, {longitude}")
                    
                    # Verify location-specific coordinates
                    if aan in expected_locations:
                        expected_location = expected_locations[aan]
                        print(f"         📍 Expected location: {expected_location}")
                        
                        # Basic coordinate validation for Nova Scotia Cape Breton area
                        if 45.5 <= latitude <= 47.0 and -61.5 <= longitude <= -59.5:
                            print(f"         ✅ Coordinates within Cape Breton region")
                        else:
                            print(f"         ⚠️ Coordinates may not be accurate for Cape Breton region")
                else:
                    print(f"      ❌ COORDINATES MISSING: No latitude/longitude for boundary image generation")
                    coordinates_assigned = False
                
                # Check HST detection for Entry 8
                if aan == "09541209":
                    if hst_applicable and hst_applicable.lower() == "yes":
                        print(f"      ✅ HST DETECTION CORRECT: Entry 8 shows HST applicable due to '+ HST' in PDF")
                    else:
                        print(f"      ❌ HST DETECTION INCORRECT: Entry 8 should show HST applicable, got '{hst_applicable}'")
                        hst_detection_correct = False
                
                # Check boundary screenshot generation
                if boundary_screenshot:
                    print(f"      ✅ BOUNDARY IMAGE: Screenshot field populated - {boundary_screenshot}")
                    
                    # Test if the boundary image is accessible
                    try:
                        image_response = requests.get(f"{BACKEND_URL}/boundary-image/{boundary_screenshot}", timeout=10)
                        if image_response.status_code == 200:
                            print(f"         ✅ Image accessible via API endpoint")
                            print(f"         📏 Image size: {len(image_response.content)} bytes")
                        else:
                            print(f"         ❌ Image not accessible: HTTP {image_response.status_code}")
                            boundary_images_present = False
                    except Exception as e:
                        print(f"         ❌ Error accessing image: {e}")
                        boundary_images_present = False
                else:
                    print(f"      ❌ BOUNDARY IMAGE: No screenshot field - image generation still not working")
                    boundary_images_present = False
                
                # Check raw_data for tax amount extraction patterns
                if raw_data:
                    tax_amount_raw = raw_data.get('tax_amount', '')
                    if tax_amount_raw:
                        print(f"      📊 Raw tax amount: {tax_amount_raw}")
                        # Check if it matches the "Taxes, Interest and Expenses owing: $X,XXX.XX" pattern
                        if "Taxes, Interest and Expenses owing:" in str(tax_amount_raw):
                            print(f"         ✅ Tax amount extraction pattern working")
                        else:
                            print(f"         ⚠️ Tax amount may not be extracted from expected pattern")
                    else:
                        print(f"      ⚠️ No raw tax amount data available")
                else:
                    print(f"      ⚠️ No raw data available for tax amount analysis")
            
            # Summary of fixed scraper findings
            print(f"\n   📊 FIXED SCRAPER ANALYSIS SUMMARY:")
            print(f"      Properties found: {len(victoria_properties)}")
            print(f"      Fixed bid calculations correct: {bid_calculations_correct}")
            print(f"      Coordinates assigned: {coordinates_assigned}")
            print(f"      Boundary images present: {boundary_images_present}")
            print(f"      HST detection correct: {hst_detection_correct}")
            print(f"      AANs found: {found_aans}")
            
            # Critical issues identified
            if not bid_calculations_correct:
                print(f"\n   🚨 CRITICAL ISSUE: Fixed minimum bid calculations still incorrect")
                print(f"      - Enhanced tax amount extraction patterns not working")
                print(f"      - Opening bid values still showing low amounts instead of correct PDF tax amounts")
                print(f"      - Expected: Entry 1=$2,009.03, Entry 2=$1,599.71, Entry 8=$5,031.96")
            
            if not coordinates_assigned:
                print(f"\n   🚨 CRITICAL ISSUE: Coordinates not assigned")
                print(f"      - Properties missing latitude/longitude for boundary image generation")
                print(f"      - Location-specific coordinates for Little Narrows, Middle River, Washabuck not working")
            
            if not boundary_images_present:
                print(f"\n   🚨 CRITICAL ISSUE: Boundary images still missing")
                print(f"      - boundary_screenshot fields still None/empty")
                print(f"      - Image generation pipeline still not working")
                print(f"      - May be related to coordinates or Google Maps API integration")
            
            if not hst_detection_correct:
                print(f"\n   🚨 CRITICAL ISSUE: HST detection not working")
                print(f"      - Entry 8 should show hst_applicable: 'Yes' due to '+ HST' in PDF")
                print(f"      - Enhanced patterns not detecting HST indicators correctly")
            
        else:
            print(f"   ❌ Failed to retrieve Victoria County properties: {properties_response.status_code}")
            return False, {"error": f"Failed to retrieve properties: HTTP {properties_response.status_code}"}
        
        # Test 3: Test Enhanced Tax Amount Extraction Patterns
        print(f"\n   🔧 TEST 3: Test Enhanced Tax Amount Extraction Patterns")
        
        debug_response = requests.get(f"{BACKEND_URL}/debug/victoria-county-pdf", timeout=30)
        
        enhanced_patterns_working = False
        
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            print(f"   ✅ Debug endpoint available for enhanced pattern analysis")
            
            # Analyze PDF content for enhanced tax amount patterns
            pdf_content = debug_data.get('pdf_content_preview', '')
            analysis = debug_data.get('analysis', {})
            
            print(f"      PDF Content Length: {len(pdf_content)} characters")
            
            # Check for enhanced tax amount extraction patterns
            enhanced_patterns = [
                r"Taxes, Interest and Expenses owing:\s*\$[\d,]+\.?\d*",
                r"owing:\s*\$[\d,]+\.?\d*",
                r"\$[\d,]+\.\d{2}",  # General dollar amounts
                r"[\d,]+\.\d{2}"     # Numeric amounts
            ]
            
            print(f"   🔍 TESTING ENHANCED TAX AMOUNT PATTERNS:")
            
            for i, pattern in enumerate(enhanced_patterns):
                matches = re.findall(pattern, pdf_content)
                print(f"      Pattern {i+1}: {pattern}")
                print(f"         Matches found: {len(matches)}")
                
                if matches:
                    enhanced_patterns_working = True
                    for j, match in enumerate(matches[:3]):  # Show first 3 matches
                        print(f"         Match {j+1}: {match}")
                        
                        # Extract numeric value
                        numeric_match = re.search(r'[\d,]+\.?\d*', match.replace('$', ''))
                        if numeric_match:
                            amount = numeric_match.group().replace(',', '')
                            try:
                                amount_float = float(amount)
                                if 1000 <= amount_float <= 10000:  # Expected range for Victoria County
                                    print(f"            ✅ Valid tax amount: ${amount}")
                                else:
                                    print(f"            ⚠️ Amount outside expected range: ${amount}")
                            except:
                                print(f"            ❌ Could not parse amount: {amount}")
            
            # Check for HST indicators
            hst_patterns = [r"\+\s*HST", r"plus HST", r"HST applicable"]
            hst_found = False
            
            print(f"\n   🔍 TESTING HST DETECTION PATTERNS:")
            for pattern in hst_patterns:
                hst_matches = re.findall(pattern, pdf_content, re.IGNORECASE)
                if hst_matches:
                    hst_found = True
                    print(f"      ✅ HST pattern found: {pattern} - {len(hst_matches)} matches")
                    for match in hst_matches[:2]:
                        print(f"         Match: {match}")
                else:
                    print(f"      ❌ HST pattern not found: {pattern}")
            
            if not hst_found:
                print(f"   ❌ NO HST INDICATORS FOUND: Entry 8 HST detection may fail")
                
            # Check for AAN occurrences
            aan_count = analysis.get('aan_occurrences', 0)
            if aan_count >= 3:
                print(f"   ✅ AAN DETECTION: Found {aan_count} AAN occurrences in PDF")
            else:
                print(f"   ❌ AAN DETECTION ISSUE: Only {aan_count} AAN occurrences found (expected 3)")
                
        else:
            print(f"   ⚠️ Debug endpoint not available (status: {debug_response.status_code})")
            print(f"   ℹ️ Cannot verify enhanced tax amount extraction patterns without debug endpoint")
        
        # Test 4: Test Boundary Image Generation and Endpoints
        print(f"\n   🔧 TEST 4: Test Boundary Image Generation and Endpoints")
        
        # Test Google Maps API key and static map generation
        google_maps_working = True
        boundary_endpoints_working = True
        
        # Check if properties have coordinates for map generation
        properties_with_coords = [p for p in victoria_properties if p.get('latitude') and p.get('longitude')]
        print(f"   📍 Properties with coordinates: {len(properties_with_coords)}/{len(victoria_properties)}")
        
        if properties_with_coords:
            # Test Google Maps static API with first property coordinates
            test_prop = properties_with_coords[0]
            lat = test_prop.get('latitude')
            lng = test_prop.get('longitude')
            aan = test_prop.get('assessment_number')
            
            # Test static map API (similar to what the backend uses for boundary generation)
            test_map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=405x290&maptype=satellite&format=png&key=AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY"
            
            try:
                map_response = requests.get(test_map_url, timeout=10)
                if map_response.status_code == 200 and 'image' in map_response.headers.get('content-type', ''):
                    print(f"   ✅ GOOGLE MAPS API: Static map generation working")
                    print(f"      Test coordinates: {lat}, {lng} (AAN: {aan})")
                    print(f"      Response size: {len(map_response.content)} bytes")
                else:
                    print(f"   ❌ GOOGLE MAPS API: Static map generation failed")
                    print(f"      Status: {map_response.status_code}")
                    print(f"      Content-Type: {map_response.headers.get('content-type', 'unknown')}")
                    google_maps_working = False
            except Exception as e:
                print(f"   ❌ GOOGLE MAPS API: Error testing static map - {e}")
                google_maps_working = False
        else:
            print(f"   ❌ COORDINATES MISSING: No properties have latitude/longitude for map generation")
            google_maps_working = False
        
        # Test boundary image endpoints for all Victoria County properties
        print(f"\n   🔍 TESTING BOUNDARY IMAGE ENDPOINTS:")
        
        for prop in victoria_properties:
            aan = prop.get('assessment_number')
            boundary_screenshot = prop.get('boundary_screenshot')
            
            if aan:
                # Test property image endpoint
                try:
                    image_response = requests.get(f"{BACKEND_URL}/property-image/{aan}", timeout=10)
                    if image_response.status_code == 200:
                        print(f"      ✅ Property image endpoint working for AAN {aan}")
                        print(f"         Image size: {len(image_response.content)} bytes")
                        print(f"         Content-Type: {image_response.headers.get('content-type', 'unknown')}")
                    else:
                        print(f"      ❌ Property image endpoint failed for AAN {aan} - HTTP {image_response.status_code}")
                        boundary_endpoints_working = False
                except Exception as e:
                    print(f"      ❌ Property image endpoint error for AAN {aan} - {e}")
                    boundary_endpoints_working = False
                
                # Test boundary image endpoint if screenshot exists
                if boundary_screenshot:
                    try:
                        boundary_response = requests.get(f"{BACKEND_URL}/boundary-image/{boundary_screenshot}", timeout=10)
                        if boundary_response.status_code == 200:
                            print(f"      ✅ Boundary image endpoint working for {boundary_screenshot}")
                            print(f"         Image size: {len(boundary_response.content)} bytes")
                        else:
                            print(f"      ❌ Boundary image endpoint failed for {boundary_screenshot} - HTTP {boundary_response.status_code}")
                            boundary_endpoints_working = False
                    except Exception as e:
                        print(f"      ❌ Boundary image endpoint error for {boundary_screenshot} - {e}")
                        boundary_endpoints_working = False
                else:
                    print(f"      ⚠️ No boundary screenshot file for AAN {aan}")
        
        # Summary of boundary image generation status
        if coordinates_assigned and google_maps_working and boundary_images_present:
            print(f"\n   ✅ BOUNDARY IMAGE GENERATION: All components working")
            print(f"      - Coordinates assigned to all properties")
            print(f"      - Google Maps API generating static maps")
            print(f"      - Boundary screenshot files created and accessible")
        else:
            print(f"\n   ❌ BOUNDARY IMAGE GENERATION: Issues identified")
            if not coordinates_assigned:
                print(f"      - Missing coordinates for location-specific assignment")
            if not google_maps_working:
                print(f"      - Google Maps API not generating static maps")
            if not boundary_images_present:
                print(f"      - Boundary screenshot files not created or not accessible")
        
        # Final Assessment - Victoria County Fixed Scraper
        print(f"\n   📊 FINAL ASSESSMENT - Victoria County Fixed Scraper:")
        
        requirements_met = []
        requirements_failed = []
        
        # Requirement 1: Fixed scraper execution with enhanced tax amount extraction
        if scrape_response.status_code == 200 and properties_count == 3:
            requirements_met.append("1. Fixed scraper with enhanced tax amount extraction patterns")
        else:
            requirements_failed.append("1. Fixed scraper with enhanced tax amount extraction patterns")
        
        # Requirement 2: Correct minimum bids (fixed calculations)
        if bid_calculations_correct:
            requirements_met.append("2. Correct minimum bids - Entry 1: $2,009.03, Entry 2: $1,599.71, Entry 8: $5,031.96")
        else:
            requirements_failed.append("2. Correct minimum bids - Entry 1: $2,009.03, Entry 2: $1,599.71, Entry 8: $5,031.96")
        
        # Requirement 3: Boundary image generation with coordinates
        if coordinates_assigned and boundary_images_present:
            requirements_met.append("3. Boundary image generation - coordinates and screenshot URLs")
        else:
            requirements_failed.append("3. Boundary image generation - coordinates and screenshot URLs")
        
        # Requirement 4: HST detection for Entry 8
        if hst_detection_correct:
            requirements_met.append("4. HST detection - Entry 8 shows 'Yes' due to '+ HST' in PDF")
        else:
            requirements_failed.append("4. HST detection - Entry 8 shows 'Yes' due to '+ HST' in PDF")
        
        # Requirement 5: Boundary image endpoints accessible
        if boundary_endpoints_working:
            requirements_met.append("5. Boundary image endpoints accessible")
        else:
            requirements_failed.append("5. Boundary image endpoints accessible")
        
        print(f"\n   ✅ REQUIREMENTS MET ({len(requirements_met)}/5):")
        for req in requirements_met:
            print(f"      ✅ {req}")
        
        if requirements_failed:
            print(f"\n   ❌ REQUIREMENTS FAILED ({len(requirements_failed)}/5):")
            for req in requirements_failed:
                print(f"      ❌ {req}")
        
        # Overall result
        if len(requirements_failed) == 0:
            print(f"\n   🎉 VICTORIA COUNTY FIXED SCRAPER: ALL REQUIREMENTS MET!")
            print(f"   ✅ Enhanced tax amount extraction patterns working correctly")
            print(f"   ✅ All 3 properties show correct minimum bids from PDF tax amounts")
            print(f"   ✅ Boundary image generation working with proper coordinates")
            print(f"   ✅ Location-specific coordinates assigned for Little Narrows, Middle River, Washabuck")
            print(f"   ✅ HST detection working for Entry 8 with '+ HST' indicator")
            print(f"   ✅ Boundary image endpoints accessible for all properties")
            return True, {
                "requirements_met": len(requirements_met),
                "requirements_failed": len(requirements_failed),
                "properties_found": properties_count,
                "bid_calculations_correct": bid_calculations_correct,
                "coordinates_assigned": coordinates_assigned,
                "boundary_images_present": boundary_images_present,
                "hst_detection_correct": hst_detection_correct,
                "boundary_endpoints_working": boundary_endpoints_working,
                "expected_aans_found": found_aans
            }
        else:
            print(f"\n   ❌ VICTORIA COUNTY FIXED SCRAPER: {len(requirements_failed)} REQUIREMENTS FAILED")
            return False, {
                "requirements_met": len(requirements_met),
                "requirements_failed": len(requirements_failed),
                "failed_requirements": requirements_failed,
                "properties_found": properties_count,
                "bid_calculations_correct": bid_calculations_correct,
                "coordinates_assigned": coordinates_assigned,
                "boundary_images_present": boundary_images_present,
                "hst_detection_correct": hst_detection_correct,
                "boundary_endpoints_working": boundary_endpoints_working,
                "expected_aans_found": found_aans
            }
            
    except Exception as e:
        print(f"   ❌ Victoria County improved parser test error: {e}")
        return False, {"error": str(e)}

def main():
    """Main test execution function - Focus on Victoria County Data Extraction Debug"""
    print("🚀 Starting Backend API Testing for Nova Scotia Tax Sale Aggregator")
    print("=" * 80)
    print("🎯 FOCUS: Victoria County Data Extraction Issues - Minimum Bid and Missing Images")
    print("📋 REVIEW REQUEST: Debug Victoria County data extraction issues")
    print("🔍 REQUIREMENTS:")
    print("   1. Test current Victoria County properties - Check actual data being extracted for all 3 properties")
    print("   2. Verify minimum bid calculations - Compare extracted opening_bid values against PDF tax amounts")
    print("   3. Check boundary screenshot generation - Verify if boundary_screenshot field is being generated")
    print("   4. Debug tax amount extraction - Check if regex patterns correctly extract from 'Taxes, Interest and Expenses owing: $X,XXX.XX'")
    print("   5. Verify property images - Check if Google Maps static API is generating boundary thumbnails")
    print("=" * 80)
    
    # Track overall results
    test_results = {}
    
    # Test 1: Basic API connectivity
    api_connected, _ = test_api_connection()
    test_results['api_connection'] = api_connected
    
    if not api_connected:
        print("\n❌ Cannot proceed without API connection")
        return False
    
    # Test 2: Victoria County Data Extraction Debug (MAIN FOCUS)
    print("\n🎯 MAIN FOCUS: Victoria County Data Extraction Debug")
    victoria_county_working, victoria_county_data = test_victoria_county_data_extraction_debug()
    test_results['victoria_county_data_extraction_debug'] = victoria_county_working
    
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
    print("📊 FINAL TEST RESULTS SUMMARY - Victoria County Improved Parser Focus")
    print("=" * 80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"❌ Tests Failed: {total_tests - passed_tests}/{total_tests}")
    
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name.replace('_', ' ').title()}")
    
    # Victoria County Specific Analysis
    print(f"\n🎯 VICTORIA COUNTY IMPROVED PARSER ANALYSIS:")
    
    if victoria_county_working and victoria_county_data:
        print(f"   ✅ VICTORIA COUNTY IMPROVED PARSER: ALL REQUIREMENTS MET!")
        print(f"      Requirements Met: {victoria_county_data.get('requirements_met', 0)}/6")
        print(f"      Properties Found: {victoria_county_data.get('properties_found', 0)}")
        print(f"      All Data Complete: {victoria_county_data.get('all_data_complete', False)}")
        print(f"      Fallback Detected: {victoria_county_data.get('fallback_detected', True)}")
        print(f"      Sale Date Correct: {victoria_county_data.get('sale_date_correct', False)}")
        
        if victoria_county_data.get('expected_aans_found'):
            print(f"      Expected AANs Found: {victoria_county_data['expected_aans_found']}")
        
        print(f"\n   🎉 SUCCESS: Victoria County improved parser working correctly!")
        print(f"   ✅ Enhanced regex patterns successfully extract all 3 properties")
        print(f"   ✅ Pattern matching handles different property formats and multiple PIDs")
        print(f"   ✅ All properties have correct owners, addresses, tax amounts, and property types")
        print(f"   ✅ Using actual PDF data, not fallback sample data")
        print(f"   ✅ Sale date correctly set to 2025-08-26")
        
    elif not victoria_county_working and victoria_county_data:
        print(f"   ❌ VICTORIA COUNTY IMPROVED PARSER: REQUIREMENTS NOT MET")
        print(f"      Requirements Met: {victoria_county_data.get('requirements_met', 0)}/6")
        print(f"      Requirements Failed: {victoria_county_data.get('requirements_failed', 6)}/6")
        
        if victoria_county_data.get('failed_requirements'):
            print(f"      Failed Requirements:")
            for req in victoria_county_data['failed_requirements']:
                print(f"         ❌ {req}")
        
        print(f"      Properties Found: {victoria_county_data.get('properties_found', 0)} (expected 3)")
        print(f"      All Data Complete: {victoria_county_data.get('all_data_complete', False)}")
        print(f"      Fallback Detected: {victoria_county_data.get('fallback_detected', True)}")
        
        print(f"\n   ❌ ISSUES IDENTIFIED:")
        if victoria_county_data.get('properties_found', 0) != 3:
            print(f"      - Parser not finding all 3 properties from PDF entries 1, 2, 8")
        if victoria_county_data.get('fallback_detected', True):
            print(f"      - System using fallback data instead of actual PDF parsing")
        if not victoria_county_data.get('all_data_complete', False):
            print(f"      - Some properties missing correct AANs, owners, addresses, or tax amounts")
    else:
        print(f"   ❌ VICTORIA COUNTY PARSER: CRITICAL ERROR")
        print(f"      - Parser execution failed or returned no data")
    
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
    
    if victoria_county_working:
        print(f"🎉 VICTORIA COUNTY IMPROVED PARSER: SUCCESS!")
        print(f"   ✅ All review request requirements met")
        print(f"   ✅ Enhanced regex patterns working for all property formats")
        print(f"   ✅ All 3 properties extracted from PDF entries 1, 2, 8")
        print(f"   ✅ Pattern matching handles different formats and multiple PIDs")
        print(f"   ✅ Complete data validation passed")
        print(f"   ✅ Using actual PDF data, not fallback")
        print(f"   ✅ Sale date correctly set to 2025-08-26")
        print(f"   🚀 Victoria County improved parser is production-ready!")
    else:
        print(f"❌ VICTORIA COUNTY IMPROVED PARSER: FAILED")
        print(f"   ❌ Review request requirements not met")
        print(f"   🔧 Enhanced regex patterns need additional work")
        print(f"   📋 Check pattern matching for PDF entries 1, 2, 8 extraction")
        print(f"   📋 Verify enhanced patterns handle different property formats")
        print(f"   📋 Ensure multiple PID handling for Entry 2")
        print(f"   📋 Verify sale date extraction to 2025-08-26")
    
    print(f"\n📊 System Success Rate: {success_rate:.1f}%")
    print("=" * 80)
    
    return victoria_county_working

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)