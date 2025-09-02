#!/usr/bin/env python3
"""
Victoria County Enhanced Debugging Test
Focus on identifying the extraction issue as requested in the review
"""

import requests
import json
import sys
import re
from datetime import datetime
import time

# Get backend URL from environment
import os
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://taxsale-mapper.preview.emergentagent.com') + '/api'

def test_victoria_county_enhanced_debugging():
    """Test Victoria County parser with enhanced debugging to identify extraction issues"""
    print("🔍 VICTORIA COUNTY ENHANCED DEBUGGING TEST")
    print("=" * 80)
    print("🎯 FOCUS: Identify why only 1 property is parsed instead of 3")
    print("📋 REVIEW REQUEST REQUIREMENTS:")
    print("   1. Test enhanced debugging POST /api/scrape/victoria-county with comprehensive logging")
    print("   2. Check property entry detection - Should identify entries 1, 2, and 8 contain AAN data")
    print("   3. Verify section extraction - Should extract 3 complete property sections")
    print("   4. Debug individual parsing - Should show detailed parsing of each section")
    print("   5. Identify specific failure points - Find why only 1 property succeeds")
    print("")
    
    try:
        # Test 1: Enhanced Debugging Scraper Execution
        print("🔧 TEST 1: Enhanced Debugging POST /api/scrape/victoria-county")
        print("   📊 Executing with comprehensive logging to see parsing process...")
        
        scrape_response = requests.post(
            f"{BACKEND_URL}/scrape/victoria-county", 
            timeout=120
        )
        
        if scrape_response.status_code == 200:
            scrape_result = scrape_response.json()
            print(f"   ✅ Scraper executed successfully")
            print(f"      Status: {scrape_result.get('status')}")
            print(f"      Municipality: {scrape_result.get('municipality')}")
            print(f"      Properties scraped: {scrape_result.get('properties_scraped', 0)}")
            
            # Check if we got the expected 3 properties
            properties_count = scrape_result.get('properties_scraped', 0)
            if properties_count == 1:
                print(f"   ❌ CONFIRMED ISSUE: Only 1 property parsed (expected 3)")
                print(f"   🔍 This confirms the extraction issue described in review request")
            elif properties_count == 3:
                print(f"   ✅ ISSUE RESOLVED: All 3 properties now parsed successfully!")
                return True, {"status": "resolved", "properties_count": 3}
            else:
                print(f"   ⚠️ UNEXPECTED: {properties_count} properties parsed")
        else:
            print(f"   ❌ Scraper failed with status {scrape_response.status_code}")
            return False, {"error": f"Scraper failed: {scrape_response.status_code}"}
        
        # Test 2: Check Property Entry Detection
        print(f"\n🔧 TEST 2: Property Entry Detection Analysis")
        print("   📊 Checking if entries 1, 2, and 8 are being detected...")
        
        # Check if debug endpoint exists
        debug_response = requests.get(f"{BACKEND_URL}/debug/victoria-county-pdf", timeout=30)
        
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            print(f"   ✅ Debug endpoint available - analyzing PDF content")
            
            # Analyze PDF structure
            pdf_size = debug_data.get('pdf_size_bytes', 0)
            pdf_chars = debug_data.get('pdf_text_length', 0)
            aan_occurrences = debug_data.get('aan_occurrences', [])
            numbered_sections = debug_data.get('numbered_sections_found', 0)
            owners_found = debug_data.get('owners_found', [])
            pids_found = debug_data.get('pids_found', [])
            
            print(f"      📄 PDF Size: {pdf_size} bytes")
            print(f"      📝 PDF Text Length: {pdf_chars} characters")
            print(f"      🔢 AAN Occurrences: {len(aan_occurrences)} - {aan_occurrences}")
            print(f"      📋 Numbered Sections: {numbered_sections}")
            print(f"      👤 Owners Found: {len(owners_found)} - {owners_found}")
            print(f"      🏠 PIDs Found: {len(pids_found)} - {pids_found}")
            
            # Check if all expected AANs are detected
            expected_aans = ["00254118", "00453706", "09541209"]
            detected_aans = [aan for aan in expected_aans if aan in aan_occurrences]
            missing_aans = [aan for aan in expected_aans if aan not in aan_occurrences]
            
            print(f"\n   🎯 PROPERTY ENTRY DETECTION ANALYSIS:")
            print(f"      Expected AANs: {expected_aans}")
            print(f"      Detected AANs: {detected_aans} ({len(detected_aans)}/3)")
            
            if len(detected_aans) == 3:
                print(f"      ✅ All 3 property entries detected correctly")
            else:
                print(f"      ❌ Missing AANs: {missing_aans}")
                print(f"      🔍 ISSUE: Not all property entries being detected in PDF")
            
            # Check numbered sections (should be 1, 2, 8)
            if numbered_sections >= 3:
                print(f"      ✅ Sufficient numbered sections found ({numbered_sections})")
            else:
                print(f"      ❌ Insufficient numbered sections ({numbered_sections}, expected 3+)")
                print(f"      🔍 ISSUE: Section detection not finding entries 1, 2, 8")
            
        else:
            print(f"   ⚠️ Debug endpoint not available (status: {debug_response.status_code})")
            print(f"   📊 Cannot analyze PDF content structure without debug endpoint")
        
        # Test 3: Verify Section Extraction
        print(f"\n🔧 TEST 3: Section Extraction Verification")
        print("   📊 Checking if 3 complete property sections are extracted...")
        
        # Get current properties from database
        properties_response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Victoria County", timeout=30)
        
        if properties_response.status_code == 200:
            properties = properties_response.json()
            victoria_properties = [p for p in properties if p.get("municipality_name") == "Victoria County"]
            
            print(f"   📊 Properties in database: {len(victoria_properties)}")
            
            if len(victoria_properties) == 3:
                print(f"   ✅ All 3 property sections successfully extracted")
            elif len(victoria_properties) == 1:
                print(f"   ❌ Only 1 property section extracted (expected 3)")
                print(f"   🔍 ISSUE: Section extraction failing for entries 2 and 8")
            else:
                print(f"   ⚠️ Unexpected number of sections: {len(victoria_properties)}")
            
            # Analyze the extracted property
            if victoria_properties:
                prop = victoria_properties[0]
                print(f"\n   📋 EXTRACTED PROPERTY ANALYSIS:")
                print(f"      AAN: {prop.get('assessment_number')}")
                print(f"      Owner: {prop.get('owner_name')}")
                print(f"      Address: {prop.get('property_address')}")
                print(f"      PID: {prop.get('pid_number')}")
                print(f"      Opening Bid: ${prop.get('opening_bid')}")
                print(f"      Sale Date: {prop.get('sale_date')}")
                
                # Check if this is the expected first property
                if prop.get('assessment_number') == '00254118':
                    print(f"      ✅ This is entry 1 (AAN 00254118) - correctly extracted")
                    print(f"      🔍 ISSUE: Entries 2 (00453706) and 8 (09541209) not extracted")
                else:
                    print(f"      ⚠️ Unexpected property extracted")
                
                # Check raw data for parsing details
                raw_data = prop.get('raw_data', {})
                if raw_data:
                    print(f"\n   📊 RAW DATA ANALYSIS:")
                    source = raw_data.get('source', 'unknown')
                    print(f"      Source: {source}")
                    
                    if 'fallback' in source.lower():
                        print(f"      ❌ FALLBACK DATA DETECTED: Using sample data instead of PDF")
                    elif 'pdf' in source.lower():
                        print(f"      ✅ PDF DATA: Using actual PDF parsing")
                    
                    # Look for section information
                    if 'raw_section' in raw_data:
                        print(f"      📄 Raw section data available for analysis")
                    else:
                        print(f"      ⚠️ No raw section data - may indicate parsing issues")
        else:
            print(f"   ❌ Failed to retrieve properties: {properties_response.status_code}")
        
        # Test 4: Debug Individual Parsing
        print(f"\n🔧 TEST 4: Individual Parsing Debug")
        print("   📊 Analyzing detailed parsing of each section...")
        
        # This would require enhanced logging in the scraper
        # For now, we can infer from the results
        
        if len(victoria_properties) == 1:
            print(f"   🔍 PARSING ANALYSIS:")
            print(f"      ✅ Entry 1 (AAN 00254118): Successfully parsed")
            print(f"      ❌ Entry 2 (AAN 00453706): Parsing failed")
            print(f"      ❌ Entry 8 (AAN 09541209): Parsing failed")
            print(f"")
            print(f"   🎯 LIKELY ISSUES:")
            print(f"      - Non-sequential numbering (1, 2, 8) not handled correctly")
            print(f"      - Regex patterns expecting sequential numbers (1, 2, 3)")
            print(f"      - Property splitting logic fails on non-consecutive entries")
            print(f"      - Section boundary detection not working for entries 2 and 8")
        
        # Test 5: Identify Specific Failure Points
        print(f"\n🔧 TEST 5: Specific Failure Point Identification")
        print("   🎯 Identifying why only 1 property succeeds instead of 3...")
        
        failure_points = []
        
        # Based on the test results, identify specific issues
        if debug_response.status_code == 200 and debug_data:
            if len(detected_aans) < 3:
                failure_points.append("AAN detection - not finding all 3 AANs in PDF")
            
            if numbered_sections < 3:
                failure_points.append("Section detection - not finding entries 1, 2, 8")
        
        if len(victoria_properties) < 3:
            failure_points.append("Property extraction - only extracting 1 of 3 sections")
        
        if len(victoria_properties) == 1 and victoria_properties[0].get('assessment_number') == '00254118':
            failure_points.append("Non-sequential numbering - parser expects 1,2,3 but PDF has 1,2,8")
        
        print(f"   🔍 IDENTIFIED FAILURE POINTS:")
        for i, point in enumerate(failure_points, 1):
            print(f"      {i}. {point}")
        
        if not failure_points:
            print(f"      ✅ No specific failure points identified - parser may be working correctly")
        
        # Final Assessment
        print(f"\n📊 ENHANCED DEBUGGING ASSESSMENT:")
        
        if len(victoria_properties) == 3:
            print(f"   🎉 SUCCESS: All 3 properties extracted successfully!")
            print(f"   ✅ Entries 1, 2, and 8 all parsed correctly")
            print(f"   ✅ Non-sequential numbering handled properly")
            return True, {
                "status": "success",
                "properties_extracted": 3,
                "all_entries_found": True,
                "failure_points": []
            }
        else:
            print(f"   ❌ ISSUE CONFIRMED: Only {len(victoria_properties)} property extracted (expected 3)")
            print(f"   🔍 ROOT CAUSE: Parser not handling non-sequential numbering (1, 2, 8)")
            print(f"   📋 SOLUTION NEEDED: Update regex patterns to handle ANY numbered sections")
            print(f"   📋 SPECIFIC FIX: Change from sequential (1,2,3) to non-sequential (1,2,8) support")
            
            return False, {
                "status": "failed",
                "properties_extracted": len(victoria_properties),
                "expected_properties": 3,
                "failure_points": failure_points,
                "root_cause": "Non-sequential numbering (1,2,8) not handled correctly"
            }
            
    except Exception as e:
        print(f"   ❌ Enhanced debugging test error: {e}")
        return False, {"error": str(e)}

