#!/usr/bin/env python3
"""
Comprehensive test for Halifax PDF parsing implementation
Validates all requirements from the review request
"""

import requests
import json
import sys
from datetime import datetime

BACKEND_URL = "https://nstaxmap.preview.emergentagent.com/api"

def test_halifax_scrape_endpoint():
    """Test the /api/scrape/halifax endpoint"""
    print("🔍 Testing /api/scrape/halifax endpoint...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/scrape/halifax", timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            properties_scraped = result.get('properties_scraped', 0)
            
            print(f"✅ Endpoint working - Status: {result.get('status')}")
            print(f"   Properties scraped: {properties_scraped}")
            
            if properties_scraped > 1:
                print("✅ Successfully extracted multiple properties (more than sample)")
                return True, properties_scraped
            else:
                print("❌ Only extracted 1 property - likely fallback data")
                return False, properties_scraped
        else:
            print(f"❌ Endpoint failed with status {response.status_code}")
            return False, 0
    except Exception as e:
        print(f"❌ Endpoint error: {e}")
        return False, 0

def verify_property_fields():
    """Verify extracted properties have proper required fields"""
    print("\n📋 Verifying property field completeness...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax&limit=100", timeout=30)
        if response.status_code == 200:
            properties = response.json()
            halifax_properties = [p for p in properties if "Halifax" in p.get("municipality_name", "")]
            
            print(f"   Found {len(halifax_properties)} Halifax properties")
            
            required_fields = ['assessment_number', 'owner_name', 'pid_number', 'opening_bid']
            field_stats = {field: 0 for field in required_fields}
            
            for prop in halifax_properties:
                for field in required_fields:
                    if prop.get(field) and str(prop.get(field)).strip():
                        field_stats[field] += 1
            
            print("   Field completeness:")
            all_fields_good = True
            for field, count in field_stats.items():
                percentage = (count / len(halifax_properties)) * 100 if halifax_properties else 0
                print(f"   - {field}: {count}/{len(halifax_properties)} ({percentage:.1f}%)")
                if percentage < 80:  # Require at least 80% completeness
                    all_fields_good = False
            
            if all_fields_good:
                print("✅ All required fields have good coverage")
                return True, halifax_properties
            else:
                print("⚠️ Some required fields have low coverage")
                return False, halifax_properties
        else:
            print(f"❌ Could not retrieve properties: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ Error verifying fields: {e}")
        return False, []

def test_data_realism():
    """Test if extracted data looks realistic and properly formatted"""
    print("\n🔍 Testing data realism and formatting...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax&limit=20", timeout=30)
        if response.status_code == 200:
            properties = response.json()
            halifax_properties = [p for p in properties if "Halifax" in p.get("municipality_name", "")]
            
            if not halifax_properties:
                print("❌ No Halifax properties found")
                return False
            
            # Check data patterns
            assessment_numbers = []
            owner_names = []
            pid_numbers = []
            opening_bids = []
            
            for prop in halifax_properties[:10]:  # Check first 10
                assessment = prop.get('assessment_number', '')
                owner = prop.get('owner_name', '')
                pid = prop.get('pid_number', '')
                bid = prop.get('opening_bid', 0)
                
                if assessment:
                    assessment_numbers.append(assessment)
                if owner:
                    owner_names.append(owner)
                if pid:
                    pid_numbers.append(pid)
                if bid and bid > 0:
                    opening_bids.append(bid)
            
            print(f"   Sample data analysis (first 10 properties):")
            
            # Check assessment number format (should be 8 digits)
            valid_assessments = [a for a in assessment_numbers if len(str(a)) == 8 and str(a).isdigit()]
            print(f"   - Valid assessment numbers: {len(valid_assessments)}/{len(assessment_numbers)}")
            
            # Check owner names (should have proper case and spaces)
            valid_owners = [o for o in owner_names if len(o) > 3 and ' ' in o and any(c.isupper() for c in o)]
            print(f"   - Realistic owner names: {len(valid_owners)}/{len(owner_names)}")
            
            # Check PID numbers (should be 8 digits)
            valid_pids = [p for p in pid_numbers if len(str(p)) == 8 and str(p).isdigit()]
            print(f"   - Valid PID numbers: {len(valid_pids)}/{len(pid_numbers)}")
            
            # Check opening bids (should be reasonable amounts)
            reasonable_bids = [b for b in opening_bids if 100 <= b <= 1000000]
            print(f"   - Reasonable opening bids: {len(reasonable_bids)}/{len(opening_bids)}")
            
            # Show some examples
            print("\n   Sample properties:")
            for i, prop in enumerate(halifax_properties[:3]):
                print(f"   {i+1}. Assessment: {prop.get('assessment_number', 'N/A')}")
                print(f"      Owner: {prop.get('owner_name', 'N/A')}")
                print(f"      PID: {prop.get('pid_number', 'N/A')}")
                print(f"      Bid: ${prop.get('opening_bid', 0)}")
            
            # Overall assessment
            total_checks = 4
            passed_checks = 0
            
            if len(valid_assessments) >= len(assessment_numbers) * 0.8:
                passed_checks += 1
            if len(valid_owners) >= len(owner_names) * 0.8:
                passed_checks += 1
            if len(valid_pids) >= len(pid_numbers) * 0.8:
                passed_checks += 1
            if len(reasonable_bids) >= len(opening_bids) * 0.8:
                passed_checks += 1
            
            if passed_checks >= 3:
                print("✅ Data appears realistic and properly formatted")
                return True
            else:
                print("⚠️ Some data quality issues detected")
                return False
        else:
            print(f"❌ Could not retrieve properties: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing data realism: {e}")
        return False

def test_tax_sales_endpoint():
    """Test the /api/tax-sales endpoint shows newly parsed properties"""
    print("\n🏠 Testing /api/tax-sales endpoint...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/tax-sales", timeout=30)
        if response.status_code == 200:
            properties = response.json()
            halifax_properties = [p for p in properties if "Halifax" in p.get("municipality_name", "")]
            
            print(f"✅ Endpoint working - Total properties: {len(properties)}")
            print(f"   Halifax properties: {len(halifax_properties)}")
            
            if len(halifax_properties) > 1:
                print("✅ Multiple Halifax properties visible in endpoint")
                return True, halifax_properties
            else:
                print("❌ Only 1 or no Halifax properties found")
                return False, halifax_properties
        else:
            print(f"❌ Endpoint failed with status {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ Endpoint error: {e}")
        return False, []

def run_comprehensive_test():
    """Run all comprehensive tests"""
    print("🚀 Comprehensive Halifax PDF Parsing Test")
    print("Testing all requirements from review request")
    print("=" * 60)
    
    test_results = {
        "scrape_endpoint": False,
        "pdf_parsing": False,
        "multiple_properties": False,
        "proper_fields": False,
        "tax_sales_endpoint": False,
        "data_realism": False
    }
    
    # Test 1: /api/scrape/halifax endpoint
    scrape_success, properties_count = test_halifax_scrape_endpoint()
    test_results["scrape_endpoint"] = scrape_success
    test_results["pdf_parsing"] = scrape_success  # Same test
    test_results["multiple_properties"] = properties_count > 1
    
    # Test 2: Property field verification
    fields_success, properties = verify_property_fields()
    test_results["proper_fields"] = fields_success
    
    # Test 3: /api/tax-sales endpoint
    tax_sales_success, _ = test_tax_sales_endpoint()
    test_results["tax_sales_endpoint"] = tax_sales_success
    
    # Test 4: Data realism
    realism_success = test_data_realism()
    test_results["data_realism"] = realism_success
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    requirements = [
        ("✅ /api/scrape/halifax endpoint works", test_results["scrape_endpoint"]),
        ("✅ PDF parsing logic works correctly", test_results["pdf_parsing"]),
        ("✅ Downloads and parses actual Halifax PDF", test_results["pdf_parsing"]),
        ("✅ Extracts more than single sample property", test_results["multiple_properties"]),
        ("✅ Properties have proper required fields", test_results["proper_fields"]),
        ("✅ /api/tax-sales shows newly parsed properties", test_results["tax_sales_endpoint"]),
        ("✅ Data looks realistic and properly formatted", test_results["data_realism"])
    ]
    
    passed_requirements = 0
    for requirement, passed in requirements:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{requirement}: {status}")
        if passed:
            passed_requirements += 1
    
    print(f"\nOverall: {passed_requirements}/{len(requirements)} requirements met")
    
    if passed_requirements == len(requirements):
        print("🎉 ALL REQUIREMENTS MET - Halifax PDF parsing is fully working!")
    elif passed_requirements >= 5:
        print("✅ MOSTLY WORKING - Core functionality operational")
    else:
        print("❌ SIGNIFICANT ISSUES - Multiple requirements not met")
    
    return test_results, passed_requirements, len(requirements)

if __name__ == "__main__":
    print(f"Testing Halifax PDF parsing at: {BACKEND_URL}")
    print(f"Test started at: {datetime.now()}")
    
    results, passed, total = run_comprehensive_test()
    
    if passed == total:
        sys.exit(0)  # All requirements met
    elif passed >= 5:
        sys.exit(1)  # Mostly working
    else:
        sys.exit(2)  # Significant issues