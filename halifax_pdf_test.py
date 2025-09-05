#!/usr/bin/env python3
"""
Specific test for Halifax PDF parsing functionality
Tests if the PDF parsing is actually working vs using fallback data
"""

import requests
import json
import sys
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://tax-auction-hub.preview.emergentagent.com/api"

def test_halifax_pdf_parsing():
    """Test Halifax PDF parsing specifically"""
    print("🔍 Testing Halifax PDF Parsing Implementation...")
    
    # First, clear existing tax sales to get a clean test
    print("   Clearing existing tax sales for clean test...")
    try:
        clear_response = requests.post(f"{BACKEND_URL}/clear-tax-sales", timeout=30)
        if clear_response.status_code == 200:
            result = clear_response.json()
            print(f"   ✅ Cleared {result.get('deleted_count', 0)} existing properties")
        else:
            print(f"   ⚠️ Could not clear existing data: {clear_response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Error clearing data: {e}")
    
    # Now trigger Halifax scraping
    print("   Triggering Halifax scrape to test PDF parsing...")
    try:
        response = requests.post(f"{BACKEND_URL}/scrape/halifax", timeout=180)  # Longer timeout for PDF processing
        
        if response.status_code == 200:
            result = response.json()
            properties_scraped = result.get('properties_scraped', 0)
            
            print(f"✅ Halifax scraper completed")
            print(f"   📊 Status: {result.get('status', 'unknown')}")
            print(f"   🏠 Properties scraped: {properties_scraped}")
            
            # Check if we got more than 1 property (indicating successful PDF parsing)
            if properties_scraped > 1:
                print("🎉 SUCCESS: Multiple properties extracted - PDF parsing is working!")
                return True, properties_scraped
            elif properties_scraped == 1:
                print("⚠️ WARNING: Only 1 property extracted - likely using fallback sample data")
                print("   This suggests PDF parsing failed and fallback was used")
                return False, properties_scraped
            else:
                print("❌ ERROR: No properties extracted")
                return False, properties_scraped
        else:
            print(f"❌ Halifax scraper failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Raw response: {response.text}")
            return False, 0
    except Exception as e:
        print(f"❌ Halifax scraper error: {e}")
        return False, 0

def verify_extracted_properties():
    """Verify the quality and variety of extracted properties"""
    print("\n🔍 Verifying Extracted Property Data...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax", timeout=30)
        if response.status_code == 200:
            properties = response.json()
            halifax_properties = [p for p in properties if "Halifax" in p.get("municipality_name", "")]
            
            print(f"   Found {len(halifax_properties)} Halifax properties")
            
            if len(halifax_properties) == 0:
                print("❌ No Halifax properties found")
                return False
            
            # Analyze the properties
            unique_assessments = set()
            unique_owners = set()
            unique_pids = set()
            opening_bids = []
            
            print("\n   📋 Property Analysis:")
            for i, prop in enumerate(halifax_properties[:5]):  # Show first 5
                assessment = prop.get('assessment_number', 'N/A')
                owner = prop.get('owner_name', 'N/A')
                pid = prop.get('pid_number', 'N/A')
                bid = prop.get('opening_bid', 0)
                
                unique_assessments.add(assessment)
                unique_owners.add(owner)
                unique_pids.add(pid)
                if bid and bid > 0:
                    opening_bids.append(bid)
                
                print(f"   {i+1}. Assessment: {assessment}")
                print(f"      Owner: {owner}")
                print(f"      PID: {pid}")
                print(f"      Opening Bid: ${bid}")
                print(f"      Address: {prop.get('property_address', 'N/A')}")
                print()
            
            # Check for diversity (indicates real PDF parsing vs sample data)
            print(f"   📊 Data Diversity Analysis:")
            print(f"   - Unique Assessment Numbers: {len(unique_assessments)}")
            print(f"   - Unique Owner Names: {len(unique_owners)}")
            print(f"   - Unique PIDs: {len(unique_pids)}")
            print(f"   - Properties with Opening Bids: {len(opening_bids)}")
            
            if len(opening_bids) > 0:
                avg_bid = sum(opening_bids) / len(opening_bids)
                min_bid = min(opening_bids)
                max_bid = max(opening_bids)
                print(f"   - Bid Range: ${min_bid:.2f} - ${max_bid:.2f} (avg: ${avg_bid:.2f})")
            
            # Determine if this looks like real parsed data
            if len(halifax_properties) > 1 and len(unique_assessments) > 1 and len(unique_owners) > 1:
                print("✅ Data appears to be from successful PDF parsing (diverse properties)")
                return True
            elif len(halifax_properties) == 1:
                # Check if it's the known sample property
                sample_prop = halifax_properties[0]
                if (sample_prop.get('assessment_number') == '02102943' and 
                    'MARILYN ANNE BURNS' in sample_prop.get('owner_name', '')):
                    print("⚠️ Data appears to be fallback sample data (PDF parsing likely failed)")
                    return False
                else:
                    print("✅ Single property but not the known sample - may be real data")
                    return True
            else:
                print("❌ Insufficient data to determine parsing success")
                return False
                
        else:
            print(f"❌ Could not retrieve tax sales: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error verifying properties: {e}")
        return False

