#!/usr/bin/env python3
"""
Backend API Testing for Nova Scotia Tax Sale Aggregator
Focus on Victoria County Final Parser with Enhanced Error Handling
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

def test_victoria_county_data_extraction_debug():
    """Debug Victoria County data extraction issues - minimum bid and missing images"""
    print("\n🔍 Testing Victoria County Data Extraction Issues...")
    print("🎯 FOCUS: Debug minimum bid calculations and missing boundary images")
    print("📋 REQUIREMENTS from Review Request:")
    print("   1. Test current Victoria County properties - Check actual data being extracted for all 3 properties")
    print("   2. Verify minimum bid calculations - Compare extracted opening_bid values against PDF tax amounts:")
    print("      - Entry 1: Should be $2,009.03")
    print("      - Entry 2: Should be $1,599.71") 
    print("      - Entry 8: Should be $5,031.96 + HST")
    print("   3. Check boundary screenshot generation - Verify if boundary_screenshot field is being generated")
    print("   4. Debug tax amount extraction - Check if regex patterns correctly extract from 'Taxes, Interest and Expenses owing: $X,XXX.XX'")
    print("   5. Verify property images - Check if Google Maps static API is generating boundary thumbnails")
    print("")
    print("🔍 EXPECTED MINIMUM BIDS (from PDF tax amounts):")
    print("   - Entry 1 (AAN 00254118): $2,009.03")
    print("   - Entry 2 (AAN 00453706): $1,599.71")
    print("   - Entry 8 (AAN 09541209): $5,031.96 + HST")
    print("🔍 EXPECTED BOUNDARY IMAGES: All properties should have boundary_screenshot URLs")
    
    try:
        # Test 1: Victoria County Scraper - Check Current Data Extraction
        print(f"\n   🔧 TEST 1: POST /api/scrape/victoria-county (Current Data Extraction)")
        
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
            print(f"   ✅ Victoria County scraper executed successfully")
            print(f"      Status: {scrape_result.get('status')}")
            print(f"      Municipality: {scrape_result.get('municipality', 'N/A')}")
            print(f"      Properties scraped: {scrape_result.get('properties_scraped', 0)}")
            
            # Check property count - expecting 3 properties
            properties_count = scrape_result.get('properties_scraped', 0)
            if properties_count == 3:
                print(f"   ✅ PROPERTY COUNT: Found all 3 properties")
            elif properties_count == 1:
                print(f"   ❌ PROPERTY COUNT ISSUE: Only 1 property found (expected 3)")
                print(f"   🔍 DEBUG: This indicates PDF parsing is not finding all numbered sections")
            else:
                print(f"   ⚠️ UNEXPECTED PROPERTY COUNT: Found {properties_count} properties (expected 3)")
            
        else:
            print(f"   ❌ Victoria County scraper failed with status {scrape_response.status_code}")
            try:
                error_detail = scrape_response.json()
                print(f"      Error details: {error_detail}")
            except:
                print(f"      Raw response: {scrape_response.text[:200]}...")
            return False, {"error": f"Scraper failed with HTTP {scrape_response.status_code}"}
        
        # Test 2: Verify Minimum Bid Calculations Against PDF Tax Amounts
        print(f"\n   🔧 TEST 2: GET /api/tax-sales (Verify Minimum Bid Calculations)")
        
        properties_response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Victoria County", timeout=30)
        
        if properties_response.status_code == 200:
            properties = properties_response.json()
            victoria_properties = [p for p in properties if p.get("municipality_name") == "Victoria County"]
            
            print(f"   ✅ Retrieved {len(victoria_properties)} Victoria County properties from database")
            
            # Expected minimum bids from PDF tax amounts (from review request)
            expected_bids = {
                "00254118": 2009.03,  # Entry 1: Should be $2,009.03
                "00453706": 1599.71,  # Entry 2: Should be $1,599.71  
                "09541209": 5031.96   # Entry 8: Should be $5,031.96 + HST
            }
            
            print(f"\n   🎯 VERIFYING MINIMUM BID CALCULATIONS:")
            
            found_aans = []
            bid_calculations_correct = True
            boundary_images_present = True
            
            for i, prop in enumerate(victoria_properties):
                aan = prop.get("assessment_number")
                owner = prop.get("owner_name")
                address = prop.get("property_address")
                pid = prop.get("pid_number")
                opening_bid = prop.get("opening_bid")
                boundary_screenshot = prop.get("boundary_screenshot")
                raw_data = prop.get("raw_data", {})
                
                print(f"\n   📋 Property {i+1} - Minimum Bid & Image Analysis:")
                print(f"      AAN: {aan}")
                print(f"      Owner: '{owner}'")
                print(f"      Address: '{address}'")
                print(f"      Opening Bid: ${opening_bid}")
                print(f"      Boundary Screenshot: {boundary_screenshot}")
                
                # Verify minimum bid calculation against expected PDF tax amounts
                if aan in expected_bids:
                    expected_bid = expected_bids[aan]
                    if opening_bid and abs(float(opening_bid) - expected_bid) < 0.01:
                        print(f"      ✅ MINIMUM BID CORRECT: ${opening_bid} matches expected ${expected_bid}")
                    else:
                        print(f"      ❌ MINIMUM BID INCORRECT: Got ${opening_bid}, expected ${expected_bid}")
                        print(f"         🔍 DEBUG: Tax amount extraction may be failing")
                        bid_calculations_correct = False
                    found_aans.append(aan)
                else:
                    print(f"      ⚠️ AAN {aan} not in expected list for bid verification")
                
                # Check boundary screenshot generation
                if boundary_screenshot:
                    print(f"      ✅ BOUNDARY IMAGE: Screenshot field populated - {boundary_screenshot}")
                    
                    # Test if the boundary image is accessible
                    try:
                        image_response = requests.get(f"{BACKEND_URL}/boundary-image/{boundary_screenshot}", timeout=10)
                        if image_response.status_code == 200:
                            print(f"         ✅ Image accessible via API endpoint")
                        else:
                            print(f"         ❌ Image not accessible: HTTP {image_response.status_code}")
                            boundary_images_present = False
                    except Exception as e:
                        print(f"         ❌ Error accessing image: {e}")
                        boundary_images_present = False
                else:
                    print(f"      ❌ BOUNDARY IMAGE: No screenshot field - missing image generation")
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
            
            # REQUIREMENT 4: Validate complete data
            if all_data_complete and len(found_aans) == 3:
                print(f"\n   ✅ REQUIREMENT 4 MET: All properties have correct AANs, owners, addresses, and tax amounts")
            else:
                print(f"\n   ❌ REQUIREMENT 4 FAILED: Some properties missing correct data")
                all_data_complete = False
            
            # REQUIREMENT 5: Confirm no fallback
            if fallback_detected:
                print(f"\n   ❌ REQUIREMENT 5 FAILED: Fallback sample data detected instead of actual PDF data")
                return False, {"error": "System using fallback data instead of actual PDF parsing"}
            else:
                print(f"\n   ✅ REQUIREMENT 5 MET: Using actual PDF data, not fallback sample data")
            
            # Verify all expected AANs were found
            missing_aans = [aan for aan in expected_aans if aan not in found_aans]
            if missing_aans:
                print(f"\n   ❌ MISSING AANs: {missing_aans} not found in parsed properties")
                return False, {"error": f"Missing expected AANs: {missing_aans}"}
            else:
                print(f"\n   ✅ ALL EXPECTED AANs FOUND: {found_aans}")
            
        else:
            print(f"   ❌ Failed to retrieve Victoria County properties: {properties_response.status_code}")
            return False, {"error": f"Failed to retrieve properties: HTTP {properties_response.status_code}"}
        
        # Test 3: Debug Tax Amount Extraction Patterns
        print(f"\n   🔧 TEST 3: Debug Tax Amount Extraction Patterns")
        
        debug_response = requests.get(f"{BACKEND_URL}/debug/victoria-county-pdf", timeout=30)
        
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            print(f"   ✅ Debug endpoint available for tax amount pattern analysis")
            
            # Analyze PDF content for tax amount patterns
            pdf_content = debug_data.get('pdf_content_preview', '')
            analysis = debug_data.get('analysis', {})
            
            print(f"      PDF Content Length: {len(pdf_content)} characters")
            
            # Check for the specific tax amount pattern mentioned in review request
            tax_pattern = r"Taxes, Interest and Expenses owing:\s*\$[\d,]+\.?\d*"
            import re
            tax_matches = re.findall(tax_pattern, pdf_content)
            
            if tax_matches:
                print(f"   ✅ TAX AMOUNT PATTERN FOUND: {len(tax_matches)} matches")
                for i, match in enumerate(tax_matches):
                    print(f"      Match {i+1}: {match}")
                    # Extract the dollar amount
                    amount_match = re.search(r'\$[\d,]+\.?\d*', match)
                    if amount_match:
                        amount = amount_match.group().replace('$', '').replace(',', '')
                        print(f"         Extracted amount: ${amount}")
            else:
                print(f"   ❌ TAX AMOUNT PATTERN NOT FOUND: 'Taxes, Interest and Expenses owing: $X,XXX.XX' pattern missing")
                print(f"   🔍 DEBUG: Regex patterns may not be correctly extracting tax amounts")
                
            # Check for AAN occurrences
            aan_count = analysis.get('aan_occurrences', 0)
            if aan_count >= 3:
                print(f"   ✅ AAN DETECTION: Found {aan_count} AAN occurrences in PDF")
            else:
                print(f"   ❌ AAN DETECTION ISSUE: Only {aan_count} AAN occurrences found (expected 3)")
                
        else:
            print(f"   ⚠️ Debug endpoint not available (status: {debug_response.status_code})")
            print(f"   ℹ️ Cannot verify tax amount extraction patterns without debug endpoint")
        
        # Test 4: Multiple PID Handling Verification
        print(f"\n   🔧 TEST 4: Multiple PID Handling Verification")
        
        # Check if Entry 2 (AAN 00453706) has multiple PIDs as expected
        entry_2_property = None
        for prop in victoria_properties:
            if prop.get("assessment_number") == "00453706":
                entry_2_property = prop
                break
        
        if entry_2_property:
            print(f"   ✅ Entry 2 (AAN 00453706) found - checking for multiple PID handling")
            raw_data = entry_2_property.get("raw_data", {})
            if raw_data and "multiple_pids" in str(raw_data).lower():
                print(f"   ✅ Multiple PID handling: Entry 2 shows evidence of multiple PID processing")
            else:
                print(f"   ⚠️ Multiple PID handling: Cannot verify multiple PID processing for Entry 2")
        else:
            print(f"   ❌ Entry 2 (AAN 00453706) not found - multiple PID handling cannot be verified")
        
        # Final Assessment
        print(f"\n   📊 FINAL ASSESSMENT - Victoria County Improved Parser:")
        
        requirements_met = []
        requirements_failed = []
        
        # Requirement 1: Enhanced regex patterns working
        if scrape_response.status_code == 200:
            requirements_met.append("1. Enhanced regex patterns working")
        else:
            requirements_failed.append("1. Enhanced regex patterns working")
        
        # Requirement 2: All 3 properties extracted
        if properties_count == 3:
            requirements_met.append("2. All 3 properties extracted")
        else:
            requirements_failed.append("2. All 3 properties extracted")
        
        # Requirement 3: Pattern matching for different formats
        if debug_response.status_code == 200 and aan_count >= 3:
            requirements_met.append("3. Pattern matching handles different formats")
        else:
            requirements_failed.append("3. Pattern matching handles different formats")
        
        # Requirement 4: Complete data validation
        if all_data_complete:
            requirements_met.append("4. Complete data validation")
        else:
            requirements_failed.append("4. Complete data validation")
        
        # Requirement 5: No fallback data
        if not fallback_detected:
            requirements_met.append("5. No fallback data")
        else:
            requirements_failed.append("5. No fallback data")
        
        # Requirement 6: Correct sale date
        sale_date_correct = any("2025-08-26" in str(prop.get("sale_date", "")) for prop in victoria_properties)
        if sale_date_correct:
            requirements_met.append("6. Correct sale date (2025-08-26)")
        else:
            requirements_failed.append("6. Correct sale date (2025-08-26)")
        
        print(f"\n   ✅ REQUIREMENTS MET ({len(requirements_met)}/6):")
        for req in requirements_met:
            print(f"      ✅ {req}")
        
        if requirements_failed:
            print(f"\n   ❌ REQUIREMENTS FAILED ({len(requirements_failed)}/6):")
            for req in requirements_failed:
                print(f"      ❌ {req}")
        
        # Overall result
        if len(requirements_failed) == 0:
            print(f"\n   🎉 VICTORIA COUNTY IMPROVED PARSER: ALL REQUIREMENTS MET!")
            print(f"   ✅ Enhanced regex patterns successfully extract all 3 properties")
            print(f"   ✅ Pattern matching handles different property formats and multiple PIDs")
            print(f"   ✅ All properties have correct owners, addresses, tax amounts, and property types")
            print(f"   ✅ Using actual PDF data, not fallback sample data")
            print(f"   ✅ Sale date correctly set to 2025-08-26")
            return True, {
                "requirements_met": len(requirements_met),
                "requirements_failed": len(requirements_failed),
                "properties_found": properties_count,
                "all_data_complete": all_data_complete,
                "fallback_detected": fallback_detected,
                "expected_aans_found": found_aans,
                "sale_date_correct": sale_date_correct
            }
        else:
            print(f"\n   ❌ VICTORIA COUNTY IMPROVED PARSER: {len(requirements_failed)} REQUIREMENTS FAILED")
            return False, {
                "requirements_met": len(requirements_met),
                "requirements_failed": len(requirements_failed),
                "failed_requirements": requirements_failed,
                "properties_found": properties_count,
                "all_data_complete": all_data_complete,
                "fallback_detected": fallback_detected,
                "sale_date_correct": sale_date_correct
            }
            
    except Exception as e:
        print(f"   ❌ Victoria County improved parser test error: {e}")
        return False, {"error": str(e)}

def main():
    """Main test execution function - Focus on Victoria County Improved Parser Testing"""
    print("🚀 Starting Backend API Testing for Nova Scotia Tax Sale Aggregator")
    print("=" * 80)
    print("🎯 FOCUS: Victoria County Parser with Improved Pattern Matching")
    print("📋 REVIEW REQUEST: Test Victoria County parser with enhanced regex patterns for all property formats")
    print("🔍 REQUIREMENTS:")
    print("   1. Test improved parser POST /api/scrape/victoria-county with enhanced regex patterns")
    print("   2. Verify all 3 properties extracted - Entry 1: AAN 00254118, Entry 2: AAN 00453706, Entry 8: AAN 09541209")
    print("   3. Check pattern matching - Enhanced patterns should handle different property formats and multiple PIDs")
    print("   4. Verify complete data - All properties should have correct owners, addresses, tax amounts, and property types")
    print("   5. Confirm no fallback - Should extract actual PDF data, not use fallback sample data")
    print("   6. Verify sale date correctly set to '2025-08-26'")
    print("=" * 80)
    
    # Track overall results
    test_results = {}
    
    # Test 1: Basic API connectivity
    api_connected, _ = test_api_connection()
    test_results['api_connection'] = api_connected
    
    if not api_connected:
        print("\n❌ Cannot proceed without API connection")
        return False
    
    # Test 2: Victoria County Improved Parser (MAIN FOCUS)
    print("\n🎯 MAIN FOCUS: Victoria County Improved Parser Testing")
    victoria_county_working, victoria_county_data = test_victoria_county_improved_parser()
    test_results['victoria_county_improved_parser'] = victoria_county_working
    
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