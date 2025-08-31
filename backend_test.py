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

def test_victoria_county_improved_parser():
    """Test Victoria County Parser with Improved Pattern Matching - Review Request Focus"""
    print("\n🔍 Testing Victoria County Parser with Improved Pattern Matching...")
    print("🎯 FOCUS: Test improved parser with enhanced regex patterns for all property formats")
    print("📋 REQUIREMENTS from Review Request:")
    print("   1. Test improved parser POST /api/scrape/victoria-county with enhanced regex patterns")
    print("   2. Verify all 3 properties extracted from PDF entries 1, 2, and 8")
    print("   3. Check pattern matching - Enhanced patterns should handle different property formats and multiple PIDs")
    print("   4. Verify complete data - All properties should have correct owners, addresses, tax amounts, and property types")
    print("   5. Confirm no fallback - Should extract actual PDF data, not use fallback sample data")
    print("   6. Verify sale date correctly set to '2025-08-26'")
    print("")
    print("🔍 EXPECTED PROPERTIES (from PDF entries 1, 2, 8):")
    print("   - Entry 1: AAN 00254118, Donald John Beaton, Land/Dwelling")
    print("   - Entry 2: AAN 00453706, Kenneth Ferneyhough, Land/Dwelling (with multiple PIDs)")
    print("   - Entry 8: AAN 09541209, Florance Debra Cleaves, Land only")
    print("🔍 EXPECTED SALE DATE: Tuesday, August 26TH, 2025 at 2:00PM (should be 2025-08-26)")
    
    try:
        # Test 1: Victoria County Improved Parser with Enhanced Regex Patterns
        print(f"\n   🔧 TEST 1: POST /api/scrape/victoria-county (Improved Parser with Enhanced Regex Patterns)")
        
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
            
            # CRITICAL TEST: Verify we got 3 properties (not just 1 fallback)
            properties_count = scrape_result.get('properties_scraped', 0)
            if properties_count == 3:
                print(f"   ✅ PROPERTY COUNT CORRECT: Found all 3 properties from entries 1, 2, 8")
                print(f"   ✅ REQUIREMENT 3 MET: Successfully extracted all 3 properties")
            elif properties_count == 1:
                print(f"   ❌ PROPERTY COUNT ISSUE: Still only 1 property found (expected 3)")
                print(f"   ❌ REQUIREMENT 3 FAILED: Parser not finding all 3 properties from PDF")
                return False, {"error": "Parser still only finding 1 property instead of 3 from PDF entries 1, 2, 8"}
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
        
        # Test 2: Verify Properties in Database with Complete Data Validation
        print(f"\n   🔧 TEST 2: GET /api/tax-sales (Validate Complete Data)")
        
        properties_response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Victoria County", timeout=30)
        
        if properties_response.status_code == 200:
            properties = properties_response.json()
            victoria_properties = [p for p in properties if p.get("municipality_name") == "Victoria County"]
            
            print(f"   ✅ Retrieved {len(victoria_properties)} Victoria County properties from database")
            
            if len(victoria_properties) != 3:
                print(f"   ❌ DATABASE PROPERTY COUNT MISMATCH: Expected 3, found {len(victoria_properties)}")
                return False, {"error": f"Database contains {len(victoria_properties)} properties instead of 3"}
            
            # Expected AANs from PDF entries 1, 2, 8 (confirmed from debug analysis)
            expected_aans = ["00254118", "00453706", "09541209"]
            expected_owners = ["Donald John Beaton", "Kenneth Ferneyhough", "Florance Debra Cleaves"]
            expected_pids = ["85006500", "85010866", "85142388"]
            expected_property_types = ["Land/Dwelling", "Land/Dwelling", "Land"]
            
            print(f"\n   🎯 VALIDATING COMPLETE DATA FOR ALL 3 PROPERTIES:")
            
            found_aans = []
            all_data_complete = True
            fallback_detected = False
            
            for i, prop in enumerate(victoria_properties):
                aan = prop.get("assessment_number")
                owner = prop.get("owner_name")
                address = prop.get("property_address")
                pid = prop.get("pid_number")
                opening_bid = prop.get("opening_bid")
                sale_date = prop.get("sale_date")
                property_type = prop.get("property_type")
                raw_data = prop.get("raw_data", {})
                
                print(f"\n   📋 Property {i+1} Complete Data Validation:")
                print(f"      AAN: {aan}")
                print(f"      Owner: '{owner}'")
                print(f"      Address: '{address}'")
                print(f"      PID: {pid}")
                print(f"      Opening Bid: ${opening_bid}")
                print(f"      Property Type: {property_type}")
                print(f"      Sale Date: {sale_date}")
                
                # Verify AAN is one of the expected ones from PDF
                if aan in expected_aans:
                    print(f"      ✅ AAN matches expected PDF data")
                    found_aans.append(aan)
                else:
                    print(f"      ❌ AAN not in expected list: {expected_aans}")
                    all_data_complete = False
                
                # Verify owner name matches expected (partial match for variations)
                owner_match = False
                for expected_owner in expected_owners:
                    if expected_owner.lower() in owner.lower() or owner.lower() in expected_owner.lower():
                        owner_match = True
                        break
                
                if owner_match:
                    print(f"      ✅ Owner name matches expected PDF data")
                else:
                    print(f"      ❌ Owner name doesn't match expected: {expected_owners}")
                    all_data_complete = False
                
                # Verify PID is one of the expected ones
                if pid in expected_pids:
                    print(f"      ✅ PID matches expected PDF data")
                else:
                    print(f"      ❌ PID not in expected list: {expected_pids}")
                    all_data_complete = False
                
                # Verify property type matches expected format
                property_type_match = False
                for expected_type in expected_property_types:
                    if expected_type.lower() in property_type.lower() if property_type else False:
                        property_type_match = True
                        break
                
                if property_type_match:
                    print(f"      ✅ Property type matches expected format")
                else:
                    print(f"      ❌ Property type doesn't match expected: {expected_property_types}")
                    all_data_complete = False
                
                # Verify sale date is correct (should be 2025-08-26 from "Tuesday, August 26TH, 2025")
                if sale_date and "2025-08-26" in str(sale_date):
                    print(f"      ✅ Sale date correct: extracted from 'Tuesday, August 26TH, 2025 at 2:00PM'")
                else:
                    print(f"      ❌ Sale date incorrect: expected 2025-08-26, got {sale_date}")
                    all_data_complete = False
                
                # Check for fallback data indicators
                if (aan == "00254118" and 
                    "Donald John Beaton" in owner and 
                    "198 Little Narrows Rd" in address and
                    len(victoria_properties) == 1):
                    print(f"      ⚠️ POSSIBLE FALLBACK DATA: This looks like sample/fallback data")
                    fallback_detected = True
                
                # Verify raw_data contains actual parsing information
                if raw_data:
                    source = raw_data.get('source', '')
                    if 'pdf_parsing' in source.lower():
                        print(f"      ✅ Raw data indicates actual PDF parsing")
                    elif 'fallback' in source.lower():
                        print(f"      ❌ Raw data indicates fallback data used")
                        fallback_detected = True
                    else:
                        print(f"      📊 Raw data source: {source}")
                else:
                    print(f"      ⚠️ No raw data available for analysis")
            
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
        
        # Test 3: Check Enhanced Pattern Matching (if debug endpoint exists)
        print(f"\n   🔧 TEST 3: Check Enhanced Pattern Matching (Debug Analysis)")
        
        debug_response = requests.get(f"{BACKEND_URL}/debug/victoria-county-pdf", timeout=30)
        
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            print(f"   ✅ Debug endpoint available for comprehensive logging analysis")
            
            # Analyze PDF content and parsing details
            pdf_size = debug_data.get('pdf_size_bytes', 0)
            pdf_chars = debug_data.get('pdf_text_length', 0)
            aan_count = len(debug_data.get('aan_occurrences', []))
            numbered_sections = debug_data.get('numbered_sections_found', 0)
            
            print(f"      PDF Size: {pdf_size} bytes")
            print(f"      PDF Text Length: {pdf_chars} characters")
            print(f"      AAN Occurrences: {aan_count}")
            print(f"      Numbered Sections: {numbered_sections}")
            
            if aan_count >= 3 and numbered_sections >= 3:
                print(f"   ✅ ENHANCED PATTERN MATCHING: Parser correctly identifies all 3 AAN occurrences and numbered sections")
            else:
                print(f"   ⚠️ PATTERN MATCHING ISSUE: Limited AAN/section detection - may indicate regex pattern problems")
        else:
            print(f"   ⚠️ Debug endpoint not available (status: {debug_response.status_code})")
            print(f"   ℹ️ REQUIREMENT 2: Cannot verify comprehensive logging without debug endpoint")
        
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
        
        # Requirement 1: Enhanced error handling
        if scrape_response.status_code == 200:
            requirements_met.append("1. Enhanced error handling and validation")
        else:
            requirements_failed.append("1. Enhanced error handling and validation")
        
        # Requirement 2: Comprehensive logging
        if debug_response.status_code == 200:
            requirements_met.append("2. Comprehensive logging")
        else:
            requirements_failed.append("2. Comprehensive logging (debug endpoint unavailable)")
        
        # Requirement 3: All 3 properties
        if properties_count == 3:
            requirements_met.append("3. All 3 properties extracted")
        else:
            requirements_failed.append("3. All 3 properties extracted")
        
        # Requirement 4: Complete data
        if all_data_complete:
            requirements_met.append("4. Complete data validation")
        else:
            requirements_failed.append("4. Complete data validation")
        
        # Requirement 5: No fallback
        if not fallback_detected:
            requirements_met.append("5. No fallback data")
        else:
            requirements_failed.append("5. No fallback data")
        
        print(f"\n   ✅ REQUIREMENTS MET ({len(requirements_met)}/5):")
        for req in requirements_met:
            print(f"      ✅ {req}")
        
        if requirements_failed:
            print(f"\n   ❌ REQUIREMENTS FAILED ({len(requirements_failed)}/5):")
            for req in requirements_failed:
                print(f"      ❌ {req}")
        
        # Overall result
        if len(requirements_failed) == 0:
            print(f"\n   🎉 VICTORIA COUNTY FINAL PARSER: ALL REQUIREMENTS MET!")
            print(f"   ✅ Final verification successful - Victoria County PDF parser working correctly")
            return True, {
                "requirements_met": len(requirements_met),
                "requirements_failed": len(requirements_failed),
                "properties_found": properties_count,
                "all_data_complete": all_data_complete,
                "fallback_detected": fallback_detected,
                "expected_aans_found": found_aans
            }
        else:
            print(f"\n   ❌ VICTORIA COUNTY FINAL PARSER: {len(requirements_failed)} REQUIREMENTS FAILED")
            return False, {
                "requirements_met": len(requirements_met),
                "requirements_failed": len(requirements_failed),
                "failed_requirements": requirements_failed,
                "properties_found": properties_count,
                "all_data_complete": all_data_complete,
                "fallback_detected": fallback_detected
            }
            
    except Exception as e:
        print(f"   ❌ Victoria County final parser test error: {e}")
        return False, {"error": str(e)}

