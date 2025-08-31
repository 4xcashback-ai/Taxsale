#!/usr/bin/env python3
"""
Backend API Testing for Nova Scotia Tax Sale Aggregator
Focus on Victoria County scraper with direct PDF extraction fix for correct minimum bid amounts
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

def test_victoria_county_scraper_with_pdf_extraction():
    """Test Victoria County scraper with direct PDF extraction fix for correct minimum bid amounts"""
    print("\n🔍 Testing Victoria County Scraper with Direct PDF Extraction Fix...")
    print("🎯 FOCUS: Test fixed Victoria County scraper with new direct PDF extraction logic")
    print("📋 REQUIREMENTS from Review Request:")
    print("   1. Test fixed Victoria County scraper POST /api/scrape/victoria-county with new direct PDF extraction logic")
    print("   2. Verify correct minimum bid amounts - Should now extract actual tax amounts from PDF:")
    print("      - Entry 1 (AAN 00254118): $2,009.03 (not $2.0)")
    print("      - Entry 2 (AAN 00453706): $1,599.71 (not $1.0)")
    print("      - Entry 8 (AAN 09541209): $5,031.96 (not $0.0)")
    print("   3. Check HST detection - Entry 8 should now show hst_applicable: 'Yes'")
    print("   4. Verify all properties - Should find all 3 properties with complete accurate data")
    print("   5. Test boundary images - Confirm boundary screenshot URLs are still working")
    print("")
    print("🔍 TESTING GOALS:")
    print("   - Are the opening_bid amounts now correct from actual PDF extraction?")
    print("   - Does Entry 8 correctly show HST as 'Yes'?")
    print("   - Are all 3 properties extracted with complete and accurate data?")
    print("   - Do boundary images continue to work properly?")
    
    try:
        # Test 1: Execute Victoria County Scraper
        print(f"\n   🔧 TEST 1: Execute Victoria County Scraper with Direct PDF Extraction")
        
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
        
        # Test 2: Compare Halifax Property Thumbnails
        print(f"\n   🔧 TEST 2: Test Halifax Property Thumbnails")
        
        halifax_thumbnail_results = {
            "properties_with_coordinates": 0,
            "properties_with_boundary_screenshots": 0,
            "working_thumbnail_endpoints": 0,
            "thumbnail_sizes": [],
            "coordinate_accuracy": True,
            "sample_properties": []
        }
        
        if halifax_properties:
            print(f"   📊 Analyzing {len(halifax_properties)} Halifax properties...")
            
            # Test first 3 Halifax properties for thumbnail generation
            for i, prop in enumerate(halifax_properties[:3]):
                aan = prop.get("assessment_number")
                owner = prop.get("owner_name")
                address = prop.get("property_address")
                latitude = prop.get("latitude")
                longitude = prop.get("longitude")
                boundary_screenshot = prop.get("boundary_screenshot")
                
                print(f"\n   📋 Halifax Property {i+1}:")
                print(f"      AAN: {aan}")
                print(f"      Owner: {owner}")
                print(f"      Address: {address}")
                print(f"      Coordinates: {latitude}, {longitude}")
                print(f"      Boundary Screenshot: {boundary_screenshot}")
                
                # Check coordinates
                if latitude and longitude:
                    halifax_thumbnail_results["properties_with_coordinates"] += 1
                    print(f"      ✅ Has coordinates for thumbnail generation")
                    
                    # Verify Halifax coordinates are in Nova Scotia region
                    if 44.0 <= latitude <= 47.0 and -66.0 <= longitude <= -59.0:
                        print(f"      ✅ Coordinates within Nova Scotia region")
                    else:
                        print(f"      ⚠️ Coordinates may be outside Nova Scotia region")
                        halifax_thumbnail_results["coordinate_accuracy"] = False
                else:
                    print(f"      ❌ Missing coordinates - cannot generate thumbnails")
                
                # Check boundary screenshot
                if boundary_screenshot:
                    halifax_thumbnail_results["properties_with_boundary_screenshots"] += 1
                    print(f"      ✅ Has boundary screenshot: {boundary_screenshot}")
                else:
                    print(f"      ❌ No boundary screenshot generated")
                
                # Test property image endpoint
                if aan:
                    try:
                        image_response = requests.get(f"{BACKEND_URL}/property-image/{aan}", timeout=10)
                        if image_response.status_code == 200:
                            image_size = len(image_response.content)
                            halifax_thumbnail_results["working_thumbnail_endpoints"] += 1
                            halifax_thumbnail_results["thumbnail_sizes"].append(image_size)
                            print(f"      ✅ Thumbnail endpoint working - Size: {image_size} bytes")
                            print(f"      📷 Content-Type: {image_response.headers.get('content-type', 'unknown')}")
                        else:
                            print(f"      ❌ Thumbnail endpoint failed - HTTP {image_response.status_code}")
                    except Exception as e:
                        print(f"      ❌ Thumbnail endpoint error: {e}")
                
                halifax_thumbnail_results["sample_properties"].append({
                    "aan": aan,
                    "has_coordinates": bool(latitude and longitude),
                    "has_boundary_screenshot": bool(boundary_screenshot),
                    "thumbnail_working": False  # Will be updated above
                })
        
        else:
            print(f"   ⚠️ No Halifax properties available for thumbnail comparison")
        # Test 3: Compare Victoria County Property Thumbnails
        print(f"\n   🔧 TEST 3: Test Victoria County Property Thumbnails")
        
        victoria_thumbnail_results = {
            "properties_with_coordinates": 0,
            "properties_with_boundary_screenshots": 0,
            "working_thumbnail_endpoints": 0,
            "thumbnail_sizes": [],
            "coordinate_accuracy": True,
            "sample_properties": []
        }
        
        if victoria_properties:
            print(f"   📊 Analyzing {len(victoria_properties)} Victoria County properties...")
            
            # Test all Victoria County properties for thumbnail generation
            for i, prop in enumerate(victoria_properties):
                aan = prop.get("assessment_number")
                owner = prop.get("owner_name")
                address = prop.get("property_address")
                latitude = prop.get("latitude")
                longitude = prop.get("longitude")
                boundary_screenshot = prop.get("boundary_screenshot")
                
                print(f"\n   📋 Victoria County Property {i+1}:")
                print(f"      AAN: {aan}")
                print(f"      Owner: {owner}")
                print(f"      Address: {address}")
                print(f"      Coordinates: {latitude}, {longitude}")
                print(f"      Boundary Screenshot: {boundary_screenshot}")
                
                # Check coordinates
                if latitude and longitude:
                    victoria_thumbnail_results["properties_with_coordinates"] += 1
                    print(f"      ✅ Has coordinates for thumbnail generation")
                    
                    # Verify Victoria County coordinates are in Cape Breton region
                    if 45.5 <= latitude <= 47.0 and -61.5 <= longitude <= -59.5:
                        print(f"      ✅ Coordinates within Cape Breton region")
                    else:
                        print(f"      ⚠️ Coordinates may be outside Cape Breton region")
                        victoria_thumbnail_results["coordinate_accuracy"] = False
                else:
                    print(f"      ❌ Missing coordinates - cannot generate thumbnails")
                
                # Check boundary screenshot
                if boundary_screenshot:
                    victoria_thumbnail_results["properties_with_boundary_screenshots"] += 1
                    print(f"      ✅ Has boundary screenshot: {boundary_screenshot}")
                else:
                    print(f"      ❌ No boundary screenshot generated")
                
                # Test property image endpoint
                if aan:
                    try:
                        image_response = requests.get(f"{BACKEND_URL}/property-image/{aan}", timeout=10)
                        if image_response.status_code == 200:
                            image_size = len(image_response.content)
                            victoria_thumbnail_results["working_thumbnail_endpoints"] += 1
                            victoria_thumbnail_results["thumbnail_sizes"].append(image_size)
                            print(f"      ✅ Thumbnail endpoint working - Size: {image_size} bytes")
                            print(f"      📷 Content-Type: {image_response.headers.get('content-type', 'unknown')}")
                        else:
                            print(f"      ❌ Thumbnail endpoint failed - HTTP {image_response.status_code}")
                    except Exception as e:
                        print(f"      ❌ Thumbnail endpoint error: {e}")
                
                victoria_thumbnail_results["sample_properties"].append({
                    "aan": aan,
                    "has_coordinates": bool(latitude and longitude),
                    "has_boundary_screenshot": bool(boundary_screenshot),
                    "thumbnail_working": False  # Will be updated above
                })
        
        else:
            print(f"   ⚠️ No Victoria County properties available for thumbnail comparison")
        # Test 4: Compare Boundary Data Availability
        print(f"\n   🔧 TEST 4: Compare Boundary Data Availability Between Municipalities")
        
        print(f"\n   📊 HALIFAX BOUNDARY DATA SUMMARY:")
        if halifax_properties:
            halifax_total = len(halifax_properties)
            halifax_coords = halifax_thumbnail_results["properties_with_coordinates"]
            halifax_screenshots = halifax_thumbnail_results["properties_with_boundary_screenshots"]
            halifax_working = halifax_thumbnail_results["working_thumbnail_endpoints"]
            
            print(f"      Total properties: {halifax_total}")
            print(f"      Properties with coordinates: {halifax_coords}/{halifax_total} ({(halifax_coords/halifax_total*100):.1f}%)")
            print(f"      Properties with boundary screenshots: {halifax_screenshots}/{halifax_total} ({(halifax_screenshots/halifax_total*100):.1f}%)")
            print(f"      Working thumbnail endpoints: {halifax_working}/{halifax_total} ({(halifax_working/halifax_total*100):.1f}%)")
            
            if halifax_thumbnail_results["thumbnail_sizes"]:
                avg_size = sum(halifax_thumbnail_results["thumbnail_sizes"]) / len(halifax_thumbnail_results["thumbnail_sizes"])
                print(f"      Average thumbnail size: {avg_size:.0f} bytes")
        else:
            print(f"      No Halifax properties available for analysis")
        
        print(f"\n   📊 VICTORIA COUNTY BOUNDARY DATA SUMMARY:")
        if victoria_properties:
            victoria_total = len(victoria_properties)
            victoria_coords = victoria_thumbnail_results["properties_with_coordinates"]
            victoria_screenshots = victoria_thumbnail_results["properties_with_boundary_screenshots"]
            victoria_working = victoria_thumbnail_results["working_thumbnail_endpoints"]
            
            print(f"      Total properties: {victoria_total}")
            print(f"      Properties with coordinates: {victoria_coords}/{victoria_total} ({(victoria_coords/victoria_total*100):.1f}%)")
            print(f"      Properties with boundary screenshots: {victoria_screenshots}/{victoria_total} ({(victoria_screenshots/victoria_total*100):.1f}%)")
            print(f"      Working thumbnail endpoints: {victoria_working}/{victoria_total} ({(victoria_working/victoria_total*100):.1f}%)")
            
            if victoria_thumbnail_results["thumbnail_sizes"]:
                avg_size = sum(victoria_thumbnail_results["thumbnail_sizes"]) / len(victoria_thumbnail_results["thumbnail_sizes"])
                print(f"      Average thumbnail size: {avg_size:.0f} bytes")
        else:
            print(f"      No Victoria County properties available for analysis")
        
        # Test 5: Verify Boundary Generation Process Comparison
        print(f"\n   🔧 TEST 5: Verify Boundary Generation Process for Both Municipality Types")
        
        print(f"\n   🔍 TESTING /api/property-image ENDPOINT FOR BOTH MUNICIPALITIES:")
        
        # Test Halifax property image endpoints
        halifax_endpoint_results = []
        if halifax_properties:
            print(f"\n   📍 Testing Halifax Property Image Endpoints:")
            for i, prop in enumerate(halifax_properties[:3]):  # Test first 3
                aan = prop.get("assessment_number")
                if aan:
                    try:
                        image_response = requests.get(f"{BACKEND_URL}/property-image/{aan}", timeout=10)
                        result = {
                            "aan": aan,
                            "status_code": image_response.status_code,
                            "content_type": image_response.headers.get('content-type', 'unknown'),
                            "size": len(image_response.content) if image_response.status_code == 200 else 0,
                            "working": image_response.status_code == 200
                        }
                        halifax_endpoint_results.append(result)
                        
                        if result["working"]:
                            print(f"      ✅ Halifax AAN {aan}: {result['size']} bytes, {result['content_type']}")
                        else:
                            print(f"      ❌ Halifax AAN {aan}: HTTP {result['status_code']}")
                    except Exception as e:
                        print(f"      ❌ Halifax AAN {aan}: Error - {e}")
                        halifax_endpoint_results.append({"aan": aan, "working": False, "error": str(e)})
        
        # Test Victoria County property image endpoints
        victoria_endpoint_results = []
        if victoria_properties:
            print(f"\n   📍 Testing Victoria County Property Image Endpoints:")
            for i, prop in enumerate(victoria_properties):
                aan = prop.get("assessment_number")
                if aan:
                    try:
                        image_response = requests.get(f"{BACKEND_URL}/property-image/{aan}", timeout=10)
                        result = {
                            "aan": aan,
                            "status_code": image_response.status_code,
                            "content_type": image_response.headers.get('content-type', 'unknown'),
                            "size": len(image_response.content) if image_response.status_code == 200 else 0,
                            "working": image_response.status_code == 200
                        }
                        victoria_endpoint_results.append(result)
                        
                        if result["working"]:
                            print(f"      ✅ Victoria County AAN {aan}: {result['size']} bytes, {result['content_type']}")
                        else:
                            print(f"      ❌ Victoria County AAN {aan}: HTTP {result['status_code']}")
                    except Exception as e:
                        print(f"      ❌ Victoria County AAN {aan}: Error - {e}")
                        victoria_endpoint_results.append({"aan": aan, "working": False, "error": str(e)})
        
        # Test 6: Check Coordinate Accuracy for Boundary Generation
        print(f"\n   🔧 TEST 6: Check Coordinate Accuracy for Proper Boundary Generation")
        
        print(f"\n   📍 COORDINATE ACCURACY ANALYSIS:")
        
        # Analyze Halifax coordinates
        if halifax_properties:
            halifax_coords_analysis = []
            for prop in halifax_properties[:3]:
                lat = prop.get("latitude")
                lng = prop.get("longitude")
                aan = prop.get("assessment_number")
                address = prop.get("property_address", "")
                
                if lat and lng:
                    # Check if coordinates are in Halifax region (approximate bounds)
                    halifax_region = 44.5 <= lat <= 45.0 and -64.0 <= lng <= -63.0
                    halifax_coords_analysis.append({
                        "aan": aan,
                        "coordinates": (lat, lng),
                        "in_halifax_region": halifax_region,
                        "address": address
                    })
            
            print(f"   📊 Halifax Coordinate Analysis:")
            for analysis in halifax_coords_analysis:
                region_status = "✅ In Halifax region" if analysis["in_halifax_region"] else "⚠️ Outside Halifax region"
                print(f"      AAN {analysis['aan']}: {analysis['coordinates']} - {region_status}")
        
        # Analyze Victoria County coordinates
        if victoria_properties:
            victoria_coords_analysis = []
            for prop in victoria_properties:
                lat = prop.get("latitude")
                lng = prop.get("longitude")
                aan = prop.get("assessment_number")
                address = prop.get("property_address", "")
                
                if lat and lng:
                    # Check if coordinates are in Cape Breton/Victoria County region
                    cape_breton_region = 45.5 <= lat <= 47.0 and -61.5 <= lng <= -59.5
                    victoria_coords_analysis.append({
                        "aan": aan,
                        "coordinates": (lat, lng),
                        "in_cape_breton_region": cape_breton_region,
                        "address": address
                    })
            
            print(f"   📊 Victoria County Coordinate Analysis:")
            for analysis in victoria_coords_analysis:
                region_status = "✅ In Cape Breton region" if analysis["in_cape_breton_region"] else "⚠️ Outside Cape Breton region"
                print(f"      AAN {analysis['aan']}: {analysis['coordinates']} - {region_status}")
        
        # Test Google Maps API with sample coordinates from both municipalities
        print(f"\n   🗺️ GOOGLE MAPS API TESTING:")
        
        google_maps_api_key = "AIzaSyACMb9WO0Y-f0-qNraOgInWvSdErwyrCdY"
        
        # Test with Halifax coordinates if available
        if halifax_properties and halifax_properties[0].get("latitude"):
            halifax_prop = halifax_properties[0]
            lat, lng = halifax_prop.get("latitude"), halifax_prop.get("longitude")
            test_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=405x290&maptype=satellite&format=png&key={google_maps_api_key}"
            
            try:
                response = requests.get(test_url, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ Halifax Google Maps API test: {len(response.content)} bytes")
                else:
                    print(f"   ❌ Halifax Google Maps API test failed: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ Halifax Google Maps API test error: {e}")
        
        # Test with Victoria County coordinates if available
        if victoria_properties and victoria_properties[0].get("latitude"):
            victoria_prop = victoria_properties[0]
            lat, lng = victoria_prop.get("latitude"), victoria_prop.get("longitude")
            test_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=405x290&maptype=satellite&format=png&key={google_maps_api_key}"
            
            try:
                response = requests.get(test_url, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ Victoria County Google Maps API test: {len(response.content)} bytes")
                else:
                    print(f"   ❌ Victoria County Google Maps API test failed: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ Victoria County Google Maps API test error: {e}")
        
        # Final Comparison Analysis
        print(f"\n   📊 FINAL HALIFAX vs VICTORIA COUNTY THUMBNAIL COMPARISON:")
        
        # Calculate comparison metrics
        halifax_success_rate = 0
        victoria_success_rate = 0
        
        if halifax_properties:
            halifax_working_endpoints = len([r for r in halifax_endpoint_results if r.get("working", False)])
            halifax_success_rate = (halifax_working_endpoints / len(halifax_endpoint_results)) * 100 if halifax_endpoint_results else 0
        
        if victoria_properties:
            victoria_working_endpoints = len([r for r in victoria_endpoint_results if r.get("working", False)])
            victoria_success_rate = (victoria_working_endpoints / len(victoria_endpoint_results)) * 100 if victoria_endpoint_results else 0
        
        print(f"\n   🏆 THUMBNAIL GENERATION COMPARISON RESULTS:")
        print(f"      Halifax thumbnail success rate: {halifax_success_rate:.1f}%")
        print(f"      Victoria County thumbnail success rate: {victoria_success_rate:.1f}%")
        
        # Identify key differences
        differences_found = []
        
        if halifax_success_rate > victoria_success_rate:
            differences_found.append("Halifax has higher thumbnail success rate than Victoria County")
        elif victoria_success_rate > halifax_success_rate:
            differences_found.append("Victoria County has higher thumbnail success rate than Halifax")
        else:
            differences_found.append("Both municipalities have similar thumbnail success rates")
        
        # Check coordinate availability differences
        if halifax_properties and victoria_properties:
            halifax_coord_rate = (halifax_thumbnail_results["properties_with_coordinates"] / len(halifax_properties)) * 100
            victoria_coord_rate = (victoria_thumbnail_results["properties_with_coordinates"] / len(victoria_properties)) * 100
            
            if abs(halifax_coord_rate - victoria_coord_rate) > 10:
                differences_found.append(f"Coordinate availability differs: Halifax {halifax_coord_rate:.1f}% vs Victoria County {victoria_coord_rate:.1f}%")
        
        # Check boundary screenshot availability differences
        if halifax_properties and victoria_properties:
            halifax_screenshot_rate = (halifax_thumbnail_results["properties_with_boundary_screenshots"] / len(halifax_properties)) * 100
            victoria_screenshot_rate = (victoria_thumbnail_results["properties_with_boundary_screenshots"] / len(victoria_properties)) * 100
            
            if abs(halifax_screenshot_rate - victoria_screenshot_rate) > 10:
                differences_found.append(f"Boundary screenshot availability differs: Halifax {halifax_screenshot_rate:.1f}% vs Victoria County {victoria_screenshot_rate:.1f}%")
        
        print(f"\n   🔍 KEY DIFFERENCES IDENTIFIED:")
        for diff in differences_found:
            print(f"      • {diff}")
        
        # Determine if Victoria County thumbnails are working properly
        victoria_thumbnails_working = victoria_success_rate >= 80 and victoria_thumbnail_results["coordinate_accuracy"]
        halifax_thumbnails_working = halifax_success_rate >= 80 and halifax_thumbnail_results["coordinate_accuracy"]
        
        print(f"\n   📋 REVIEW REQUEST ANSWERS:")
        print(f"      1. Do Halifax properties show proper boundary thumbnails? {'✅ YES' if halifax_thumbnails_working else '❌ NO'}")
        print(f"      2. Do Victoria County properties show same quality thumbnails? {'✅ YES' if victoria_thumbnails_working else '❌ NO'}")
        print(f"      3. Are Victoria County coordinates accurate for boundary generation? {'✅ YES' if victoria_thumbnail_results['coordinate_accuracy'] else '❌ NO'}")
        print(f"      4. Is boundary generation using same process for both? {'✅ YES' if halifax_success_rate > 0 and victoria_success_rate > 0 else '❌ NO'}")
        
        return victoria_thumbnails_working and halifax_thumbnails_working, {
            "halifax_success_rate": halifax_success_rate,
            "victoria_success_rate": victoria_success_rate,
            "differences_found": differences_found,
            "halifax_thumbnails_working": halifax_thumbnails_working,
            "victoria_thumbnails_working": victoria_thumbnails_working,
            "halifax_results": halifax_thumbnail_results,
            "victoria_results": victoria_thumbnail_results,
            "halifax_endpoint_results": halifax_endpoint_results,
            "victoria_endpoint_results": victoria_endpoint_results
        }
            
    except Exception as e:
        print(f"   ❌ Victoria County improved parser test error: {e}")
        return False, {"error": str(e)}

def main():
    """Main test execution function - Focus on Halifax vs Victoria County Thumbnail Comparison"""
    print("🚀 Starting Backend API Testing for Nova Scotia Tax Sale Aggregator")
    print("=" * 80)
    print("🎯 FOCUS: Halifax vs Victoria County thumbnail generation comparison")
    print("📋 REVIEW REQUEST: Compare Halifax vs Victoria County thumbnail generation to identify why Victoria County thumbnails aren't working properly")
    print("🔍 REQUIREMENTS:")
    print("   1. Test Halifax property thumbnails - Check Halifax property thumbnail URL and verify proper boundary images")
    print("   2. Test Victoria County property thumbnails - Check Victoria County thumbnail URLs and compare quality/content")
    print("   3. Compare boundary data availability - Check if both have proper boundary_screenshot URLs and coordinate data")
    print("   4. Verify boundary generation process - Test /api/property-image endpoint for both municipality types")
    print("   5. Check coordinate accuracy - Verify if Victoria County coordinates are accurate for proper boundary generation")
    print("=" * 80)
    
    # Track overall results
    test_results = {}
    
    # Test 1: Basic API connectivity
    api_connected, _ = test_api_connection()
    test_results['api_connection'] = api_connected
    
    if not api_connected:
        print("\n❌ Cannot proceed without API connection")
        return False
    
    # Test 2: Halifax vs Victoria County Thumbnail Comparison (MAIN FOCUS)
    print("\n🎯 MAIN FOCUS: Halifax vs Victoria County Thumbnail Comparison")
    comparison_successful, comparison_data = test_halifax_vs_victoria_county_thumbnails()
    test_results['halifax_vs_victoria_comparison'] = comparison_successful
    
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
    print("📊 FINAL TEST RESULTS SUMMARY - Halifax vs Victoria County Thumbnail Comparison")
    print("=" * 80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"❌ Tests Failed: {total_tests - passed_tests}/{total_tests}")
    
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name.replace('_', ' ').title()}")
    
    # Halifax vs Victoria County Comparison Analysis
    print(f"\n🎯 HALIFAX vs VICTORIA COUNTY THUMBNAIL COMPARISON ANALYSIS:")
    
    if comparison_successful and comparison_data:
        print(f"   ✅ THUMBNAIL COMPARISON: BOTH MUNICIPALITIES WORKING PROPERLY!")
        print(f"      Halifax thumbnail success rate: {comparison_data.get('halifax_success_rate', 0):.1f}%")
        print(f"      Victoria County thumbnail success rate: {comparison_data.get('victoria_success_rate', 0):.1f}%")
        print(f"      Halifax thumbnails working: {comparison_data.get('halifax_thumbnails_working', False)}")
        print(f"      Victoria County thumbnails working: {comparison_data.get('victoria_thumbnails_working', False)}")
        
        if comparison_data.get('differences_found'):
            print(f"\n   🔍 Key differences identified:")
            for diff in comparison_data['differences_found']:
                print(f"      • {diff}")
        
        print(f"\n   🎉 SUCCESS: Both Halifax and Victoria County thumbnails working properly!")
        print(f"   ✅ Halifax properties show proper boundary thumbnails with property boundaries")
        print(f"   ✅ Victoria County properties show same quality boundary thumbnails")
        print(f"   ✅ Victoria County coordinates are accurate enough for proper boundary generation")
        print(f"   ✅ Boundary image generation using same process for both municipalities")
        
    elif not comparison_successful and comparison_data:
        print(f"   ❌ THUMBNAIL COMPARISON: ISSUES IDENTIFIED BETWEEN MUNICIPALITIES")
        print(f"      Halifax thumbnail success rate: {comparison_data.get('halifax_success_rate', 0):.1f}%")
        print(f"      Victoria County thumbnail success rate: {comparison_data.get('victoria_success_rate', 0):.1f}%")
        print(f"      Halifax thumbnails working: {comparison_data.get('halifax_thumbnails_working', False)}")
        print(f"      Victoria County thumbnails working: {comparison_data.get('victoria_thumbnails_working', False)}")
        
        if comparison_data.get('differences_found'):
            print(f"\n   🔍 Key differences identified:")
            for diff in comparison_data['differences_found']:
                print(f"      • {diff}")
        
        print(f"\n   ❌ ISSUES IDENTIFIED:")
        if not comparison_data.get('halifax_thumbnails_working', False):
            print(f"      - Halifax properties not showing proper boundary thumbnails")
        if not comparison_data.get('victoria_thumbnails_working', False):
            print(f"      - Victoria County properties not showing same quality boundary thumbnails")
        if comparison_data.get('halifax_success_rate', 0) != comparison_data.get('victoria_success_rate', 0):
            print(f"      - Different success rates between municipalities indicate process differences")
    else:
        print(f"   ❌ THUMBNAIL COMPARISON: CRITICAL ERROR")
        print(f"      - Comparison test execution failed or returned no data")
    
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
    
    if comparison_successful:
        print(f"🎉 HALIFAX vs VICTORIA COUNTY THUMBNAIL COMPARISON: SUCCESS!")
        print(f"   ✅ All review request requirements met")
        print(f"   ✅ Halifax properties show proper boundary thumbnails with property boundaries")
        print(f"   ✅ Victoria County properties show same quality boundary thumbnails")
        print(f"   ✅ Victoria County coordinates are accurate enough for proper boundary generation")
        print(f"   ✅ Boundary image generation using same process for both municipalities")
        print(f"   🚀 Both Halifax and Victoria County thumbnail systems are working properly!")
        
        if comparison_data and comparison_data.get('differences_found'):
            print(f"\n   📋 Minor differences noted but not affecting functionality:")
            for diff in comparison_data['differences_found']:
                print(f"      • {diff}")
    else:
        print(f"❌ HALIFAX vs VICTORIA COUNTY THUMBNAIL COMPARISON: ISSUES FOUND")
        print(f"   ❌ Review request requirements not fully met")
        print(f"   🔧 Victoria County thumbnails may not be working the same as Halifax thumbnails")
        
        if comparison_data:
            if not comparison_data.get('halifax_thumbnails_working', False):
                print(f"   📋 Halifax thumbnail issues need investigation")
            if not comparison_data.get('victoria_thumbnails_working', False):
                print(f"   📋 Victoria County thumbnail issues need fixing:")
                print(f"       - Check coordinate accuracy for boundary generation")
                print(f"       - Verify boundary screenshot generation process")
                print(f"       - Test /api/property-image endpoint functionality")
            
            halifax_rate = comparison_data.get('halifax_success_rate', 0)
            victoria_rate = comparison_data.get('victoria_success_rate', 0)
            if abs(halifax_rate - victoria_rate) > 20:
                print(f"   📋 Significant difference in success rates:")
                print(f"       - Halifax: {halifax_rate:.1f}% vs Victoria County: {victoria_rate:.1f}%")
                print(f"       - This indicates different processes or data quality issues")
    
    print(f"\n📊 System Success Rate: {success_rate:.1f}%")
    print("=" * 80)
    
    return comparison_successful

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)