def test_pdf_download_capability():
    """Test if the system can actually download the Halifax PDF"""
    print("\n🌐 Testing PDF Download Capability...")
    
    # Test the known Halifax PDF URL
    pdf_url = "https://www.halifax.ca/media/91654"
    
    try:
        print(f"   Attempting to download PDF from: {pdf_url}")
        response = requests.get(pdf_url, timeout=60)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            
            print(f"✅ PDF download successful")
            print(f"   Content-Type: {content_type}")
            print(f"   Size: {content_length} bytes")
            
            if 'pdf' in content_type.lower() or content_length > 10000:
                print("✅ Downloaded content appears to be a valid PDF")
                return True
            else:
                print("⚠️ Downloaded content may not be a valid PDF")
                return False
        else:
            print(f"❌ PDF download failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ PDF download error: {e}")
        return False

def run_halifax_pdf_tests():
    """Run comprehensive Halifax PDF parsing tests"""
    print("🚀 Halifax PDF Parsing Comprehensive Test")
    print("=" * 50)
    
    test_results = {
        "pdf_download": False,
        "pdf_parsing": False,
        "data_verification": False
    }
    
    # Test 1: PDF Download Capability
    test_results["pdf_download"] = test_pdf_download_capability()
    
    # Test 2: Halifax PDF Parsing
    parsing_success, properties_count = test_halifax_pdf_parsing()
    test_results["pdf_parsing"] = parsing_success
    
    # Test 3: Data Verification
    test_results["data_verification"] = verify_extracted_properties()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 HALIFAX PDF PARSING TEST SUMMARY")
    print("=" * 50)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if test_results["pdf_parsing"] and test_results["data_verification"]:
        print("🎉 SUCCESS: Halifax PDF parsing is working correctly!")
        print("   Multiple properties are being extracted from the actual PDF document.")
    elif test_results["pdf_download"] and not test_results["pdf_parsing"]:
        print("⚠️ PARTIAL: PDF can be downloaded but parsing is not extracting multiple properties")
        print("   The system is likely falling back to sample data due to PDF parsing issues.")
    else:
        print("❌ FAILURE: Halifax PDF parsing is not working")
        print("   The system cannot download or parse the PDF document properly.")
    
    return test_results

if __name__ == "__main__":
    print(f"Testing Halifax PDF parsing at: {BACKEND_URL}")
    print(f"Test started at: {datetime.now()}")
    
    results = run_halifax_pdf_tests()
    
    # Exit with appropriate code based on PDF parsing success
    if results["pdf_parsing"] and results["data_verification"]:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # PDF parsing issues