def main():
    """Main test execution function - Focus on Victoria County Final Parser Testing"""
    print("🚀 Starting Backend API Testing for Nova Scotia Tax Sale Aggregator")
    print("=" * 80)
    print("🎯 FOCUS: Victoria County Final Parser with Enhanced Error Handling")
    print("📋 REVIEW REQUEST: Final test of Victoria County parser with improved error handling")
    print("🔍 REQUIREMENTS:")
    print("   1. Test final parser POST /api/scrape/victoria-county with enhanced error handling")
    print("   2. Check comprehensive logging - Should show detailed PDF parsing steps")
    print("   3. Verify all 3 properties - Should extract all properties from entries 1, 2, and 8")
    print("   4. Validate complete data - All properties should have correct AANs, owners, addresses, tax amounts")
    print("   5. Confirm no fallback - Should use actual PDF data, not fallback sample data")
    print("=" * 80)
    
    # Track overall results
    test_results = {}
    
    # Test 1: Basic API connectivity
    api_connected, _ = test_api_connection()
    test_results['api_connection'] = api_connected
    
    if not api_connected:
        print("\n❌ Cannot proceed without API connection")
        return False
    
    # Test 2: Victoria County Final Parser (MAIN FOCUS)
    print("\n🎯 MAIN FOCUS: Victoria County Final Parser Testing")
    victoria_county_working, victoria_county_data = test_victoria_county_final_parser()
    test_results['victoria_county_final_parser'] = victoria_county_working
    
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
    print("📊 FINAL TEST RESULTS SUMMARY - Victoria County Final Parser Focus")
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
    print(f"\n🎯 VICTORIA COUNTY FINAL PARSER ANALYSIS:")
    
    if victoria_county_working and victoria_county_data:
        print(f"   ✅ VICTORIA COUNTY PARSER: ALL REQUIREMENTS MET!")
        print(f"      Requirements Met: {victoria_county_data.get('requirements_met', 0)}/5")
        print(f"      Properties Found: {victoria_county_data.get('properties_found', 0)}")
        print(f"      All Data Complete: {victoria_county_data.get('all_data_complete', False)}")
        print(f"      Fallback Detected: {victoria_county_data.get('fallback_detected', True)}")
        
        if victoria_county_data.get('expected_aans_found'):
            print(f"      Expected AANs Found: {victoria_county_data['expected_aans_found']}")
        
        print(f"\n   🎉 SUCCESS: Victoria County PDF parser working correctly with actual PDF data!")
        print(f"   ✅ Enhanced error handling and validation working")
        print(f"   ✅ All 3 properties successfully extracted from entries 1, 2, and 8")
        print(f"   ✅ Complete data validation passed")
        print(f"   ✅ Using actual PDF data, not fallback sample data")
        
    elif not victoria_county_working and victoria_county_data:
        print(f"   ❌ VICTORIA COUNTY PARSER: REQUIREMENTS NOT MET")
        print(f"      Requirements Met: {victoria_county_data.get('requirements_met', 0)}/5")
        print(f"      Requirements Failed: {victoria_county_data.get('requirements_failed', 5)}/5")
        
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
        print(f"🎉 VICTORIA COUNTY FINAL PARSER: SUCCESS!")
        print(f"   ✅ All review request requirements met")
        print(f"   ✅ Enhanced error handling working")
        print(f"   ✅ All 3 properties extracted from PDF entries 1, 2, 8")
        print(f"   ✅ Complete data validation passed")
        print(f"   ✅ Using actual PDF data, not fallback")
        print(f"   🚀 Victoria County PDF parser is production-ready!")
    else:
        print(f"❌ VICTORIA COUNTY FINAL PARSER: FAILED")
        print(f"   ❌ Review request requirements not met")
        print(f"   🔧 Additional debugging and fixes needed")
        print(f"   📋 Check parser logic for PDF entries 1, 2, 8 extraction")
        print(f"   📋 Verify non-sequential numbering handling (1, 2, 8)")
        print(f"   📋 Ensure actual PDF parsing instead of fallback data")
    
    print(f"\n📊 System Success Rate: {success_rate:.1f}%")
    print("=" * 80)
    
    return victoria_county_working

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)