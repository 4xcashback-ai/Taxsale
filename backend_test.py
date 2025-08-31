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
        
        # Test 2: Retrieve Victoria County Properties and Verify Data
        print(f"\n   🔧 TEST 2: Retrieve Victoria County Properties and Verify Complete Data")
        
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
            
            print(f"   ✅ Found all 3 expected Victoria County properties")
            
        else:
            print(f"   ❌ Failed to retrieve properties: HTTP {response.status_code}")
            return False, {"error": f"Failed to retrieve properties: HTTP {response.status_code}"}
        # Test 3: Verify Correct Minimum Bid Amounts from PDF Extraction
        print(f"\n   🔧 TEST 3: Verify Correct Minimum Bid Amounts from PDF Extraction")
        
        expected_bids = {
            "00254118": 2009.03,  # Entry 1
            "00453706": 1599.71,  # Entry 2  
            "09541209": 5031.96   # Entry 8
        }
        
        bid_verification_results = {
            "correct_bids": 0,
            "incorrect_bids": 0,
            "bid_details": []
        }
        
        print(f"   📊 Verifying minimum bid amounts for all 3 properties...")
        
        for i, prop in enumerate(victoria_properties):
            aan = prop.get("assessment_number")
            opening_bid = prop.get("opening_bid")
            owner = prop.get("owner_name")
            
            print(f"\n   📋 Property {i+1} - AAN {aan}:")
            print(f"      Owner: {owner}")
            print(f"      Opening Bid: ${opening_bid}")
            
            if aan in expected_bids:
                expected_bid = expected_bids[aan]
                print(f"      Expected Bid: ${expected_bid}")
                
                # Check if bid is correct (allow small floating point differences)
                if abs(opening_bid - expected_bid) < 0.01:
                    print(f"      ✅ Opening bid is CORRECT: ${opening_bid}")
                    bid_verification_results["correct_bids"] += 1
                else:
                    print(f"      ❌ Opening bid is INCORRECT: Got ${opening_bid}, expected ${expected_bid}")
                    bid_verification_results["incorrect_bids"] += 1
                
                bid_verification_results["bid_details"].append({
                    "aan": aan,
                    "actual_bid": opening_bid,
                    "expected_bid": expected_bid,
                    "correct": abs(opening_bid - expected_bid) < 0.01
                })
            else:
                print(f"      ⚠️ Unexpected AAN {aan} - not in expected list")
                bid_verification_results["incorrect_bids"] += 1
        
        print(f"\n   📊 Bid Verification Summary:")
        print(f"      Correct bids: {bid_verification_results['correct_bids']}/3")
        print(f"      Incorrect bids: {bid_verification_results['incorrect_bids']}/3")
        
        if bid_verification_results["correct_bids"] != 3:
            print(f"   ❌ CRITICAL: Not all minimum bid amounts are correct!")
            return False, {"error": "Minimum bid amounts are incorrect", "details": bid_verification_results}
        # Test 4: Check HST Detection for Entry 8
        print(f"\n   🔧 TEST 4: Check HST Detection for Entry 8 (AAN 09541209)")
        
        hst_verification_results = {
            "entry_8_found": False,
            "hst_correct": False,
            "hst_value": None
        }
        
        # Find Entry 8 (AAN 09541209)
        entry_8 = None
        for prop in victoria_properties:
            if prop.get("assessment_number") == "09541209":
                entry_8 = prop
                hst_verification_results["entry_8_found"] = True
                break
        
        if entry_8:
            hst_applicable = entry_8.get("hst_applicable")
            hst_verification_results["hst_value"] = hst_applicable
            
            print(f"   📋 Entry 8 (AAN 09541209) found:")
            print(f"      Owner: {entry_8.get('owner_name')}")
            print(f"      HST Applicable: {hst_applicable}")
            print(f"      Expected HST: 'Yes'")
            
            if hst_applicable and hst_applicable.lower() == "yes":
                print(f"      ✅ HST detection is CORRECT: {hst_applicable}")
                hst_verification_results["hst_correct"] = True
            else:
                print(f"      ❌ HST detection is INCORRECT: Got '{hst_applicable}', expected 'Yes'")
                hst_verification_results["hst_correct"] = False
        else:
            print(f"   ❌ Entry 8 (AAN 09541209) not found in Victoria County properties")
            return False, {"error": "Entry 8 (AAN 09541209) not found"}
        
        if not hst_verification_results["hst_correct"]:
            print(f"   ❌ CRITICAL: HST detection for Entry 8 is incorrect!")
            return False, {"error": "HST detection incorrect for Entry 8", "details": hst_verification_results}
        
        # Test 5: Test Boundary Images - Confirm Boundary Screenshot URLs are Working
        print(f"\n   🔧 TEST 5: Test Boundary Images - Confirm Boundary Screenshot URLs are Working")
        
        boundary_image_results = {
            "properties_with_coordinates": 0,
            "properties_with_boundary_urls": 0,
            "working_boundary_endpoints": 0,
            "boundary_image_sizes": [],
            "boundary_details": []
        }
        
        print(f"   📊 Testing boundary images for all 3 Victoria County properties...")
        
        for i, prop in enumerate(victoria_properties):
            aan = prop.get("assessment_number")
            owner = prop.get("owner_name")
            latitude = prop.get("latitude")
            longitude = prop.get("longitude")
            boundary_screenshot = prop.get("boundary_screenshot")
            
            print(f"\n   📋 Property {i+1} - AAN {aan}:")
            print(f"      Owner: {owner}")
            print(f"      Coordinates: {latitude}, {longitude}")
            print(f"      Boundary Screenshot: {boundary_screenshot}")
            
            # Check coordinates
            if latitude and longitude:
                boundary_image_results["properties_with_coordinates"] += 1
                print(f"      ✅ Has coordinates for boundary generation")
                
                # Verify coordinates are in Cape Breton region
                if 45.5 <= latitude <= 47.0 and -61.5 <= longitude <= -59.5:
                    print(f"      ✅ Coordinates within Cape Breton region")
                else:
                    print(f"      ⚠️ Coordinates outside expected Cape Breton region")
            else:
                print(f"      ❌ Missing coordinates - cannot generate boundary images")
            
            # Check boundary screenshot URL
            if boundary_screenshot:
                boundary_image_results["properties_with_boundary_urls"] += 1
                print(f"      ✅ Has boundary screenshot URL")
            else:
                print(f"      ❌ No boundary screenshot URL")
            
            # Test property image endpoint
            if aan:
                try:
                    image_response = requests.get(f"{BACKEND_URL}/property-image/{aan}", timeout=10)
                    if image_response.status_code == 200:
                        image_size = len(image_response.content)
                        content_type = image_response.headers.get('content-type', 'unknown')
                        boundary_image_results["working_boundary_endpoints"] += 1
                        boundary_image_results["boundary_image_sizes"].append(image_size)
                        print(f"      ✅ Boundary image endpoint working - Size: {image_size} bytes")
                        print(f"      📷 Content-Type: {content_type}")
                        
                        # Verify it's a valid image
                        if 'image' in content_type and image_size > 1000:
                            print(f"      ✅ Valid boundary image confirmed")
                        else:
                            print(f"      ⚠️ Image may be invalid or too small")
                    else:
                        print(f"      ❌ Boundary image endpoint failed - HTTP {image_response.status_code}")
                except Exception as e:
                    print(f"      ❌ Boundary image endpoint error: {e}")
            
            boundary_image_results["boundary_details"].append({
                "aan": aan,
                "has_coordinates": bool(latitude and longitude),
                "has_boundary_url": bool(boundary_screenshot),
                "image_endpoint_working": False  # Will be updated above
            })
        
        print(f"\n   📊 Boundary Image Summary:")
        print(f"      Properties with coordinates: {boundary_image_results['properties_with_coordinates']}/3")
        print(f"      Properties with boundary URLs: {boundary_image_results['properties_with_boundary_urls']}/3")
        print(f"      Working boundary endpoints: {boundary_image_results['working_boundary_endpoints']}/3")
        
        if boundary_image_results["boundary_image_sizes"]:
            avg_size = sum(boundary_image_results["boundary_image_sizes"]) / len(boundary_image_results["boundary_image_sizes"])
            print(f"      Average boundary image size: {avg_size:.0f} bytes")
        
        if boundary_image_results["working_boundary_endpoints"] != 3:
            print(f"   ❌ CRITICAL: Not all boundary images are working!")
            return False, {"error": "Boundary images not working for all properties", "details": boundary_image_results}
        
        # Test 6: Verify All Properties Have Complete and Accurate Data
        print(f"\n   🔧 TEST 6: Verify All Properties Have Complete and Accurate Data")
        
        data_completeness_results = {
            "properties_with_complete_data": 0,
            "missing_data_issues": [],
            "data_accuracy_issues": []
        }
        
        required_fields = ["assessment_number", "owner_name", "property_address", "opening_bid", 
                          "municipality_name", "sale_date", "latitude", "longitude"]
        
        print(f"   📊 Checking data completeness for all 3 properties...")
        
        for i, prop in enumerate(victoria_properties):
            aan = prop.get("assessment_number")
            print(f"\n   📋 Property {i+1} - AAN {aan}:")
            
            missing_fields = []
            for field in required_fields:
                value = prop.get(field)
                if value is None or value == "":
                    missing_fields.append(field)
                    print(f"      ❌ Missing {field}")
                else:
                    print(f"      ✅ Has {field}: {value}")
            
            if not missing_fields:
                data_completeness_results["properties_with_complete_data"] += 1
                print(f"      ✅ Property has complete data")
            else:
                data_completeness_results["missing_data_issues"].append({
                    "aan": aan,
                    "missing_fields": missing_fields
                })
                print(f"      ❌ Property missing {len(missing_fields)} fields")
        
        print(f"\n   📊 Data Completeness Summary:")
        print(f"      Properties with complete data: {data_completeness_results['properties_with_complete_data']}/3")
        
        if data_completeness_results["properties_with_complete_data"] != 3:
            print(f"   ❌ CRITICAL: Not all properties have complete data!")
            return False, {"error": "Properties missing required data", "details": data_completeness_results}
        
        # Final Success Verification
        print(f"\n   🎉 FINAL VERIFICATION: All Victoria County Scraper Requirements Met!")
        
        all_tests_passed = (
            bid_verification_results["correct_bids"] == 3 and
            hst_verification_results["hst_correct"] and
            boundary_image_results["working_boundary_endpoints"] == 3 and
            data_completeness_results["properties_with_complete_data"] == 3
        )
        
        print(f"\n   📋 REVIEW REQUEST REQUIREMENTS STATUS:")
        print(f"      1. ✅ Victoria County scraper executed successfully")
        print(f"      2. {'✅' if bid_verification_results['correct_bids'] == 3 else '❌'} Correct minimum bid amounts from PDF extraction:")
        for detail in bid_verification_results["bid_details"]:
            status = "✅" if detail["correct"] else "❌"
            print(f"         {status} AAN {detail['aan']}: ${detail['actual_bid']} (expected ${detail['expected_bid']})")
        print(f"      3. {'✅' if hst_verification_results['hst_correct'] else '❌'} HST detection for Entry 8: {hst_verification_results['hst_value']}")
        print(f"      4. ✅ All 3 properties found with complete accurate data")
        print(f"      5. {'✅' if boundary_image_results['working_boundary_endpoints'] == 3 else '❌'} Boundary images working: {boundary_image_results['working_boundary_endpoints']}/3")
        
        return all_tests_passed, {
            "scraper_executed": True,
            "bid_verification": bid_verification_results,
            "hst_verification": hst_verification_results,
            "boundary_images": boundary_image_results,
            "data_completeness": data_completeness_results,
            "all_requirements_met": all_tests_passed
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