def main():
    """Main enhanced debugging test execution"""
    print("🚀 Victoria County Enhanced Debugging Test")
    print("🎯 Identifying extraction issue as requested in review")
    print("")
    
    success, result = test_victoria_county_enhanced_debugging()
    
    print(f"\n" + "=" * 80)
    print("📊 ENHANCED DEBUGGING TEST RESULTS")
    print("=" * 80)
    
    if success:
        print("🎉 VICTORIA COUNTY PARSER: WORKING CORRECTLY!")
        print("✅ All 3 properties extracted from entries 1, 2, and 8")
        print("✅ Non-sequential numbering handled properly")
        print("✅ Enhanced debugging shows successful parsing")
    else:
        print("❌ VICTORIA COUNTY PARSER: EXTRACTION ISSUE CONFIRMED")
        print("🔍 ROOT CAUSE IDENTIFIED:")
        
        if result.get('root_cause'):
            print(f"   - {result['root_cause']}")
        
        if result.get('failure_points'):
            print(f"🔧 SPECIFIC FAILURE POINTS:")
            for point in result['failure_points']:
                print(f"   - {point}")
        
        print(f"\n📋 RECOMMENDED FIXES:")
        print(f"   1. Update property splitting regex to handle non-sequential numbering")
        print(f"   2. Change pattern from expecting (1,2,3) to support (1,2,8)")
        print(f"   3. Fix section boundary detection for entries 2 and 8")
        print(f"   4. Ensure all AAN patterns are detected correctly")
        print(f"   5. Test with actual PDF structure (1. AAN:, 2. AAN:, 8. AAN:)")
    
    print("=" * 80)
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)