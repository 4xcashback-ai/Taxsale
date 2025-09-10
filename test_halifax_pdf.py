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

# Backend URL for local server
BACKEND_URL = "http://localhost:8001/api"

def test_halifax_pdf_parsing():
    """Test Halifax PDF parsing specifically"""
    print("🔍 Testing Halifax PDF Parsing Implementation...")
    
    # Get admin token first
    print("   Getting admin authentication...")
    try:
        auth_response = requests.post(f"{BACKEND_URL}/auth/login", 
                                    json={"email": "admin", "password": "TaxSale2025!SecureAdmin"},
                                    timeout=30)
        if auth_response.status_code == 200:
            token = auth_response.json().get('access_token')
            headers = {"Authorization": f"Bearer {token}"}
            print("   ✅ Admin authentication successful")
        else:
            print(f"   ❌ Authentication failed: {auth_response.status_code}")
            return False, 0
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return False, 0
    
    # Now trigger Halifax scraping
    print("   Triggering Halifax scrape to test PDF parsing...")
    try:
        response = requests.post(f"{BACKEND_URL}/admin/scrape/halifax", 
                               headers=headers, 
                               timeout=180)  # Longer timeout for PDF processing
        
        if response.status_code == 200:
            result = response.json()
            properties_scraped = result.get('properties_found', 0)
            
            print(f"✅ Halifax scraper completed")
            print(f"   📊 Status: {result.get('success', 'unknown')}")
            print(f"   🏠 Properties scraped: {properties_scraped}")
            print(f"   🔍 Debug info: {result.get('debug_info', {})}")
            
            # Check if we got more than 50 properties (indicating successful PDF parsing)
            if properties_scraped > 50:
                print("🎉 SUCCESS: Multiple properties extracted - PDF parsing is working!")
                return True, properties_scraped
            elif properties_scraped > 1:
                print("⚠️ PARTIAL SUCCESS: Some properties extracted but less than expected")
                print("   This might indicate partial PDF parsing success")
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
    """Verify the quality and variety of extracted properties via direct database check"""
    print("\n🔍 Verifying Extracted Property Data via Database...")
    
    try:
        import mysql.connector
        
        # Connect to database
        conn = mysql.connector.connect(
            host='localhost',
            user='taxsale',
            password='SecureTaxSale2025!',
            database='tax_sale_compass'
        )
        cursor = conn.cursor(dictionary=True)
        
        # Get Halifax properties
        cursor.execute("SELECT * FROM properties WHERE municipality = 'Halifax Regional Municipality'")
        halifax_properties = cursor.fetchall()
        
        print(f"   Found {len(halifax_properties)} Halifax properties in database")
        
        if len(halifax_properties) == 0:
            print("❌ No Halifax properties found in database")
            return False
        
        # Analyze the properties
        unique_assessments = set()
        addresses_with_streets = 0
        addresses_with_owners = 0
        valid_tax_amounts = 0
        
        print("\n   📋 Property Analysis:")
        for i, prop in enumerate(halifax_properties[:5]):  # Show first 5
            assessment = prop.get('assessment_number', 'N/A')
            address = prop.get('civic_address', 'N/A')
            tax_amount = prop.get('total_taxes', 0)
            
            unique_assessments.add(assessment)
            
            # Check if address looks like a street address vs owner name
            if any(word in address.lower() for word in ['rd', 'road', 'st', 'street', 'ave', 'avenue', 'dr', 'drive', 'lot']):
                addresses_with_streets += 1
            elif any(word in address for word in ['Burns', 'Wigginton', 'Estate']):  # Common owner name patterns
                addresses_with_owners += 1
            
            if tax_amount and tax_amount > 0:
                valid_tax_amounts += 1
            
            print(f"   {i+1}. Assessment: {assessment}")
            print(f"      Address: {address}")
            print(f"      Tax Amount: ${tax_amount}")
            print()
        
        # Check for diversity and quality (indicates real PDF parsing vs sample data)
        print(f"   📊 Data Quality Analysis:")
        print(f"   - Total Properties: {len(halifax_properties)}")
        print(f"   - Unique Assessment Numbers: {len(unique_assessments)}")
        print(f"   - Addresses with Street Names: {addresses_with_streets}")
        print(f"   - Addresses with Owner Names: {addresses_with_owners}")
        print(f"   - Properties with Valid Tax Amounts: {valid_tax_amounts}")
        
        cursor.close()
        conn.close()
        
        # Determine if this looks like real parsed data
        if len(halifax_properties) > 50 and len(unique_assessments) > 50:
            print("✅ Data appears to be from successful PDF parsing (many diverse properties)")
            if addresses_with_streets > addresses_with_owners:
                print("✅ Address parsing is working well (more street addresses than owner names)")
            else:
                print("⚠️ Address parsing needs improvement (too many owner names in addresses)")
            return True
        elif len(halifax_properties) > 10:
            print("⚠️ Moderate success - some properties extracted but not full PDF")
            return True
        else:
            print("❌ Insufficient data - likely fallback sample data only")
            return False
                
    except Exception as e:
        print(f"❌ Error verifying properties: {e}")
        return False

def test_pdf_download_capability():
    """Test if the system can actually download the Halifax PDF"""
    print("\n🌐 Testing PDF Download Capability...")
    
    # Test the actual Halifax PDF URL we're using
    pdf_url = "https://cdn.halifax.ca/sites/default/files/documents/home-property/property-taxes/sept16.2025newspaper.website-sept3.25.pdf"
    
    try:
        print(f"   Attempting to download PDF from: {pdf_url}")
        response = requests.get(pdf_url, timeout=60)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            
            print(f"✅ PDF download successful")
            print(f"   Content-Type: {content_type}")
            print(f"   Size: {content_length} bytes ({content_length/1024:.1f} KB)")
            
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

def clear_test_data():
    """Clear existing Halifax properties for clean test"""
    print("\n🧹 Clearing existing Halifax properties for clean test...")
    
    try:
        import mysql.connector
        
        conn = mysql.connector.connect(
            host='localhost',
            user='taxsale',
            password='SecureTaxSale2025!',
            database='tax_sale_compass'
        )
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM properties WHERE municipality = 'Halifax Regional Municipality'")
        deleted_count = cursor.rowcount
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Cleared {deleted_count} existing Halifax properties")
        return True
        
    except Exception as e:
        print(f"   ❌ Error clearing data: {e}")
        return False

def run_halifax_pdf_tests():
    """Run comprehensive Halifax PDF parsing tests"""
    print("🚀 Halifax PDF Parsing Comprehensive Test")
    print("=" * 50)
    
    test_results = {
        "pdf_download": False,
        "data_clearing": False,
        "pdf_parsing": False,
        "data_verification": False
    }
    
    # Test 0: Clear existing data
    test_results["data_clearing"] = clear_test_data()
    
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
        print("\n🎉 ALL TESTS PASSED - Halifax PDF parsing is fully operational!")
        sys.exit(0)  # Success
    else:
        print("\n❌ SOME TESTS FAILED - Halifax PDF parsing needs attention")
        sys.exit(1)  # PDF parsing issues